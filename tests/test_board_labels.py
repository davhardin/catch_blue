"""Display-only board aliases.

Every shipped label's fit on the board is checked by the full-bank audit in
test_pixel_layout.py, at each board size on both themes.
"""

from collections import Counter

import pygame
import pytest

from board import Board, Cell
from board_view import BoardView
from constants import BOARD_REGION


@pytest.fixture
def renderer(flat_renderer):
    """These tests pin flat's own primitives."""
    return flat_renderer


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
