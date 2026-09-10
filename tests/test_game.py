"""Exercise the frame loop without initializing pygame or opening a window."""

import pygame
import pytest

from game import Game


@pytest.mark.parametrize("transition", [False, True])
def test_frame_updates_before_input_and_does_not_forward_stale_events(monkeypatch, transition):
    game = Game.__new__(Game)
    game.screen = object()
    game.fps = 60
    game.running = True
    calls = []
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10))
    batches = iter([[event], [pygame.event.Event(pygame.QUIT)]])

    class Clock:
        def tick(self, fps):
            assert fps == 60
            calls.append("tick")
            return 37

    class State:
        def __init__(self, name):
            self.name = name

        def update(self, dt_ms):
            calls.append((self.name, "update", dt_ms))
            if self is original and transition:
                game.change_state(replacement)

        def handle_events(self, events):
            assert all(item.type != pygame.QUIT for item in events)
            calls.append((self.name, "input", list(events)))

        def draw(self, screen):
            assert screen is game.screen
            calls.append((self.name, "draw"))

    original = State("original")
    replacement = State("replacement")
    game.state = original
    game.clock = Clock()

    def get_events():
        batch = next(batches)
        calls.append("quit_events" if batch[0].type == pygame.QUIT else "events")
        return batch

    monkeypatch.setattr(pygame.event, "get", get_events)
    monkeypatch.setattr(pygame.display, "flip", lambda: calls.append("flip"))
    monkeypatch.setattr(pygame, "quit", lambda: calls.append("quit"))

    game.run()

    expected = ["tick", "events", ("original", "update", 37)]
    if not transition:
        expected.append(("original", "input", [event]))
    expected.extend([("replacement" if transition else "original", "draw"), "flip"])
    assert calls[:len(expected)] == expected
    assert calls[len(expected):len(expected) + 2] == ["tick", "quit_events"]
    assert calls[-1] == "quit"
    assert calls.count("quit") == 1
    assert game.running is False
    input_batches = [call[2] for call in calls if isinstance(call, tuple) and call[1] == "input"]
    assert sum(event in batch for batch in input_batches) == (0 if transition else 1)


def test_step_reports_running_and_leaves_quit_to_the_caller(monkeypatch):
    game = Game.__new__(Game)
    game.screen = object()
    game.fps = 60
    game.running = True
    calls = []
    batches = iter([[], [pygame.event.Event(pygame.QUIT)]])

    class Clock:
        def tick(self, fps):
            return 16

    class State:
        def update(self, dt_ms):
            calls.append("update")

        def handle_events(self, events):
            calls.append("input")

        def draw(self, screen):
            calls.append("draw")

    game.state = State()
    game.clock = Clock()
    monkeypatch.setattr(pygame.event, "get", lambda: next(batches))
    monkeypatch.setattr(pygame.display, "flip", lambda: calls.append("flip"))
    monkeypatch.setattr(pygame, "quit", lambda: calls.append("quit"))

    assert game.step() is True
    assert calls == ["update", "input", "draw", "flip"]
    assert game.step() is False
    assert game.running is False
    assert "quit" not in calls
