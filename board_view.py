import pygame
from board import Board, Cell
from characters import Character
from constants import CELL_COLOR, LINE_COLOR, LINE_WIDTH, SELECTED_LINE_COLOR

class BoardView:
    def __init__(self,
        board: Board, origin_x: int, origin_y: int, region: int
    ):
        self.board = board
        self.cell_size = region // max(board.cols, board.rows)
        self.origin_x = origin_x + (region - self.cell_size * board.cols) // 2
        self.origin_y = origin_y + (region - self.cell_size * board.rows) // 2

    def cell_to_rect(self, cell: Cell) -> pygame.Rect:
        return pygame.Rect(
            self.origin_x + cell.col * self.cell_size,
            self.origin_y + cell.row * self.cell_size,
            self.cell_size,
            self.cell_size
        )

    def pixel_to_cell(self, x: int, y: int) -> Cell | None:
        col = (x - self.origin_x) // self.cell_size
        row = (y - self.origin_y) // self.cell_size
        if self.board.in_bounds(col, row):
            return Cell(col, row)
        return None

    def draw(
        self,
        screen: pygame.Surface,
        hovered: Cell | None,
        entities: list[Character],
        selected: Cell| None) -> None:
        for cell in self.board.cells():
            rect = self.cell_to_rect(cell)
            pygame.draw.rect(screen, CELL_COLOR, rect)
            pygame.draw.rect(screen, LINE_COLOR, rect, width=LINE_WIDTH)

        if hovered is not None:
            hov_rect = self.cell_to_rect(hovered)
            pygame.draw.rect(screen, LINE_COLOR, hov_rect, width=LINE_WIDTH*4)

        for e in entities:
            rect = self.cell_to_rect(e.cell)
            margin = self.cell_size // 6
            if e.shape == "circle":
                pygame.draw.circle(screen, e.color, rect.center, margin)
            elif e.shape == "square":
                pygame.draw.rect(screen, e.color, rect.inflate(-3 * margin, -3 * margin))

        if selected is not None:
            sel_rect = self.cell_to_rect(selected)
            pygame.draw.rect(screen, SELECTED_LINE_COLOR, sel_rect, width=LINE_WIDTH*4)
