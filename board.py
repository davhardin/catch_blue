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
