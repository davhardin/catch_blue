from dataclasses import replace

import pygame

from constants import (
    SCREEN_WIDTH, MENU_BACK_LEFT, MENU_BACK_WIDTH, MENU_START_TOP, MENU_BUTTON_HEIGHT,
    SETTINGS_LEFT, SETTINGS_WIDTH, SETTINGS_TITLE_TOP, SETTINGS_FIRST_ROW_TOP,
    SETTINGS_LABEL_GAP, SETTINGS_ROW_GAP, SETTINGS_OPTION_GAP,
)
from game_setup import PRESETS, TierPolicy, preset_for
from theme import Alignment
from ui import Button, ButtonAction, OptionRow, TextBox, pointer_position, update_button_lifts


class SettingsState:
    def __init__(self, game, bank):
        self.game = game
        self.bank = bank
        self.renderer = game.renderer
        self.pointer_pos: tuple[int, int] | None = None
        self.button_action = ButtonAction()

        limits = sorted({10, 15, 20, 25, 30, game.settings.move_limit})
        row_specs = (
            ('preset', 'Difficulty', (
                ('easy', 'Easy'), ('medium', 'Medium'),
                ('hard', 'Hard'), ('custom', 'Custom'),
            )),
            ('board_size', 'Board size', ((5, '5 x 5'), (7, '7 x 7'), (9, '9 x 9'))),
            ('move_limit', 'Move limit', tuple((value, str(value)) for value in limits)),
            ('tier_policy', 'Question tiers', (
                (TierPolicy.TIERS_1_2, 'T1 + T2'),
                (TierPolicy.ALL, 'All tiers'),
                (TierPolicy.DISTANCE, 'Distance based'),
            )),
        )
        self.headings = []
        self.rows = {}
        values = self._values()
        next_top = SETTINGS_FIRST_ROW_TOP
        for key, label, options in row_specs:
            heading = TextBox(
                label, self.renderer, 'checkbox', SETTINGS_LEFT, next_top,
                SETTINGS_WIDTH, 'background_text',
            )
            self.headings.append(heading)
            row = OptionRow(
                pygame.Rect(
                    SETTINGS_LEFT, heading.y + heading.height + SETTINGS_LABEL_GAP,
                    SETTINGS_WIDTH, MENU_BUTTON_HEIGHT,
                ),
                options, self.renderer, selected=values[key], gap=SETTINGS_OPTION_GAP,
                read_only=('custom',) if key == 'preset' else (),
            )
            self.rows[key] = row
            next_top = row.rect.bottom + SETTINGS_ROW_GAP

        self.custom_note = TextBox(
            'Custom is automatic when values do not match a preset.',
            self.renderer, 'credits', SETTINGS_LEFT, next_top,
            SETTINGS_WIDTH, 'background_text',
        )
        self.tier_note = TextBox(
            'Tier choices are saved now; question filtering arrives in M7.f.',
            self.renderer, 'credits', SETTINGS_LEFT,
            self.custom_note.y + self.custom_note.height + 8,
            SETTINGS_WIDTH, 'background_text',
        )
        self.back_button = Button(
            pygame.Rect(MENU_BACK_LEFT, MENU_START_TOP, MENU_BACK_WIDTH, MENU_BUTTON_HEIGHT),
            'Back', self.renderer, lift=self.renderer.theme.menu_lift,
        )

    def _values(self):
        settings = self.game.settings
        return {
            'preset': preset_for(settings),
            'board_size': settings.board_size,
            'move_limit': settings.move_limit,
            'tier_policy': settings.tier_policy,
        }

    def _sync_rows(self):
        for key, value in self._values().items():
            self.rows[key].set_selected(value)

    def _apply_option(self, key, value):
        if key == 'preset':
            self.game.settings = PRESETS[value]
        else:
            self.game.settings = replace(self.game.settings, **{key: value})
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
                    lambda: self.game.show_main_menu(self.bank),
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
        self.custom_note.draw(screen)
        self.tier_note.draw(screen)
        self.back_button.draw(screen)
