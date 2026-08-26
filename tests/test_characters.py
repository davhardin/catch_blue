"""Characters: starting positions, movement rules, flee logic, and the
drawing contract.

Everything here runs without a window -- characters.py is pygame-free by
design, and the last test makes sure it stays that way.
"""

import subprocess
import sys
from pathlib import Path

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


# --- shape/color: the contract BoardView draws against ---------------------

def test_shapes_are_names_the_view_knows():
    """draw() dispatches on these exact strings; a typo here means an entity
    silently never gets drawn."""
    assert Player.shape == "circle"
    assert Blue.shape == "square"


def test_subclasses_override_the_default_color():
    assert Player.color != Character.color
    assert Blue.color != Character.color
    assert Player.color != Blue.color


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


# --- Blue.flee_step (M2.e) --------------------------------------------------

def test_flee_strictly_increases_distance_when_escape_exists():
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    threat = Cell(2, 3)
    step = blue.flee_step(board, threat)
    assert get_distance(step, threat) > get_distance(blue.cell, threat)


def test_flee_step_chooses_without_moving_blue():
    """flee_step decides; move_to acts. The chooser must not mutate -- that
    split is what lets these tests call it freely."""
    blue = Blue(Cell(2, 2))
    blue.flee_step(Board(5, 5), Cell(2, 3))
    assert blue.cell == Cell(2, 2)


def test_flee_ties_break_deterministically():
    """Threat directly below Blue mid-board: left, right, and up all improve
    distance by exactly 1 (Manhattan). Sorted order must crown the same
    winner every time -- Cell(1, 2), the smallest of the tied three."""
    board = Board(5, 5)
    results = {Blue(Cell(2, 2)).flee_step(board, Cell(2, 3)) for _ in range(10)}
    assert results == {Cell(1, 2)}


def test_flee_is_not_derailed_by_a_worsening_candidate():
    """Regression for the early-return bug: threat two cells west, so east,
    north, and south all improve while west worsens. Meeting the worsening
    candidate mid-scan must not read as "Blue is stuck"."""
    board = Board(5, 5)
    blue = Blue(Cell(2, 2))
    threat = Cell(0, 2)
    step = blue.flee_step(board, threat)
    assert step != blue.cell
    assert get_distance(step, threat) > get_distance(blue.cell, threat)


def test_flee_runs_along_an_edge_not_off_it():
    """Blue against the left wall, threat adjacent below: the wall-hugging
    step up and the step inward both improve; ties sort to Cell(0, 1), so
    Blue runs along the edge."""
    board = Board(5, 5)
    blue = Blue(Cell(0, 2))
    assert blue.flee_step(board, Cell(0, 3)) == Cell(0, 1)


def test_flee_stays_when_cornered():
    """Corner with the threat on the diagonal: both exits move Blue closer,
    so no candidate survives the strict filter. Blue holds still -- and the
    empty-survivors guard, not a max() over nothing, is what answers."""
    board = Board(5, 5)
    assert Blue(Cell(0, 0)).flee_step(board, Cell(1, 1)) == Cell(0, 0)


def test_flee_from_every_position_stays_on_board_and_off_the_threat():
    """Sweep all 600 (blue, threat) pairings on the 5x5. Wherever Blue stands
    and wherever the threat is, the chosen cell is on the board, is never
    the threat's own square, and is reachable in one step or a stand-still.
    m2.md's success check ("never off it, never onto you") as a property."""
    board = Board(5, 5)
    for start in board.cells():
        for threat in board.cells():
            if threat == start:
                continue
            step = Blue(start).flee_step(board, threat)
            assert board.in_bounds(step.col, step.row)
            assert step != threat
            assert step == start or is_adjacent(step, start)


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
