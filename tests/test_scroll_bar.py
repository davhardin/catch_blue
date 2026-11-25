"""M8.e: the Select Topics scroll bar, so the list scrolls on a touch screen.

`ScrollBar` is pure rect math. `TopicsState` routes button-down, motion, and
button-up to it before the list's hit test, so a tap on the bar never
toggles a checkbox. A&P's list has 21 rows (All plus 20 topics), 9 visible.
Touch screens send emulated mouse events with `touch=True`; nothing here
handles `FINGER*` events (m8.md trap 12).
"""

import pygame
import pytest

from constants import MENU_ROW_HEIGHT, MENU_SCROLL_THUMB_MIN_HEIGHT, MENU_VISIBLE_ROWS
from states.menus import TopicsState
from ui import ScrollBar

from conftest import A_AND_P, GameStub, land_press, question_dict, write_bank

ROWS = 21
REGION = pygame.Rect(540, 260, 540, MENU_VISIBLE_ROWS * MENU_ROW_HEIGHT)


def make_bar(row_count=ROWS):
    return ScrollBar(
        REGION, row_height=MENU_ROW_HEIGHT, visible_rows=MENU_VISIBLE_ROWS, row_count=row_count,
    )


# --- ScrollBar, pure --------------------------------------------------------


def test_bar_sits_beside_the_list_with_arrows_at_both_ends():
    bar = make_bar()
    assert bar.rect.left > REGION.right
    assert (bar.rect.top, bar.rect.bottom) == (REGION.top, REGION.bottom)
    assert bar.up_rect.top == bar.rect.top and bar.down_rect.bottom == bar.rect.bottom
    assert bar.up_rect.bottom < bar.track_rect.top < bar.track_rect.bottom < bar.down_rect.top
    assert bar.max_scroll == (ROWS - MENU_VISIBLE_ROWS) * MENU_ROW_HEIGHT == 624
    # A page is the visible rows less one, so the edge row stays in view.
    assert bar.page_scroll == (MENU_VISIBLE_ROWS - 1) * MENU_ROW_HEIGHT


def test_thumb_runs_from_the_track_top_to_flush_with_its_bottom():
    bar = make_bar()
    track = bar.track_rect
    top, bottom = bar.thumb_rect(0), bar.thumb_rect(bar.max_scroll)
    assert top.top == track.top
    assert bottom.bottom == track.bottom
    # Length = track x visible rows / total rows, never below the grab minimum.
    expected = max(MENU_SCROLL_THUMB_MIN_HEIGHT, track.height * MENU_VISIBLE_ROWS // ROWS)
    assert top.height == bottom.height == expected
    previous = None
    for offset in range(0, bar.max_scroll + 1, MENU_ROW_HEIGHT):
        thumb = bar.thumb_rect(offset)
        assert track.contains(thumb)
        assert previous is None or thumb.top > previous
        previous = thumb.top
    # Offsets out of range clamp to the ends.
    assert bar.thumb_rect(-50) == top and bar.thumb_rect(10_000) == bottom


def test_part_at_names_each_part_and_nothing_outside():
    bar = make_bar()
    offset = 4 * MENU_ROW_HEIGHT
    thumb = bar.thumb_rect(offset)
    assert bar.part_at(bar.up_rect.center, offset) == 'up'
    assert bar.part_at(bar.down_rect.center, offset) == 'down'
    assert bar.part_at(thumb.center, offset) == 'thumb'
    assert bar.part_at((bar.rect.centerx, thumb.top - 1), offset) == 'page_up'
    assert bar.part_at((bar.rect.centerx, thumb.bottom + 1), offset) == 'page_down'
    # The gap between an arrow and the track, and anything off the bar, is not a part.
    assert bar.part_at((bar.rect.centerx, bar.up_rect.bottom), offset) is None
    assert bar.part_at((bar.rect.left - 1, thumb.centery), offset) is None
    assert bar.part_at(REGION.center, offset) is None


def test_click_targets_move_a_row_or_a_page():
    bar = make_bar()
    offset = 3 * MENU_ROW_HEIGHT
    assert bar.click_target_offset('up', offset) == offset - MENU_ROW_HEIGHT
    assert bar.click_target_offset('down', offset) == offset + MENU_ROW_HEIGHT
    assert bar.click_target_offset('page_up', offset) == offset - bar.page_scroll
    assert bar.click_target_offset('page_down', offset) == offset + bar.page_scroll
    assert bar.click_target_offset('thumb', offset) is None


def test_starting_a_drag_without_moving_keeps_the_row():
    bar = make_bar()
    for offset in range(0, bar.max_scroll + 1, MENU_ROW_HEIGHT):
        thumb = bar.thumb_rect(offset)
        grab = thumb.height // 2
        target = bar.drag_target_offset(thumb.top + grab, grab)
        assert target // MENU_ROW_HEIGHT * MENU_ROW_HEIGHT == offset
    assert bar.drag_target_offset(bar.track_rect.top - 500, 0) == 0
    assert bar.drag_target_offset(bar.track_rect.bottom + 500, 0) == bar.max_scroll


@pytest.mark.parametrize('row_count', [0, 3, MENU_VISIBLE_ROWS])
def test_a_list_that_fits_has_no_bar_and_no_hit(row_count):
    bar = make_bar(row_count)
    assert bar.max_scroll == 0
    assert bar.thumb_rect(0) is None
    for point in (bar.up_rect.center, bar.down_rect.center, bar.track_rect.center):
        assert bar.part_at(point, 0) is None
    assert bar.drag_target_offset(bar.track_rect.bottom, 0) == 0


@pytest.mark.parametrize('kwargs', [
    {'row_height': 0},
    {'visible_rows': 0},
    {'row_count': -1},
    {'visible_rows': MENU_VISIBLE_ROWS - 1},  # list height no longer rows x row height
])
def test_invalid_geometry_is_rejected(kwargs):
    arguments = dict(row_height=MENU_ROW_HEIGHT, visible_rows=MENU_VISIBLE_ROWS, row_count=ROWS)
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        ScrollBar(REGION, **arguments)


# --- TopicsState: taps, drags, and touch ------------------------------------


def pointer(kind, pos, touch, **extra):
    return pygame.event.Event(kind, pos=pos, touch=touch, **extra)


def tap(state, pos, touch):
    state.handle_events([pointer(pygame.MOUSEBUTTONDOWN, pos, touch, button=1)])
    state.handle_events([pointer(pygame.MOUSEBUTTONUP, pos, touch, button=1)])


def tap_arrow(state, part, touch):
    """An arrow is a button: its scroll lands after the press animation."""
    pos = state.scroll_arrow_buttons[part].rect.center
    state.handle_events([pointer(pygame.MOUSEBUTTONDOWN, pos, touch, button=1)])
    land_press(state)
    state.handle_events([])  # a landed press swallows the next batch
    state.handle_events([pointer(pygame.MOUSEBUTTONUP, pos, touch, button=1)])


def checked(state):
    return [state.all_checkbox.checked, *(box.checked for _, box in state.topic_checkboxes)]


@pytest.fixture
def topics(flat_renderer, bank):
    # The bar's behavior does not depend on the theme; its placement on both
    # themes is checked in test_menu_layout.py and test_pixel_layout.py.
    state = TopicsState(GameStub(bank, flat_renderer), 'catch_blue', A_AND_P)
    assert len(checked(state)) == ROWS and state.max_scroll == 624
    return state


@pytest.mark.parametrize('touch', [False, True], ids=['mouse', 'touch'])
def test_arrows_move_one_row_and_clamp(topics, touch):
    before = checked(topics)
    tap_arrow(topics, 'down', touch)
    assert topics.scroll_offset == MENU_ROW_HEIGHT
    tap_arrow(topics, 'up', touch)
    assert topics.scroll_offset == 0
    tap_arrow(topics, 'up', touch)
    assert topics.scroll_offset == 0
    topics._set_scroll_offset(topics.max_scroll)
    tap_arrow(topics, 'down', touch)
    assert topics.scroll_offset == topics.max_scroll
    assert checked(topics) == before


@pytest.mark.parametrize('touch', [False, True], ids=['mouse', 'touch'])
def test_track_taps_move_a_page_and_clamp(topics, touch):
    bar = topics.scroll_bar
    page = (MENU_VISIBLE_ROWS - 1) * MENU_ROW_HEIGHT
    before = checked(topics)

    def below_thumb():
        return (bar.rect.centerx, bar.thumb_rect(topics.scroll_offset).bottom + 4)

    def above_thumb():
        return (bar.rect.centerx, bar.thumb_rect(topics.scroll_offset).top - 4)

    tap(topics, below_thumb(), touch)
    assert topics.scroll_offset == page
    tap(topics, below_thumb(), touch)
    assert topics.scroll_offset == topics.max_scroll  # 2 pages would pass the end
    tap(topics, above_thumb(), touch)
    assert topics.scroll_offset == topics.max_scroll - page
    tap(topics, above_thumb(), touch)
    assert topics.scroll_offset == 0
    assert checked(topics) == before


@pytest.mark.parametrize('touch', [False, True], ids=['mouse', 'touch'])
def test_thumb_drag_snaps_to_rows_and_ends_on_button_up_off_the_bar(topics, touch):
    bar = topics.scroll_bar
    before = checked(topics)
    start = bar.thumb_rect(0).center
    topics.handle_events([pointer(pygame.MOUSEBUTTONDOWN, start, touch, button=1)])
    for y in range(start[1], bar.rect.bottom + 60, 13):
        topics.handle_events([pointer(pygame.MOUSEMOTION, (start[0], y), touch, rel=(0, 13), buttons=(1, 0, 0))])
        assert topics.scroll_offset % MENU_ROW_HEIGHT == 0
        assert 0 <= topics.scroll_offset <= topics.max_scroll
    assert topics.scroll_offset == topics.max_scroll
    # Released over the list, well off the bar: the drag still ends.
    topics.handle_events([pointer(pygame.MOUSEBUTTONUP, topics.scroll_region.center, touch, button=1)])
    topics.handle_events([pointer(pygame.MOUSEMOTION, start, touch, rel=(0, -400), buttons=(0, 0, 0))])
    assert topics.scroll_offset == topics.max_scroll
    assert bar.thumb_rect(topics.scroll_offset).bottom == bar.track_rect.bottom
    assert checked(topics) == before


def test_leaving_the_window_ends_a_drag(topics):
    bar = topics.scroll_bar
    start = bar.thumb_rect(0).center
    topics.handle_events([pointer(pygame.MOUSEBUTTONDOWN, start, False, button=1)])
    topics.handle_events([pygame.event.Event(pygame.WINDOWLEAVE)])
    topics.handle_events([pointer(pygame.MOUSEMOTION, (start[0], bar.rect.bottom), False, rel=(0, 300), buttons=(1, 0, 0))])
    assert topics.scroll_offset == 0


def test_bar_taps_never_toggle_a_checkbox_at_any_offset(topics):
    bar = topics.scroll_bar
    before = checked(topics)
    for offset in range(0, topics.max_scroll + 1, MENU_ROW_HEIGHT):
        topics._set_scroll_offset(offset)
        thumb = bar.thumb_rect(offset)
        for y in (thumb.centery, bar.track_rect.top + 1, bar.track_rect.bottom - 1):
            topics._set_scroll_offset(offset)
            tap(topics, (bar.rect.centerx, y), touch=True)
        assert checked(topics) == before


def test_a_short_list_draws_no_bar_and_ignores_taps_there(flat_renderer, tmp_path):
    bank = write_bank(tmp_path, [
        question_dict(f'q-{topic}', subject=A_AND_P, topic=topic, subtopic='Overview')
        for topic in ('cells', 'tissues', 'blood')
    ])
    state = TopicsState(GameStub(bank, flat_renderer), 'catch_blue', A_AND_P)
    bar = state.scroll_bar
    assert state.max_scroll == 0 and bar.thumb_rect(0) is None
    before = checked(state)
    for point in (bar.up_rect.center, bar.track_rect.center, bar.down_rect.center):
        tap(state, point, touch=True)
        land_press(state)
    assert state.scroll_offset == 0 and checked(state) == before
    screen = pygame.Surface((1600, 900))
    state.draw(screen)
    background = flat_renderer.color('background')
    area = pygame.image.tobytes(screen.subsurface(bar.rect), 'RGB')
    assert area == bytes(background) * (bar.rect.width * bar.rect.height)
