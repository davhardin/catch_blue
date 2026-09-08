from dataclasses import dataclass
from random import Random

import pygame

from board import Board, Cell, get_distance, is_adjacent
from board_view import BoardView
from characters import Blue, Character, Player
from constants import (
    BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION, MOVE_LIMIT, REVEAL_DURATION,
    WRONG_REVEAL_EXTRA_MS, SIDE_PANEL_LEFT, SIDE_PANEL_TOP,
    SIDE_PANEL_WIDTH, SIDE_PANEL_PADDING,
)
from game_setup import GameConfig, assign_cell_topics
from questions import Question, QuestionBank
from states.game_over import GameOverState
from ui import Button, TextBox



def build_question_popup(
    question: Question,
    renderer,
    display_order: list[int],
):
    popup_left = SIDE_PANEL_LEFT
    popup_top = SIDE_PANEL_TOP
    popup_width = SIDE_PANEL_WIDTH
    padding = SIDE_PANEL_PADDING
    gap = 12

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
                44,
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


@dataclass
class AnswerReveal:
    canonical_index: int
    duration_ms: int
    elapsed_ms: int = 0


class PlayState:
    def __init__(
        self,
        game,
        bank: QuestionBank,
        config: GameConfig,
        rng: Random,
        *,
        reveal_duration_ms: int = REVEAL_DURATION,
    ):
        if reveal_duration_ms < 0:
            raise ValueError("Reveal duration cannot be negative")

        self.game = game
        self.bank = bank
        self.config = config
        self.rng = rng
        self.reveal_duration_ms = reveal_duration_ms
        self.renderer = game.renderer
        self.moves_remaining = MOVE_LIMIT

        self.board = Board(5, 5)
        topic_subtopics = [
            (topic, subtopic)
            for topic in self.config.selected_topics
            for subtopic in self.bank.subtopics(topic)
        ]
        self.cell_topics = assign_cell_topics(
            self.board.cells(),
            topic_subtopics,
            self.rng,
        )

        self.view = BoardView(
            self.board,
            BOARD_ORIGIN_X,
            BOARD_ORIGIN_Y,
            BOARD_REGION,
            theme=self.renderer.theme,
        )

        self.hovering: Cell | None = None
        self.selected: Cell | None = None
        self.pending: tuple[Question, Cell, str] | None = None
        self.reveal: AnswerReveal | None = None
        self._discard_events_after_reveal = False
        self.prompt_box: TextBox | None = None
        self.answer_buttons: list[Button] = []
        self.answer_order: list[int] = []
        self.hovered_answer: int | None = None
        self.popup_rect: pygame.Rect | None = None


        self.player = Player.at_start(self.board)
        self.blue = Blue.at_start(self.board)
        self.entities: list[Character] = [self.player, self.blue]
        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

    def _begin_reveal(self, canonical_index: int):
        assert self.pending is not None
        assert self.reveal is None

        question, _, _ = self.pending
        duration_ms = self.reveal_duration_ms
        if duration_ms > 0 and not question.is_correct(canonical_index):
            duration_ms += WRONG_REVEAL_EXTRA_MS
        self.reveal = AnswerReveal(canonical_index, duration_ms=duration_ms)
        self.hovered_answer = None

        for display_index, button in enumerate(self.answer_buttons):
            answer_index = self.answer_order[display_index]
            button.settle_for_reveal(
                selected=answer_index == canonical_index,
            )
            button.highlight = None

            if answer_index == question.answer_index:
                button.highlight = 'correct'
            elif answer_index == canonical_index:
                button.highlight = 'incorrect'

        if self.reveal.duration_ms == 0:
            self._resolve_pending_answer()

    def update(self, dt_ms: int):
        self.view.update(
            dt_ms,
            hovered=self.hovering,
            selected=self.selected,
            moves=self.moves,
            occupied={entity.cell for entity in self.entities},
        )

        if self.reveal is None:
            for index, button in enumerate(self.answer_buttons):
                button.update_lift(dt_ms, hovered=index == self.hovered_answer)
            return

        self.reveal.elapsed_ms += dt_ms
        if self.reveal.elapsed_ms < self.reveal.duration_ms:
            return

        self._resolve_pending_answer()

        # This frame's events were collected while the reveal was active.
        # Discard them rather than letting them click the newly exposed board.
        self._discard_events_after_reveal = True

    def _resolve_pending_answer(self):
        assert self.pending is not None
        assert self.reveal is not None

        question, target, intent = self.pending
        is_correct = question.is_correct(self.reveal.canonical_index)
        caught = is_correct and intent == "catch"

        if is_correct:
            if not caught:
                self.player.move_to(target)
        else:
            flee_target = self.blue.flee_step(
                self.board,
                self.player.cell,
                self.rng,
            )
            self.blue.move_to(flee_target)

        self.moves_remaining -= 1
        self.pending = None
        self.reveal = None
        self.selected = None
        self.popup_rect = None

        self.prompt_box = None
        self.answer_buttons = []
        self.answer_order = []
        self.hovered_answer = None

        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

        distance = get_distance(self.player.cell, self.blue.cell)
        cannot_reach_blue = self.moves_remaining < distance
        out_of_moves = self.moves_remaining <= 0

        if caught or out_of_moves or cannot_reach_blue:
            result = "win" if caught else "lose"
            self.game.change_state(
                GameOverState(
                    self.game,
                    self.bank,
                    self.config,
                    result,
                    self,
                )
            )

    def handle_events(self, events):
        if self._discard_events_after_reveal:
            self._discard_events_after_reveal = False
            return

        if self.reveal is not None:
            return

        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

        for event in events:
            if self.pending is not None:
                if event.type == pygame.MOUSEMOTION:
                    self.hovered_answer = next(
                        (index for index, button in enumerate(self.answer_buttons)
                         if button.is_clicked(event.pos)),
                        None,
                    )
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for display_index, button in enumerate(self.answer_buttons):
                        if not button.is_clicked(event.pos):
                            continue

                        canonical_index = self.answer_order[display_index]
                        self._begin_reveal(canonical_index)
                        return

            # Board mode: board clicks and hover are active.
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    cell = self.view.pixel_to_cell(*event.pos)

                    target = None
                    intent = None

                    # Check catch before legal movement because Blue's occupied
                    # square is intentionally excluded from moves.
                    if (
                        cell == self.blue.cell
                        and is_adjacent(self.player.cell, self.blue.cell)
                    ):
                        target = cell
                        intent = "catch"

                    elif cell in self.moves:
                        target = cell
                        intent = "move"

                    if target is not None and intent is not None:
                        topic, subtopic = self.cell_topics[target]
                        question = self.bank.next_question(topic, subtopic, self.rng)

                        self.pending = (question, target, intent)
                        self.selected = target
                        self.hovering = None
                        self.hovered_answer = None
                        self.answer_order = question.display_order(self.rng)

                        (
                            self.popup_rect,
                            self.prompt_box,
                            self.answer_buttons,

                        ) = build_question_popup(
                            question,
                            self.renderer,
                            self.answer_order,
                        )

                elif event.type == pygame.MOUSEMOTION:
                    self.hovering = self.view.pixel_to_cell(*event.pos)

        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

    def draw(self, screen: pygame.Surface):
        self.renderer.fill(screen)
        self.view.draw(
            screen,
            self.hovering,
            self.entities,
            self.selected,
            self.moves,
            self.cell_topics,
            self.renderer,
            catchable=(
                self.blue.cell
                if is_adjacent(self.player.cell, self.blue.cell)
                else None
            ),
        )

        counter = f"Moves remaining: {self.moves_remaining}"
        self.renderer.text(
            screen, counter, pygame.Rect((SIDE_PANEL_LEFT, 50), self.renderer.measure(counter, 'counter')),
            'counter',
        )

        if self.pending is not None:
            assert self.popup_rect is not None
            assert self.prompt_box is not None

            self.renderer.panel(screen, self.popup_rect)


            self.prompt_box.draw(screen)

            elapsed_ms = self.reveal.elapsed_ms if self.reveal is not None else 0
            for button in self.answer_buttons:
                button.draw(screen, reveal_elapsed_ms=elapsed_ms)
