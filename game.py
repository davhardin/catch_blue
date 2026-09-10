import sys
from random import Random

import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from game_setup import DEFAULT_PRESET, PRESETS
from render import Renderer
from theme import DEFAULT_THEME, THEMES
from states.menus import GameSelectState
from states.play import PlayState


class Game:
    def __init__(self, bank, rng=None, *, theme=THEMES[DEFAULT_THEME]):
        pygame.init()
        self.renderer = Renderer(theme)

        self.rng = rng if rng is not None else Random()

        # In the browser (pygbag) the page scales the canvas itself, and SCALED
        # would scale mouse coordinates a second time, so leave it off there.
        flags = 0 if sys.platform == "emscripten" else pygame.SCALED
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            flags,
        )
        pygame.display.set_caption("Catch Blue: The Science Learning Game")

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True
        self.settings = PRESETS[DEFAULT_PRESET]
        self.topic_selections: dict[
            tuple[str, str], tuple[str, ...]
        ] = {}
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

    def step(self):
        """Advance one frame. Return False once the player has quit."""
        dt_ms = self.clock.tick(self.fps)
        state_events = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                state_events.append(event)

        if not self.running:
            return False

        state = self.state
        state.update(dt_ms)

        if self.state is state:
            state.handle_events(state_events)

        self.state.draw(self.screen)
        pygame.display.flip()
        return True

    def run(self):
        while self.step():
            pass

        pygame.quit()
