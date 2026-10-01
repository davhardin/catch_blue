"""Theme-aware pygame drawing and text layout."""

from colorsys import rgb_to_hsv
from contextlib import contextmanager
from dataclasses import fields, replace
from math import cos, tau

import pygame

from constants import LINE_WIDTH
from theme import Alignment, HueShift, Skin, Theme, shift_color_to_hue


def mix_color(start, end, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


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
        self._font_specs = {
            role.name: getattr(theme.fonts, role.name)
            for role in fields(theme.fonts)
        }
        self._board_label_roles = {}
        for board_size, font_size in theme.board_label_sizes:
            role = f'label.{board_size}'
            self._font_specs[role] = replace(
                theme.fonts.label,
                size=font_size,
            )
            self._board_label_roles[board_size] = role

        self.fonts = {}
        loaded = {}
        for role, spec in self._font_specs.items():
            key = (spec.path, spec.size)
            if key not in loaded:
                loaded[key] = pygame.font.Font(
                    str(spec.path) if spec.path is not None else None,
                    spec.size,
                )
            self.fonts[role] = loaded[key]

    @staticmethod
    def _extract_packed_source(
        sheet: pygame.Surface,
        source_rect: pygame.Rect,
        tile_size: int,
        gap: int,
    ) -> pygame.Surface:
        pitch = tile_size + gap
        if (
            (source_rect.width + gap) % pitch
            or (source_rect.height + gap) % pitch
        ):
            raise ValueError('Packed skin source does not align to its tile grid')

        cols = (source_rect.width + gap) // pitch
        rows = (source_rect.height + gap) // pitch
        extracted = pygame.Surface(
            (cols * tile_size, rows * tile_size),
            pygame.SRCALPHA,
        )

        for row in range(rows):
            for col in range(cols):
                tile_rect = pygame.Rect(
                    source_rect.left + col * pitch,
                    source_rect.top + row * pitch,
                    tile_size,
                    tile_size,
                )
                extracted.blit(
                    sheet,
                    (col * tile_size, row * tile_size),
                    tile_rect,
                )

        return extracted

    @staticmethod
    def _apply_hue_shift(
        surface: pygame.Surface,
        shift: HueShift,
    ) -> None:
        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                color = surface.get_at((x, y))
                if color.a == 0:
                    continue

                hue, saturation, _ = rgb_to_hsv(
                    color.r / 255,
                    color.g / 255,
                    color.b / 255,
                )
                hue_degrees = hue * 360
                distance = abs(
                    (hue_degrees - shift.source_hue + 180) % 360 - 180
                )
                if (
                    saturation < shift.minimum_saturation
                    or distance > shift.tolerance
                ):
                    continue

                red, green, blue = shift_color_to_hue(
                    (color.r, color.g, color.b),
                    shift.target_hue,
                )
                surface.set_at((x, y), (red, green, blue, color.a))

    def _load_skin(self, skin: Skin):
        if type(skin.scale) is not int or skin.scale <= 0:
            raise ValueError('Skin scale must be an exact positive integer')

        tile_size = skin.packed_tile_size
        gap = skin.packed_tile_gap
        if tile_size is None:
            if gap != 0:
                raise ValueError('Packed skin gap requires a tile size')
        elif (
            type(tile_size) is not int
            or tile_size <= 0
            or type(gap) is not int
            or gap < 0
        ):
            raise ValueError('Packed skin tile size and gap are invalid')

        # Renderer is constructed before Game creates the display.
        sheet = pygame.image.load(str(skin.sheet))
        uses_custom_sources = (
            tile_size is not None
            or skin.hue_shift is not None
        )

        if not uses_custom_sources:
            self._skin_sheet = pygame.transform.scale(
                sheet,
                (
                    sheet.get_width() * skin.scale,
                    sheet.get_height() * skin.scale,
                ),
            )

        for name, spec in skin.elements:
            if name in self._skin_elements:
                raise ValueError(f'Duplicate skin element: {name}')

            x, y, width, height = spec.source
            source_rect = pygame.Rect(spec.source)
            if (
                any(type(value) is not int for value in spec.source)
                or width <= 0
                or height <= 0
                or not sheet.get_rect().contains(source_rect)
            ):
                raise ValueError(f'Invalid skin source: {name}')

            if tile_size is not None:
                source = self._extract_packed_source(
                    sheet,
                    source_rect,
                    tile_size,
                    gap,
                )
            elif skin.hue_shift is not None:
                source = sheet.subsurface(source_rect).copy()
            else:
                assert self._skin_sheet is not None
                scaled_rect = pygame.Rect(
                    x * skin.scale,
                    y * skin.scale,
                    width * skin.scale,
                    height * skin.scale,
                )
                source = self._skin_sheet.subsurface(scaled_rect)

            left, top, right, bottom = spec.insets
            inset_width = source.get_width() if uses_custom_sources else width
            inset_height = source.get_height() if uses_custom_sources else height
            if (
                any(
                    type(value) is not int or value < 0
                    for value in spec.insets
                )
                or left + right >= inset_width
                or top + bottom >= inset_height
            ):
                raise ValueError(f'Invalid skin insets: {name}')

            if uses_custom_sources:
                source = source.copy()
                if skin.hue_shift is not None:
                    self._apply_hue_shift(source, skin.hue_shift)
                source = pygame.transform.scale(
                    source,
                    (
                        source.get_width() * skin.scale,
                        source.get_height() * skin.scale,
                    ),
                )

            if spec.recolor:
                # A plain skin's source is a view into the shared sheet.
                source = source.copy()
                with pygame.PixelArray(source) as pixels:
                    for sheet_color, drawn_color in spec.recolor:
                        pixels.replace(sheet_color, drawn_color)

            self._skin_elements[name] = (
                source,
                tuple(value * skin.scale for value in spec.insets),
            )

    def _draw_skin(self, surface, rect, name) -> bool:
        if name not in self._skin_elements:
            return False

        source, (left, top, right, bottom) = self._skin_elements[name]
        if rect.width <= left + right or rect.height <= top + bottom:
            raise ValueError(f'Destination too small for skin element: {name}')

        source_rect = source.get_rect()
        source_x = (
            source_rect.left,
            source_rect.left + left,
            source_rect.right - right,
            source_rect.right,
        )
        source_y = (
            source_rect.top,
            source_rect.top + top,
            source_rect.bottom - bottom,
            source_rect.bottom,
        )
        dest_x = (
            rect.left,
            rect.left + left,
            rect.right - right,
            rect.right,
        )
        dest_y = (
            rect.top,
            rect.top + top,
            rect.bottom - bottom,
            rect.bottom,
        )

        for row in range(3):
            for col in range(3):
                src = pygame.Rect(
                    source_x[col],
                    source_y[row],
                    source_x[col + 1] - source_x[col],
                    source_y[row + 1] - source_y[row],
                )
                dst = pygame.Rect(
                    dest_x[col],
                    dest_y[row],
                    dest_x[col + 1] - dest_x[col],
                    dest_y[row + 1] - dest_y[row],
                )
                if (
                    not src.width
                    or not src.height
                    or not dst.width
                    or not dst.height
                ):
                    continue

                piece = source.subsurface(src)
                if piece.get_size() != dst.size:
                    piece = pygame.transform.scale(piece, dst.size)
                surface.blit(piece, dst)

        return True

    def color(self, role):
        return getattr(self.theme.palette, role)

    def font(self, role):
        return self.fonts[role]

    def label_role(self, board_size: int) -> str:
        return self._board_label_roles.get(board_size, 'label')

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
            alignment = self._font_specs[font_role].alignment
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

    def button(self, surface, rect, style='normal', *, lift=0):
        draw_rect = rect.move(0, -lift)
        if lift:
            pygame.draw.rect(surface, self.color('panel_line'), rect)

        element = f'button.{style}'
        if self._draw_skin(surface, draw_rect, element):
            if style == 'correct':
                _, (left, top, right, bottom) = self._skin_elements[element]
                face = pygame.Rect(draw_rect.left + left, draw_rect.top + top,
                                   draw_rect.width - left - right, draw_rect.height - top - bottom)
                pygame.draw.rect(surface, self.color('correct'), face)
            return
        role = {'normal': 'button', 'inactive': 'button_inactive',
                'correct': 'correct'}[style]
        pygame.draw.rect(surface, self.color(role), draw_rect)

    def answer_feedback(self, surface, rect, outcome, elapsed_ms):
        style = self.theme.reveal
        background = self.color('background')
        highlight = self.color('highlight')

        if outcome == 'correct':
            phase = (elapsed_ms % style.pulse_period_ms) / style.pulse_period_ms
            pulse = (1 + cos(tau * phase)) / 2
            brightness = style.minimum_brightness + (1 - style.minimum_brightness) * pulse
            outline_color = mix_color(background, highlight, brightness)
            if 'button.correct' in self._skin_elements:
                _, (left, top, right, bottom) = self._skin_elements['button.correct']
                # Tint the existing bevel, retaining its shading through alpha
                # blending. The center stays untouched by the border pulse.
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((*highlight, round(255 * brightness)))
                overlay.fill((0, 0, 0, 0), pygame.Rect(
                    left, top, rect.width - left - right, rect.height - top - bottom,
                ))
                surface.blit(overlay, rect)
            else:
                pygame.draw.rect(surface, outline_color, rect, width=style.outline_width)
            return
        elif outcome == 'incorrect':
            # Remove chroma first, then reduce contrast against the panel, not
            # the dark window background. This recedes without a dark-grey fill.
            visible = rect.clip(surface.get_rect())
            if visible.width and visible.height:
                desaturated = pygame.transform.grayscale(surface.subsurface(visible))
                desaturated.set_alpha(style.desaturate_alpha)
                surface.blit(desaturated, visible)
            panel = self.color('panel')
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((*panel, style.fade_alpha))
            surface.blit(overlay, rect)
            outline_color = mix_color(panel, self.color('panel_line'), 0.15)
        else:
            raise ValueError(f'Unknown answer feedback: {outcome}')

        # An outer ring preserves the text area and hit target.
        width = style.outline_width
        pygame.draw.rect(surface, outline_color, rect.inflate(2 * width, 2 * width), width=width)

    def cell(self, surface, rect, style='normal', *, lift=0):
        if style in ('hover', 'selected'):
            role, width = ('hover_line', 5) if style == 'hover' else ('selected_line', 4)
            pygame.draw.rect(surface, self.color(role), rect, width=LINE_WIDTH * width)
            return

        tile_rect = rect.move(0, -lift)
        if lift:
            pygame.draw.rect(surface, self.color('panel_line'), rect)

        if style == 'move' and 'cell.move' in self._skin_elements:
            tile = pygame.Surface(tile_rect.size, pygame.SRCALPHA)
            self._draw_skin(tile, tile.get_rect(), 'cell.move')
            with pygame.PixelArray(tile) as pixels:
                pixels.replace(self.color('cell'), self.color('cell_move'))
            surface.blit(tile, tile_rect)
            return

        if self._draw_skin(surface, tile_rect, f'cell.{style}'):
            return
        role = {'normal': 'cell', 'move': 'cell_move'}[style]
        pygame.draw.rect(surface, self.color(role), tile_rect)
        pygame.draw.rect(surface, self.color('cell_line'), tile_rect, width=LINE_WIDTH)


    def text(self, surface, text, rect, font_role, color_role=None, alignment=None):
        self.wrapped_text(surface, [text], rect, font_role, color_role, alignment)

    def wrapped_text(self, surface, lines, rect, font_role, color_role=None, alignment=None):
        if color_role is None:
            color_role = self._font_specs[font_role].color_role
        font = self.font(font_role)
        rendered = [font.render(line, True, self.color(color_role)) for line in lines]
        rects = self._text_rects(
            [line.get_size() for line in rendered], rect, font_role, alignment,
        )
        for line, line_rect in zip(rendered, rects):
            surface.blit(line, line_rect)

    def checkbox(self, surface, rect, checked=False):
        color = self.color(self._font_specs['checkbox'].color_role)
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
