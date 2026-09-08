"""Credits use real fonts/rendering without changing menu hit targets."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pygame
import pytest

from constants import (
    SCREEN_HEIGHT, SCREEN_WIDTH, MENU_BUTTON_LEFT, MENU_BUTTON_WIDTH,
    MENU_BUTTON_HEIGHT, MENU_BUTTON_GAP, MENU_FIRST_BUTTON_TOP, MENU_START_TOP,
    MENU_CREDITS_SIDE_MARGIN, MENU_CREDITS_TOP, MENU_CREDITS_HEIGHT,
)
from questions import QuestionBank
from render import Renderer
from states.menus import CREDITS_RECT, CREDITS_TEXT, GameSelectState, SubjectState, TopicsState
from theme import FLAT, PIXEL


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def renderer(request):
    pygame.font.init()
    yield Renderer(request.param)
    pygame.font.quit()


@pytest.fixture
def menus(renderer):
    bank = QuestionBank(Path(__file__).resolve().parents[1] / 'data' / 'questions')
    game = SimpleNamespace(renderer=renderer)
    return (
        GameSelectState(game, bank),
        SubjectState(game, bank, 'catch_blue'),
        TopicsState(game, bank, 'catch_blue', 'anatomy_physiology'),
    )


class RecordingSurface(pygame.Surface):
    def blit(self, source, dest, *args, **kwargs):
        self.last_blit_bounds = source.get_rect(topleft=pygame.Rect(dest).topleft)
        return super().blit(source, dest, *args, **kwargs)


def test_credits_exact_call_and_actual_rendered_bounds(renderer, menus, monkeypatch):
    assert CREDITS_TEXT == 'UI assets: Kenney | Fonts: Braille Institute'
    assert CREDITS_RECT == pygame.Rect(
            MENU_CREDITS_SIDE_MARGIN, MENU_CREDITS_TOP,
            SCREEN_WIDTH - 2 * MENU_CREDITS_SIDE_MARGIN, MENU_CREDITS_HEIGHT,
        )
    screen = RecordingSurface((SCREEN_WIDTH, SCREEN_HEIGHT))
    text = Mock(wraps=renderer.text)
    monkeypatch.setattr(renderer, 'text', text)
    menus[0].draw(screen)
    credits_calls = [item for item in text.call_args_list if item.args[3] == 'credits']
    assert credits_calls == [call(screen, CREDITS_TEXT, CREDITS_RECT, 'credits')]

    rendered = renderer.font('credits').render(
        CREDITS_TEXT, True, renderer.color('background_text'),
    )
    bounds = rendered.get_rect(center=CREDITS_RECT.center)
    assert screen.last_blit_bounds == bounds
    assert CREDITS_RECT.contains(bounds)
    assert screen.get_rect().contains(CREDITS_RECT)
    for button in (menus[0].catch_blue_button, menus[0].run_from_red_button):
        assert not bounds.colliderect(button.rect)

    # Compare actual footer pixels to an independently centered font render.
    expected = pygame.Surface(CREDITS_RECT.size)
    renderer.fill(expected)
    background = pygame.image.tobytes(expected, 'RGB')
    expected.blit(rendered, rendered.get_rect(center=expected.get_rect().center))
    actual = pygame.image.tobytes(screen.subsurface(CREDITS_RECT), 'RGB')
    assert actual == pygame.image.tobytes(expected, 'RGB')
    assert actual != background


def test_other_menus_do_not_render_credits(renderer, menus, monkeypatch):
    text = Mock(wraps=renderer.text)
    monkeypatch.setattr(renderer, 'text', text)
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for menu in menus[1:]:
        text.reset_mock()
        menu.draw(screen)
        assert all(item.args[1] != CREDITS_TEXT and item.args[3] != 'credits'
                   for item in text.call_args_list)


def test_menu_buttons_use_shared_geometry(menus):
    select, subject, topics = menus
    first = pygame.Rect(MENU_BUTTON_LEFT, MENU_FIRST_BUTTON_TOP, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
    second = first.move(0, MENU_BUTTON_HEIGHT + MENU_BUTTON_GAP)
    assert select.catch_blue_button.rect == first
    assert select.run_from_red_button.rect == second
    assert subject.anatomy_button.rect == first
    assert subject.organic_chemistry_button.rect == second
    assert topics.start_button.rect == pygame.Rect(
            MENU_BUTTON_LEFT, MENU_START_TOP, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT,
        )
