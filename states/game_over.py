import pygame

from constants import (
    CELL_COLOR,
    LINE_COLOR,
    MENU_TEXT_COLOR,
    MOVE_COLOR,
)
from ui import Button, TextBox

PANEL_LEFT = 720
PANEL_TOP = 40
PANEL_WIDTH = 520
PANEL_HEIGHT = 640
PANEL_PADDING = 40

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
        self.result_font = pygame.font.Font(None, 40)
        self.button_font = pygame.font.Font(None, 36)

        self.panel_rect = pygame.Rect(
            PANEL_LEFT,
            PANEL_TOP,
            PANEL_WIDTH,
            PANEL_HEIGHT,
        )
        content_left = PANEL_LEFT + PANEL_PADDING
        content_width = PANEL_WIDTH - 2 * PANEL_PADDING

        if self.result == "win":
            message = "You caught Blue!"
            replay_text = "Play again"
        else:
            message = "Blue got away!"
            replay_text = "Try again"

        self.result_box = TextBox(
            message,
            self.result_font,
            MENU_TEXT_COLOR,
            content_left,
            PANEL_TOP + 80,
            content_width,
        )

        replay_top = PANEL_TOP + 220
        main_menu_top = replay_top + BUTTON_HEIGHT + BUTTON_GAP

        self.replay_button = Button(
            pygame.Rect(
                content_left,
                replay_top,
                content_width,
                BUTTON_HEIGHT,
            ),
            replay_text,
            self.button_font,
            MENU_TEXT_COLOR,
            MOVE_COLOR,
        )
        self.main_menu_button = Button(
            pygame.Rect(
                content_left,
                main_menu_top,
                content_width,
                BUTTON_HEIGHT,
            ),
            "Main Menu",
            self.button_font,
            MENU_TEXT_COLOR,
            MOVE_COLOR,
        )

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

        pygame.draw.rect(screen, CELL_COLOR, self.panel_rect)
        pygame.draw.rect(screen, LINE_COLOR, self.panel_rect, width=2)

        self.result_box.draw(screen)
        self.replay_button.draw(screen)
        self.main_menu_button.draw(screen)
