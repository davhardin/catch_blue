from random import Random

import pygame

from board import Board, Cell
from board_view import BoardView
from cell_topics import CellTopics
from characters import Blue, Character, Player
from constants import (
    BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION, REVEAL_DURATION,
    SIDE_PANEL_LEFT, SIDE_PANEL_TOP, SIDE_PANEL_WIDTH,
    HUD_BUTTON_WIDTH, HUD_BUTTON_HEIGHT, HUD_PANEL_GAP,
)
from game_setup import (
    GameConfig,
    allowed_tiers_for,
    wanted_tier_for,
)
from match import Match
from modes import get_mode
from question_popup import AnswerReveal, QuestionPopup
from questions import Question, QuestionBank
from rules import Intent, Rules
from states.game_over import GameOverState
from states.pause import PauseState
from ui import (
    Button,
    ButtonAction,
    pointer_position,
    update_button_lifts,
)


class PlayState:
    def __init__(
        self,
        game,
        config: GameConfig,
        rng: Random,
        *,
        reveal_duration_ms: int = REVEAL_DURATION,
    ):
        if reveal_duration_ms < 0:
            raise ValueError("Reveal duration cannot be negative")

        self.game = game
        self.bank: QuestionBank = game.bank
        self.config = config
        self.rng = rng
        self.reveal_duration_ms = reveal_duration_ms
        settings = config.settings
        self.renderer = game.renderer

        self.mode = get_mode(config.mode)
        self.match = Match(settings, rng, rules=self.mode.make_rules())

        self.cell_topics = CellTopics(
            self.bank,
            self.config.selected_topics,
            self.rng,
            cells=self.board.cells(),
            policy_tiers=allowed_tiers_for(settings.tier_policy),
        )
        self.cell_topics.refresh(allowed_tiers=self.allowed_tiers)

        self.view = BoardView(
            self.board,
            BOARD_ORIGIN_X,
            BOARD_ORIGIN_Y,
            BOARD_REGION,
            theme=self.renderer.theme,
        )

        self.hovering: Cell | None = None
        self.selected: Cell | None = None
        self.pending: tuple[Question, Cell, Intent] | None = None
        self.popup: QuestionPopup | None = None
        self._discard_events_after_reveal = False
        self.pointer_pos: tuple[int, int] | None = None
        self.button_action = ButtonAction()

        self.pause_button = Button(
            pygame.Rect(
                SIDE_PANEL_LEFT + SIDE_PANEL_WIDTH - HUD_BUTTON_WIDTH,
                0,
                HUD_BUTTON_WIDTH,
                HUD_BUTTON_HEIGHT,
            ),
            "Pause",
            self.renderer,
            lift=self.renderer.theme.menu_lift,
        )
        self.pause_button.rect.bottom = SIDE_PANEL_TOP - HUD_PANEL_GAP

    @property
    def board(self) -> Board:
        return self.match.board

    @property
    def player(self) -> Player:
        return self.match.player

    @property
    def rules(self) -> Rules:
        return self.match.rules

    @property
    def npc(self) -> Character:
        return self.match.npc

    @property
    def blue(self) -> Blue:
        npc = self.npc
        if not isinstance(npc, Blue):
            raise AttributeError('This match does not have Blue')
        return npc

    @property
    def entities(self) -> list[Character]:
        return self.rules.entities(self.match)

    @property
    def moves_remaining(self) -> int:
        return self.match.moves_remaining

    @property
    def moves(self) -> set[Cell]:
        return self.match.moves

    @property
    def reveal(self) -> AnswerReveal | None:
        return self.popup.reveal if self.popup is not None else None

    @property
    def allowed_tiers(self) -> tuple[int, ...] | None:
        return allowed_tiers_for(
            self.config.settings.tier_policy,
            distance=self.rules.pressure_distance(self.match),
        )

    def _catchable_cell(self) -> Cell | None:
        cell = self.npc.cell
        if self.rules.click_intent(cell, self.match) == Intent.CATCH:
            return cell
        return None


    def _begin_reveal(self, canonical_index: int):
        assert self.pending is not None
        assert self.popup is not None

        self.popup.begin_reveal(
            canonical_index,
            self.reveal_duration_ms,
        )
        if self.reveal_duration_ms == 0:
            self._resolve_pending_answer()

    def update(self, dt_ms: int):
        update_button_lifts(
            (self.pause_button,),
            dt_ms,
            self.pointer_pos,
        )

        self.view.update(
            dt_ms,
            hovered=self.hovering,
            selected=self.selected,
            moves=self.moves,
            occupied={entity.cell for entity in self.entities},
            catchable=self._catchable_cell(),
        )

        popup = self.popup
        if popup is None:
            return

        if popup.update(dt_ms, self.pointer_pos):
            self._resolve_pending_answer()

            # These events were collected while the reveal was still active.
            self._discard_events_after_reveal = True
        elif popup.reveal is not None and popup.reveal.waits_for_click:
            self.button_action.update(dt_ms)

    def _resolve_pending_answer(self):
        assert self.pending is not None
        assert self.reveal is not None

        question, target, intent = self.pending
        is_correct = question.is_correct(self.reveal.canonical_index)
        result = self.match.resolve(is_correct, target, intent)

        self.pending = None
        self.selected = None
        self.popup = None

        if result is not None:
            self.game.change_state(
                GameOverState(
                    self.game,
                    self.config,
                    result,
                    self,
                )
            )
            return

        self.cell_topics.refresh(allowed_tiers=self.allowed_tiers)

    def handle_events(self, events):
        if self._discard_events_after_reveal:
            self._discard_events_after_reveal = False
            return

        if self.button_action.blocks_events():
            for event in events:
                self.pointer_pos = pointer_position(self.pointer_pos, event)
            return

        for event in events:
            self.pointer_pos = pointer_position(
                self.pointer_pos,
                event,
            )

            if event.type == pygame.WINDOWLEAVE:
                self.hovering = None
                if self.popup is not None:
                    self.popup.hover(None)
                continue

            left_click = (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            )
            pause_requested = (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ) or (
                left_click
                and self.pause_button.is_clicked(event.pos)
            )
            if pause_requested:
                self.game.change_state(PauseState(self))
                return

            popup = self.popup
            if popup is not None:
                if popup.reveal is not None:
                    if left_click and popup.wants_continue(event.pos):
                        assert popup.continue_button is not None
                        self.button_action.begin(
                            popup.continue_button,
                            self._resolve_pending_answer,
                        )
                        return
                    continue

                if event.type == pygame.MOUSEMOTION:
                    popup.hover(event.pos)
                elif left_click:
                    canonical_index = popup.answer_at(event.pos)
                    if canonical_index is not None:
                        self._begin_reveal(canonical_index)
                        return
                continue

            if event.type == pygame.MOUSEMOTION:
                self.hovering = self.view.pixel_to_cell(*event.pos)
                continue

            if not left_click:
                continue

            target = self.view.pixel_to_cell(*event.pos)
            if target is None:
                continue

            intent = self.rules.click_intent(target, self.match)
            if intent is None:
                continue

            self.cell_topics.refresh(allowed_tiers=self.allowed_tiers)
            question_cell = self.rules.question_cell(target, intent, self.match)
            topic, subtopic = self.cell_topics[question_cell]
            wanted_tier = wanted_tier_for(
                self.config.settings.tier_policy,
                self.rules.pressure_distance(self.match),
            )
            question = self.bank.next_unused_question(
                topic,
                subtopic,
                self.rng,
                wanted_tier=wanted_tier,
                allowed_tiers=self.allowed_tiers,
            )
            if question is None:
                raise RuntimeError(
                    f"No unused question after refreshing cell {question_cell}: "
                    f"{topic}/{subtopic}"
                )

            self.pending = (question, target, intent)
            self.selected = target
            self.hovering = None
            self.popup = QuestionPopup(
                question,
                self.renderer,
                question.display_order(self.rng),
            )

            # Later events in this batch must not answer a newly opened question.
            return

    def draw(self, screen: pygame.Surface, *, show_pause=True):
        self.renderer.fill(screen)
        self.view.draw(
            screen,
            self.hovering,
            self.entities,
            self.selected,
            self.moves,
            self.cell_topics.labels(),
            self.renderer,
            catchable=self._catchable_cell(),
        )

        counter = f"Moves remaining: {self.moves_remaining}"
        self.renderer.text(
            screen,
            counter,
            pygame.Rect(
                (SIDE_PANEL_LEFT, 50),
                self.renderer.measure(counter, 'counter'),
            ),
            'counter',
        )

        if show_pause:
            self.pause_button.draw(screen)

        if self.popup is not None:
            self.popup.draw(screen)
