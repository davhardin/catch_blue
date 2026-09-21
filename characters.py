from collections.abc import Callable, Set
from operator import gt
from random import Random

from board import Board, Cell


def best_step(
    board: Board,
    from_cell: Cell,
    target: Cell,
    rng: Random,
    *,
    prefer: Callable[[int, int], bool],
    blocked: Set[Cell],
) -> Cell:
    """Choose a strictly improving step using a strict distance comparator.

    prefer(candidate_distance, best_distance) is gt for fleeing or lt
    for chasing. Randomness is used only for tied best steps.
    """
    best_distance = board.distance(from_cell, target)
    best_cells: list[Cell] = []

    for candidate in sorted(board.neighbors(from_cell) - blocked):
        distance = board.distance(candidate, target)
        if prefer(distance, best_distance):
            best_distance = distance
            best_cells = [candidate]
        elif best_cells and distance == best_distance:
            best_cells.append(candidate)

    if not best_cells:
        return from_cell
    if len(best_cells) == 1:
        return best_cells[0]
    return rng.choice(best_cells)


class Character:
    shape = "circle"
    color_role = 'character'

    def __init__(self, cell: Cell) -> None:
        self.cell = cell

    def move_to(self, cell: Cell) -> None:
        self.cell = cell

    def legal_moves(self, board: Board, blocked: Set[Cell]) -> set[Cell]:
        return board.neighbors(self.cell) - blocked


class Player(Character):
    color_role = 'player'


class Blue(Character):
    shape = "square"
    color_role = 'blue'

    def flee_step(self, board: Board, threat: Cell, rng: Random) -> Cell:
        return best_step(
            board,
            self.cell,
            threat,
            rng,
            prefer=gt,
            blocked={threat},
        )
