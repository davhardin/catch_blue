"""Pygame-free match state and shared turn accounting."""

from random import Random

from board import Cell
from characters import Player
from game_setup import Settings
from rules import Intent, Outcome, Rules


class Match:
    def __init__(self, settings: Settings, rng: Random, *, rules: Rules):
        self.rules = rules
        self.rng = rng
        self.moves_remaining = settings.move_limit
        self.board = rules.make_board(settings, rng)

        starts = rules.start_cells(self.board, rng)
        reason = rules.validate_setup(self.board, starts, settings)
        if reason is not None:
            raise ValueError(reason)

        player_cell, npc_cell = starts
        self.player = Player(player_cell)
        self.npc = rules.make_npc(npc_cell)

    @property
    def moves(self) -> set[Cell]:
        return self.player.legal_moves(
            self.board,
            self.rules.player_blocked(self),
        )

    def resolve(
        self,
        is_correct: bool,
        target: Cell,
        intent: Intent,
    ) -> Outcome | None:
        """Apply one answer for a caller-validated move or catch."""
        if is_correct:
            immediate = self.rules.on_correct(self, target, intent)
        else:
            immediate = self.rules.on_incorrect(self)

        self.moves_remaining -= 1

        # A successful catch wins even when it consumes the final move.
        if immediate is not None:
            return immediate

        return self.rules.outcome(self)
