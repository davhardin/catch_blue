"""CLI validation precedes bank loading and game initialization."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import main
from game import Game
from theme import DEFAULT_THEME, FLAT, PIXEL, THEMES


@pytest.fixture
def startup(monkeypatch):
    bank = SimpleNamespace(subjects=['anatomy_physiology'])
    load = Mock(return_value=bank)
    game = Mock()
    monkeypatch.setattr(main, 'QuestionBank', load)
    monkeypatch.setattr(main, 'Game', game)
    return bank, load, game


@pytest.mark.parametrize(('argv', 'selected'), [
    ([], PIXEL),
    *[(['--theme', name], theme) for name, theme in sorted(THEMES.items())],
])
def test_theme_selection_passes_registry_identity(startup, argv, selected):
    bank, load, game = startup
    main.main(argv)
    load.assert_called_once_with(Path(main.__file__).resolve().parent / 'data' / 'questions')
    game.assert_called_once_with(bank, theme=selected)
    assert game.call_args.kwargs['theme'] is selected
    game.return_value.run.assert_called_once_with()
    assert DEFAULT_THEME == 'pixel'


@pytest.mark.parametrize(('argv', 'code'), [
    (['--help'], 0), (['--theme', 'unknown'], 2), (['--theme'], 2),
])
def test_cli_exits_before_loading_bank(startup, capsys, argv, code):
    _, load, game = startup
    with pytest.raises(SystemExit) as error:
        main.main(argv)
    assert error.value.code == code
    output = capsys.readouterr()
    assert '{' + ','.join(sorted(THEMES)) + '}' in output.out + output.err
    load.assert_not_called()
    game.assert_not_called()


def test_choices_are_taken_from_registry_and_sorted(startup, monkeypatch, capsys):
    monkeypatch.setattr(main, 'THEMES', {'zeta': FLAT, 'pixel': PIXEL, 'alpha': FLAT})
    with pytest.raises(SystemExit) as error:
        main.main(['--help'])
    assert error.value.code == 0
    assert '--theme {alpha,pixel,zeta}' in capsys.readouterr().out
    startup[1].assert_not_called()
    startup[2].assert_not_called()


def test_none_argv_reads_process_arguments(startup, monkeypatch):
    monkeypatch.setattr('sys.argv', ['catch-blue', '--theme', 'flat'])
    main.main()
    assert startup[2].call_args.kwargs['theme'] is FLAT


def test_question_path_is_resolved_and_independent_of_cwd(startup, monkeypatch, tmp_path):
    expected = Path(main.__file__).resolve().parent / 'data' / 'questions'
    monkeypatch.chdir(tmp_path)
    main.main([])
    startup[1].assert_called_once_with(expected)
    assert expected.is_absolute()
    assert expected.is_dir()


def test_empty_bank_fails_before_game_creation(startup):
    bank, load, game = startup
    bank.subjects = []
    with pytest.raises(ValueError, match='The question bank contains no subjects'):
        main.main([])
    load.assert_called_once()
    game.assert_not_called()


def test_lower_level_game_default_remains_flat():
    assert Game.__init__.__kwdefaults__['theme'] is FLAT
