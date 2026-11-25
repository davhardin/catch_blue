"""Theme data is immutable, portable, and independent of pygame."""

from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
import subprocess
import sys

import pytest

import theme as theme_module
from theme import (
    ACCENT_KEYS, ASSET_ROOT, DEFAULT_THEME, FLAT, PIXEL, PIXEL_ACCENTS, THEMES,
    Alignment, FontSpec, NineSlice, Skin, SpriteSpec, Theme, resolve_accent,
    theme_accent,
)

# GDD §3: character colors come from the Okabe-Ito colorblind-safe palette.
OKABE_ITO = {
    'player': (230, 159, 0),
    'blue': (0, 114, 178),
    'red': (213, 94, 0),
    'green': (0, 158, 115),
    'yellow': (240, 228, 66),
}


def assert_immutable(value):
    if is_dataclass(value):
        for item in fields(value):
            child = getattr(value, item.name)
            with pytest.raises(FrozenInstanceError):
                setattr(value, item.name, child)
            assert_immutable(child)
    elif isinstance(value, tuple):
        for child in value:
            assert_immutable(child)
    else:
        assert value is None or isinstance(value, (str, int, float, Path))


def test_nested_theme_data_is_immutable():
    for registered in THEMES.values():
        assert_immutable(registered)
    assert_immutable(Theme(
        'future', FLAT.palette, FLAT.fonts,
        Skin(ASSET_ROOT / 'skin.png', 2, (
            ('panel', NineSlice((0, 0, 16, 16), (2, 3, 4, 5))),
            ('cell.normal', NineSlice(
                (0, 0, 32, 32), (5, 5, 5, 5), tile=ASSET_ROOT / 'tile.png', tile_size=32,
            )),
        )),
        (('blue', SpriteSpec(ASSET_ROOT / 'sprites.png', (0, 0, 8, 8))),),
    ))
    first, second = FontSpec(None, 28), FontSpec(None, 28)
    assert first.alignment == Alignment()
    assert first.alignment is not second.alignment


def test_registry_is_flat_and_the_pixel_family():
    assert THEMES == {
        'flat': FLAT,
        'pixel': PIXEL,
        'pixel-red': PIXEL_ACCENTS['red'],
        'pixel-green': PIXEL_ACCENTS['green'],
        'pixel-yellow': PIXEL_ACCENTS['yellow'],
    }
    assert all(name == registered.name for name, registered in THEMES.items())
    assert PIXEL_ACCENTS['blue'] is PIXEL
    assert DEFAULT_THEME == 'pixel' and THEMES[DEFAULT_THEME] is PIXEL
    # M8.d (2026-11-24): the hue remap and the ui-* themes were deleted.
    assert not any(name.startswith('ui-') for name in THEMES)
    for removed in ('UI_ACCENTS', 'UI_BLUE', 'HueShift', 'with_accent', 'shift_color_to_hue'):
        assert not hasattr(theme_module, removed), removed


@pytest.mark.parametrize('accent', ACCENT_KEYS)
def test_accents_resolve_within_the_pixel_family_and_flat_ignores_them(accent):
    assert resolve_accent(PIXEL, accent) is PIXEL_ACCENTS[accent]
    assert resolve_accent(PIXEL_ACCENTS['red'], accent) is PIXEL_ACCENTS[accent]
    assert resolve_accent(FLAT, accent) is FLAT
    assert theme_accent(PIXEL_ACCENTS[accent]) == accent


def test_unknown_accent_is_rejected_and_flat_has_none():
    assert theme_accent(FLAT) is None
    with pytest.raises(ValueError):
        resolve_accent(PIXEL, 'purple')


@pytest.mark.parametrize('theme', THEMES.values(), ids=THEMES.keys())
def test_character_colors_are_okabe_ito(theme):
    expected = dict(OKABE_ITO)
    if theme is PIXEL_ACCENTS['red']:
        # A darker Red so it stands out on its own board (M8.d).
        expected['red'] = (149, 66, 0)
    assert {role: getattr(theme.palette, role) for role in expected} == expected


@pytest.mark.parametrize('theme', THEMES.values(), ids=THEMES.keys())
def test_text_alignment_roles(theme):
    for role in fields(theme.fonts):
        spec = getattr(theme.fonts, role.name)
        if role.name in ('label', 'choice', 'credits'):
            assert spec.alignment == Alignment('center', 'center'), role.name
        elif theme is FLAT:
            assert spec.alignment == Alignment(), role.name
    # Credits sit on the window background, never on a panel.
    assert theme.fonts.credits.color_role == 'background_text'


@pytest.mark.parametrize('theme', THEMES.values(), ids=THEMES.keys())
def test_registered_popup_fonts_and_no_banner(theme):
    assert theme.fonts.choice.size == theme.fonts.prompt.size
    assert theme.fonts.choice.alignment == Alignment('center', 'center')
    assert not hasattr(theme.fonts, 'banner')
    assert not hasattr(theme.layout, 'show_category_banner')
    assert not hasattr(theme.palette, 'incorrect')
    assert not hasattr(theme.reveal, 'wash_min_alpha')
    if theme.skin:
        # The correct-answer pulse tints the bevel toward the window color.
        assert theme.palette.highlight == theme.palette.background
        assert not {'banner', 'button.incorrect'} & dict(theme.skin.elements).keys()
    else:
        # Flat pulses an outline, which must stand out from the window.
        assert theme.palette.highlight != theme.palette.background


@pytest.mark.parametrize('theme', THEMES.values(), ids=THEMES.keys())
def test_registered_assets_and_licenses_exist(theme, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    paths = [getattr(theme.fonts, role.name).path for role in fields(theme.fonts)]
    if theme.skin is not None:
        paths.append(theme.skin.sheet)
        paths.extend(spec.tile for _, spec in theme.skin.elements if spec.tile is not None)
    paths.extend(spec.sheet for _, spec in theme.sprites)
    # License files relative to ASSET_ROOT. The hand-drawn tiles were edited
    # from the Pixel Adventure pack, so they carry its license (ATTRIBUTION.md).
    licenses = {
        'Atkinson_Hyperlegible_Next': 'Atkinson_Hyperlegible_Next/OFL.txt',
        'Atkinson_Hyperlegible_Mono': 'Atkinson_Hyperlegible_Mono/OFL.txt',
        'kenney_ui-pack-pixel-adventure': 'kenney_ui-pack-pixel-adventure/License.txt',
        'four_color_buttons': 'kenney_ui-pack-pixel-adventure/License.txt',
    }
    for path in paths:
        if path is None:
            continue
        assert path.is_absolute()
        assert path.is_file(), path
        package = path.relative_to(ASSET_ROOT).parts[0]
        license_path = ASSET_ROOT / licenses[package]
        assert license_path.is_file(), license_path
        assert license_path.stat().st_size > 0


def test_theme_import_never_attempts_to_import_pygame():
    result = subprocess.run(
        [sys.executable, '-c', '''
import sys
class Guard:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'pygame':
            raise AssertionError('theme attempted to import pygame')
sys.meta_path.insert(0, Guard())
import theme
assert 'pygame' not in sys.modules
'''],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr.decode()
