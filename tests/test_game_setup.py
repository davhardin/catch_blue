"""Game setup: topic prettifying and the scrambled cell->pair assignment.

Everything here runs without a window -- game_setup.py is pygame-free by
design, and the last test makes sure it stays that way.

The assignment tests lean on seeded random.Random instances (milestones/m4.md
trap 5): same seed asserts exact equality, and the coverage test sweeps many
seeds to assert what any single scramble can't show -- that every pair CAN
appear. That sweep is the regression test for the M4 review bug where pairs
beyond the board size were deterministically excluded from every game.
"""

import subprocess
import sys
from collections import Counter
from pathlib import Path
from random import Random

import pytest

from board import Board
from game_setup import assign_cell_topics, prettify_topic

# --- prettify_topic ---------------------------------------------------------


@pytest.mark.parametrize("raw, display", [
    ("anatomical_language", "Anatomical Language"),
    ("chemical_foundations", "Chemical Foundations"),
    ("cells", "Cells"),
])
def test_prettify_topic(raw, display):
    assert prettify_topic(raw) == display


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


@pytest.mark.parametrize("n_pairs", [1, 3, 5, 25, 27])
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


def test_game_setup_module_never_imports_pygame():
    """milestones/m4.md: game_setup.py stays pygame-free so setup logic stays
    headless-testable. Same guard as board, characters, and questions."""
    result = subprocess.run(
        [sys.executable, "-c", "import game_setup, sys; assert 'pygame' not in sys.modules"],
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, "game_setup.py has picked up a pygame dependency"
