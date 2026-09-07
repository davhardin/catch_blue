import pygame

from constants import SCREEN_WIDTH
from theme import Alignment
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

CREDITS_TEXT = 'UI assets: Kenney | Fonts: Braille Institute'
CREDITS_RECT = pygame.Rect(40, 650, SCREEN_WIDTH - 80, 40)


def _draw_centered_text(screen, text, renderer, y):
    renderer.text(
        screen, text, pygame.Rect(0, y, SCREEN_WIDTH, renderer.measure(text, 'title')[1]),
        'title', alignment=Alignment('center', 'top'),
    )


def _make_menu_button(text, renderer, top, active=True):
    return Button(
        pygame.Rect(
            BUTTON_LEFT,
            top,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
        text,
        renderer,
        active=active,
    )


class GameSelectState:
    def __init__(self, game, bank: QuestionBank):
        self.game = game
        self.bank = bank
        self.renderer = game.renderer

        self.catch_blue_button = _make_menu_button(
            "Catch Blue",
            self.renderer,
            FIRST_BUTTON_TOP,
        )
        self.run_from_red_button = _make_menu_button(
            "Run from Red (coming soon)",
            self.renderer,
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

    def update(self, dt_ms):
        pass

    def draw(self, screen):
        self.renderer.fill(screen)
        _draw_centered_text(
            screen,
            "Select Game",
            self.renderer,
            140,
        )
        self.catch_blue_button.draw(screen)
        self.run_from_red_button.draw(screen)
        self.renderer.text(screen, CREDITS_TEXT, CREDITS_RECT, 'credits')


class SubjectState:
    def __init__(self, game, bank: QuestionBank, mode):
        self.game = game
        self.bank = bank
        self.mode = mode
        self.renderer = game.renderer

        self.anatomy_button = _make_menu_button(
            subject_display_name("anatomy_physiology"),
            self.renderer,
            FIRST_BUTTON_TOP,
        )
        self.organic_chemistry_button = _make_menu_button(
            f"{subject_display_name('organic_chemistry')} (coming soon)",
            self.renderer,
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

    def update(self, dt_ms):
        pass

    def draw(self, screen):
        self.renderer.fill(screen)
        _draw_centered_text(
            screen,
            "Select Subject",
            self.renderer,
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
        self.renderer = game.renderer

        self.all_checkbox = Checkbox(
            pygame.Rect(
                CHECKBOX_LEFT,
                CHECKBOX_TOP,
                CHECKBOX_SIZE,
                CHECKBOX_SIZE,
            ),
            "All",
            self.renderer,
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
                self.renderer,
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
        self.scroll_region = SCROLL_REGION.copy()
        right = max(SCROLL_REGION.right, max(checkbox.hit_rect.right for checkbox in checkboxes) + 8)
        self.scroll_region.width = right - self.scroll_region.left
        content_bottom = max(
            checkbox.hit_rect.bottom
            for checkbox in checkboxes
        )
        self.scroll_offset = 0
        self.max_scroll = max(
            0,
            content_bottom - self.scroll_region.bottom,
        )

        self.start_button = _make_menu_button(
            "Start",
            self.renderer,
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

            if not self.scroll_region.collidepoint(event.pos):
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

    def update(self, dt_ms):
        pass

    def draw(self, screen):
        self.renderer.fill(screen)
        _draw_centered_text(
            screen,
            "Select Topics",
            self.renderer,
            120,
        )
        with self.renderer.clip(screen, self.scroll_region):
            self.all_checkbox.draw(
                screen,
                offset_y=self.scroll_offset,
            )
            for _, checkbox in self.topic_checkboxes:
                checkbox.draw(
                    screen,
                    offset_y=self.scroll_offset,
                )

        self.start_button.draw(screen)
