import pygame
from board import Board, Cell
from characters import Character
from game_setup import subtopic_display_name
from constants import LABEL_PADDING
from theme import FLAT

class BoardView:
    def __init__(
        self,
        board: Board,
        origin_x: int,
        origin_y: int,
        region: int,
        *,
        theme=FLAT,
    ):
        self.board = board
        self.cell_size = region // max(board.cols, board.rows)
        self.origin_x = origin_x + (region - self.cell_size * board.cols) // 2
        self.origin_y = origin_y + (region - self.cell_size * board.rows) // 2
        self.cell_lift = theme.cell_lift
        self.lift_step = theme.skin.scale if theme.skin is not None else 1
        self._lifts: dict[Cell, float] = {}

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

    def update(
        self,
        dt_ms: int,
        *,
        hovered: Cell | None,
        selected: Cell | None,
        moves: set[Cell],
        occupied: set[Cell],
        catchable: Cell | None = None,
    ) -> None:
        settings = self.cell_lift
        if settings.rest_px == 0 and settings.hover_px == 0:
            return

        travel = max(settings.rest_px, abs(settings.hover_px - settings.rest_px))
        step = (
            travel * max(0, dt_ms) / settings.pop_ms
            if settings.pop_ms > 0
            else None
        )

        for cell in self.board.cells():
            if cell == selected or (
                cell in occupied and cell != catchable
            ):
                self._lifts.pop(cell, None)
                continue

            if cell in moves or cell == catchable:
                target = (
                    settings.hover_px
                    if cell == hovered
                    else settings.rest_px
                )
            else:
                target = 0
            current = self._lifts.get(cell, 0.0)
            if step is None:
                current = float(target)
            elif current < target:
                current = min(target, current + step)
            elif current > target:
                current = max(target, current - step)

            if current == 0:
                self._lifts.pop(cell, None)
            else:
                self._lifts[cell] = current

    def lift_for(
        self,
        cell: Cell,
        *,
        selected: Cell | None,
        occupied: set[Cell],
        catchable: Cell | None = None,
    ) -> int:
        # Input and answer resolution can change these after this frame's update.
        if cell == selected or (
            cell in occupied and cell != catchable
        ):
            return 0
        value = self._lifts.get(cell, 0.0)
        return int(value / self.lift_step + 0.5) * self.lift_step

    def draw(
        self,
        screen: pygame.Surface,
        hovered: Cell | None,
        entities: list[Character],
        selected: Cell | None,
        moves: set[Cell],
        labels: dict[Cell, tuple[str, str]],
        renderer,
        *,
        catchable: Cell | None = None,
    ) -> None:
        board_size = max(self.board.cols, self.board.rows)
        label_role = renderer.label_role(board_size)
        occupied = {entity.cell for entity in entities}
        lifts = {
            cell: self.lift_for(
                cell,
                selected=selected,
                occupied=occupied,
                catchable=catchable,
            )
            for cell in self.board.cells()
        }
        cells = sorted(lifts, key=lambda cell: (lifts[cell], cell.row, cell.col))

        for cell in cells:
            grid_rect = self.cell_to_rect(cell)
            lift = lifts[cell]
            show_move = cell in moves or (
                renderer.theme.layout.highlight_catchable_cell and cell == catchable
            )
            renderer.cell(screen, grid_rect, 'move' if show_move else 'normal', lift=lift)

            if cell in occupied:
                continue
            label_rect = grid_rect.move(0, -lift).inflate(-2 * LABEL_PADDING, -2 * LABEL_PADDING)
            topic, subtopic = labels[cell]
            display_name = subtopic_display_name(
                topic,
                subtopic,
                board_size=board_size,
            )
            lines = renderer.wrap(
                display_name,
                label_rect.width,
                label_role,
            )
            renderer.wrapped_text(
                screen,
                lines,
                label_rect,
                label_role,
                'label',
            )

        if (renderer.theme.layout.show_cell_hover_ring
                and hovered is not None and hovered in moves):
            renderer.cell(screen, self.cell_to_rect(hovered), 'hover')

        for entity in entities:
            entity_rect = self.cell_to_rect(entity.cell).move(
                0,
                -lifts[entity.cell],
            )
            renderer.sprite(
                screen,
                entity_rect,
                entity.shape,
                entity.color_role,
            )

        if selected is not None:
            renderer.cell(screen, self.cell_to_rect(selected), 'selected')
