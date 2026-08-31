"""Questions: the from_dict boundary, bank loading, and pair-scoped rotation.

Everything here runs without a window -- questions.py is pygame-free by
design, and the last test makes sure it stays that way.

Per milestones/m3.md trap 7: next_question mutates used-state, so every test
builds its own bank from its own tmp_path files -- no shared banks, ever.
The real data/questions/ content gets exactly one smoke test; content is
data, not behavior, and M5 will churn it.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

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
    (directory / filename).write_text(json.dumps(questions), encoding="utf-8")


def build_bank(tmp_path, questions, filename="bank.json"):
    """One-file bank from a list of question dicts."""
    write_file(tmp_path, filename, questions)
    return QuestionBank(tmp_path)


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


@pytest.mark.parametrize("choice_index", [0, 1, 2])
def test_is_correct_only_at_answer_index(choice_index):
    q = Question.from_dict(make_question())
    assert q.is_correct(choice_index) == (choice_index == 1)


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


@pytest.mark.parametrize("bad_index", [-1, 3, 99])
def test_from_dict_rejects_out_of_range_answer_index(bad_index):
    """Three choices, so valid indices are 0-2; the error names the id."""
    with pytest.raises(ValueError, match="q-001"):
        Question.from_dict(make_question(answer_index=bad_index))


def test_from_dict_rejects_unknown_type():
    """fill_blank is a Phase 2 stretch goal -- the type field ships now,
    but only multiple_choice may pass the gate."""
    with pytest.raises(ValueError, match="q-001"):
        Question.from_dict(make_question(type="fill_blank"))


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
    bank = build_bank(tmp_path, [
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
    bank = build_bank(tmp_path, [
        make_question(id="1", subject="subject_z"),
        make_question(id="2", subject="subject_a", topic="anatomy"),
        make_question(id="3", subject="subject_a", topic="zoology"),
    ])
    assert bank.subjects == ["subject_a", "subject_z"]


def test_topics_are_sorted_unique_and_scoped_to_subject(tmp_path):
    bank = build_bank(tmp_path, [
        make_question(id="1", subject="subject_a", topic="zoology"),
        make_question(id="2", subject="subject_a", topic="anatomy"),
        make_question(id="3", subject="subject_b", topic="chemistry"),
    ])
    assert bank.topics("subject_a") == ["anatomy", "zoology"]
    assert bank.topics("subject_b") == ["chemistry"]
    assert bank.topics("made_up_subject") == []


def test_subtopics_are_sorted_unique_and_scoped_to_their_topic(tmp_path):
    bank = build_bank(tmp_path, [
        make_question(id="1", topic="topic_a", subtopic="Zebra Section"),
        make_question(id="2", topic="topic_a", subtopic="Apple Section"),
        make_question(id="3", topic="topic_a", subtopic="Apple Section"),
        make_question(id="4", topic="topic_b", subtopic="Other Section"),
    ])
    assert bank.subtopics("topic_a") == ["Apple Section", "Zebra Section"]
    assert bank.subtopics("topic_b") == ["Other Section"]


# --- next_question: rotation within a (topic, subtopic) pool ----------------


def three_pool():
    """One pool of three questions, in load order a1, a2, a3."""
    return [make_question(id=f"a{n}") for n in (1, 2, 3)]


def test_rotation_walks_the_pool_in_load_order(tmp_path):
    bank = build_bank(tmp_path, three_pool())
    drawn = [bank.next_question("topic_a", "Section One").id for _ in range(3)]
    assert drawn == ["a1", "a2", "a3"]


def test_dry_pool_recycles_from_the_top(tmp_path):
    bank = build_bank(tmp_path, three_pool())
    drawn = [bank.next_question("topic_a", "Section One").id for _ in range(7)]
    assert drawn == ["a1", "a2", "a3", "a1", "a2", "a3", "a1"]


def test_recycle_resets_only_its_own_pool(tmp_path):
    """Exhausting pool A must not disturb pool B's mid-rotation position."""
    bank = build_bank(tmp_path, [
        make_question(id="a1"),
        make_question(id="a2"),
        make_question(id="b1", subtopic="Section Two"),
        make_question(id="b2", subtopic="Section Two"),
    ])
    assert bank.next_question("topic_a", "Section Two").id == "b1"
    # Exhaust and recycle Section One...
    for _ in range(3):
        bank.next_question("topic_a", "Section One")
    # ...and Section Two resumes where it left off.
    assert bank.next_question("topic_a", "Section Two").id == "b2"


def test_pools_of_the_same_topic_stay_isolated(tmp_path):
    bank = build_bank(tmp_path, [
        make_question(id="a1"),
        make_question(id="b1", subtopic="Section Two"),
    ])
    drawn = [bank.next_question("topic_a", "Section One").id for _ in range(4)]
    assert drawn == ["a1", "a1", "a1", "a1"]


def test_same_subtopic_name_under_two_topics_is_two_pools(tmp_path):
    """milestones/m3.md trap 10, live in the real data already: cells and
    tissues both have Filler subtopics. The pair key keeps them apart."""
    bank = build_bank(tmp_path, [
        make_question(id="a1", topic="topic_a", subtopic="Overview"),
        make_question(id="b1", topic="topic_b", subtopic="Overview"),
    ])
    assert bank.next_question("topic_a", "Overview").id == "a1"
    assert bank.next_question("topic_b", "Overview").id == "b1"
    # Recycling one Overview must not reset or leak into the other.
    assert bank.next_question("topic_a", "Overview").id == "a1"
    assert bank.next_question("topic_b", "Overview").id == "b1"


def test_unknown_pair_raises(tmp_path):
    bank = build_bank(tmp_path, [make_question()])
    with pytest.raises(ValueError):
        bank.next_question("topic_a", "No Such Section")
    with pytest.raises(ValueError):
        bank.next_question("no_such_topic", "Section One")


# --- the shipped data: one smoke test ---------------------------------------


def test_shipped_question_files_load_and_validate():
    """Content is data, not behavior -- this only proves the real files pass
    the from_dict gate and every topic has at least one subtopic."""
    bank = QuestionBank(Path(__file__).parent.parent / "data" / "questions")
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
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, "questions.py has picked up a pygame dependency"
