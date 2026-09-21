"""Question popup layout, interaction, and answer-reveal visuals."""

from dataclasses import dataclass

import pygame

from constants import (
    SIDE_PANEL_LEFT, SIDE_PANEL_TOP, SIDE_PANEL_WIDTH, SIDE_PANEL_PADDING,
    HUD_BUTTON_WIDTH, HUD_BUTTON_HEIGHT, HUD_PANEL_GAP,
    CONTINUE_HORIZONTAL_PADDING,
)
from questions import Question
from ui import Button, TextBox, update_button_lifts


ANSWER_BUTTON_MIN_HEIGHT = 44
ANSWER_BUTTON_GAP = 12


def build_question_popup(
    question: Question,
    renderer,
    display_order: list[int],
):
    popup_left = SIDE_PANEL_LEFT
    popup_top = SIDE_PANEL_TOP
    popup_width = SIDE_PANEL_WIDTH
    padding = SIDE_PANEL_PADDING
    gap = ANSWER_BUTTON_GAP

    content_left = popup_left + padding
    content_width = popup_width - 2 * padding
    prompt_top = popup_top + padding

    prompt_box = TextBox(
        question.prompt,
        renderer,
        'prompt',
        content_left,
        prompt_top,
        content_width,
    )

    answer_buttons = []
    next_button_top = prompt_box.y + prompt_box.height + gap

    for canonical_index in display_order:
        choice = question.choices[canonical_index]
        button = Button(
            pygame.Rect(
                content_left,
                next_button_top,
                content_width,
                ANSWER_BUTTON_MIN_HEIGHT,
            ),
            choice,
            renderer,
            'choice',
        )
        answer_buttons.append(button)

        # Button may have enlarged its rect to fit wrapped text.
        next_button_top = button.rect.bottom + gap

    popup_bottom = answer_buttons[-1].rect.bottom + padding
    popup_rect = pygame.Rect(
        popup_left,
        popup_top,
        popup_width,
        popup_bottom - popup_top,
    )

    return popup_rect, prompt_box, answer_buttons


def build_reveal_continue(popup_rect, renderer):
    text = "Continue"
    text_bounds = renderer.text_rects(
        [text],
        pygame.Rect(0, 0, 1, 1),
        "button",
    )[0]
    horizontal_padding = max(
        renderer.theme.layout.button_padding,
        CONTINUE_HORIZONTAL_PADDING,
    )
    width = max(
        HUD_BUTTON_WIDTH,
        text_bounds.width + 2 * horizontal_padding,
    )

    return Button(
        pygame.Rect(
            popup_rect.right - width,
            popup_rect.bottom + HUD_PANEL_GAP,
            width,
            HUD_BUTTON_HEIGHT,
        ),
        text,
        renderer,
        lift=renderer.theme.menu_lift,
    )


@dataclass
class AnswerReveal:
    canonical_index: int
    duration_ms: int | None
    elapsed_ms: int = 0

    @property
    def waits_for_click(self) -> bool:
        return self.duration_ms is None


class QuestionPopup:
    def __init__(
        self,
        question: Question,
        renderer,
        display_order: list[int],
    ):
        self.question = question
        self.renderer = renderer
        self.answer_order = display_order
        (
            self.popup_rect,
            self.prompt_box,
            self.answer_buttons,
        ) = build_question_popup(question, renderer, display_order)

        self.hovered_answer: int | None = None
        self.reveal: AnswerReveal | None = None
        self.continue_button: Button | None = None

    @property
    def elapsed_ms(self) -> int:
        return self.reveal.elapsed_ms if self.reveal is not None else 0

    def hover(self, pos: tuple[int, int] | None):
        self.hovered_answer = None
        if pos is None or self.reveal is not None:
            return

        self.hovered_answer = next(
            (
                index
                for index, button in enumerate(self.answer_buttons)
                if button.is_clicked(pos)
            ),
            None,
        )

    def answer_at(self, pos: tuple[int, int]) -> int | None:
        if self.reveal is not None:
            return None

        for display_index, button in enumerate(self.answer_buttons):
            if button.is_clicked(pos):
                return self.answer_order[display_index]

        return None

    def begin_reveal(self, canonical_index: int, duration_ms: int):
        assert self.reveal is None

        reveal_duration = (
            None
            if duration_ms > 0 and not self.question.is_correct(canonical_index)
            else duration_ms
        )
        self.reveal = AnswerReveal(
            canonical_index,
            duration_ms=reveal_duration,
        )
        self.hovered_answer = None

        if self.reveal.waits_for_click:
            self.continue_button = build_reveal_continue(
                self.popup_rect,
                self.renderer,
            )

        for display_index, button in enumerate(self.answer_buttons):
            answer_index = self.answer_order[display_index]
            button.settle_for_reveal(
                selected=answer_index == canonical_index,
            )
            button.highlight = None

            if answer_index == self.question.answer_index:
                button.highlight = 'correct'
            elif answer_index == canonical_index:
                button.highlight = 'incorrect'

    def wants_continue(self, pos: tuple[int, int]) -> bool:
        return (
            self.reveal is not None
            and self.reveal.waits_for_click
            and self.continue_button is not None
            and self.continue_button.is_clicked(pos)
        )

    def update(
        self,
        dt_ms: int,
        pointer_pos: tuple[int, int] | None,
    ) -> bool:
        """Advance visuals; report when a timed reveal is ready to resolve."""
        if self.continue_button is not None:
            update_button_lifts(
                (self.continue_button,),
                dt_ms,
                pointer_pos,
            )

        if self.reveal is None:
            for index, button in enumerate(self.answer_buttons):
                button.update_lift(
                    dt_ms,
                    hovered=index == self.hovered_answer,
                )
            return False

        self.reveal.elapsed_ms += max(0, dt_ms)
        duration_ms = self.reveal.duration_ms
        return (
            duration_ms is not None
            and self.reveal.elapsed_ms >= duration_ms
        )

    def draw(self, screen):
        self.renderer.panel(screen, self.popup_rect)
        self.prompt_box.draw(screen)

        for button in self.answer_buttons:
            button.draw(screen, reveal_elapsed_ms=self.elapsed_ms)

        if self.continue_button is not None:
            self.continue_button.draw(screen)
