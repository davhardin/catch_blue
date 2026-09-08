"""Theme data is immutable, portable, and independent of pygame."""

from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
import subprocess
import sys

import pytest

from theme import ASSET_ROOT, DEFAULT_THEME, FLAT, PIXEL, THEMES, Alignment, FontSpec, Layout, NineSlice, Skin, SpriteSpec, Theme


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
    assert_immutable(FLAT)
    assert_immutable(PIXEL)
    assert THEMES == {'flat': FLAT, 'pixel': PIXEL}
    assert FLAT.layout == Layout()
    assert FLAT.fonts.choice.color_role == 'choice_text'
    assert all(getattr(PIXEL.fonts, role.name).path.is_file() for role in fields(PIXEL.fonts))
    assert_immutable(Theme(
        'future', FLAT.palette, FLAT.fonts,
        Skin(ASSET_ROOT / 'skin.png', 2, (
            ('panel', NineSlice((0, 0, 16, 16), (2, 3, 4, 5))),
        )),
        (('blue', SpriteSpec(ASSET_ROOT / 'sprites.png', (0, 0, 8, 8))),),
    ))
    first, second = FontSpec(None, 28), FontSpec(None, 28)
    assert first.alignment == Alignment()
    assert first.alignment is not second.alignment


def test_flat_preserves_all_palette_values():
    assert {item.name: getattr(FLAT.palette, item.name) for item in fields(FLAT.palette)} == {
        'background': (24, 26, 32), 'cell': (58, 64, 78),
        'cell_move': (60, 88, 90), 'cell_line': (120, 130, 148),
        'selected_line': (255, 0, 0), 'hover_line': (120, 130, 148),
        'label': (245, 245, 245), 'text': (245, 245, 245),
        'choice_text': (255, 255, 255), 'text_inactive': (145, 148, 156),
        'panel': (58, 64, 78), 'panel_line': (120, 130, 148),
        'button': (60, 88, 90), 'button_inactive': (75, 78, 86),
        'correct': (0, 100, 70),
        'player': (230, 159, 0), 'blue': (0, 114, 178),
        'character': (180, 180, 180),
        'background_text': (245, 245, 245), 'highlight': (245, 245, 245),
    }


def test_flat_fonts_and_alignment():
    assert FLAT.name == 'flat'
    assert FLAT.skin is None
    assert FLAT.sprites == ()
    assert ASSET_ROOT == Path(__file__).resolve().parents[1] / 'assets'
    assert FLAT.fonts.label.path == (
        ASSET_ROOT / 'Atkinson_Hyperlegible_Next' / 'static'
        / 'AtkinsonHyperlegibleNext-Regular.ttf'
    )
    assert FLAT.fonts.label.path.is_file()
    sizes = dict(label=16, prompt=32, choice=32, button=36,
                 title=56, counter=36, checkbox=30, result=40)
    for role, size in sizes.items():
        spec = getattr(FLAT.fonts, role)
        assert spec.size == size
        if role != 'label':
            assert spec.path is None
        assert spec.alignment == (
            Alignment('center', 'center') if role in ('label', 'choice') else Alignment()
        )


def test_readability_label_sizes():
    assert PIXEL.fonts.label.size == 20
    assert FLAT.fonts.label.size == 16


@pytest.mark.parametrize('theme', THEMES.values(), ids=THEMES.keys())
def test_registered_popup_fonts_and_no_banner(theme):
    size = {'flat': 32, 'pixel': 24}[theme.name]
    assert theme.fonts.prompt.size == size
    assert theme.fonts.choice.size == size
    assert theme.fonts.choice.alignment == Alignment('center', 'center')
    assert not hasattr(theme.fonts, 'banner')
    assert not hasattr(theme.layout, 'show_category_banner')
    assert not hasattr(theme.palette, 'incorrect')
    assert not hasattr(theme.reveal, 'wash_min_alpha')
    assert theme.palette.highlight == ((69, 82, 91) if theme is PIXEL else (245, 245, 245))
    if theme.skin:
        assert not {'banner', 'button.incorrect'} & dict(theme.skin.elements).keys()


def test_default_theme_and_credits_fonts():
    assert DEFAULT_THEME == 'pixel'
    assert THEMES[DEFAULT_THEME] is PIXEL
    assert FLAT.fonts.credits == FontSpec(
        None, 20, Alignment('center', 'center'), color_role='background_text',
    )
    assert PIXEL.fonts.credits == FontSpec(
        ASSET_ROOT / 'Atkinson_Hyperlegible_Mono' / 'static'
        / 'AtkinsonHyperlegibleMono-Regular.ttf',
        16, Alignment('center', 'center'), color_role='background_text',
    )


@pytest.mark.parametrize('theme', THEMES.values(), ids=THEMES.keys())
def test_registered_assets_and_licenses_exist(theme, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    paths = [getattr(theme.fonts, role.name).path for role in fields(theme.fonts)]
    if theme.skin is not None:
        paths.append(theme.skin.sheet)
    paths.extend(spec.sheet for _, spec in theme.sprites)
    licenses = {
        'Atkinson_Hyperlegible_Next': 'OFL.txt',
        'Atkinson_Hyperlegible_Mono': 'OFL.txt',
        'kenney_ui-pack-pixel-adventure': 'License.txt',
    }
    for path in paths:
        if path is None:
            continue
        assert path.is_absolute()
        assert path.is_file(), path
        package = path.relative_to(ASSET_ROOT).parts[0]
        license_path = ASSET_ROOT / package / licenses[package]
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
