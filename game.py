import sys
from random import Random

import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from modes import DEFAULT_MODE, MODES, get_mode
from render import Renderer
from states.menus import GameSelectState, SubjectState, TopicsState
from states.play import PlayState
from states.settings import SettingsState
from theme import (
    Accent,
    ACCENT_KEYS,
    DEFAULT_THEME,
    THEMES,
    resolve_accent,
    theme_accent,
)


class Game:
    def __init__(
        self,
        bank,
        rng=None,
        *,
        theme=THEMES[DEFAULT_THEME],
        dev_accent_cycle=False,
    ):
        pygame.init()
        self._base_theme = theme
        self.renderer = Renderer(theme)
        self._renderers = {
            self.renderer.theme.name: self.renderer,
        }
        self._dev_accent_cycle = dev_accent_cycle
        self._accent_override: Accent | None = None

        self.bank = bank
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
        self.settings_by_mode = {
            mode.key: mode.settings_spec().default
            for mode in MODES.values()
            if mode.active
        }
        self.settings_mode = DEFAULT_MODE
        self.topic_selections: dict[
            tuple[str, str], tuple[str, ...]
        ] = {}
        self.state = GameSelectState(self)

    def change_state(self, state):
        self.state = state

    def renderer_for(self, accent: Accent):
        effective_accent = self._accent_override or accent
        theme = resolve_accent(
            self._base_theme,
            effective_accent,
        )
        renderer = self._renderers.get(theme.name)
        if renderer is None:
            renderer = Renderer(theme)
            self._renderers[theme.name] = renderer
        return renderer

    def _rebuild_menu_for_accent(self):
        state = self.state

        if isinstance(state, GameSelectState):
            replacement = GameSelectState(self)
        elif isinstance(state, SubjectState):
            replacement = SubjectState(self, mode=state.mode)
        elif isinstance(state, TopicsState):
            replacement = TopicsState(
                self,
                mode=state.mode,
                subject=state.subject,
            )
            replacement._set_scroll_offset(state.scroll_offset)
        elif isinstance(state, SettingsState):
            replacement = SettingsState(self, mode=state.mode)
        else:
            return False

        self.change_state(replacement)
        return True

    def _cycle_dev_accent(self):
        if not self._dev_accent_cycle:
            return

        base_accent = theme_accent(self._base_theme)
        if base_accent is None:
            return

        state = self.state
        if not isinstance(
            state,
            (GameSelectState, SubjectState, TopicsState, SettingsState),
        ):
            return

        current = self._accent_override or base_accent
        index = ACCENT_KEYS.index(current)
        accent = ACCENT_KEYS[(index + 1) % len(ACCENT_KEYS)]

        self._accent_override = accent
        self.renderer = self.renderer_for(accent)
        self._rebuild_menu_for_accent()

    def start_play(self, config):
        mode = get_mode(config.mode)
        renderer = self.renderer_for(mode.accent)
        self.change_state(
            PlayState(
                self,
                config,
                self.rng,
                renderer=renderer,
            )
        )

    def show_main_menu(self):
        self.change_state(GameSelectState(self))

    def step(self):
        """Advance one frame. Return False once the player has quit."""
        dt_ms = self.clock.tick(self.fps)
        state_events = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif (
                self._dev_accent_cycle
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_F8
            ):
                self._cycle_dev_accent()
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
