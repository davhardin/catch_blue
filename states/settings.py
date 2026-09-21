from dataclasses import replace

import pygame

from constants import (
    SCREEN_WIDTH, MENU_BACK_LEFT, MENU_BACK_WIDTH, MENU_START_TOP, MENU_BUTTON_HEIGHT,
    SETTINGS_LEFT, SETTINGS_WIDTH, SETTINGS_TITLE_TOP, SETTINGS_FIRST_ROW_TOP,
    SETTINGS_LABEL_GAP, SETTINGS_ROW_GAP, SETTINGS_OPTION_GAP,
)
from modes import MODES, get_mode
from theme import Alignment
from ui import Button, ButtonAction, OptionRow, TextBox, pointer_position, update_button_lifts


class SettingsState:
    def __init__(self, game, *, mode=None):
        self.game = game
        self.renderer = game.renderer
        self.pointer_pos: tuple[int, int] | None = None
        self.button_action = ButtonAction()

        self._select_mode(game.settings_mode if mode is None else mode)

        self.back_button = Button(
            pygame.Rect(
                MENU_BACK_LEFT, MENU_START_TOP,
                MENU_BACK_WIDTH, MENU_BUTTON_HEIGHT,
            ),
            'Back',
            self.renderer,
            lift=self.renderer.theme.menu_lift,
        )

    def _select_mode(self, mode):
        self.spec = get_mode(mode).settings_spec()
        self.mode = mode
        self.game.settings_mode = mode
        self._build_rows()

    def _build_rows(self):
        settings = self.game.settings_by_mode[self.mode]
        row_specs = list(self.spec.row_specs(settings))
        available_modes = tuple(
            (mode.key, mode.display_name)
            for mode in MODES.values()
            if mode.active
        )
        if len(available_modes) > 1:
            row_specs.insert(0, ('mode', 'Game', available_modes))

        self.headings = []
        self.rows = {}
        values = self._values()
        next_top = SETTINGS_FIRST_ROW_TOP

        for key, label, options in row_specs:
            heading = TextBox(
                label,
                self.renderer,
                'checkbox',
                SETTINGS_LEFT,
                next_top,
                SETTINGS_WIDTH,
                'background_text',
            )
            self.headings.append(heading)
            row = OptionRow(
                pygame.Rect(
                    SETTINGS_LEFT,
                    heading.y + heading.height + SETTINGS_LABEL_GAP,
                    SETTINGS_WIDTH,
                    MENU_BUTTON_HEIGHT,
                ),
                options,
                self.renderer,
                selected=values[key],
                gap=SETTINGS_OPTION_GAP,
                read_only=('custom',) if key == 'preset' else (),
            )
            self.rows[key] = row
            next_top = row.rect.bottom + SETTINGS_ROW_GAP

    def _values(self):
        settings = self.game.settings_by_mode[self.mode]
        return {
            'mode': self.mode,
            'preset': self.spec.preset_for(settings),
            **{
                row.key: getattr(settings, row.key)
                for row in self.spec.rows
            },
        }

    def _sync_rows(self):
        values = self._values()
        for key, row in self.rows.items():
            row.set_selected(values[key])

    def _apply_option(self, key, value):
        if key == 'mode':
            self._select_mode(value)
            return

        settings = self.game.settings_by_mode[self.mode]
        if key == 'preset':
            settings = self.spec.preset(value)
        else:
            settings = replace(settings, **{key: value})

        self.game.settings_by_mode[self.mode] = settings
        self._sync_rows()

    def handle_events(self, events):
        if self.button_action.blocks_events():
            for event in events:
                self.pointer_pos = pointer_position(self.pointer_pos, event)
            return
        for event in events:
            self.pointer_pos = pointer_position(self.pointer_pos, event)
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.back_button.is_clicked(event.pos):
                self.button_action.begin(
                    self.back_button,
                    lambda: self.game.show_main_menu(),
                )
                return

            for key, row in self.rows.items():
                value = row.choice_at(event.pos)
                if value is None:
                    continue
                button = row.buttons[value]
                if button.selected:
                    return
                self.button_action.begin(
                    button,
                    lambda key=key, value=value: self._apply_option(key, value),
                )
                return

    def update(self, dt_ms):
        for row in self.rows.values():
            row.update(dt_ms, self.pointer_pos)
        update_button_lifts((self.back_button,), dt_ms, self.pointer_pos)
        self.button_action.update(dt_ms)

    def draw(self, screen):
        self.renderer.fill(screen)
        self.renderer.text(
            screen, 'Settings',
            pygame.Rect(0, SETTINGS_TITLE_TOP, SCREEN_WIDTH, self.renderer.line_height('title')),
            'title', alignment=Alignment('center', 'top'),
        )
        for heading in self.headings:
            heading.draw(screen)
        for row in self.rows.values():
            row.draw(screen)

        self.back_button.draw(screen)
