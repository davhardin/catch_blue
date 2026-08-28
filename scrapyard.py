import pygame
from ui import word_wrap, TextBox, Button
from constants import BG_COLOR

pygame.init()

font = pygame.font.Font(None, 28)

test_string = "The wrap algorithm in words: split the text into words, then greedily build lines — keep a current line, and for each word ask the font how wide current line + this word would be; if it fits, append, if not, the current line is finished and the word starts the next one."
result = word_wrap(test_string, 300, font)
print(result)

surface = pygame.Surface((400, 600))
surface.fill((BG_COLOR))

textbox = TextBox(test_string, font, (255, 255, 255), 20, 20, 300)

gap = 12
button_width = 300
button_height = 50

first_button_top = textbox.y + textbox.height + gap
first_button = Button(
    pygame.Rect(
        20,
        textbox.y + textbox.height + gap,
        button_width,
        button_height,
    ),
    "The wrap algorithm in words: split the text into words",
    font,
    (255, 255, 255),
    (58, 64, 78),
)

second_button = Button(
    pygame.Rect(
        20,
        first_button.rect.bottom + gap,
        button_width,
        button_height,
    ),
    "then greedily build lines — keep a current line,",
    font,
    (255, 255, 255),
    (58, 64, 78),
)

third_button = Button(
    pygame.Rect(
        20,
        second_button.rect.bottom + gap,
        button_width,
        button_height,
    ),
    "and for each word ask the font how wide current line + this word would be; ",
    font,
    (255, 255, 255),
    (58, 64, 78),
)

textbox.draw(surface)
first_button.draw(surface)
second_button.draw(surface)
third_button.draw(surface)

pygame.image.save(surface, "scrapyard.png")
