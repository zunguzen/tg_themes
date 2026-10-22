#!/usr/bin/env python3
"""Convert Telegram iOS themes (.tgios-theme) to Telegram Android themes (.attheme).

Usage:
    python3 tools/ios_to_android.py                  # every */*.tgios-theme in the repo
    python3 tools/ios_to_android.py Japan/washi.tgios-theme [more files]
    python3 tools/ios_to_android.py --check          # convert in memory, fail if a file differs

How it works
- The iOS file gives the main roles: backgrounds, text, accent, chat bubbles, unread badge,
  input panel, wallpaper (see `convert`, dictionary `P`).
- Telegram Android has about 800 color keys. The names and default colors are read from Telegram's own
  source (ThemeColors.java and the darkblue.attheme asset in github.com/DrKLO/Telegram). The two
  files are downloaded when needed and kept in tools/.cache; they are not stored in this repo.
- Every other key is recolored from those defaults: grays follow the lightness of the iOS palette,
  colored keys become the accent (red keys become the destructive color).
- A few text/background pairs are corrected when the contrast is below 3.
- Raster themes (--raster, or a path with /Raster/) also get neutral avatars and flat bubbles.
Colors are written as decimal ARGB numbers, like Telegram's own .attheme files.
The result is close to the iOS theme but not identical. It needs a check on a real Android phone.
"""
import sys, os, re, colorsys, glob, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, '.cache')
BASE = 'https://raw.githubusercontent.com/DrKLO/Telegram/master/TMessagesProj/src/main/'
SOURCES = {
    'ThemeColors.java': BASE + 'java/org/telegram/ui/ActionBar/ThemeColors.java',
    'darkblue.attheme': BASE + 'assets/darkblue.attheme',
}


def fetch(name):
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        with urllib.request.urlopen(SOURCES[name], timeout=60) as r:
            data = r.read()
        open(path, 'wb').write(data)
    return open(path, encoding='utf-8').read()


def load():
    """Return (light, dark): dictionaries {android key name: 0xAARRGGBB}."""
    t = fetch('ThemeColors.java')
    consts = {'TELEGRAM_COLOR': 0xFF229AF0, 'TELEGRAM_COLOR_TEXT': 0xFF298ACF, 'DEFAULT_BLACK_TEXT': 0xFF1A1D21,
              'Color.WHITE': 0xFFFFFFFF, 'ColorUtils.setAlphaComponent(Color.WHITE, 90)': 0x5AFFFFFF, '0': 0}
    d = {}
    for k, v in re.findall(r'defaultColors\[(key_\w+)\]\s*=\s*([^;]+);', t):
        v = v.strip()
        if re.fullmatch(r'0x[0-9a-fA-F]+', v): d[k] = int(v, 16)
        elif v in consts: d[k] = consts[v]
        elif re.fullmatch(r'-\d+', v): d[k] = int(v) & 0xFFFFFFFF
    names = dict(re.findall(r'colorKeysMap\.put\((key_\w+),\s*"(\w+)"\)', t))
    light = {names[k]: v for k, v in d.items() if k in names}
    dark = dict(light)
    for l in fetch('darkblue.attheme').splitlines():
        if '=' in l:
            k, v = l.split('=', 1); v = v.strip()
            if v.startswith('#'):
                dark[k] = int(v[1:], 16) if len(v) == 9 else 0xFF000000 | int(v[1:], 16)
            else:
                dark[k] = int(v) & 0xFFFFFFFF
    return light, dark


# ---------- colour helpers (all colours are 0xAARRGGBB ints) ----------
def parts(c): return (c >> 24) & 255, (c >> 16) & 255, (c >> 8) & 255, c & 255
def mk(a, r, g, b): return (a << 24) | (r << 16) | (g << 8) | b
def hls(c):
    a, r, g, b = parts(c); return colorsys.rgb_to_hls(r/255, g/255, b/255)
def lum(c): return hls(c)[1]
def chroma(c):
    a, r, g, b = parts(c); return (max(r, g, b) - min(r, g, b)) / 255
def with_alpha(c, a): return (a << 24) | (c & 0xFFFFFF)
def mix(c1, c2, t):
    a1, r1, g1, b1 = parts(c1); a2, r2, g2, b2 = parts(c2)
    f = lambda x, y: round(x + (y - x) * t)
    return mk(f(a1, a2), f(r1, r2), f(g1, g2), f(b1, b2))
def rel(c):
    _, r, g, b = parts(c)
    f = lambda v: (v/255/12.92) if v/255 <= 0.03928 else (((v/255)+0.055)/1.055)**2.4
    return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b)
def contrast(c1, c2):
    a, b = sorted((rel(c1), rel(c2)), reverse=True); return (a+0.05)/(b+0.05)
def hexs(c): return '#%08x' % c

def ios_color(s):
    s = s.strip()
    if s == 'clear': return 0
    h = s[1:]
    if len(h) == 6: return 0xFF000000 | int(h, 16)
    return int(h, 16)  # iOS themes write transparent colors as #AARRGGBB (alpha first)

def read_ios(path):
    d = {}
    for l in open(path, encoding='utf-8').read().splitlines():
        if ': ' in l:
            k, v = l.split(': ', 1); d[k.strip()] = v.strip()
    return d

# ---------- ramp: neutral colours are mapped by lightness between anchors ----------
def ramp(anchors):
    pts = sorted((lum(t), p) for t, p in anchors)
    def f(c):
        L = lum(c); a = c >> 24
        if L <= pts[0][0]: r = pts[0][1]
        elif L >= pts[-1][0]: r = pts[-1][1]
        else:
            for (l1, p1), (l2, p2) in zip(pts, pts[1:]):
                if l1 <= L <= l2:
                    r = mix(p1, p2, 0 if l2 == l1 else (L - l1)/(l2 - l1)); break
        return with_alpha(r, a)
    return f

def recolor(c, neutral, acc, acc_ref_L, dest):
    a = c >> 24
    if a == 0: return c
    if chroma(c) < 0.2: return neutral(c)
    h, L, s = hls(c)
    if s > 0.3 and (h < 0.07 or h > 0.93):          # red family
        base = dest
    else:
        base = acc
    bh, bl, bs = hls(base)
    nl = min(0.95, max(0.05, bl + (L - acc_ref_L) * 0.8))
    r, g, b = colorsys.hls_to_rgb(bh, nl, bs)
    return mk(a, round(r*255), round(g*255), round(b*255))

def convert(path, raster):
    ios = read_ios(path)
    g = lambda k: ios_color(ios[k])
    dark = ios['dark'] == 'true'
    P = dict(
        bg=g('list_plainBg'), surf=g('list_itemBlocksBg'), text=g('list_primaryText'),
        sec=g('list_secondaryText'), acc=g('list_accent'), sep=g('list_plainSeparator'),
        nav=g('root_navBar_background'), inb=g('chat_message_incoming_bubble_withoutWp_bg'),
        inbsel=g('chat_message_incoming_bubble_withoutWp_highlightedBg'),
        outb=g('chat_message_outgoing_bubble_withoutWp_bgList_0'),
        outbsel=g('chat_message_outgoing_bubble_withoutWp_highlightedBg'),
        outt=g('chat_message_outgoing_primaryText'), outl=g('chat_message_outgoing_linkText'),
        outs=g('chat_message_outgoing_secondaryText'), ins=g('chat_message_incoming_secondaryText'),
        inl=g('chat_message_incoming_linkText'), dest=g('list_destructive'), wp=g('wallpaper'),
        badge=g('chatList_unreadBadgeActiveBg'), badget=g('chatList_unreadBadgeActiveText'),
        pin=g('chatList_pinnedItemBg'), panel=g('chat_inputPanel_panelBg'),
        inp=g('chat_inputPanel_inputBg'), inpt=g('chat_inputPanel_inputText'),
        inph=g('chat_inputPanel_inputPlaceholder'), ctl=g('chat_inputPanel_panelControl'),
        svc=g('chat_serviceMessage_components_withDefaultWp_bg'),
        svct=g('chat_serviceMessage_components_withDefaultWp_primaryText'),
        navsep=g('root_navBar_separator'))
    LIGHT, DARK = templates()
    T = DARK if dark else LIGHT
    ref = 0.69 if dark else 0.53
    if dark:
        anchors = [(T['windowBackgroundGray'], P['bg']), (T['windowBackgroundWhite'], P['surf']),
                   (T['chat_inBubble'], P['inb']), (T['chats_message'], P['sec']),
                   (T['chat_messageTextIn'], P['text'])]
    else:
        anchors = [(T['windowBackgroundWhite'], P['surf']), (T['windowBackgroundGray'], P['bg']),
                   (T['divider'], P['sep']), (T['chats_message'], P['sec']),
                   (T['windowBackgroundWhiteBlackText'], P['text'])]
    neutral = ramp(anchors)
    # the outgoing bubble can have the opposite polarity from the theme (Washi, Raster Weiss)
    out_dark = lum(P['outb']) < 0.5
    TO = DARK if out_dark else LIGHT
    out_neutral = ramp([(TO['chat_outBubble'], P['outb']), (TO['chat_outTimeText'], P['outs']),
                        (TO['chat_messageTextOut'], P['outt'])])
    out_ref = 0.69 if out_dark else 0.53

    out = {}
    for k in LIGHT:
        is_out = k.startswith('chat_out') or k.startswith('chat_stickerOut')
        src = TO if is_out else T
        c = src.get(k, T[k])
        if k.startswith('avatar_background') and 'ActionBar' not in k and 'InProfile' not in k or k.startswith('avatar_nameInMessage'):
            c = (P['sec'] if k.startswith('avatar_background') else P['text']) if raster else c
            if not raster: c = T[k]
        elif is_out:
            c = recolor(c, out_neutral, P['outl'], out_ref, P['dest'])
        else:
            c = recolor(c, neutral, P['acc'], ref, P['dest'])
        out[k] = c

    explicit = {
        'windowBackgroundWhite': P['surf'], 'windowBackgroundGray': P['bg'],
        'windowBackgroundWhiteBlackText': P['text'], 'actionBarDefault': P['nav'],
        'actionBarDefaultTitle': P['text'], 'actionBarDefaultIcon': P['text'],
        'actionBarDefaultSubtitle': P['sec'], 'divider': P['sep'],
        'chats_pinnedOverlay': P['pin'], 'chats_actionBackground': P['acc'],
        'chats_actionIcon': P['badget'], 'chats_unreadCounter': P['badge'],
        'chats_unreadCounterText': P['badget'], 'chats_name': P['text'],
        'chats_nameMessage': P['text'], 'chats_message': P['sec'], 'chats_date': P['sec'],
        'chats_sentCheck': P['acc'], 'chat_wallpaper': P['wp'],
        'chat_inBubble': P['inb'], 'chat_outBubble': P['outb'],
        'chat_inBubbleSelected': P['inbsel'], 'chat_outBubbleSelected': P['outbsel'],
        'chat_messageTextIn': P['text'], 'chat_messageTextOut': P['outt'],
        'chat_messageLinkIn': P['inl'], 'chat_messageLinkOut': P['outl'],
        'chat_inTimeText': P['ins'], 'chat_outTimeText': P['outs'], 'chat_outSentCheck': P['outs'],
        'chat_messagePanelBackground': P['panel'], 'chat_messagePanelText': P['inpt'],
        'chat_messagePanelHint': P['inph'], 'chat_messagePanelSend': P['acc'],
        'chat_messagePanelIcons': P['ctl'],
        'chat_serviceBackground': P['svc'], 'chat_serviceText': P['svct'],
        'avatar_backgroundActionBarBlue': P['nav'], 'avatar_backgroundInProfileBlue': P['nav'],
        'avatar_subtitleInProfileBlue': P['sec'], 'avatar_actionBarIconBlue': P['text'],
        'actionBarDefaultSelector': with_alpha(P['text'], 0x20),
        'listSelector': with_alpha(P['text'], 0x14),
        'chats_menuBackground': P['surf'], 'chats_menuName': P['text'],
        'chats_menuPhone': P['sec'], 'chats_menuPhoneShadow': 0,
        'chats_menuTopShadow': 0, 'chats_menuTopShadowCats': 0,
        'chat_outBubbleGradient1': 0, 'chat_outBubbleGradient2': 0, 'chat_outBubbleGradient3': 0,
    }
    if raster:
        explicit.update({'chat_inBubbleShadow': 0, 'chat_outBubbleShadow': 0})
    for k, v in explicit.items():
        if k in out: out[k] = v
    # keep text readable on its own background
    pairs = [('chats_unreadCounterText', 'chats_unreadCounter'), ('chats_actionIcon', 'chats_actionBackground'),
             ('chat_goDownButtonCounter', 'chat_goDownButtonCounterBackground'),
             ('chat_messageTextIn', 'chat_inBubble'), ('chat_messageTextOut', 'chat_outBubble'),
             ('chat_messageLinkIn', 'chat_inBubble'), ('chat_messageLinkOut', 'chat_outBubble'),
             ('chat_inTimeText', 'chat_inBubble'), ('chat_outTimeText', 'chat_outBubble'),
             ('actionBarDefaultTitle', 'actionBarDefault'),
             ('windowBackgroundWhiteBlackText', 'windowBackgroundWhite'),
             ('chats_message', 'windowBackgroundWhite'),
             ('chat_messagePanelText', 'chat_messagePanelBackground')]
    report = []
    for fg, bgk in pairs:
        if fg not in out or bgk not in out: continue
        r = contrast(out[fg], out[bgk])
        if r < 3.0 and fg not in ('chat_inTimeText', 'chat_outTimeText', 'chats_message', 'chat_messageLinkIn', 'chat_messageLinkOut'):
            cand = [P['text'], P['bg'], P['surf'], 0xFFFFFFFF, 0xFF000000]
            best = max(cand, key=lambda x: contrast(x, out[bgk]))
            out[fg] = best; r2 = contrast(best, out[bgk]); report.append((fg, round(r, 2), round(r2, 2)))
    return out, report

def render(out):
    # decimal signed 32-bit ARGB, the format Telegram itself writes (hex would be read as RRGGBBAA by some tools)
    sint = lambda v: v - (1 << 32) if v >= (1 << 31) else v
    return ''.join('%s=%d\n' % (k, sint(v)) for k, v in sorted(out.items()))


_TEMPLATES = None
def templates():
    global _TEMPLATES
    if _TEMPLATES is None: _TEMPLATES = load()
    return _TEMPLATES


def main(argv):
    check = '--check' in argv
    files = [a for a in argv if not a.startswith('--')]
    if not files:
        files = sorted(glob.glob(os.path.join(ROOT, '*', '*.tgios-theme')))
    bad = 0
    for f in files:
        raster = '--raster' in argv or os.sep + 'Raster' + os.sep in os.path.abspath(f)
        out, fixes = convert(f, raster)
        dst = f[:-len('.tgios-theme')] + '.attheme'
        text = render(out)
        if check:
            same = os.path.exists(dst) and open(dst, encoding='utf-8').read() == text
            print(('ok      ' if same else 'DIFFERS ') + os.path.relpath(dst, ROOT)); bad += not same
        else:
            open(dst, 'w', encoding='utf-8', newline='\n').write(text)
            print('wrote %s (%d keys)%s' % (os.path.relpath(dst, ROOT), len(out),
                  ''.join('; contrast fix %s %s->%s' % x for x in fixes)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
