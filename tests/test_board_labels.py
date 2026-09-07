"""Display-only board aliases and shipped-label fit on the current 5x5 board."""

from collections import Counter
from pathlib import Path

import pygame
import pytest

from render import Renderer
from theme import FLAT
from board import Board, Cell
from board_view import BoardView
from constants import BOARD_REGION, LABEL_PADDING
from game_setup import subtopic_display_name
from questions import QuestionBank


@pytest.fixture
def renderer():
    pygame.font.init()
    try:
        yield Renderer(FLAT)
    finally:
        pygame.font.quit()


def test_board_draw_uses_display_alias_without_mutating_labels(renderer, monkeypatch):
    board = Board(5, 5)
    view = BoardView(board, 0, 0, BOARD_REGION)
    labels = {cell: ("cells", "Overview") for cell in board.cells()}
    raw_subtopic = "Neuromuscular Junction, EC Coupling, and Cross-Bridge Cycling"
    labels[Cell(0, 0)] = ("muscular_system", raw_subtopic)
    original = labels.copy()
    wrapped_texts = []

    original_wrap = renderer.wrap

    def recording_word_wrap(text, width, font_role):
        wrapped_texts.append(text)
        return original_wrap(text, width, font_role)

    monkeypatch.setattr(renderer, "wrap", recording_word_wrap)
    view.draw(
        pygame.Surface((BOARD_REGION, BOARD_REGION)),
        hovered=None,
        entities=[],
        selected=None,
        moves=set(),
        labels=labels,
        renderer=renderer,
    )

    assert Counter(wrapped_texts) == {"Muscle Physiology": 1, "Overview": 24}
    assert raw_subtopic not in wrapped_texts
    assert labels == original


def test_all_shipped_labels_fit_current_board(renderer):
    bank = QuestionBank(Path(__file__).resolve().parent.parent / "data" / "questions")
    raw_pairs = {(q.topic, q.subtopic) for q in bank.questions}
    assert len(raw_pairs) == 75
    view = BoardView(Board(5, 5), 0, 0, BOARD_REGION)
    available = view.cell_size - 2 * LABEL_PADDING
    failures = []

    for topic, subtopic in sorted(raw_pairs):
        display_name = subtopic_display_name(topic, subtopic)
        lines = renderer.wrap(display_name, available, 'label')
        widths = [renderer.measure(line, 'label')[0] for line in lines]
        rect = pygame.Rect(LABEL_PADDING, LABEL_PADDING, available, available)
        assert all(rect.contains(line_rect) for line_rect in renderer.text_rects(lines, rect, 'label'))
        height = len(lines) * renderer.line_height('label')
        if any(width > available for width in widths) or height > available:
            failures.append(
                f"{(topic, subtopic)!r}: display={display_name!r}, "
                f"lines={lines!r}, widths={widths}, height={height}, "
                f"available={available}x{available}"
            )

    assert not failures, "Labels exceed cell bounds:\n" + "\n".join(failures)
