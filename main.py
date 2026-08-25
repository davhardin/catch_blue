import pygame

from board import Board, Cell
from board_view import BoardView
from characters import Player, Blue
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
pygame.display.set_caption("Catch Blue: The Science Learning Game")

clock = pygame.time.Clock()
fps = 60

board = Board(5,5)
view = BoardView(board, BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION)

hovering: Cell | None = None
selected: Cell | None = None
entities = [Player.at_start(board), Blue.at_start(board)]

# Main loop

running = True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse clicking

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            selected = view.pixel_to_cell(*event.pos)

        if event.type == pygame.MOUSEMOTION:
            hovering = view.pixel_to_cell(*event.pos)


    screen.fill(BG_COLOR)
    view.draw(screen, hovering, entities, selected)
    pygame.display.flip()
    clock.tick(fps)
