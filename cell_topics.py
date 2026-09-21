"""Pygame-free cell-topic assignment and exhausted-pool replacement."""

from collections import Counter
from collections.abc import Collection, Iterable, Sequence
from random import Random

from board import Cell
from game_setup import TopicPair
from questions import QuestionBank


def assign_cell_topics(
    cells: Iterable[Cell],
    topic_subtopics: Sequence[TopicPair],
    rng: Random,
) -> dict[Cell, TopicPair]:
    cells = list(cells)
    topic_subtopics = list(topic_subtopics)

    if not topic_subtopics:
        raise ValueError("Cannot assign cells without topic/subtopic pairs")

    rng.shuffle(topic_subtopics)
    assignments = [
        topic_subtopics[index % len(topic_subtopics)]
        for index in range(len(cells))
    ]
    rng.shuffle(assignments)

    return dict(zip(cells, assignments))


class CellTopics:
    def __init__(
        self,
        bank: QuestionBank,
        selected_topics: Iterable[str],
        rng: Random,
        *,
        cells: Iterable[Cell],
        policy_tiers: Collection[int] | None = None,
    ):
        self.bank = bank
        self.rng = rng
        self.topic_subtopics = tuple(
            (topic, subtopic)
            for topic in selected_topics
            for subtopic in bank.subtopics(
                topic,
                allowed_tiers=policy_tiers,
            )
        )
        if not self.topic_subtopics:
            raise ValueError(
                "Selected topics contain no questions for this tier policy"
            )

        self._labels: dict[Cell, TopicPair] = assign_cell_topics(
            cells,
            self.topic_subtopics,
            self.rng,
        )

    def __getitem__(self, cell: Cell) -> TopicPair:
        return self._labels[cell]

    def labels(self) -> dict[Cell, TopicPair]:
        """Return the live label map used by the board view."""
        return self._labels

    def refresh(
        self,
        *,
        allowed_tiers: Collection[int] | None,
    ) -> None:
        available = self.bank.available_pools(
            self.topic_subtopics,
            allowed_tiers=allowed_tiers,
        )

        if not available:
            self.bank.restart_pools(
                self.topic_subtopics,
                allowed_tiers=allowed_tiers,
            )
            available = self.bank.available_pools(
                self.topic_subtopics,
                allowed_tiers=allowed_tiers,
            )
            if not available:
                raise ValueError(
                    "Selected topics contain no questions for this tier policy"
                )

        # Distance changes can leave some labels ineligible even after a restart.
        available_set = set(available)
        exhausted_cells = [
            cell
            for cell, pair in sorted(self._labels.items())
            if pair not in available_set
        ]
        if not exhausted_cells:
            return

        counts = Counter(self._labels.values())

        for cell in exhausted_cells:
            minimum_count = min(counts[pair] for pair in available)
            replacements = [
                pair
                for pair in available
                if counts[pair] == minimum_count
            ]
            replacement = (
                replacements[0]
                if len(replacements) == 1
                else self.rng.choice(replacements)
            )

            current = self._labels[cell]
            counts[current] -= 1
            self._labels[cell] = replacement
            counts[replacement] += 1
