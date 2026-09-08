import pygame

from theme import Alignment, CellLift


class TextBox:
    def __init__(self, text, renderer, font_role, x, y, width, color_role=None):
        self.text = text
        self.renderer = renderer
        self.font_role = font_role
        self.color_role = color_role
        self.x = x
        self.y = y
        self.width = width
        self.lines = renderer.wrap(text, width, font_role)
        self.height = renderer.line_height(font_role) * len(self.lines)

    def draw(self, surface):
        self.renderer.wrapped_text(
            surface, self.lines, pygame.Rect(self.x, self.y, self.width, self.height),
            self.font_role, self.color_role,
        )


class Button:
    def __init__(
        self, rect, text, renderer, font_role='button', *,
        active=True, lift: CellLift | None = None,
    ):
        self.rect = rect
        self.text = text
        self.renderer = renderer
        self.font_role = font_role
        self.active = active
        self.highlight: str | None = None
        layout = renderer.theme.layout
        self.padding = layout.choice_padding if font_role == 'choice' else layout.button_padding
        width = rect.width - 2 * self.padding
        if width <= 0:
            raise ValueError('Button padding leaves no text width')
        self.lines = renderer.wrap(text, width, font_role)
        self.height = renderer.line_height(font_role) * len(self.lines)
        self.rect.height = max(self.height + 2 * self.padding, rect.height)
        self._lift = 0.0
        if lift is not None:
            self.lift_settings = lift
        elif font_role == 'choice':
            self.lift_settings = renderer.theme.answer_lift
        else:
            self.lift_settings = CellLift()

    def update_lift(self, dt_ms: int, *, hovered: bool):
        settings = self.lift_settings
        if not self.active or self.highlight is not None:
            self.reset_lift()
            return
        if settings.rest_px == 0 and settings.hover_px == 0:
            self.reset_lift()
            return

        target = settings.hover_px if hovered else settings.rest_px
        if settings.pop_ms <= 0:
            self._lift = float(target)
            return

        travel = max(settings.rest_px, abs(settings.hover_px - settings.rest_px))
        step = travel * max(0, dt_ms) / settings.pop_ms
        if self._lift < target:
            self._lift = min(target, self._lift + step)
        elif self._lift > target:
            self._lift = max(target, self._lift - step)

    def reset_lift(self):
        self._lift = 0.0

    def settle_for_reveal(self, *, selected: bool):
        settings = self.lift_settings
        self._lift = 0.0 if selected else float(settings.rest_px)

    @property
    def draw_lift(self) -> int:
        if not self.active:
            return 0
        skin = self.renderer.theme.skin
        step = skin.scale if skin is not None else 1
        return int(self._lift / step + 0.5) * step

    def draw(self, surface, *, reveal_elapsed_ms=0):
        style = 'normal' if self.active else 'inactive'
        if self.highlight == 'correct':
            style = 'correct'
        color_role = None if self.active else 'text_inactive'
        lift = self.draw_lift
        draw_rect = self.rect.move(0, -lift)
        self.renderer.button(surface, self.rect, style, lift=lift)
        if self.highlight == 'correct':
            self.renderer.answer_feedback(
                surface, draw_rect, self.highlight, reveal_elapsed_ms,
            )
        self.renderer.wrapped_text(
            surface, self.lines, draw_rect.inflate(-2 * self.padding, -2 * self.padding),
            self.font_role, color_role,
        )
        if self.highlight is not None and self.highlight != 'correct':
            self.renderer.answer_feedback(
                surface, draw_rect, self.highlight, reveal_elapsed_ms,
            )

    def is_clicked(self, pos):
        return self.active and self.rect.collidepoint(pos)


class Checkbox:
    def __init__(self, rect, text, renderer, checked=False):
        self.rect = rect
        self.text = text
        self.renderer = renderer
        self.checked = checked
        self.label_rect = renderer.text_rects(
            [text], pygame.Rect(0, 0, 1, 1), 'checkbox', alignment=Alignment('left', 'top'),
        )[0]
        self.label_rect.midleft = (self.rect.right + 12, self.rect.centery)
        self.hit_rect = self.rect.union(self.label_rect)

    def toggle(self):
        self.checked = not self.checked

    def is_clicked(self, pos):
        return self.hit_rect.collidepoint(pos)

    def draw(self, surface, offset_y=0):
        draw_rect = self.rect.move(0, -offset_y)
        draw_label_rect = self.label_rect.move(0, -offset_y)
        self.renderer.checkbox(surface, draw_rect, self.checked)
        self.renderer.text(surface, self.text, draw_label_rect, 'checkbox')
