"""Immutable, pygame-free visual theme definitions."""

from colorsys import hsv_to_rgb, rgb_to_hsv
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

Color = tuple[int, int, int]
Accent = Literal['blue', 'red', 'green', 'yellow']
ACCENT_KEYS: tuple[Accent, ...] = ('blue', 'red', 'green', 'yellow')
ASSET_ROOT = Path(__file__).resolve().parent / 'assets'


@dataclass(frozen=True)
class Alignment:
    horizontal: Literal['left', 'center'] = 'left'
    vertical: Literal['top', 'center'] = 'top'


@dataclass(frozen=True)
class FontSpec:
    path: Path | None
    size: int
    alignment: Alignment = field(default_factory=Alignment)
    color_role: str = 'text'


@dataclass(frozen=True)
class Palette:
    background: Color
    cell: Color
    cell_move: Color
    cell_line: Color
    selected_line: Color
    hover_line: Color
    label: Color
    text: Color
    choice_text: Color
    text_inactive: Color
    panel: Color
    panel_line: Color
    button: Color
    button_inactive: Color
    correct: Color

    player: Color
    blue: Color
    red: Color
    green: Color
    yellow: Color
    character: Color
    background_text: Color = (245, 245, 245)
    highlight: Color = (245, 245, 245)


@dataclass(frozen=True)
class Fonts:
    label: FontSpec
    prompt: FontSpec
    choice: FontSpec
    button: FontSpec
    title: FontSpec
    counter: FontSpec
    checkbox: FontSpec
    result: FontSpec

    credits: FontSpec = field(default_factory=lambda: FontSpec(
        None, 20, Alignment('center', 'center'), color_role='background_text',
    ))


@dataclass(frozen=True)
class NineSlice:
    source: tuple[int, int, int, int]
    insets: tuple[int, int, int, int]
    # Exact sheet colors swapped once at load, (sheet color, drawn color).
    recolor: tuple[tuple[Color, Color], ...] = ()


@dataclass(frozen=True)
class HueShift:
    source_hue: int
    target_hue: int
    tolerance: int = 18
    minimum_saturation: float = 0.10


@dataclass(frozen=True)
class Skin:
    sheet: Path
    scale: int
    elements: tuple[tuple[str, NineSlice], ...]
    packed_tile_size: int | None = None
    packed_tile_gap: int = 0
    hue_shift: HueShift | None = None


@dataclass(frozen=True)
class SpriteSpec:
    sheet: Path
    source: tuple[int, int, int, int]


@dataclass(frozen=True)
class Layout:
    button_padding: int = 0
    choice_padding: int = 0
    show_cell_hover_ring: bool = True
    highlight_catchable_cell: bool = False



@dataclass(frozen=True)
class RevealStyle:
    outline_width: int = 4
    pulse_period_ms: int = 1000
    minimum_brightness: float = 0.55

    desaturate_alpha: int = 220
    fade_alpha: int = 100


@dataclass(frozen=True)
class CellLift:
    rest_px: int = 0
    hover_px: int = 0
    pop_ms: int = 0


@dataclass(frozen=True)
class Theme:
    name: str
    palette: Palette
    fonts: Fonts
    skin: Skin | None = None
    sprites: tuple[tuple[str, SpriteSpec], ...] = ()
    layout: Layout = field(default_factory=Layout)
    reveal: RevealStyle = field(default_factory=RevealStyle)
    cell_lift: CellLift = field(default_factory=CellLift)
    answer_lift: CellLift = field(default_factory=CellLift)
    menu_lift: CellLift = field(default_factory=CellLift)
    board_label_sizes: tuple[tuple[int, int], ...] = ()


def shift_color_to_hue(color: Color, target_hue: int) -> Color:
    _, saturation, value = rgb_to_hsv(
        *(channel / 255 for channel in color)
    )
    red, green, blue = hsv_to_rgb(
        (target_hue % 360) / 360,
        saturation,
        value,
    )
    return (
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )


def _mix_color(start: Color, end: Color, amount: float) -> Color:
    return (
        round(start[0] + (end[0] - start[0]) * amount),
        round(start[1] + (end[1] - start[1]) * amount),
        round(start[2] + (end[2] - start[2]) * amount),
    )


FLAT = Theme(
    name='flat',
    palette=Palette(
        background=(24, 26, 32),
        cell=(58, 64, 78),
        cell_move=(60, 88, 90),
        cell_line=(120, 130, 148),
        selected_line=(255, 0, 0),
        hover_line=(120, 130, 148),
        label=(245, 245, 245),
        text=(245, 245, 245),
        choice_text=(255, 255, 255),
        text_inactive=(145, 148, 156),
        panel=(58, 64, 78),
        panel_line=(120, 130, 148),
        button=(60, 88, 90),
        button_inactive=(75, 78, 86),
        correct=(0, 100, 70),

        player=(230, 159, 0),
        blue=(0, 114, 178),
        red=(213, 94, 0),
        green=(0, 158, 115),
        yellow=(240, 228, 66),
        character=(180, 180, 180),
    ),
    fonts=Fonts(
        label=FontSpec(
            ASSET_ROOT / 'Atkinson_Hyperlegible_Next' / 'static'
            / 'AtkinsonHyperlegibleNext-Regular.ttf', 16, Alignment('center', 'center'),
        ),
        prompt=FontSpec(None, 32),
        choice=FontSpec(None, 32, Alignment('center', 'center'), 'choice_text'),
        button=FontSpec(None, 36),
        title=FontSpec(None, 56),
        counter=FontSpec(None, 36),
        checkbox=FontSpec(None, 30),
        result=FontSpec(None, 40),
    ),
    board_label_sizes=((7, 14), (9, 12)),
)

_NEXT = ASSET_ROOT / 'Atkinson_Hyperlegible_Next' / 'static' / 'AtkinsonHyperlegibleNext-Regular.ttf'
_MONO = ASSET_ROOT / 'Atkinson_Hyperlegible_Mono' / 'static' / 'AtkinsonHyperlegibleMono-Regular.ttf'
_MONO_BOLD = _MONO.with_name('AtkinsonHyperlegibleMono-Bold.ttf')
_CENTER = Alignment('center', 'center')

PIXEL = Theme(
    name='pixel',
    palette=replace(
        FLAT.palette,
        background=(69, 82, 91), cell=(148, 175, 198), cell_move=(196, 213, 226),
        button=(148, 175, 198), cell_line=(0, 0, 0), panel_line=(0, 0, 0),
        selected_line=(255, 241, 210), hover_line=(35, 40, 45),
        label=(35, 40, 45), text=(35, 40, 45), choice_text=(35, 40, 45),
        text_inactive=(35, 40, 45), panel=(255, 241, 210),
        button_inactive=(100, 118, 133), correct=(114, 184, 78),
        background_text=(255, 241, 210), highlight=(69, 82, 91),
    ),
    fonts=Fonts(
        label=FontSpec(_NEXT, 20, _CENTER, 'label'),
        prompt=FontSpec(_NEXT, 24),
        choice=FontSpec(_NEXT, 24, _CENTER),
        button=FontSpec(_MONO, 24, _CENTER),
        title=FontSpec(_MONO_BOLD, 40, color_role='background_text'),
        counter=FontSpec(_MONO, 28, color_role='background_text'),
        checkbox=FontSpec(_MONO, 22, color_role='background_text'),
        result=FontSpec(_MONO_BOLD, 30),

        credits=FontSpec(_MONO, 16, _CENTER, color_role='background_text'),
    ),
    skin=Skin(
        ASSET_ROOT / 'kenney_ui-pack-pixel-adventure' / 'Tilesheets'
        / 'Large tiles' / 'Thick outline' / 'tilemap_packed.png',
        2,
        (
            # Plain panel/button borders are five pixels; colored corners extend to six.
            ('panel', NineSlice((0, 0, 32, 32), (5, 5, 5, 5))),
            ('button.normal', NineSlice((64, 0, 32, 32), (5, 5, 5, 5))),
            ('button.inactive', NineSlice((96, 0, 32, 32), (5, 5, 5, 5))),
            ('button.correct', NineSlice((256, 64, 32, 32), (6, 6, 6, 6))),

            # Crop outer cell outlines to leave 116px faces at scale two;
            # move insets still preserve diagonal corner details outside the label band.
            ('cell.normal', NineSlice((66, 2, 28, 28), (3, 3, 3, 3))),
            ('cell.move', NineSlice((289, 65, 30, 30), (5, 5, 5, 5))),

        ),
    ),
    layout=Layout(
        button_padding=10,
        choice_padding=12,
        show_cell_hover_ring=False,
        highlight_catchable_cell=True,
    ),
    cell_lift=CellLift(rest_px=2, hover_px=6, pop_ms=120),
    answer_lift=CellLift(rest_px=2, hover_px=6, pop_ms=120),
    menu_lift=CellLift(rest_px=2, hover_px=6, pop_ms=120),
    board_label_sizes=((7, 14), (9, 12)),
)

_ACCENT_HUES: dict[Accent, int] = {
    'blue': 207,
    'red': 27,
    'green': 164,
    'yellow': 56,
}

_BLUE_GREY_ROLES = (
    'background',
    'cell',
    'cell_move',
    'button',
    'button_inactive',
    'highlight',
)


def with_accent(theme: Theme, accent: Accent) -> Theme:
    if accent not in ACCENT_KEYS:
        raise ValueError(f'Unknown accent: {accent}')
    if theme is not PIXEL:
        raise ValueError('Hue-remapped accents require the PIXEL theme')
    if accent == 'blue':
        return PIXEL

    target_hue = _ACCENT_HUES[accent]
    palette_changes = {
        role: shift_color_to_hue(
            getattr(theme.palette, role),
            target_hue,
        )
        for role in _BLUE_GREY_ROLES
    }
    palette = replace(theme.palette, **palette_changes)

    if accent == 'red':
        palette = replace(palette, red=(149, 66, 0))

    assert theme.skin is not None
    skin = replace(
        theme.skin,
        hue_shift=HueShift(
            source_hue=_ACCENT_HUES['blue'],
            target_hue=target_hue,
        ),
    )
    return replace(
        theme,
        name=f'pixel-{accent}',
        palette=palette,
        skin=skin,
    )


PIXEL_ACCENTS: dict[Accent, Theme] = {
    accent: with_accent(PIXEL, accent)
    for accent in ACCENT_KEYS
}

_UI_SHEET = (
    ASSET_ROOT
    / 'kenney_pixel-ui-pack'
    / 'Spritesheet'
    / 'UIpackSheet_transparent.png'
)

_UI_COLOR_X: dict[Accent, int] = {
    'yellow': 108,
    'green': 216,
    'red': 324,
    'blue': 432,
}

_UI_FACE_COLORS: dict[Accent, Color] = {
    'blue': (30, 167, 225),
    'red': (232, 106, 23),
    'green': (115, 205, 75),
    'yellow': (255, 204, 0),
}

# The sheet's drop shadow under each solid face; lifted elements sit on it.
_UI_SHADOW_COLORS: dict[Accent, Color] = {
    'blue': (22, 110, 147),
    'red': (170, 78, 17),
    'green': (71, 131, 44),
    'yellow': (168, 134, 0),
}

_UI_CELL_FACE = (238, 238, 238)

# Resting cells sit below the sheet's white face; legal moves glow above it.
_UI_REST_BASE = (200, 200, 200)
_UI_GLOW_BASE = (250, 250, 250)

# One outline pixel and two highlight pixels; the bottom adds a 2 px shadow.
_UI_BEVEL_INSETS = (3, 3, 3, 5)


def _ui_slice(
    x: int,
    y: int,
    insets: tuple[int, int, int, int] = _UI_BEVEL_INSETS,
    recolor: tuple[tuple[Color, Color], ...] = (),
) -> NineSlice:
    return NineSlice(
        source=(x, y, 52, 52),
        insets=insets,
        recolor=recolor,
    )


def _ui_theme(accent: Accent) -> Theme:
    x = _UI_COLOR_X[accent]
    face = _UI_FACE_COLORS[accent]
    dark_accent = _mix_color((0, 0, 0), face, 0.45)
    rest_face = _mix_color(_UI_REST_BASE, face, 0.10)
    move_face = _mix_color(_UI_GLOW_BASE, face, 0.25)
    cell = _ui_slice(x, 144, recolor=((_UI_CELL_FACE, rest_face),))

    palette = replace(
        PIXEL.palette,
        background=dark_accent,
        cell=rest_face,
        cell_move=move_face,
        selected_line=dark_accent,
        panel=_UI_CELL_FACE,
        panel_line=_UI_SHADOW_COLORS[accent],
        button=face,
        button_inactive=_UI_CELL_FACE,
        correct=_UI_FACE_COLORS['green'],
        highlight=dark_accent,
    )

    skin = Skin(
        sheet=_UI_SHEET,
        scale=2,
        # Each color block opens with two one-tile-tall bars (y 0 and 18);
        # its 3x3 panels start below them: solid at y 36, outline at y 144.
        # The outline face is recolored to palette.cell, so the move tint
        # replaces it.
        elements=(
            ('panel', _ui_slice(0, 162, (2, 3, 2, 2))),
            ('button.normal', _ui_slice(x, 36)),
            ('button.inactive', _ui_slice(0, 36)),
            ('button.correct', _ui_slice(_UI_COLOR_X['green'], 36)),
            ('cell.normal', cell),
            ('cell.move', cell),
        ),
        packed_tile_size=16,
        packed_tile_gap=2,
    )

    return replace(
        PIXEL,
        name=f'ui-{accent}',
        palette=palette,
        skin=skin,
    )


UI_ACCENTS: dict[Accent, Theme] = {
    accent: _ui_theme(accent)
    for accent in ACCENT_KEYS
}

UI_BLUE = UI_ACCENTS['blue']
UI_RED = UI_ACCENTS['red']
UI_GREEN = UI_ACCENTS['green']
UI_YELLOW = UI_ACCENTS['yellow']

_ACCENT_FAMILIES = {
    'pixel': PIXEL_ACCENTS,
    'ui': UI_ACCENTS,
}

_THEME_FAMILIES = {
    theme.name: family_name
    for family_name, family in _ACCENT_FAMILIES.items()
    for theme in family.values()
}

_THEME_ACCENTS: dict[str, Accent] = {
    theme.name: accent
    for family in _ACCENT_FAMILIES.values()
    for accent, theme in family.items()
}


def theme_accent(theme: Theme) -> Accent | None:
    return _THEME_ACCENTS.get(theme.name)


def resolve_accent(theme: Theme, accent: Accent) -> Theme:
    if accent not in ACCENT_KEYS:
        raise ValueError(f'Unknown accent: {accent}')

    family_name = _THEME_FAMILIES.get(theme.name)
    if family_name is None:
        return theme

    return _ACCENT_FAMILIES[family_name][accent]


THEMES = {
    'flat': FLAT,
    'pixel': PIXEL,
    'pixel-red': PIXEL_ACCENTS['red'],
    'pixel-green': PIXEL_ACCENTS['green'],
    'pixel-yellow': PIXEL_ACCENTS['yellow'],
    'ui-blue': UI_BLUE,
    'ui-red': UI_RED,
    'ui-green': UI_GREEN,
    'ui-yellow': UI_YELLOW,
}
DEFAULT_THEME = 'ui-blue'
