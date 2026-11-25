"""Run from Red (M8.a and M8.c): Red's chase, its rules, a pure Match, and the
mode played through a PlayState to both outcomes.

Rules (GDD §2, m8.md): the Player starts in the centre and Red in the
bottom-left corner. A right answer moves the Player to the clicked square; a
wrong one steps Red one square toward the Player, and Red landing on the
Player is a loss. The Player escapes, a win, once the moves left are fewer
than Red's distance. The Player may not step onto Red. Red's distance tier
curve is inverted: tier 3 at range, tier 2 at two squares, tier 1 adjacent,
with every tier eligible.
"""

from random import Random

import pygame
import pytest

from board import Board, Cell
from characters import Red
from conftest import (
    REAL_BANK, GameStub, answer, make_play, open_question, play_config,
)
from game_setup import TierPolicy
from match import Match
from modes import get_mode
from questions import QuestionBank
from render import Renderer
from rules import Intent, Outcome, RunFromRedRules
from states.game_over import GameOverState
from theme import FLAT, PIXEL, resolve_accent

SPEC = get_mode('run_from_red').settings_spec()
EASY = SPEC.preset('easy')


def red_match(settings=EASY, seed=1):
    return Match(settings, Random(seed), rules=RunFromRedRules())


def place(match, player, red, moves=None):
    match.player.move_to(player)
    match.npc.move_to(red)
    if moves is not None:
        match.moves_remaining = moves


def farthest_from_red(match):
    """The legal square farthest from Red, first in sorted order on a tie."""
    return max(
        sorted(match.moves),
        key=lambda cell: match.board.distance(cell, match.npc.cell),
    )


# --- Red's chase step -------------------------------------------------------


@pytest.mark.parametrize('size', [5, 7, 9])
def test_chase_step_closes_one_square_from_any_position(size):
    # A sample of positions, not every pair (David, 2026-09-30).
    board = Board(size, size)
    cells = list(board.cells())
    sample = Random(size)
    for _ in range(500):
        red_cell, target = sample.sample(cells, 2)
        step = Red(red_cell).chase_step(board, target, Random(0))
        assert step in board.neighbors(red_cell)
        assert board.distance(step, target) == board.distance(red_cell, target) - 1


def test_chase_step_breaks_ties_from_the_sorted_list_with_the_rng():
    board = Board(5, 5)
    red, target = Cell(0, 0), Cell(2, 2)
    ties = sorted([Cell(0, 1), Cell(1, 0)])
    for seed in range(4):
        rng, reference = Random(seed), Random(seed)
        assert Red(red).chase_step(board, target, rng) == reference.choice(ties)
        assert rng.getstate() == reference.getstate()


def test_chase_step_uses_no_randomness_without_a_tie():
    board = Board(5, 5)
    rng = Random(3)
    before = rng.getstate()
    assert Red(Cell(0, 2)).chase_step(board, Cell(4, 2), rng) == Cell(1, 2)
    assert rng.getstate() == before


def test_red_holds_still_only_on_its_target():
    # On an open grid some step always improves, so Red stands still only
    # when it is already on the square it chases.
    board = Board(5, 5)
    rng = Random(3)
    before = rng.getstate()
    assert Red(Cell(2, 2)).chase_step(board, Cell(2, 2), rng) == Cell(2, 2)
    assert rng.getstate() == before


def test_red_steps_onto_an_adjacent_player():
    board = Board(5, 5)
    assert Red(Cell(2, 2)).chase_step(board, Cell(2, 3), Random(0)) == Cell(2, 3)


# --- starts ------------------------------------------------------------------


@pytest.mark.parametrize('cols,rows,player,red', [
    (5, 5, Cell(2, 2), Cell(0, 4)),
    (7, 7, Cell(3, 3), Cell(0, 6)),
    (9, 9, Cell(4, 4), Cell(0, 8)),
    (7, 5, Cell(3, 2), Cell(0, 4)),  # not square: centre by each axis, corner by rows
])
def test_player_starts_centre_and_red_bottom_left(cols, rows, player, red):
    board = Board(cols, rows)
    rng = Random(0)
    before = rng.getstate()
    assert RunFromRedRules().start_cells(board, rng) == (player, red)
    assert rng.getstate() == before
    assert board.in_bounds(*player) and board.in_bounds(*red)


# --- win, loss, and what a click means ----------------------------------------


def test_escape_needs_moves_left_below_reds_distance():
    match = red_match()
    rules = match.rules
    place(match, Cell(3, 3), Cell(0, 6), moves=6)      # distance 6
    assert rules.outcome(match) is None                 # moves == distance: play on
    match.moves_remaining = 5                           # moves == distance - 1
    assert rules.outcome(match) == Outcome.WIN


def test_a_right_answer_that_leaves_moves_equal_to_distance_plays_on():
    match = red_match()
    place(match, Cell(3, 3), Cell(0, 6), moves=8)       # distance 6
    assert match.resolve(True, Cell(4, 3), Intent.MOVE) is None
    assert (match.moves_remaining, match.rules.pressure_distance(match)) == (7, 7)
    # One more square away leaves 6 moves for 8 squares: Red can't close the gap.
    assert match.resolve(True, Cell(5, 3), Intent.MOVE) == Outcome.WIN


def test_a_catch_on_the_final_move_is_a_loss():
    match = red_match()
    place(match, Cell(3, 3), Cell(3, 4), moves=1)
    assert match.resolve(False, Cell(4, 3), Intent.MOVE) == Outcome.LOSE
    assert match.npc.cell == match.player.cell
    assert match.moves_remaining == 0


def test_the_player_cannot_step_onto_red_and_no_click_is_a_catch():
    match = red_match()
    place(match, Cell(3, 3), Cell(3, 4))
    rules = match.rules
    assert rules.player_blocked(match) == {Cell(3, 4)}
    assert Cell(3, 4) not in match.moves
    assert rules.click_intent(Cell(3, 4), match) is None
    intents = {rules.click_intent(cell, match) for cell in match.board.cells()}
    assert intents == {Intent.MOVE, None}


def test_the_question_comes_from_the_clicked_square():
    match = red_match()
    assert match.rules.question_cell(Cell(4, 3), Intent.MOVE, match) == Cell(4, 3)


# --- tiers --------------------------------------------------------------------


@pytest.mark.parametrize('distance,wanted', [(1, 1), (2, 2), (3, 3), (6, 3), (12, 3)])
def test_distance_policy_wants_hard_questions_at_range(distance, wanted):
    rules = RunFromRedRules()
    assert rules.wanted_tier(TierPolicy.DISTANCE, distance) == wanted
    # The curve changes the preference only; every tier stays eligible.
    assert rules.allowed_tiers(TierPolicy.DISTANCE, distance=distance) is None


def test_other_policies_want_no_tier_and_keep_their_filters():
    rules = RunFromRedRules()
    for distance in (1, 2, 5):
        assert rules.wanted_tier(TierPolicy.ALL, distance) is None
        assert rules.wanted_tier(TierPolicy.TIERS_1_2, distance) is None
    assert rules.allowed_tiers(TierPolicy.ALL) is None
    assert rules.allowed_tiers(TierPolicy.TIERS_1_2, distance=1) == (1, 2)


def test_every_preset_can_start_with_any_single_topic():
    bank = QuestionBank(REAL_BANK)
    topics = bank.topics('anatomy_physiology')
    rules = RunFromRedRules()
    for name, preset in SPEC.presets:
        assert rules.menu_eligible(preset, bank, topics), name
        for topic in topics:
            assert rules.menu_eligible(preset, bank, (topic,)), (name, topic)


# --- a pure Match, no play state ----------------------------------------------


def test_match_scripted_to_the_catch():
    match = red_match()
    start = match.rules.pressure_distance(match)
    assert start == 6
    for answered in range(1, start + 1):
        player = match.player.cell
        result = match.resolve(False, sorted(match.moves)[0], Intent.MOVE)
        assert match.player.cell == player                # a wrong answer leaves the Player put
        assert match.rules.pressure_distance(match) == start - answered
        if answered < start:
            assert result is None
    assert result == Outcome.LOSE
    assert match.moves_remaining == EASY.move_limit - start


def test_match_scripted_to_the_escape():
    match = red_match()
    red = match.npc.cell
    results = []
    while not results or results[-1] is None:
        target = farthest_from_red(match)
        results.append(match.resolve(True, target, Intent.MOVE))
        assert match.player.cell == target and match.npc.cell == red
    assert results[-1] == Outcome.WIN
    assert len(results) == 5                              # 7x7/15: four steps leave 11 moves for 10 squares
    assert match.moves_remaining < match.rules.pressure_distance(match)


# --- the mode played through PlayState (M8.c) ---------------------------------


def red_play(bank, renderer=None, **play_kwargs):
    game = GameStub(bank, renderer)
    return make_play(bank, play_config(mode='run_from_red'), game=game, **play_kwargs)


def test_a_wrong_answer_brings_red_closer_and_a_right_one_moves_only_the_player(fonts, bank):
    state = red_play(bank, reveal_duration_ms=0)
    assert isinstance(state.npc, Red)
    assert (state.player.cell, state.npc.cell) == (Cell(3, 3), Cell(0, 6))

    distance = state.board.distance(state.player.cell, state.npc.cell)
    open_question(state)
    answer(state, False)
    assert state.pending is None
    assert state.player.cell == Cell(3, 3)
    assert state.board.distance(state.player.cell, state.npc.cell) == distance - 1

    red = state.npc.cell
    target = farthest_from_red(state.match)
    open_question(state, target)
    answer(state, True)
    assert state.player.cell == target and state.npc.cell == red
    assert state.moves_remaining == EASY.move_limit - 2


def test_red_catches_the_player_and_the_end_screen_says_so(fonts, bank):
    state = red_play(bank, reveal_duration_ms=0)
    game = state.game
    for _ in range(EASY.move_limit):
        if game.state is not state:
            break
        open_question(state)
        answer(state, False)
    over = game.state
    assert isinstance(over, GameOverState) and over.result == Outcome.LOSE
    assert over.play_state is state
    assert over.result_box.text == 'Red caught you!'
    assert over.replay_button.text == 'Try again'
    assert state.npc.cell == state.player.cell


def test_a_fresh_game_escapes_early_and_the_end_screen_says_so(fonts, bank):
    state = red_play(bank, reveal_duration_ms=0)
    game = state.game
    for _ in range(EASY.move_limit):
        if game.state is not state:
            break
        open_question(state, farthest_from_red(state.match))
        answer(state, True)
    over = game.state
    assert isinstance(over, GameOverState) and over.result == Outcome.WIN
    assert over.result_box.text == 'You got away!'
    assert over.replay_button.text == 'Play again'
    assert state.moves_remaining > 0                      # early: moves were left over
    assert state.moves_remaining < state.board.distance(state.player.cell, state.npc.cell)


@pytest.mark.parametrize('base', [FLAT, PIXEL], ids=['flat', 'pixel'])
def test_the_catching_frame_draws_red_over_the_player(fonts, bank, base):
    # Play draws with the mode's accent renderer, as Game.start_play does.
    play_renderer = Renderer(resolve_accent(base, 'red'))
    state = red_play(bank, renderer=play_renderer, reveal_duration_ms=0)
    assert state.entities == [state.player, state.npc]   # Red last, so on top
    for _ in range(EASY.move_limit):
        if state.game.state is not state:
            break
        open_question(state)
        answer(state, False)
    over = state.game.state
    assert isinstance(over, GameOverState) and over.renderer is play_renderer
    screen = pygame.Surface((1600, 900))
    over.draw(screen)
    centre = state.view.cell_to_rect(state.player.cell).center
    assert screen.get_at(centre)[:3] == play_renderer.color('red')
    assert play_renderer.color('red') != play_renderer.color('player')
