"""Immutable, pygame-free visual theme definitions."""

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

Color = tuple[int, int, int]
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

THEMES = {'flat': FLAT, 'pixel': PIXEL}
DEFAULT_THEME = 'pixel'
