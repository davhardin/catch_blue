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
    MENU_CREDITS_BOTTOM_MARGIN, MENU_VISIBLE_ROWS, MENU_TITLE_TOP, MENU_TOPICS_TITLE_TOP,
)
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


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def game(request):
    pygame.font.init()
    yield SimpleNamespace(renderer=Renderer(request.param))
    pygame.font.quit()


@pytest.fixture(scope='module')
def bank():
    return QuestionBank(Path(__file__).resolve().parents[1] / 'data' / 'questions')


def buttons_of(state):
    return [value for value in vars(state).values()
            if hasattr(value, 'rect') and hasattr(value, 'is_clicked')]


@pytest.mark.parametrize('make', [
    lambda game, bank: GameSelectState(game, bank),
    lambda game, bank: SubjectState(game, bank, 'catch_blue'),
], ids=['game_select', 'subject'])
def test_two_button_menus_stack_inside_the_screen(game, bank, make, monkeypatch):
    state = make(game, bank)
    buttons = buttons_of(state)
    assert len(buttons) == 2
    assert all(SCREEN.contains(button.rect) for button in buttons)
    first, second = sorted(buttons, key=lambda b: b.rect.top)
    assert first.rect.bottom < second.rect.top
    assert first.rect.left == second.rect.left
    assert first.rect.width == second.rect.width
    # Centered horizontally on the canvas, whatever its width.
    assert abs(first.rect.centerx - SCREEN.centerx) <= 1
    assert abs(first.rect.union(second.rect).centery - SCREEN.centery) <= 1
    titles = []
    original = game.renderer.text
    def record(surface, text, rect, role, *args, **kwargs):
        if role == 'title':
            titles.extend(game.renderer.text_rects([text], rect, role, kwargs.get('alignment')))
        original(surface, text, rect, role, *args, **kwargs)
    monkeypatch.setattr(game.renderer, 'text', record)
    state.draw(pygame.Surface(SCREEN.size))
    assert len(titles) == 1
    assert titles[0].top == MENU_TITLE_TOP
    assert SCREEN.contains(titles[0])
    assert titles[0].bottom < first.rect.top
    assert titles[0].centerx == SCREEN.centerx


def test_credits_line_sits_in_the_bottom_band():
    assert SCREEN.contains(CREDITS_RECT)
    assert SCREEN_HEIGHT - CREDITS_RECT.bottom == MENU_CREDITS_BOTTOM_MARGIN


def test_topics_screen_regions_do_not_collide(game, bank):
    state = TopicsState(game, bank, 'catch_blue', 'anatomy_physiology')
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


def test_topics_scroll_snaps_clamps_and_clicks_last_visible_row(game, bank):
    state = TopicsState(game, bank, 'catch_blue', 'anatomy_physiology')
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
def test_topics_screen_draws_without_touching_the_start_button(game, bank, position):
    state = TopicsState(game, bank, 'catch_blue', 'anatomy_physiology')
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
