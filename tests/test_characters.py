"""Characters: starting positions, movement rules, flee logic, and the
drawing contract.

Everything here runs without a window -- characters.py is pygame-free by
design, and the last test makes sure it stays that way.
"""

import subprocess
import sys
from operator import gt, lt
from pathlib import Path
from random import Random

import pytest

from board import Board, Cell
from characters import Blue, Character, Player, best_step
from rules import CatchBlueRules

# Same sizes as test_board.py: 5x5 is the shipping board, 9x9 proves nothing
# is hardcoded to 5.
SIZES = [5, 9]


@pytest.fixture(params=SIZES, ids=lambda n: f"{n}x{n}")
def board(request):
    return Board(request.param, request.param)


# --- start cells: positions derived from the board ---------------------------
#
# Starts left the character classes in the Phase 2 refactor (refactor doc 6a):
# the mode's rules place both characters, so Run from Red can put the Player
# in the center without a mode flag on Player. Catch Blue's placement is what
# at_start used to compute.

def start_cells(board):
    return CatchBlueRules().start_cells(board, Random(0))


def test_player_starts_bottom_left(board):
    player_cell, _ = start_cells(board)
    assert player_cell == Cell(0, board.rows - 1)


def test_blue_starts_in_the_center(board):
    """Center start (changed in M2): a fleeing character's real resource is
    distance to the walls, and the old corner start began Blue in the very
    square it would eventually be caught in."""
    _, blue_cell = start_cells(board)
    assert blue_cell == Cell(board.cols // 2, board.rows // 2)


def test_starting_positions_leave_room_to_play(board):
    """Properties, not coordinates: however the start formulas change, the
    player needs a chase ahead and Blue needs somewhere to run."""
    p, blue_cell = start_cells(board)
    blue = Blue(blue_cell)
    assert blue.cell not in board.neighbors(p)
    assert board.distance(p, blue.cell) >= max(board.cols, board.rows) // 2
    # Blue opens with full freedom: all four exits on the board and unblocked.
    assert len(blue.legal_moves(board, {p})) == 4


def test_start_cells_on_a_non_square_board_do_not_transpose():
    """cols=9, rows=5: a col/row swap in either formula lands on the wrong
    cell (off the board entirely, in the player's case)."""
    board = Board(cols=9, rows=5)
    assert start_cells(board) == (Cell(0, 4), Cell(4, 2))


def test_start_cells_do_not_consume_randomness():
    """Catch Blue's starts are fixed; the rng parameter exists for modes whose
    placement depends on a generated board. Drawing from it here would shift
    every seeded scramble that follows."""
    rng = Random(7)
    before = rng.getstate()
    CatchBlueRules().start_cells(Board(5, 5), rng)
    assert rng.getstate() == before


# --- __init__: arbitrary placement -----------------------------------------

def test_characters_can_be_placed_on_any_cell():
    """The rules' start cells are a convenience, not a constraint -- __init__
    takes any cell."""
    assert Player(Cell(2, 3)).cell == Cell(2, 3)
    assert Blue(Cell(1, 1)).cell == Cell(1, 1)


# --- shape/color role: the contract BoardView draws against ---------------------

def test_shapes_are_names_the_view_knows():
    """draw() dispatches on these exact strings; a typo here means an entity
    silently never gets drawn."""
    assert Player.shape == "circle"
    assert Blue.shape == "square"


def test_subclasses_override_the_default_color_role():
    assert Character.color_role == 'character'
    assert Player.color_role == 'player'
    assert Blue.color_role == 'blue'
    assert Player.color_role != Character.color_role
    assert Blue.color_role != Character.color_role
    assert Player.color_role != Blue.color_role


# --- move_to / legal_moves (M2.b) -------------------------------------------

def test_move_to_is_an_unvalidated_setter():
    """m2.md: legality is the caller's question, asked through legal_moves
    before calling move_to. One gate, not two -- so move_to accepts anything,
    even a teleport across the board."""
    p = Player(Cell(0, 0))
    p.move_to(Cell(4, 4))
    assert p.cell == Cell(4, 4)


def test_legal_moves_with_nothing_blocked_are_the_board_neighbors(board):
    mid = Cell(board.cols // 2, board.rows // 2)
    c = Character(mid)
    assert c.legal_moves(board, set()) == board.neighbors(mid)


def test_legal_moves_respect_the_board_edge():
    board = Board(5, 5)
    assert Player(Cell(0, 0)).legal_moves(board, set()) == {Cell(1, 0), Cell(0, 1)}


def test_a_blocked_neighbor_is_not_a_legal_move():
    """The M2.b success check: a cornered player has 2 moves; Blue standing
    on one of them leaves 1."""
    board = Board(5, 5)
    player = Player(Cell(0, 0))
    blue = Blue(Cell(1, 0))
    assert player.legal_moves(board, {blue.cell}) == {Cell(0, 1)}


def test_blocking_a_distant_cell_changes_nothing():
    board = Board(5, 5)
    player = Player(Cell(2, 2))
    assert player.legal_moves(board, {Cell(4, 4)}) == board.neighbors(Cell(2, 2))


# --- Blue.flee_step (M2.e, M6.b) --------------------------------------------


def test_flee_strictly_increases_distance_when_escape_exists():
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    threat = Cell(2, 3)
    step = blue.flee_step(board, threat, Random(7))
    assert board.distance(step, threat) > board.distance(blue.cell, threat)


def test_flee_step_chooses_without_moving_blue():
    """flee_step decides; move_to acts. Only the RNG may advance."""
    blue = Blue(Cell(2, 2))
    rng = Random(7)

    for _ in range(10):
        blue.flee_step(Board(5, 5), Cell(2, 3), rng)
        assert blue.cell == Cell(2, 2)


def test_flee_ties_choose_only_best_cells_and_can_reach_each():
    """Threat below Blue: left, right, and up all improve by one."""
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    threat = Cell(2, 3)
    expected = {Cell(1, 2), Cell(3, 2), Cell(2, 1)}
    results = set()

    for seed in range(100):
        step = blue.flee_step(board, threat, Random(seed))
        assert step in expected
        results.add(step)

    assert results == expected


def test_same_seed_produces_same_flee_sequence():
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    threat = Cell(2, 3)
    rng_a = Random(42)
    rng_b = Random(42)

    sequence_a = [
        blue.flee_step(board, threat, rng_a)
        for _ in range(20)
    ]
    sequence_b = [
        blue.flee_step(board, threat, rng_b)
        for _ in range(20)
    ]

    assert sequence_a == sequence_b
    assert len(set(sequence_a)) > 1


def test_flee_is_not_derailed_by_a_worsening_candidate():
    """A worsening candidate must not hide the available improving moves."""
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    threat = Cell(0, 2)
    expected = {Cell(3, 2), Cell(2, 1), Cell(2, 3)}

    for seed in range(20):
        step = blue.flee_step(board, threat, Random(seed))
        assert step in expected
        assert board.distance(step, threat) > board.distance(blue.cell, threat)


def test_flee_at_an_edge_chooses_only_improving_neighbors():
    """Against the left wall, both up and inward are valid escapes."""
    board = Board(5, 5)
    blue = Blue(Cell(0, 2))
    threat = Cell(0, 3)
    expected = {Cell(0, 1), Cell(1, 2)}
    results = set()

    for seed in range(100):
        step = blue.flee_step(board, threat, Random(seed))
        assert step in expected
        results.add(step)

    assert results == expected


@pytest.mark.parametrize("seed", range(10))
def test_flee_stays_when_cornered(seed):
    """Both exits reduce distance when the threat is on the diagonal."""
    board = Board(5, 5)
    blue = Blue(Cell(0, 0))

    assert blue.flee_step(board, Cell(1, 1), Random(seed)) == blue.cell


@pytest.mark.parametrize("seed", range(10))
def test_flee_chooses_the_only_improving_candidate(seed):
    board = Board(5, 5)
    blue = Blue(Cell(0, 0))

    assert blue.flee_step(board, Cell(0, 1), Random(seed)) == Cell(1, 0)


@pytest.mark.parametrize(
    "threat",
    [Cell(1, 1), Cell(0, 1)],
    ids=["cornered", "single-escape"],
)
def test_flee_without_a_tie_does_not_consume_randomness(threat):
    blue = Blue(Cell(0, 0))
    rng = Random(7)
    before = rng.getstate()

    blue.flee_step(Board(5, 5), threat, rng)

    assert rng.getstate() == before


@pytest.mark.parametrize("seed", range(10))
def test_flee_from_every_position_stays_on_board_and_off_the_threat(seed):
    """Sweep all 600 distinct pairings, including the full escape contract."""
    board = Board(5, 5)
    rng = Random(seed)

    for start in board.cells():
        for threat in board.cells():
            if threat == start:
                continue

            current_distance = board.distance(start, threat)
            improving = {
                cell
                for cell in board.neighbors(start)
                if cell != threat
                and board.distance(cell, threat) > current_distance
            }

            blue = Blue(start)
            step = blue.flee_step(board, threat, rng)

            assert board.in_bounds(step.col, step.row)
            assert step != threat
            assert step == start or step in board.neighbors(start)
            assert board.distance(step, threat) >= current_distance
            assert blue.cell == start

            if improving:
                assert step in improving
                assert board.distance(step, threat) == current_distance + 1
            else:
                assert step == start


# --- best_step: the chooser Blue, Red, and Yellow share (refactor doc 6b) -----
#
# flee_step is best_step with prefer=gt and the threat blocked; Red's chase is
# the same call with prefer=lt and nothing blocked. The contract Blue's tests
# pin above -- strict improvement, sorted ties, rng only on a real tie, hold
# still when cornered -- has to hold for both directions, so it is tested on
# the function itself here.


def test_best_step_gt_matches_flee_step_everywhere():
    """flee_step is a one-line delegation; a drift between the two would be a
    behaviour change for Blue hiding behind an unchanged test suite."""
    board = Board(5, 5)
    for start in board.cells():
        for threat in board.cells():
            if threat == start:
                continue
            via_blue = Blue(start).flee_step(board, threat, Random(3))
            direct = best_step(
                board, start, threat, Random(3), prefer=gt, blocked={threat},
            )
            assert via_blue == direct


def test_best_step_chases_with_lt_by_strictly_decreasing_distance():
    """Red's direction: every position with a closing move closes by exactly
    one; a position with none (only the target itself adjacent, and the
    target is not blocked) steps onto the target -- that is the catch."""
    board = Board(5, 5)
    rng = Random(1)
    for start in board.cells():
        for target in board.cells():
            if target == start:
                continue
            current = board.distance(start, target)
            step = best_step(
                board, start, target, rng, prefer=lt, blocked=set(),
            )
            assert step in board.neighbors(start)
            assert board.distance(step, target) == current - 1


def test_best_step_lt_lands_on_an_unblocked_target():
    """The 'one argument left out' rule: the chase must not block its target,
    because landing on it is how Red catches (refactor doc 6b)."""
    board = Board(5, 5)
    assert best_step(
        board, Cell(2, 2), Cell(2, 3), Random(0), prefer=lt, blocked=set(),
    ) == Cell(2, 3)


def test_best_step_blocked_cells_are_never_chosen():
    board = Board(5, 5)
    # Chasing (0, 0) from (1, 1): both closing cells blocked -> hold still.
    assert best_step(
        board, Cell(1, 1), Cell(0, 0), Random(0),
        prefer=lt, blocked={Cell(0, 1), Cell(1, 0)},
    ) == Cell(1, 1)


def test_best_step_ties_are_the_sorted_improving_cells_in_both_directions():
    """Sorted for reproducibility: the tie list is the sorted set of cells at
    the best distance, so a seed picks the same cell on every machine."""
    board = Board(5, 5)
    # Flee from a threat below: left, right, up all improve by one.
    flee_results = {
        best_step(board, Cell(2, 2), Cell(2, 3), Random(seed), prefer=gt, blocked={Cell(2, 3)})
        for seed in range(100)
    }
    assert flee_results == {Cell(1, 2), Cell(3, 2), Cell(2, 1)}
    # Chase a target on the diagonal: right and down both close by one.
    chase_results = {
        best_step(board, Cell(1, 1), Cell(3, 3), Random(seed), prefer=lt, blocked=set())
        for seed in range(100)
    }
    assert chase_results == {Cell(2, 1), Cell(1, 2)}


@pytest.mark.parametrize("prefer,target", [(gt, Cell(0, 1)), (lt, Cell(0, 2))], ids=["flee", "chase"])
def test_best_step_without_a_tie_does_not_consume_randomness(prefer, target):
    """One best cell (or none) means no draw from the rng -- the gallery and
    every seeded test depend on Blue's exact consumption, and Red inherits it."""
    rng = Random(7)
    before = rng.getstate()
    best_step(Board(5, 5), Cell(0, 0), target, rng, prefer=prefer, blocked=set())
    assert rng.getstate() == before


def test_best_step_with_a_tie_consumes_randomness_once():
    rng = Random(7)
    before = rng.getstate()
    best_step(Board(5, 5), Cell(2, 2), Cell(2, 3), rng, prefer=gt, blocked={Cell(2, 3)})
    after_one = rng.getstate()
    assert after_one != before
    reference = Random(7)
    reference.choice([1, 2, 3])
    assert after_one == reference.getstate()


def test_best_step_ignores_equal_and_worsening_candidates():
    """Strict improvement only: a candidate at the same distance as the start
    is not a move, so with no strictly better cell the chooser holds still."""
    board = Board(5, 5)
    # (0, 0) chasing a target already adjacent but blocked: (1, 0) closes to 0
    # but is blocked; (0, 1) is at distance 2, worse than the current 1.
    assert best_step(
        board, Cell(0, 0), Cell(1, 0), Random(0), prefer=lt, blocked={Cell(1, 0)},
    ) == Cell(0, 0)


def test_best_step_returns_a_cell_without_moving_anything():
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    step = best_step(board, blue.cell, Cell(2, 3), Random(0), prefer=gt, blocked={Cell(2, 3)})
    assert isinstance(step, Cell)
    assert blue.cell == Cell(2, 2)


# --- the architectural line ------------------------------------------------

def test_characters_module_never_imports_pygame():
    """milestones/m1.md: characters stay pygame-free so the rules stay testable.

    Subprocess for the same reason as the board guard: this test file's own
    imports would pollute an in-process sys.modules check.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import characters, sys; assert 'pygame' not in sys.modules"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
    )
    assert result.returncode == 0, "characters.py has picked up a pygame dependency"
