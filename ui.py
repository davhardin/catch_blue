from collections.abc import Callable

import pygame

from constants import BUTTON_PRESS_DOWN_MS, BUTTON_PRESS_HOLD_MS
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
        active=True, selected=False, lift: CellLift | None = None,
    ):
        self.rect = rect
        self.text = text
        self.renderer = renderer
        self.font_role = font_role
        self.active = active
        self.selected = selected
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
        self._press_start: float | None = None
        self._press_elapsed_ms = 0
        self._press_hold_elapsed_ms = 0
        if lift is not None:
            self.lift_settings = lift
        elif font_role == 'choice':
            self.lift_settings = renderer.theme.answer_lift
        else:
            self.lift_settings = CellLift()

    def update_lift(self, dt_ms: int, *, hovered: bool):
        if self._press_start is not None:
            return
        settings = self.lift_settings
        if not self.active or self.highlight is not None or self.selected:
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

    def start_press(self):
        self._press_start = self._lift
        self._press_elapsed_ms = 0
        self._press_hold_elapsed_ms = 0

    def update_press(self, dt_ms: int) -> bool:
        if self._press_start is None:
            return False
        dt_ms = max(0, dt_ms)
        if self._press_elapsed_ms < BUTTON_PRESS_DOWN_MS:
            self._press_elapsed_ms = min(BUTTON_PRESS_DOWN_MS, self._press_elapsed_ms + dt_ms)
            progress = self._press_elapsed_ms / BUTTON_PRESS_DOWN_MS
            self._lift = self._press_start * (1 - progress)
            return False
        self._press_hold_elapsed_ms += dt_ms
        if self._press_hold_elapsed_ms < BUTTON_PRESS_HOLD_MS:
            return False
        self._press_start = None
        return True

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
        if self.highlight == 'correct' or (self.active and self.selected):
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


class ButtonAction:
    def __init__(self):
        self.button: Button | None = None
        self.callback: Callable[[], None] | None = None
        self._discard_events = False

    def begin(self, button: Button, callback: Callable[[], None]):
        if self.button is not None or not button.active:
            return
        self.button = button
        self.callback = callback
        button.start_press()

    def update(self, dt_ms: int):
        if self.button is None:
            return
        if not self.button.update_press(dt_ms):
            return
        callback = self.callback
        assert callback is not None
        self.button = None
        self.callback = None
        self._discard_events = True
        callback()

    def blocks_events(self) -> bool:
        if self._discard_events:
            self._discard_events = False
            return True
        return self.button is not None


def pointer_position(current, event):
    if event.type == pygame.WINDOWLEAVE:
        return None
    if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
        return event.pos
    return current


def update_button_lifts(buttons, dt_ms, pointer_pos):
    for button in buttons:
        hovered = pointer_pos is not None and button.is_clicked(pointer_pos)
        button.update_lift(dt_ms, hovered=hovered)


class OptionRow:
    def __init__(self, rect, options, renderer, *, selected, gap=16, read_only=()):
        self.options = tuple(options)
        if not self.options:
            raise ValueError('OptionRow requires at least one option')
        values = [value for value, _ in self.options]
        if len(set(values)) != len(values):
            raise ValueError('OptionRow option values must be unique')
        count = len(self.options)
        available = rect.width - gap * (count - 1)
        if gap < 0 or available < count:
            raise ValueError('OptionRow requires a nonnegative gap and positive option widths')

        self.rect = rect.copy()
        self.read_only = frozenset(read_only)
        self.buttons = {}
        for index, (value, label) in enumerate(self.options):
            button_rect = self.rect.copy()
            button_rect.left = rect.left + available * index // count + gap * index
            button_rect.width = available * (index + 1) // count - available * index // count
            self.buttons[value] = Button(
                button_rect, label, renderer, lift=renderer.theme.menu_lift,
            )
        self.rect.height = max(button.rect.height for button in self.buttons.values())
        for button in self.buttons.values():
            button.rect.height = self.rect.height
        self.set_selected(selected)

    def set_selected(self, value):
        if value not in self.buttons:
            raise ValueError(f'Unknown OptionRow value: {value!r}')
        self.selected = value
        for option, button in self.buttons.items():
            button.selected = option == value
            if button.selected:
                button.reset_lift()

    def choice_at(self, pos):
        for value, button in self.buttons.items():
            if value not in self.read_only and button.is_clicked(pos):
                return value
        return None

    def update(self, dt_ms, pointer_pos):
        for value, button in self.buttons.items():
            if value in self.read_only:
                button.reset_lift()
            else:
                update_button_lifts((button,), dt_ms, pointer_pos)

    def draw(self, surface):
        for button in self.buttons.values():
            button.draw(surface)


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
