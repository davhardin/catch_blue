import argparse
import asyncio
import sys
from pathlib import Path

import pygame

from game import Game
from questions import QuestionBank
from theme import DEFAULT_THEME, THEMES


def build_game(argv=None):
    parser = argparse.ArgumentParser(description="Catch Blue: The Science Learning Game")
    parser.add_argument("--theme", choices=sorted(THEMES), default=DEFAULT_THEME)
    args = parser.parse_args(argv)

    questions_path = Path(__file__).resolve().parent / "data" / "questions"
    bank = QuestionBank(questions_path)

    if not bank.subjects:
        raise ValueError("The question bank contains no subjects")

    return Game(bank, theme=THEMES[args.theme])


def main(argv=None):
    build_game(argv).run()


def _fit_browser_canvas():
    """Ask pygbag to re-fit the canvas now that the display has its real size.

    pygbag sizes the canvas once at page load, before set_mode runs, so it
    otherwise keeps the placeholder 1x1 aspect ratio and stretches the frame.
    """
    import platform

    window = getattr(platform, "window", None)
    if window is not None:
        window.window_resize()


async def main_web():
    """Browser entry point (pygbag): yield to the event loop every frame."""
    game = build_game([])
    _fit_browser_canvas()

    while game.step():
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.run(main_web())
    else:
        main()
