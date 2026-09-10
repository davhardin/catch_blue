from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from random import Random

from board import Cell
from constants import MOVE_LIMIT

TopicPair = tuple[str, str]

SUBJECT_DISPLAY_NAMES = {
    "anatomy_physiology": "Anatomy & Physiology",
    "organic_chemistry": "Organic Chemistry",
}

SUBTOPIC_DISPLAY_NAMES: dict[TopicPair, str] = {
    ("muscular_system",
     "Neuromuscular Junction, EC Coupling, and Cross-Bridge Cycling"): "Muscle Physiology",
    ("heart", "Cardiac Electrophysiology"): "Cardiac Conduction",
}

COMPACT_SUBTOPIC_DISPLAY_NAMES: dict[TopicPair, str] = {
    ("anatomical_language", "Levels of Organization"):
        "Body Levels",
    ("chemical_foundations", "Atoms, Elements, and Compounds"):
        "Atoms & Matter",
    ("chemical_foundations", "Macromolecules"):
        "Biomolecules",
    ("cells", "DNA, Transcription and Translation"):
        "DNA, RNA & Protein",
    ("integumentary_system", "Aging: Integumentary System"):
        "Skin Aging",
    ("integumentary_system", "Integumentary Damage / Repair"):
        "Skin Damage & Repair",
    ("skeletal_system", "Bone Classification"):
        "Bone Types",
    ("skeletal_system", "Bone Development and Growth"):
        "Bone Growth",
    ("nervous_system", "Divisions of the Nervous System"):
        "Neural Divisions",
    ("nervous_system", "Synaptic Transmission"):
        "Synapses",
    ("brain", "Cerebrospinal Fluid"):
        "CSF",
    ("autonomic_nervous_system", "Autonomic Nervous System"):
        "ANS Overview",
    (
        "autonomic_nervous_system",
        "Divisions of the Autonomic Nervous System",
    ):
        "ANS Divisions",
    ("endocrine_system", "Secondary Endocrine Organs"):
        "Other Hormone Organs",
    ("blood_vessels", "Aging: Cardiovascular System"):
        "Vascular Aging",
    ("blood_vessels", "Fetal Cardiovascular System"):
        "Fetal Heart",
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
        "nervous_system",
        "spinal_cord",
        "brain",
        "sensory_pathways_and_somatic_nervous_system",
        "autonomic_nervous_system",
        "special_senses",
        "endocrine_system",
        "blood",
        "heart",
        "blood_vessels",
        "lymphatic_and_immune_system",
    ),
}


class TierPolicy(StrEnum):
    ALL = "all"
    TIERS_1_2 = "tiers_1_2"
    DISTANCE = "distance"


@dataclass(frozen=True)
class Settings:
    board_size: int = 5
    move_limit: int = MOVE_LIMIT
    tier_policy: TierPolicy = TierPolicy.TIERS_1_2

    def __post_init__(self):
        if type(self.board_size) is not int or self.board_size not in (5, 7, 9):
            raise ValueError("Board size must be 5, 7, or 9")

        if type(self.move_limit) is not int or self.move_limit <= 0:
            raise ValueError("Move limit must be a positive integer")

        object.__setattr__(self, "tier_policy", TierPolicy(self.tier_policy))


PRESETS: dict[str, Settings] = {
    "easy": Settings(
        board_size=5,
        move_limit=15,
        tier_policy=TierPolicy.TIERS_1_2,
    ),
    "medium": Settings(
        board_size=7,
        move_limit=20,
        tier_policy=TierPolicy.ALL,
    ),
    "hard": Settings(
        board_size=9,
        move_limit=25,
        tier_policy=TierPolicy.DISTANCE,
    ),
}

DEFAULT_PRESET = "easy"


def preset_for(settings: Settings) -> str:
    for name, preset in PRESETS.items():
        if settings == preset:
            return name
    return "custom"


@dataclass(frozen=True)
class GameConfig:
    mode: str
    subject: str
    selected_topics: tuple[str, ...]
    settings: Settings = field(
        default_factory=lambda: PRESETS[DEFAULT_PRESET],
    )


def prettify_topic(topic: str) -> str:
    return topic.replace("_", " ").title()


def subject_display_name(subject: str) -> str:
    return SUBJECT_DISPLAY_NAMES.get(subject, prettify_topic(subject))


def subtopic_display_name(
    topic: str,
    subtopic: str,
    *,
    board_size: int = 5,
) -> str:
    pair = (topic, subtopic)
    if board_size > 5:
        compact_name = COMPACT_SUBTOPIC_DISPLAY_NAMES.get(pair)
        if compact_name is not None:
            return compact_name
    return SUBTOPIC_DISPLAY_NAMES.get(pair, subtopic)


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
