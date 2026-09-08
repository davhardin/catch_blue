"""Answer reveal timing and input isolation, without a display or real bank."""

from dataclasses import replace
import json
from random import Random

import pygame
import pytest

import constants
from constants import (
    SIDE_PANEL_LEFT, SIDE_PANEL_PADDING, SIDE_PANEL_TOP, SIDE_PANEL_WIDTH,
)
from render import Renderer
from theme import FLAT, Alignment
from board import Cell, get_distance
from game_setup import GameConfig
from questions import Question, QuestionBank
from states.game_over import GameOverState
from states.play import PlayState, build_question_popup


class GameStub:
    def __init__(self):
        self.renderer = Renderer(FLAT)
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


@pytest.mark.parametrize('duration', [0, 35])
@pytest.mark.parametrize('player,blue,target,moves,correct,result', [
    (Cell(0, 4), Cell(2, 2), Cell(1, 4), 4, True, None),
    (Cell(1, 2), Cell(3, 2), Cell(0, 2), 3, True, 'lose'),
    (Cell(0, 4), Cell(2, 2), Cell(1, 4), 5, False, 'lose'),
    (Cell(0, 4), Cell(2, 2), Cell(1, 4), 6, False, None),
    (Cell(1, 1), Cell(0, 0), Cell(2, 1), 2, False, 'lose'),
    (Cell(1, 1), Cell(0, 0), Cell(2, 1), 3, False, None),
    (Cell(1, 2), Cell(2, 2), Cell(2, 2), 1, True, 'win'),
])
def test_distance_loss_uses_resolved_positions_and_preserves_win(
    make_play, duration, player, blue, target, moves, correct, result,
):
    state = make_play(reveal_duration_ms=duration)
    state.player.move_to(player)
    state.blue.move_to(blue)
    state.moves_remaining = moves
    state.handle_events([board_click(state, target)])
    assert state.pending is not None
    before = snapshot(state)
    expected_rng = Random()
    expected_rng.setstate(state.rng.getstate())
    expected_blue = blue if correct else state.blue.flee_step(
        state.board, player, expected_rng,
    )
    state.handle_events([answer_click(state, 0 if correct else 1)])
    if duration:
        assert state.game.state is state
        state.update(state.reveal.duration_ms - 1)
        assert snapshot(state) == before
        assert state.pending is not None
        state.update(1)
    assert_popup_cleared(state)
    assert state.moves_remaining == moves - 1
    assert state.blue.cell == expected_blue
    assert state.player.cell == (target if correct and result != 'win' else player)
    assert state.rng.getstate() == expected_rng.getstate()
    distance = get_distance(state.player.cell, state.blue.cell)
    if result is None:
        assert state.game.state is state
        assert state.moves_remaining == distance
        assert not state.game.transitions
    else:
        assert isinstance(state.game.state, GameOverState)
        assert state.game.state.result == result
        assert state.game.state.play_state is state
        if result == 'lose':
            assert 0 < state.moves_remaining < distance
        else:
            assert state.moves_remaining == 0
        assert len(state.game.transitions) == 1
    resolved = snapshot(state)
    state.update(5000)
    assert snapshot(state) == resolved


@pytest.mark.parametrize("chosen", [0, 1, 2])
def test_shuffled_highlights_use_canonical_indices(make_play, monkeypatch, chosen):
    monkeypatch.setattr(Question, "display_order", lambda self, rng: [1, 2, 0])
    state = make_play()
    open_question(state)
    before = snapshot(state)
    popup = (state.pending, state.popup_rect, state.prompt_box, state.selected)
    button_rects = [button.rect.copy() for button in state.answer_buttons]
    text_rects = [
        state.renderer.text_rects(button.lines, button.rect, 'choice')
        for button in state.answer_buttons
    ]

    state.handle_events([answer_click(state, chosen)])

    assert state.reveal_duration_ms == constants.REVEAL_DURATION
    assert state.answer_order == [1, 2, 0]
    assert [button.text for button in state.answer_buttons] == [
        "Wrong one", "Wrong two", "Correct",
    ]
    assert [button.highlight for button in state.answer_buttons] == [
        'incorrect' if chosen == 1 else None,
        'incorrect' if chosen == 2 else None,
        'correct',
    ]
    assert [button.rect for button in state.answer_buttons] == button_rects
    assert [
        state.renderer.text_rects(button.lines, button.rect, 'choice')
        for button in state.answer_buttons
    ] == text_rects
    for button, rects in zip(state.answer_buttons, text_rects):
        assert all(rect.centerx == button.rect.centerx for rect in rects)
        assert abs((rects[0].top + rects[-1].bottom) / 2 - button.rect.centery) <= 1
    assert state.reveal.canonical_index == chosen
    assert state.reveal.elapsed_ms == 0
    assert snapshot(state) == before
    assert (state.pending, state.popup_rect, state.prompt_box, state.selected) == popup
    state.draw(pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)))
    duration = constants.REVEAL_DURATION + (constants.WRONG_REVEAL_EXTRA_MS if chosen else 0)
    assert state.reveal.duration_ms == duration
    state.update(duration - 1)
    assert snapshot(state) == before
    assert state.reveal.elapsed_ms == duration - 1
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

    if not correct:
        state.update(constants.WRONG_REVEAL_EXTRA_MS)
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
    assert state.reveal.duration_ms == 50 + (0 if correct else constants.WRONG_REVEAL_EXTRA_MS)
    state.update(state.reveal.duration_ms - 1)
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
    assert all(button.highlight is None for button in state.answer_buttons)


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


@pytest.mark.parametrize('long_choices', [False, True])
def test_choice_centering_preserves_popup_geometry_and_indices(make_play, long_choices):
    state = make_play()
    open_question(state)
    question = state.pending[0]
    if long_choices:
        question = Question(**{
            **vars(question),
            'choices': [choice + ' with many extra words' * 12 for choice in question.choices],
        })
    top_left = Renderer(replace(FLAT, fonts=replace(
        FLAT.fonts, choice=replace(FLAT.fonts.choice, alignment=Alignment()),
    )))
    order = [2, 0, 1]
    old_rect, old_prompt, old_buttons = build_question_popup(question, top_left, order)
    rect, prompt, buttons = build_question_popup(question, state.renderer, order)
    assert rect == old_rect
    assert rect.topleft == (SIDE_PANEL_LEFT, SIDE_PANEL_TOP)
    assert rect.width == SIDE_PANEL_WIDTH
    assert (prompt.x, prompt.y, prompt.width) == (
        SIDE_PANEL_LEFT + SIDE_PANEL_PADDING, SIDE_PANEL_TOP + SIDE_PANEL_PADDING,
        SIDE_PANEL_WIDTH - 2 * SIDE_PANEL_PADDING,
    )
    assert (prompt.lines, prompt.height) == (old_prompt.lines, old_prompt.height)
    assert buttons[0].rect.top == prompt.y + prompt.height + 12
    for index, (button, old_button) in enumerate(zip(buttons, old_buttons)):
        assert button.rect == old_button.rect
        assert button.lines == old_button.lines
        assert button.text == question.choices[order[index]]
        assert button.rect.height == max(44, len(button.lines) * state.renderer.line_height('choice'))
        assert button.is_clicked(old_button.rect.center)
        if index:
            assert button.rect.top == buttons[index - 1].rect.bottom + 12
    assert rect.bottom == buttons[-1].rect.bottom + 20


def test_negative_reveal_duration_is_rejected(make_play):
    with pytest.raises(ValueError):
        make_play(reveal_duration_ms=-1)
