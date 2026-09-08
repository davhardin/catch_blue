"""M6.f.8 — lifted tiles and buttons.

The lift is theme data that defaults to zero, so the flat theme must draw
exactly as before, and on the pixel theme lifted things move in whole
skin-scale pixels, hit-testing stays on the grid, and a legal-move face is
visibly lighter than a normal one.
"""

from pathlib import Path
from random import Random
from types import SimpleNamespace

import pygame
import pytest

from board import Board, Cell
from board_view import BoardView
from constants import BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_REGION, SCREEN_HEIGHT, SCREEN_WIDTH
from game_setup import GameConfig
from questions import QuestionBank
from render import Renderer
from states.menus import GameSelectState, TopicsState
from states.play import PlayState
from theme import FLAT, PIXEL, CellLift
from ui import Button

SCREEN = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)


@pytest.fixture(params=[FLAT, PIXEL], ids=['flat', 'pixel'])
def renderer(request):
    pygame.font.init()
    yield Renderer(request.param)
    pygame.font.quit()


@pytest.fixture(scope='module')
def bank():
    return QuestionBank(Path(__file__).resolve().parents[1] / 'data' / 'questions')


def make_play(renderer, bank, seed=17):
    game = SimpleNamespace(renderer=renderer, change_state=lambda s: None)
    return PlayState(game, bank, GameConfig('catch_blue', 'anatomy_physiology', ('cells',)),
                     Random(seed), reveal_duration_ms=0)


def settle(state, ms=1000):
    state.update(ms)


def luminance(color):
    r, g, b = color[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def mean_face_luminance(surface, rect):
    face = rect.inflate(-rect.width // 2, -rect.height // 2)
    total = 0
    count = 0
    for y in range(face.top, face.bottom, 4):
        for x in range(face.left, face.right, 4):
            total += luminance(surface.get_at((x, y)))
            count += 1
    return total / count


# --- theme data ---------------------------------------------------------------

def test_lift_defaults_to_zero_and_pixel_lifts_are_scale_multiples():
    assert CellLift() == CellLift(0, 0, 0)
    for lift in (FLAT.cell_lift, FLAT.answer_lift, FLAT.menu_lift):
        assert lift == CellLift()
    scale = PIXEL.skin.scale
    for lift in (PIXEL.cell_lift, PIXEL.answer_lift, PIXEL.menu_lift):
        assert lift.rest_px > 0 and lift.hover_px > lift.rest_px and lift.pop_ms > 0
        assert lift.rest_px % scale == 0 and lift.hover_px % scale == 0


# --- board view ---------------------------------------------------------------

def test_board_lifts_settle_to_rest_hover_and_pressed(renderer, bank):
    state = make_play(renderer, bank)
    view = state.view
    lift = renderer.theme.cell_lift
    step = renderer.theme.skin.scale if renderer.theme.skin else 1
    occupied = {e.cell for e in state.entities}
    legal = sorted(state.moves)
    hovered, other = legal[0], legal[1]
    not_legal = next(c for c in state.board.cells() if c not in state.moves and c not in occupied)

    # Nothing has moved yet: everything sits at zero.
    assert all(view.lift_for(c, selected=None, occupied=occupied) == 0 for c in state.board.cells())

    state.hovering = hovered
    settle(state)
    assert view.lift_for(hovered, selected=None, occupied=occupied) == lift.hover_px
    assert view.lift_for(other, selected=None, occupied=occupied) == lift.rest_px
    assert view.lift_for(not_legal, selected=None, occupied=occupied) == 0
    for cell in state.board.cells():
        assert view.lift_for(cell, selected=None, occupied=occupied) % step == 0

    # Hovering a non-legal cell lifts nothing extra.
    state.hovering = not_legal
    settle(state)
    assert view.lift_for(not_legal, selected=None, occupied=occupied) == 0
    assert view.lift_for(hovered, selected=None, occupied=occupied) == lift.rest_px

    # Selection presses the tile down immediately, even mid-tween.
    state.hovering = hovered
    state.update(1)
    assert view.lift_for(hovered, selected=hovered, occupied=occupied) == 0
    # Occupied cells never lift.
    assert all(view.lift_for(c, selected=None, occupied=occupied) == 0 for c in occupied)


def test_board_pop_is_a_tween_not_a_jump(bank):
    pygame.font.init()
    try:
        state = make_play(Renderer(PIXEL), bank)
        lift = PIXEL.cell_lift
        occupied = {e.cell for e in state.entities}
        hovered = sorted(state.moves)[0]
        state.hovering = hovered
        seen = []
        for _ in range(lift.pop_ms // 16 + 4):
            state.update(16)
            seen.append(state.view.lift_for(hovered, selected=None, occupied=occupied))
        assert seen[0] < lift.hover_px, 'the pop should take more than one frame'
        assert seen[-1] == lift.hover_px
        assert seen == sorted(seen), 'the lift only rises while hovered'
    finally:
        pygame.font.quit()


def test_hit_testing_stays_on_the_grid_when_popped(bank):
    pygame.font.init()
    try:
        state = make_play(Renderer(PIXEL), bank)
        hovered = sorted(state.moves)[0]
        state.hovering = hovered
        settle(state)
        rect = state.view.cell_to_rect(hovered)
        # The drawn tile now extends hover_px above the grid rect; a click in
        # that strip belongs to the cell above, exactly as before the lift.
        above = state.view.pixel_to_cell(rect.centerx, rect.top - 1)
        assert above != hovered
        assert state.view.pixel_to_cell(rect.centerx, rect.top) == hovered
    finally:
        pygame.font.quit()


def test_pixel_lifted_tile_draws_higher_with_a_shadow_below(bank):
    pygame.font.init()
    try:
        renderer = Renderer(PIXEL)
        state = make_play(renderer, bank)
        occupied = {e.cell for e in state.entities}
        hovered = sorted(state.moves)[0]
        rect = state.view.cell_to_rect(hovered)
        flat_screen = pygame.Surface(SCREEN.size)
        state.draw(flat_screen)  # no update yet: lift 0
        state.hovering = hovered
        settle(state)
        popped = pygame.Surface(SCREEN.size)
        state.draw(popped)
        lift = PIXEL.cell_lift.hover_px
        # The tile's top row moved up by the lift...
        assert popped.get_at((rect.centerx, rect.top - lift)) == flat_screen.get_at((rect.centerx, rect.top))
        # ...and the socket colour shows in the strip the tile vacated.
        socket = renderer.color('panel_line')
        assert popped.get_at((rect.centerx, rect.bottom - 1))[:3] == socket
        assert flat_screen.get_at((rect.centerx, rect.bottom - 1))[:3] != socket
    finally:
        pygame.font.quit()


def test_move_face_is_lighter_than_normal_face(renderer):
    surface = pygame.Surface((400, 200))
    renderer.fill(surface)
    normal = pygame.Rect(20, 20, 160, 160)
    move = pygame.Rect(220, 20, 160, 160)
    renderer.cell(surface, normal, 'normal')
    renderer.cell(surface, move, 'move')
    gap = mean_face_luminance(surface, move) - mean_face_luminance(surface, normal)
    # Flat's pre-existing faces differ by ~18 (and by hue); pixel was retuned
    # in M6.f.8 to clear a wider margin. Both must stay separable by luminance.
    floor = 20 if renderer.theme is PIXEL else 15
    assert abs(gap) >= floor, f'legal-move face must differ by luminance, got {gap:.1f}'


def test_flat_board_draw_is_unchanged_by_the_lift_machinery(bank):
    pygame.font.init()
    try:
        state = make_play(Renderer(FLAT), bank)
        before = pygame.Surface(SCREEN.size)
        state.draw(before)
        state.hovering = sorted(state.moves)[0]
        settle(state)
        after = pygame.Surface(SCREEN.size)
        state.draw(after)
        # Flat keeps its hover ring, so compare everything except that ring's cell.
        ring = state.view.cell_to_rect(state.hovering)
        for surf in (before, after):
            surf.fill((0, 0, 0), ring)
        assert pygame.image.tobytes(before, 'RGB') == pygame.image.tobytes(after, 'RGB')
    finally:
        pygame.font.quit()


# --- buttons ------------------------------------------------------------------

def test_answer_buttons_lift_rest_pop_and_press(renderer, bank):
    state = make_play(renderer, bank)
    lift = renderer.theme.answer_lift
    target = sorted(state.moves)[0]
    state.handle_events([pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=state.view.cell_to_rect(target).center)])
    assert state.pending is not None
    buttons = state.answer_buttons
    settle(state)
    assert all(b.draw_lift == lift.rest_px for b in buttons)
    state.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=buttons[1].rect.center)])
    settle(state)
    assert buttons[1].draw_lift == lift.hover_px
    assert all(b.draw_lift == lift.rest_px for b in buttons if b is not buttons[1])
    # is_clicked uses the resting rect, not the lifted one.
    assert buttons[1].is_clicked(buttons[1].rect.center)
    assert not buttons[1].is_clicked((buttons[1].rect.centerx, buttons[1].rect.top - 1))


def test_reveal_presses_the_pick_and_freezes_the_rest(bank):
    pygame.font.init()
    try:
        renderer = Renderer(PIXEL)
        state = PlayState(SimpleNamespace(renderer=renderer, change_state=lambda s: None), bank,
                          GameConfig('catch_blue', 'anatomy_physiology', ('cells',)),
                          Random(17), reveal_duration_ms=1300)
        lift = PIXEL.answer_lift
        target = sorted(state.moves)[0]
        state.handle_events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=state.view.cell_to_rect(target).center)])
        buttons = state.answer_buttons
        state.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=buttons[2].rect.center)])
        settle(state)
        assert buttons[2].draw_lift == lift.hover_px
        state.handle_events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=buttons[2].rect.center)])
        assert state.reveal is not None
        assert buttons[2].draw_lift == 0
        assert all(b.draw_lift == lift.rest_px for b in buttons if b is not buttons[2])
        state.update(500)
        assert buttons[2].draw_lift == 0
        assert all(b.draw_lift == lift.rest_px for b in buttons if b is not buttons[2])
    finally:
        pygame.font.quit()


def test_menu_buttons_pop_on_hover_and_inactive_never_lift(renderer, bank):
    game = SimpleNamespace(renderer=renderer, change_state=lambda s: None)
    state = GameSelectState(game, bank)
    lift = renderer.theme.menu_lift
    active, inactive = state.catch_blue_button, state.run_from_red_button
    state.update(1000)
    assert active.draw_lift == lift.rest_px
    assert inactive.draw_lift == 0
    state.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=active.rect.center)])
    state.update(1000)
    assert active.draw_lift == lift.hover_px
    state.handle_events([pygame.event.Event(pygame.WINDOWLEAVE)])
    state.update(1000)
    assert active.draw_lift == lift.rest_px
    state.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=inactive.rect.center)])
    state.update(1000)
    assert inactive.draw_lift == 0


def test_start_button_drops_when_disabled(renderer, bank):
    game = SimpleNamespace(renderer=renderer, change_state=lambda s: None, start_play=lambda *a: None)
    state = TopicsState(game, bank, 'catch_blue', 'anatomy_physiology')
    state.update(1000)
    assert state.start_button.draw_lift == renderer.theme.menu_lift.rest_px
    all_box = state.all_checkbox
    state.handle_events([pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=all_box.hit_rect.center)])
    assert not state.start_button.active
    assert state.start_button.draw_lift == 0
    state.update(1000)
    assert state.start_button.draw_lift == 0


def test_button_with_explicit_zero_lift_never_moves(renderer):
    button = Button(pygame.Rect(10, 10, 300, 60), 'Still', renderer, lift=CellLift())
    button.update_lift(1000, hovered=True)
    assert button.draw_lift == 0
