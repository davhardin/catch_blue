"""Mode registration and mode-specific settings data."""

from dataclasses import dataclass

from game_setup import Settings, TierPolicy
from rules import CatchBlueRules, Rules

Options = tuple[tuple[int | str, str], ...]
RowSpec = tuple[str, str, Options]


@dataclass(frozen=True)
class SettingRow:
    """One settings row; include_current is for integer-valued rows."""

    key: str
    label: str
    options: Options
    include_current: bool = False

    def options_for(self, settings: Settings) -> Options:
        current = getattr(settings, self.key)
        if not self.include_current or any(
            value == current for value, _ in self.options
        ):
            return self.options

        return tuple(sorted(
            (*self.options, (current, str(current))),
            key=lambda option: int(option[0]),
        ))


@dataclass(frozen=True)
class ModeSettings:
    """Mode-local presets and rows.

    Each preset value must appear in its row's declared options.
    """

    presets: tuple[tuple[str, Settings], ...]
    default_preset: str
    rows: tuple[SettingRow, ...]

    def preset(self, name: str) -> Settings:
        return dict(self.presets)[name]

    @property
    def default(self) -> Settings:
        return self.preset(self.default_preset)

    def preset_for(self, settings: Settings) -> str:
        for name, preset in self.presets:
            if settings == preset:
                return name
        return 'custom'

    def row_specs(self, settings: Settings) -> tuple[RowSpec, ...]:
        preset_options = tuple(
            (name, name.title()) for name, _ in self.presets
        )
        return (
            ('preset', 'Difficulty', (*preset_options, ('custom', 'Custom'))),
            *(
                (row.key, row.label, row.options_for(settings))
                for row in self.rows
            ),
        )


@dataclass(frozen=True)
class Mode:
    key: str
    display_name: str
    npc_color_role: str
    accent: str
    rules_factory: type[Rules] | None = None
    settings: ModeSettings | None = None

    @property
    def active(self) -> bool:
        return self.rules_factory is not None and self.settings is not None

    def make_rules(self) -> Rules:
        if not self.active or self.rules_factory is None:
            raise ValueError(f'Game mode is not available: {self.key}')
        return self.rules_factory()

    def settings_spec(self) -> ModeSettings:
        if not self.active or self.settings is None:
            raise ValueError(f'Game mode is not available: {self.key}')
        return self.settings


CATCH_BLUE_SETTINGS = ModeSettings(
    presets=(
        ('easy', Settings(
            board_size=5,
            move_limit=15,
            tier_policy=TierPolicy.TIERS_1_2,
        )),
        ('medium', Settings(
            board_size=5,
            move_limit=15,
            tier_policy=TierPolicy.DISTANCE,
        )),
        ('hard', Settings(
            board_size=7,
            move_limit=20,
            tier_policy=TierPolicy.DISTANCE,
        )),
    ),
    default_preset='easy',
    rows=(
        SettingRow(
            'board_size',
            'Board size',
            ((5, '5 x 5'), (7, '7 x 7'), (9, '9 x 9')),
        ),
        SettingRow(
            'move_limit',
            'Move limit',
            tuple((value, str(value)) for value in (10, 15, 20, 25, 30)),
            include_current=True,
        ),
        SettingRow(
            'tier_policy',
            'Question tiers',
            (
                (TierPolicy.TIERS_1_2, 'T1 + T2'),
                (TierPolicy.ALL, 'All tiers'),
                (TierPolicy.DISTANCE, 'Distance based'),
            ),
        ),
    ),
)

DEFAULT_MODE = 'catch_blue'

MODES = {
    'catch_blue': Mode(
        key='catch_blue',
        display_name='Catch Blue',
        npc_color_role='blue',
        accent='blue',
        rules_factory=CatchBlueRules,
        settings=CATCH_BLUE_SETTINGS,
    ),
    'run_from_red': Mode(
        key='run_from_red',
        display_name='Run from Red',
        npc_color_role='red',
        accent='red',
    ),
}


def get_mode(key: str) -> Mode:
    try:
        return MODES[key]
    except KeyError:
        raise ValueError(f'Unknown game mode: {key}') from None
