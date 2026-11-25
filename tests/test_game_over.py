"""Ending panels share question geometry and retain their navigation actions."""

import pygame
import pytest

from board import Cell
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SIDE_PANEL_GAP, SIDE_PANEL_LEFT, SIDE_PANEL_PADDING,
    SIDE_PANEL_TOP, SIDE_PANEL_WIDTH,
)
from conftest import GameStub, land_press, make_play, play_config
from question_popup import build_question_popup
from states.game_over import GameOverState


@pytest.mark.parametrize('result', ['win', 'lose'])
def test_ending_panel_matches_question_and_navigation(renderer, bank, result):
    game = GameStub(bank, renderer)
    config = play_config()
    play = make_play(bank, config, game=game)
    state = GameOverState(game, config, result, play)
    assert state.renderer is play.renderer
    question = bank.questions[0]
    panel, prompt, choices = build_question_popup(
        question, game.renderer, list(range(len(question.choices))),
    )
    assert state.panel_rect.topleft == panel.topleft == (SIDE_PANEL_LEFT, SIDE_PANEL_TOP)
    assert state.panel_rect.width == panel.width == SIDE_PANEL_WIDTH
    assert (state.result_box.x, state.result_box.y, state.result_box.width) == (
        prompt.x, prompt.y, prompt.width,
    )
    assert state.result_box.text == ('You caught Blue!' if result == 'win' else 'Blue got away!')
    assert state.replay_button.text == ('Play again' if result == 'win' else 'Try again')
    assert state.replay_button.rect.top == state.result_box.y + state.result_box.height + 24
    assert state.main_menu_button.rect.top == state.replay_button.rect.bottom + 24
    assert state.panel_rect.bottom == state.main_menu_button.rect.bottom + SIDE_PANEL_PADDING
    for button in (state.replay_button, state.main_menu_button):
        assert button.rect.left == choices[0].rect.left
        assert button.rect.width == choices[0].rect.width
        assert state.panel_rect.contains(button.rect)
        area = button.rect.inflate(-2 * button.padding, -2 * button.padding)
        assert all(area.contains(r) for r in game.renderer.text_rects(button.lines, area, 'button'))
    board = play.view.cell_to_rect(Cell(0, 0)).union(play.view.cell_to_rect(Cell(4, 4)))
    assert state.panel_rect.left - board.right == SIDE_PANEL_GAP
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    assert screen.get_rect().contains(state.panel_rect)
    play.draw(screen, show_pause=False)
    hud = pygame.Rect(SIDE_PANEL_LEFT, 50, SIDE_PANEL_WIDTH, SIDE_PANEL_TOP - 50)
    before_hud = pygame.image.tobytes(screen.subsurface(hud), 'RGB')
    before_board = pygame.image.tobytes(screen.subsurface(board), 'RGB')
    state.draw(screen)
    assert pygame.image.tobytes(screen.subsurface(hud), 'RGB') == before_hud
    assert pygame.image.tobytes(screen.subsurface(board), 'RGB') == before_board
    for button, callback, args in (
        (state.replay_button, game.start_play, (config,)),
        (state.main_menu_button, game.show_main_menu, ()),
    ):
        state.handle_events([])  # drain the batch a previous press discards
        state.handle_events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=button.rect.center,
        )])
        callback.assert_not_called()  # the press lands after its animation
        land_press(state)
        callback.assert_called_once_with(*args)
