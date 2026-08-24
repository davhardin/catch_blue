import pygame

from board import Board
from board_view import BoardView
from constants import (
    BG_COLOR,
    BOARD_ORIGIN_X,
    BOARD_ORIGIN_Y,
    BOARD_REGION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
pygame.display.set_caption("My Pygame Window")

clock = pygame.time.Clock()
fps = 60

board = Board(5,5)
view = BoardView(board, BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION)

# Main loop

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)
    view.draw(screen)
    pygame.display.flip()
    clock.tick(fps)
