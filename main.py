from pathlib import Path

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
    LINE_COLOR,
    MOVE_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from questions import Question, QuestionBank
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


pygame.init()
font = pygame.font.Font(None, 28)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
pygame.display.set_caption("Catch Blue: The Science Learning Game")

clock = pygame.time.Clock()
fps = 60

board = Board(5,5)
questions_path = Path(__file__).parent / "data" / "questions"
bank = QuestionBank(questions_path)

if not bank.topics:
    raise ValueError("The question bank contains no topics")

cell_topics = {
    cell: bank.topics[index % len(bank.topics)]
    for index, cell in enumerate(board.cells())
}

view = BoardView(board, BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION)

hovering: Cell | None = None
selected: Cell | None = None
pending: tuple[Question, Cell, str] | None = None
prompt_box: TextBox | None = None
answer_buttons: list[Button] = []
popup_rect: pygame.Rect | None = None
player = Player.at_start(board)
blue = Blue.at_start(board)
entities: list[Character] = [player, blue]

# Main loop

running = True


while running:

    moves = player.legal_moves(board, {blue.cell})

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif pending is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                question, target, intent = pending

                for choice_index, button in enumerate(answer_buttons):
                    if not button.is_clicked(event.pos):
                        continue

                    if question.is_correct(choice_index):
                        if intent == "catch":
                            print("caught!")
                        else:
                            player.move_to(target)
                    else:
                        flee_target = blue.flee_step(board, player.cell)
                        blue.move_to(flee_target)

                    pending = None
                    selected = None
                    popup_rect = None
                    prompt_box = None
                    answer_buttons = []
                    break

        # Board mode: board clicks and hover are active.
        else:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cell = view.pixel_to_cell(*event.pos)

                target = None
                intent = None

                # Check catch before legal movement because Blue's occupied
                # square is intentionally excluded from moves.
                if (
                    cell == blue.cell
                    and is_adjacent(player.cell, blue.cell)
                ):
                    target = cell
                    intent = "catch"

                elif cell in moves:
                    target = cell
                    intent = "move"

                if target is not None and intent is not None:
                    topic = cell_topics[target]
                    question = bank.next_question(topic)

                    pending = (question, target, intent)
                    selected = target
                    hovering = None

                    popup_rect, prompt_box, answer_buttons = (
                        build_question_popup(question, font)
                    )

            elif event.type == pygame.MOUSEMOTION:
                hovering = view.pixel_to_cell(*event.pos)

    moves = player.legal_moves(board, {blue.cell})

    screen.fill(BG_COLOR)
    view.draw(screen, hovering, entities, selected, moves)

    if pending is not None:
        assert popup_rect is not None
        assert prompt_box is not None

        pygame.draw.rect(screen, CELL_COLOR, popup_rect)
        pygame.draw.rect(screen, LINE_COLOR, popup_rect, width=2)

        prompt_box.draw(screen)

        for button in answer_buttons:
            button.draw(screen)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
