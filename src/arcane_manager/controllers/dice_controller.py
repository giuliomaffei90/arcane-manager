from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    def refreshDiceHistory(self):
        if self.dice_history_view is not None:
            self.dice_history_view.setString_(format_dice_roll_history())

    def currentDiceExpression(self) -> str:
        parts = []
        for sides in self.dice_presets:
            count = int(self.dice_pool.get(int(sides), 0))
            if count <= 0:
                continue
            parts.append(f"{count}d{sides}")
        return "+".join(parts)

    def refreshDiceFormula_(self, _sender):
        expression = self.currentDiceExpression()
        self.dice_formula_label.setStringValue_(expression or "Click a die")
        for button in self.dice_preset_buttons:
            sides = int(button.tag())
            count = int(self.dice_pool.get(sides, 0))
            button.setTitle_(f"d{sides} x{count}" if count else f"d{sides}")
        self.dice_roll_button.setEnabled_(bool(expression))
        self.dice_clear_button.setEnabled_(bool(expression))

    def addDieToPool_(self, sender):
        sides = int(sender.tag())
        total = sum(int(value) for value in self.dice_pool.values())
        if total >= 40:
            return
        if sides not in self.dice_pool:
            return
        self.dice_pool[sides] = int(self.dice_pool.get(sides, 0)) + 1
        self.dice_result_label.setStringValue_("")
        self.refreshDiceFormula_(None)

    def clearDicePool_(self, _sender):
        for sides in list(self.dice_pool):
            self.dice_pool[sides] = 0
        self.dice_result_label.setStringValue_("")
        self.refreshDiceFormula_(None)

    def rollCustomDice_(self, _sender):
        self.refreshDiceFormula_(None)
        expression = self.currentDiceExpression()
        if not expression:
            self.dice_result_label.setStringValue_("Choose at least one die.")
            return
        self.rollDice_(expression)

    def rollDice_(self, expression):
        expression = str(expression).strip()
        if not (DICE_PATTERN.fullmatch(expression) or DICE_FORMULA_PATTERN.fullmatch(expression)):
            result = f"Invalid dice expression: {expression}"
            self.displayDiceRollResult_(result)
            return
        self.displayDiceRollResult_(f"Rolling {expression}...")
        if show_3d_dice_roll(expression, self):
            return
        try:
            result = roll_dice_formula(expression)
            if DICE_PATTERN.fullmatch(expression):
                show_dice_roll_animation(roll_dice(expression))
        except ValueError as exc:
            result = str(exc)
        self.displayDiceRollResult_(result)

    def displayDiceRollResult_(self, result):
        record_dice_roll_history(result)
        if self.dice_result_label is not None and self.current_tab == "dice":
            self.dice_result_label.setStringValue_(result)
