import pygame

from board import Board, Cell, is_adjacent
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
player = Player.at_start(board)
blue = Blue.at_start(board)
entities = [player, blue]

# Main loop

running = True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse clicking

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cell = view.pixel_to_cell(*event.pos)
            if cell is None:
                selected = None
            elif cell == blue.cell and is_adjacent(player.cell, blue.cell):
                print("caught!")
            elif cell in player.legal_moves(board, {blue.cell}):
                player.move_to(cell)
            else:
                selected = cell


        if event.type == pygame.MOUSEMOTION:
            hovering = view.pixel_to_cell(*event.pos)


    screen.fill(BG_COLOR)
    view.draw(screen, hovering, entities, selected)
    pygame.display.flip()
    clock.tick(fps)
