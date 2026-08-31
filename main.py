from pathlib import Path

from game import Game
from questions import QuestionBank


def main():
    questions_path = Path(__file__).parent / "data" / "questions"
    bank = QuestionBank(questions_path)

    if not bank.subjects:
        raise ValueError("The question bank contains no subjects")

    game = Game(bank)
    game.run()


if __name__ == "__main__":
    main()
