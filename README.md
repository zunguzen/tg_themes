# tg_themes

Custom color themes for Telegram on iOS (`.tgios-theme` files) and on Android (`.attheme` files). Each set has its own folder and its own README with the full details.

## Installation

Open the link of a theme below on your phone, then tap **Apply**. That is all. The same link works on iPhone and on Android: each theme in Telegram holds both an iOS and an Android file.

To switch between light and dark automatically, apply the light theme first. Then open Auto-Night Mode, choose **Automatic** or **Scheduled**, and pick the dark theme of the same set.

- iPhone: **Settings › Appearance › Auto-Night Mode**
- Android: **Settings › Chat Settings › Auto-Night Mode**

The Android files are converted from the iOS ones, so the themes look very similar but not identical.

## Theme sets

### [Japan](Japan/README.md) (霧 Kiri)

Six quiet, Zen-inspired themes in three dark/light pairs: ink, mist, moon and snow.

| Pair | Dark | Light |
|---|---|---|
| Sumi (ink) | [Sumi-yo](https://t.me/addtheme/sumiyo) | [Washi](https://t.me/addtheme/washi) |
| Kiri (mist) | [Koke-giri](https://t.me/addtheme/kokegiri) | [Asagiri](https://t.me/addtheme/asagiri) |
| Tsuki (moon and snow) | [Sugi-tsuki](https://t.me/addtheme/sugitsuki) | [Yuki-dera](https://t.me/addtheme/yukidera) |

### [Raster](Raster/README.md)

Two minimal themes in the Swiss style: black and white with one red accent.

- Light: [raster-weiss](https://t.me/addtheme/rasterWeiss)
- Dark: [raster-schwarz](https://t.me/addtheme/rasterSchwarz)

## Install from a file

If a link does not work, send the theme file to yourself (for example, in Saved Messages), tap it in Telegram and choose **Apply**. Use the `.tgios-theme` file on iPhone and the `.attheme` file on Android.

## Converter (iOS → Android)

`tools/ios_to_android.py` makes the `.attheme` files from the `.tgios-theme` files. It needs Python 3 and an internet connection (it reads Telegram's list of Android color keys once and keeps it in `tools/.cache`).

```
python3 tools/ios_to_android.py                          # all themes
python3 tools/ios_to_android.py Japan/washi.tgios-theme  # one theme
python3 tools/ios_to_android.py --check                  # do the .attheme files match the .tgios-theme files?
```

Change an iOS theme, run the script, and commit both files. For a new theme in a set whose look should be neutral (like Raster), put it in the `Raster/` folder or add `--raster`.

## Repository layout

```
tg_themes/
├── Japan/    six themes (.tgios-theme and .attheme) + README
├── Raster/   two themes (.tgios-theme and .attheme) + README
└── tools/    ios_to_android.py
```

## Notes

- The themes change colors only. Telegram fixes the shapes of bubbles and avatars.
- `.tgios-theme` files are for Telegram on iOS, `.attheme` files are for Telegram on Android. They do not work in the other app.
