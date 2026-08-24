# Catch Blue — Implementation Plan

Companion to `game_design.md`. Covers technology choice, proposed architecture, and a time-boxed milestone plan for Personal Project 1 on the boot.dev DevOps path.

## 1. Where you're starting from

By this point in the DevOps path you've completed: Python basics, Bookbot (a CLI project), Linux + shell scripting, Git, Object-Oriented Programming, and **Build an Asteroids Game — which is built with Pygame**. That last one matters a lot: you've already written a Pygame game loop, handled events, drawn to a screen, and organized game objects as classes. Catch Blue is *mechanically simpler* than Asteroids (turn-based, no physics, no delta-time movement), so the new work is mostly UI (menus, question popups, text) and game-state management, not rendering fundamentals.

## 2. Framework options

| Option | What it is | Pros | Cons |
|---|---|---|---|
| **Pygame** ⭐ | The library you used for Asteroids | You already know it; huge community; handles grid + mouse clicks easily; path to web (pygbag) and .exe (PyInstaller) later | No built-in UI widgets — you write your own buttons/text boxes |
| Terminal / TUI (plain `input()` or Textual) | Text-based version in the terminal | Fastest to build (could halve the estimate); very DevOps-flavored; trivial to test | No real "clicking a grid"; feels like a step back from Asteroids; menus in Textual are their own learning curve |
| Arcade | Modern Pygame alternative (OpenGL-based) | Cleaner API, nice docs | New library to learn for no real benefit at this scale |
| Pyxel | Retro fantasy-console engine | Charming aesthetic, small API | 16-color/lo-fi constraints fight against text-heavy flashcards |
| tkinter | Python's built-in GUI toolkit | Ships with Python; buttons/text entry are *built in* (great for quizzes) | Feels like a form app, not a game; skills don't build on Asteroids |
| Godot / Ren'Py etc. | Full engines | Powerful | Not Python (GDScript) or wrong genre; defeats the "apply my Python" goal |

**Recommendation: Pygame.** It's the only option where week one is spent building the game instead of learning a tool, and it directly reinforces what Asteroids taught. The one honest caveat: Pygame has no widget library, so question popups, buttons, and (especially) fill-in-the-blank text input are things you build yourself. That's good OOP practice, but it's where your hours will go — see §6.

If you'd rather keep this project small and lean into the DevOps identity, the terminal version is the legitimate alternative — but given the GDD's click-a-square design, Pygame is the better fit.

**Settled in M0: the flavor is `pygame-ce`, not upstream `pygame`.** pygame-ce is the community fork that most of the active maintainers moved to in 2023. It's a drop-in — you still write `import pygame`, and every pro/con above holds unchanged. The deciding factor was Python support: upstream's last release is 2.6.1 (Sept 2024), shipping wheels only through cp313, while this machine runs Python 3.14. pygame-ce 2.5.8 ships cp314 wheels and releases on a regular cadence. One rule: never install both into the same venv — they claim the same `pygame` import name and will clobber each other.

## 3. Recommended stack

- **Python 3.14** with `pygame-ce==2.5.8` (see §2), in a `uv`-managed venv. Runtime deps live in `requirements.txt`; test-only deps belong in `requirements-dev.txt`, so the eventual container doesn't ship a test runner. Note the venv is uv-created and therefore has no `pip` — install with `uv pip install <pkg>`, not `python -m pip`.
- Questions stored as **JSON files** in a `data/` folder (no database needed)
- `pytest` for unit-testing the game *logic* (movement rules, answer checking) — a nice DevOps-path touch, and easy if you keep logic separate from rendering. **This is real as of M0:** `tests/test_board.py` covers the grid math and runs fully headless, because `pygame.Rect` works without `pygame.init()` and no window is ever opened. That means it runs in CI with no display attached. `pytest.ini` sets `pythonpath = .` so `tests/` can import top-level modules without any packaging ceremony.
- Distribution: just run it as `.py` for the project submission. Later, `PyInstaller` makes an executable and `pygbag` compiles Pygame to WebAssembly for the browser — both are post-MVP, and this answers the "web app vs executable" unknown in the GDD: **defer it; the code doesn't change either way.**

## 4. Proposed architecture

### Scene/state machine

The biggest structural difference from Asteroids: Catch Blue is a sequence of *modes*, not one continuous loop. Model it as a state machine where each state owns its own event handling and drawing:

```
MENU ──► BOARD ──► QUESTION ──► BOARD ──► ... ──► GAME_OVER ──► MENU
```

One top-level `Game` class runs the loop and delegates to the current state object. Clicking a topic square switches `BOARD → QUESTION`; answering switches back and applies the result (Blue flees or holds).

### Classes (maps to GDD §4)

- `Game` — window, clock, main loop, state switching
- `Cell` — a `NamedTuple` of `(col, row)`. Unpacks and hashes like a plain tuple, but `.col` / `.row` at call sites kills a whole class of transposition bug. *(Built in M0.)*
- `Board` — grid model, **pure logic, no pygame import**. Holds `cols` / `rows`; provides `in_bounds(col, row)` and `cells()`, a generator yielding every `Cell` col-major so the nested loop is written exactly once. Later gains `is_adjacent(a, b)` and occupancy. *(Built in M0; adjacency and occupancy land in M2.)*
- `BoardView` — everything pixel-shaped: `cell_size`, `origin_x` / `origin_y`, `cell_to_rect(cell)`, `pixel_to_cell(x, y) -> Cell | None`, and `draw(screen)`. Holds a reference to its `Board`; the board knows nothing about the view. *(Built in M0.)*
- `Player` — grid position, move validation
- `NPC` (base) → `Blue` (moves *away* from player on wrong answers) and `Red` (moves *toward* player every turn). A greedy "step in the direction that increases/decreases distance" is fine — no pathfinding needed on an open grid.
- `Question` / `QuestionBank` — load JSON, filter by topic and difficulty, track which questions were used
- UI helpers — `Button`, `TextBox` (word-wrapped text rendering), later `TextInput` for fill-in-the-blank

### Grid and screen layout (settled in M0)

**Window: 1280×720, created with the `pygame.SCALED` flag.** 720p fits every laptop panel including old 1366×768 ones, matches what Asteroids used, and leaves a natural side column for HUD. `SCALED` means all code works in fixed 1280×720 logical coordinates while pygame scales the output to the real display — so HiDPI monitors and a future fullscreen toggle cost nothing in layout math.

**Fixed board *region*, derived cell size.** The board occupies a square 640×640 region at origin (40, 40); `cell_size = BOARD_REGION // max(cols, rows)`, and any leftover pixels are absorbed by centring the board inside the region. This is what lets one `BoardView` serve Catch Blue's 5×5 (128px cells, no slack) and Run from Red's 9×9 (71px cells, 1px slack) without the window resizing between modes and without every HUD coordinate moving. For Marathon's unbounded grid, the same region becomes a viewport: hold `cell_size` fixed and scrolling is an offset change rather than a layout rewrite.

**Coordinate order is `(col, row)`, everywhere, forever.** Integer division must use `//`, never `int(x / y)`: `//` floors, so a click left of or above the grid yields a negative index that `in_bounds` rejects, whereas `int()` truncates toward zero and would silently land that click in column 0. Bounds are checked *after* dividing, reusing `Board.in_bounds` rather than a second pixel-space guard.

All layout numbers live in `constants.py` — one definition each, so changing `BOARD_REGION` moves everything consistently.

### Question data format

```json
{
  "id": "bio-042",
  "topic": "biology",
  "difficulty": 2,
  "type": "multiple_choice",
  "prompt": "Which organelle is the site of ATP synthesis?",
  "choices": ["Nucleus", "Mitochondrion", "Ribosome", "Golgi apparatus"],
  "answer_index": 1
}
```

For fill-in-the-blank, use `"type": "fill_blank"` with an `"accepted_answers"` list, and normalize input (lowercase, strip whitespace) before comparing. **Start with multiple-choice only** — clickable answer buttons are far easier in Pygame than a text-input widget, and you can add `fill_blank` as its own milestone.

### Suggested file layout

Files marked ✅ exist as of M0; the rest are still planned.

```
catch_blue/
├── main.py            ✅ init, window, main loop  (becomes a thin entry point once game.py lands)
├── constants.py       ✅ screen + board geometry, colors
├── board.py           ✅ pure logic: Cell, Board
├── board_view.py      ✅ pixel conversions + drawing
├── game.py               Game class + state machine
├── states/               menu.py, board_state.py, question_state.py, game_over.py
├── characters.py         Player, NPC, Blue, Red
├── questions.py          Question, QuestionBank
├── ui.py                 Button, TextBox
├── data/questions/*.json
├── tests/             ✅ test_board.py  (later: test_questions.py)
├── pytest.ini         ✅ pythonpath = .
├── .gitignore         ✅
├── requirements.txt   ✅ runtime only
└── requirements-dev.txt  pytest and friends
```

`board_view.py` and `constants.py` weren't in the original layout — they fell out of the M0 decision to keep pixels out of `board.py`.

## 5. Milestones and time estimates

Estimates assume you're writing most code yourself, are new-ish to coding, and include the debugging time that always comes with "first time building X." Honest range, not best case.

### Phase 1 — Catch Blue MVP

| Milestone | Deliverable | Hours |
|---|---|---|
| ~~M0~~ ✅ | Repo, venv, window opens, empty 5×5 grid drawn — *plus* the pixel↔cell conversions and 25 passing tests | 1–2 |
| M1 | Click detection on squares; player + Blue rendered at opposite corners | 3–5 |
| M2 | Movement rules: adjacency check, player moves on click, Blue's flee logic | 4–6 |
| M3 | Question system: JSON loading, question popup with clickable multiple-choice answers, correct/incorrect flow | 6–10 |
| M4 | Game flow: menu, win condition (click adjacent Blue), optional move-limit loss, game-over screen | 5–8 |
| M5 | Content: write/import a starter question bank with difficulty tags | 3–5 |
| M6 | Polish: playtesting, bug fixes, visual cleanup | 4–8 |
| | **Total** | **~26–44** |

The GDD's gate says "only add Run from Red if Catch Blue lands under 30 hours." That's achievable if you stay multiple-choice-only, keep art to colored rectangles + text, and defer accessibility modes. If you're past 30 hours at M6, ship it — a finished Catch Blue is a better portfolio piece than a half-finished Run from Red.

### Phase 2 — Run from Red (stretch)

| Feature | Hours | Notes |
|---|---|---|
| Escape mode | +8–15 | Mostly reuse: bigger grid, Red's chase logic, turn counter, edge-of-map win check |
| Marathon mode | +10–20 | Adaptive difficulty + scoring is real design work; "unlimited" board means scrolling/camera logic — the single biggest hidden cost in the GDD |
| Fill-in-the-blank input | +3–6 | Custom Pygame text input widget |

### Explicitly deferred (post-project)

Multiplayer, colorblind/low-vision modes (do pick colorblind-safe colors from day one — it's free), web deployment via pygbag, packaged executables.

## 6. Scope traps to watch

1. **Text rendering in Pygame is manual.** `font.render()` gives one line, no wrapping. Budget for a small word-wrap helper early — every question popup depends on it.
2. **Fill-in-the-blank is deceptively expensive** (cursor, backspace, focus, answer normalization). That's why it's a stretch goal, not MVP.
3. **Marathon mode's procedural/unlimited grid** implies a camera system. Everything else in the GDD lives on a fixed screen; this one feature doesn't. Cut it first if hours run long.
4. **Question authoring is a content treadmill.** Timebox it — 20–30 questions is plenty to prove the game works.
5. **Logic/rendering separation** is the difference between a testable project and an untestable one. If `board.py` never imports pygame, you can `pytest` your rules — and that's the line on this project that will impress on the DevOps path. **This is now enforced, not aspirational:** `test_board_module_never_imports_pygame` imports `board` in a subprocess and asserts `pygame` never lands in `sys.modules`. It fails the moment someone reaches for `pygame.Rect` in the wrong file.
6. **`.gitignore` before the first commit, not after.** M0 committed `__pycache__` because the ignore file didn't exist yet; untracking it needed `git rm -r --cached`, since git ignores untracked files only. Bytecode in history is harmless, but the same mistake with a `.env` is not — set this up before adding any file you'd regret.
