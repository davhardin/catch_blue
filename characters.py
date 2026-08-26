from board import Cell, Board
from constants import BLUE_COLOR, DEFAULT_COLOR, PLAYER_COLOR

class Character():
    shape = "circle"
    color = DEFAULT_COLOR

    def __init__(self, cell: Cell) -> None:
        self.cell = cell

    def move_to(self, cell: Cell) -> None:
        self.cell = cell

    def legal_moves(self, board: Board, blocked: set[Cell]) -> set[Cell]:
        return board.neighbors(self.cell) - blocked


class Player(Character):
    color = PLAYER_COLOR

    @classmethod
    def at_start(cls, board: Board):
        return cls(Cell(0, board.rows - 1))


class Blue(Character):
    shape = "square"
    color = BLUE_COLOR

    @classmethod
    def at_start(cls, board: Board):
        return cls(Cell(board.cols - 1, 0))
