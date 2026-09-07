"""Real-bank layout, menu bounds, and theme-independent gameplay contracts."""

from copy import copy
from itertools import permutations
from pathlib import Path
from random import Random
from types import SimpleNamespace

import pygame
import pytest

from board import Board, Cell, get_distance, is_adjacent
from board_view import BoardView
from game import Game
from game_setup import GameConfig, subtopic_display_name
from questions import QuestionBank
from render import Renderer
from states.game_over import GameOverState
from states.menus import GameSelectState, SubjectState, TopicsState, SCROLL_REGION
from states.play import build_question_popup
from theme import FLAT, PIXEL
from tools.theme_fit import audit
from ui import Button

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def renderer(request):
    pygame.font.init()
    yield Renderer(request.param)
    pygame.font.quit()


@pytest.fixture
def bank():
    return QuestionBank(ROOT / 'data' / 'questions')


def test_entire_bank_popup_and_category_fit(renderer, bank):
    report = audit(bank, renderer)
    assert not report['failures'], '\n'.join(report['failures'])
    assert report['worst']['bottom'] <= 700, report['worst']


def assert_button_fit(button):
    area = button.rect.inflate(-2 * button.padding, -2 * button.padding)
    assert all(area.contains(r) for r in button.renderer.text_rects(button.lines, area, button.font_role))


def test_menus_end_controls_titles_hud_and_scroll(renderer, bank):
    game = SimpleNamespace(renderer=renderer)
    menus = [GameSelectState(game, bank), SubjectState(game, bank, 'catch_blue'),
             TopicsState(game, bank, 'catch_blue', 'anatomy_physiology')]
    screen = pygame.Rect(0, 0, 1280, 720)
    for menu in menus:
        buttons = [value for value in vars(menu).values() if isinstance(value, Button)]
        for button in buttons:
            assert_button_fit(button)
            assert screen.contains(button.rect)
        assert all(not a.rect.colliderect(b.rect) for a, b in zip(buttons, buttons[1:]))
    topics = menus[-1]
    overflows = []
    for checkbox in [topics.all_checkbox, *(c for _, c in topics.topic_checkboxes)]:
        if checkbox.label_rect.right > topics.scroll_region.right:
            overflows.append((checkbox.text, checkbox.label_rect.right - topics.scroll_region.right))
        assert checkbox.label_rect.left >= topics.scroll_region.left
        assert checkbox.is_clicked(checkbox.label_rect.center)
        expected = renderer.font('checkbox').render(checkbox.text, True, (255, 255, 255))
        assert checkbox.label_rect.size == expected.get_size()
    topics._set_scroll_offset(topics.max_scroll)
    assert topics.topic_checkboxes[-1][1].hit_rect.move(0, -topics.scroll_offset).bottom <= topics.scroll_region.bottom
    for text in ['Select Game', 'Select Subject', 'Select Topics']:
        assert screen.contains(renderer.text_rects([text], pygame.Rect(0, 120, 1280, 80), 'title')[0])
    hud = renderer.text_rects(['Moves remaining: 20'], pygame.Rect(720, 50, 520, 50), 'counter')[0]
    assert hud.right <= 1240 and hud.bottom < 100
    for result in ['win', 'lose']:
        state = GameOverState(game, bank, None, result, None)
        for button in [state.replay_button, state.main_menu_button]:
            assert_button_fit(button)
            assert state.panel_rect.contains(button.rect)
        box = state.result_box
        assert all(state.panel_rect.contains(r) for r in renderer.text_rects(
            box.lines, pygame.Rect(box.x, box.y, box.width, box.height), 'result'))
        assert box.y + box.height < state.replay_button.rect.top
    assert not overflows, f'Checkbox labels exceed scroll clip: {overflows}'


def test_scrolled_rightmost_label_click_uses_instance_clip(renderer, bank, monkeypatch):
    topics = TopicsState(SimpleNamespace(renderer=renderer), bank, 'catch_blue', 'anatomy_physiology')
    assert SCROLL_REGION == pygame.Rect(300, 200, 680, 390)
    assert topics.scroll_region is not SCROLL_REGION
    assert topics.scroll_region.topleft == SCROLL_REGION.topleft
    assert topics.scroll_region.height == SCROLL_REGION.height
    assert topics.scroll_region.bottom == SCROLL_REGION.bottom
    checkboxes = [topics.all_checkbox, *(c for _, c in topics.topic_checkboxes)]
    expected_right = max(SCROLL_REGION.right, max(c.hit_rect.right for c in checkboxes) + 8)
    assert topics.scroll_region.right == expected_right
    assert topics.scroll_region.right <= 1280
    if renderer.theme is FLAT:
        assert topics.scroll_region == SCROLL_REGION
    else:
        assert topics.scroll_region.right == 1032
    assert topics.max_scroll == max(0, max(c.hit_rect.bottom for c in checkboxes) - SCROLL_REGION.bottom)
    topics._set_scroll_offset(topics.max_scroll)
    target = max((c for _, c in topics.topic_checkboxes), key=lambda c: c.label_rect.right)
    point = (target.label_rect.right - 1, target.label_rect.centery - topics.scroll_offset)
    assert topics.scroll_region.collidepoint(point)
    if renderer.theme is PIXEL:
        assert not SCROLL_REGION.collidepoint(point)
    before = [c.checked for _, c in topics.topic_checkboxes]
    topics.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)])
    assert [c.checked for _, c in topics.topic_checkboxes] == [
        not checked if c is target else checked
        for (_, c), checked in zip(topics.topic_checkboxes, before)
    ]
    assert not topics.all_checkbox.checked
    after = [c.checked for c in checkboxes]
    topics.handle_events([pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(topics.scroll_region.right, point[1]),
    )])
    assert [c.checked for c in checkboxes] == after
    # A clipped-off label still has a content hit rect, but must not receive clicks.
    hidden = topics.topic_checkboxes[0][1]
    outside = (hidden.label_rect.centerx, hidden.label_rect.centery - topics.scroll_offset)
    assert hidden.is_clicked((outside[0], outside[1] + topics.scroll_offset))
    assert not topics.scroll_region.collidepoint(outside)
    topics.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=outside)])
    assert [c.checked for c in checkboxes] == after
    clips = []
    original_clip = renderer.clip
    def record_clip(surface, rect):
        clips.append(rect.copy())
        return original_clip(surface, rect)
    monkeypatch.setattr(renderer, 'clip', record_clip)
    topics.draw(pygame.Surface((1280, 720)))
    assert clips == [topics.scroll_region]


def test_labels_clear_actual_skin_face(renderer, bank):
    report = audit(bank, renderer)
    assert not report['label_border_intrusions'], report['label_border_intrusions']


def test_banner_identity_and_permutations(renderer, bank):
    question = copy(next(q for q in bank.questions if q.topic == 'muscular_system'))
    question.subtopic = 'Unaliased Raw Category / Identity'
    original = (question.topic, question.subtopic, list(question.choices), question.answer_index)
    base = None
    for order in permutations(range(len(question.choices))):
        rect, prompt, buttons, banner = build_question_popup(question, renderer, order)
        if base is None:
            base = rect
        assert rect == base
        assert [b.text for b in buttons] == [question.choices[i] for i in order]
        if renderer.theme.layout.show_category_banner:
            assert ' '.join(banner.lines) == subtopic_display_name(question.topic, question.subtopic)
            assert banner.rect.bottom + 12 == prompt.y
        else:
            assert banner is None
    assert original == (question.topic, question.subtopic, question.choices, question.answer_index)


def test_button_padding_validation_and_role_color(renderer, monkeypatch):
    padding = renderer.theme.layout.choice_padding
    with pytest.raises(ValueError, match='padding'):
        Button(pygame.Rect(0, 0, 2 * padding, 44), 'Answer', renderer, 'choice')
    calls = []
    monkeypatch.setattr(renderer, 'wrapped_text', lambda *args: calls.append(args))
    for role in ['choice', 'button', 'title']:
        button = Button(pygame.Rect(0, 0, 480, 64), 'Answer', renderer, role)
        button.draw(pygame.Surface((480, 64)))
        assert calls[-1][-1] is None
        button.active = False
        button.draw(pygame.Surface((480, 64)))
        assert calls[-1][-1] == 'text_inactive'


def test_base_cells_drawn_once_with_moves(renderer, monkeypatch):
    board = Board(5, 5)
    calls = []
    original = renderer.cell
    def record(surface, rect, style='normal'):
        calls.append((rect.copy(), style))
        original(surface, rect, style)
    monkeypatch.setattr(renderer, 'cell', record)
    view = BoardView(board, 0, 0, 640)
    move = Cell(0, 0)
    view.draw(pygame.Surface((640, 640)), None, [], None, {move},
              {c: ('cells', 'Overview') for c in board.cells()}, renderer)
    assert len(calls) == len(list(board.cells()))
    assert [style for rect, style in calls if rect == view.cell_to_rect(move)] == ['move']


@pytest.mark.parametrize('duration', [0, 15])
def test_both_themes_win_replay_loss_and_rng_parity(bank, monkeypatch, duration):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    traces = []
    original_questions = [(q.id, list(q.choices), q.answer_index) for q in bank.questions]
    for theme in (FLAT, PIXEL):
        fresh_bank = QuestionBank(bank.data_dir)
        rng = Random(2026)
        game = Game(fresh_bank, rng=rng, theme=theme)
        renderer = game.renderer
        config = GameConfig('catch_blue', 'anatomy_physiology', ('cells', 'tissues'))
        game.start_play(fresh_bank, config)
        trace = []
        def click(pos):
            return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
        def answer(state, target, correct):
            state.reveal_duration_ms = duration
            state.handle_events([click(state.view.cell_to_rect(target).center)])
            question = state.pending[0]
            trace.append((question.id, tuple(state.answer_order)))
            assert (state.popup_banner is not None) == (theme is PIXEL)
            index = next(i for i in state.answer_order if (i == question.answer_index) == correct)
            state.handle_events([click(state.answer_buttons[state.answer_order.index(index)].rect.center)])
            state.update(duration)
            assert state.popup_banner is state.popup_rect is state.prompt_box is None
            assert not state.answer_buttons and not state.answer_order
            state.handle_events([])  # drain timed reveal's event-isolation frame
            trace.append((state.player.cell, state.blue.cell, state.moves_remaining, rng.getstate()))
        for _ in range(40):
            if isinstance(game.state, GameOverState):
                break
            state = game.state
            target = state.blue.cell if is_adjacent(state.player.cell, state.blue.cell) else min(
                sorted(state.moves), key=lambda c: get_distance(c, state.blue.cell))
            answer(state, target, True)
        assert isinstance(game.state, GameOverState) and game.state.result == 'win'
        game.state.handle_events([click(game.state.replay_button.rect.center)])
        replay = game.state
        assert replay.bank is fresh_bank and replay.rng is rng and replay.renderer is renderer
        assert replay.config is config and replay.popup_banner is None
        replay.moves_remaining = 1
        answer(replay, sorted(replay.moves)[0], False)
        assert isinstance(game.state, GameOverState) and game.state.result == 'lose'
        game.state.handle_events([click(game.state.replay_button.rect.center)])
        assert game.state.bank is fresh_bank and game.state.rng is rng and game.state.renderer is renderer
        assert [(q.id, q.choices, q.answer_index) for q in fresh_bank.questions] == original_questions
        traces.append(trace)
        pygame.quit()
    assert traces[0] == traces[1]
