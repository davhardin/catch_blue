import argparse
from pathlib import Path

from game import Game
from questions import QuestionBank
from theme import DEFAULT_THEME, THEMES


def main(argv=None):
    parser = argparse.ArgumentParser(description="Catch Blue: The Science Learning Game")
    parser.add_argument("--theme", choices=sorted(THEMES), default=DEFAULT_THEME)
    args = parser.parse_args(argv)

    questions_path = Path(__file__).resolve().parent / "data" / "questions"
    bank = QuestionBank(questions_path)

    if not bank.subjects:
        raise ValueError("The question bank contains no subjects")

    game = Game(bank, theme=THEMES[args.theme])
    game.run()


if __name__ == "__main__":
    main()
