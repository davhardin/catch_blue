"""Pygame-free mode policies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import StrEnum
from random import Random
from typing import TYPE_CHECKING, Protocol

from board import Board, Cell
from characters import Blue, Character
from game_setup import Settings, allowed_tiers_for
from questions import QuestionBank

if TYPE_CHECKING:
    from match import Match


class Intent(StrEnum):
    MOVE = 'move'
    CATCH = 'catch'


class Outcome(StrEnum):
    WIN = 'win'
    LOSE = 'lose'


class Rules(Protocol):
    """Mode policy for a pygame-free Match.

    Query methods must not mutate the match or consume randomness.
    Answer handlers run before the shared move deduction and must not
    deduct moves themselves. outcome runs after movement and deduction,
    only when the handler did not return an immediate result.
    """

    result_messages: Mapping[Outcome, str]

    def make_board(self, settings: Settings, rng: Random) -> Board: ...

    def start_cells(
        self, board: Board, rng: Random,
    ) -> tuple[Cell, Cell]: ...

    def validate_setup(
        self,
        board: Board,
        starts: tuple[Cell, Cell],
        settings: Settings,
    ) -> str | None: ...

    def make_npc(self, cell: Cell) -> Character: ...

    def entities(self, match: Match) -> list[Character]: ...

    def player_blocked(self, match: Match) -> set[Cell]: ...

    def click_intent(self, cell: Cell, match: Match) -> Intent | None: ...

    def question_cell(
        self, target: Cell, intent: Intent, match: Match,
    ) -> Cell: ...

    def pressure_distance(self, match: Match) -> int: ...

    def on_correct(
        self, match: Match, target: Cell, intent: Intent,
    ) -> Outcome | None: ...

    def on_incorrect(self, match: Match) -> Outcome | None: ...

    def outcome(self, match: Match) -> Outcome | None: ...

    def menu_eligible(
        self,
        settings: Settings,
        bank: QuestionBank,
        topics: Iterable[str],
    ) -> bool: ...


def _catch_blue_start_cells(board: Board) -> tuple[Cell, Cell]:
    return Cell(0, board.rows - 1), Cell(board.cols // 2, board.rows // 2)


class CatchBlueRules:
    result_messages: Mapping[Outcome, str] = {
        Outcome.WIN: 'You caught Blue!',
        Outcome.LOSE: 'Blue got away!',
    }

    def make_board(self, settings: Settings, rng: Random) -> Board:
        return Board(settings.board_size, settings.board_size)

    def start_cells(
        self, board: Board, rng: Random,
    ) -> tuple[Cell, Cell]:
        return _catch_blue_start_cells(board)

    def validate_setup(
        self,
        board: Board,
        starts: tuple[Cell, Cell],
        settings: Settings,
    ) -> str | None:
        return None

    def make_npc(self, cell: Cell) -> Blue:
        return Blue(cell)

    def entities(self, match: Match) -> list[Character]:
        return [match.player, match.npc]

    def player_blocked(self, match: Match) -> set[Cell]:
        return {match.npc.cell}

    def click_intent(self, cell: Cell, match: Match) -> Intent | None:
        if (
            cell == match.npc.cell
            and cell in match.board.neighbors(match.player.cell)
        ):
            return Intent.CATCH
        if cell in match.moves:
            return Intent.MOVE
        return None

    def question_cell(
        self, target: Cell, intent: Intent, match: Match,
    ) -> Cell:
        return target

    def pressure_distance(self, match: Match) -> int:
        return match.board.distance(match.player.cell, match.npc.cell)

    def on_correct(
        self, match: Match, target: Cell, intent: Intent,
    ) -> Outcome | None:
        if intent == Intent.CATCH:
            return Outcome.WIN
        match.player.move_to(target)
        return None

    def on_incorrect(self, match: Match) -> Outcome | None:
        npc = match.npc
        assert isinstance(npc, Blue)
        npc.move_to(
            npc.flee_step(match.board, match.player.cell, match.rng),
        )
        return None

    def outcome(self, match: Match) -> Outcome | None:
        distance = self.pressure_distance(match)
        if match.moves_remaining <= 0 or match.moves_remaining < distance:
            return Outcome.LOSE
        return None

    def menu_eligible(
        self,
        settings: Settings,
        bank: QuestionBank,
        topics: Iterable[str],
    ) -> bool:
        board = Board(settings.board_size, settings.board_size)
        player_cell, npc_cell = _catch_blue_start_cells(board)
        tiers = allowed_tiers_for(
            settings.tier_policy,
            distance=board.distance(player_cell, npc_cell),
        )
        return any(
            bank.subtopics(topic, allowed_tiers=tiers)
            for topic in topics
        )
