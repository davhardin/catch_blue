import pygame

from constants import (
    SIDE_PANEL_LEFT, SIDE_PANEL_TOP, SIDE_PANEL_WIDTH, SIDE_PANEL_PADDING,
)
from ui import Button, TextBox

BUTTON_HEIGHT = 60
BUTTON_GAP = 24


class GameOverState:
    def __init__(self, game, bank, config, result, play_state):
        if result not in {"win", "lose"}:
            raise ValueError(f"Unknown game result: {result}")

        self.game = game
        self.bank = bank
        self.config = config
        self.result = result
        self.play_state = play_state
        self.renderer = game.renderer

        content_left = SIDE_PANEL_LEFT + SIDE_PANEL_PADDING
        content_width = SIDE_PANEL_WIDTH - 2 * SIDE_PANEL_PADDING

        if self.result == "win":
            message = "You caught Blue!"
            replay_text = "Play again"
        else:
            message = "Blue got away!"
            replay_text = "Try again"

        self.result_box = TextBox(
            message,
            self.renderer,
            'result',
            content_left,
            SIDE_PANEL_TOP + SIDE_PANEL_PADDING,
            content_width,
        )

        replay_top = self.result_box.y + self.result_box.height + BUTTON_GAP

        self.replay_button = Button(
            pygame.Rect(
                content_left,
                replay_top,
                content_width,
                BUTTON_HEIGHT,
            ),
            replay_text,
            self.renderer,
        )
        self.main_menu_button = Button(
            pygame.Rect(
                content_left,
                self.replay_button.rect.bottom + BUTTON_GAP,
                content_width,
                BUTTON_HEIGHT,
            ),
            "Main Menu",
            self.renderer,
        )
        self.panel_rect = pygame.Rect(
            SIDE_PANEL_LEFT,
            SIDE_PANEL_TOP,
            SIDE_PANEL_WIDTH,
            self.main_menu_button.rect.bottom + SIDE_PANEL_PADDING - SIDE_PANEL_TOP,
        )

    def update(self, dt_ms):
        pass

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.replay_button.is_clicked(event.pos):
                self.game.start_play(self.bank, self.config)
                return

            if self.main_menu_button.is_clicked(event.pos):
                self.game.show_main_menu(self.bank)
                return

    def draw(self, screen):
        self.play_state.draw(screen)

        self.renderer.panel(screen, self.panel_rect)

        self.result_box.draw(screen)
        self.replay_button.draw(screen)
        self.main_menu_button.draw(screen)
