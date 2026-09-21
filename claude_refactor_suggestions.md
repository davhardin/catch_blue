# Catch Blue — Structural Review Before Phase 2

*Claude, 2026-09-20. Read: every module in the repo root and `states/`, the tests that exercise them, `game_design.md`, and §4–§7 of `implementation_plan.md`. Baseline: `pytest` passes 555 tests headless. This is a review of shape, not a bug hunt; the suggestions are sketched as responsibilities and signatures, not code, per `preferences.md`.*

The question behind the review: **what would make Run from Red, Race Green, and Find Yellow additions rather than forks?** Each section ends with which mode the suggestion serves, and §13 sequences them.

*Revised 2026-09-20 after a second agent's review (David relayed it). That review corrected four factual claims (fonts are not shared across renderers; incorrect-answer desaturation is not time-bounded; catches use Manhattan `is_adjacent`, which a maze breaks; label sizing keys on board dimension rather than displayed cell size) and tightened several contracts. Its changes are folded in below and marked **[rev]**. David also settled three things the same day: **Race Green is forward-only** (each move is one row up: straight, up-left, or up-right, so two or three options per cell; Catch Blue, Run from Red, and Find Yellow stay four-way orthogonal); **Race Green's tier policy measures rows to the top**, not Player-to-Green; and **Race Green gets a camera showing five rows at the bottom of the strips**, so strip height can become a difficulty knob. All three are folded into §2a, §5, §7, §8b, §14, and §15. Later the same day David added Kenney's Pixel UI Pack to `assets/` and asked for it as an optional third theme with a key to cycle its four colors; that is §11a, and §13 step 5 and §14 point at it.*

---

## 1. What is already carrying its weight

Worth naming first, because the refactors below should preserve these, not trade them away.

- **The pygame-free core.** `board.py`, `characters.py`, `questions.py`, `theme.py`, and most of `game_setup.py` import no pygame. Every rule test runs without a display. Keep the line where it is: anything new about *rules* (Red's chase, maze generation, Green's advance) belongs on this side.
- **`GameConfig` as the one value that crosses the menu → play boundary.** Replay, Retry, and Main Menu all work by re-running `start_play(bank, config)`. Frozen, validated, testable. Phase 2 should extend this value, not add a second channel.
- **`Renderer` owns every pixel decision; states never call `pygame.draw`.** The theme swap in M6 proved the seam. The per-mode accent color slots into this seam without touching a state.
- **The state machine is minimal and honest.** `Game.step` is twelve lines; states are duck-typed with `update / handle_events / draw`; the `if self.state is state` guard after `update` is the one subtlety and it is commented.
- **`Board` already abstracts adjacency.** `Character.legal_moves` and `Blue.flee_step` go through `board.neighbors`, never through coordinate arithmetic of their own. That single fact is what makes a maze cheap (§5).
- **`BoardView` already separates a fixed pixel *region* from the board's cell count.** The camera (§7) is a change to two methods, not a rewrite.
- **The test suite is behavioral, not structural**, mostly. It drives the real state machine with synthetic clicks. That is what lets the internals move.

---

## 2. The central finding: `PlayState` *is* Catch Blue

`states/play.py` is 575 lines and it is the only place the game's rules live. Reading it with Run from Red in mind, the Catch Blue assumptions are spread across the file rather than gathered in one place:

| Assumption | Where |
|---|---|
| Player starts in a corner, Blue in the center | `__init__` → `Player.at_start`, `Blue.at_start` |
| Blue's cell blocks the player's moves | `__init__`, `_resolve_pending_answer`, `handle_events` (three copies of `legal_moves(board, {self.blue.cell})`) |
| Clicking the NPC when adjacent means "catch" | `handle_events`, the `intent = "catch"` branch and `_catchable_cell` |
| Correct answer: player moves, unless it was a catch | `_resolve_pending_answer` |
| Incorrect answer: NPC flees | `_resolve_pending_answer` → `blue.flee_step` |
| Win = caught; lose = out of moves, or moves < distance | `_resolve_pending_answer` |
| The question comes from the *clicked* square | `handle_events` |
| "Distance" for the tier policy = player-to-Blue | `allowed_tiers`, `handle_events` |
| Result copy: "You caught Blue!" / "Blue got away!" | `states/game_over.py` |
| Starting distance for the Topics screen's tier check | `states/menus.py` `TopicsState._sync_selection` builds a Board and calls both `at_start`s |

Run from Red flips six of those ten. Race Green changes eight. The plan (§5 Phase 2) leaves open whether Run from Red is "a flag on PlayState or a sibling state". My recommendation is **neither**:

- A **flag** means `if self.config.mode == "run_from_red"` at each of the ten sites above. Four modes makes that forty branches in one file, and every branch is a place a later mode is forgotten.
- A **sibling** copies the 400 lines that *don't* change (popup, reveal, pause, HUD, event routing) and then the two drift. The plan already flagged this risk for Race Green and Find Yellow and leaned toward siblings anyway because of the camera and the maze. But the camera lives in `BoardView` and the maze lives in `Board` (§5, §7), so neither forces a second play state.
- A **rules object** gathers those ten decisions into one pygame-free class per mode. `PlayState` keeps the turn loop, the popup, the reveal, the HUD, and asks the rules object at each of the ten points. This is the same move the project already made with `TierPolicy`: a policy value in a slot, chosen by config, tested in isolation.

### 2a. Shape of the rules object

One class per mode, all sharing a surface something like:

- `make_board(settings, rng) -> Board` — Catch Blue returns `Board(n, n)`; Race Green returns a strip board; Find Yellow returns a generated maze. **[rev]** The rng is required, not optional: maze generation is seeded gameplay randomness, and it must be the match's rng so a seed reproduces the whole game.
- `start_cells(board, rng) -> (player_cell, npc_cell)` — replaces the per-subclass `at_start` (§6). Takes the *built* board, because a maze's starts depend on its corridors.
- `validate_setup(board, starts, settings) -> None | reason` — **[rev]** match-time checks that cannot be done from the menu: the two characters are connected, Yellow starts outside the initial viewport (a large maze does not guarantee that by itself), and the shortest catch path does not already exceed the move budget. Catch Blue's implementation is empty.
- `npc_class` (or `make_npc(cell)`) and the `entities` draw order — Red must draw *above* the player on the catching frame, so the order is a rule, not a constant.
- `player_blocked(state) -> set[Cell]` — Blue's cell in Catch Blue. **[rev]** For Run from Red the plan says only that *Red's* moves must not treat the Player's cell as blocked (landing on it is the catch); it does not say the Player may walk onto Red. Default to blocking the Player from Red's cell and record the decision in the M8 doc (§14).
- `click_intent(cell, state) -> Intent | None` — the "is this a catch, a move, or nothing" decision. Today it is a string pair `"catch" / "move"`; make it an enum while it moves. **[rev]** Catch eligibility must come from `board.neighbors`, not `is_adjacent` (§5b).
- `question_cell(target, intent, state) -> Cell` — the plan's open question "which square's question does Run from Red ask" becomes one method with one answer per mode. The answer itself is still open (§14).
- `pressure_distance(state) -> int` — what the tier policy's `distance` means. Player-to-Blue in Catch Blue, player-to-Red in Run from Red. **Race Green: rows to the top** (settled by David 2026-09-20): the Player's row index, since row 0 is the finish and every forward-only move is exactly one row up. David's formulation — the minimum Manhattan distance to the three finish cells — computes the same number, because one finish cell always shares the Player's column. Player-to-Green is not measured. Today `allowed_tiers` and `wanted_tier_for` hard-code `get_distance(player, blue)`.
- `on_correct(state, target, intent)` and `on_incorrect(state)` — the two halves of `_resolve_pending_answer` that differ. Catch Blue: move-or-catch / Blue flees. Run from Red: move / Red chases. Race Green: move / Green advances. Find Yellow: move-or-catch / Yellow flees.
- `outcome(state) -> "win" | "lose" | None` — the terminal check, including the early-loss rule and its mirror, Run from Red's early *win*. **[rev]** Two current behaviors must survive verbatim: a successful catch wins *even on the final move* (`caught or out_of_moves` resolves to win when caught), and a catch does *not* move the Player onto Blue's cell. An outcome check written as "characters overlap" would silently change both. See `states/play.py:351–399`.
- `result_messages` and `accent` — the copy on the end screen and the pixel-theme accent, both data.
- `menu_eligible(settings, bank, topics) -> bool` — **[rev]** replaces the earlier `starting_distance(settings)`, which assumed the starting distance is knowable before the board exists. It is not for a maze, and the Topics screen must not generate a maze on every checkbox toggle or consume gameplay randomness. The menu check answers a weaker question: can the selected content support the mode's *guaranteed* starting tier conditions (for Catch Blue, the known corner-to-center distance; for a maze, the policy-wide tiers with no distance)? The strong check is `validate_setup` above, at match start. `menus.py` then stops importing `Player` and `Blue`.

`state` here means the pygame-free match model of §3b, not `PlayState` itself, so the rules can be unit-tested with a `Board`, two characters, and a seeded `Random` — no clicks, no renderer.

**[rev] Scope for M8.** Build this interface around Catch Blue and Run from Red only. Do not pre-design methods for Green and Yellow; extend the interface when those modes make their actual requirements concrete. Two modes are enough to find the seams, four imagined ones are enough to invent wrong ones.

### 2b. A mode registry, so adding a mode is one entry

A `modes.py` (pygame-free) with a small frozen dataclass per mode — key, display name, rules class, character color role, accent, `active` flag — and a `MODES` mapping. Then:

- `GameSelectState` builds its buttons *from* the registry (§9). Today it hand-places "Catch Blue" and "Run from Red (coming soon)", and the constants file already needed a `MENU_THREE_*` set to fit a third button. Five buttons breaks that pattern.
- `GameConfig.mode` stays a string key (serializable, test-friendly); `PlayState` does `MODES[config.mode].rules`.
- `Palette` gains a color role per character (§6c); the registry names which role each mode's NPC uses.
- **[rev] `accent` is a key, not a color.** Two accent mechanisms are being built side by side for comparison (David, 2026-09-20): a hue remap of the current pixel theme's blue-grey roles (plan §7) and a whole-skin variant from the Pixel UI pack (§11a). The registry entry names the accent (`"red"`, `"green"`, …); `Game.renderer_for(accent)` resolves it to a `Theme` through whichever mechanism the session's base theme uses. Step 4 is written against the key and stays neutral; which mechanism ships is the §14 decision.

*Serves: all three modes. This is the prerequisite for everything else.*

---

## 3. Decomposing `PlayState` even for Catch Blue alone

Independent of modes, three clusters of attributes in `PlayState` always change together, which is the usual sign that they are one object each.

### 3a. The question popup

`prompt_box`, `answer_buttons`, `answer_order`, `hovered_answer`, `popup_rect`, `continue_button`, `reveal`, plus the two builder functions at the top of the file. Eight attributes, all set in one place (`handle_events`, the click branch), all cleared in one place (`_resolve_pending_answer`), all drawn in one block. `AnswerReveal` is already a dataclass; it is the seed of this object.

A `QuestionPopup` would own: `open(question, display_order)`, `hover(pos)`, `answer_at(pos) -> canonical_index | None`, `begin_reveal(canonical_index, duration_ms)`, `wants_continue(pos)`, `update(dt_ms)`, `draw(screen)`, `elapsed_ms`. `PlayState` keeps one attribute, `popup: QuestionPopup | None`, and `pending` shrinks to `(question, target, intent)` as it is now.

Every mode asks questions the same way, so this is the largest block of code the four modes share verbatim.

### 3b. The match model (pure turn logic)

`board`, `player`, the NPC, `moves_remaining`, `moves`, and the two rule-facing halves of `_resolve_pending_answer` — everything that is true about the match whether or not a screen exists. A pygame-free `Match` (or `Turn`) object with `resolve(is_correct, target, intent) -> outcome | None` is what §2a's rules methods act on, and it is what the rule tests should construct directly. Today those tests go through `PlayState`, which is why the suite has 43 references to `state.pending` and 39 to `state.reveal`; after the split, rule tests can drop the reveal choreography entirely.

**[rev] This extraction is a prerequisite for the rules object, and §13 now schedules it first.** The original order delegated to rules in step 4 before the object those rules act on existed. The sequence is: extract Catch Blue's existing turn resolution into `Match` with behavior unchanged, prove it through the existing play screen and tests, *then* introduce the rules interface against it. `Match` alone applies a resolved answer, decrements the counter exactly once, and reports the outcome; `PlayState` decides only *when* the reveal has finished and calls `resolve`. Nothing about move accounting is duplicated on the screen side.

`self.moves` is currently recomputed in three places (`__init__`, top of every `handle_events`, and `_resolve_pending_answer`). **[rev]** Rather than caching it after each move (one more field to keep in sync), make it a derived property on `Match` computed from the characters and the rules' blocked set. It is four set operations; the per-frame cost is nothing and there is no stale-cache bug to write.

### 3c. The cell-topic map

`topic_subtopics`, `cell_topics`, `_refresh_exhausted_cell_topics`, and `assign_cell_topics` from `game_setup.py`. About 70 pygame-free lines that depend only on the bank, the rng, the current allowed tiers, and a set of cells. `assign_cell_topics` already takes *any* iterable of cells, so a maze's corridor cells or two strips' cells work unchanged — as long as this logic is not welded to `PlayState`.

A `CellTopics` object with `assign(cells)`, `refresh(allowed_tiers)`, `__getitem__(cell)`, and `labels()` keeps the "one map" rule from `milestones/m3.md` (one dict is still the truth) while giving §11's label cache a single place to invalidate.

### 3d. Make the input phase explicit

`handle_events` is one loop with three nested phases: reveal active → pending question → board idle. Each `continue`/`return` is a phase transition written as control flow. An explicit phase reads better and, more to the point, lets modes reuse the Asking and Revealing phases untouched while only the Idle phase (the board click, which is where `click_intent` and `question_cell` live) varies. **[rev]** Prefer a phase *derived* from existing fields (`popup is None` → idle; `popup.reveal is None` → asking; else revealing) over three phase objects or an enum field that must be kept in step with them. This item is optional for M8. The `_discard_events_after_reveal` flag and `ButtonAction.blocks_events` stay as they are; they are correct.

*Serves: all modes (3a, 3d), rule testability (3b), Race Green and Find Yellow boards (3c). Required for M8: 3b. Recommended before M8: 3a, 3c. Optional: 3d.*

---

## 4. `Game` and the session

Small plumbing items that Phase 2 will bump into on day one.

### 4a. Put the bank on `Game`

`bank` is threaded through every state constructor and through `show_main_menu(bank)` / `start_play(bank, config)`, while `renderer`, `rng`, `settings`, and `topic_selections` live on `game`. It is process-wide, loaded once in `main.py`, and never varies. Making it `game.bank` removes a parameter from seven constructors and two `Game` methods. Tests already build `Game(bank, ...)`, so nothing changes for them.

### 4b. Name the session

`settings` and `topic_selections` are the player's between-games preferences; `SettingsState` writes `game.settings` directly. As modes arrive, `topic_selections` is already keyed by `(mode, subject)`, and per-mode presets (plan §5) would key `settings` the same way. A `Session` dataclass on `Game` with both fields makes that one change rather than two, and gives the Settings screen one object to edit. See §8b for the "per-mode presets or per-mode interpretation" choice.

### 4c. A `State` protocol and an enter hook

A `typing.Protocol` with `update`, `handle_events`, `draw` costs nothing and documents what `Game.step` relies on. Separately, `PauseState._resume` reaches into `play_state` to null out `pointer_pos`, `hovering`, and `hovered_answer` — another state's privates. If `Game.change_state` called an optional `on_enter()` on the incoming state, `PlayState` would own that reset. `GameOverState` has the same shape (it holds `play_state` to draw under itself; fine) and takes `bank` and `config` it could read from `play_state`.

**[rev]** Of this section only 4a (`game.bank`) is worth doing before M8. `Session` and the protocol are cleanups to do when a concrete need appears (per-mode settings in §8b is the likely one).

*Serves: every new state; per-mode settings.*

---

## 5. `Board`: one class, three shapes

This is the highest-leverage small change in the review, and **[rev]** Race Green's forward-only movement, plus the maze, turns it from "nice" into "necessary": the game now has three different ideas of adjacency (four orthogonal offsets; three *forward* offsets; four offsets minus walls) and two different ideas of distance (Manhattan on an open grid; shortest path over `neighbors` everywhere else), and today both are hard-coded as four orthogonal offsets and Manhattan distance in `board.py`. Every rule already asks the board two questions — `in_bounds` and `neighbors` — and never does its own arithmetic. So the maze and the forward-only strips are **board variants that answer those questions differently**, and `Character`, `Blue.flee_step`, `assign_cell_topics`, and `BoardView.draw` (which iterates `board.cells()`) all keep working.

### 5a. Three things the board owns, kept distinct

**[rev]** Keep bounds, walkability, and adjacency as three separate questions rather than overloading `in_bounds`:

- **Bounds** — `in_bounds(col, row)`: is this inside the rectangle. Stays geometric. `pixel_to_cell` uses it and must keep working on a strip board's gap column (the pointer *is* over a cell; it is just not a walkable one).
- **Walkability** — a new `is_walkable(cell)` (or a `passable` set). Race Green's gap column is in bounds and not walkable. `cells()` yields walkable cells only, so topic assignment, lifts, and labels skip the gap without knowing it exists.
- **Adjacency** — `neighbors(cell)`: walkable, in-bounds cells reachable in one step. This is where the three variants differ: four offsets in Catch Blue, Run from Red, and Find Yellow; **three forward offsets in Race Green** — up, up-left, up-right, so a middle-column cell has three moves and an edge-column cell has two; and in the maze, the four offsets minus any pair separated by a wall. Make the offset set **board data** (an `offsets` tuple the constructor takes, defaulting to the four orthogonal ones) rather than a `diagonal` flag: it covers all three cases with one parameter and no branching. Note that forward-only makes `neighbors` *directed* — (c, r−1) is a neighbor of (c, r) but not the reverse. Nothing in the code relies on symmetry, and the same offsets serve both the Player and Green, so this stays on the board rather than becoming a per-character rule.

### 5b. Adjacency governs catches, not just movement

**[rev]** `is_adjacent` is Manhattan-based and is used for catch eligibility in two places: `_catchable_cell` (`states/play.py:226–229`) and the click branch (`states/play.py:487–491`). In a maze, two cells on opposite sides of a wall are Manhattan-adjacent and would read as catchable. (Race Green, the only diagonal mode, has no catch, so diagonals do not add a second case.) The fix: **catch eligibility is `npc.cell in board.neighbors(player.cell)`**, full stop. `is_adjacent` then has no caller in the rules and can go.

### 5c. Distance is a board method with three implementations

`get_distance` is Manhattan. It is used by Blue's flee, the tier policy's `distance`, and the early-loss rule. **[rev]** It is wrong in two modes for two reasons. In Race Green, movement is directed: a cell two rows *below* is unreachable, not two away, and a cell up-left is one step, not two. In Find Yellow, **Manhattan is wrong because of walls**: two cells one wall apart are Manhattan distance 1 and corridor distance possibly 20. Both are the same fix — the true distance is a shortest path over `neighbors` — and an earlier revision's Chebyshev case (for free 8-way movement) is gone with the forward-only decision. So:

- `Board.distance(a, b)`: Manhattan on the open orthogonal board (Catch Blue, Run from Red) and **one BFS over `neighbors` for both the strips and the maze**. Two implementations, not three. A small cache keyed on `(a, b)` is worth it in the maze because Yellow's flee asks for each candidate. On the strip the rules never actually call it — rows-to-top is the row index — but it must still be correct there, because the default (Manhattan) would silently answer for unreachable cells.
- **Disconnected cells must have a defined answer.** A strip board must not report a finite path across its gap, and a maze generator bug must not produce a silent wrong number. Return `None` (or `math.inf`) and make the early-loss rule and the flee chooser handle it explicitly. `validate_setup` (§2a) rejects a disconnected start.
- `characters.py` calls `board.distance` and stays pure. Blue's flee comment — "every improving step adds exactly one, so all survivors tie" — is a property of the open orthogonal grid; the shared chooser (§6b) should not assume it, but on Catch Blue's board it still holds and the tie-breaking behavior is unchanged.
- **This lands with the rules interface, not with the maze.** Run from Red does not need it, but the rules methods are written once against `board.distance` rather than against `get_distance` and then touched again later. It is a one-line default (Manhattan) at that point; the BFS arrives with Race Green.
- **If BFS is deferred, Manhattan is a *safe* placeholder for the early-loss rule and an *unsafe* one for everything else.** Manhattan is a lower bound on corridor distance, so "moves remaining < Manhattan" never declares a loss wrongly; it only misses positions that are already unwinnable. But Yellow's flee would step away by Manhattan into cells that are closer by corridor, and the distance tier policy would ask tier 3 across a wall. Ship the maze with BFS.

### 5d. The maze

Walls between cells, not blocked cells: corridors are cells, walls are *edges*. A `walls: frozenset[frozenset[Cell]]` (each wall an unordered pair) and a `neighbors` that drops pairs in the set. The generator (recursive backtracker or Prim's, both ~30 lines) is a pure function `generate_maze(cols, rows, rng) -> walls`, in the `board.py` tradition, seeded and testable.

**[rev] The maze is orthogonal (David, 2026-09-20), which keeps it simple.** Walls are defined between orthogonal neighbors, so with four-way movement the wall set *fully* defines adjacency and there is no corner-cutting question to settle. An earlier revision of this section needed a corner rule for diagonal mazes; it is gone.

### 5e. Minor

`Board.neighbors` builds a `candidates` set and then filters it into a second set; a single comprehension over the offsets reads the same and allocates half as much. It is called for every flee candidate, so it is worth the two-line tidy while the method is open anyway.

*Serves: Run from Red (5b, 5c — via the rules interface), Race Green (5a walkability and forward-only offsets, BFS in 5c), Find Yellow (5a, 5b, BFS in 5c, 5d).*

---

## 6. `characters.py`

### 6a. Start cells belong to the mode

`Player.at_start` and `Blue.at_start` hard-code one cell per class. Run from Red wants the *Player* in the center. The plan already names the two options (parameterize `at_start`, or have the mode pass cells); with §2a the answer is the second — `rules.start_cells(board)` — and `at_start` goes away rather than growing a mode argument. Characters take a cell; where it came from is not their concern.

### 6b. One step-chooser, parameterized by direction

`Blue.flee_step` is: candidates = legal moves minus threat; keep those that *increase* distance; sort for determinism; random tie-break; hold still if none. Red's chase is the same with *decrease*; Yellow is Blue. **Green does not need the chooser at all** under forward-only movement: every legal move is one row up, so Green's "step" is a column choice among two or three cells — random, straight, or toward the Player's column, which is cosmetic (§14). One module-level function — something like `best_step(board, from_cell, target, rng, *, prefer, blocked)` where `prefer` is a comparison or a key — and each subclass's method becomes a one-line call. The ties-and-cornering behavior, already tested for Blue, is then tested once and inherited.

Note `flee_step` passes `{threat}` as `blocked`; the chase variant must **not** block the target cell, because landing on it is the catch (plan, Run from Red loss rule). That is the "one argument left out" the plan mentions, and it is exactly the kind of thing that is obvious in a shared function and invisible in a copied one.

**[rev] Compatibility requirement for the shared chooser: preserve tie-breaking and RNG consumption exactly.** Blue sorts survivors and draws from the rng *only* when there are two or more; it consumes nothing when holding still or when one move is best (`characters.py:43–52`). Seeded tests and the deterministic gallery depend on that. The shared function must keep the same sort and the same "only call `rng.choice` on a real tie" rule, and use `board.distance` (§5c) so the same chooser is correct under diagonals and in the maze.

### 6c. Palette roles

`Palette` has `player`, `blue`, and an unused `character` fallback (no concrete class uses the role; `test_characters.py` and `test_theme.py` pin it, so drop it or use it, but decide). Red, Green, and Yellow each need a role. `Renderer.color` is a `getattr` on the palette, so adding three fields is the whole change on the render side; the registry (§2b) names which role each NPC uses. The game design already picks the Okabe-Ito vermillion, bluish green, and yellow; check the contrast against each mode's accented cell color the way M6.f did.

*Serves: Run from Red (6a, 6b), all three (6b, 6c).*

---

## 7. `BoardView`: camera, draw signature, fog

### 7a. The camera is an offset and a visible-cell count

`BoardView` already derives `cell_size = region // max(cols, rows)` and centers slack. For a 9-tall strip or a 20×20 maze that formula *shrinks* cells to fit, which is the opposite of what those modes want. Two additions:

- A constructor parameter for **how many cells the region shows** — as a `(visible_cols, visible_rows)` pair, defaulting to the board's own size so Catch Blue is unchanged. `cell_size` derives from that, not from the board.
- **Race Green's viewport (David, 2026-09-20): five rows visible, starting at the bottom of the strips.** Strip height then becomes a difficulty knob (§8b) with no view change. One piece of arithmetic to settle in the Race Green milestone: the world is *seven* cells wide (3 + gap + 3), so "5 × 5" cannot be literal. With the 800 px region and seven columns, cells are 114 px and five rows are 571 px tall — a 7 × 5 viewport that leaves the bottom of the square region for a HUD line or empty. The alternatives are a narrower gap drawn as a divider rather than a cell column (six columns, 133 px cells) or a wider region. Pick one; the camera code does not care which.
- A **pixel offset** (a `Camera` with `offset` and `region_rect`, or two ints on the view) that `cell_to_rect` subtracts and `pixel_to_cell` adds back. A `follow(cell)` method centers the offset on a cell and clamps so the board edge never scrolls past the region when the board is larger than the view.

`draw` then clips to the region (`renderer.clip` already exists and `TopicsState` uses it for the scroll list) and skips cells whose rect misses the region. `update`'s lift loop can skip them too. Catch Blue's 5×5 has offset zero and is byte-identical in the gallery, which is the regression check.

**[rev] The camera is more than an offset. Explicit requirements, each a test:**

- **Reject pointer positions outside the viewport before converting to a cell.** Today `pixel_to_cell` maps any screen point through the origin; with a larger world, a click on the side panel could land on a valid off-screen cell.
- **Center boards smaller than the viewport, and clamp scrolling per axis.** Race Green's board fits horizontally and scrolls vertically; both strips stay visible side by side; the initial offset shows the bottom five rows, and `follow(player.cell)` moves the view up as the race proceeds. A maze may exceed the viewport on both axes.
- **Cull entities as well as cells**, and account for lift when deciding whether a rect touches the region, so a lifted tile at the viewport edge is not clipped a frame early.
- **Non-scrolling boards must render identically**, including the edge-lift drawing at the region border.
- **Label font and compact-name selection must key on the displayed cell size, not the board's largest dimension.** Today `BoardView.draw` derives both `label_role` and `subtopic_display_name(board_size=…)` from `max(cols, rows)` (`board_view.py:118–147`). A 20-tall maze with 5×5-sized cells would get 9×9 fonts. Key both on `cell_size` (or the visible-cell count), which is what they were standing in for all along.

Build this in Race Green first, as the plan says: rectangular board, no walls, the camera is the only new thing on screen. **[rev]** For the record: a 7 × 9 board would *fit* the existing fixed region without a camera at 88 px cells, the size the 9 × 9 board ships with today. David chose the camera anyway (2026-09-20) so strip height can grow with difficulty, which is the right reason — a mode whose board can be any height needs a viewport, and Race Green is the safest place to build one.

### 7b. Fog in Find Yellow is the camera, plus a placement rule

The design says Yellow is hidden *because* the maze is larger than the screen and the camera follows the player. With 7a, that is already true: off-region cells are not drawn. No fog rule is needed for v1. If a "seen cells" memory is wanted later, it is a `set[Cell]` on the match model that `draw` consults, not a view concern.

**[rev]** A large maze does not by itself put Yellow off-screen. `start_cells` must place Yellow outside the initial viewport and `validate_setup` must check it (§2a), or the reveal-on-discovery moment is lost whenever the generator happens to put Yellow nearby.

### 7c. The draw call

`draw(screen, hovered, entities, selected, moves, labels, renderer, *, catchable)` is seven positionals, and `renderer` is passed per call while `theme` was passed at construction. Either store the renderer on the view (it never changes for the view's lifetime) or pass a small frozen `BoardFrame` (hovered, selected, moves, catchable, entities) per draw. The second is nicer for modes because a mode that has no "catchable" concept just leaves it `None` without touching the signature. `update` has the same parameter list minus two; the same frame value can serve both.

### 7d. Walls need drawing

A maze view needs to draw walls between cells. That is one more `Renderer` primitive (`wall(surface, a_rect, b_rect)` or a per-edge line) and a loop over `board.walls` inside the clip — not a new view class.

*Serves: Race Green (7a, 7c), Find Yellow (7a, 7b, 7d).*

---

## 8. `game_setup.py` and settings

### 8a. Split by concern

The module holds three unrelated things: display-name tables (`SUBJECT_DISPLAY_NAMES`, both subtopic maps, `SUBJECT_TOPIC_ORDERS`, `prettify_topic`), the settings/config domain (`TierPolicy`, `Settings`, `PRESETS`, `GameConfig`), and one board-content function (`assign_cell_topics`). The name tables will grow with every subject and every Vol. 2 topic (the tracker has an open append for two of them); the config types will grow with every mode. Two modules — say `display_names.py` and `config.py` — with `assign_cell_topics` moving next to §3c's `CellTopics`.

### 8b. Per-mode settings: share the type and the widgets, not the meaning

**[rev] The first version of this section recommended keeping `Settings` global and letting each mode reinterpret `board_size` (9 = a 9×9 grid, or a 9-tall strip, or a 9×9 maze). The second review disagreed and it was right.** The Settings screen labels the row "5 x 5 / 7 x 7 / 9 x 9"; those labels would lie in two of the four modes. Race Green specifies 3×9 strips, not strips whose height follows Catch Blue's Easy preset. Find Yellow needs a board larger than the viewport, which none of 5/7/9 is. And the same move budget does not obviously make a viable maze. One setting with several hidden meanings is worse than four honest ones.

The revised recommendation:

- **Share the `Settings` value type, its validation, and the `OptionRow` widgets.** They are mode-agnostic and good.
- **Each registry entry (§2b) declares its own preset table, which rows apply, the supported values, and the labels.** Catch Blue's is the current `PRESETS`. Run from Red's likely shares the tier policy and move limit rows and defaults to 9×9. Race Green's replaces the board-size row with a **strip height** row (9 by default; longer for harder presets, now that the camera makes height free — §7a). `preset_for` keeps deriving the name from the values, per mode.
- **[rev] Race Green's move limit needs a decision.** Under forward-only movement a strip of height H is decided within 2H − 3 questions (H − 1 correct or H − 1 wrong, whichever comes first), so at H = 9 the race ends within 15 questions and a 15-move limit never bites. Either drop the move-limit row from Race Green's settings, or keep it as a *harder* knob and define what happens when it runs out with neither runner at the top (§14).
- **Settle where settings are chosen — before or after the mode — as an explicit UX decision in the M8 doc.** Today Settings is reached from Game Select before a mode exists. The two honest options are a mode selector at the top of the Settings screen, or a Settings button inside each mode's flow (on the Subject or Topics screen). Do not resolve it by giving one value four meanings.
- `Session` (§4b) then holds settings keyed by mode, the same way `topic_selections` already is.

### 8c. Constants

`constants.py` is a flat list of 60 layout numbers and it is already showing strain: the `MENU_THREE_*` trio exists because Game Select gained a third button. Two small moves: group by screen (a few frozen `Layout` dataclasses or just clear sections), and replace fixed button tops with a `stack_buttons(count, gap, height)` helper that returns tops for any count (§9). Also a doc drift: the plan's §4 says the board region is 640×640 at (40, 40); `constants.py` says 800. The code is right; fix the plan when the M8 doc is written.

*Serves: all modes (8b), Game Select with five buttons (8c).*

---

## 9. Menu states

`GameSelectState`, `SubjectState`, `TopicsState`, `SettingsState`, `PauseState`, and `GameOverState` each repeat the same prelude: a `pointer_pos`, a `ButtonAction`, the `blocks_events` early-return that still tracks the pointer, `update_button_lifts` over a tuple of buttons, `renderer.fill`, a centered title. Six copies of ~15 lines, and every new screen (a mode-specific end screen, a "how to play" page) will be a seventh.

- A `MenuState` base (or a `ButtonPanel` helper the states compose) that owns `buttons`, the pointer, the action, the prelude, and a `route_click(pos)` that walks `(button, callback)` pairs. Subclasses declare their buttons and callbacks and override `draw` for anything beyond the buttons. `SettingsState`'s `OptionRow`s and `TopicsState`'s scroll list stay as-is; they are the genuinely different parts.
- **Game Select from the registry** (§2b): a loop over `MODES` producing one button each, inactive when `active` is false, positioned by the stack helper from §8c, plus Settings. Adding Find Yellow to the menu is then zero lines in `menus.py`.
- `TopicsState._sync_selection` builds a `Board` and calls `Player.at_start` and `Blue.at_start` to find the starting distance for the tier check. With §2a it calls `rules.menu_eligible(settings, bank, selected)` and stops importing characters.
- `menus.py` aliases `pointer_position as _menu_pointer_position` and `update_button_lifts as _update_menu_button_lifts`; the other states import them unaliased. Drop the aliases.

*Serves: Game Select for four modes; every future screen.*

---

## 10. `questions.py`

Four items, in order of value.

### 10a. Separate the data from the draw state

`QuestionBank` is two things: an immutable, validated question set (loaded once in `main.py`, shared by every state) and a mutable draw state (`used_ids`, `_pool_orders`) that `PlayState` advances. The mutable half persisting across matches is a feature — "no repeats until the pool is spent" survives Retry and Main Menu — but it is a hidden one, and it means two test files that share a bank share draw state. A `QuestionBank` (data + indexes) and a `QuestionDraw` / `Pools` object (the used set and orders, holding a reference to the bank) makes the persistence explicit: `Game` owns one draw object per session, and a match asks it for questions.

**[rev] Defer this split.** As specified, Green does not answer questions, so no current mode needs a second draw cursor. Do it when a mode does, or when it materially simplifies something being built. Whichever extraction eventually happens (this one, or `CellTopics` in §3c, which touches the same code), these current behaviors are the contract and each should have a test before the code moves:

- Draw history survives Retry and Main Menu.
- One shuffled order per pool and one shared used-id history, as designed in M5/M7.
- Unused eligible fallback-tier questions are drawn before any repeat.
- Easy and far-distance draws never use tier 3.
- A tier-limited restart preserves the excluded tiers' history.
- Cells whose label is still eligible keep it across a restart.
- Replacement labels stay balanced (the `Counter` logic in `_refresh_exhausted_cell_topics`).
- The deliberately retained T3-only-subtopic edge (plan §7, 2026-09-19) stays as it is.

### 10b. Index by pool at load time

`topics()`, `subtopics()`, `available_pools()`, `restart_pools()`, and the candidate build in `next_unused_question` each scan all 2,603 questions. `_refresh_exhausted_cell_topics` calls `available_pools` at init, on every board click, and after every answer. This is fractions of a millisecond and not a performance problem today. It *is* a clarity problem: five methods re-derive the same grouping. A `by_pool: dict[(topic, subtopic), list[Question]]` and `by_topic` built once in the loader replaces the five comprehensions with lookups, and `next_unused_question`'s "build candidates if missing" branch becomes "copy and shuffle the pool".

### 10c. Two recycling policies coexist

`next_question` (recycle this pool when it runs dry) is called only from tests. Production uses `next_unused_question` plus an explicit `restart_pools` when *every* pool is dry — a different policy, chosen deliberately in M5/M7. **[rev]** The first draft said "keep one". Softened: `next_question` is a coherent standalone per-pool-recycling API with its own coverage, and its behavior differs from production on purpose. Document that in its docstring so the next reader does not mistake it for dead code. Deleting it is a separate decision for David, not something to bundle into a structural refactor.

### 10d. The loader

`QuestionBank.__init__` is ~60 lines with validation four levels deep inside the file loop, and three `seen_*` dicts that exist only during loading. Split into `_load_file(path) -> list[Question]` and `_register(question, path)` (the duplicate-id and case-collision checks). `Question` itself is a twelve-line `__init__` that a frozen dataclass would replace, with `from_dict` staying as the validating constructor; `id` and `type` shadow builtins as parameter names, which the dataclass would also clean up. `type` and `subject` are stored but never read at play time; they are fine as data.

*Serves: Race Green (10a), Find Yellow's larger cell count (10b, mildly), general hygiene.*

---

## 11. `Renderer` and per-frame cost

The renderer is in good shape. Three things matter more once boards have 81 cells or scroll, and more again in the browser, where pygbag runs slower than native:

- **The tinted "move" tile is rebuilt every frame per cell.** `Renderer.cell` with the pixel skin creates a `Surface`, nine-slices into it, then runs a `PixelArray.replace` over the whole tile, for every move-highlighted cell, every frame. On a 9×9 that is up to four 88×88 pixel passes per frame plus the catchable cell, and up to eight under diagonal movement. Cache the tinted tile per `(size, style)` on first use; it never changes for a given renderer. **[rev]** To be precise about what is known: the repeated work is *verified by reading the code*; its frame-time impact is *not measured*. It is the most likely per-frame cost on the largest boards and in the browser, and the cache is cheap, but profile before calling it a fix.
- **Board labels re-wrap and re-render every frame.** Already logged in the plan as "don't do it speculatively". With §3c's `CellTopics` owning the map and knowing when it changes, the cache has an owner and an invalidation point, which is what the plan's objection was really about. **[rev]** The cached *surfaces* belong in the view or renderer, not in the pygame-free `CellTopics`; `CellTopics` only exposes a change signal (a version counter, or a callback) that the view uses to drop its cache. On a scrolling maze, only visible cells render anyway (§7a), so this can wait until it shows up in a profile.
- **A renderer per accent, built once.** The accent design in plan §7 needs a `Renderer` built from an accented theme for play screens. The M7 finding already rejected "a state constructs a renderer"; the shape that fits is a small cache on `Game` keyed by accent (`renderer_for(accent)`), with menus using the base renderer and `start_play` picking the mode's. **[rev] Correction:** the first draft claimed the four renderers would share fonts through the existing cache. They would not: `loaded` is a local dict inside `Renderer.__init__` (`render.py:52–61`) and deduplicates within one renderer only. Choose explicitly between a small module-level font cache keyed on `(path, size)` and simply accepting one duplicate font load per cached renderer (about ten font objects each, once per session). Either is fine; the second is fewer lines. **[rev] Also required:** `GameOverState` takes `game.renderer` (`states/game_over.py:22`) while `PauseState` takes `play_state.renderer`. With an accented play renderer the end screen would snap back to blue. It must inherit the play renderer the way Pause does.

Also: `answer_feedback` for an incorrect choice runs `pygame.transform.grayscale` on a subsurface every frame. **[rev]** The first draft said this was bounded by the reveal duration; it is not, because an incorrect answer waits for Continue (`_begin_reveal` sets `duration_ms = None`), so the transform runs until the player clicks. Still one button and one small subsurface, so leave it unless the browser build shows it, but it is the same shape as the move-tile issue and the same cache-on-first-use fix applies.

### 11a. A third theme from the Pixel UI pack, as the accent test-bed **[added 2026-09-20]**

David added `assets/kenney_pixel-ui-pack/` (Kenney, CC0, 2015): one 538×592 sheet of 16 px tiles on an 18 px pitch, with panel and button faces in **blue, green, red, and yellow**, each with a pressed state, in a solid variant and a light-face-with-colored-outline variant, plus tan/grey/brown/white panels, checkboxes, radio dots, sliders, arrows, and cursors. It answers the accent question in §11 with data instead of the hue remap sketched in plan §7: per color, a different set of source rects in the *same* sheet, which is exactly what `Skin.elements` already expresses. The renderer needs no new code path to draw it.

**Shape, and how it fits the refactor order.**

- **One base theme, four derived variants, all additive.** A `UI_BLUE` theme from the new sheet, then green, red, and yellow by `replace` on the palette (the accent roles: `background`, `cell`, `cell_move`, `button`, `button_inactive`, `highlight`) and on the element table (the color's column of rects). Fonts, lifts, layout, reveal, and `board_label_sizes` are taken from `PIXEL` unchanged, so the variants differ from today's look only in skin and palette, and the theme-fit numbers carry over. Build the palettes with `replace(PIXEL.palette, ...)` so the per-character roles step 3 adds (§6c) flow into the variants without a second edit. `FLAT` and `PIXEL` are not touched, which keeps both galleries byte-identical — the regression rule every step in §13 relies on.
- **Register all four in `THEMES`.** `--theme` and `tools/gallery.py` then cover each variant for free, and the gallery gains one board per variant, which is the same extension the accent note in plan §7 already asks for.
- **This can land at any point in §13** — before step 1 or after step 5 — because it touches only `theme.py`, the asset folder, and the gallery. It is the safest thing to build while the refactor is in flight, on the condition that it stays additive: no edits to the existing theme constants, no changes to `Renderer`'s draw primitives.
- **The cycling key.** Handled once in `Game.step` before events reach the state, so it works on every screen; a bracket key or function key, not Escape (pause). It cycles only among the four variants, never into flat or pixel, so widget geometry under the pointer never changes. What the press *does* has to respect §11's design: production will build one renderer per accent through a `renderer_for(accent)` cache on `Game`, chosen at `start_play`. The key should not become a second mechanism. Two honest options:
  - **Menu-only cycling, rebuild the state.** The key sets a session-level theme override and rebuilds the current *menu* state, which the states already support (Back rebuilds from `Game`-held values, m7.md). During play the key is ignored; the next `start_play` picks up the override through `renderer_for`. Zero conflict with the refactor, and all four looks are still reachable in one session. **Recommended.**
  - **In-place retheme.** A `Renderer.retheme(theme)` that swaps palette and reloads the skin while keeping fonts (legal because the four variants share fonts). Works mid-game, since every held reference sees the new look on the next frame, but it makes renderers mutable, which the per-accent cache assumes they are not. Only if mid-game cycling turns out to matter for the evaluation.
- **What the key is not.** A test aid for choosing the look. When the accent becomes mode-driven (step 5), the key is deleted or hidden behind a dev flag; a shipped hotkey that recolors the game would confuse students.
- **`GameOverState` must inherit the play renderer** (§11's correction) before any of this is judged, or the end screen snaps back to the base look on every evaluation game.

**Decisions to make while building it, not before.**

- **Solid or outline per element.** Outline for cells: the light face keeps subtopic labels legible and keeps the Blue character visible on a blue board and Yellow on a yellow one; solid faces for buttons and the HUD panel, where text is short. Dark label text on the solid orange-red face is marginal, and the pack's red is close to the Okabe-Ito vermillion planned for Red, so Red on a solid red cell is the case to check first.
- **Scale and insets.** Current slices are 32 px at scale 2; these are 16 px, so expect scale 3 or 4 and insets of two to four source pixels. The corner tile is 16 px, but the drawn border is a few pixels of it; keep insets small, as today's 5 px ones are. Run `tools/theme_fit.py` at each board size once the label band is known.
- **The move-cell tint assumes the palette matches the sheet.** `Renderer.cell` highlights a legal move by nine-slicing `cell.move` into a scratch surface and pixel-replacing the palette's `cell` color with `cell_move` (`render.py:233–238`). That only works when `palette.cell` is *exactly* the sheet's face color, as it is for the Pixel Adventure sheet today. For each new variant either sample the face pixel into the palette, or point `cell.move` at a distinct rect (the pack's pressed or outline face) and let the replace be a no-op. Otherwise move highlighting silently disappears on the new theme. The same applies to the remap accents: after a hue shift, `palette.cell` must be the *shifted* face color.
- **Style clash.** The new pack has soft bevels and no outline; the Pixel Adventure sheet has thick dark outlines. Do not mix them on one screen: this is a whole-skin alternative to `PIXEL`, not a supplement. Its blue-grey "space" tile is close to today's cell color, so Catch Blue's look survives the swap.

**Housekeeping before it is committed.** `.gitignore` excludes `Tiles/` and previews but not `9-Slice/` or the magenta-keyed sheet; commit the transparent sheet and the license only, add the rest to the ignore list, keep the 48×48 cutouts locally for measuring rects, and add a row to `assets/ATTRIBUTION.md`. `assets/` ships in the web build, so the sheet's 40 KB is the only cost there.

**Tests.** Each variant's element rects lie inside the sheet; each variant has every element name the renderer looks up; the gallery renders a board per variant; the pygame-free guard on `theme.py` and the AST guard on `ui.py` are unchanged.

*Serves: Run from Red (9×9 default), both camera modes, the web build; §11a serves the accent for every mode and can be built now.*

---

## 12. Small cleanups

Not worth their own section; worth a pass while the files are open.

- `PlayState.draw` positions the move counter at a literal `(SIDE_PANEL_LEFT, 50)`; every other HUD coordinate comes from `constants.py`.
- `build_question_popup`'s answer-button height `44` and gap `12` are literals; `states/game_over.py` defines its own `BUTTON_HEIGHT = 60` and `BUTTON_GAP = 24` at module level while `PauseState` uses `MENU_BUTTON_HEIGHT`/`MENU_BUTTON_GAP` for the same visual role.
- `Game.__init__` sets `self.fps = 60` as an instance attribute; it is a constant.
- `characters.py`: `class Character():` — drop the empty parens; `Character.legal_moves` type-hints `blocked: set[Cell]` but callers pass set literals and `frozenset` would document that it is not mutated.
- `board_view.py` import order is inconsistent with the rest of the repo (stdlib, third-party, local, blank lines between).
- `GameConfig` and the reveal `intent` use bare strings (`"catch_blue"`, `"catch"`, `"move"`, `"win"`, `"lose"`); `StrEnum` is already in use for `TierPolicy` and reads better in the rules object.
- `ui.Button.__init__` mutates the `rect` it was handed (`self.rect.height = ...`); callers build fresh rects so it is harmless today, but `OptionRow` copies its rect defensively for the same reason — pick one convention.
- `tests/test_play.py` and `test_pixel_layout.py` reach into `state._discard_events_after_reveal`, and `test_menu_layout.py` into `state._set_scroll_offset`; after §3, prefer driving those through events so the underscore stays meaningful.

---

## 13. Suggested order, and how each mode depends on it

**[rev] Revised after the second review.** The original ten steps front-loaded every abstraction before M8. The revised order makes only what Run from Red actually depends on a prerequisite, schedules the match-model extraction explicitly (it was implied before), and moves board generalization to where diagonals and the maze need it — except `board.distance` and adjacency-based catches, which land with the rules interface because the rules are written against them (§5b, §5c).

Each step should leave the suite green and the flat gallery byte-identical.

**Status (2026-09-20):** steps 1–4 landed and were reviewed one at a time; both galleries stayed byte-identical to `*-m7-close` throughout, and the suite was re-swept to the new surface at the end of step 4 (567 tests). The `MENU_THREE_*` constants were deleted in that sweep. Step 5 is `milestones/m8.md`.

| Step | Change | Sections | Status for M8 |
|---|---|---|---|
| 1 | Extract Catch Blue's turn logic into a pure `Match`, behavior unchanged; `game.bank` | 3b, 4a | **prerequisite** |
| 2 | Extract `QuestionPopup` and `CellTopics`, as two separate behavior-preserving changes | 3a, 3c | recommended before M8; each is independently revertible |
| 3 | `Board.distance` (Manhattan default, BFS hook), catches via `board.neighbors`, tidy `neighbors`; shared step-chooser with RNG-compatibility tests; start cells from outside; palette roles | 5b, 5c, 5e, 6 | **prerequisite** (small) |
| 4 | Minimal mode registry + rules interface built around Catch Blue and Run from Red only; `PlayState` delegates at the ten sites; Game Select from the registry; per-mode preset tables; `GameOverState` inherits the play renderer | 2, 8b, 9, 11 | **prerequisite** |
| 5 | **Run from Red** as M8: `Red`, its rules, end-screen copy, accent + renderer-per-accent cache; both accent mechanisms — the hue remap of `PIXEL` (plan §7) and the Pixel UI variants with their cycling key (§11a) — are built side by side in this milestone for comparison and can land at any step, being additive | — | the milestone |
| 6 | Walkability + `offsets` on `Board` (forward-only strips); BFS `distance`; camera in `BoardView` with the §7a requirements, five rows visible from the bottom; `BoardFrame` draw value; label sizing by cell size | 5a, 5c, 7 | with Race Green |
| 7 | **Race Green** | — | — |
| 8 | Maze generator, walls, BFS distance with disconnected handling, placement validation, wall drawing | 5c, 5d, 7b, 7d | with Find Yellow |
| 9 | **Find Yellow** | — | — |
| any | `Session`, `State` protocol, menu base, explicit input phases, `questions.py` loader split and pool index, bank/draw split, `game_setup.py` split, constants regroup, move-tile cache | 3d, 4b, 4c, 8a, 8c, 9, 10, 11 | separate cleanups; do each when a concrete need appears or the file is open anyway |

Two notes on testing through this:

- The rule tests (`test_play.py`, `test_m7_flow.py`, `test_tier_policy.py`'s flow half) will need attribute renames at steps 1, 2, and 4, because they read `state.blue`, `state.pending`, `state.reveal` directly. That is the cost of those tests being behavioral-through-`PlayState` rather than behavioral-through-the-match-model. Keep thin read-only properties on `PlayState` (`blue`, `pending`) for one milestone so the tests move one at a time rather than all at once.
- The gallery (`tools/gallery.py`) is the visual regression for steps 2, 5, 6, and the move-tile cache: flat must diff to nothing; pixel changes only where the change is intended. Extend it with one board per mode as each mode lands, as the plan's accent note already suggests.

---

## 14. Gameplay decisions this document must leave open **[rev]**

Several sketches above read as settled mechanics. They are not; each is David's call, for the relevant milestone doc. The rules interface should make each one a single method so the decision has one home.

- **Can the Player move onto Red's cell?** Red landing on the Player is the catch; that does not imply the reverse. Default recommendation: block it.
- ~~Does Green always step straight up?~~ **Mostly settled by forward-only (2026-09-20):** every Green move is one row up, so only the column is open — random, straight, or toward the Player's column. Cosmetic; pick in the Race Green doc.
- **Race Green's move limit.** Drop the row, or keep it and define the outcome when moves run out with neither runner at the top (§8b).
- **Race Green's viewport width.** Seven columns cannot show as "5 × 5"; choose between a 7 × 5 view at 114 px cells, a divider-style gap, or a wider region (§7a).
- ~~Does Green's question difficulty rise near the finish?~~ **Settled 2026-09-20 (David):** Race Green's distance tier policy measures the Player's distance to the top of the grid, not Player-to-Green. Under the `distance` policy that means tier 3 on the last row or two before the finish, tier 2 two rows out, tiers 1 and 2 beyond. Because every move is one row up, the difficulty curve is fixed by the strip height and cannot be dodged.
- **Which square supplies Run from Red's questions?** The plan leaves it open. The square fled to, or Red's square, are the two candidates.
- **Where settings are chosen** — before or after the mode (§8b).
- **Which accent mechanism ships.** Both are being built (David, 2026-09-20): hue-remapped accents on the current `PIXEL` theme, and the Pixel UI third theme with four color variants (§11a). Compare them in the gallery, one board per accent per mechanism, at the end of M8. The loser is deleted rather than kept as an option, the cycling key goes away either way, and plan §7 and `assets/ATTRIBUTION.md` are updated to match the winner.

---

## 15. Movement rules by mode, in one place **[rev]**

Settled by David on 2026-09-20, after two revisions in one day (free diagonals in two modes → diagonals in Race Green only → forward-only in Race Green):

| Mode | Moves from a cell | `offsets` | `distance` |
|---|---|---|---|
| Catch Blue | four orthogonal neighbors | (±1, 0), (0, ±1) | Manhattan |
| Run from Red | same | same | Manhattan |
| Race Green | **forward only**: up, up-left, up-right; 2 or 3 options | (0, −1), (−1, −1), (+1, −1) | BFS (rules use the row index) |
| Find Yellow | four orthogonal neighbors minus walls | (±1, 0), (0, ±1), filtered by `walls` | BFS |

What forward-only does to Race Green, beyond §5:

- **Every move is progress.** The Player cannot retreat or stall, so the race is decided within 2H − 3 questions on a strip of height H (§8b), and the only strategic choice is *which subtopic to answer next* among the two or three forward cells. That makes the forward cells' labels the most consequential labels in the game; the compact-name table and label-size audit should be run on the Race Green cell size early.
- **Rows-to-top is exact**, not an estimate: the Player at row r needs exactly r correct answers. David's min-Manhattan-to-the-three-finish-cells formula gives r too, because one finish cell shares the Player's column; the row index is the cheaper spelling.
- **Green needs no chooser** (§6b); its move is a column choice.
- **No catch, no blocking.** Green is on the other strip and nothing ever occupies a Player-reachable cell, so `player_blocked` is empty and `click_intent` is only ever "move".
- **The strip gap is not walkable** (§5a), so no neighbor relation reaches across it; forward offsets keep runners in their own strip without any extra rule.
- **Find Yellow is orthogonal and still needs BFS**, because walls break Manhattan regardless of diagonals (§5c). No diagonals there means no corner-cutting rule.
- `game_design.md` §2–3 now record the forward-only rule, the five-row viewport, per-mode distance for the tier policy, and strip height as a difficulty knob; the two open Race Green questions (move limit, viewport width) sit in its §5 Unknowns.

---

## 16. What I would *not* do

- **Do not split `PlayState` into four sibling states.** The differences between modes are rules and board shape; the view and the popup are the same. Siblings look simpler on day one and cost every fix four times after.
- **Do not build a general entity or component system.** Two characters, one board, one popup. The rules object is as much abstraction as four modes need.
- **Do not add the label cache or the pool index for speed.** Add them, if at all, for the clarity reasons above; the profiler has not asked for either yet. The move-tile cache is the exception, because it is a per-frame allocation loop on the largest board.
- **Do not move the name tables to JSON.** They are small, typed, and tested in Python; a data file would trade an import for a loader and a schema.
