"""Characters: starting positions, movement rules, flee logic, and the
drawing contract.

Everything here runs without a window -- characters.py is pygame-free by
design, and the last test makes sure it stays that way.
"""

import subprocess
import sys
from pathlib import Path
from random import Random

import pytest

from board import Board, Cell, get_distance, is_adjacent
from characters import Blue, Character, Player

# Same sizes as test_board.py: 5x5 is the shipping board, 9x9 proves nothing
# is hardcoded to 5.
SIZES = [5, 9]


@pytest.fixture(params=SIZES, ids=lambda n: f"{n}x{n}")
def board(request):
    return Board(request.param, request.param)


# --- at_start: positions derived from the board -----------------------------

def test_player_starts_bottom_left(board):
    assert Player.at_start(board).cell == Cell(0, board.rows - 1)


def test_blue_starts_in_the_center(board):
    """Center start (changed in M2): a fleeing character's real resource is
    distance to the walls, and the old corner start began Blue in the very
    square it would eventually be caught in."""
    assert Blue.at_start(board).cell == Cell(board.cols // 2, board.rows // 2)


def test_starting_positions_leave_room_to_play(board):
    """Properties, not coordinates: however the start formulas change, the
    player needs a chase ahead and Blue needs somewhere to run."""
    p = Player.at_start(board).cell
    blue = Blue.at_start(board)
    assert not is_adjacent(p, blue.cell)
    assert get_distance(p, blue.cell) >= max(board.cols, board.rows) // 2
    # Blue opens with full freedom: all four exits on the board and unblocked.
    assert len(blue.legal_moves(board, {p})) == 4


def test_at_start_on_a_non_square_board_does_not_transpose():
    """cols=9, rows=5: a col/row swap in either formula lands on the wrong
    cell (off the board entirely, in the player's case)."""
    board = Board(cols=9, rows=5)
    assert Player.at_start(board).cell == Cell(0, 4)
    assert Blue.at_start(board).cell == Cell(4, 2)


# --- __init__: arbitrary placement -----------------------------------------

def test_characters_can_be_placed_on_any_cell():
    """at_start is a convenience, not a constraint -- __init__ takes any cell."""
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
    assert get_distance(step, threat) > get_distance(blue.cell, threat)


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
        assert get_distance(step, threat) > get_distance(blue.cell, threat)


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

            current_distance = get_distance(start, threat)
            improving = {
                cell
                for cell in board.neighbors(start)
                if cell != threat
                and get_distance(cell, threat) > current_distance
            }

            blue = Blue(start)
            step = blue.flee_step(board, threat, rng)

            assert board.in_bounds(step.col, step.row)
            assert step != threat
            assert step == start or is_adjacent(step, start)
            assert get_distance(step, threat) >= current_distance
            assert blue.cell == start

            if improving:
                assert step in improving
                assert get_distance(step, threat) == current_distance + 1
            else:
                assert step == start


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
