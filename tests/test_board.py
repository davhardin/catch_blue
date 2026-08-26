"""Grid logic and pixel<->cell conversions.

No window is opened here: pygame.Rect works without pygame.init(), so these
run headless (in CI, over SSH, wherever).
"""

import subprocess
import sys
from pathlib import Path

import pytest

from board import Board, Cell, get_distance, is_adjacent
from board_view import BoardView
from constants import BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION

# 5x5 divides BOARD_REGION evenly; 9x9 leaves slack the origin has to absorb.
SIZES = [5, 9]


@pytest.fixture(params=SIZES, ids=lambda n: f"{n}x{n}")
def view(request):
    board = Board(request.param, request.param)
    return BoardView(board, BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION)


# --- board.py: pure logic -------------------------------------------------

def test_in_bounds_accepts_every_cell_on_the_grid():
    board = Board(5, 5)
    assert all(board.in_bounds(c.col, c.row) for c in board.cells())


@pytest.mark.parametrize(
    "col,row",
    [(-1, 0), (0, -1), (5, 0), (0, 5), (-1, -1), (5, 5), (99, 99)],
)
def test_in_bounds_rejects_cells_off_the_grid(col, row):
    assert not Board(5, 5).in_bounds(col, row)


def test_in_bounds_is_not_confused_by_a_non_square_board():
    board = Board(cols=9, rows=5)
    assert board.in_bounds(8, 4)
    assert not board.in_bounds(4, 8)  # transposed: valid col, invalid row


def test_cells_yields_every_cell_exactly_once():
    board = Board(cols=9, rows=5)
    cells = list(board.cells())
    assert len(cells) == 45
    assert len(set(cells)) == 45


# --- board.py: adjacency geometry (M2.a) -----------------------------------

@pytest.mark.parametrize(
    "a,b,expected",
    [
        (Cell(0, 0), Cell(0, 0), 0),
        (Cell(0, 0), Cell(1, 0), 1),
        (Cell(0, 0), Cell(0, 1), 1),
        (Cell(0, 0), Cell(1, 1), 2),  # diagonal is two steps, not one
        (Cell(2, 3), Cell(4, 0), 5),
    ],
)
def test_distance_is_manhattan(a, b, expected):
    assert get_distance(a, b) == expected


def test_no_cell_is_adjacent_to_itself():
    assert not any(is_adjacent(c, c) for c in Board(5, 5).cells())


def test_adjacency_is_symmetric():
    cells = list(Board(5, 5).cells())
    for a in cells:
        for b in cells:
            assert is_adjacent(a, b) == is_adjacent(b, a)


def test_diagonal_cells_are_not_adjacent():
    """Adjacency is 4-way orthogonal (m2.md); 8-way creep starts here."""
    assert not is_adjacent(Cell(2, 2), Cell(3, 3))
    assert not is_adjacent(Cell(2, 2), Cell(1, 3))


@pytest.mark.parametrize(
    "cell,count",
    [
        (Cell(0, 0), 2),
        (Cell(4, 4), 2),
        (Cell(2, 0), 3),
        (Cell(0, 2), 3),
        (Cell(2, 2), 4),
    ],
    ids=["corner", "far-corner", "top-edge", "left-edge", "middle"],
)
def test_neighbor_counts_match_position(cell, count):
    assert len(Board(5, 5).neighbors(cell)) == count


def test_every_neighbor_is_on_the_board():
    board = Board(5, 5)
    for cell in board.cells():
        for neighbor in board.neighbors(cell):
            assert board.in_bounds(neighbor.col, neighbor.row)


def test_neighbors_agrees_with_is_adjacent_for_every_pair():
    """One adjacency rule, two views (set-valued and boolean) -- no drift."""
    board = Board(5, 5)
    for a in board.cells():
        neighbors = board.neighbors(a)
        for b in board.cells():
            assert (b in neighbors) == is_adjacent(a, b)


def test_neighbors_is_not_confused_by_a_non_square_board():
    board = Board(cols=9, rows=5)
    assert len(board.neighbors(Cell(2, 4))) == 3  # bottom edge, not interior
    assert len(board.neighbors(Cell(8, 2))) == 3  # right edge


def test_a_one_by_one_board_has_no_neighbors():
    assert Board(1, 1).neighbors(Cell(0, 0)) == set()


# --- board_view.py: conversions -------------------------------------------

def test_round_trip_through_every_cell_centre(view):
    """cell -> rect -> centre pixel -> cell must be the identity."""
    for cell in view.board.cells():
        assert view.pixel_to_cell(*view.cell_to_rect(cell).center) == cell


def test_round_trip_holds_at_the_top_left_pixel_of_each_cell(view):
    """The centre is the easy case; boundaries are where off-by-ones live."""
    for cell in view.board.cells():
        rect = view.cell_to_rect(cell)
        assert view.pixel_to_cell(rect.left, rect.top) == cell


def test_clicks_just_outside_each_edge_return_none(view):
    first = view.cell_to_rect(Cell(0, 0))
    last = view.cell_to_rect(Cell(view.board.cols - 1, view.board.rows - 1))

    assert view.pixel_to_cell(first.left - 1, first.top) is None    # left
    assert view.pixel_to_cell(first.left, first.top - 1) is None    # above
    assert view.pixel_to_cell(last.right, last.top) is None         # right
    assert view.pixel_to_cell(last.left, last.bottom) is None       # below


def test_clicks_far_from_the_board_return_none(view):
    assert view.pixel_to_cell(0, 0) is None
    assert view.pixel_to_cell(10_000, 10_000) is None


def test_cells_tile_without_gaps_or_overlap(view):
    """Neighbouring rects share an edge exactly -- no drift, no seams."""
    for cell in view.board.cells():
        rect = view.cell_to_rect(cell)
        if cell.col + 1 < view.board.cols:
            assert view.cell_to_rect(Cell(cell.col + 1, cell.row)).left == rect.right
        if cell.row + 1 < view.board.rows:
            assert view.cell_to_rect(Cell(cell.col, cell.row + 1)).top == rect.bottom


def test_board_fits_inside_its_region(view):
    first = view.cell_to_rect(Cell(0, 0))
    last = view.cell_to_rect(Cell(view.board.cols - 1, view.board.rows - 1))

    assert first.left >= BOARD_ORIGIN_X
    assert first.top >= BOARD_ORIGIN_Y
    assert last.right <= BOARD_ORIGIN_X + BOARD_REGION
    assert last.bottom <= BOARD_ORIGIN_Y + BOARD_REGION


def test_cells_are_square(view):
    rect = view.cell_to_rect(Cell(0, 0))
    assert rect.width == rect.height


# --- the architectural line ------------------------------------------------

def test_board_module_never_imports_pygame():
    """implementation_plan.md 6.5: board.py stays pure so the rules stay testable.

    Runs in a subprocess because this test file imports board_view, which does
    import pygame -- so checking sys.modules in-process would always fail.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import board, sys; assert 'pygame' not in sys.modules"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
    )
    assert result.returncode == 0, "board.py has picked up a pygame dependency"
