from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from random import Random

from board import Cell

TopicPair = tuple[str, str]

SUBJECT_DISPLAY_NAMES = {
    "anatomy_physiology": "Anatomy & Physiology",
    "organic_chemistry": "Organic Chemistry",
}

SUBJECT_TOPIC_ORDERS = {
    "anatomy_physiology": (
        "anatomical_language",
        "chemical_foundations",
        "cells",
        "tissues",
        "integumentary_system",
        "skeletal_system",
        "muscular_system",
        "nervous_tissue",
        "spinal_cord",
        "brain",
        "sensory_pathways_and_somatic_nervous_system",
        "autonomic_nervous_system",
        "special_senses",
        "endocrine_system",
    ),
}


@dataclass(frozen=True)
class GameConfig:
    mode: str
    subject: str
    selected_topics: tuple[str, ...]


def prettify_topic(topic: str) -> str:
    return topic.replace("_", " ").title()


def subject_display_name(subject: str) -> str:
    return SUBJECT_DISPLAY_NAMES.get(subject, prettify_topic(subject))


def order_topics_for_subject(
    subject: str,
    topics: Iterable[str],
) -> list[str]:
    available_topics = set(topics)
    configured_order = SUBJECT_TOPIC_ORDERS.get(subject, ())
    configured_topics = [
        topic
        for topic in configured_order
        if topic in available_topics
    ]
    configured_topic_set = set(configured_order)
    additional_topics = sorted(available_topics - configured_topic_set)
    return configured_topics + additional_topics


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
