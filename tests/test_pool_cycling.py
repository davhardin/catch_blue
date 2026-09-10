"""Pool cycling (M7 decision, 2026-09-09): a (topic, subtopic) pool with no
unused question left cycles *off the board* — its cells are relabeled to
pools that still have questions — instead of recycling in place, so a
1–3-question subtopic can't be memorized by landing on it repeatedly. Every
pool recycles together only once all of them are dry.

Bank-level rules live in questions.py (available_pools, restart_pools,
next_unused_question); the board rule lives in PlayState. The synthetic bank
below has two one-question pools and two five-question pools under one topic
so a pool can be drained in a single ask. Reveal duration is zero so answers
resolve on the click; a wrong answer keeps the player put (only Blue moves),
which keeps every click a plain 'move' and the game far from ending.
"""

import json
from collections import Counter
from random import Random

import pygame
import pytest

from board import get_distance
from game_setup import GameConfig, Settings
from questions import QuestionBank
from render import Renderer
from states.play import PlayState
from theme import FLAT

TOPIC = "cycling"
TINY = (("A", 1), ("B", 1))
BIG = (("C", 5), ("D", 5))
POOLS = tuple((TOPIC, name) for name, _ in TINY + BIG)


def write_bank(path, pools):
    questions = []
    for name, count in pools:
        for index in range(count):
            questions.append({
                "id": f"{name}-{index}",
                "subject": "science",
                "topic": TOPIC,
                "subtopic": name,
                "difficulty": 1,
                "type": "multiple_choice",
                "prompt": f"{name} question {index}?",
                "choices": ["Correct", "Wrong one", "Wrong two"],
                "answer_index": 0,
            })
    (path / "bank.json").write_text(json.dumps(questions), encoding="utf-8")
    return QuestionBank(path)


class GameStub:
    def __init__(self):
        self.renderer = Renderer(FLAT)
        self.state = None

    def change_state(self, state):
        self.state = state


@pytest.fixture
def fonts():
    pygame.font.init()
    yield
    pygame.font.quit()


def make_play(bank, seed=17):
    game = GameStub()
    state = PlayState(
        game, bank,
        GameConfig("catch_blue", "science", (TOPIC,), settings=Settings(move_limit=100)),
        Random(seed), reveal_duration_ms=0,
    )
    game.state = state
    return state


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def ask_wrong(state, cell=None):
    """Click a legal cell (the first, or a chosen one), answer wrong, return
    the (question, cell) that was served. Zero duration: resolved on return."""
    if cell is None:
        cell = sorted(state.moves)[0]
    assert cell in state.moves
    state.handle_events([click(state.view.cell_to_rect(cell).center)])
    question = state.pending[0]
    wrong = next(i for i in state.answer_order if i != question.answer_index)
    button = state.answer_buttons[state.answer_order.index(wrong)]
    state.handle_events([click(button.rect.center)])
    assert state.pending is None and state.game.state is state
    return question, cell


def drain(bank, pair, rng=None):
    rng = rng or Random(0)
    while bank.next_unused_question(*pair, rng) is not None:
        pass


# ---------------------------------------------------------------- bank -----


def test_available_pools_lists_only_pairs_with_unused_questions(tmp_path):
    bank = write_bank(tmp_path, TINY + BIG)
    assert bank.available_pools(POOLS) == sorted(POOLS)
    # Restricted to the pairs asked about, sorted, unknown pairs ignored.
    assert bank.available_pools([POOLS[2], POOLS[0], (TOPIC, "nope")]) == [POOLS[0], POOLS[2]]
    drain(bank, POOLS[0])
    assert bank.available_pools(POOLS) == sorted(POOLS[1:])
    bank.next_unused_question(*POOLS[2], Random(0))  # one of five used: still available
    assert POOLS[2] in bank.available_pools(POOLS)


def test_next_unused_question_returns_none_when_dry_and_never_recycles(tmp_path):
    bank = write_bank(tmp_path, TINY + BIG)
    rng = Random(3)
    served = {bank.next_unused_question(*POOLS[2], rng).id for _ in range(5)}
    assert len(served) == 5
    assert bank.next_unused_question(*POOLS[2], rng) is None
    assert bank.next_unused_question(*POOLS[2], rng) is None
    assert served <= bank.used_ids
    with pytest.raises(ValueError):
        bank.next_unused_question(TOPIC, "No Such Pool", rng)


def test_restart_pools_clears_only_the_named_pools_and_reshuffles(tmp_path):
    bank = write_bank(tmp_path, TINY + BIG)
    for pair in POOLS:
        drain(bank, pair)
    assert bank.available_pools(POOLS) == []
    bank.restart_pools(POOLS[:2])
    assert bank.available_pools(POOLS) == sorted(POOLS[:2])
    assert all(q.id in bank.used_ids for q in bank.questions if q.subtopic in ("C", "D"))
    # A restarted pool draws a fresh shuffled order rather than the stale one.
    bank.restart_pools(POOLS)
    orders = set()
    for seed in range(12):
        bank.restart_pools(POOLS)
        orders.add(tuple(bank.next_unused_question(*POOLS[2], Random(seed)).id for _ in range(5)))
    assert len(orders) > 1


# --------------------------------------------------------------- board -----


def test_a_dry_pool_leaves_the_board_and_its_cells_spread_evenly(tmp_path, fonts):
    bank = write_bank(tmp_path, TINY + BIG)
    state = make_play(bank)
    before = Counter(state.cell_topics.values())
    assert set(before) == set(POOLS)

    drain(bank, POOLS[0])  # "A" is used up behind the board's back
    ask_wrong(state)       # the click-time refresh runs before the question is drawn

    after = Counter(state.cell_topics.values())
    assert POOLS[0] not in after
    assert sum(after.values()) == len(state.cell_topics)
    # The ask may itself have drained the other one-question pool ("B"), in
    # which case it cycled off at the resolve — so judge balance over the
    # pools that still have questions, which is exactly what the board shows.
    live_pools = bank.available_pools(POOLS)
    assert set(after) == set(live_pools)
    live = [after[pair] for pair in live_pools]
    # Relabeled cells went to the least-populated live pools: balance holds.
    assert max(live) - min(live) <= 1


def test_the_question_served_always_matches_the_label_the_student_clicked(tmp_path, fonts):
    bank = write_bank(tmp_path, TINY + BIG)
    state = make_play(bank)
    seen = Counter()
    for _ in range(10):
        cell = sorted(state.moves)[0]
        label = state.cell_topics[cell]
        question, _ = ask_wrong(state, cell)
        assert (question.topic, question.subtopic) == label
        seen[label] += 1
        # Never a repeat while unused questions remain anywhere.
        assert len(bank.used_ids) == sum(seen.values())
    assert state.moves_remaining == 90
    assert get_distance(state.player.cell, state.blue.cell) <= 8


def test_tiny_pool_cycles_off_after_its_single_ask(tmp_path, fonts):
    # Find a seed whose opening legal moves include a one-question pool.
    for seed in range(40):
        bank = write_bank(tmp_path, TINY + BIG)
        state = make_play(bank, seed=seed)
        tiny = next((c for c in sorted(state.moves) if state.cell_topics[c] in POOLS[:2]), None)
        if tiny is not None:
            break
    assert tiny is not None, "no seed in 0..39 opened next to a tiny pool"
    pair = state.cell_topics[tiny]
    question, _ = ask_wrong(state, tiny)
    assert (question.topic, question.subtopic) == pair
    # Resolved: the refresh after the reveal has already moved every such cell.
    assert pair not in set(state.cell_topics.values())
    assert bank.available_pools(POOLS) == sorted(set(POOLS) - {pair})


def test_all_pools_dry_restarts_them_and_keeps_every_label(tmp_path, fonts):
    bank = write_bank(tmp_path, TINY)
    state = make_play(bank)
    for pair in POOLS[:2]:
        drain(bank, pair)
    assert bank.available_pools(POOLS[:2]) == []
    snapshot = dict(state.cell_topics)

    cell = sorted(state.moves)[0]
    question, _ = ask_wrong(state, cell)

    assert (question.topic, question.subtopic) == snapshot[cell]
    # The restart made every assignment fresh again — nothing was relabeled
    # on the restart itself; only the pool just drained (one question) cycled.
    drained = (question.topic, question.subtopic)
    for c, pair in snapshot.items():
        if pair != drained:
            assert state.cell_topics[c] == pair
    assert drained not in set(state.cell_topics.values())


def test_relabeling_is_seeded(tmp_path, fonts):
    boards = []
    for _ in range(2):
        bank = write_bank(tmp_path, TINY + BIG)
        state = make_play(bank, seed=5)
        drain(bank, POOLS[0])
        drain(bank, POOLS[1])
        ask_wrong(state)
        boards.append(dict(state.cell_topics))
    assert boards[0] == boards[1]


def test_a_new_game_on_a_living_bank_hides_dry_pools_before_the_first_click(tmp_path, fonts):
    """Used marks carry across replays (m5), so a replay must not open with a
    label whose pool is already empty."""
    bank = write_bank(tmp_path, TINY + BIG)
    drain(bank, POOLS[0])
    drain(bank, POOLS[1])
    state = make_play(bank)
    assert set(state.cell_topics.values()) == set(POOLS[2:])
    counts = Counter(state.cell_topics.values()).values()
    assert max(counts) - min(counts) <= 1
