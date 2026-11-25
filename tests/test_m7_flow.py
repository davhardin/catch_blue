"""M7.a–d — settings in the config, the Settings screen, Back and Pause, and
click-to-continue on wrong answers.

Every button press is deferred behind the press animation for exactly
BUTTON_PRESS_DOWN_MS + BUTTON_PRESS_HOLD_MS on every theme, so `press()`
advances that much and no more. The reveal and resolve rules themselves
(timers, zero duration, the last move) belong to test_play.py. Flows that do
not depend on the theme run on flat only; the theme parameter stays where
layout, fonts, or lift data are what is tested.
"""

from dataclasses import replace

import pygame
import pytest

import constants
from board import Cell
from constants import (
    BUTTON_PRESS_DOWN_MS, BUTTON_PRESS_HOLD_MS, REVEAL_DURATION, SCREEN_HEIGHT, SCREEN_WIDTH,
)
from conftest import (
    A_AND_P, GameStub, answer, click, make_play, open_question, play_config, press, settle,
)
from game_setup import (
    COMPACT_SUBTOPIC_DISPLAY_NAMES, GameConfig, Settings, TierPolicy,
    subtopic_display_name,
)
from modes import MODES, get_mode
from render import Renderer
from states.game_over import GameOverState
from states.menus import GameSelectState, SubjectState, TopicsState
from states.pause import PauseState
from states.settings import SettingsState
from theme import PIXEL

SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
MODE = 'catch_blue'
SPEC = get_mode(MODE).settings_spec()
PRESETS = dict(SPEC.presets)
DEFAULT_PRESET = SPEC.default_preset
preset_for = SPEC.preset_for
ACTIVE_MODES = [key for key, mode in MODES.items() if mode.active]


# ---------------------------------------------------------------- M7.a ------

def test_default_config_is_the_shipped_game():
    # GameConfig no longer defaults its settings; the mode's default preset is
    # the one value the menus stamp in, and it is still the shipped game.
    config = GameConfig(MODE, A_AND_P, ('cells',), settings=SPEC.default)
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


@pytest.mark.parametrize('size', [5, 7, 9])
def test_board_size_and_move_limit_ride_in_from_the_config(renderer, bank, size):
    game = GameStub(renderer=renderer)
    settings = replace(PRESETS['medium'], board_size=size, move_limit=22)
    state = make_play(bank, play_config(settings=settings), game=game)
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
    assert state.moves_remaining > state.board.distance(state.player.cell, state.npc.cell) + 1


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

def test_preset_click_stamps_rows_and_row_click_flips_to_custom(flat_renderer):
    game = GameStub(renderer=flat_renderer)
    state = SettingsState(game)
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


def test_settings_back_keeps_values_and_start_carries_them_into_the_config(flat_renderer, bank):
    game = GameStub(bank, flat_renderer)
    state = SettingsState(game)
    press(state, state.rows['board_size'].buttons[9])
    press(state, state.back_button)
    game.show_main_menu.assert_called_once_with()
    assert game.settings.board_size == 9

    topics = TopicsState(game, MODE, A_AND_P)
    press(topics, topics.start_button)
    game.start_play.assert_called_once()
    config = game.start_play.call_args.args[0]
    assert config.settings is game.settings
    assert config.settings.board_size == 9


@pytest.mark.parametrize('mode', ACTIVE_MODES)
def test_settings_screen_fits_and_draws_through_the_renderer(renderer, mode):
    state = SettingsState(GameStub(renderer=renderer), mode=mode)
    for row in state.rows.values():
        for button in row.buttons.values():
            assert SCREEN.contains(button.rect)
    assert SCREEN.contains(state.back_button.rect)
    rects = [b.rect for row in state.rows.values() for b in row.buttons.values()]
    assert all(not a.colliderect(b) for i, a in enumerate(rects) for b in rects[i + 1:])
    # Every row, the Game row included, ends above the Back line (M8.b: the
    # fifth row on pixel once reached 781 px against Back's 756).
    back_top = state.back_button.rect.top
    assert 'mode' in state.rows and len(state.rows) == 5
    for key, row in state.rows.items():
        assert row.rect.bottom < back_top, (key, row.rect.bottom, back_top)
        assert all(b.rect.bottom < back_top for b in row.buttons.values()), key
    settle(state)
    # A lift draws a button higher, never lower, so drawn rows stay clear of Back too.
    assert all(b.draw_lift >= 0 for row in state.rows.values() for b in row.buttons.values())
    state.draw(pygame.Surface(SCREEN.size))


def test_press_timing_is_identical_on_every_theme(renderer):
    """The press delay is behaviour, so it must not vary with theme lift data."""
    game = GameStub(renderer=renderer)
    state = SettingsState(game)
    state.handle_events([click(state.back_button.rect.center)])
    game.show_main_menu.assert_not_called()
    state.update(BUTTON_PRESS_DOWN_MS)
    state.update(BUTTON_PRESS_HOLD_MS - 1)
    game.show_main_menu.assert_not_called()
    # Input is locked for the whole animation, on flat as much as on pixel.
    state.handle_events([click(state.rows['board_size'].buttons[9].rect.center)])
    assert game.settings.board_size == PRESETS[DEFAULT_PRESET].board_size
    state.update(1)
    game.show_main_menu.assert_called_once_with()


def test_game_select_offers_settings(flat_renderer, bank):
    game = GameStub(bank, flat_renderer)
    state = GameSelectState(game)
    press(state, state.settings_button)
    assert isinstance(game.state, SettingsState)


# ---------------------------------------------------------------- M7.c ------

def test_back_buttons_return_and_keep_the_topic_selection(flat_renderer, bank):
    game = GameStub(bank, flat_renderer)
    subject = SubjectState(game, MODE)
    press(subject, subject.back_button)
    game.show_main_menu.assert_called_once_with()

    topics = TopicsState(game, MODE, A_AND_P)
    dropped, box = topics.topic_checkboxes[2]
    topics.handle_events([click(box.hit_rect.center)])
    assert not box.checked
    press(topics, topics.back_button)
    assert isinstance(game.state, SubjectState)

    again = TopicsState(game, MODE, A_AND_P)
    checked = {topic: cb.checked for topic, cb in again.topic_checkboxes}
    assert checked[dropped] is False
    assert all(value for topic, value in checked.items() if topic != dropped)
    assert not again.all_checkbox.checked


@pytest.mark.parametrize('how', ['button', 'escape'])
def test_pause_opens_from_the_hud_button_or_escape(flat_renderer, bank, how):
    game = GameStub(renderer=flat_renderer)
    state = make_play(bank, game=game)
    if how == 'button':
        state.handle_events([click(state.pause_button.rect.center)])
    else:
        state.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
    assert isinstance(game.state, PauseState)
    assert game.state.play_state is state


def test_pause_freezes_the_reveal_and_continue_resumes_it(flat_renderer, bank):
    game = GameStub(renderer=flat_renderer)
    state = make_play(bank, game=game)
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
    pause.handle_events([click(state.popup.answer_buttons[0].rect.center)])
    assert state.reveal.elapsed_ms == 300 and state.pending is not None

    press(pause, pause.continue_button)
    assert game.state is state
    assert state.reveal.elapsed_ms == 300
    state.update(REVEAL_DURATION - 300)
    assert state.reveal is None and state.pending is None


def test_pause_retry_and_main_menu_route_through_the_game(flat_renderer, bank):
    game = GameStub(renderer=flat_renderer)
    state = make_play(bank, game=game)
    state.handle_events([click(state.pause_button.rect.center)])
    pause = game.state
    press(pause, pause.retry_button)
    game.start_play.assert_called_once_with(state.config)

    pause = PauseState(state)
    press(pause, pause.main_menu_button)
    game.show_main_menu.assert_called_once_with()


def test_pause_draws_the_board_beneath_its_panel(renderer, bank):
    game = GameStub(renderer=renderer)
    state = make_play(bank, game=game)
    pause = PauseState(state)
    settle(pause)
    screen = pygame.Surface(SCREEN.size)
    pause.draw(screen)
    assert SCREEN.contains(pause.panel_rect)
    for button in pause.buttons:
        assert pause.panel_rect.contains(button.rect)


def test_end_screen_buttons_lift_like_menu_buttons(fonts, bank):
    # Pixel only: flat's lift is zero, so the same check there asserts nothing.
    game = GameStub(renderer=Renderer(PIXEL))
    state = make_play(bank, game=game)
    over = GameOverState(game, state.config, 'lose', state)
    assert over.replay_button.lift_settings == PIXEL.menu_lift
    over.pointer_pos = over.replay_button.rect.center
    settle(over)
    assert over.replay_button.draw_lift == PIXEL.menu_lift.hover_px > 0


# ---------------------------------------------------------------- M7.d ------

def test_wrong_answer_holds_until_continue_then_blue_flees(renderer, bank):
    # The hold itself is test_play.py's; this checks Continue's placement on
    # each theme and that the board and answers stay locked while it waits.
    game = GameStub(renderer=renderer)
    state = make_play(bank, game=game)
    open_question(state)
    blue_before = state.npc.cell
    answer(state, False)
    assert state.reveal.waits_for_click
    popup = state.popup
    assert popup.continue_button is not None
    assert SCREEN.contains(popup.continue_button.rect)
    assert popup.continue_button.rect.top >= popup.popup_rect.bottom

    state.update(10 * 60 * 1000)  # ten minutes: still waiting
    assert state.pending is not None and state.npc.cell == blue_before

    # Board and answer clicks are ignored while the reveal holds.
    target = sorted(state.moves)[0]
    state.handle_events([click(state.view.cell_to_rect(target).center)])
    state.handle_events([click(popup.answer_buttons[0].rect.center)])
    assert state.pending is not None and state.npc.cell == blue_before

    press(state, popup.continue_button)
    assert state.reveal is None and state.pending is None
    assert state.popup is None
    assert state.npc.cell != blue_before
