import pygame

from constants import (
    BG_COLOR,
    MENU_TEXT_COLOR,
    MOVE_COLOR,
    SCREEN_WIDTH,
)
from game_setup import GameConfig, prettify_topic
from questions import QuestionBank
from ui import Button, Checkbox

BUTTON_WIDTH = 520
BUTTON_HEIGHT = 64
BUTTON_LEFT = (SCREEN_WIDTH - BUTTON_WIDTH) // 2
FIRST_BUTTON_TOP = 260
BUTTON_GAP = 24

CHECKBOX_LEFT = 380
CHECKBOX_TOP = 225
CHECKBOX_SIZE = 30
CHECKBOX_GAP = 52


def _draw_centered_text(screen, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(centerx=SCREEN_WIDTH // 2, top=y)
    screen.blit(rendered, rect)


def _make_menu_button(text, font, top, active=True):
    return Button(
        pygame.Rect(
            BUTTON_LEFT,
            top,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
        text,
        font,
        MENU_TEXT_COLOR,
        MOVE_COLOR,
        active=active,
    )


class GameSelectState:
    def __init__(self, game, bank: QuestionBank):
        self.game = game
        self.bank = bank
        self.title_font = pygame.font.Font(None, 56)
        self.button_font = pygame.font.Font(None, 36)

        self.catch_blue_button = _make_menu_button(
            "Catch Blue",
            self.button_font,
            FIRST_BUTTON_TOP,
        )
        self.run_from_red_button = _make_menu_button(
            "Run from Red (coming soon)",
            self.button_font,
            FIRST_BUTTON_TOP + BUTTON_HEIGHT + BUTTON_GAP,
            active=False,
        )

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.catch_blue_button.is_clicked(event.pos):
                self.game.change_state(
                    SubjectState(
                        self.game,
                        self.bank,
                        mode="catch_blue",
                    )
                )
                return

    def draw(self, screen):
        screen.fill(BG_COLOR)
        _draw_centered_text(
            screen,
            "Select Game",
            self.title_font,
            MENU_TEXT_COLOR,
            140,
        )
        self.catch_blue_button.draw(screen)
        self.run_from_red_button.draw(screen)


class SubjectState:
    def __init__(self, game, bank: QuestionBank, mode):
        self.game = game
        self.bank = bank
        self.mode = mode
        self.title_font = pygame.font.Font(None, 56)
        self.button_font = pygame.font.Font(None, 36)

        self.anatomy_button = _make_menu_button(
            "Anatomy & Physiology",
            self.button_font,
            FIRST_BUTTON_TOP,
        )
        self.organic_chemistry_button = _make_menu_button(
            "Organic Chemistry (coming soon)",
            self.button_font,
            FIRST_BUTTON_TOP + BUTTON_HEIGHT + BUTTON_GAP,
            active=False,
        )

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.anatomy_button.is_clicked(event.pos):
                self.game.change_state(
                    TopicsState(
                        self.game,
                        self.bank,
                        mode=self.mode,
                        subject="anatomy_physiology",
                    )
                )
                return

    def draw(self, screen):
        screen.fill(BG_COLOR)
        _draw_centered_text(
            screen,
            "Select Subject",
            self.title_font,
            MENU_TEXT_COLOR,
            140,
        )
        self.anatomy_button.draw(screen)
        self.organic_chemistry_button.draw(screen)


class TopicsState:
    def __init__(self, game, bank: QuestionBank, mode, subject):
        self.game = game
        self.bank = bank
        self.mode = mode
        self.subject = subject
        self.title_font = pygame.font.Font(None, 56)
        self.checkbox_font = pygame.font.Font(None, 30)
        self.button_font = pygame.font.Font(None, 36)

        self.all_checkbox = Checkbox(
            pygame.Rect(
                CHECKBOX_LEFT,
                CHECKBOX_TOP,
                CHECKBOX_SIZE,
                CHECKBOX_SIZE,
            ),
            "All",
            self.checkbox_font,
            MENU_TEXT_COLOR,
            checked=True,
        )

        self.topic_checkboxes = []
        for index, topic in enumerate(self.bank.topics, start=1):
            checkbox = Checkbox(
                pygame.Rect(
                    CHECKBOX_LEFT,
                    CHECKBOX_TOP + index * CHECKBOX_GAP,
                    CHECKBOX_SIZE,
                    CHECKBOX_SIZE,
                ),
                prettify_topic(topic),
                self.checkbox_font,
                MENU_TEXT_COLOR,
                checked=True,
            )
            self.topic_checkboxes.append((topic, checkbox))

        start_top = (
            CHECKBOX_TOP
            + (len(self.bank.topics) + 1) * CHECKBOX_GAP
            + 20
        )
        self.start_button = _make_menu_button(
            "Start",
            self.button_font,
            start_top,
        )
        self._update_start_button()

    def _update_start_button(self):
        self.start_button.active = any(
            checkbox.checked
            for _, checkbox in self.topic_checkboxes
        )

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.all_checkbox.is_clicked(event.pos):
                self.all_checkbox.toggle()
                for _, checkbox in self.topic_checkboxes:
                    checkbox.checked = self.all_checkbox.checked
                self._update_start_button()
                continue

            topic_toggled = False
            for _, checkbox in self.topic_checkboxes:
                if checkbox.is_clicked(event.pos):
                    checkbox.toggle()
                    self.all_checkbox.checked = all(
                        topic_checkbox.checked
                        for _, topic_checkbox in self.topic_checkboxes
                    )
                    self._update_start_button()
                    topic_toggled = True
                    break

            if topic_toggled:
                continue

            if self.start_button.is_clicked(event.pos):
                selected_topics = tuple(
                    topic
                    for topic, checkbox in self.topic_checkboxes
                    if checkbox.checked
                )
                config = GameConfig(
                    mode=self.mode,
                    subject=self.subject,
                    selected_topics=selected_topics,
                )
                self.game.start_play(self.bank, config)
                return

    def draw(self, screen):
        screen.fill(BG_COLOR)
        _draw_centered_text(
            screen,
            "Select Topics",
            self.title_font,
            MENU_TEXT_COLOR,
            120,
        )
        self.all_checkbox.draw(screen)

        for _, checkbox in self.topic_checkboxes:
            checkbox.draw(screen)

        self.start_button.draw(screen)
