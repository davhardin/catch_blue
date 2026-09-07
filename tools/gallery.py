"""Render every screen of Catch Blue headlessly to PNG, for comparing themes.

Usage (from the repo root):

    .venv/bin/python tools/gallery.py --out catch_blue_local_only/gallery/flat-before
    .venv/bin/python tools/gallery.py --theme pixel --out catch_blue_local_only/gallery/pixel-v1
    .venv/bin/python tools/gallery.py --compare A B      # pixel-diff two galleries

Deterministic: a fixed seed drives the scramble, rotation, shuffle, and flee,
so the same code produces the same PNGs, and two runs can be diffed byte for
byte. That is the M6.f.2 check — the flat gallery must be identical before
and after the render-primitive refactor.

`--theme` is exported as CATCH_BLUE_THEME for main-style theme selection once
`theme.py` exists; until then it only names the output folder.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from random import Random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from board import Cell, get_distance, is_adjacent  # noqa: E402
from game import Game  # noqa: E402
from game_setup import GameConfig  # noqa: E402
from questions import QuestionBank  # noqa: E402
from states.game_over import GameOverState  # noqa: E402
from states.menus import GameSelectState  # noqa: E402

SEED = 2026
TOPICS = ("cells", "tissues")


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)


def frame(game, events=(), dt=16):
    """One iteration of Game.run's body, in its real order."""
    state = game.state
    state.update(dt)
    if game.state is state:
        state.handle_events(list(events))
    game.state.draw(game.screen)


def answer_event(state, correct):
    question, _, _ = state.pending
    for display_index, canonical in enumerate(state.answer_order):
        if (canonical == question.answer_index) == correct:
            return click(state.answer_buttons[display_index].rect.center)
    raise RuntimeError("no matching answer button")


def capture(game, out_dir, name):
    path = out_dir / f"{name}.png"
    pygame.image.save(game.screen, str(path))
    return path


def render_gallery(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    bank = QuestionBank(ROOT / "data" / "questions")
    game = Game(bank, rng=Random(SEED))
    saved = []

    # 1. Game Select
    frame(game)
    saved.append(capture(game, out_dir, "01_game_select"))

    # 2. Subject
    frame(game, [click(game.state.catch_blue_button.rect.center)])
    saved.append(capture(game, out_dir, "02_subject"))

    # 3. Topics (as it opens, all checked)
    frame(game, [click(game.state.anatomy_button.rect.center)])
    saved.append(capture(game, out_dir, "03_topics"))

    # 4. Play — board, straight into a fixed config for determinism
    game.start_play(bank, GameConfig("catch_blue", "anatomy_physiology", TOPICS))
    state = game.state
    frame(game)
    saved.append(capture(game, out_dir, "04_play_board"))

    # 5. Play — hover over a legal move
    hover_cell = min(state.moves, key=lambda c: get_distance(c, state.blue.cell))
    hover = pygame.event.Event(
        pygame.MOUSEMOTION, pos=state.view.cell_to_rect(hover_cell).center
    )
    frame(game, [hover])
    saved.append(capture(game, out_dir, "05_play_hover"))

    # 6. Play — question popup
    frame(game, [click(state.view.cell_to_rect(hover_cell).center)])
    assert state.pending is not None
    saved.append(capture(game, out_dir, "06_play_popup"))

    # 7. Play — reveal after a wrong answer (board frozen, red + green)
    frame(game, [answer_event(state, False)])
    assert state.reveal is not None
    saved.append(capture(game, out_dir, "07_play_reveal_wrong"))
    frame(game, dt=state.reveal_duration_ms)  # resolve: Blue flees

    # 8. Play — reveal after a correct answer
    target = min(state.moves, key=lambda c: get_distance(c, state.blue.cell))
    frame(game, [click(state.view.cell_to_rect(target).center)])
    frame(game, [answer_event(state, True)])
    saved.append(capture(game, out_dir, "08_play_reveal_right"))
    frame(game, dt=state.reveal_duration_ms)

    # 9. Game Over — win (walk to Blue answering correctly)
    for _ in range(40):
        if isinstance(game.state, GameOverState):
            break
        st = game.state
        if is_adjacent(st.player.cell, st.blue.cell):
            target = st.blue.cell
        else:
            target = min(st.moves, key=lambda c: get_distance(c, st.blue.cell))
        frame(game, [click(st.view.cell_to_rect(target).center)])
        frame(game, [answer_event(st, True)])
        frame(game, dt=st.reveal_duration_ms)
    assert isinstance(game.state, GameOverState) and game.state.result == "win"
    frame(game)
    saved.append(capture(game, out_dir, "09_game_over_win"))

    # 10. Game Over — lose (fresh game, burn the counter on wrong answers)
    game.start_play(bank, GameConfig("catch_blue", "anatomy_physiology", TOPICS))
    state = game.state
    state.moves_remaining = 1
    frame(game)
    target = next(iter(sorted(state.moves)))
    frame(game, [click(state.view.cell_to_rect(target).center)])
    frame(game, [answer_event(state, False)])
    frame(game, dt=state.reveal_duration_ms)
    assert isinstance(game.state, GameOverState) and game.state.result == "lose"
    frame(game)
    saved.append(capture(game, out_dir, "10_game_over_lose"))

    pygame.quit()
    return saved


def compare(a: Path, b: Path) -> int:
    """Byte-compare same-named PNGs in two galleries; return the mismatch count."""
    names = sorted({p.name for p in a.glob("*.png")} | {p.name for p in b.glob("*.png")})
    mismatches = 0
    for name in names:
        pa, pb = a / name, b / name
        if not pa.exists() or not pb.exists():
            print(f"  MISSING   {name}  ({'A' if not pa.exists() else 'B'})")
            mismatches += 1
            continue
        if pa.read_bytes() == pb.read_bytes():
            print(f"  identical {name}")
        else:
            print(f"  DIFFERS   {name}")
            mismatches += 1
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--theme", default="flat", help="theme name (exported as CATCH_BLUE_THEME)")
    parser.add_argument("--out", type=Path, help="output folder (default: catch_blue_local_only/gallery/<theme>)")
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("A", "B"), help="diff two gallery folders instead of rendering")
    args = parser.parse_args()

    if args.compare:
        a, b = args.compare
        print(f"comparing {a} vs {b}")
        n = compare(a, b)
        print(f"{n} mismatch(es)")
        sys.exit(1 if n else 0)

    os.environ["CATCH_BLUE_THEME"] = args.theme
    out = args.out or (ROOT / "catch_blue_local_only" / "gallery" / args.theme)
    saved = render_gallery(out)
    print(f"rendered {len(saved)} screens to {out}")
    for path in saved:
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
