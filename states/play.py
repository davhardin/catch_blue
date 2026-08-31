from random import Random

import pygame

from board import Board, Cell, is_adjacent
from board_view import BoardView
from characters import Blue, Character, Player
from constants import (
    BG_COLOR,
    BOARD_ORIGIN_X,
    BOARD_ORIGIN_Y,
    BOARD_REGION,
    CELL_COLOR,
    LABEL_FONT_SIZE,
    LINE_COLOR,
    MENU_TEXT_COLOR,
    MOVE_COLOR,
    MOVE_LIMIT,
)
from game_setup import GameConfig, assign_cell_topics
from questions import Question, QuestionBank
from states.game_over import GameOverState
from ui import Button, TextBox


def build_question_popup(question: Question, font):
    popup_left = 720
    popup_top = 80
    popup_width = 520
    padding = 20
    gap = 12

    content_left = popup_left + padding
    content_width = popup_width - 2 * padding

    prompt_box = TextBox(
        question.prompt,
        font,
        (245, 245, 245),
        content_left,
        popup_top + padding,
        content_width,
    )

    answer_buttons = []
    next_button_top = prompt_box.y + prompt_box.height + gap

    for choice in question.choices:
        button = Button(
            pygame.Rect(
                content_left,
                next_button_top,
                content_width,
                44,
            ),
            choice,
            font,
            (255, 255, 255),
            MOVE_COLOR,
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


class PlayState:
    def __init__(
        self,
        game,
        bank: QuestionBank,
        config: GameConfig,
        rng: Random,
    ):
        self.game = game
        self.bank = bank
        self.config = config
        self.font = pygame.font.Font(None, 28)
        self.label_font = pygame.font.Font(None, LABEL_FONT_SIZE)
        self.counter_font = pygame.font.Font(None, 36)
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
            rng,
        )

        self.view = BoardView(
            self.board,
            BOARD_ORIGIN_X,
            BOARD_ORIGIN_Y,
            BOARD_REGION,
        )

        self.hovering: Cell | None = None
        self.selected: Cell | None = None
        self.pending: tuple[Question, Cell, str] | None = None
        self.prompt_box: TextBox | None = None
        self.answer_buttons: list[Button] = []
        self.popup_rect: pygame.Rect | None = None

        self.player = Player.at_start(self.board)
        self.blue = Blue.at_start(self.board)
        self.entities: list[Character] = [self.player, self.blue]
        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

    def handle_events(self, events):
        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

        for event in events:
            if self.pending is not None:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    question, target, intent = self.pending

                    for choice_index, button in enumerate(self.answer_buttons):
                        if not button.is_clicked(event.pos):
                            continue

                        is_correct = question.is_correct(choice_index)
                        caught = is_correct and intent == "catch"

                        if is_correct:
                            if not caught:
                                self.player.move_to(target)
                        else:
                            flee_target = self.blue.flee_step(
                                self.board,
                                self.player.cell,
                            )
                            self.blue.move_to(flee_target)

                        self.moves_remaining -= 1
                        self.pending = None
                        self.selected = None
                        self.popup_rect = None
                        self.prompt_box = None
                        self.answer_buttons = []

                        if caught or self.moves_remaining == 0:
                            self.moves = self.player.legal_moves(
                                self.board,
                                {self.blue.cell},
                            )
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
                            return

                        break

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
                        question = self.bank.next_question(topic, subtopic)

                        self.pending = (question, target, intent)
                        self.selected = target
                        self.hovering = None

                        (
                            self.popup_rect,
                            self.prompt_box,
                            self.answer_buttons,
                        ) = build_question_popup(question, self.font)

                elif event.type == pygame.MOUSEMOTION:
                    self.hovering = self.view.pixel_to_cell(*event.pos)

        self.moves = self.player.legal_moves(self.board, {self.blue.cell})

    def draw(self, screen: pygame.Surface):
        screen.fill(BG_COLOR)
        self.view.draw(
            screen,
            self.hovering,
            self.entities,
            self.selected,
            self.moves,
            self.cell_topics,
            self.label_font,
        )

        counter = self.counter_font.render(
            f"Moves remaining: {self.moves_remaining}",
            True,
            MENU_TEXT_COLOR,
        )
        screen.blit(counter, (720, 50))

        if self.pending is not None:
            assert self.popup_rect is not None
            assert self.prompt_box is not None

            pygame.draw.rect(screen, CELL_COLOR, self.popup_rect)
            pygame.draw.rect(screen, LINE_COLOR, self.popup_rect, width=2)

            self.prompt_box.draw(screen)

            for button in self.answer_buttons:
                button.draw(screen)
