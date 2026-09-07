"""Button reveal backgrounds must not change text styling or eligibility."""

import pygame
import pytest

from constants import INACTIVE_BUTTON_COLOR, INACTIVE_TEXT_COLOR
from ui import Button


@pytest.fixture
def font():
    pygame.font.init()
    yield pygame.font.Font(None, 24)
    pygame.font.quit()


@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("highlight", [(0, 100, 70), (150, 45, 35)])
def test_highlight_overrides_only_background_and_resets(font, active, highlight):
    background = (60, 88, 90)
    foreground = (245, 245, 245)
    button = Button(
        pygame.Rect(10, 10, 180, 60), "Answer", font,
        foreground, background, active=active,
    )
    surface = pygame.Surface((200, 80))
    sample = (button.rect.right - 2, button.rect.bottom - 2)
    normal_background = background if active else INACTIVE_BUTTON_COLOR
    text_color = foreground if active else INACTIVE_TEXT_COLOR
    expected_text = font.render("Answer", True, text_color)

    def assert_rendered(expected_background):
        surface.fill((1, 2, 3))
        button.draw(surface)
        assert tuple(surface.get_at(sample))[:3] == expected_background
        expected = pygame.Surface(surface.get_size())
        expected.fill((1, 2, 3))
        pygame.draw.rect(expected, expected_background, button.rect)
        expected.blit(expected_text, button.rect.topleft)
        assert pygame.image.tobytes(surface, "RGB") == pygame.image.tobytes(expected, "RGB")
        assert button.is_clicked(button.rect.center) == active
        assert not button.is_clicked((0, 0))
        assert button.active == active
        assert button.rect_color == background
        assert button.color == foreground

    assert button.highlight_color is None
    assert_rendered(normal_background)
    button.highlight_color = highlight
    assert_rendered(highlight)
    button.highlight_color = None
    assert_rendered(normal_background)
