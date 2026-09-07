import pygame

from theme import Alignment


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
    def __init__(self, rect, text, renderer, font_role='button', *, active=True):
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

    def draw(self, surface):
        style = self.highlight if self.highlight is not None else (
            'normal' if self.active else 'inactive'
        )
        color_role = None if self.active else 'text_inactive'
        self.renderer.button(surface, self.rect, style)
        self.renderer.wrapped_text(
            surface, self.lines, self.rect.inflate(-2 * self.padding, -2 * self.padding),
            self.font_role, color_role,
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
