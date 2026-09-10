"""M7.a–d — settings in the config, the Settings screen, Back and Pause, and
click-to-continue on wrong answers.

Every button press is deferred behind the press animation for exactly
BUTTON_PRESS_DOWN_MS + BUTTON_PRESS_HOLD_MS on every theme, so `press()`
advances that much and no more.
"""

from dataclasses import replace
from pathlib import Path
from random import Random
from types import SimpleNamespace
from unittest.mock import Mock

import pygame
import pytest

import constants
from board import Cell
from constants import (
    BUTTON_PRESS_DOWN_MS, BUTTON_PRESS_HOLD_MS, REVEAL_DURATION, SCREEN_HEIGHT, SCREEN_WIDTH,
)
from game_setup import (
    COMPACT_SUBTOPIC_DISPLAY_NAMES, DEFAULT_PRESET, PRESETS, GameConfig, Settings,
    TierPolicy, preset_for, subtopic_display_name,
)
from questions import QuestionBank
from render import Renderer
from states.game_over import GameOverState
from states.menus import GameSelectState, SubjectState, TopicsState
from states.pause import PauseState
from states.play import PlayState
from states.settings import SettingsState
from theme import FLAT, PIXEL

SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
A_AND_P = 'anatomy_physiology'


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def renderer(request):
    pygame.font.init()
    yield Renderer(request.param)
    pygame.font.quit()


@pytest.fixture(scope='module')
def bank():
    return QuestionBank(Path(__file__).resolve().parents[1] / 'data' / 'questions')


class FakeGame:
    def __init__(self, renderer):
        self.renderer = renderer
        self.settings = PRESETS[DEFAULT_PRESET]
        self.topic_selections = {}
        self.state = None
        self.transitions = []
        self.start_play = Mock()
        self.show_main_menu = Mock()

    def change_state(self, state):
        self.state = state
        self.transitions.append(state)


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def settle(state, frames=30):
    for _ in range(frames):
        state.update(16)


def land_press(state):
    """Tick exactly the press animation: the down phase, then the hold."""
    state.update(BUTTON_PRESS_DOWN_MS)
    state.update(BUTTON_PRESS_HOLD_MS)


def press(state, button):
    # A press swallows the batch after it lands; drain before clicking.
    state.handle_events([])
    state.handle_events([click(button.rect.center)])
    land_press(state)


def make_play(game, bank, settings=None, *, reveal_duration_ms=REVEAL_DURATION, topics=('cells',)):
    config = GameConfig('catch_blue', A_AND_P, topics,
                        settings=settings or PRESETS[DEFAULT_PRESET])
    state = PlayState(game, bank, config, Random(17), reveal_duration_ms=reveal_duration_ms)
    game.state = state
    return state


def open_question(state):
    target = sorted(state.moves)[0]
    state.handle_events([click(state.view.cell_to_rect(target).center)])
    assert state.pending is not None
    return target


def answer(state, correct):
    question = state.pending[0]
    canonical = next(i for i in state.answer_order if (i == question.answer_index) == correct)
    state.handle_events([click(state.answer_buttons[state.answer_order.index(canonical)].rect.center)])
    assert state.reveal is not None


# ---------------------------------------------------------------- M7.a ------

def test_default_config_is_the_shipped_game():
    config = GameConfig('catch_blue', A_AND_P, ('cells',))
    assert config.settings == PRESETS[DEFAULT_PRESET]
    # One default, not two: a bare Settings() is the easy preset.
    assert Settings() == PRESETS['easy']
    assert config.settings.board_size == 5
    assert config.settings.move_limit == constants.MOVE_LIMIT == 15


def test_settings_validate_their_inputs():
    with pytest.raises(ValueError):
        Settings(board_size=6)
    with pytest.raises(ValueError):
        Settings(move_limit=0)
    assert Settings(tier_policy='distance').tier_policy is TierPolicy.DISTANCE


def test_preset_lookup_round_trips_and_detects_custom():
    for name, preset in PRESETS.items():
        assert preset_for(preset) == name
        assert preset_for(replace(preset, move_limit=preset.move_limit + 1)) == 'custom'
    assert preset_for(replace(PRESETS['easy'], board_size=9)) == 'custom'


@pytest.mark.parametrize('size', [5, 7, 9])
def test_board_size_and_move_limit_ride_in_from_the_config(renderer, bank, size):
    game = FakeGame(renderer)
    settings = replace(PRESETS['medium'], board_size=size, move_limit=22)
    state = make_play(game, bank, settings)
    assert (state.board.cols, state.board.rows) == (size, size)
    assert state.moves_remaining == 22
    assert state.view.cell_to_rect(Cell(size - 1, size - 1)).bottom <= SCREEN_HEIGHT
    # One renderer per game, whatever the board size (2026-09-09 rework):
    # the smaller label font is a role the renderer already holds.
    assert state.renderer is game.renderer
    expected_size = dict(renderer.theme.board_label_sizes).get(size, renderer.theme.fonts.label.size)
    label_font = renderer.font(renderer.label_role(size))
    reference = pygame.font.Font(
        str(renderer.theme.fonts.label.path) if renderer.theme.fonts.label.path else None,
        expected_size,
    )
    assert label_font.size('Cardiac Conduction') == reference.size('Cardiac Conduction')
    # Start distance never trips the early-loss rule on the first move.
    from board import get_distance
    assert state.moves_remaining > get_distance(state.player.cell, state.blue.cell) + 1


def test_compact_labels_name_real_pairs_and_apply_only_above_five(bank):
    pairs = {(q.topic, q.subtopic) for q in bank.questions}
    for pair, label in COMPACT_SUBTOPIC_DISPLAY_NAMES.items():
        assert pair in pairs, f'compact label {label!r} names a pair not in the bank: {pair}'
        assert subtopic_display_name(*pair, board_size=7) == label
        assert subtopic_display_name(*pair, board_size=9) == label
        assert subtopic_display_name(*pair) != label or pair in (
            ('muscular_system', 'Neuromuscular Junction, EC Coupling, and Cross-Bridge Cycling'),
        )
    assert subtopic_display_name('x', 'Unmapped', board_size=9) == 'Unmapped'


def test_renderer_holds_a_label_font_per_board_size(renderer):
    """The theme's board_label_sizes become extra font roles loaded once at
    construction; 5x5 and any unlisted size fall back to the plain label role."""
    theme = renderer.theme
    assert renderer.label_role(5) == 'label'
    assert renderer.label_role(11) == 'label'
    base_height = renderer.line_height('label')
    for board_size, font_size in theme.board_label_sizes:
        role = renderer.label_role(board_size)
        assert role != 'label' and role in renderer.fonts
        assert renderer.line_height(role) < base_height
        # The derived role inherits the label's alignment and color, so the
        # board view can pass it anywhere it passed 'label'.
        rect = pygame.Rect(0, 0, 120, 60)
        lines = renderer.wrap('Cardiac Conduction', rect.width, role)
        bounds = renderer.text_rects(lines, rect, role)
        assert bounds and all(rect.contains(b) for b in bounds)
        renderer.wrapped_text(pygame.Surface(rect.size), lines, rect, role)
    # Nothing else moved: every dataclass role is still present and untouched.
    for role in ('prompt', 'choice', 'button', 'title', 'checkbox', 'result', 'counter', 'credits'):
        assert role in renderer.fonts


# ---------------------------------------------------------------- M7.b ------

def test_preset_click_stamps_rows_and_row_click_flips_to_custom(renderer, bank):
    game = FakeGame(renderer)
    state = SettingsState(game, bank)
    assert state.rows['preset'].selected == DEFAULT_PRESET

    press(state, state.rows['preset'].buttons['hard'])
    assert game.settings == PRESETS['hard']
    assert state.rows['board_size'].selected == PRESETS['hard'].board_size
    assert state.rows['move_limit'].selected == PRESETS['hard'].move_limit
    assert state.rows['tier_policy'].selected == PRESETS['hard'].tier_policy

    other_size = next(s for s in (5, 7, 9) if s != PRESETS['hard'].board_size)
    press(state, state.rows['board_size'].buttons[other_size])
    assert game.settings.board_size == other_size
    assert game.settings.move_limit == PRESETS['hard'].move_limit
    assert state.rows['preset'].selected == 'custom'
    assert preset_for(game.settings) == 'custom'

    # Custom is a display, not a choice: clicking it changes nothing.
    before = game.settings
    press(state, state.rows['preset'].buttons['custom'])
    assert game.settings == before
    assert state.rows['preset'].selected == 'custom'

    press(state, state.rows['preset'].buttons['easy'])
    assert game.settings == PRESETS['easy']
    assert state.rows['preset'].selected == 'easy'


def test_settings_back_keeps_values_and_start_carries_them_into_the_config(renderer, bank):
    game = FakeGame(renderer)
    state = SettingsState(game, bank)
    press(state, state.rows['board_size'].buttons[9])
    press(state, state.back_button)
    game.show_main_menu.assert_called_once_with(bank)
    assert game.settings.board_size == 9

    topics = TopicsState(game, bank, 'catch_blue', A_AND_P)
    press(topics, topics.start_button)
    game.start_play.assert_called_once()
    config = game.start_play.call_args.args[1]
    assert config.settings is game.settings
    assert config.settings.board_size == 9


def test_settings_screen_fits_and_draws_through_the_renderer(renderer, bank):
    state = SettingsState(FakeGame(renderer), bank)
    for row in state.rows.values():
        for button in row.buttons.values():
            assert SCREEN.contains(button.rect)
    assert SCREEN.contains(state.back_button.rect)
    rects = [b.rect for row in state.rows.values() for b in row.buttons.values()]
    assert all(not a.colliderect(b) for i, a in enumerate(rects) for b in rects[i + 1:])
    settle(state)
    state.draw(pygame.Surface(SCREEN.size))


def test_press_timing_is_identical_on_every_theme(renderer, bank):
    """The press delay is behaviour, so it must not vary with theme lift data."""
    game = FakeGame(renderer)
    state = SettingsState(game, bank)
    state.handle_events([click(state.back_button.rect.center)])
    game.show_main_menu.assert_not_called()
    state.update(BUTTON_PRESS_DOWN_MS)
    state.update(BUTTON_PRESS_HOLD_MS - 1)
    game.show_main_menu.assert_not_called()
    # Input is locked for the whole animation, on flat as much as on pixel.
    state.handle_events([click(state.rows['board_size'].buttons[9].rect.center)])
    assert game.settings.board_size == PRESETS[DEFAULT_PRESET].board_size
    state.update(1)
    game.show_main_menu.assert_called_once_with(bank)


def test_game_select_offers_settings(renderer, bank):
    game = FakeGame(renderer)
    state = GameSelectState(game, bank)
    press(state, state.settings_button)
    assert isinstance(game.state, SettingsState)


# ---------------------------------------------------------------- M7.c ------

def test_back_buttons_return_and_keep_the_topic_selection(renderer, bank):
    game = FakeGame(renderer)
    subject = SubjectState(game, bank, 'catch_blue')
    press(subject, subject.back_button)
    game.show_main_menu.assert_called_once_with(bank)

    topics = TopicsState(game, bank, 'catch_blue', A_AND_P)
    dropped, box = topics.topic_checkboxes[2]
    topics.handle_events([click(box.hit_rect.center)])
    assert not box.checked
    press(topics, topics.back_button)
    assert isinstance(game.state, SubjectState)

    again = TopicsState(game, bank, 'catch_blue', A_AND_P)
    checked = {topic: cb.checked for topic, cb in again.topic_checkboxes}
    assert checked[dropped] is False
    assert all(value for topic, value in checked.items() if topic != dropped)
    assert not again.all_checkbox.checked


@pytest.mark.parametrize('how', ['button', 'escape'])
def test_pause_opens_from_the_hud_button_or_escape(renderer, bank, how):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    if how == 'button':
        state.handle_events([click(state.pause_button.rect.center)])
    else:
        state.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
    assert isinstance(game.state, PauseState)
    assert game.state.play_state is state


def test_pause_freezes_the_reveal_and_continue_resumes_it(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    open_question(state)
    answer(state, True)
    state.update(300)
    assert state.reveal.elapsed_ms == 300
    state.handle_events([click(state.pause_button.rect.center)])
    pause = game.state
    assert isinstance(pause, PauseState)

    pause.update(60_000)
    assert state.reveal is not None and state.reveal.elapsed_ms == 300
    assert state.pending is not None

    # Clicks on the board or the popup do nothing while paused.
    target = sorted(state.moves)[0]
    pause.handle_events([click(state.view.cell_to_rect(target).center)])
    pause.handle_events([click(state.answer_buttons[0].rect.center)])
    assert state.reveal.elapsed_ms == 300 and state.pending is not None

    press(pause, pause.continue_button)
    assert game.state is state
    assert state.reveal.elapsed_ms == 300
    state.update(REVEAL_DURATION - 300)
    assert state.reveal is None and state.pending is None


def test_pause_retry_and_main_menu_route_through_the_game(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    state.handle_events([click(state.pause_button.rect.center)])
    pause = game.state
    press(pause, pause.retry_button)
    game.start_play.assert_called_once_with(bank, state.config)

    pause = PauseState(state)
    press(pause, pause.main_menu_button)
    game.show_main_menu.assert_called_once_with(bank)


def test_pause_draws_the_board_beneath_its_panel(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    pause = PauseState(state)
    settle(pause)
    screen = pygame.Surface(SCREEN.size)
    pause.draw(screen)
    assert SCREEN.contains(pause.panel_rect)
    for button in pause.buttons:
        assert pause.panel_rect.contains(button.rect)


def test_end_screen_buttons_lift_like_menu_buttons(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    over = GameOverState(game, bank, state.config, 'lose', state)
    assert over.replay_button.lift_settings == renderer.theme.menu_lift
    over.pointer_pos = over.replay_button.rect.center
    settle(over)
    assert over.replay_button.draw_lift == renderer.theme.menu_lift.hover_px


# ---------------------------------------------------------------- M7.d ------

def test_wrong_answer_holds_until_continue_then_blue_flees(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    open_question(state)
    blue_before = state.blue.cell
    answer(state, False)
    assert state.reveal.waits_for_click
    assert state.continue_button is not None
    assert SCREEN.contains(state.continue_button.rect)
    assert state.continue_button.rect.top >= state.popup_rect.bottom

    state.update(10 * 60 * 1000)  # ten minutes: still waiting
    assert state.pending is not None and state.blue.cell == blue_before

    # Board and answer clicks are ignored while the reveal holds.
    target = sorted(state.moves)[0]
    state.handle_events([click(state.view.cell_to_rect(target).center)])
    state.handle_events([click(state.answer_buttons[0].rect.center)])
    assert state.pending is not None and state.blue.cell == blue_before

    press(state, state.continue_button)
    assert state.reveal is None and state.pending is None
    assert state.continue_button is None
    assert state.blue.cell != blue_before


def test_correct_answer_still_resolves_on_the_timer(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank)
    target = open_question(state)
    answer(state, True)
    assert state.reveal.duration_ms == REVEAL_DURATION
    assert state.continue_button is None
    state.update(REVEAL_DURATION - 1)
    assert state.pending is not None
    state.update(1)
    assert state.pending is None and state.player.cell == target


def test_zero_duration_resolves_wrong_answers_immediately_without_continue(renderer, bank):
    game = FakeGame(renderer)
    state = make_play(game, bank, reveal_duration_ms=0)
    open_question(state)
    blue_before = state.blue.cell
    answer_buttons = state.answer_buttons
    question = state.pending[0]
    wrong = next(i for i in state.answer_order if i != question.answer_index)
    state.handle_events([click(answer_buttons[state.answer_order.index(wrong)].rect.center)])
    assert state.pending is None and state.continue_button is None
    assert state.blue.cell != blue_before


def test_the_extra_second_constant_is_gone():
    assert not hasattr(constants, 'WRONG_REVEAL_EXTRA_MS')
