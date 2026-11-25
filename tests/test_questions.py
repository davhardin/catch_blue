"""Questions: the from_dict boundary, bank loading, and pair-scoped draws.

Everything here runs without a window -- questions.py is pygame-free by
design, and the last test makes sure it stays that way.

Per milestones/m3.md trap 7: drawing a question (next_unused_question)
mutates used-state, so every test builds its own bank from its own tmp_path
files -- no shared banks, ever. The real data/questions/ content gets exactly
one smoke test; content is data, not behavior, and M5 will churn it.

Drawing until a pool is dry, and restarting pools, are in test_pool_cycling.py.
"""

import json
import subprocess
import sys
from random import Random

import pytest

from conftest import ROOT, write_bank
from questions import Question, QuestionBank

# --- helpers ----------------------------------------------------------------


def make_question(**overrides):
    """A complete, valid question dict; override fields per test."""
    q = {
        "id": "q-001",
        "subject": "subject_a",
        "topic": "topic_a",
        "subtopic": "Section One",
        "difficulty": 1,
        "type": "multiple_choice",
        "prompt": "Which organelle is the site of ATP synthesis?",
        "choices": ["Nucleus", "Mitochondrion", "Ribosome"],
        "answer_index": 1,
    }
    q.update(overrides)
    return q


def write_file(directory, filename, questions):
    """Write one file without loading, for banks built from several files."""
    (directory / filename).write_text(json.dumps(questions), encoding="utf-8")


# --- Question.from_dict: the happy path -------------------------------------


def test_from_dict_carries_every_field():
    q = Question.from_dict(make_question())
    assert q.id == "q-001"
    assert q.subject == "subject_a"
    assert q.topic == "topic_a"
    assert q.subtopic == "Section One"
    assert q.difficulty == 1
    assert q.type == "multiple_choice"
    assert q.prompt == "Which organelle is the site of ATP synthesis?"
    assert q.choices == ["Nucleus", "Mitochondrion", "Ribosome"]
    assert q.answer_index == 1
    assert q.shuffle is True


@pytest.mark.parametrize("choice_index", [0, 1, 2])
def test_is_correct_only_at_answer_index(choice_index):
    q = Question.from_dict(make_question())
    assert q.is_correct(choice_index) == (choice_index == 1)


def test_from_dict_preserves_explicit_shuffle_false():
    q = Question.from_dict(make_question(shuffle=False))
    assert q.shuffle is False


# --- Question display order -------------------------------------------------


def test_shuffled_display_order_is_a_permutation_without_mutation():
    q = Question.from_dict(make_question())
    original_choices = list(q.choices)
    original_answer_index = q.answer_index

    order = q.display_order(Random(7))
    displayed_choices = [q.choices[index] for index in order]

    assert sorted(order) == list(range(len(q.choices)))
    assert sorted(displayed_choices) == sorted(original_choices)
    assert q.choices == original_choices
    assert q.answer_index == original_answer_index


def test_correct_answer_tracks_through_every_seeded_display_order():
    q = Question.from_dict(make_question())
    correct_text = q.choices[q.answer_index]

    for seed in range(100):
        order = q.display_order(Random(seed))
        correct_display_slot = order.index(q.answer_index)
        displayed_choices = [q.choices[index] for index in order]

        assert displayed_choices[correct_display_slot] == correct_text
        assert q.is_correct(order[correct_display_slot])


def test_shuffle_false_preserves_file_order():
    q = Question.from_dict(make_question(shuffle=False))
    canonical_order = list(range(len(q.choices)))

    for seed in range(10):
        assert q.display_order(Random(seed)) == canonical_order


def test_repeated_asks_create_fresh_orders_without_mutating_question():
    q = Question.from_dict(make_question())
    original_choices = list(q.choices)
    rng = Random(3)

    orders = [q.display_order(rng) for _ in range(10)]

    assert all(
        order is not other
        for index, order in enumerate(orders)
        for other in orders[index + 1:]
    )
    assert len({tuple(order) for order in orders}) > 1
    assert q.choices == original_choices


# --- Question.from_dict: every rejection ------------------------------------

REQUIRED_FIELDS = [
    "id",
    "subject",
    "topic",
    "subtopic",
    "difficulty",
    "type",
    "prompt",
    "choices",
    "answer_index",
]


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_from_dict_rejects_missing_field(field):
    data = make_question()
    del data[field]
    with pytest.raises(KeyError, match=field):
        Question.from_dict(data)


@pytest.mark.parametrize("bad_index", [-1, 3])
def test_from_dict_rejects_out_of_range_answer_index(bad_index):
    """Three choices, so valid indices are 0-2; the error names the id."""
    with pytest.raises(ValueError, match="q-001"):
        Question.from_dict(make_question(answer_index=bad_index))


def test_from_dict_rejects_unknown_type():
    """fill_blank is a Phase 2 stretch goal -- the type field ships now,
    but only multiple_choice may pass the gate."""
    with pytest.raises(ValueError, match="q-001"):
        Question.from_dict(make_question(type="fill_blank"))


@pytest.mark.parametrize("bad_shuffle", ["false", 1, None])
def test_from_dict_rejects_non_boolean_shuffle(bad_shuffle):
    with pytest.raises(ValueError, match="q-001"):
        Question.from_dict(make_question(shuffle=bad_shuffle))


# --- QuestionBank: loading --------------------------------------------------


def test_bank_pools_questions_from_multiple_files(tmp_path):
    write_file(tmp_path, "one.json", [make_question(id="a1")])
    write_file(tmp_path, "two.json", [make_question(id="b1", topic="topic_b")])
    bank = QuestionBank(tmp_path)
    assert sorted(q.id for q in bank.questions) == ["a1", "b1"]


def test_bank_loads_files_in_sorted_filename_order(tmp_path):
    """Write the later-sorting file first: load order must follow filename
    sort, not creation order, or rotation differs between machines."""
    write_file(tmp_path, "02_written_first.json", [make_question(id="second")])
    write_file(tmp_path, "01_written_second.json", [make_question(id="first")])
    bank = QuestionBank(tmp_path)
    assert [q.id for q in bank.questions] == ["first", "second"]


def test_bank_crashes_at_load_naming_the_bad_file(tmp_path):
    """Validate at load, crash at startup: a malformed question must never
    survive until mid-game."""
    write_file(tmp_path, "good.json", [make_question(id="ok")])
    write_file(tmp_path, "broken.json", [make_question(id="bad", answer_index=9)])
    with pytest.raises(ValueError, match="broken"):
        QuestionBank(tmp_path)


def test_bank_missing_field_also_names_the_bad_file(tmp_path):
    data = make_question(id="bad")
    del data["subtopic"]
    write_file(tmp_path, "broken.json", [data])
    with pytest.raises(ValueError, match="broken"):
        QuestionBank(tmp_path)


def test_bank_json_syntax_error_names_file(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text('[{"id": "q-001",}]', encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        QuestionBank(tmp_path)

    assert "broken.json" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)


def test_bank_rejects_duplicate_ids_across_files(tmp_path):
    write_file(tmp_path, "first.json", [make_question(id="duplicate-id")])
    write_file(tmp_path, "second.json", [
        make_question(id="duplicate-id", topic="topic_b")
    ])

    with pytest.raises(ValueError) as exc_info:
        QuestionBank(tmp_path)

    message = str(exc_info.value)
    assert "duplicate-id" in message
    assert "first.json" in message
    assert "second.json" in message


def test_bank_rejects_near_identical_subtopics(tmp_path):
    write_file(tmp_path, "broken.json", [
        make_question(
            id="q-001",
            topic="anatomy",
            subtopic="Body Regions",
        ),
        make_question(
            id="q-002",
            topic="anatomy",
            subtopic=" body  regions ",
        ),
    ])

    with pytest.raises(ValueError) as exc_info:
        QuestionBank(tmp_path)

    message = str(exc_info.value)
    assert "Body Regions" in message
    assert " body  regions " in message
    assert "anatomy" in message
    assert "broken.json" in message


def test_bank_rejects_near_identical_subjects(tmp_path):
    write_file(tmp_path, "broken.json", [
        make_question(id="q-001", subject="anatomy_physiology"),
        make_question(
            id="q-002",
            subject=" ANATOMY_PHYSIOLOGY ",
            topic="topic_b",
        ),
    ])

    with pytest.raises(ValueError) as exc_info:
        QuestionBank(tmp_path)

    message = str(exc_info.value)
    assert "anatomy_physiology" in message
    assert " ANATOMY_PHYSIOLOGY " in message
    assert "broken.json" in message


def test_near_identical_subtopics_are_allowed_under_different_topics(tmp_path):
    bank = write_bank(tmp_path, [
        make_question(
            id="a1",
            topic="topic_a",
            subtopic="Overview",
        ),
        make_question(
            id="b1",
            topic="topic_b",
            subtopic=" overview ",
        ),
    ])

    assert bank.subtopics("topic_a") == ["Overview"]
    assert bank.subtopics("topic_b") == [" overview "]


# --- topics and subtopics ---------------------------------------------------


def test_subjects_are_sorted_and_unique(tmp_path):
    bank = write_bank(tmp_path, [
        make_question(id="1", subject="subject_z"),
        make_question(id="2", subject="subject_a", topic="anatomy"),
        make_question(id="3", subject="subject_a", topic="zoology"),
    ])
    assert bank.subjects == ["subject_a", "subject_z"]


def test_topics_are_sorted_unique_and_scoped_to_subject(tmp_path):
    bank = write_bank(tmp_path, [
        make_question(id="1", subject="subject_a", topic="zoology"),
        make_question(id="2", subject="subject_a", topic="anatomy"),
        make_question(id="3", subject="subject_b", topic="chemistry"),
    ])
    assert bank.topics("subject_a") == ["anatomy", "zoology"]
    assert bank.topics("subject_b") == ["chemistry"]
    assert bank.topics("made_up_subject") == []


def test_subtopics_are_sorted_unique_and_scoped_to_their_topic(tmp_path):
    bank = write_bank(tmp_path, [
        make_question(id="1", topic="topic_a", subtopic="Zebra Section"),
        make_question(id="2", topic="topic_a", subtopic="Apple Section"),
        make_question(id="3", topic="topic_a", subtopic="Apple Section"),
        make_question(id="4", topic="topic_b", subtopic="Other Section"),
    ])
    assert bank.subtopics("topic_a") == ["Apple Section", "Zebra Section"]
    assert bank.subtopics("topic_b") == ["Other Section"]


# --- next_unused_question: draws within a (topic, subtopic) pool -----------
#
# The checks here hold for any draw. Serving each question once and then
# None, and restarting a pool with a fresh shuffle, are in test_pool_cycling.py.


def draw(bank, rng, topic="topic_a", subtopic="Section One"):
    question = bank.next_unused_question(topic, subtopic, rng)
    return None if question is None else question.id


def test_pool_shuffles_once_on_its_first_draw(tmp_path):
    class RecordingRandom(Random):
        def __init__(self, seed):
            super().__init__(seed)
            self.shuffled_ids = []

        def shuffle(self, items):
            self.shuffled_ids.append({q.id for q in items})
            super().shuffle(items)

    bank = write_bank(tmp_path, [make_question(id=f"a{n}") for n in (1, 2, 3)])
    rng = RecordingRandom(7)
    for _ in range(3):
        draw(bank, rng)
    assert rng.shuffled_ids == [{"a1", "a2", "a3"}]


def test_draws_do_not_mutate_canonical_questions(tmp_path):
    bank = write_bank(tmp_path, [
        make_question(id=f"q{n}", shuffle=False) for n in range(5)
    ])
    originals = [(q.id, list(q.choices), q.answer_index, q.shuffle) for q in bank.questions]
    load_order = [q.id for q in bank.questions]
    orders = set()
    for seed in range(4):
        fresh = QuestionBank(tmp_path)
        rng = Random(seed)
        orders.add(tuple(draw(fresh, rng) for _ in range(5)))
        assert [(q.id, q.choices, q.answer_index, q.shuffle) for q in fresh.questions] == originals
        for q in fresh.questions:
            assert q.display_order(rng) == list(range(len(q.choices)))
    # shuffle=False keeps each question's answers in file order, not the pool's.
    assert any(order != tuple(load_order) for order in orders)


def test_pools_of_the_same_topic_stay_isolated(tmp_path):
    bank = write_bank(tmp_path, [
        make_question(id="a1"),
        make_question(id="b1", subtopic="Section Two"),
    ])
    rng = Random(7)
    assert [draw(bank, rng), draw(bank, rng)] == ["a1", None]
    assert bank.used_ids == {"a1"}


def test_same_subtopic_name_under_two_topics_is_two_pools(tmp_path):
    """milestones/m3.md trap 10, live in the real data already: cells and
    tissues both have Filler subtopics. The pair key keeps them apart."""
    bank = write_bank(tmp_path, [
        make_question(id="a1", topic="topic_a", subtopic="Overview"),
        make_question(id="b1", topic="topic_b", subtopic="Overview"),
    ])
    rng = Random(7)
    assert draw(bank, rng, "topic_a", "Overview") == "a1"
    assert draw(bank, rng, "topic_b", "Overview") == "b1"
    # Using up one Overview must not reset or leak into the other.
    assert draw(bank, rng, "topic_a", "Overview") is None
    assert draw(bank, rng, "topic_b", "Overview") is None


def test_unknown_pair_raises_naming_it_and_marks_nothing_used(tmp_path):
    bank = write_bank(tmp_path, [make_question()])
    rng = Random(7)
    with pytest.raises(ValueError, match="No Such Section"):
        draw(bank, rng, "topic_a", "No Such Section")
    with pytest.raises(ValueError, match="no_such_topic"):
        draw(bank, rng, "no_such_topic", "Section One")
    assert bank.used_ids == set()


# --- the shipped data: one smoke test ---------------------------------------


def test_shipped_question_files_load_and_validate(bank):
    """Content is data, not behavior -- this only proves the real files pass
    the from_dict gate and every topic has at least one subtopic."""
    assert bank.subjects
    for subject in bank.subjects:
        topics = bank.topics(subject)
        assert topics
        for topic in topics:
            assert bank.subtopics(topic)


# --- the pure/pixel line ----------------------------------------------------


def test_questions_module_never_imports_pygame():
    """milestones/m3.md: questions.py stays pygame-free so loading and
    rotation stay headless-testable. Same guard as board and characters."""
    result = subprocess.run(
        [sys.executable, "-c", "import questions, sys; assert 'pygame' not in sys.modules"],
        capture_output=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, "questions.py has picked up a pygame dependency"
