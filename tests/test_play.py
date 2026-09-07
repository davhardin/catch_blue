"""Answer reveal timing and input isolation, without a display or real bank."""

import json
from random import Random

import pygame
import pytest

import constants
from board import Cell
from game_setup import GameConfig
from questions import Question, QuestionBank
from states.game_over import GameOverState
from states.play import PlayState


class GameStub:
    def __init__(self):
        self.state = None
        self.transitions = []

    def change_state(self, state):
        self.state = state
        self.transitions.append(state)


@pytest.fixture
def make_play(tmp_path):
    pygame.font.init()
    (tmp_path / "questions.json").write_text(json.dumps([
        {
            "id": f"synthetic-{index}",
            "subject": "science",
            "topic": "testing",
            "subtopic": "Reveal",
            "difficulty": 1,
            "type": "multiple_choice",
            "prompt": "Which answer is correct?",
            "choices": ["Correct", "Wrong one", "Wrong two"],
            "answer_index": 0,
        }
        for index in range(3)
    ]), encoding="utf-8")

    def factory(**kwargs):
        game = GameStub()
        state = PlayState(
            game,
            QuestionBank(tmp_path),
            GameConfig("catch_blue", "science", ("testing",)),
            Random(17),
            **kwargs,
        )
        game.state = state
        return state

    yield factory
    pygame.font.quit()


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def board_click(state, cell):
    return click(state.view.cell_to_rect(cell).center)


def open_question(state, intent="move"):
    if intent == "catch":
        state.player.move_to(Cell(1, 2))
        target = state.blue.cell
    else:
        target = Cell(1, 4)
    state.handle_events([board_click(state, target)])
    assert state.pending is not None
    assert state.pending[1:] == (target, intent)
    return target


def answer_click(state, canonical_index):
    return click(state.answer_buttons[state.answer_order.index(canonical_index)].rect.center)


def snapshot(state):
    return (
        state.player.cell, state.blue.cell, state.moves_remaining,
        state.rng.getstate(), tuple(state.game.transitions),
    )


def assert_popup_cleared(state):
    assert state.pending is None
    assert state.reveal is None
    assert state.selected is None
    assert state.popup_rect is None
    assert state.prompt_box is None
    assert state.answer_buttons == []
    assert state.answer_order == []


@pytest.mark.parametrize("chosen", [0, 1, 2])
def test_shuffled_highlights_use_canonical_indices(make_play, monkeypatch, chosen):
    monkeypatch.setattr(Question, "display_order", lambda self, rng: [1, 2, 0])
    state = make_play()
    open_question(state)
    before = snapshot(state)
    popup = (state.pending, state.popup_rect, state.prompt_box, state.selected)

    state.handle_events([answer_click(state, chosen)])

    assert state.reveal_duration_ms == constants.REVEAL_DURATION
    assert state.answer_order == [1, 2, 0]
    assert [button.text for button in state.answer_buttons] == [
        "Wrong one", "Wrong two", "Correct",
    ]
    assert [button.highlight_color for button in state.answer_buttons] == [
        constants.INCORRECT_ANSWER_COLOR if chosen == 1 else None,
        constants.INCORRECT_ANSWER_COLOR if chosen == 2 else None,
        constants.CORRECT_ANSWER_COLOR,
    ]
    assert state.reveal.canonical_index == chosen
    assert state.reveal.elapsed_ms == 0
    assert snapshot(state) == before
    assert (state.pending, state.popup_rect, state.prompt_box, state.selected) == popup
    state.draw(pygame.Surface((1280, 720)))
    state.update(constants.REVEAL_DURATION - 1)
    assert snapshot(state) == before
    assert state.reveal.elapsed_ms == constants.REVEAL_DURATION - 1
    state.update(1)
    assert_popup_cleared(state)


@pytest.mark.parametrize("intent", ["move", "catch"])
@pytest.mark.parametrize("correct", [True, False])
@pytest.mark.parametrize("overshoot", [0, 75])
def test_delayed_consequences_resolve_exactly_once(make_play, intent, correct, overshoot):
    state = make_play(reveal_duration_ms=100)
    target = open_question(state, intent)
    before = snapshot(state)
    expected_rng = Random()
    expected_rng.setstate(state.rng.getstate())
    expected_blue = state.blue.cell
    if not correct:
        expected_blue = state.blue.flee_step(state.board, state.player.cell, expected_rng)
        assert expected_blue != state.blue.cell

    state.handle_events([answer_click(state, 0 if correct else 1)])
    state.update(40)
    assert state.reveal.elapsed_ms == 40
    state.update(59)
    assert state.reveal.elapsed_ms == 99
    assert snapshot(state) == before
    assert state.pending is not None

    state.update(1 + overshoot)
    assert state.player.cell == (target if correct and intent == "move" else before[0])
    assert state.blue.cell == expected_blue
    assert state.rng.getstate() == expected_rng.getstate()
    assert state.moves_remaining == before[2] - 1
    assert state.moves == state.player.legal_moves(state.board, {state.blue.cell})
    assert_popup_cleared(state)
    assert len(state.game.transitions) == int(correct and intent == "catch")
    if state.game.transitions:
        assert state.game.state.result == "win"
    resolved = snapshot(state)
    state.update(1000)
    state.update(0)
    assert snapshot(state) == resolved
    assert_popup_cleared(state)


@pytest.mark.parametrize("intent,correct,result", [
    ("catch", True, "win"),
    ("catch", False, "lose"),
    ("move", True, "lose"),
    ("move", False, "lose"),
])
def test_last_move_result_waits_for_reveal(make_play, intent, correct, result):
    state = make_play(reveal_duration_ms=50)
    state.moves_remaining = 1
    open_question(state, intent)
    state.handle_events([answer_click(state, 0 if correct else 1)])
    state.update(49)
    assert state.game.state is state
    assert state.game.transitions == []
    assert state.moves_remaining == 1
    state.update(1)
    assert isinstance(state.game.state, GameOverState)
    assert state.game.state.result == result
    assert state.game.state.play_state is state
    assert state.moves_remaining == 0
    assert_popup_cleared(state)
    state.update(500)
    assert len(state.game.transitions) == 1
    assert state.moves_remaining == 0


@pytest.mark.parametrize("duration", [0, 100])
def test_answer_ignores_remaining_batch_and_reveal_blocks_input(make_play, duration):
    state = make_play(reveal_duration_ms=duration)
    open_question(state)
    accepted = answer_click(state, 0)
    other_answer = answer_click(state, 1)
    next_cell = Cell(2, 4)
    hover = pygame.event.Event(
        pygame.MOUSEMOTION, pos=state.view.cell_to_rect(next_cell).center,
    )
    state.handle_events([accepted, other_answer, board_click(state, next_cell), hover])
    assert state.hovering is None
    if duration:
        before = snapshot(state)
        pending = state.pending
        state.handle_events([other_answer, board_click(state, next_cell), hover])
        assert snapshot(state) == before
        assert state.pending is pending
        assert state.reveal.canonical_index == 0
        assert state.reveal.elapsed_ms == 0
        assert state.hovering is None
        state.update(duration)
    assert state.player.cell == Cell(1, 4)
    assert state.moves_remaining == constants.MOVE_LIMIT - 1
    assert_popup_cleared(state)


@pytest.mark.parametrize("empty_batch", [False, True])
def test_expiry_discards_one_batch_then_accepts_input(make_play, empty_batch):
    state = make_play(reveal_duration_ms=10)
    open_question(state)
    state.handle_events([answer_click(state, 0)])
    state.update(10)
    next_cell = Cell(2, 4)
    event = board_click(state, next_cell)
    hover = pygame.event.Event(
        pygame.MOUSEMOTION, pos=state.view.cell_to_rect(next_cell).center,
    )
    before = snapshot(state)
    assert state._discard_events_after_reveal is True
    state.handle_events([] if empty_batch else [event, hover])
    assert state._discard_events_after_reveal is False
    assert snapshot(state) == before
    assert state.hovering is None
    assert_popup_cleared(state)
    state.handle_events([event])
    assert state.pending is not None
    assert state.pending[1:] == (next_cell, "move")
    assert state.reveal is None
    assert all(button.highlight_color is None for button in state.answer_buttons)


@pytest.mark.parametrize("intent", ["move", "catch"])
@pytest.mark.parametrize("correct", [True, False])
def test_zero_duration_resolves_immediately_once(make_play, intent, correct):
    state = make_play(reveal_duration_ms=0)
    target = open_question(state, intent)
    before = snapshot(state)
    expected_rng = Random()
    expected_rng.setstate(state.rng.getstate())
    expected_blue = state.blue.cell if correct else state.blue.flee_step(
        state.board, state.player.cell, expected_rng,
    )
    event = answer_click(state, 0 if correct else 1)
    state.handle_events([event, event])
    assert state.player.cell == (target if correct and intent == "move" else before[0])
    assert state.blue.cell == expected_blue
    assert state.rng.getstate() == expected_rng.getstate()
    assert state.moves_remaining == before[2] - 1
    assert len(state.game.transitions) == int(correct and intent == "catch")
    assert_popup_cleared(state)
    resolved = snapshot(state)
    state.update(900)
    assert snapshot(state) == resolved


def test_negative_reveal_duration_is_rejected(make_play):
    with pytest.raises(ValueError):
        make_play(reveal_duration_ms=-1)
