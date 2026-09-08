"""Nine-slice geometry and shipped artwork, without a display."""
from dataclasses import replace

import pygame
import pytest

from render import Renderer
from theme import FLAT, PIXEL, NineSlice, Skin


@pytest.fixture(autouse=True)
def fonts():
    pygame.font.init()
    yield
    pygame.font.quit()


def synthetic(tmp_path, scale=1, source=(1, 2, 9, 11), insets=(2, 3, 4, 2)):
    sheet = pygame.Surface((12, 15), pygame.SRCALPHA)
    # Unique pixels exercise nearest-neighbor resampling, not just solid fills.
    for y in range(15):
        for x in range(12):
            sheet.set_at((x, y), (x * 20, y * 16, (x + y) * 9, 255))
    path = tmp_path / 'sheet.png'
    pygame.image.save(sheet, path)
    return replace(FLAT, skin=Skin(path, scale, (('panel', NineSlice(source, insets)),))), sheet


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('size', [(37, 29), (19, 43)])
@pytest.mark.parametrize('insets', [(2, 3, 4, 2), (0, 3, 4, 0), (0, 0, 0, 0)])
def test_nine_slice_every_pixel(tmp_path, scale, size, insets):
    theme, sheet = synthetic(tmp_path, scale, insets=insets)
    renderer = Renderer(theme)
    target = pygame.Surface((60, 60), pygame.SRCALPHA)
    target.fill((7, 8, 9, 255))
    rect = pygame.Rect((7, 5), size)
    assert renderer._draw_skin(target, rect, 'panel')

    def source_coordinate(pos, length, source_length, before, after):
        before *= scale
        after *= scale
        if pos < before:
            return pos // scale
        if pos >= length - after:
            return source_length - (length - pos + scale - 1) // scale
        # Use pygame's nearest sampling convention (not an assumed floor rule).
        # A 1D coordinate ramp is independent of the renderer's 2D region assembly.
        center_length = source_length * scale - before - after
        ramp = pygame.Surface((center_length, 1))
        for i in range(center_length):
            ramp.set_at((i, 0), ((before + i) // scale, 0, 0))
        sampled = pygame.transform.scale(ramp, (length - before - after, 1))
        return sampled.get_at((pos - before, 0)).r

    left, top, right, bottom = insets
    for y in range(rect.height):
        for x in range(rect.width):
            sx = 1 + source_coordinate(x, rect.width, 9, left, right)
            sy = 2 + source_coordinate(y, rect.height, 11, top, bottom)
            assert target.get_at((rect.x + x, rect.y + y)) == sheet.get_at((sx, sy))
    assert target.get_at((rect.left - 1, rect.top)) == (7, 8, 9, 255)
    assert not renderer._draw_skin(target, rect, 'missing')


@pytest.mark.parametrize('scale', [0, -1, 1.0, True, '2'])
def test_invalid_scale(tmp_path, scale):
    theme, _ = synthetic(tmp_path, scale)
    with pytest.raises(ValueError, match='scale'):
        Renderer(theme)


@pytest.mark.parametrize('source', [(0, 0, 0, 5), (0, 0, 5, -1), (-1, 0, 9, 11),
                                    (4, 5, 9, 11), (1.5, 2, 9, 11)])
def test_invalid_source(tmp_path, source):
    theme, _ = synthetic(tmp_path, source=source)
    with pytest.raises(ValueError, match='source'):
        Renderer(theme)


@pytest.mark.parametrize('insets', [(-1, 0, 0, 0), (5, 0, 4, 0), (0, 6, 0, 5),
                                    (1.5, 0, 0, 0), (0, False, 0, 0)])
def test_invalid_insets(tmp_path, insets):
    theme, _ = synthetic(tmp_path, insets=insets)
    with pytest.raises(ValueError, match='insets'):
        Renderer(theme)


def test_duplicate_elements(tmp_path):
    theme, _ = synthetic(tmp_path)
    theme = replace(theme, skin=replace(theme.skin, elements=theme.skin.elements * 2))
    with pytest.raises(ValueError, match='Duplicate'):
        Renderer(theme)


@pytest.mark.parametrize('size', [(6, 20), (20, 5), (5, 20), (20, 4), (0, 0)])
def test_invalid_destination(tmp_path, size):
    theme, _ = synthetic(tmp_path)
    with pytest.raises(ValueError, match='Destination'):
        Renderer(theme).panel(pygame.Surface((50, 50)), pygame.Rect((0, 0), size))


def test_loading_without_display_and_flat_without_images(monkeypatch):
    pygame.display.quit()
    renderer = Renderer(PIXEL)
    assert pygame.display.get_surface() is None
    assert renderer._skin_sheet.get_size() == (832, 448)
    def unexpected(*args, **kwargs):
        raise AssertionError('FLAT loaded an image')
    monkeypatch.setattr(pygame.image, 'load', unexpected)
    Renderer(FLAT)


def test_sheet_scaled_once(tmp_path, monkeypatch):
    theme, _ = synthetic(tmp_path, 2)
    original = pygame.transform.scale
    calls = []
    def record(surface, size):
        calls.append((surface.get_size(), size))
        return original(surface, size)
    monkeypatch.setattr(pygame.transform, 'scale', record)
    renderer = Renderer(theme)
    assert calls == [((12, 15), (24, 30))]
    renderer.panel(pygame.Surface((80, 80)), pygame.Rect(0, 0, 40, 50))
    assert calls.count(((12, 15), (24, 30))) == 1


def test_correct_skin_has_green_face_and_preserves_corners():
    style, border = 'correct', (114, 184, 78)
    renderer = Renderer(PIXEL)
    surface = pygame.Surface((480, 70))
    surface.fill((1, 2, 3))
    renderer.button(surface, surface.get_rect(), style)
    assert surface.get_at((4, 35))[:3] == border
    assert surface.get_at((240, 35))[:3] == PIXEL.palette.correct
    assert surface.get_at((0, 0))[:3] == (1, 2, 3)  # colorkey survives scaling
    # Diagonal corner accents must remain local, never stretch across the face.
    assert surface.get_at((240, 10))[:3] == (148, 175, 198)
    spec = dict(PIXEL.skin.elements)[f'button.{style}']
    source = pygame.image.load(str(PIXEL.skin.sheet))
    for y in range(12):
        for x in range(12):
            color = source.get_at((spec.source[0] + x // 2, spec.source[1] + y // 2))
            expected = (1, 2, 3) if color[:3] == (0, 0, 0) else color[:3]
            assert surface.get_at((x, y))[:3] == expected
    renderer.cell(surface, surface.get_rect(), 'selected')
    assert surface.get_at((240, 35))[:3] == PIXEL.palette.correct



def test_partial_skin_falls_back_exactly(tmp_path):
    theme, _ = synthetic(tmp_path)
    actual, expected = pygame.Surface((90, 90)), pygame.Surface((90, 90))
    partial, flat = Renderer(theme), Renderer(FLAT)
    for method, style in [('button', 'correct'), ('cell', 'move'), ('cell', 'hover')]:
        actual.fill((1, 2, 3))
        expected.fill((1, 2, 3))
        getattr(partial, method)(actual, pygame.Rect(10, 10, 60, 60), style)
        getattr(flat, method)(expected, pygame.Rect(10, 10, 60, 60), style)
        assert pygame.image.tobytes(actual, 'RGB') == pygame.image.tobytes(expected, 'RGB')
