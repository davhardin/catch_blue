"""Audit shipped-bank theme geometry and optionally capture worst popups.

Run with explicit SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame

from board import Board, Cell
from board_view import BoardView
from constants import (
    BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION, LABEL_PADDING,
    SCREEN_HEIGHT, SCREEN_WIDTH,
)
from game_setup import subtopic_display_name
from questions import QuestionBank
from render import Renderer
from states.play import build_question_popup
from theme import THEMES


def audit(bank, renderer, board_size=5):
    failures = []
    records = []

    screen_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    preferred_bottom = SCREEN_HEIGHT - 20
    view = BoardView(Board(board_size, board_size), BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION)
    cell_rect = view.cell_to_rect(Cell(0, 0))
    cell_rect.topleft = (0, 0)

    def check_lines(identity, lines, rect, role, vertical=True):
        for text, bounds in zip(lines, renderer.text_rects(lines, rect, role)):
            if bounds.left < rect.left or bounds.right > rect.right or (
                vertical and (bounds.top < rect.top or bounds.bottom > rect.bottom)
            ):
                failures.append(f'{identity}: {role} {text!r} bounds={tuple(bounds)} available={tuple(rect)}')

    for question in bank.questions:
        rect, prompt, buttons = build_question_popup(
            question, renderer, list(range(len(question.choices))),
        )
        records.append({'id': question.id, 'bottom': rect.bottom, 'topic': question.topic,
                        'prompt_lines': len(prompt.lines), 'choice_lines': [len(b.lines) for b in buttons]})
        if not screen_rect.contains(rect):
            failures.append(f'{question.id}: popup bounds={tuple(rect)} outside screen={tuple(screen_rect)}')
        check_lines(question.id, prompt.lines,
                    pygame.Rect(prompt.x, prompt.y, prompt.width, prompt.height), 'prompt')
        previous_bottom = prompt.y + prompt.height
        for button in buttons:
            assert button.rect.top >= previous_bottom + 12
            previous_bottom = button.rect.bottom
            check_lines(question.id, button.lines,
                        button.rect.inflate(-2 * button.padding, -2 * button.padding), 'choice')

        reverse = build_question_popup(question, renderer, list(reversed(range(len(question.choices)))))
        assert reverse[0] == rect, question.id
        assert sorted(b.rect.height for b in reverse[2]) == sorted(b.rect.height for b in buttons)

    labels = sorted({(q.topic, q.subtopic) for q in bank.questions})
    label_max_width = 0
    label_max_height = 0
    border_intrusions = []
    cells = {}
    for style, role in (('normal', 'cell'), ('move', 'cell_move')):
        surface = pygame.Surface(cell_rect.size)
        renderer.fill(surface)
        renderer.cell(surface, surface.get_rect(), style)
        cells[style] = (surface, renderer.color(role))
    label_role = renderer.label_role(board_size)  # the per-size label font (M7.a)
    for topic, subtopic in labels:
        rect = cell_rect.inflate(-2 * LABEL_PADDING, -2 * LABEL_PADDING)
        lines = renderer.wrap(subtopic_display_name(topic, subtopic, board_size=board_size), rect.width, label_role)
        check_lines(f'{topic}/{subtopic}', lines, rect, label_role)
        bounds = renderer.text_rects(lines, rect, label_role)
        label_max_width = max(label_max_width, *(b.width for b in bounds))
        label_max_height = max(label_max_height, bounds[-1].bottom - bounds[0].top)
        # Corner-preserving cuts can exceed the straight border thickness.
        # Check the actual face under every rendered line, for both cell styles.
        for style, (surface, face_color) in cells.items():
            if any(not surface.get_rect().contains(b) for b in bounds) or any(
                surface.get_at((x, y))[:3] != face_color
                for b in bounds for x in range(b.left, b.right) for y in range(b.top, b.bottom)
            ):
                border_intrusions.append({'topic': topic, 'subtopic': subtopic, 'style': style,
                                          'lines': lines, 'width': max(b.width for b in bounds)})
    return {'theme': renderer.theme.name, 'questions': len(records), 'categories': len(labels),
            'worst': max(records, key=lambda r: r['bottom']),
            'preferred_bottom': preferred_bottom,
            'over_preferred_bottom': sum(r['bottom'] > preferred_bottom for r in records),
            'failures': failures, 'label_max_width': label_max_width,
            'label_max_height': label_max_height, 'label_border_intrusions': border_intrusions,
            'worst_muscular': max((r for r in records if r['topic'] == 'muscular_system'),
                                  key=lambda r: r['bottom'])}


def capture_popup(question, renderer, path):
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer.fill(surface)
    rect, prompt, buttons = build_question_popup(question, renderer, list(range(len(question.choices))))
    renderer.panel(surface, rect)

    prompt.draw(surface)
    for button in buttons:
        button.draw(surface)
    pygame.image.save(surface, str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', choices=THEMES, required=True)
    parser.add_argument('--board-size', type=int, choices=(5, 7, 9), default=5)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    pygame.font.init()
    bank = QuestionBank(ROOT / 'data' / 'questions')
    renderer = Renderer(THEMES[args.theme])
    report = audit(bank, renderer, board_size=args.board_size)
    for name in ('worst', 'worst_muscular'):
        question = next(q for q in bank.questions if q.id == report[name]['id'])
        capture_popup(question, renderer, args.out / f'{name}.png')
    text = json.dumps(report, indent=2)
    (args.out / 'fit.json').write_text(text + '\n')
    print(text)
    pygame.font.quit()


if __name__ == '__main__':
    main()
