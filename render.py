"""Theme-aware pygame drawing and text layout."""

from contextlib import contextmanager
from dataclasses import fields

import pygame

from constants import LINE_WIDTH
from theme import Alignment, Theme


def word_wrap(text: str, width: int, font) -> list[str]:
    lines = []

    for word in text.split():
        if not lines:
            lines.append(word)
        elif font.size(lines[-1] + ' ' + word)[0] <= width:
            lines[-1] += ' ' + word
        else:
            lines.append(word)
    return lines


class Renderer:
    def __init__(self, theme: Theme):
        if theme.sprites:
            raise NotImplementedError('Sprite loading is not implemented yet')
        self.theme = theme
        self._skin_elements = {}
        self._skin_sheet = None
        if theme.skin is not None:
            self._load_skin(theme.skin)
        self.fonts = {}
        loaded = {}
        for role in fields(theme.fonts):
            spec = getattr(theme.fonts, role.name)
            key = (spec.path, spec.size)
            if key not in loaded:
                loaded[key] = pygame.font.Font(
                    str(spec.path) if spec.path is not None else None, spec.size,
                )
            self.fonts[role.name] = loaded[key]

    def _load_skin(self, skin):
        if type(skin.scale) is not int or skin.scale <= 0:
            raise ValueError('Skin scale must be an exact positive integer')
        # Renderer is constructed before Game creates the display.
        sheet = pygame.image.load(str(skin.sheet))
        scale = skin.scale
        for name, spec in skin.elements:
            if name in self._skin_elements:
                raise ValueError(f'Duplicate skin element: {name}')
            x, y, width, height = spec.source
            if (any(type(value) is not int for value in spec.source)
                    or width <= 0 or height <= 0
                    or not sheet.get_rect().contains(pygame.Rect(spec.source))):
                raise ValueError(f'Invalid skin source: {name}')
            left, top, right, bottom = spec.insets
            if (any(type(value) is not int or value < 0 for value in spec.insets)
                    or left + right >= width or top + bottom >= height):
                raise ValueError(f'Invalid skin insets: {name}')
            self._skin_elements[name] = (
                pygame.Rect(x * scale, y * scale, width * scale, height * scale),
                tuple(value * scale for value in spec.insets),
            )
        self._skin_sheet = pygame.transform.scale(
            sheet, (sheet.get_width() * scale, sheet.get_height() * scale),
        )

    def _draw_skin(self, surface, rect, name) -> bool:
        if name not in self._skin_elements:
            return False
        source, (left, top, right, bottom) = self._skin_elements[name]
        if rect.width <= left + right or rect.height <= top + bottom:
            raise ValueError(f'Destination too small for skin element: {name}')
        source_x = (source.left, source.left + left, source.right - right, source.right)
        source_y = (source.top, source.top + top, source.bottom - bottom, source.bottom)
        dest_x = (rect.left, rect.left + left, rect.right - right, rect.right)
        dest_y = (rect.top, rect.top + top, rect.bottom - bottom, rect.bottom)
        for row in range(3):
            for col in range(3):
                src = pygame.Rect(source_x[col], source_y[row],
                                  source_x[col + 1] - source_x[col], source_y[row + 1] - source_y[row])
                dst = pygame.Rect(dest_x[col], dest_y[row],
                                  dest_x[col + 1] - dest_x[col], dest_y[row + 1] - dest_y[row])
                if not src.width or not src.height or not dst.width or not dst.height:
                    continue
                piece = self._skin_sheet.subsurface(src)
                if piece.get_size() != dst.size:
                    piece = pygame.transform.scale(piece, dst.size)
                surface.blit(piece, dst)
        return True

    def color(self, role):
        return getattr(self.theme.palette, role)

    def font(self, role):
        return self.fonts[role]

    def measure(self, text, font_role):
        return self.font(font_role).size(text)

    def line_height(self, font_role):
        return self.font(font_role).get_linesize()

    def wrap(self, text, width, font_role):
        return word_wrap(text, width, self.font(font_role))

    def text_rects(self, lines, rect, font_role, alignment: Alignment | None = None):
        """Return rendered text bounds; font.size can differ from surface size."""
        font = self.font(font_role)
        sizes = [font.render(line, True, self.color('text')).get_size() for line in lines]
        return self._text_rects(sizes, rect, font_role, alignment)

    def _text_rects(self, sizes, rect, font_role, alignment):
        if not sizes:
            return []
        if alignment is None:
            alignment = getattr(self.theme.fonts, font_role).alignment
        stride = self.line_height(font_role)
        block_height = (len(sizes) - 1) * stride + sizes[-1][1]
        top = rect.centery - block_height // 2 if alignment.vertical == 'center' else rect.top
        rects = []
        for index, size in enumerate(sizes):
            line_rect = pygame.Rect(rect.left, top + index * stride, *size)
            if alignment.horizontal == 'center':
                line_rect.centerx = rect.centerx
            rects.append(line_rect)
        return rects

    def fill(self, surface):
        surface.fill(self.color('background'))

    def panel(self, surface, rect):
        if self._draw_skin(surface, rect, 'panel'):
            return
        pygame.draw.rect(surface, self.color('panel'), rect)
        pygame.draw.rect(surface, self.color('panel_line'), rect, width=2)

    def button(self, surface, rect, style='normal'):
        if self._draw_skin(surface, rect, f'button.{style}'):
            return
        role = {'normal': 'button', 'inactive': 'button_inactive',
                'correct': 'correct', 'incorrect': 'incorrect'}[style]
        pygame.draw.rect(surface, self.color(role), rect)

    def cell(self, surface, rect, style='normal'):
        if style in ('hover', 'selected'):
            role, width = ('hover_line', 5) if style == 'hover' else ('selected_line', 4)
            pygame.draw.rect(surface, self.color(role), rect, width=LINE_WIDTH * width)
        else:
            if self._draw_skin(surface, rect, f'cell.{style}'):
                return
            role = {'normal': 'cell', 'move': 'cell_move'}[style]
            pygame.draw.rect(surface, self.color(role), rect)
            pygame.draw.rect(surface, self.color('cell_line'), rect, width=LINE_WIDTH)

    def banner(self, surface, rect, lines):
        if not self._draw_skin(surface, rect, 'banner'):
            raise ValueError('Missing skin element: banner')
        layout = self.theme.layout
        content = rect.inflate(-2 * layout.banner_side_padding, -2 * layout.banner_vertical_padding)
        self.wrapped_text(surface, lines, content, 'banner')

    def text(self, surface, text, rect, font_role, color_role=None, alignment=None):
        self.wrapped_text(surface, [text], rect, font_role, color_role, alignment)

    def wrapped_text(self, surface, lines, rect, font_role, color_role=None, alignment=None):
        if color_role is None:
            color_role = getattr(self.theme.fonts, font_role).color_role
        font = self.font(font_role)
        rendered = [font.render(line, True, self.color(color_role)) for line in lines]
        rects = self._text_rects(
            [line.get_size() for line in rendered], rect, font_role, alignment,
        )
        for line, line_rect in zip(rendered, rects):
            surface.blit(line, line_rect)

    def checkbox(self, surface, rect, checked=False):
        color = self.color(self.theme.fonts.checkbox.color_role)
        pygame.draw.rect(surface, color, rect, width=2)
        if checked:
            pygame.draw.rect(surface, color, rect.inflate(-8, -8))

    def sprite(self, surface, rect, shape, color_role):
        margin = rect.width // 6
        if shape == 'circle':
            pygame.draw.circle(surface, self.color(color_role), rect.center, margin)
        elif shape == 'square':
            pygame.draw.rect(surface, self.color(color_role), rect.inflate(-3 * margin, -3 * margin))

    @contextmanager
    def clip(self, surface, rect):
        previous_clip = surface.get_clip()
        surface.set_clip(rect)
        try:
            yield
        finally:
            surface.set_clip(previous_clip)
