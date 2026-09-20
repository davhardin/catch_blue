"""M7.e loader guard and M7.f tier policy (milestones/m7.md).

Bank level: a wanted tier is served while unused questions exist at that
tier, the fallback order is 2 → 3 → 1 and 3 → 2 → 1 (1 → 2 → 3), every
question in a pool is served once before any repeat even under a tier
preference, and an allowed-tier filter never serves outside it. With no
policy the draw sequence on the real bank is byte-for-byte the pre-M7.f
algorithm (same seed, same order).

Game level: easy is a policy-wide tiers-1+2 filter; distance wants 3 at
0–1 and 2 at 2, and beyond 2 wants nothing but filters to tiers 1+2 so the
3s are not spent far from Blue (David, 2026-09-19). PlayState asks with the
player-to-Blue distance at ask time; the Topics screen checks the starting
distance and refuses to start a selection with nothing at those tiers.
"""

import json
from pathlib import Path
from random import Random
from types import SimpleNamespace

import pygame
import pytest

from board import get_distance
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from game_setup import (
    DEFAULT_PRESET, PRESETS, GameConfig, Settings, TierPolicy,
    allowed_tiers_for, wanted_tier_for,
)
from questions import TIER_FALLBACKS, QuestionBank
from render import Renderer
from states.menus import TopicsState
from states.play import PlayState
from theme import FLAT

SUBJECT = "science"
TOPIC = "tiers"
POOL = (TOPIC, "Mixed")
REAL_BANK = Path(__file__).resolve().parents[1] / "data" / "questions"


def question(qid, difficulty, topic=TOPIC, subtopic="Mixed"):
    return {
        "id": qid,
        "subject": SUBJECT,
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "type": "multiple_choice",
        "prompt": f"{qid}?",
        "choices": ["Correct", "Wrong one", "Wrong two"],
        "answer_index": 0,
    }


def write_bank(path, questions):
    (path / "bank.json").write_text(json.dumps(questions), encoding="utf-8")
    return QuestionBank(path)


def mixed_pool(per_tier):
    """One pool with `per_tier` questions at each of tiers 1, 2, 3."""
    return [
        question(f"t{tier}-{index}", tier)
        for tier in (1, 2, 3)
        for index in range(per_tier)
    ]


@pytest.fixture
def fonts():
    pygame.font.init()
    yield
    pygame.font.quit()


# --- loader guard (M7.e) ----------------------------------------------------


@pytest.mark.parametrize("bad", [0, 4, -1, "2", 2.0, True, None])
def test_loader_rejects_difficulty_outside_1_to_3(tmp_path, bad):
    with pytest.raises(ValueError) as excinfo:
        write_bank(tmp_path, [question("bad-one", bad)])
    assert "difficulty" in str(excinfo.value).lower()
    assert "bad-one" in str(excinfo.value)


def test_loader_requires_difficulty(tmp_path):
    broken = question("no-tier", 1)
    del broken["difficulty"]
    with pytest.raises(ValueError, match="difficulty"):
        write_bank(tmp_path, [broken])


@pytest.mark.parametrize("tier", [1, 2, 3])
def test_loader_accepts_each_tier(tmp_path, tier):
    bank = write_bank(tmp_path, [question("ok", tier)])
    assert bank.questions[0].difficulty == tier


def test_real_bank_is_fully_graded():
    bank = QuestionBank(REAL_BANK)
    tiers = {q.difficulty for q in bank.questions}
    assert tiers == {1, 2, 3}
    for topic in bank.topics("anatomy_physiology"):
        present = {q.difficulty for q in bank.questions if q.topic == topic}
        assert {1, 2} <= present, f"{topic} has no tier-1 or tier-2 question"


# --- the policy tables (game_setup) ------------------------------------------


def test_allowed_tiers_policy_wide_restrict_only_easy():
    assert allowed_tiers_for(TierPolicy.TIERS_1_2) == (1, 2)
    assert allowed_tiers_for(TierPolicy.ALL) is None
    assert allowed_tiers_for(TierPolicy.DISTANCE) is None


@pytest.mark.parametrize("distance,expected", [
    (0, None), (1, None), (2, None), (3, (1, 2)), (4, (1, 2)), (8, (1, 2)),
])
def test_distance_policy_excludes_tier_3_far_from_blue(distance, expected):
    assert allowed_tiers_for(TierPolicy.DISTANCE, distance=distance) == expected


@pytest.mark.parametrize("distance", [0, 2, 3, 8])
def test_distance_never_changes_the_other_policies(distance):
    assert allowed_tiers_for(TierPolicy.TIERS_1_2, distance=distance) == (1, 2)
    assert allowed_tiers_for(TierPolicy.ALL, distance=distance) is None


@pytest.mark.parametrize("distance,expected", [
    (0, 3), (1, 3), (2, 2), (3, None), (4, None), (8, None),
])
def test_distance_curve_prefers_hard_questions_near_blue(distance, expected):
    assert wanted_tier_for(TierPolicy.DISTANCE, distance) == expected


@pytest.mark.parametrize("policy", [TierPolicy.ALL, TierPolicy.TIERS_1_2])
@pytest.mark.parametrize("distance", [0, 1, 2, 5])
def test_only_the_distance_policy_wants_a_tier(policy, distance):
    assert wanted_tier_for(policy, distance) is None


def test_presets_carry_the_shipped_policies():
    assert PRESETS["easy"].tier_policy is TierPolicy.TIERS_1_2
    assert PRESETS["medium"].tier_policy is TierPolicy.DISTANCE
    assert PRESETS["hard"].tier_policy is TierPolicy.DISTANCE
    assert PRESETS[DEFAULT_PRESET] is PRESETS["easy"]


# --- bank draws under a wanted tier ------------------------------------------


def test_fallback_table_is_nearest_tier_first():
    assert TIER_FALLBACKS == {1: (1, 2, 3), 2: (2, 3, 1), 3: (3, 2, 1)}


@pytest.mark.parametrize("wanted", [1, 2, 3])
def test_wanted_tier_is_served_while_any_remains(tmp_path, wanted):
    bank = write_bank(tmp_path, mixed_pool(3))
    rng = Random(3)
    served = [bank.next_unused_question(*POOL, rng, wanted_tier=wanted) for _ in range(3)]
    assert [q.difficulty for q in served] == [wanted] * 3
    assert len({q.id for q in served}) == 3


@pytest.mark.parametrize("wanted,order", [(2, (2, 3, 1)), (3, (3, 2, 1)), (1, (1, 2, 3))])
def test_fallback_walks_the_nearest_tier_then_the_last(tmp_path, wanted, order):
    bank = write_bank(tmp_path, mixed_pool(2))
    rng = Random(5)
    tiers = [bank.next_unused_question(*POOL, rng, wanted_tier=wanted).difficulty for _ in range(6)]
    assert tiers == [order[0]] * 2 + [order[1]] * 2 + [order[2]] * 2
    assert bank.next_unused_question(*POOL, rng, wanted_tier=wanted) is None


def test_fallback_respects_the_shuffled_pool_order_within_a_tier(tmp_path):
    bank = write_bank(tmp_path, mixed_pool(4))
    rng = Random(11)
    first = bank.next_unused_question(*POOL, rng, wanted_tier=2)
    shuffled = bank._pool_orders[POOL]
    assert first is next(q for q in shuffled if q.difficulty == 2)
    # A different seed, a different order; the same rule picks the first tier-2.
    other = write_bank(tmp_path, mixed_pool(4))
    other_rng = Random(12)
    got = other.next_unused_question(*POOL, other_rng, wanted_tier=2)
    assert got is next(q for q in other._pool_orders[POOL] if q.difficulty == 2)


def test_every_question_is_served_once_before_any_repeat_under_a_tier(tmp_path):
    bank = write_bank(tmp_path, mixed_pool(3))
    rng = Random(9)
    first_lap = [bank.next_question(*POOL, rng, wanted_tier=3).id for _ in range(9)]
    assert sorted(first_lap) == sorted(q["id"] for q in mixed_pool(3))
    second_lap = [bank.next_question(*POOL, rng, wanted_tier=3).id for _ in range(9)]
    assert sorted(second_lap) == sorted(first_lap)
    # The recycle still prefers the wanted tier: the fresh lap opens on a 3.
    assert second_lap[0].startswith("t3-")


def test_one_used_set_and_one_pool_order_serve_both_tier_and_plain_draws(tmp_path):
    bank = write_bank(tmp_path, mixed_pool(2))
    rng = Random(2)
    a = bank.next_unused_question(*POOL, rng, wanted_tier=3)
    b = bank.next_unused_question(*POOL, rng)
    c = bank.next_unused_question(*POOL, rng, wanted_tier=3)
    assert a.difficulty == 3 and c.difficulty == 3
    assert len({a.id, b.id, c.id}) == 3
    assert bank.used_ids == {a.id, b.id, c.id}
    assert list(bank._pool_orders) == [POOL]


@pytest.mark.parametrize("bad", [0, 4, "2", 2.0, True])
def test_wanted_tier_must_be_a_real_tier(tmp_path, bad):
    bank = write_bank(tmp_path, mixed_pool(1))
    with pytest.raises(ValueError):
        bank.next_unused_question(*POOL, Random(0), wanted_tier=bad)


# --- bank draws under an allowed set -----------------------------------------


def test_allowed_tiers_never_serve_outside_and_dry_out_honestly(tmp_path):
    bank = write_bank(tmp_path, mixed_pool(2))
    rng = Random(4)
    served = [bank.next_unused_question(*POOL, rng, allowed_tiers=(1, 2)) for _ in range(4)]
    assert sorted(q.id for q in served) == ["t1-0", "t1-1", "t2-0", "t2-1"]
    assert bank.next_unused_question(*POOL, rng, allowed_tiers=(1, 2)) is None
    # Tier-3 questions are still unused for a policy that allows them.
    assert bank.next_unused_question(*POOL, rng).difficulty == 3


def test_next_question_recycles_only_the_allowed_tiers(tmp_path):
    bank = write_bank(tmp_path, mixed_pool(1))
    rng = Random(6)
    laps = [bank.next_question(*POOL, rng, allowed_tiers=(1, 2)).difficulty for _ in range(6)]
    assert set(laps) == {1, 2}
    assert "t3-0" not in bank.used_ids


def test_next_question_raises_when_nothing_is_allowed(tmp_path):
    bank = write_bank(tmp_path, [question("only-3", 3)])
    with pytest.raises(ValueError, match="allowed tiers"):
        bank.next_question(*POOL, Random(0), allowed_tiers=(1, 2))


def test_subtopics_and_pools_and_restart_honor_the_allowed_set(tmp_path):
    bank = write_bank(tmp_path, [
        question("a-1", 1, subtopic="Alpha"),
        question("b-3", 3, subtopic="Beta"),
        question("c-2", 2, subtopic="Gamma"),
        question("c-3", 3, subtopic="Gamma"),
    ])
    pools = [(TOPIC, "Alpha"), (TOPIC, "Beta"), (TOPIC, "Gamma")]
    assert bank.subtopics(TOPIC) == ["Alpha", "Beta", "Gamma"]
    assert bank.subtopics(TOPIC, allowed_tiers=(1, 2)) == ["Alpha", "Gamma"]
    assert bank.available_pools(pools, allowed_tiers=(1, 2)) == [(TOPIC, "Alpha"), (TOPIC, "Gamma")]

    rng = Random(1)
    bank.next_unused_question(TOPIC, "Gamma", rng, allowed_tiers=(1, 2))
    assert bank.available_pools(pools, allowed_tiers=(1, 2)) == [(TOPIC, "Alpha")]
    assert (TOPIC, "Gamma") in bank.available_pools(pools)  # c-3 is still unused

    bank.next_unused_question(TOPIC, "Gamma", rng)  # uses c-3
    bank.restart_pools(pools, allowed_tiers=(1, 2))
    assert "c-2" not in bank.used_ids
    assert "c-3" in bank.used_ids


# --- "all" is byte-for-byte the pre-M7.f draw on the real bank -------------


def reference_draw_sequence(bank, pair, seed):
    """The pre-M7.f algorithm: shuffle the pool in load order, walk it once."""
    candidates = [q for q in bank.questions if (q.topic, q.subtopic) == pair]
    Random(seed).shuffle(candidates)
    return [q.id for q in candidates]


@pytest.mark.parametrize("seed", [0, 17, 2026])
def test_no_policy_matches_the_pre_m7f_sequence_on_the_real_bank(seed):
    bank = QuestionBank(REAL_BANK)
    pair = ("cells", bank.subtopics("cells")[0])
    expected = reference_draw_sequence(bank, pair, seed)
    rng = Random(seed)
    got = [bank.next_unused_question(*pair, rng).id for _ in expected]
    assert got == expected
    assert bank.next_unused_question(*pair, rng) is None


# --- PlayState asks with the policy -----------------------------------------


class GameStub:
    def __init__(self):
        self.renderer = Renderer(FLAT)
        self.state = None

    def change_state(self, state):
        self.state = state


def make_play(bank, settings, seed=17):
    game = GameStub()
    state = PlayState(
        game, bank,
        GameConfig("catch_blue", SUBJECT, (TOPIC,), settings=settings),
        Random(seed), reveal_duration_ms=0,
    )
    game.state = state
    return state


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def place_player_at_distance(state, distance):
    blue = state.blue.cell
    cell = next(
        c for c in state.board.cells()
        if c != blue and get_distance(c, blue) == distance
    )
    state.player.move_to(cell)
    assert get_distance(state.player.cell, state.blue.cell) == distance


def open_question(state):
    moves = state.player.legal_moves(state.board, {state.blue.cell})
    target = sorted(moves)[0]
    distance = get_distance(state.player.cell, state.blue.cell)
    state.handle_events([click(state.view.cell_to_rect(target).center)])
    assert state.pending is not None
    return state.pending[0], distance


def answer_wrong(state):
    question = state.pending[0]
    wrong = next(i for i in state.answer_order if i != question.answer_index)
    button = state.answer_buttons[state.answer_order.index(wrong)]
    state.handle_events([click(button.rect.center)])
    assert state.pending is None and state.game.state is state


@pytest.mark.parametrize("distance,expected", [(1, 3), (2, 2)])
def test_distance_policy_asks_by_player_to_blue_distance_at_ask_time(tmp_path, fonts, distance, expected):
    bank = write_bank(tmp_path, mixed_pool(6))
    state = make_play(bank, Settings(tier_policy=TierPolicy.DISTANCE, move_limit=100))
    place_player_at_distance(state, distance)
    question, asked_at = open_question(state)
    assert asked_at == distance
    assert question.difficulty == expected


def test_distance_policy_catch_click_asks_a_tier_3(tmp_path, fonts):
    bank = write_bank(tmp_path, mixed_pool(6))
    state = make_play(bank, Settings(tier_policy=TierPolicy.DISTANCE, move_limit=100))
    place_player_at_distance(state, 1)
    state.handle_events([click(state.view.cell_to_rect(state.blue.cell).center)])
    question, _, intent = state.pending
    assert intent == "catch"
    assert question.difficulty == 3


def test_distance_policy_far_from_blue_serves_pool_order_without_tier_3(tmp_path, fonts):
    bank = write_bank(tmp_path, mixed_pool(6))
    state = make_play(bank, Settings(tier_policy=TierPolicy.DISTANCE, move_limit=100))
    place_player_at_distance(state, 4)
    assert state.allowed_tiers == (1, 2)
    question, _ = open_question(state)
    # No wanted tier, but a filter: the first tier-1/2 question in the shuffled order.
    assert question is next(q for q in bank._pool_orders[POOL] if q.difficulty != 3)


def test_distance_policy_saves_tier_3_for_the_approach(tmp_path, fonts):
    """Twelve far asks drain every 1 and 2 and recycle them; not one 3 is spent.
    The first near ask then still finds a fresh 3."""
    bank = write_bank(tmp_path, mixed_pool(2))
    state = make_play(bank, Settings(tier_policy=TierPolicy.DISTANCE, move_limit=100))
    for _ in range(12):
        place_player_at_distance(state, 4)
        asked, _ = open_question(state)
        assert asked.difficulty in (1, 2)
        answer_wrong(state)
    assert not any(q.difficulty == 3 for q in bank.questions if q.id in bank.used_ids)
    place_player_at_distance(state, 1)
    asked, _ = open_question(state)
    assert asked.difficulty == 3


def test_allowed_tiers_follow_the_player_across_the_board(tmp_path, fonts):
    bank = write_bank(tmp_path, mixed_pool(2))
    state = make_play(bank, Settings(tier_policy=TierPolicy.DISTANCE, move_limit=100))
    place_player_at_distance(state, 3)
    assert state.allowed_tiers == (1, 2)
    place_player_at_distance(state, 2)
    assert state.allowed_tiers is None


def test_distance_policy_falls_back_silently_when_tier_3_is_thin(tmp_path, fonts):
    thin = [question("hard-0", 3)] + [question(f"easy-{i}", 1) for i in range(5)]
    bank = write_bank(tmp_path, thin)
    state = make_play(bank, Settings(tier_policy=TierPolicy.DISTANCE, move_limit=100))
    served = []
    for _ in range(6):
        place_player_at_distance(state, 1)
        asked, _ = open_question(state)
        served.append(asked.id)
        answer_wrong(state)
    assert served[0] == "hard-0"
    assert sorted(served) == sorted(q["id"] for q in thin)
    assert len(set(served)) == 6  # no early repeat


def test_easy_policy_never_serves_tier_3_even_after_recycling(tmp_path, fonts):
    bank = write_bank(tmp_path, mixed_pool(2))
    state = make_play(bank, Settings(tier_policy=TierPolicy.TIERS_1_2, move_limit=100))
    assert state.allowed_tiers == (1, 2)
    served = []
    for _ in range(7):  # four allowed questions, so the pool recycles inside the loop
        question, _ = open_question(state)
        served.append(question)
        answer_wrong(state)
    assert all(q.difficulty in (1, 2) for q in served)
    assert {q.id for q in served} == {"t1-0", "t1-1", "t2-0", "t2-1"}
    assert not any(q.id.startswith("t3-") for q in bank.questions if q.id in bank.used_ids)


def test_all_policy_asks_with_no_preference_and_no_filter(tmp_path, fonts):
    bank = write_bank(tmp_path, mixed_pool(2))
    state = make_play(bank, Settings(tier_policy=TierPolicy.ALL, move_limit=100))
    assert state.allowed_tiers is None
    place_player_at_distance(state, 1)
    question, _ = open_question(state)
    assert question is bank._pool_orders[POOL][0]


def test_play_drops_subtopics_with_nothing_allowed_and_refuses_an_empty_selection(tmp_path, fonts):
    bank = write_bank(tmp_path, [
        question("a-1", 1, subtopic="Alpha"),
        question("b-3", 3, subtopic="Beta"),
    ])
    state = make_play(bank, Settings(tier_policy=TierPolicy.TIERS_1_2, move_limit=100))
    assert state.topic_subtopics == ((TOPIC, "Alpha"),)
    assert set(state.cell_topics.values()) == {(TOPIC, "Alpha")}

    only_hard = write_bank(tmp_path, [question("b-3", 3, subtopic="Beta")])
    with pytest.raises(ValueError, match="tier policy"):
        make_play(only_hard, Settings(tier_policy=TierPolicy.TIERS_1_2, move_limit=100))


# --- Topics screen guard ------------------------------------------------------


def make_topics(bank, settings, renderer):
    game = SimpleNamespace(settings=settings, topic_selections={}, renderer=renderer)
    return TopicsState(game, bank, "catch_blue", SUBJECT)


def note_rect(topics):
    note = topics.no_questions_note
    return pygame.Rect(note.x, note.y, note.width, note.height)


def test_topics_refuses_to_start_when_nothing_matches_the_allowed_tiers(tmp_path, fonts):
    bank = write_bank(tmp_path, [question("b-3", 3)])
    renderer = Renderer(FLAT)
    topics = make_topics(bank, PRESETS["easy"], renderer)
    assert topics.no_matching_questions
    assert not topics.start_button.active

    # The distance presets check the *starting* distance, which is always far,
    # so a tier-3-only selection cannot start there either.
    for name in ("medium", "hard"):
        far = make_topics(bank, PRESETS[name], renderer)
        assert far.no_matching_questions, name
        assert not far.start_button.active, name

    relaxed = make_topics(bank, Settings(tier_policy=TierPolicy.ALL), renderer)
    assert not relaxed.no_matching_questions
    assert relaxed.start_button.active


def test_topics_note_sits_inside_the_screen_clear_of_the_buttons(tmp_path, fonts):
    bank = write_bank(tmp_path, [question("b-3", 3)])
    topics = make_topics(bank, PRESETS["easy"], Renderer(FLAT))
    rect = note_rect(topics)
    screen = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    assert screen.contains(rect)
    assert rect.top >= topics.start_button.rect.bottom
    assert not rect.colliderect(topics.back_button.rect)
    topics.draw(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)))  # draws the note without error


def test_topics_start_follows_the_selection_under_the_allowed_tiers(tmp_path, fonts):
    bank = write_bank(tmp_path, [
        question("hard-only", 3, topic="hard_topic"),
        question("mixed-1", 1, topic="mixed_topic"),
        question("mixed-3", 3, topic="mixed_topic"),
    ])
    topics = make_topics(bank, PRESETS["easy"], Renderer(FLAT))
    boxes = dict(topics.topic_checkboxes)
    assert topics.start_button.active and not topics.no_matching_questions

    boxes["mixed_topic"].checked = False
    topics._sync_selection()
    assert not topics.start_button.active and topics.no_matching_questions

    boxes["hard_topic"].checked = False
    topics._sync_selection()
    assert not topics.start_button.active and not topics.no_matching_questions  # nothing selected: no note

    boxes["mixed_topic"].checked = True
    topics._sync_selection()
    assert topics.start_button.active and not topics.no_matching_questions


@pytest.mark.parametrize("preset", ["easy", "medium", "hard"])
def test_every_real_topic_can_start_on_every_preset(fonts, preset):
    bank = QuestionBank(REAL_BANK)
    game = SimpleNamespace(settings=PRESETS[preset], topic_selections={}, renderer=Renderer(FLAT))
    topics = TopicsState(game, bank, "catch_blue", "anatomy_physiology")
    for topic, checkbox in topics.topic_checkboxes:
        for _, other in topics.topic_checkboxes:
            other.checked = other is checkbox
        topics._sync_selection()
        assert topics.start_button.active, f"{topic} cannot start on {preset}"
