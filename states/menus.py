import pygame

from constants import (
    SCREEN_WIDTH, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT, MENU_BUTTON_GAP,
    MENU_BUTTON_LEFT, MENU_FIRST_BUTTON_TOP, MENU_TITLE_TOP,
    MENU_CHECKBOX_SIZE, MENU_ROW_HEIGHT, MENU_LIST_SIDE_PADDING,
    MENU_CHECKBOX_LEFT, MENU_CHECKBOX_TOP, MENU_TOPICS_TITLE_TOP,
    MENU_SCROLL_LEFT, MENU_SCROLL_TOP, MENU_SCROLL_WIDTH, MENU_SCROLL_HEIGHT,
    MENU_START_TOP, MENU_CREDITS_SIDE_MARGIN, MENU_CREDITS_TOP, MENU_CREDITS_HEIGHT,
)
from theme import Alignment
from game_setup import (
    GameConfig,
    order_topics_for_subject,
    prettify_topic,
    subject_display_name,
)
from questions import QuestionBank
from ui import Button, Checkbox

SCROLL_REGION = pygame.Rect(
    MENU_SCROLL_LEFT, MENU_SCROLL_TOP, MENU_SCROLL_WIDTH, MENU_SCROLL_HEIGHT,
)

CREDITS_TEXT = 'UI assets: Kenney | Fonts: Braille Institute'
CREDITS_RECT = pygame.Rect(
    MENU_CREDITS_SIDE_MARGIN, MENU_CREDITS_TOP,
    SCREEN_WIDTH - 2 * MENU_CREDITS_SIDE_MARGIN, MENU_CREDITS_HEIGHT,
)


def _draw_centered_text(screen, text, renderer, y):
    renderer.text(
        screen, text, pygame.Rect(0, y, SCREEN_WIDTH, renderer.measure(text, 'title')[1]),
        'title', alignment=Alignment('center', 'top'),
    )


def _make_menu_button(text, renderer, top, active=True):
    return Button(
        pygame.Rect(
            MENU_BUTTON_LEFT,
            top,
            MENU_BUTTON_WIDTH,
            MENU_BUTTON_HEIGHT,
        ),
        text,
        renderer,
        active=active,
        lift=renderer.theme.menu_lift,
    )


def _menu_pointer_position(current, event):
    if event.type == pygame.WINDOWLEAVE:
        return None
    if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
        return event.pos
    return current


def _update_menu_button_lifts(buttons, dt_ms, pointer_pos):
    for button in buttons:
        hovered = pointer_pos is not None and button.is_clicked(pointer_pos)
        button.update_lift(dt_ms, hovered=hovered)


class GameSelectState:
    def __init__(self, game, bank: QuestionBank):
        self.game = game
        self.bank = bank
        self.renderer = game.renderer
        self.pointer_pos: tuple[int, int] | None = None

        self.catch_blue_button = _make_menu_button(
            "Catch Blue",
            self.renderer,
            MENU_FIRST_BUTTON_TOP,
        )
        self.run_from_red_button = _make_menu_button(
            "Run from Red (coming soon)",
            self.renderer,
            MENU_FIRST_BUTTON_TOP + MENU_BUTTON_HEIGHT + MENU_BUTTON_GAP,
            active=False,
        )

    def handle_events(self, events):
        for event in events:
            self.pointer_pos = _menu_pointer_position(self.pointer_pos, event)
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
        _update_menu_button_lifts(
            (self.catch_blue_button, self.run_from_red_button), dt_ms, self.pointer_pos,
        )

    def draw(self, screen):
        self.renderer.fill(screen)
        _draw_centered_text(
            screen,
            "Select Game",
            self.renderer,
            MENU_TITLE_TOP,
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
        self.pointer_pos: tuple[int, int] | None = None

        self.anatomy_button = _make_menu_button(
            subject_display_name("anatomy_physiology"),
            self.renderer,
            MENU_FIRST_BUTTON_TOP,
        )
        self.organic_chemistry_button = _make_menu_button(
            f"{subject_display_name('organic_chemistry')} (coming soon)",
            self.renderer,
            MENU_FIRST_BUTTON_TOP + MENU_BUTTON_HEIGHT + MENU_BUTTON_GAP,
            active=False,
        )

    def handle_events(self, events):
        for event in events:
            self.pointer_pos = _menu_pointer_position(self.pointer_pos, event)
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
        _update_menu_button_lifts(
            (self.anatomy_button, self.organic_chemistry_button), dt_ms, self.pointer_pos,
        )

    def draw(self, screen):
        self.renderer.fill(screen)
        _draw_centered_text(
            screen,
            "Select Subject",
            self.renderer,
            MENU_TITLE_TOP,
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
        self.pointer_pos: tuple[int, int] | None = None

        self.all_checkbox = Checkbox(
            pygame.Rect(
                MENU_CHECKBOX_LEFT,
                MENU_CHECKBOX_TOP,
                MENU_CHECKBOX_SIZE,
                MENU_CHECKBOX_SIZE,
            ),
            "All",
            self.renderer,
            checked=True,
        )

        self.topic_checkboxes = []
        for index, topic in enumerate(self.topics, start=1):
            checkbox = Checkbox(
                pygame.Rect(
                    MENU_CHECKBOX_LEFT,
                    MENU_CHECKBOX_TOP + index * MENU_ROW_HEIGHT,
                    MENU_CHECKBOX_SIZE,
                    MENU_CHECKBOX_SIZE,
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
        right = max(SCROLL_REGION.right, max(checkbox.hit_rect.right for checkbox in checkboxes) + MENU_LIST_SIDE_PADDING)
        self.scroll_region.width = right - self.scroll_region.left
        self.scroll_offset = 0
        self.max_scroll = max(
            0, len(checkboxes) * MENU_ROW_HEIGHT - self.scroll_region.height,
        )

        self.start_button = _make_menu_button(
            "Start",
            self.renderer,
            MENU_START_TOP,
        )
        self._update_start_button()

    def _update_start_button(self):
        self.start_button.active = any(
            checkbox.checked
            for _, checkbox in self.topic_checkboxes
        )
        if not self.start_button.active:
            self.start_button.reset_lift()

    def _set_scroll_offset(self, offset):
        clamped = max(0, min(offset, self.max_scroll))
        self.scroll_offset = (int(clamped) // MENU_ROW_HEIGHT) * MENU_ROW_HEIGHT

    def handle_events(self, events):
        for event in events:
            self.pointer_pos = _menu_pointer_position(self.pointer_pos, event)
            if event.type == pygame.MOUSEWHEEL:
                self._set_scroll_offset(
                    self.scroll_offset - event.y * MENU_ROW_HEIGHT
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
        _update_menu_button_lifts((self.start_button,), dt_ms, self.pointer_pos)

    def draw(self, screen):
        self.renderer.fill(screen)
        _draw_centered_text(
            screen,
            "Select Topics",
            self.renderer,
            MENU_TOPICS_TITLE_TOP,
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
