"""Nine-slice geometry and shipped artwork, without a display."""
from dataclasses import replace

import pygame
import pytest

from render import Renderer
from theme import ACCENT_KEYS, FLAT, PIXEL, PIXEL_ACCENTS, NineSlice, Skin

pytestmark = pytest.mark.usefixtures('fonts')


def art_pixels(path, art_width=32):
    """A tile file read back at one pixel per art pixel, by sampling block centres."""
    image = pygame.image.load(str(path))
    factor = image.get_width() // art_width
    height = image.get_height() // factor
    return [
        [tuple(image.get_at((x * factor + factor // 2, y * factor + factor // 2)))
         for x in range(art_width)]
        for y in range(height)
    ]


def write_export(path, art, factor):
    """Save `art` (rows of RGBA tuples) blown up by `factor`, as a pixel editor exports it."""
    height, width = len(art), len(art[0])
    image = pygame.Surface((width * factor, height * factor), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, color in enumerate(row):
            image.fill(color, pygame.Rect(x * factor, y * factor, factor, factor))
    pygame.image.save(image, path)


def tile_skin_theme(path, tile_size, source=(0, 0, 4, 3), insets=(1, 1, 1, 1), scale=2):
    spec = NineSlice(source, insets, tile=path, tile_size=tile_size)
    return replace(FLAT, skin=Skin(path, scale, (('panel', spec),)))


ART = [
    [(x * 60, y * 80, 200, 255) for x in range(4)]
    for y in range(3)
]


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


@pytest.mark.parametrize('accent', ACCENT_KEYS)
def test_correct_skin_has_green_face_and_preserves_corners(accent):
    theme = PIXEL_ACCENTS[accent]
    renderer = Renderer(theme)
    spec = dict(theme.skin.elements)['button.correct']
    art = art_pixels(spec.tile)
    surface = pygame.Surface((480, 70))
    surface.fill((1, 2, 3))
    renderer.button(surface, surface.get_rect(), 'correct')
    # The left edge stretches the tile's edge column; the face is the correct color.
    assert surface.get_at((4, 35))[:3] == art[16][2][:3]
    assert surface.get_at((240, 35))[:3] == theme.palette.correct
    # Diagonal corner accents must remain local, never stretch across the face.
    assert surface.get_at((240, 10))[:3] == art[5][16][:3]
    # The corner is the tile at scale 2, with transparent pixels left see-through.
    for y in range(12):
        for x in range(12):
            color = art[y // 2][x // 2]
            expected = (1, 2, 3) if color[3] == 0 else color[:3]
            assert surface.get_at((x, y))[:3] == expected
    renderer.cell(surface, surface.get_rect(), 'selected')
    assert surface.get_at((240, 35))[:3] == theme.palette.correct


# --- loose tiles (M8.d) -------------------------------------------------------


@pytest.mark.parametrize('factor', [1, 8])
def test_tile_export_is_read_back_at_one_pixel_per_art_pixel(tmp_path, factor):
    path = tmp_path / 'tile.png'
    write_export(path, ART, factor)
    spec = NineSlice((0, 0, 4, 3), (1, 1, 1, 1), tile=path, tile_size=4)
    tile = Renderer._load_tile('panel', spec)
    assert tile.get_size() == (4, 3)
    assert [[tuple(tile.get_at((x, y))) for x in range(4)] for y in range(3)] == ART

    # Through the skin: the element is the art at the skin's scale, insets scaled too.
    renderer = Renderer(tile_skin_theme(path, 4))
    source, insets = renderer._skin_elements['panel']
    assert source.get_size() == (8, 6)
    assert insets == (2, 2, 2, 2)
    for y in range(6):
        for x in range(8):
            assert tuple(source.get_at((x, y))) == ART[y // 2][x // 2]


@pytest.mark.parametrize('file_size,tile_size,message', [
    ((30, 24), 4, 'tile size'),  # 30 px is not a whole multiple of 4
    ((32, 20), 4, 'whole-pixel'),  # 8x wide, but 20 px is not a whole number of 8x rows
    ((32, 24), None, 'tile size'),
    ((32, 24), 0, 'tile size'),
    ((32, 24), True, 'tile size'),
    ((32, 24), 4.0, 'tile size'),
])
def test_invalid_tile_exports_are_rejected(tmp_path, file_size, tile_size, message):
    path = tmp_path / 'tile.png'
    pygame.image.save(pygame.Surface(file_size, pygame.SRCALPHA), path)
    with pytest.raises(ValueError, match=message):
        Renderer(tile_skin_theme(path, tile_size))


def test_tile_source_is_checked_in_art_pixels(tmp_path):
    path = tmp_path / 'tile.png'
    write_export(path, ART, 8)
    # The file is 32 px wide, but the art is 4: a 5 px source does not fit.
    with pytest.raises(ValueError, match='source'):
        Renderer(tile_skin_theme(path, 4, source=(0, 0, 5, 3)))


@pytest.mark.parametrize('accent', ACCENT_KEYS)
def test_shipped_tiles_are_whole_pixel_exports(accent):
    tiles = {spec.tile for _, spec in PIXEL_ACCENTS[accent].skin.elements if spec.tile}
    assert len(tiles) == 4  # normal (buttons and resting cells), inactive, correct, move
    for path in tiles:
        image = pygame.image.load(str(path))
        spec = next(s for _, s in PIXEL_ACCENTS[accent].skin.elements if s.tile == path)
        art = Renderer._load_tile(path.name, spec)
        assert art.get_size() == (spec.tile_size, spec.tile_size)
        # Blowing the art back up reproduces the file byte for byte: no smoothing.
        restored = pygame.transform.scale(art, image.get_size())
        assert pygame.image.tobytes(restored, 'RGBA') == pygame.image.tobytes(image, 'RGBA'), path.name


@pytest.mark.parametrize('accent', ACCENT_KEYS)
def test_move_tint_finds_each_accents_cell_face(accent):
    theme = PIXEL_ACCENTS[accent]
    renderer = Renderer(theme)
    palette = theme.palette

    # The move tile's face was recolored to palette.cell at load, so the tint finds it.
    move_tile = renderer._skin_elements['cell.move'][0]
    assert any(move_tile.get_at((x, y))[:3] == palette.cell
               for x in range(move_tile.get_width())
               for y in range(move_tile.get_height()))

    rest, move = pygame.Surface((152, 152)), pygame.Surface((152, 152))
    for surface, style in ((rest, 'normal'), (move, 'move')):
        renderer.fill(surface)
        renderer.cell(surface, surface.get_rect(), style)
    assert rest.get_at((76, 76))[:3] == palette.cell
    assert move.get_at((76, 76))[:3] == palette.cell_move

    # No untinted face is left on a legal move: neither the resting face nor
    # the move tile's own face as drawn in the file.
    raw_move_face = art_pixels(dict(theme.skin.elements)['cell.move'].tile)[16][16][:3]
    leftovers = {palette.cell, raw_move_face} - {palette.cell_move}
    assert not any(move.get_at((x, y))[:3] in leftovers
                   for x in range(0, 152, 2) for y in range(0, 152, 2))



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
