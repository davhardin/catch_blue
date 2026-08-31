import json
from pathlib import Path

class Question:
    def __init__(self, id, topic, subtopic, difficulty, type, prompt, choices, answer_index):
        self.id = id
        self.topic = topic
        self.subtopic = subtopic
        self.difficulty = difficulty
        self.type = type
        self.prompt = prompt
        self.choices = choices
        self.answer_index = answer_index

    @classmethod
    def from_dict(cls, data):
        try:
            if data["type"] != 'multiple_choice':
                raise ValueError(f"Invalid question type: {data['type']}, see question {data.get('id', 'unknown')}")
            if data['answer_index'] < 0 or data['answer_index'] >= len(data['choices']):
                raise ValueError(f"Invalid answer index: {data['answer_index']}, see question {data.get('id', 'unknown')}")

            return cls(
                id = data['id'],
                topic = data['topic'],
                subtopic = data['subtopic'],
                difficulty = data['difficulty'],
                type = data['type'],
                prompt = data['prompt'],
                choices = data['choices'],
                answer_index = data['answer_index'],
            )
        except KeyError as e:
            raise KeyError(f"Missing key: {e}") from e

    def is_correct(self, choice_index):
        return self.answer_index == choice_index

class QuestionBank:
    def __init__(self, data_dir):
        self.questions = []
        self.used_ids = set()
        self.data_dir = data_dir

        path = Path(self.data_dir)

        for filename in sorted(path.rglob("*.json")):
            if filename.is_file():
                with open(filename, encoding='utf-8') as f:
                    data = json.load(f)
                    for d in data:
                        try:
                            self.questions.append(Question.from_dict(d))
                        except (ValueError, KeyError) as e:
                            raise ValueError(f"Error parsing question from {filename}: {e}") from e

        self.topics = sorted(set(q.topic for q in self.questions))

    def subtopics(self, topic):
        return sorted(
            set(q.subtopic for q in self.questions if q.topic == topic)
        )

    def next_question(self, topic, subtopic):
        candidates = [
            q
            for q in self.questions
            if q.topic == topic and q.subtopic == subtopic
        ]
        if not candidates:
            raise ValueError(f"No questions available for topic '{topic}' and subtopic '{subtopic}'")

        for q in candidates:
            if q.id not in self.used_ids:
                self.used_ids.add(q.id)
                return q

        for q in candidates:
            self.used_ids.discard(q.id)

        first = candidates[0]
        self.used_ids.add(first.id)
        return first
