"""Characters: starting positions, construction, and the drawing contract.

Everything here runs without a window -- characters.py is pygame-free by
design, and the last test makes sure it stays that way.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from board import Board, Cell
from characters import Blue, Character, Player

# Same sizes as test_board.py: 5x5 is the shipping board, 9x9 proves nothing
# is hardcoded to 5.
SIZES = [5, 9]


@pytest.fixture(params=SIZES, ids=lambda n: f"{n}x{n}")
def board(request):
    return Board(request.param, request.param)


# --- at_start: corners derived from the board ------------------------------

def test_player_starts_bottom_left(board):
    assert Player.at_start(board).cell == Cell(0, board.rows - 1)


def test_blue_starts_top_right(board):
    assert Blue.at_start(board).cell == Cell(board.cols - 1, 0)


def test_starting_corners_are_opposite(board):
    """Player and Blue must never start adjacent, whatever the board size."""
    p = Player.at_start(board).cell
    b = Blue.at_start(board).cell
    assert abs(p.col - b.col) == board.cols - 1
    assert abs(p.row - b.row) == board.rows - 1


def test_at_start_on_a_non_square_board_does_not_transpose():
    """cols=9, rows=5: a col/row swap in at_start lands off the board."""
    board = Board(cols=9, rows=5)
    assert Player.at_start(board).cell == Cell(0, 4)
    assert Blue.at_start(board).cell == Cell(8, 0)


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
