import pygame

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT,
    MENU_BUTTON_GAP, SIDE_PANEL_PADDING,
)
from ui import Button, ButtonAction, TextBox, pointer_position, update_button_lifts


class PauseState:
    def __init__(self, play_state):
        self.play_state = play_state
        self.game = play_state.game
        self.renderer = play_state.renderer
        self.pointer_pos = None
        self.button_action = ButtonAction()
        self.play_state.pause_button.reset_lift()

        padding = SIDE_PANEL_PADDING
        content_width = MENU_BUTTON_WIDTH
        self.title = TextBox('Paused', self.renderer, 'result', 0, 0, content_width)

        self.continue_button = Button(
            pygame.Rect(
                0, self.title.height + MENU_BUTTON_GAP,
                content_width, MENU_BUTTON_HEIGHT,
            ),
            'Continue',
            self.renderer,
            lift=self.renderer.theme.menu_lift,
        )
        self.retry_button = Button(
            pygame.Rect(
                0, self.continue_button.rect.bottom + MENU_BUTTON_GAP,
                content_width, MENU_BUTTON_HEIGHT,
            ),
            'Retry',
            self.renderer,
            lift=self.renderer.theme.menu_lift,
        )
        self.main_menu_button = Button(
            pygame.Rect(
                0, self.retry_button.rect.bottom + MENU_BUTTON_GAP,
                content_width, MENU_BUTTON_HEIGHT,
            ),
            'Main Menu',
            self.renderer,
            lift=self.renderer.theme.menu_lift,
        )
        self.buttons = (
            self.continue_button, self.retry_button, self.main_menu_button,
        )
        self.panel_rect = pygame.Rect(
            0, 0, content_width + 2 * padding,
            self.main_menu_button.rect.bottom + 2 * padding,
        )
        self.panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        offset = (self.panel_rect.left + padding, self.panel_rect.top + padding)
        self.title.x += offset[0]
        self.title.y += offset[1]
        for button in self.buttons:
            button.rect.move_ip(*offset)

    def _resume(self):
        self.play_state.pointer_pos = None
        self.play_state.hovering = None
        self.play_state.hovered_answer = None
        self.game.change_state(self.play_state)

    def handle_events(self, events):
        if self.button_action.blocks_events():
            for event in events:
                self.pointer_pos = pointer_position(self.pointer_pos, event)
            return

        for event in events:
            self.pointer_pos = pointer_position(self.pointer_pos, event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._resume()
                return

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.continue_button.is_clicked(event.pos):
                self.button_action.begin(self.continue_button, self._resume)
                return

            if self.retry_button.is_clicked(event.pos):
                self.button_action.begin(
                    self.retry_button,
                    lambda: self.game.start_play(
                        self.play_state.bank, self.play_state.config,
                    ),
                )
                return

            if self.main_menu_button.is_clicked(event.pos):
                self.button_action.begin(
                    self.main_menu_button,
                    lambda: self.game.show_main_menu(self.play_state.bank),
                )
                return

    def update(self, dt_ms):
        # Gameplay time must not advance while paused; update only our buttons.
        update_button_lifts(self.buttons, dt_ms, self.pointer_pos)
        self.button_action.update(dt_ms)

    def draw(self, screen):
        self.play_state.draw(screen, show_pause=True)
        self.renderer.panel(screen, self.panel_rect)
        self.title.draw(screen)
        for button in self.buttons:
            button.draw(screen)
