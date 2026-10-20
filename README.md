# tg_themes

Custom color themes for Telegram on iOS (`.tgios-theme` files). Each set has its own folder and its own README with the full details.

## Theme sets

| Set | Themes | Style |
|---|---|---|
| [Japan](Japan/README.md) (霧 Kiri) | 6, in three dark/light pairs | Quiet, Zen-inspired colors: ink, mist, moon and snow |
| [Raster](Raster/README.md) | 2, one dark and one light | Minimal Swiss style: black and white with one red accent |

### Japan

| Pair | Dark | Light |
|---|---|---|
| Sumi (ink) | `sumi-yo` | `washi` |
| Kiri (mist) | `koke-giri` | `asagiri` |
| Tsuki (moon and snow) | `sugi-tsuki` | `yuki-dera` |

### Raster

- `raster-weiss`: light
- `raster-schwarz`: dark

## Installation

1. Send a `.tgios-theme` file to yourself (for example, in Saved Messages).
2. Tap the file in Telegram for iOS and choose **Apply**.
3. Optional: to switch between light and dark automatically, apply the light theme first. Then go to **Settings › Appearance › Auto-Night Mode**, choose **Automatic** or **Scheduled**, and pick the dark theme of the same set.

## Repository layout

```
tg_themes/
├── Japan/    six themes + README
└── Raster/   two themes + README
```

## Notes

- The themes change colors only. Telegram fixes the shapes of bubbles and avatars.
- These files are for Telegram on iOS. They do not work in other Telegram apps.
