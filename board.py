from typing import NamedTuple


class Cell(NamedTuple):
    col: int
    row: int


class Board:
    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def cells(self):
        for col in range(self.cols):
            for row in range(self.rows):
                yield Cell(col, row)

    def neighbors(self, cell: Cell) -> set[Cell]:
        offsets = ((+1, 0), (-1, 0), (0, +1), (0, -1))
        return {
            Cell(cell.col + dc, cell.row + dr)
            for dc, dr in offsets
            if self.in_bounds(cell.col + dc, cell.row + dr)
        }

    def distance(self, a: Cell, b: Cell) -> int:
        """Return Manhattan distance on the open orthogonal board."""
        return abs(a.col - b.col) + abs(a.row - b.row)
