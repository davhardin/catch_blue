"""Pulsing bevels, steady correct faces, and low-contrast wrong selections."""

import pygame
import pytest

from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from question_popup import build_question_popup
from theme import FLAT, PIXEL
from ui import Button

from conftest import GameStub, answer_button, click, land_press, make_play


def pixels(surface):
    return pygame.image.tobytes(surface, 'RGB')


def test_pulse_highlight_and_steady_correct_face(renderer):
    button = Button(pygame.Rect(20, 20, 400, 70), 'Answer', renderer, 'choice')
    surface = pygame.Surface((440, 110))
    renderer.fill(surface)
    button.draw(surface)
    normal = surface.copy()
    rect = button.rect.copy()
    button.highlight = 'correct'
    background = renderer.color('background')
    bright = renderer.color('highlight')
    centers = []
    borders = []
    for elapsed, amount in [(0, 1), (250, 0.775), (500, 0.55), (750, 0.775), (1000, 1)]:
        renderer.fill(surface)
        button.draw(surface, reveal_elapsed_ms=elapsed)
        expected = tuple(round(a + (b - a) * amount) for a, b in zip(background, bright))
        assert surface.get_at((rect.left - 1, rect.centery))[:3] == background
        assert surface.get_at((rect.left - 4, rect.centery))[:3] == background
        if renderer.theme is FLAT:
            assert surface.get_at((rect.left, rect.centery))[:3] == expected
        expected_face = pygame.Surface(surface.get_size())
        renderer.fill(expected_face)
        renderer.button(expected_face, rect, 'correct')
        if renderer.theme is PIXEL:
            border = pygame.Surface(rect.size, pygame.SRCALPHA)
            border.fill((*bright, round(255 * amount)))
            border.fill((0, 0, 0, 0), pygame.Rect(12, 12, rect.width - 24, rect.height - 24))
            expected_face.blit(border, rect)
            # Use the correct tile's twelve-pixel bevel, not the normal tile's ten.
            for inset in (0, 3, 7, 9, 11):
                assert surface.get_at((rect.left + inset, rect.centery)) == expected_face.get_at(
                    (rect.left + inset, rect.centery)
                )
        else:
            pygame.draw.rect(expected_face, expected, rect, width=4)
        renderer.wrapped_text(expected_face, button.lines,
                              rect.inflate(-2 * button.padding, -2 * button.padding), 'choice')
        assert pixels(surface.subsurface(rect)) == pixels(expected_face.subsurface(rect))
        assert pixels(surface.subsurface(rect)) != pixels(normal.subsurface(rect))
        assert button.rect == rect
        assert surface.get_at((rect.left + 20, rect.centery))[:3] == renderer.color('correct')
        centers.append(pixels(surface.subsurface(rect.inflate(-24, -24))))
        borders.append(surface.get_at((rect.left + 3, rect.centery)))
        outside = surface.copy()
        outside.fill(background, rect)
        assert pixels(outside) == bytes(background) * (outside.get_width() * outside.get_height())
    assert all(center == centers[0] for center in centers)
    assert borders[0] != borders[2]
    assert borders[0] == borders[-1]


def test_wrong_selection_desaturates_and_fades_without_animation(renderer):
    button = Button(pygame.Rect(20, 20, 400, 70), 'Answer', renderer, 'choice')
    surface = pygame.Surface((440, 110))
    renderer.fill(surface)
    button.draw(surface)
    normal = surface.subsurface(button.rect).copy()
    expected = normal.copy()
    desaturated = pygame.transform.grayscale(normal)
    desaturated.set_alpha(220)
    expected.blit(desaturated, (0, 0))
    overlay = pygame.Surface(button.rect.size, pygame.SRCALPHA)
    overlay.fill((*renderer.color('panel'), 100))
    expected.blit(overlay, (0, 0))
    sample = (20, button.rect.height // 2)
    before = normal.get_at(sample)[:3]
    after = expected.get_at(sample)[:3]
    assert max(after) - min(after) < max(before) - min(before)
    panel = renderer.color('panel')
    assert sum(abs(a - b) for a, b in zip(after, panel)) < sum(
        abs(a - b) for a, b in zip(before, panel)
    )
    if renderer.theme is PIXEL:
        assert sum(after) >= sum(before)
    button.highlight = 'incorrect'
    frames = []
    for elapsed in (0, 250, 500, 1000, 2299):
        renderer.fill(surface)
        button.draw(surface, reveal_elapsed_ms=elapsed)
        assert pixels(surface.subsurface(button.rect)) == pixels(expected)
        assert pixels(expected) != pixels(normal)
        frames.append(pixels(surface))
    assert all(frame == frames[0] for frame in frames)
    button.highlight = None
    renderer.fill(surface)
    button.draw(surface)
    assert pixels(surface.subsurface(button.rect)) == pixels(normal)


def test_all_question_feedback_outlines_fit(renderer, bank):
    screen = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    width = renderer.theme.reveal.outline_width
    for question in bank.questions:
        panel, prompt, buttons = build_question_popup(
            question, renderer, list(range(len(question.choices))),
        )
        outlines = [button.rect.inflate(2 * width, 2 * width) for button in buttons]
        assert all(panel.contains(rect) and screen.contains(rect) for rect in outlines)
        assert outlines[0].top >= prompt.y + prompt.height
        assert all(b.top - a.bottom == 4 for a, b in zip(outlines, outlines[1:]))


@pytest.mark.parametrize('correct', [True, False])
def test_outcome_timing_input_guard_and_draw_clock(renderer, bank, correct, monkeypatch):
    # Zero-duration resolution is test_play.py's; this checks what the reveal draws.
    duration = 1300
    state = make_play(bank, game=GameStub(bank, renderer), reveal_duration_ms=duration)
    target = sorted(state.moves)[0]
    state.handle_events([click(state.view.cell_to_rect(target).center)])
    question = state.pending[0]
    popup = state.popup
    chosen_button = answer_button(state, correct)
    chosen = popup.answer_order[popup.answer_buttons.index(chosen_button)]
    before = (state.player.cell, state.npc.cell, state.moves_remaining, state.rng.getstate())
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Let the answer buttons settle at their resting lift (M6.f.8) before
    # capturing the distractors; the reveal must then leave them untouched.
    state.update(1000)
    state.draw(screen)
    distractors = [(b.rect.copy(), pixels(screen.subsurface(b.rect))) for i, b in zip(
        popup.answer_order, popup.answer_buttons,
    ) if i not in (chosen, question.answer_index)]
    state.handle_events([click(chosen_button.rect.center)])
    assert state.reveal.duration_ms == (1300 if correct else None)
    assert state.reveal.waits_for_click == (not correct)
    calls = []
    original = renderer.answer_feedback
    def record(surface, rect, outcome, elapsed):
        calls.append((outcome, elapsed))
        original(surface, rect, outcome, elapsed)
    monkeypatch.setattr(renderer, 'answer_feedback', record)
    state.update(500)
    state.draw(screen)
    assert ('correct', 500) in calls
    assert len(calls) == (1 if correct else 2)
    assert all(elapsed == 500 for _, elapsed in calls)
    assert all(pixels(screen.subsurface(rect)) == value for rect, value in distractors)
    state.handle_events([click(chosen_button.rect.center)])
    if correct:
        state.update(state.reveal.duration_ms - 501)
        assert (state.player.cell, state.npc.cell, state.moves_remaining, state.rng.getstate()) == before
        state.update(1)
    else:
        state.update(60_000)  # a held reveal never expires on its own
        assert (state.player.cell, state.npc.cell, state.moves_remaining, state.rng.getstate()) == before
        assert state.pending is not None
        state.handle_events([click(popup.continue_button.rect.center)])
        land_press(state)
    assert state.reveal is None and state.pending is None
    assert state.moves_remaining == before[2] - 1
    next_click = click(state.view.cell_to_rect(sorted(state.moves)[0]).center)
    if correct:
        # Timed expiry discards exactly one batch (M6.c rule).
        state.handle_events([next_click])
        assert state.pending is None
    else:
        # Click-to-continue: the rest of the Continue batch is dropped, and
        # so is the batch after the press lands.
        state.handle_events([])
    state.handle_events([next_click])
    assert state.pending is not None
