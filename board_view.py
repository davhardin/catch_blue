import pygame
from board import Board, Cell
from characters import Character
from game_setup import subtopic_display_name
from constants import LABEL_PADDING

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
        selected: Cell | None,
        moves: set[Cell],
        labels: dict[Cell, tuple[str, str]],
        renderer,
    ) -> None:
        for cell in self.board.cells():
            renderer.cell(screen, self.cell_to_rect(cell), 'move' if cell in moves else 'normal')

        occupied_cells = {entity.cell for entity in entities}
        for cell in self.board.cells():
            if cell in occupied_cells:
                continue
            rect = self.cell_to_rect(cell).inflate(-2 * LABEL_PADDING, -2 * LABEL_PADDING)
            topic, subtopic = labels[cell]
            display_name = subtopic_display_name(topic, subtopic)
            lines = renderer.wrap(display_name, rect.width, 'label')
            renderer.wrapped_text(screen, lines, rect, 'label', 'label')

        if hovered is not None and hovered in moves:
            renderer.cell(screen, self.cell_to_rect(hovered), 'hover')

        for entity in entities:
            renderer.sprite(screen, self.cell_to_rect(entity.cell), entity.shape, entity.color_role)

        if selected is not None:
            renderer.cell(screen, self.cell_to_rect(selected), 'selected')
