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
- `pytest` for unit-testing the game *logic* (movement rules, answer checking) — a nice DevOps-path touch, and easy if you keep logic separate from rendering. **This is real as of M0:** `tests/test_board.py` covers the grid math and runs fully headless, because `pygame.Rect` works without `pygame.init()` and no window is ever opened. M1 added `tests/test_characters.py` — starting positions, arbitrary placement, and the shape/color contract the view draws against. M2 grew both files: adjacency geometry tables, `legal_moves` with and without blockers, and the full flee contract (steps away, hugs edges, stays when cornered, deterministic on ties, plus a 600-pairing full-board sweep) — 66 tests total, all headless. That means it runs in CI with no display attached. `pytest.ini` sets `pythonpath = .` so `tests/` can import top-level modules without any packaging ceremony.
- Distribution: just run it as `.py` for the project submission. Later, `PyInstaller` makes an executable and `pygbag` compiles Pygame to WebAssembly for the browser — both are post-MVP, and this answers the "web app vs executable" unknown in the GDD: **defer it; the code doesn't change either way.**

## 4. Proposed architecture

### Scene/state machine

The biggest structural difference from Asteroids: Catch Blue is a sequence of *modes*, not one continuous loop. Model it as a state machine where each state owns its own event handling and drawing:

```
MENU ──► BOARD ──► QUESTION ──► BOARD ──► ... ──► GAME_OVER ──► MENU
```

One top-level `Game` class runs the loop and delegates to the current state object. Clicking a topic square switches `BOARD → QUESTION`; answering switches back and applies the result per the turn rules below.

*(Revised 2026-08-31, settled in `milestones/m4.md`: MENU is three screens — Game Select → Subject → Topics — and QUESTION stays an overlay `if` inside the play state rather than a sibling state, since the popup overlays a live board instead of replacing it. Five states total: GAME_SELECT, SUBJECT, TOPICS, PLAY, GAME_OVER.)*

### Turn and question rules (settled 2026-08-25)

- **Movement is 4-way orthogonal for every character.** Player, Blue, and later Red move only left, right, up, or down, one square, within the board. `is_adjacent` / `get_distance` in `board.py` are the single definition (built in M2 — see `milestones/m2.md`).
- **Answer outcomes are asymmetric.** Correct answer: the player moves onto the clicked square; Blue holds still. Incorrect answer: the player stays put; Blue flees. Exactly one side moves per question — the player's progress and Blue's movement are both rationed by answer quality.
- **Catching is question-gated too** *(decided 2026-08-26)*. Clicking adjacent Blue opens a question drawn from the category of Blue's square; correct completes the catch, incorrect gets the standard wrong-answer outcome — the player stays and Blue flees the fumbled grab, breaking adjacency. A playtesting-era evolution is queued in §7: Blue's square temporarily holding a random topic while Blue stands on it.
- **Red's movement trigger is undecided.** Move-on-incorrect-only (mirroring Blue) makes Red gentle; the GDD's original "toward the player every turn" makes Red relentless — very different difficulty curves for Escape and Marathon. Deliberately deferred: decide from game balance once Catch Blue mode is fully playable, not before.
- **Squares have persistent categories; questions rotate.** At game start each square is assigned a question category, fixed for the whole game. The *question* shown for a square is not fixed: once the player answers it — correct or not — and moves on, revisiting that square draws a fresh question from the same category. Implications for M3: the cell → category mapping is game state assigned at setup (not `Board` geometry), and `QuestionBank` needs "give me an unused question from category X" plus a policy for what happens when a category runs dry (recycle oldest is the likely answer — decide in M3). *(Revised 2026-08-31: categories are now two-level — chapter-scale `topic` plus section-scale `subtopic` in the question JSON. Squares are labeled with **subtopics**, drawn visibly on the board so choosing a square is an informed decision; the future menu selects which *topics* are in play; the bank rotates within (topic, subtopic) pools. See `milestones/m3.md` for the full settlement.)*

### Classes (maps to GDD §4)

- `Game` — window, clock, main loop, state switching
- `Cell` — a `NamedTuple` of `(col, row)`. Unpacks and hashes like a plain tuple, but `.col` / `.row` at call sites kills a whole class of transposition bug. *(Built in M0.)*
- `Board` — grid model, **pure logic, no pygame import**. Holds `cols` / `rows`; provides `in_bounds(col, row)` and `cells()`, a generator yielding every `Cell` col-major so the nested loop is written exactly once. *(Built in M0. Adjacency landed in M2 as free functions `is_adjacent` / `get_distance` plus `Board.neighbors`; occupancy is handled as explicit blocked-cell sets passed to the rule functions, not board state — see `milestones/m2.md`.)*
- `BoardView` — everything pixel-shaped: `cell_size`, `origin_x` / `origin_y`, `cell_to_rect(cell)`, `pixel_to_cell(x, y) -> Cell | None`, and `draw(screen)`. Holds a reference to its `Board`; the board knows nothing about the view. *(Built in M0; M1 added entity drawing — dispatch on `shape` — plus hover and selection highlights. M2 added the legal-move tint, fed the same set the click handler validates against — main computes, view paints.)*
- `Character` (base) → `Player`, `Blue` — *(Built in M1, superseding the planned `NPC` base: with two concrete classes in hand the shared surface was visible — a `cell`, plus `shape` and `color` as class-attribute defaults the subclasses override. Pygame-free like `board.py`; `BoardView` renders by dispatching on `shape`. See `milestones/m1.md`.)* Starting positions live in per-subclass `at_start(board)` classmethods — Player in a corner, Blue in the center as of M2 (a fleeing character's real resource is distance-to-walls, and the corner start had Blue beginning in its own checkmate square). Movement (`move_to`, `legal_moves`) and Blue's flee landed in M2: `flee_step` is a pure chooser returning a `Cell` — the caller applies it through `move_to` — greedy, deterministic on ties, and holding still when cornered. Greedy proved enough; no pathfinding on an open grid. `Red` (moves *toward* the player; whether every turn or only on incorrect answers is an open balance question — see the turn rules below) joins as a subclass in Phase 2. **Note for Run from Red:** that mode has only two characters — Player and Red, with the Player taking Blue's fleeing role. So the Player will need to start in the *center* (Blue's spot) when the user selects Run from Red, not the corner: `at_start` as written hard-codes one position per subclass, so Phase 2 needs a way to set the Player's start by mode (parameterize `at_start`, or have the mode/state pass the start cell). Decide the mechanism when Escape mode lands.
- `Question` / `QuestionBank` — load JSON, filter by (topic, subtopic) pair and difficulty, track which questions were used. `subject` and `topic` are snake_case identifiers forming the in-data hierarchy subject → topic → subtopic; `subtopic` is display text drawn verbatim on the board *(hierarchy settled 2026-08-31 — see `milestones/m3.md` and `m5.md`)*. Carries the optional `shuffle` opt-out flag; the *display* order of choices is the play state's business, not the data's (M5.e)
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
  "subject": "anatomy_physiology",
  "topic": "cells",
  "subtopic": "Organelles",
  "difficulty": 2,
  "type": "multiple_choice",
  "prompt": "Which organelle is the site of ATP synthesis?",
  "choices": ["Nucleus", "Mitochondrion", "Ribosome", "Golgi apparatus"],
  "answer_index": 1
}
```

For fill-in-the-blank, use `"type": "fill_blank"` with an `"accepted_answers"` list, and normalize input (lowercase, strip whitespace) before comparing. **Start with multiple-choice only** — clickable answer buttons are far easier in Pygame than a text-input widget, and you can add `fill_blank` as its own milestone.

**Choice order is a display concern, not a data concern** *(settled 2026-09-01 — see `milestones/m5.md` M5.e)*. The game shuffles the choices at ask time, so the stored order is canonical and never load-bearing: new questions may be written answer-first (`answer_index: 0`), which makes files auditable at a glance, and no hand-scrambling ever risks an `answer_index` that silently points at the wrong choice. Questions with positional choices ("all of the above") opt out with an optional `"shuffle": false` field; absent means shuffle.

### Suggested file layout

Files marked ✅ exist; the rest are still planned.

```
catch_blue/
├── main.py            ✅ thin entry point (window init + Game handoff, ~20 lines since M4)
├── constants.py       ✅ screen + board geometry, colors, label styling
├── board.py           ✅ pure logic: Cell, Board
├── board_view.py      ✅ pixel conversions + drawing, incl. subtopic labels
├── game.py            ✅ Game class + state machine  (M4)
├── states/            ✅ menus.py, play.py, game_over.py  (M4; M5 adds Topics scrolling, answer shuffle)
├── game_setup.py      ✅ pure helpers: topic prettify, scrambled cell→pair assignment  (M4, pygame-free)
├── characters.py      ✅ Character, Player, Blue  (Red lands with Phase 2)
├── questions.py       ✅ Question, QuestionBank  (M3: subtopics, pair-scoped rotation; M5: load guards, subject, shuffle flag)
├── ui.py              ✅ Button, TextBox  (M4 adds Checkbox + inactive buttons)
├── data/questions/    ✅ one .json per topic (M5 split; 14 topic files scaffolded, prompts filling in via the treadmill)
├── tests/             ✅ test_board.py, test_characters.py, test_questions.py, test_game_setup.py
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
| ~~M1~~ ✅ | Click → cell with hover + selection highlights; `Character` base class; Player + Blue drawn at opposite corners; 36 tests total | 3–5 |
| ~~M2~~ ✅ | Click-to-move with legal-move highlights, catch detection (`print` for now), Blue's greedy flee behind a debug key, Blue's start moved to center; 66 tests total | 4–6 |
| ~~M3~~ ✅ | Question system: JSON loading, question popup with clickable multiple-choice answers, correct/incorrect flow — *expanded 2026-08-31:* topic/subtopic hierarchy and subtopic labels drawn on the board; 96 tests total | 8–14 |
| ~~M4~~ ✅ | Game flow: state machine, three-screen menu wizard (Game Select → Subject → Topics), win condition (catch adjacent Blue through its question — see §4), 20-move loss, end screens with replay — *scope settled 2026-08-31, see `milestones/m4.md`*; 113 tests total | 8–12 |
| M5 | Content: the real question bank — deep (8+ per subtopic, 200+ questions), curated by David from his study materials and openly licensed banks (CC-attributed — see the curation decision in `milestones/m5.md`), difficulty-tagged 1–3 (tag shipped in the format; grading deferred to playtesting, see §7) — plus data-layer hardening for authoring at scale, the `subject` field (settled, see §7), per-topic file split, runtime answer-choice shuffling before any import (files stay canonical — see §4 and `milestones/m5.md` M5.e), and the Topics screen learning to scroll (list scrolls, Start button stationary). *Scope settled 2026-08-31, shuffle added 2026-09-01; engineering half largely landed as of the 2026-09-01 commit — see `milestones/m5.md`* | 10–16 |
| M6 | Polish: playtesting, bug fixes, visual cleanup | 4–8 |
| | **Total** | **~38–63** |

The GDD's gate says "only add Run from Red if Catch Blue lands under 30 hours." That's achievable if you stay multiple-choice-only, keep art to colored rectangles + text, and defer accessibility modes. If you're past 30 hours at M6, ship it — a finished Catch Blue is a better portfolio piece than a half-finished Run from Red.

*(Gate accounting, settled 2026-08-31: M5's deep bank was chosen deliberately — David tutors A&P, and the game is a study resource for his students, so bank depth and question quality are the product, not scope creep. Content hours are tutoring-practice work, not engineering, so measure the 30-hour gate against build hours only. The engineering total without M5's treadmill remains inside the original envelope; the treadmill runs on its own clock and can spill past the M5 commit — see `milestones/m5.md`.)*

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
4. **Question authoring is a content treadmill.** Timebox it — 20–30 questions is plenty to prove the game works. *(Knowingly overridden 2026-08-31: proving the game works stopped being the goal in M4 — it's a study resource for David's A&P students now, so M5 goes deep on purpose. The 30-hour gate is measured against build hours only; see the gate accounting under the table in §5 and `milestones/m5.md`.)*
5. **Logic/rendering separation** is the difference between a testable project and an untestable one. If `board.py` never imports pygame, you can `pytest` your rules — and that's the line on this project that will impress on the DevOps path. **This is now enforced, not aspirational:** `test_board_module_never_imports_pygame` imports `board` in a subprocess and asserts `pygame` never lands in `sys.modules`. It fails the moment someone reaches for `pygame.Rect` in the wrong file.
6. **`.gitignore` before the first commit, not after.** M0 committed `__pycache__` because the ignore file didn't exist yet; untracking it needed `git rm -r --cached`, since git ignores untracked files only. Bytecode in history is harmless, but the same mistake with a `.env` is not — set this up before adding any file you'd regret.

## 7. Possible changes during playtesting

Knobs deliberately left at their simplest setting until the game is playable end-to-end. Revisit during M6 (or Phase 2 balance work) — none of these are worth tuning against an imagined player.

- **Randomized flee tie-breaks.** Blue currently breaks ties among equally-good escape cells by sorted order — deterministic, which is what makes the flee tests assertable, but learnable: a threat directly below always sends Blue *left*, never up or right. Randomizing the pick among tied candidates would make Blue feel evasive rather than mechanical. Two facts to carry into that change: equal-*distance* sidesteps are impossible (each orthogonal step changes Manhattan distance by exactly ±1 — see the corrected note in `milestones/m2.md` M2.e), so ties among improving candidates are the only randomness that exists to add; and the tests would need to either seed the randomness or assert membership in the tied set instead of an exact cell.
- **Randomized question rotation within a pool.** M3 hands out questions in deterministic load order — testable, but memorizable. The forcing function is topic selection, and it ships in M4's Topics screen: when the user picks which topics are on the board, a game might run on only 1–3 of them, and a fixed rotation becomes obvious fast. Softened somewhat by the bank surviving replays (used-marks carry over, so rotation continues rather than restarts — see `milestones/m4.md`), but a full app restart still opens identically. Switch `next_question` to a shuffled draw (per-(topic, subtopic)-pool shuffle, reshuffle on recycle); same test strategy as randomized flee — seed it or assert membership. (Distinct from M5.e's *answer* shuffle, which randomizes choice order within one question and is settled, not a knob — this knob is about which question comes next.)
- **Randomized cell→category assignment** *(shipped in M4 — settled 2026-08-31)*. Every game start shuffles a balanced cell→pair assignment (pairs cycled to fill the board, then shuffled), driven by an injected `random.Random` so tests can seed it. See `milestones/m4.md`. Question *rotation* (previous entry) is now the only deterministic layer left.
- **Blue's square holds a random category.** Planned evolution of the question-gated catch (§4): while Blue stands on a square, that square temporarily *possesses a random (topic, subtopic) pair* — the catch question could be anything — reverting to the square's assigned pair when Blue moves off. Makes the final catch a test of everything rather than one known category. Build the possession/reversion logic during playtesting once the gated catch is proven in its simple form.
- **Red's movement trigger** (already flagged in §4's turn rules): move-every-turn (relentless) vs move-on-incorrect-only (gentle, mirrors Blue). Deferred until Catch Blue mode is fully playable; this is the main difficulty lever for Escape and Marathon.
- **Move-limit difficulty** *(mechanism settled 2026-08-31, number still a knob)*. M4 ships the loss: 20 moves, every answered question — right or wrong, move or catch — costs one. What remains tunable is the number itself, and whether difficulty presets or user-facing fine-tuning ever expose it. Question difficulty and move budget trade off against each other, so tune only with the full flow playable.
- **Answer feedback on the buttons** *(added 2026-09-01)*. Today the popup resolves inside the click that answers it: `PlayState.handle_events` checks `is_correct`, applies the consequence (move, flee, or the `GameOverState` transition), and tears the popup down — `pending`, `prompt_box`, `answer_buttons` all cleared — before the next frame draws. The player never *sees* which answer was right; they infer it from whether Blue fled. The change: on click, keep the popup up briefly and mark the buttons with a color/border animation — the chosen button flashes green or red, ideally also highlighting the correct answer when the pick was wrong — then resolve. Structurally that's a short *reveal* interlude between answered and resolved: the consequence block (including the end-screen transition on catch or final move) moves out of the click handler and behind a timer, with clicks ignored while the reveal runs. Three things to carry into the build: `Button` currently knows only its own color vs `INACTIVE_BUTTON_COLOR`, so it needs a per-button highlight override; the timer must accumulate in `update` (frame `dt` or `pygame.time.get_ticks()`), never a blocking `pygame.time.wait`, which would freeze the whole loop mid-frame; and the synthetic-click tests assume click → consequence in one step, so the reveal duration wants to be injectable (zero in tests) or the test driver learns to tick past it. For a study tool this is the highest-value knob on the list — "wrong, *and here's the right answer*" is feedback the game currently swallows.
- **Subject → data mechanism** *(settled 2026-08-31 — a `subject` field per question, shipping in M5)*. The topic-from-data principle extended a level up, completing the in-data hierarchy subject → topic → subtopic; `QuestionBank` grows the matching `subjects` / `topics(subject)` rungs. The alternatives lost on drift: a hand-kept subject→topics dict is a second copy of the truth whose failure mode is an invisibly unlisted topic, and subject-as-directory makes location meaningful with nothing inside a misfiled file to check against. Two refinements keep their conveniences without their costs: subject *folders* are welcome as shelves (`data/questions/anatomy_physiology/cells.json` — nominal, not functional; the loader globs everything and the field alone decides), and the menu layer keeps a small *display-name* dict (`anatomy_physiology` → "Anatomy & Physiology", `prettify_topic` fallback) — allowed because it's cosmetic-only: a drifted label costs a label, never reachability. Settled ahead of M5's treadmill so every real question is born with the field. See `milestones/m5.md`.
- **Board size as difficulty.** With Blue starting center, board size scales how much herding a catch requires with no other code changes (5×5 quick, 9×9 patient). If Catch Blue needs difficulty settings, try board size before touching the flee rules.
- **Difficulty-grading the imported bank** *(deferred 2026-09-01)*. The Anson import landed all 1,595 questions at `difficulty: 1` — a default, not a judgment; nothing in the game reads the field yet. Grade during playtesting, when playing the actual questions shows which ones bite: that's also when the tag starts earning its keep, and it matters most for Run from Red, where question difficulty is a core pressure lever rather than Catch Blue's flavoring. Until then the field is honest scaffolding — don't build difficulty-filtered drawing on top of ungraded data.
- **Board labels re-wrap every frame** *(noted 2026-08-31)*. `BoardView.draw` calls `word_wrap` for all 25 cells on every frame at 60fps, even though the labels are static for the whole game. Harmless at this scale — measured in fractions of a millisecond — and not worth complicating the view over. If profiling during M6 polish (or Run from Red's 81-cell board) ever shows it, the fix is caching: pre-render each label to a surface once when the cell map is built, and blit the cached surfaces in `draw`. Don't do it speculatively; a cache is a second copy of the truth, and the one-map rule in `milestones/m3.md` exists for a reason.
- **JSON *syntax* errors crash without a filename** *(decided 2026-08-27)*. `QuestionBank`'s loader enriches *shape* errors (missing field, bad index, wrong type) with the offending filename, but a syntactically broken file — stray comma, single quotes — crashes inside `json.load` with a raw `JSONDecodeError`: line and column, no file named. Deliberately left that way: the IDE flags syntax errors live while editing data files, so the gap only bites if a file is edited outside the IDE. If a bare "Expecting ',' delimiter: line 3 column 5" ever appears at startup (M5's content authoring is the likely moment), this is why — the fix is the same catch-enrich-reraise the loader already applies around `from_dict`, wrapped around the `json.load` call instead. *(Shipped: M5.a built exactly this ahead of the treadmill it protects — the loader now names the file on syntax errors, alongside the duplicate-id and near-collision guards; see `milestones/m5.md`.)*
