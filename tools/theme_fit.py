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

from constants import LABEL_PADDING
from game_setup import subtopic_display_name
from questions import QuestionBank
from render import Renderer
from states.play import build_question_popup
from theme import THEMES


def audit(bank, renderer):
    failures = []
    records = []
    layout = renderer.theme.layout

    def check_lines(identity, lines, rect, role, vertical=True):
        for text, bounds in zip(lines, renderer.text_rects(lines, rect, role)):
            if bounds.left < rect.left or bounds.right > rect.right or (
                vertical and (bounds.top < rect.top or bounds.bottom > rect.bottom)
            ):
                failures.append(f'{identity}: {role} {text!r} bounds={tuple(bounds)} available={tuple(rect)}')

    for question in bank.questions:
        rect, prompt, buttons, banner = build_question_popup(
            question, renderer, list(range(len(question.choices))),
        )
        records.append({'id': question.id, 'bottom': rect.bottom, 'topic': question.topic,
                        'prompt_lines': len(prompt.lines), 'choice_lines': [len(b.lines) for b in buttons]})
        if rect.bottom > 720:
            failures.append(f'{question.id}: popup bottom {rect.bottom} > 720')
        check_lines(question.id, prompt.lines,
                    pygame.Rect(prompt.x, prompt.y, prompt.width, prompt.height), 'prompt')
        previous_bottom = prompt.y + prompt.height
        for button in buttons:
            assert button.rect.top >= previous_bottom + 12
            previous_bottom = button.rect.bottom
            check_lines(question.id, button.lines,
                        button.rect.inflate(-2 * button.padding, -2 * button.padding), 'choice')
        if banner is not None:
            assert banner.rect.bottom + 12 == prompt.y
            check_lines(question.id, banner.lines,
                        banner.rect.inflate(-2 * layout.banner_side_padding,
                                            -2 * layout.banner_vertical_padding), 'banner')
        reverse = build_question_popup(question, renderer, list(reversed(range(len(question.choices)))))
        assert reverse[0] == rect, question.id
        assert sorted(b.rect.height for b in reverse[2]) == sorted(b.rect.height for b in buttons)

    labels = sorted({(q.topic, q.subtopic) for q in bank.questions})
    label_max_width = 0
    label_max_height = 0
    border_intrusions = []
    cells = {}
    for style, role in (('normal', 'cell'), ('move', 'cell_move')):
        surface = pygame.Surface((128, 128))
        renderer.fill(surface)
        renderer.cell(surface, surface.get_rect(), style)
        cells[style] = (surface, renderer.color(role))
    for topic, subtopic in labels:
        rect = pygame.Rect(LABEL_PADDING, LABEL_PADDING, 128 - 2 * LABEL_PADDING, 128 - 2 * LABEL_PADDING)
        lines = renderer.wrap(subtopic_display_name(topic, subtopic), rect.width, 'label')
        check_lines(f'{topic}/{subtopic}', lines, rect, 'label')
        bounds = renderer.text_rects(lines, rect, 'label')
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
            'over_preferred_700': sum(r['bottom'] > 700 for r in records),
            'failures': failures, 'label_max_width': label_max_width,
            'label_max_height': label_max_height, 'label_border_intrusions': border_intrusions,
            'worst_muscular': max((r for r in records if r['topic'] == 'muscular_system'),
                                  key=lambda r: r['bottom'])}


def capture_popup(question, renderer, path):
    surface = pygame.Surface((1280, 720))
    renderer.fill(surface)
    rect, prompt, buttons, banner = build_question_popup(question, renderer, list(range(len(question.choices))))
    renderer.panel(surface, rect)
    if banner:
        renderer.banner(surface, banner.rect, banner.lines)
    prompt.draw(surface)
    for button in buttons:
        button.draw(surface)
    pygame.image.save(surface, str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', choices=THEMES, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    pygame.font.init()
    bank = QuestionBank(ROOT / 'data' / 'questions')
    renderer = Renderer(THEMES[args.theme])
    report = audit(bank, renderer)
    for name in ('worst', 'worst_muscular'):
        question = next(q for q in bank.questions if q.id == report[name]['id'])
        capture_popup(question, renderer, args.out / f'{name}.png')
    text = json.dumps(report, indent=2)
    (args.out / 'fit.json').write_text(text + '\n')
    print(text)
    pygame.font.quit()


if __name__ == '__main__':
    main()
