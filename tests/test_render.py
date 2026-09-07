"""Flat primitives, role-based layout, and the renderer boundary."""

import ast
from dataclasses import replace
from pathlib import Path

import pygame
import pytest

from render import Renderer, word_wrap
from theme import FLAT, Alignment, SpriteSpec
from ui import Button, Checkbox, TextBox


@pytest.fixture
def renderer():
    pygame.font.init()
    yield Renderer(FLAT)
    pygame.font.quit()


@pytest.mark.parametrize('role', ['label', 'choice'])
@pytest.mark.parametrize('lines', [['One line'], ['Short', 'A longer line', 'Last']])
def test_centered_text_layout(renderer, role, lines):
    rect = pygame.Rect(17, 23, 480, 117)
    result = renderer.text_rects(lines, rect, role)
    assert all(line.centerx == rect.centerx for line in result)
    assert abs((result[0].top + result[-1].bottom) / 2 - rect.centery) <= 1
    for index, (text, line) in enumerate(zip(lines, result)):
        rendered = renderer.font(role).render(text, True, renderer.color('text'))
        assert line.size == rendered.get_size()
        assert line.top == result[0].top + index * renderer.line_height(role)


@pytest.mark.parametrize('role', ['prompt', 'button', 'result', 'title', 'counter', 'checkbox'])
def test_other_roles_stay_top_left(renderer, role):
    rect = pygame.Rect(17, 23, 480, 117)
    result = renderer.text_rects(['First', 'Second'], rect, role)
    assert result[0].topleft == rect.topleft
    assert result[1].topleft == (rect.left, rect.top + renderer.line_height(role))
    assert renderer.text_rects([], rect, role) == []
    centered = renderer.text_rects(['Title'], rect, role, Alignment('center', 'top'))
    assert centered[0].centerx == rect.centerx
    assert centered[0].top == rect.top


def test_font_reuse_and_wrapping(renderer):
    assert renderer.font('choice') is renderer.font('prompt')
    assert renderer.font('button') is renderer.font('counter')
    assert renderer.font('result') is not renderer.font('title')
    assert len({id(font) for font in renderer.fonts.values()}) == 7
    for role in renderer.fonts:
        assert renderer.measure('Text', role) == renderer.font(role).size('Text')
        assert renderer.line_height(role) == renderer.font(role).get_linesize()
    assert renderer.wrap('  one\n two   three ', 1, 'prompt') == ['one', 'two', 'three']
    assert renderer.wrap('   ', 100, 'prompt') == []
    assert word_wrap('one two', 1000, renderer.font('prompt')) == ['one two']


def test_flat_primitives_match_original_pixels(renderer):
    actual = pygame.Surface((160, 160))
    expected = pygame.Surface(actual.get_size())
    rect = pygame.Rect(20, 20, 120, 120)

    def reset():
        renderer.fill(actual)
        expected.fill((24, 26, 32))

    def equal():
        assert pygame.image.tobytes(actual, 'RGB') == pygame.image.tobytes(expected, 'RGB')

    reset()
    equal()
    renderer.panel(actual, rect)
    pygame.draw.rect(expected, (58, 64, 78), rect)
    pygame.draw.rect(expected, (120, 130, 148), rect, width=2)
    equal()
    for style, color in [('normal', (60, 88, 90)), ('inactive', (75, 78, 86)),
                         ('correct', (0, 100, 70)), ('incorrect', (150, 45, 35))]:
        reset()
        renderer.button(actual, rect, style)
        pygame.draw.rect(expected, color, rect)
        equal()
    for style, color in [('normal', (58, 64, 78)), ('move', (60, 88, 90))]:
        reset()
        renderer.cell(actual, rect, style)
        pygame.draw.rect(expected, color, rect)
        pygame.draw.rect(expected, (120, 130, 148), rect, width=1)
        equal()
    for style, color, width in [('hover', (120, 130, 148), 5), ('selected', (255, 0, 0), 4)]:
        reset()
        renderer.cell(actual, rect, style)
        pygame.draw.rect(expected, color, rect, width=width)
        equal()
    for checked in (False, True):
        reset()
        renderer.checkbox(actual, rect, checked)
        pygame.draw.rect(expected, (245, 245, 245), rect, width=2)
        if checked:
            pygame.draw.rect(expected, (245, 245, 245), rect.inflate(-8, -8))
        equal()
    for shape, role in [('circle', 'player'), ('square', 'blue')]:
        reset()
        renderer.sprite(actual, rect, shape, role)
        margin = rect.width // 6
        if shape == 'circle':
            pygame.draw.circle(expected, (230, 159, 0), rect.center, margin)
        else:
            pygame.draw.rect(expected, (0, 114, 178), rect.inflate(-3 * margin, -3 * margin))
        equal()
    reset()
    renderer.button(actual, rect)
    pygame.draw.rect(expected, (60, 88, 90), rect)
    equal()


def test_text_pixels_and_palette_variant(renderer):
    variant = Renderer(replace(FLAT, palette=replace(
        FLAT.palette, background=(1, 2, 3), choice_text=(220, 110, 50), button=(10, 20, 30),
    )))
    rect = pygame.Rect(0, 0, 240, 80)
    actual = pygame.Surface(rect.size)
    expected = pygame.Surface(rect.size)
    variant.fill(actual)
    assert actual.get_at((0, 0))[:3] == (1, 2, 3)
    Button(rect.copy(), 'Answer', variant, 'choice').draw(actual)
    expected.fill((10, 20, 30))
    rendered = variant.font('choice').render('Answer', True, (220, 110, 50))
    expected.blit(rendered, rendered.get_rect(center=rect.center))
    assert pygame.image.tobytes(actual, 'RGB') == pygame.image.tobytes(expected, 'RGB')
    actual.fill((0, 0, 0))
    expected.fill((0, 0, 0))
    renderer.text(actual, 'Prompt', rect, 'prompt')
    expected.blit(renderer.font('prompt').render('Prompt', True, (245, 245, 245)), rect)
    assert pygame.image.tobytes(actual, 'RGB') == pygame.image.tobytes(expected, 'RGB')


@pytest.mark.parametrize('text', ['Answer', 'Answer Answer'])
@pytest.mark.parametrize('highlight', [None, 'correct', 'incorrect'])
def test_choice_centers_actual_rendered_surfaces_in_44px_button(renderer, text, highlight):
    font = renderer.font('choice')
    answer = font.render('Answer', True, renderer.color('choice_text'))
    assert renderer.measure('Answer', 'choice') == (73, 19)
    assert answer.get_size() == (73, 21)
    rect = pygame.Rect(10, 20, 100, 44)
    button = Button(rect.copy(), text, renderer, 'choice')
    button.highlight = highlight
    assert button.lines == ['Answer'] * len(text.split())
    assert button.rect == rect
    assert button.height == len(button.lines) * font.get_linesize()
    assert button.is_clicked(rect.center)

    rendered = [font.render(line, True, renderer.color('choice_text')) for line in button.lines]
    sizes = [line.get_size() for line in rendered]
    block_height = (len(rendered) - 1) * font.get_linesize() + sizes[-1][1]
    top = rect.centery - block_height // 2
    expected_rects = [
        pygame.Rect(rect.centerx - width // 2, top + index * font.get_linesize(), width, height)
        for index, (width, height) in enumerate(sizes)
    ]
    assert renderer.text_rects(button.lines, rect, 'choice') == expected_rects
    assert abs((expected_rects[0].top + expected_rects[-1].bottom) / 2 - rect.centery) <= 0.5

    actual = pygame.Surface((120, 90))
    expected = pygame.Surface(actual.get_size())
    actual.fill((1, 2, 3))
    expected.fill((1, 2, 3))
    pygame.draw.rect(expected, renderer.color(highlight or 'button'), rect)
    for line, line_rect in zip(rendered, expected_rects):
        expected.blit(line, line_rect)
    button.draw(actual)
    assert pygame.image.tobytes(actual, 'RGB') == pygame.image.tobytes(expected, 'RGB')
    assert button.rect == rect


@pytest.mark.parametrize('lines', [[], ['Answer'], ['Answer', 'Second']])
def test_wrapped_text_renders_each_line_only_once(renderer, monkeypatch, lines):
    font = renderer.font('choice')
    calls = []

    class RecordingFont:
        def render(self, text, antialias, color):
            calls.append((text, antialias, color))
            return font.render(text, antialias, color)

        def get_linesize(self):
            return font.get_linesize()

        def size(self, text):
            return font.size(text)

    monkeypatch.setitem(renderer.fonts, 'choice', RecordingFont())
    renderer.wrapped_text(
        pygame.Surface((120, 90)), lines, pygame.Rect(10, 20, 100, 44),
        'choice', 'choice_text',
    )
    assert calls == [(line, True, renderer.color('choice_text')) for line in lines]


def test_clip_restored_on_normal_exit_and_error(renderer):
    surface = pygame.Surface((100, 100))
    original = pygame.Rect(5, 6, 80, 70)
    surface.set_clip(original)
    with renderer.clip(surface, pygame.Rect(10, 10, 20, 20)):
        assert surface.get_clip() == pygame.Rect(10, 10, 20, 20)
    assert surface.get_clip() == original
    with pytest.raises(RuntimeError):
        with renderer.clip(surface, pygame.Rect(10, 10, 20, 20)):
            with renderer.clip(surface, pygame.Rect(12, 12, 5, 5)):
                raise RuntimeError('draw failed')
    assert surface.get_clip() == original


def test_unsupported_assets_fail_explicitly(renderer):
    theme = replace(FLAT, sprites=(('blue', SpriteSpec(Path('unused.png'), (0, 0, 8, 8))),))
    with pytest.raises(NotImplementedError, match='Sprite'):
        Renderer(theme)


def test_widget_geometry_and_checkbox_scrolling(renderer):
    text = 'A long answer that wraps across many lines'
    button = Button(pygame.Rect(10, 20, 80, 44), text, renderer, 'choice')
    assert button.height == len(button.lines) * renderer.line_height('choice')
    assert button.rect.height == max(44, button.height)
    box = TextBox(text, renderer, 'prompt', 10, 20, 80)
    assert box.lines == button.lines
    assert box.height == button.height
    checkbox = Checkbox(pygame.Rect(10, 50, 30, 30), 'All', renderer, checked=True)
    legacy_label = renderer.font('checkbox').render('All', True, renderer.color('text'))
    legacy_rect = legacy_label.get_rect(midleft=(52, 65))
    assert checkbox.label_rect == legacy_rect
    assert checkbox.hit_rect == checkbox.rect.union(legacy_rect)
    assert checkbox.is_clicked(legacy_rect.center)
    actual, expected = pygame.Surface((150, 100)), pygame.Surface((150, 100))
    actual.fill((0, 0, 0))
    expected.fill((0, 0, 0))
    checkbox.draw(actual, offset_y=20)
    pygame.draw.rect(expected, renderer.color('text'), checkbox.rect.move(0, -20), width=2)
    pygame.draw.rect(expected, renderer.color('text'), checkbox.rect.move(0, -20).inflate(-8, -8))
    expected.blit(legacy_label, legacy_rect.move(0, -20))
    assert pygame.image.tobytes(actual, 'RGB') == pygame.image.tobytes(expected, 'RGB')
    checkbox.toggle()
    assert not checkbox.checked


def test_widgets_and_states_do_not_draw_or_load_fonts():
    root = Path(__file__).resolve().parents[1]
    for path in [root / 'ui.py', root / 'board_view.py', *sorted((root / 'states').glob('*.py'))]:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                assert not name.startswith(('pygame.draw.', 'pygame.font.')), (path, name)
                assert not name.endswith(('.blit', '.set_clip', '.get_clip', '.render')), (path, name)
                if name.endswith('.fill'):
                    assert name == 'self.renderer.fill', (path, name)
