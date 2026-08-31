import pygame

from constants import INACTIVE_BUTTON_COLOR, INACTIVE_TEXT_COLOR

def word_wrap(text: str, width: int, font) -> list[str]:
    lines = []

    for word in text.split():
        if not lines:
            lines.append(word)
        elif font.size(lines[-1] + ' ' + word)[0] <= width:
            lines[-1] += ' ' + word
        else:
            lines.append(word)
    return lines


class TextBox:
    def __init__(self, text, font, color, x, y, width):
        self.text = text
        self.font = font
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.lines = word_wrap(text, width, font)
        self.height = self.font.get_linesize() * len(self.lines)

    def draw(self, surface):
        for i, line in enumerate(self.lines):
            surface.blit(
                self.font.render(line, True, self.color),
                (self.x, self.y + i * self.font.get_linesize())
            )

class Button:
    def __init__(self, rect, text, font, color, rect_color, active=True):
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color
        self.rect_color = rect_color
        self.active = active
        self.lines = word_wrap(text, rect.width, font)
        self.height = self.font.get_linesize() * len(self.lines)
        self.rect.height = max(self.height, rect.height)

    def draw(self, surface):
        rect_color = self.rect_color if self.active else INACTIVE_BUTTON_COLOR
        text_color = self.color if self.active else INACTIVE_TEXT_COLOR

        pygame.draw.rect(surface, rect_color, self.rect)
        for i, line in enumerate(self.lines):
            surface.blit(
                self.font.render(line, True, text_color),
                (self.rect.x, self.rect.y + i * self.font.get_linesize())
            )

    def is_clicked(self, pos):
        return self.active and self.rect.collidepoint(pos)


class Checkbox:
    def __init__(self, rect, text, font, color, checked=False):
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color
        self.checked = checked
        self.label = self.font.render(self.text, True, self.color)
        self.label_rect = self.label.get_rect(
            midleft=(self.rect.right + 12, self.rect.centery)
        )
        self.hit_rect = self.rect.union(self.label_rect)

    def toggle(self):
        self.checked = not self.checked

    def is_clicked(self, pos):
        return self.hit_rect.collidepoint(pos)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, width=2)

        if self.checked:
            inner = self.rect.inflate(-8, -8)
            pygame.draw.rect(surface, self.color, inner)

        surface.blit(self.label, self.label_rect)
