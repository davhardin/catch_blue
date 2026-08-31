import pygame

from constants import (
    BG_COLOR,
    MENU_TEXT_COLOR,
    MOVE_COLOR,
    SCREEN_WIDTH,
)
from game_setup import (
    GameConfig,
    order_topics_for_subject,
    prettify_topic,
    subject_display_name,
)
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

SCROLL_REGION = pygame.Rect(300, 200, 680, 390)
SCROLL_STEP = CHECKBOX_GAP
START_BUTTON_TOP = 620


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
            subject_display_name("anatomy_physiology"),
            self.button_font,
            FIRST_BUTTON_TOP,
        )
        self.organic_chemistry_button = _make_menu_button(
            f"{subject_display_name('organic_chemistry')} (coming soon)",
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
        self.topics = order_topics_for_subject(
            self.subject,
            self.bank.topics(self.subject),
        )
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
        for index, topic in enumerate(self.topics, start=1):
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

        checkboxes = [
            self.all_checkbox,
            *[
                checkbox
                for _, checkbox in self.topic_checkboxes
            ],
        ]
        content_bottom = max(
            checkbox.hit_rect.bottom
            for checkbox in checkboxes
        )
        self.scroll_offset = 0
        self.max_scroll = max(
            0,
            content_bottom - SCROLL_REGION.bottom,
        )

        self.start_button = _make_menu_button(
            "Start",
            self.button_font,
            START_BUTTON_TOP,
        )
        self._update_start_button()

    def _update_start_button(self):
        self.start_button.active = any(
            checkbox.checked
            for _, checkbox in self.topic_checkboxes
        )

    def _set_scroll_offset(self, offset):
        self.scroll_offset = max(
            0,
            min(offset, self.max_scroll),
        )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self._set_scroll_offset(
                    self.scroll_offset - event.y * SCROLL_STEP
                )
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
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

            if not SCROLL_REGION.collidepoint(event.pos):
                continue

            content_pos = (
                event.pos[0],
                event.pos[1] + self.scroll_offset,
            )

            if self.all_checkbox.is_clicked(content_pos):
                self.all_checkbox.toggle()
                for _, checkbox in self.topic_checkboxes:
                    checkbox.checked = self.all_checkbox.checked
                self._update_start_button()
                continue

            for _, checkbox in self.topic_checkboxes:
                if checkbox.is_clicked(content_pos):
                    checkbox.toggle()
                    self.all_checkbox.checked = all(
                        topic_checkbox.checked
                        for _, topic_checkbox in self.topic_checkboxes
                    )
                    self._update_start_button()
                    break

    def draw(self, screen):
        screen.fill(BG_COLOR)
        _draw_centered_text(
            screen,
            "Select Topics",
            self.title_font,
            MENU_TEXT_COLOR,
            120,
        )
        previous_clip = screen.get_clip()
        screen.set_clip(SCROLL_REGION)

        self.all_checkbox.draw(
            screen,
            offset_y=self.scroll_offset,
        )
        for _, checkbox in self.topic_checkboxes:
            checkbox.draw(
                screen,
                offset_y=self.scroll_offset,
            )

        screen.set_clip(previous_clip)
        self.start_button.draw(screen)
