"""Game setup: topic prettifying and the scrambled cell->pair assignment.

Everything here runs without a window -- game_setup.py and cell_topics.py
(where assign_cell_topics moved in the Phase 2 refactor) are pygame-free by
design, and the last test makes sure they stay that way, along with the
Phase 2 rule modules (match, rules, modes).

The assignment tests lean on seeded random.Random instances (milestones/m4.md
trap 5): same seed asserts exact equality, and the coverage test sweeps many
seeds to assert what any single scramble can't show -- that every pair CAN
appear. That sweep is the regression test for the M4 review bug where pairs
beyond the board size were deterministically excluded from every game.
"""

import subprocess
import sys
from collections import Counter
from random import Random

import pytest

from board import Board
from cell_topics import assign_cell_topics
from conftest import ROOT
from game_setup import (
    SUBJECT_TOPIC_ORDERS,
    SUBTOPIC_DISPLAY_NAMES,
    order_topics_for_subject,
    prettify_topic,
    subtopic_display_name,
)

# --- prettify_topic ---------------------------------------------------------


@pytest.mark.parametrize("raw, display", [
    ("anatomical_language", "Anatomical Language"),
    ("cells", "Cells"),
])
def test_prettify_topic(raw, display):
    assert prettify_topic(raw) == display


# --- subtopic_display_name -------------------------------------------------


MUSCLE_SUBTOPIC = "Neuromuscular Junction, EC Coupling, and Cross-Bridge Cycling"


def test_muscle_physiology_display_alias():
    # Membership, not equality: the map is content and may grow (m5 trap 7).
    assert SUBTOPIC_DISPLAY_NAMES[("muscular_system", MUSCLE_SUBTOPIC)] == "Muscle Physiology"
    assert subtopic_display_name("muscular_system", MUSCLE_SUBTOPIC) == (
        "Muscle Physiology"
    )


@pytest.mark.parametrize("topic, subtopic", [
    ("cells", "Overview"),
    ("unknown_topic", "Unmapped Section"),
    ("muscular_system", "  Unmapped section  "),
])
def test_subtopic_display_fallback_is_verbatim(topic, subtopic):
    assert subtopic_display_name(topic, subtopic) == subtopic


def test_subtopic_alias_is_scoped_to_its_topic():
    assert subtopic_display_name("cells", MUSCLE_SUBTOPIC) == MUSCLE_SUBTOPIC


def test_subtopic_alias_keys_exist_in_shipped_bank(bank):
    raw_pairs = {(q.topic, q.subtopic) for q in bank.questions}
    assert set(SUBTOPIC_DISPLAY_NAMES) <= raw_pairs


HEART_SUBTOPIC = "Cardiac Electrophysiology"


# 5 is the compact-names boundary; 7 and 9 sit on the same side of it.
@pytest.mark.parametrize("board_size", [5, 9])
def test_cardiac_conduction_alias_applies_at_every_board_size(board_size):
    """'Electrophysiology' alone overflows a 5x5 pixel tile, so the alias
    lives in the all-sizes map, not the compact one (Anson Vol. 2 import,
    2026-09-09)."""
    assert subtopic_display_name(
        "heart", HEART_SUBTOPIC, board_size=board_size
    ) == "Cardiac Conduction"


# --- order_topics_for_subject ----------------------------------------------


def test_every_shipped_topic_has_a_configured_position(bank):
    """An unlisted topic still loads but falls to the alphabetical tail of
    the menu; this guard turns that silent demotion into a failure."""
    shipped = set(bank.topics("anatomy_physiology"))
    assert shipped <= set(SUBJECT_TOPIC_ORDERS["anatomy_physiology"])


def test_anatomy_physiology_topics_follow_curriculum_order():
    configured = list(SUBJECT_TOPIC_ORDERS["anatomy_physiology"])
    scrambled = list(reversed(configured))
    assert order_topics_for_subject("anatomy_physiology", scrambled) == configured


def test_topic_order_omits_configured_topics_absent_from_bank():
    available = ["cells", "anatomical_language", "brain"]
    assert order_topics_for_subject("anatomy_physiology", available) == [
        "anatomical_language",
        "cells",
        "brain",
    ]


def test_unknown_topics_follow_configured_topics_alphabetically():
    available = ["future_z", "cells", "future_a"]
    assert order_topics_for_subject("anatomy_physiology", available) == [
        "cells",
        "future_a",
        "future_z",
    ]


def test_subject_without_configured_order_is_alphabetical():
    assert order_topics_for_subject(
        "organic_chemistry",
        ["alkenes", "acids", "alkanes"],
    ) == ["acids", "alkanes", "alkenes"]


# --- assign_cell_topics -----------------------------------------------------

CELLS = list(Board(5, 5).cells())


def pairs(n, topic="topic_a"):
    return [(topic, f"Section {i}") for i in range(n)]


def test_every_cell_is_assigned():
    assignment = assign_cell_topics(CELLS, pairs(3), Random(0))
    assert set(assignment) == set(CELLS)


def test_only_given_pairs_appear():
    given = pairs(3)
    assignment = assign_cell_topics(CELLS, given, Random(0))
    assert set(assignment.values()) <= set(given)


# Uneven split, exactly one each, and more pairs than cells (one pair is
# test_single_pair_covers_the_whole_board).
@pytest.mark.parametrize("n_pairs", [3, 25, 27])
def test_assignment_is_balanced(n_pairs):
    """Counting absent pairs as zero: no pair may appear twice while another
    never appears -- max and min counts differ by at most 1."""
    given = pairs(n_pairs)
    counts = Counter(assign_cell_topics(CELLS, given, Random(0)).values())
    per_pair = [counts[p] for p in given]
    assert max(per_pair) - min(per_pair) <= 1
    assert sum(per_pair) == len(CELLS)


def test_more_pairs_than_cells_every_pair_can_appear():
    """27 pairs, 25 cells: which two sit out must vary by scramble. The M4
    review found the tail of the sorted pair list sat out every game."""
    given = pairs(27)
    seen = set()
    for seed in range(60):
        seen |= set(assign_cell_topics(CELLS, given, Random(seed)).values())
    assert seen == set(given)


def test_same_seed_same_board():
    a = assign_cell_topics(CELLS, pairs(5), Random(7))
    b = assign_cell_topics(CELLS, pairs(5), Random(7))
    assert a == b


def test_different_seeds_differ():
    """Not guaranteed for one pair of seeds in principle, so assert across
    several -- identical boards from 5 different seeds means the rng is
    being ignored, not that we got unlucky."""
    boards = [assign_cell_topics(CELLS, pairs(5), Random(seed)) for seed in range(5)]
    assert any(b != boards[0] for b in boards[1:])


def test_single_pair_covers_the_whole_board():
    assignment = assign_cell_topics(CELLS, pairs(1), Random(0))
    assert set(assignment.values()) == {("topic_a", "Section 0")}


def test_no_pairs_raises():
    with pytest.raises(ValueError):
        assign_cell_topics(CELLS, [], Random(0))


def test_input_pair_list_order_is_not_mutated():
    """The helper shuffles internally; the caller's list must come back
    untouched, or the same list reused elsewhere reorders behind their back."""
    given = pairs(5)
    original = list(given)
    assign_cell_topics(CELLS, given, Random(0))
    assert given == original


# --- the pure/pixel line ----------------------------------------------------


@pytest.mark.parametrize("module", ["game_setup", "cell_topics", "match", "rules", "modes"])
def test_rule_modules_never_import_pygame(module):
    """milestones/m4.md: game_setup.py stays pygame-free so setup logic stays
    headless-testable. cell_topics.py (assign_cell_topics moved there in the
    Phase 2 refactor) and the Phase 2 rule modules -- match.py, rules.py,
    modes.py -- hold to the same line, so the strips and the maze can reuse
    them. Same guard as board, characters, and questions; a subprocess,
    because this file's own imports would pollute sys.modules."""
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}, sys; assert 'pygame' not in sys.modules"],
        capture_output=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, f"{module}.py has picked up a pygame dependency"
