from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from random import Random

from board import Cell

TopicPair = tuple[str, str]


@dataclass(frozen=True)
class GameConfig:
    mode: str
    subject: str
    selected_topics: tuple[str, ...]


def prettify_topic(topic: str) -> str:
    return topic.replace("_", " ").title()


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
