"""Shared test helpers and fixtures (M8.f, 2026-11-24).

pytest finds the fixtures here on its own: `fonts`, `renderer` (both themes),
`flat_renderer`, and `bank`. The plain helpers are imported by name, for
example `from conftest import GameStub, click, make_play`, so each test file
shows where they come from. Keep this file to what several files share; a
helper used by one file stays in that file.
"""

import json
from pathlib import Path
from random import Random
from unittest.mock import Mock

import pygame
import pytest

from constants import BUTTON_PRESS_DOWN_MS, BUTTON_PRESS_HOLD_MS
from game_setup import GameConfig
from modes import MODES, get_mode
from questions import QuestionBank
from render import Renderer
from states.play import PlayState
from theme import FLAT, PIXEL

ROOT = Path(__file__).resolve().parents[1]
REAL_BANK = ROOT / 'data' / 'questions'
A_AND_P = 'anatomy_physiology'


def default_settings(mode='catch_blue'):
    """The mode's default preset: the settings the menus stamp in."""
    return get_mode(mode).settings_spec().default


# --- fixtures ---------------------------------------------------------------


@pytest.fixture
def fonts():
    pygame.font.init()
    yield
    pygame.font.quit()


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def renderer(request, fonts):
    """A renderer on each shipped base theme. Use it only where the theme matters."""
    return Renderer(request.param)


@pytest.fixture
def flat_renderer(fonts):
    return Renderer(FLAT)


@pytest.fixture
def bank():
    """A fresh copy of the shipped bank. Drawing changes a bank, so tests never share one."""
    return QuestionBank(REAL_BANK)


# --- synthetic banks --------------------------------------------------------


def question_dict(
    qid,
    *,
    subject='science',
    topic='testing',
    subtopic='Reveal',
    difficulty=1,
    prompt=None,
    choices=('Correct', 'Wrong one', 'Wrong two'),
    answer_index=0,
):
    """One question in the bank's JSON shape. The right answer is 'Correct'."""
    return {
        'id': qid,
        'subject': subject,
        'topic': topic,
        'subtopic': subtopic,
        'difficulty': difficulty,
        'type': 'multiple_choice',
        'prompt': prompt if prompt is not None else f'{qid}?',
        'choices': list(choices),
        'answer_index': answer_index,
    }


def write_bank(path, questions, name='bank.json'):
    """Write questions to one file in `path` and load that folder as a bank."""
    (path / name).write_text(json.dumps(list(questions)), encoding='utf-8')
    return QuestionBank(path)


# --- a game without a display -----------------------------------------------


class GameStub:
    """Enough of `Game` for states built without a display.

    Settings start at each active mode's default, as `Game` does. The
    renderer defaults to flat, so fonts must be initialized first.
    """

    def __init__(self, bank=None, renderer=None, *, mode='catch_blue'):
        self.bank = bank
        self.renderer = renderer if renderer is not None else Renderer(FLAT)
        self.settings_by_mode = {
            key: entry.settings_spec().default
            for key, entry in MODES.items()
            if entry.active
        }
        self.settings_mode = mode
        self.topic_selections = {}
        self.state = None
        self.transitions = []
        self.start_play = Mock()
        self.show_main_menu = Mock()

    @property
    def settings(self):
        return self.settings_by_mode[self.settings_mode]

    def change_state(self, state):
        self.state = state
        self.transitions.append(state)


def play_config(topics=('cells',), *, mode='catch_blue', subject=A_AND_P, settings=None):
    return GameConfig(
        mode,
        subject,
        tuple(topics),
        settings=settings if settings is not None else default_settings(mode),
    )


def make_play(bank, config=None, *, game=None, seed=17, **play_kwargs):
    """A `PlayState` on a `GameStub` (or on `game`), already set as the game's state.

    `play_kwargs` go to `PlayState`: `renderer=` and `reveal_duration_ms=`.
    """
    if game is None:
        game = GameStub(bank)
    game.bank = bank
    state = PlayState(game, config or play_config(), Random(seed), **play_kwargs)
    game.state = state
    return state


# --- input ------------------------------------------------------------------


def click(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button, pos=pos)


def land_press(state):
    """Tick exactly the button-press animation: the down phase, then the hold."""
    state.update(BUTTON_PRESS_DOWN_MS)
    state.update(BUTTON_PRESS_HOLD_MS)


def press(state, button):
    """Click a button and land its press.

    A landed press swallows the batch after it, so drain one empty batch first.
    """
    state.handle_events([])
    state.handle_events([click(button.rect.center)])
    land_press(state)


def settle(state, ms=480, step=16):
    """Run `ms` of frames in `step` slices, so tweens and lifts reach their targets."""
    for _ in range(ms // step):
        state.update(step)


# --- play actions -----------------------------------------------------------


def open_question(state, target=None):
    """Click a legal square (the first in sorted order unless given); return it."""
    if target is None:
        target = sorted(state.moves)[0]
    state.handle_events([click(state.view.cell_to_rect(target).center)])
    assert state.pending is not None
    return target


def answer_button(state, correct):
    """The popup button holding a right (or a wrong) answer to the pending question."""
    question = state.pending[0]
    popup = state.popup
    canonical = next(
        index for index in popup.answer_order
        if (index == question.answer_index) == correct
    )
    return popup.answer_buttons[popup.answer_order.index(canonical)]


def answer(state, correct):
    """Click a right or wrong answer. The caller checks what follows."""
    state.handle_events([click(answer_button(state, correct).rect.center)])
