"""Immutable, pygame-free visual theme definitions."""

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
    # A loose tile file read in place of the skin's sheet. tile_size is the
    # art's width in pixels; a file exported bigger (256 px for a 32 px tile)
    # is read back at one pixel per art pixel, so source and insets stay in
    # art pixels.
    tile: Path | None = None
    tile_size: int | None = None


@dataclass(frozen=True)
class Skin:
    sheet: Path
    scale: int
    elements: tuple[tuple[str, NineSlice], ...]


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

_PIXEL_SHEET = (
    ASSET_ROOT / 'kenney_ui-pack-pixel-adventure' / 'Tilesheets'
    / 'Large tiles' / 'Thick outline' / 'tilemap_packed.png'
)

# Hand-drawn button and cell tiles, one set per accent. Each is a 32 px tile
# in the Kenney sheet's layout (exported at 8x); the panel stays on the sheet.
_PIXEL_TILE_DIR = ASSET_ROOT / 'four_color_buttons'
_PIXEL_TILE_SIZE = 32
_PIXEL_TILE_FILES: dict[Accent, dict[str, str]] = {
    'blue': {
        'normal': 'blue_button_normal_v2.png',
        'inactive': 'blue_button_inactive_v2.png',
        'correct': 'blue_button_correct_v2.png',
        'move': 'blue_button_move_v2.png',
    },
    'red': {
        'normal': 'red_button_normal.png',
        'inactive': 'red_button_inactive.png',
        'correct': 'red_button_correct.png',
        'move': 'red_cell_move.png',
    },
    'green': {
        'normal': 'green_button_normal.png',
        'inactive': 'green_button_inactive.png',
        'correct': 'green_button_correct.png',
        'move': 'green_cell_move.png',
    },
    'yellow': {
        'normal': 'yellow_button_normal.png',
        'inactive': 'yellow_button_inactive.png',
        'correct': 'yellow_button_correct.png',
        'move': 'yellow_cell_move.png',
    },
}

# Colors sampled from each accent's tiles: the 2 px outer outline, the normal
# button's face (which resting cells crop), the move tile's face, and the
# inactive face. Renderer.cell finds a legal move's face by palette.cell, so
# where the move face differs from the resting face it is recolored to match.
_PIXEL_TILE_COLORS: dict[Accent, dict[str, Color]] = {
    'blue': {
        'outline': (66, 80, 107),
        'face': (133, 150, 198),
        'move_face': (133, 160, 198),
        'inactive_face': (85, 103, 133),
    },
    'red': {
        'outline': (107, 81, 81),
        'face': (199, 149, 149),
        'move_face': (199, 149, 149),
        'inactive_face': (133, 99, 99),
    },
    'green': {
        'outline': (81, 107, 82),
        'face': (150, 200, 150),
        'move_face': (149, 199, 150),
        'inactive_face': (100, 133, 99),
    },
    'yellow': {
        'outline': (107, 107, 29),
        'face': (198, 199, 100),
        'move_face': (199, 199, 100),
        'inactive_face': (133, 132, 50),
    },
}

# Roles every pixel accent shares: cream panels, dark text, black sockets.
_PIXEL_BASE_PALETTE = replace(
    FLAT.palette,
    cell_line=(0, 0, 0), panel_line=(0, 0, 0),
    selected_line=(255, 241, 210), hover_line=(35, 40, 45),
    label=(35, 40, 45), text=(35, 40, 45), choice_text=(35, 40, 45),
    text_inactive=(35, 40, 45), panel=(255, 241, 210),
    correct=(114, 184, 78), background_text=(255, 241, 210),
)


def _pixel_palette(accent: Accent) -> Palette:
    colors = _PIXEL_TILE_COLORS[accent]
    # The window sits 15% darker than the tiles' outline, and legal moves
    # glow 47% of the way to white: the Kenney sheet's own proportions.
    background = _mix_color(colors['outline'], (0, 0, 0), 0.15)
    palette = replace(
        _PIXEL_BASE_PALETTE,
        background=background,
        highlight=background,
        cell=colors['face'],
        cell_move=_mix_color(colors['face'], (255, 255, 255), 0.47),
        button=colors['face'],
        button_inactive=colors['inactive_face'],
    )
    if accent == 'red':
        # A darker Red so it stands out on its own board.
        palette = replace(palette, red=(149, 66, 0))
    return palette


def _pixel_tile(
    file_name: str,
    source: tuple[int, int, int, int],
    insets: tuple[int, int, int, int],
    recolor: tuple[tuple[Color, Color], ...] = (),
) -> NineSlice:
    return NineSlice(
        source,
        insets,
        recolor=recolor,
        tile=_PIXEL_TILE_DIR / file_name,
        tile_size=_PIXEL_TILE_SIZE,
    )


def _pixel_skin(accent: Accent) -> Skin:
    files = _PIXEL_TILE_FILES[accent]
    colors = _PIXEL_TILE_COLORS[accent]
    move_recolor = (
        ((colors['move_face'], colors['face']),)
        if colors['move_face'] != colors['face'] else ()
    )
    return Skin(
        _PIXEL_SHEET,
        2,
        (
            # Plain panel/button borders are five pixels; colored corners extend to six.
            ('panel', NineSlice((0, 0, 32, 32), (5, 5, 5, 5))),
            ('button.normal', _pixel_tile(files['normal'], (0, 0, 32, 32), (5, 5, 5, 5))),
            ('button.inactive', _pixel_tile(files['inactive'], (0, 0, 32, 32), (5, 5, 5, 5))),
            ('button.correct', _pixel_tile(files['correct'], (0, 0, 32, 32), (6, 6, 6, 6))),

            # Crop outer cell outlines to leave 116px faces at scale two;
            # move insets still preserve diagonal corner details outside the label band.
            ('cell.normal', _pixel_tile(files['normal'], (2, 2, 28, 28), (3, 3, 3, 3))),
            ('cell.move', _pixel_tile(
                files['move'], (1, 1, 30, 30), (5, 5, 5, 5), move_recolor,
            )),
        ),
    )


PIXEL = Theme(
    name='pixel',
    palette=_pixel_palette('blue'),
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
    skin=_pixel_skin('blue'),
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

def _pixel_accent(accent: Accent) -> Theme:
    if accent == 'blue':
        return PIXEL
    return replace(
        PIXEL,
        name=f'pixel-{accent}',
        palette=_pixel_palette(accent),
        skin=_pixel_skin(accent),
    )


PIXEL_ACCENTS: dict[Accent, Theme] = {
    accent: _pixel_accent(accent)
    for accent in ACCENT_KEYS
}

_ACCENT_FAMILIES = {
    'pixel': PIXEL_ACCENTS,
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
}
DEFAULT_THEME = 'pixel'
