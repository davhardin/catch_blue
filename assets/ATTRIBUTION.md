# Asset attribution

Every file under `assets/` is listed here with its source and license, the
same rule `data/questions/ATTRIBUTION.md` applies to questions. Nothing lands
in this directory without a line below.

| Directory | What | Source | License | Credit required? |
|---|---|---|---|---|
| `Atkinson_Hyperlegible_Mono/` | Monospace font, variable + static weights | Braille Institute via Google Fonts | SIL Open Font License 1.1 (`OFL.txt` in the folder) | No (OFL asks that the license file ship with the font) |
| `Atkinson_Hyperlegible_Next/` | Proportional font, variable weight. The `static/` instances (Regular 400, Medium 500, SemiBold 600, Bold 700) were generated locally from the variable file with `fonttools varLib.instancer` on 2026-09-06 | Braille Institute via the google/fonts repository (`ofl/atkinsonhyperlegiblenext`) | SIL Open Font License 1.1 (`OFL.txt` in the folder) | No |
| `kenney_ui-pack-pixel-adventure/` | UI Pack — Pixel Adventure 2.0: 9-slice panels, buttons, checkboxes, frames (16 px and 32 px tiles) | Kenney, www.kenney.nl | CC0 1.0 (`License.txt` in the folder) | No (credit "Kenney" is appreciated, not required) |
| `kenney_input-prompts-pixel/` | Input Prompts Pixel 1.0: keyboard / gamepad / mouse glyphs (16 px) | Kenney, www.kenney.nl | CC0 1.0 (`License.txt` in the folder) | No |

Notes

- Only fonts, license files, and the packed tilesheets are tracked. The
  `.gitignore` keeps the `.zip` archives, the per-tile `Tiles/` folders,
  previews, and shortcut files local (about 1,330 files); the tracked set is
  41 files, ~1.2 MB. Anything that later loads an individual tile should
  reference the packed sheet by coordinates instead.
- The OFL forbids selling the fonts on their own and requires the license
  text to accompany them; bundling them inside the game is what it's for.
- A "Credits" line naming Kenney and the Braille Institute on the Game Select
  screen is planned courtesy, not a license condition.
