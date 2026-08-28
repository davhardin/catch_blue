import pygame

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
    def __init__(self, rect, text, font, color, rect_color):
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color
        self.rect_color = rect_color
        self.lines = word_wrap(text, rect.width, font)
        self.height = self.font.get_linesize() * len(self.lines)
        self.rect.height = max(self.height, rect.height)

    def draw(self, surface):
        pygame.draw.rect(surface, self.rect_color, self.rect)
        for i, line in enumerate(self.lines):
            surface.blit(
                self.font.render(line, True, self.color),
                (self.rect.x, self.rect.y + i * self.font.get_linesize())
            )

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
