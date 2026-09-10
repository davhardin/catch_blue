import json
from collections.abc import Iterable
from pathlib import Path
from random import Random


def _normalize_label(value: str) -> str:
    return " ".join(value.split()).casefold()


class Question:
    def __init__(
        self,
        id,
        subject,
        topic,
        subtopic,
        difficulty,
        type,
        prompt,
        choices,
        answer_index,
        shuffle=True,
    ):
        self.id = id
        self.subject = subject
        self.topic = topic
        self.subtopic = subtopic
        self.difficulty = difficulty
        self.type = type
        self.prompt = prompt
        self.choices = choices
        self.answer_index = answer_index
        self.shuffle = shuffle

    @classmethod
    def from_dict(cls, data):
        try:
            if data["type"] != 'multiple_choice':
                raise ValueError(f"Invalid question type: {data['type']}, see question {data.get('id', 'unknown')}")
            if data['answer_index'] < 0 or data['answer_index'] >= len(data['choices']):
                raise ValueError(f"Invalid answer index: {data['answer_index']}, see question {data.get('id', 'unknown')}")

            shuffle = data.get('shuffle', True)
            if not isinstance(shuffle, bool):
                raise ValueError(f"Invalid shuffle value: {shuffle!r}, see question {data.get('id', 'unknown')}")

            return cls(
                id = data['id'],
                subject = data['subject'],
                topic = data['topic'],
                subtopic = data['subtopic'],
                difficulty = data['difficulty'],
                type = data['type'],
                prompt = data['prompt'],
                choices = data['choices'],
                answer_index = data['answer_index'],
                shuffle = shuffle,
            )
        except KeyError as e:
            raise KeyError(f"Missing key: {e}") from e

    def is_correct(self, choice_index):
        return self.answer_index == choice_index

    def display_order(self, rng: Random) -> list[int]:
        order = list(range(len(self.choices)))
        if self.shuffle:
            rng.shuffle(order)
        return order

class QuestionBank:
    def __init__(self, data_dir):
        self.questions = []
        self.used_ids = set()
        self._pool_orders: dict[tuple[str, str], list[Question]] = {}
        self.data_dir = data_dir

        path = Path(self.data_dir)
        seen_ids = {}
        seen_subjects = {}
        seen_subtopics = {}

        for filename in sorted(path.rglob("*.json")):
            if filename.is_file():
                with open(filename, encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"Error parsing JSON from {filename}: {e}"
                        ) from e

                    for d in data:
                        try:
                            question = Question.from_dict(d)

                            first_file = seen_ids.get(question.id)
                            if first_file is not None:
                                raise ValueError(f"Duplicate question id '{question.id}' in {filename}; first seen in {first_file}")

                            normalized_subject = _normalize_label(question.subject)
                            existing_subject = seen_subjects.get(normalized_subject)
                            if existing_subject is not None:
                                first_subject, first_subject_file = existing_subject
                                if first_subject != question.subject:
                                    raise ValueError(f"Subjects '{first_subject}' and '{question.subject}' differ only by case or whitespace; found in {first_subject_file} and {filename}")

                            normalized = _normalize_label(question.subtopic)
                            key = (question.subject, question.topic, normalized)
                            existing = seen_subtopics.get(key)

                            if existing is not None:
                                first_spelling, first_subtopic_file = existing
                                if first_spelling != question.subtopic:
                                    raise ValueError(f"Subtopics '{first_spelling}' and '{question.subtopic}' in topic '{question.topic}' differ only by case or whitespace; found in {first_subtopic_file} and {filename}")

                            seen_ids[question.id] = filename
                            if existing_subject is None:
                                seen_subjects[normalized_subject] = (
                                    question.subject,
                                    filename,
                                )
                            if existing is None:
                                seen_subtopics[key] = (
                                    question.subtopic,
                                    filename,
                                )
                            self.questions.append(question)
                        except (ValueError, KeyError) as e:
                            raise ValueError(
                                f"Error parsing question from {filename}: {e}"
                            ) from e

        self.subjects = sorted(set(q.subject for q in self.questions))

    def topics(self, subject):
        return sorted(
            set(q.topic for q in self.questions if q.subject == subject)
        )

    def subtopics(self, topic):
        return sorted(
            set(q.subtopic for q in self.questions if q.topic == topic)
        )

    def available_pools(
        self,
        pools: Iterable[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        allowed = set(pools)
        return sorted({
            (question.topic, question.subtopic)
            for question in self.questions
            if (question.topic, question.subtopic) in allowed
            and question.id not in self.used_ids
        })

    def restart_pools(
        self,
        pools: Iterable[tuple[str, str]],
    ) -> None:
        pools = set(pools)
        self.used_ids.difference_update(
            question.id
            for question in self.questions
            if (question.topic, question.subtopic) in pools
        )

        # Rebuild and shuffle each pool only when it is next requested.
        for pair in pools:
            self._pool_orders.pop(pair, None)

    def next_unused_question(
        self,
        topic,
        subtopic,
        rng: Random,
    ) -> Question | None:
        """Return an unused question, or None if the pool is exhausted."""
        key = (topic, subtopic)
        candidates = self._pool_orders.get(key)

        if candidates is None:
            candidates = [
                q
                for q in self.questions
                if q.topic == topic and q.subtopic == subtopic
            ]
            if not candidates:
                raise ValueError(
                    f"No questions available for topic '{topic}' "
                    f"and subtopic '{subtopic}'"
                )

            rng.shuffle(candidates)
            self._pool_orders[key] = candidates

        for q in candidates:
            if q.id not in self.used_ids:
                self.used_ids.add(q.id)
                return q

        return None

    def next_question(self, topic, subtopic, rng: Random) -> Question:
        question = self.next_unused_question(topic, subtopic, rng)
        if question is not None:
            return question

        candidates = self._pool_orders[(topic, subtopic)]
        for q in candidates:
            self.used_ids.discard(q.id)

        rng.shuffle(candidates)
        first = candidates[0]
        self.used_ids.add(first.id)
        return first
