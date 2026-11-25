"""The mode registry's contract (M8.b): every active mode is complete data.

Adding a mode should be one registry entry, so each active entry must carry
everything the menus, the Settings screen, and the end screen read from it.
"""

from dataclasses import replace

import pytest

from modes import DEFAULT_MODE, MODES, get_mode
from rules import Outcome
from theme import ACCENT_KEYS

ACTIVE = [key for key, mode in MODES.items() if mode.active]


def test_active_modes_are_catch_blue_and_run_from_red():
    assert ACTIVE == ['catch_blue', 'run_from_red']
    assert DEFAULT_MODE in ACTIVE
    with pytest.raises(ValueError, match='Unknown game mode'):
        get_mode('not_a_mode')


@pytest.mark.parametrize('key', ACTIVE)
def test_active_mode_has_complete_presets_rows_and_copy(key):
    mode = get_mode(key)
    assert mode.key == key and mode.display_name
    assert mode.accent in ACCENT_KEYS
    assert isinstance(mode.make_rules(), mode.rules_factory)

    spec = mode.settings_spec()
    names = [name for name, _ in spec.presets]
    assert len(names) == len(set(names)) and 'custom' not in names
    assert spec.default_preset in names
    assert spec.default == spec.preset(spec.default_preset)

    # Every preset value is one its row offers, so picking a preset always
    # selects a real button on the Settings screen.
    for name, preset in spec.presets:
        for row in spec.rows:
            offered = [value for value, _ in row.options]
            assert getattr(preset, row.key) in offered, (key, name, row.key)

    # Presets are told apart by value, so the preset name is derived, never stored.
    for name, preset in spec.presets:
        assert spec.preset_for(preset) == name
        assert spec.preset_for(replace(preset, move_limit=preset.move_limit + 1)) == 'custom'
    assert len({preset for _, preset in spec.presets}) == len(names)

    # The Settings screen's first row picks the preset and shows Custom.
    preset_row = spec.row_specs(spec.default)[0]
    assert preset_row[0] == 'preset'
    assert [value for value, _ in preset_row[2]] == [*names, 'custom']

    # The end screen has copy for both outcomes, and they differ.
    messages = mode.make_rules().result_messages
    assert set(messages) == {Outcome.WIN, Outcome.LOSE}
    assert all(messages.values()) and messages[Outcome.WIN] != messages[Outcome.LOSE]


def test_modes_have_their_own_accents():
    accents = [get_mode(key).accent for key in ACTIVE]
    assert len(accents) == len(set(accents))
    assert get_mode('catch_blue').accent == 'blue'
    assert get_mode('run_from_red').accent == 'red'
