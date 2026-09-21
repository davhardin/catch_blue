"""Menu geometry invariants that must hold at any canvas size.

The menu screens were laid out for 1280x720 and the canvas is now 1600x900
(M6.e, 2026-09-07). M6.f.6 in `milestones/m6.md` describes deriving the menu
geometry from the screen size; these tests assert only the properties that
hold before and after that change, so they guard the change rather than
freezing today's numbers.
"""

from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

from constants import (
    SCREEN_HEIGHT, SCREEN_WIDTH, MENU_ROW_HEIGHT, MENU_BOTTOM_MARGIN,
    MENU_CREDITS_BOTTOM_MARGIN, MENU_VISIBLE_ROWS, MENU_TITLE_OFFSET, MENU_TOPICS_TITLE_TOP,
)
from modes import get_mode
from questions import QuestionBank
from render import Renderer
from states.menus import (
    CREDITS_RECT,
    GameSelectState,
    SubjectState,
    TopicsState,
)
from theme import FLAT, PIXEL

SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
DEFAULT_SETTINGS = get_mode('catch_blue').settings_spec().default


@pytest.fixture(scope='module')
def bank():
    return QuestionBank(Path(__file__).resolve().parents[1] / 'data' / 'questions')


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def game(request, bank):
    pygame.font.init()
    yield SimpleNamespace(
        bank=bank,
        settings_by_mode={'catch_blue': DEFAULT_SETTINGS},
        settings_mode='catch_blue',
        topic_selections={},
        renderer=Renderer(request.param),
    )
    pygame.font.quit()


def buttons_of(state):
    # Game Select keeps its mode buttons in a dict (one per registered mode);
    # flatten containers so every button on the screen is found.
    found = []
    for value in vars(state).values():
        items = value.values() if isinstance(value, dict) else (
            value if isinstance(value, (list, tuple)) else (value,)
        )
        for item in items:
            if hasattr(item, 'rect') and hasattr(item, 'is_clicked') and item not in found:
                found.append(item)
    return found


@pytest.mark.parametrize('make', [
    lambda game: GameSelectState(game),
    lambda game: SubjectState(game, 'catch_blue'),
], ids=['game_select', 'subject'])
def test_two_button_menus_stack_inside_the_screen(game, make, monkeypatch):
    state = make(game)
    buttons = buttons_of(state)
    assert all(SCREEN.contains(button.rect) for button in buttons)
    # The centered stack; a Back button (M7.c) sits outside it, bottom-left.
    stack = sorted((b for b in buttons if b.text != 'Back'), key=lambda b: b.rect.top)
    assert len(stack) >= 2
    for upper, lower in zip(stack, stack[1:]):
        assert upper.rect.bottom < lower.rect.top
        assert upper.rect.left == lower.rect.left
        assert upper.rect.width == lower.rect.width
    first, second = stack[0], stack[1]
    # Centered horizontally on the canvas, whatever its width.
    assert abs(first.rect.centerx - SCREEN.centerx) <= 1
    whole = first.rect.unionall([b.rect for b in stack[1:]])
    assert SCREEN_HEIGHT // 8 < whole.top and whole.bottom < SCREEN_HEIGHT - SCREEN_HEIGHT // 8
    # Vertically centered as a block, however many buttons the screen stacks
    # (Game Select grew a third in M7.b).
    assert abs(whole.centery - SCREEN.centery) <= 1
    for back in (b for b in buttons if b.text == 'Back'):
        assert not back.rect.colliderect(whole)
    titles = []
    original = game.renderer.text
    def record(surface, text, rect, role, *args, **kwargs):
        if role == 'title':
            titles.extend(game.renderer.text_rects([text], rect, role, kwargs.get('alignment')))
        original(surface, text, rect, role, *args, **kwargs)
    monkeypatch.setattr(game.renderer, 'text', record)
    state.draw(pygame.Surface(SCREEN.size))
    assert len(titles) == 1
    assert titles[0].top == first.rect.top - MENU_TITLE_OFFSET
    assert SCREEN.contains(titles[0])
    assert titles[0].bottom < first.rect.top
    assert titles[0].centerx == SCREEN.centerx


def test_credits_line_sits_in_the_bottom_band():
    assert SCREEN.contains(CREDITS_RECT)
    assert SCREEN_HEIGHT - CREDITS_RECT.bottom == MENU_CREDITS_BOTTOM_MARGIN


def test_topics_screen_regions_do_not_collide(game):
    state = TopicsState(game, 'catch_blue', 'anatomy_physiology')
    region = state.scroll_region
    start = state.start_button.rect
    assert SCREEN.contains(region)
    assert SCREEN.contains(start)
    assert region.bottom < start.top, 'scroll region must end above the Start button'
    assert abs(start.centerx - SCREEN.centerx) <= 1
    assert SCREEN_HEIGHT - start.bottom == MENU_BOTTOM_MARGIN
    checkboxes = [state.all_checkbox, *(c for _, c in state.topic_checkboxes)]
    # Every checkbox row starts inside the region horizontally, and the first
    # row is fully visible without scrolling.
    assert all(region.left <= c.hit_rect.left and c.hit_rect.right <= region.right
               for c in checkboxes)
    assert region.contains(state.all_checkbox.hit_rect)
    assert all(c.rect.left == start.left for c in checkboxes)
    title = game.renderer.text_rects(['Select Topics'],
        pygame.Rect(0, MENU_TOPICS_TITLE_TOP, SCREEN_WIDTH, 80), 'title')[0]
    assert SCREEN.contains(title)
    assert title.bottom < region.top
    assert region.height % MENU_ROW_HEIGHT == 0
    assert state.max_scroll % MENU_ROW_HEIGHT == 0
    for offset in range(0, state.max_scroll + 1, MENU_ROW_HEIGHT):
        state._set_scroll_offset(offset)
        visible = [c.hit_rect.move(0, -state.scroll_offset) for c in checkboxes]
        visible = [rect for rect in visible if region.colliderect(rect)]
        assert len(visible) == min(len(checkboxes), MENU_VISIBLE_ROWS)
        assert all(region.contains(rect) for rect in visible)
    # Scrolling to the end brings the last row fully into view.
    state._set_scroll_offset(state.max_scroll)
    last = checkboxes[-1].hit_rect.move(0, -state.scroll_offset)
    assert region.contains(last)


def test_topics_scroll_snaps_clamps_and_clicks_last_visible_row(game):
    state = TopicsState(game, 'catch_blue', 'anatomy_physiology')
    assert state.max_scroll > 0
    state._set_scroll_offset(MENU_ROW_HEIGHT + 7)
    assert state.scroll_offset == MENU_ROW_HEIGHT
    state.handle_events([pygame.event.Event(pygame.MOUSEWHEEL, y=-1)])
    assert state.scroll_offset == min(2 * MENU_ROW_HEIGHT, state.max_scroll)
    state.handle_events([pygame.event.Event(pygame.MOUSEWHEEL, y=-100)])
    assert state.scroll_offset == state.max_scroll
    checkbox = state.topic_checkboxes[-1][1]
    point = checkbox.hit_rect.move(0, -state.scroll_offset).center
    state.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)])
    assert not checkbox.checked
    assert not state.all_checkbox.checked
    hidden = state.all_checkbox.hit_rect.move(0, -state.scroll_offset).center
    assert not state.scroll_region.collidepoint(hidden)
    selected = [c.checked for _, c in state.topic_checkboxes]
    state.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=hidden)])
    assert [c.checked for _, c in state.topic_checkboxes] == selected
    state.handle_events([pygame.event.Event(pygame.MOUSEWHEEL, y=100)])
    assert state.scroll_offset == 0
    state._set_scroll_offset(-1)
    assert state.scroll_offset == 0


@pytest.mark.parametrize('position', ['top', 'middle', 'bottom'])
def test_topics_screen_draws_without_touching_the_start_button(game, position):
    state = TopicsState(game, 'catch_blue', 'anatomy_physiology')
    offset = {'top': 0, 'middle': state.max_scroll // 2, 'bottom': state.max_scroll}[position]
    state._set_scroll_offset(offset)
    screen = pygame.Surface(SCREEN.size)
    state.draw(screen)
    # Drawing the (clipped) list must not spill below the region, so the
    # band between the region and Start stays background.
    band = pygame.Rect(state.scroll_region.left, state.scroll_region.bottom,
                       state.scroll_region.width, state.start_button.rect.top - state.scroll_region.bottom)
    assert band.height > 0
    background = game.renderer.color('background')
    pixels = pygame.image.tobytes(screen.subsurface(band), 'RGB')
    assert pixels == bytes(background) * (band.width * band.height)
