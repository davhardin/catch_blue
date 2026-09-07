from random import Random

from board import Cell, Board, get_distance

class Character():
    shape = "circle"
    color_role = 'character'

    def __init__(self, cell: Cell) -> None:
        self.cell = cell

    def move_to(self, cell: Cell) -> None:
        self.cell = cell

    def legal_moves(self, board: Board, blocked: set[Cell]) -> set[Cell]:
        return board.neighbors(self.cell) - blocked


class Player(Character):
    color_role = 'player'

    @classmethod
    def at_start(cls, board: Board):
        return cls(Cell(0, board.rows - 1))


class Blue(Character):
    shape = "square"
    color_role = 'blue'

    @classmethod
    def at_start(cls, board: Board):
        return cls(Cell(board.cols // 2, board.rows // 2))

    def flee_step(self, board: Board, threat: Cell, rng: Random) -> Cell:
        candidates = self.legal_moves(board, {threat})
        current_distance = get_distance(self.cell, threat)
        survivors = set()
        for candidate in candidates:
            if get_distance(candidate, threat) > current_distance:
                survivors.add(candidate)

        if not survivors:
            return self.cell

        # Every improving orthogonal step adds exactly one to Manhattan distance,
        # so all survivors tie for best. Sort for reproducible seeded choices.
        best_cells = sorted(survivors)
        if len(best_cells) == 1:
            return best_cells[0]

        return rng.choice(best_cells)
