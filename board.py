from typing import NamedTuple

class Cell(NamedTuple):
    col: int
    row: int

def get_distance(a: Cell, b: Cell) -> int:
    return abs(a.col - b.col) + abs(a.row - b.row)

def is_adjacent(a: Cell, b: Cell) -> bool:
    return get_distance(a, b) == 1

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
        neighbors = set()
        offsets = ((+1, 0), (-1, 0), (0, +1), (0, -1))
        candidates = set()
        for dc, dr in offsets:
            candidates.add(Cell(cell.col + dc, cell.row + dr))
        for candidate in candidates:
            if self.in_bounds(candidate.col, candidate.row):
                neighbors.add(candidate)
        return neighbors
