from random import Random

import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from states.menus import GameSelectState
from states.play import PlayState


class Game:
    def __init__(self, bank, rng=None):
        pygame.init()

        self.rng = rng if rng is not None else Random()

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SCALED,
        )
        pygame.display.set_caption("Catch Blue: The Science Learning Game")

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True
        self.state = GameSelectState(self, bank)

    def change_state(self, state):
        self.state = state

    def start_play(self, bank, config):
        self.change_state(
            PlayState(
                self,
                bank,
                config,
                self.rng,
            )
        )

    def show_main_menu(self, bank):
        self.change_state(GameSelectState(self, bank))

    def run(self):
        while self.running:
            state_events = []

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    state_events.append(event)

            self.state.handle_events(state_events)
            self.state.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()
