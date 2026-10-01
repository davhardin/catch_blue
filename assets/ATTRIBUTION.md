# Asset attribution

The runtime assets retained in this directory are listed below. Keep each
package's license with its assets when redistributing the game.

| Runtime file (relative to `assets/`) | Source | License file | License |
|---|---|---|---|
| `Atkinson_Hyperlegible_Next/static/AtkinsonHyperlegibleNext-Regular.ttf` | Braille Institute via [Google Fonts](https://github.com/google/fonts/tree/main/ofl/atkinsonhyperlegiblenext) | `Atkinson_Hyperlegible_Next/OFL.txt` | SIL Open Font License 1.1 |
| `Atkinson_Hyperlegible_Mono/static/AtkinsonHyperlegibleMono-Regular.ttf` | Braille Institute via [Google Fonts](https://fonts.google.com/specimen/Atkinson+Hyperlegible+Mono) | `Atkinson_Hyperlegible_Mono/OFL.txt` | SIL Open Font License 1.1 |
| `Atkinson_Hyperlegible_Mono/static/AtkinsonHyperlegibleMono-Bold.ttf` | Braille Institute via [Google Fonts](https://fonts.google.com/specimen/Atkinson+Hyperlegible+Mono) | `Atkinson_Hyperlegible_Mono/OFL.txt` | SIL Open Font License 1.1 |
| `kenney_ui-pack-pixel-adventure/Tilesheets/Large tiles/Thick outline/tilemap_packed.png` | Kenney, [UI Pack — Pixel Adventure 2.0](https://kenney.nl/assets/ui-pack-pixel-adventure) | `kenney_ui-pack-pixel-adventure/License.txt` | CC0 1.0 |
| `kenney_pixel-ui-pack/Spritesheet/UIpackSheet_transparent.png` | Kenney, with Lynn Evers, [Pixel UI Pack](https://kenney.nl/assets/pixel-ui-pack) | `kenney_pixel-ui-pack/License.txt` | CC0 1.0 |

## Notes

- The Atkinson Hyperlegible Next Regular (400) static instance was generated
  locally from the variable font using `fonttools varLib.instancer` on
  2026-09-06.
- Both Kenney packed sheets are unmodified. The renderer selects, crops, and
  scales regions at runtime for panels, buttons, and board cells. Correct-answer
  buttons receive a green center fill and a pulsing border tint at runtime.
- The Pixel UI Pack sheet packs 16 px tiles on an 18 px pitch. At load the
  renderer drops the 2 px gaps and joins 3 x 3 tiles into each nine-slice
  panel. Its `9-Slice/` cutouts, magenta-keyed sheet, and preview stay local
  and are not shipped.
- The Game Select screen displays the courtesy credit
  “UI assets: Kenney | Fonts: Braille Institute”. This on-screen credit is
  not a license requirement; the font licenses must still accompany the fonts.
- Unused downloaded archives, font variants, previews, loose tiles, sheets,
  and the input-prompts pack are archived outside the runtime assets tree in
  `catch_blue_local_only/asset_archive/m6-f5/`. That local-only archive is not
  shipped with the game.
- Character sprites are not yet bundled. Characters still use drawn shapes.
