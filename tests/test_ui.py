"""Button feedback preserves layout, eligibility, and reset behavior."""

import pygame
import pytest

from render import Renderer
from theme import FLAT
from ui import Button


@pytest.fixture
def renderer():
    pygame.font.init()
    yield Renderer(FLAT)
    pygame.font.quit()


@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("highlight", ["correct", "incorrect"])
def test_highlight_overlays_normal_button_and_resets(renderer, active, highlight):
    background = (60, 88, 90)
    foreground = (245, 245, 245)
    button = Button(
        pygame.Rect(10, 10, 180, 60), "Answer", renderer, active=active,
    )
    surface = pygame.Surface((200, 80))
    sample = (button.rect.right - 2, button.rect.bottom - 2)
    normal_background = background if active else FLAT.palette.button_inactive
    text_color = foreground if active else FLAT.palette.text_inactive
    expected_text = renderer.font("button").render("Answer", True, text_color)

    def assert_rendered(expected_background):
        surface.fill((1, 2, 3))
        button.draw(surface)
        if button.highlight is None:
            assert tuple(surface.get_at(sample))[:3] == expected_background
        expected = pygame.Surface(surface.get_size())
        expected.fill((1, 2, 3))
        base_color = renderer.color('correct') if button.highlight == 'correct' else expected_background
        pygame.draw.rect(expected, base_color, button.rect)
        if button.highlight == 'correct':
            renderer.answer_feedback(expected, button.rect, button.highlight, 0)
        expected.blit(expected_text, button.rect.topleft)
        if button.highlight == 'incorrect':
            renderer.answer_feedback(expected, button.rect, button.highlight, 0)
        assert pygame.image.tobytes(surface, "RGB") == pygame.image.tobytes(expected, "RGB")
        assert button.is_clicked(button.rect.center) == active
        assert not button.is_clicked((0, 0))
        assert button.active == active
        assert button.renderer is renderer
        assert button.font_role == "button"
        assert renderer.color("button") == background
        assert renderer.color("text") == foreground

    assert button.highlight is None
    assert_rendered(normal_background)
    button.highlight = highlight
    assert_rendered(normal_background)
    button.highlight = None
    assert_rendered(normal_background)
