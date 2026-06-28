from __future__ import annotations

from ..platform import *
from ..constants import *
from ..data import Creature, Spell, creature_summary, display_ac
from ..text_utils import normalize
from .core import *

class DiceTextView(NSTextView):
    dice_ranges: list[tuple[int, int, str]]
    spell_ranges: list[tuple[int, int, Spell]]
    combatant_ranges: list[tuple[int, int, int]]
    roll_target: Any
    spell_target: Any
    combatant_target: Any
    tracking_area: Any

    def initWithFrame_(self, frame):
        self = objc.super(DiceTextView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.dice_ranges = []
        self.spell_ranges = []
        self.combatant_ranges = []
        self.roll_target = None
        self.spell_target = None
        self.combatant_target = None
        self.tracking_area = None
        self.setEditable_(False)
        self.setSelectable_(False)
        self.setDrawsBackground_(False)
        self.setTextContainerInset_(NSMakeSize(0, 0))
        self.setHorizontallyResizable_(False)
        self.setVerticallyResizable_(True)
        self.textContainer().setLineFragmentPadding_(0)
        return self

    def setDiceRanges_(self, dice_ranges):
        self.dice_ranges = list(dice_ranges)

    def setRollTarget_(self, target):
        self.roll_target = target

    def setSpellRanges_(self, spell_ranges):
        self.spell_ranges = list(spell_ranges)

    def setSpellTarget_(self, target):
        self.spell_target = target

    def setCombatantRanges_(self, combatant_ranges):
        self.combatant_ranges = list(combatant_ranges)

    def setCombatantTarget_(self, target):
        self.combatant_target = target

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseMoved
            | NSTrackingMouseEnteredAndExited
            | NSTrackingActiveAlways
            | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(DiceTextView, self).updateTrackingAreas()

    def diceExpressionAtEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.characterIndexForInsertionAtPoint_(point)
        for start, length, expression in self.dice_ranges:
            if start <= index < start + length:
                return expression
        return None

    def spellAtEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.characterIndexForInsertionAtPoint_(point)
        for start, length, spell in self.spell_ranges:
            if start <= index < start + length:
                return spell
        return None

    def combatantIndexAtEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.characterIndexForInsertionAtPoint_(point)
        for start, length, combatant_index in self.combatant_ranges:
            if start <= index < start + length:
                return combatant_index
        return None

    def mouseMoved_(self, event):
        if (
            self.diceExpressionAtEvent_(event) is not None
            or self.spellAtEvent_(event) is not None
            or self.combatantIndexAtEvent_(event) is not None
        ):
            NSCursor.pointingHandCursor().set()
        else:
            NSCursor.arrowCursor().set()

    def mouseExited_(self, _event):
        NSCursor.arrowCursor().set()

    def mouseDown_(self, event):
        expression = self.diceExpressionAtEvent_(event)
        if expression is not None:
            if self.roll_target is not None:
                self.roll_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "rollDice:",
                    expression,
                    False,
                )
            return
        spell = self.spellAtEvent_(event)
        if spell is not None:
            if self.spell_target is not None:
                self.spell_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openSpell:",
                    spell,
                    False,
                )
            return
        combatant_index = self.combatantIndexAtEvent_(event)
        if combatant_index is not None:
            if self.combatant_target is not None:
                self.combatant_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantIndex:",
                    combatant_index,
                    False,
                )
            return
        objc.super(DiceTextView, self).mouseDown_(event)


SPELL_SCHOOL_RGB: dict[str, tuple[float, float, float]] = {
    "Abjuration": (0x72 / 255, 0xC7 / 255, 0xF7 / 255),
    "Conjuration": (0x62 / 255, 0xD7 / 255, 0xC7 / 255),
    "Divination": (0x9C / 255, 0xA8 / 255, 0xFF / 255),
    "Enchantment": (0xF0 / 255, 0x85 / 255, 0xC8 / 255),
    "Evocation": (0xF2 / 255, 0x7A / 255, 0x5E / 255),
    "Illusion": (0xC4 / 255, 0x99 / 255, 0xF2 / 255),
    "Necromancy": (0x9A / 255, 0xD8 / 255, 0x5F / 255),
    "Transmutation": (0xE7 / 255, 0xB9 / 255, 0x56 / 255),
}


def spell_school_color(school: str):
    rgb = SPELL_SCHOOL_RGB.get(str(school or "").strip())
    if rgb is None:
        return theme_color("gold")
    return ui_color(*rgb, 1.0)


class SearchResultButton(NSButton):
    row_kind = objc.ivar()
    primary_text = objc.ivar()
    secondary_text = objc.ivar()
    hp_text = objc.ivar()
    ac_text = objc.ivar()
    cr_text = objc.ivar()
    meta_text = objc.ivar()
    spell_school = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(SearchResultButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.row_kind = ""
        self.primary_text = ""
        self.secondary_text = ""
        self.hp_text = ""
        self.ac_text = ""
        self.cr_text = ""
        self.meta_text = ""
        self.spell_school = ""
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def configureMonsterResult_(self, creature: Creature):
        self.row_kind = "monster"
        self.primary_text = creature.name
        self.secondary_text = ""
        self.hp_text = f"HP {creature.hp}"
        self.ac_text = f"AC {display_ac(creature.ac)}"
        self.cr_text = f"CR {creature.cr}"
        self.meta_text = ""
        self.spell_school = ""
        self.setToolTip_(creature_summary(creature))
        self.setNeedsDisplay_(True)

    def configureSpellResult_(self, spell: Spell):
        self.row_kind = "spell"
        self.primary_text = spell.name
        self.secondary_text = spell.italian_name if normalize(spell.italian_name) != normalize(spell.name) else ""
        self.hp_text = ""
        self.ac_text = ""
        self.cr_text = ""
        self.meta_text = " | ".join(part for part in (spell.level, spell.school) if part)
        self.spell_school = spell.school
        tooltip_parts = [spell.name]
        if self.secondary_text:
            tooltip_parts.append(f"({self.secondary_text})")
        if self.meta_text:
            tooltip_parts.append(f"- {self.meta_text}")
        self.setToolTip_(" ".join(tooltip_parts))
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        fill = theme_color("surface_hover") if highlighted else theme_color("surface_soft")
        stroke = theme_color("border") if highlighted else theme_color("border_soft")
        draw_rounded_rect(
            NSMakeRect(0.5, 0.5, max(1, bounds.size.width - 1), max(1, bounds.size.height - 1)),
            fill,
            stroke,
            7,
            1,
        )
        if self.row_kind == "monster":
            self._drawMonsterResult_(bounds)
        elif self.row_kind == "spell":
            self._drawSpellResult_(bounds)

    def mouseDown_(self, event):
        if self.row_kind == "monster":
            return
        objc.super(SearchResultButton, self).mouseDown_(event)

    @objc.python_method
    def _drawMonsterResult_(self, bounds):
        width = bounds.size.width
        primary = theme_color("text_strong")
        muted = theme_color("muted")
        name_attrs = text_attributes(14, primary, True)
        meta_attrs = text_attributes(11, muted, True)
        ac_text = self.ac_text.replace("AC ", "AC: ")
        cr_text = self.cr_text.replace("CR ", "CR: ")
        ac_width = text_width(ac_text, meta_attrs)
        cr_width = text_width(cr_text, meta_attrs)
        gap = 6
        x = 14
        y = max(0, (bounds.size.height - 19) / 2 - 1)
        metadata_width = ac_width + cr_width + gap
        meta_x = width - x - metadata_width
        name_width = max(54, meta_x - x - gap)
        fitted_name = fit_text_to_width(self.primary_text, name_width, name_attrs)
        NSString.stringWithString_(fitted_name).drawInRect_withAttributes_(NSMakeRect(x, y, name_width, 20), name_attrs)
        draw_right_fitted_text(ac_text, NSMakeRect(meta_x, y + 2, ac_width, 17), 11, muted, True)
        draw_right_fitted_text(cr_text, NSMakeRect(meta_x + ac_width + gap, y + 2, cr_width, 17), 11, muted, True)

    @objc.python_method
    def _drawSpellResult_(self, bounds):
        width = bounds.size.width
        primary = theme_color("text")
        muted = theme_color("muted")
        metadata_color = spell_school_color(self.spell_school)
        draw_fitted_text(self.primary_text, NSMakeRect(14, 7, width - 28, 17), 13.5, primary, True)
        if width >= 340 and self.meta_text:
            meta_w = min(172, max(120, width * 0.40))
            secondary_w = width - meta_w - 38
            draw_fitted_text(self.secondary_text, NSMakeRect(14, 25, secondary_w, 15), 11.5, muted, False)
            draw_right_fitted_text(self.meta_text, NSMakeRect(width - meta_w - 14, 25, meta_w, 15), 11.5, metadata_color, True)
            return
        bottom = self.meta_text
        if self.secondary_text and self.meta_text:
            bottom = f"{self.secondary_text} - {self.meta_text}"
        elif self.secondary_text:
            bottom = self.secondary_text
        draw_fitted_text(bottom, NSMakeRect(14, 25, width - 28, 15), 11.5, muted, False)


def color_from_hex(value: str, fallback=None):
    text = str(value or "").strip().lstrip("#")
    if len(text) != 6:
        return fallback or theme_color("text")
    try:
        red = int(text[0:2], 16) / 255.0
        green = int(text[2:4], 16) / 255.0
        blue = int(text[4:6], 16) / 255.0
    except ValueError:
        return fallback or theme_color("text")
    return ui_color(red, green, blue, 1.0)


class AdventureTreeButton(NSButton):
    display_name = objc.ivar()
    node_path = objc.ivar()
    depth = objc.ivar()
    is_dir = objc.ivar()
    is_expanded = objc.ivar()
    is_selected = objc.ivar()
    color_hex = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(AdventureTreeButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.display_name = ""
        self.node_path = ""
        self.depth = 0
        self.is_dir = False
        self.is_expanded = False
        self.is_selected = False
        self.color_hex = ""
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def configureName_path_depth_isDir_expanded_selected_color_(
        self,
        name,
        path,
        depth,
        is_dir,
        expanded,
        selected,
        color_hex,
    ):
        self.display_name = str(name)
        self.node_path = str(path)
        self.depth = int(depth)
        self.is_dir = bool(is_dir)
        self.is_expanded = bool(expanded)
        self.is_selected = bool(selected)
        self.color_hex = str(color_hex or "")
        self.setToolTip_(str(path))
        self.setNeedsDisplay_(True)

    def menuForEvent_(self, _event):
        target = self.target()
        if target is not None and hasattr(target, "adventureContextMenuForButton_"):
            return target.adventureContextMenuForButton_(self)
        return objc.super(AdventureTreeButton, self).menuForEvent_(_event)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        if self.is_selected:
            fill = theme_color("selection")
        elif highlighted:
            fill = theme_color("surface_hover")
        else:
            fill = None
        if fill is not None:
            draw_rounded_rect(
                NSMakeRect(4, 1, max(1, bounds.size.width - 8), max(1, bounds.size.height - 2)),
                fill,
                None,
                5,
                0,
            )

        indent = 10 + int(self.depth) * 18
        text_x = indent + 20
        text_color = color_from_hex(self.color_hex, theme_color("text"))
        if self.is_selected:
            text_color = theme_color("text_strong")
        muted = theme_color("muted")

        if self.is_dir:
            arrow = "⌄" if self.is_expanded else "›"
            draw_center_fitted_text(arrow, NSMakeRect(indent, 5, 14, 16), 14, muted, True)
            draw_fitted_text(self.display_name, NSMakeRect(text_x, 5, bounds.size.width - text_x - 10, 18), 13, text_color, True)
        else:
            draw_fitted_text(self.display_name, NSMakeRect(text_x, 5, bounds.size.width - text_x - 10, 18), 13, text_color, False)


class AdventureDividerView(NSView):
    target = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(AdventureDividerView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.target = None
        self.setToolTip_("Drag to resize")
        return self

    def setTarget_(self, target):
        self.target = target

    def resetCursorRects(self):
        self.addCursorRect_cursor_(self.bounds(), NSCursor.resizeLeftRightCursor())

    def mouseEntered_(self, _event):
        NSCursor.resizeLeftRightCursor().set()

    def mouseDown_(self, event):
        NSCursor.resizeLeftRightCursor().set()
        self._sendDragLocation_(event)

    def mouseDragged_(self, event):
        self._sendDragLocation_(event)

    def mouseUp_(self, _event):
        NSCursor.arrowCursor().set()

    @objc.python_method
    def _sendDragLocation_(self, event):
        if self.target is None or not hasattr(self.target, "resizeAdventureTreeToWindowX_"):
            return
        self.target.resizeAdventureTreeToWindowX_(event.locationInWindow().x)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        x = bounds.size.width / 2 - 0.5
        theme_color("border").set()
        path = NSBezierPath.bezierPath()
        path.moveToPoint_(NSMakePoint(x, 0))
        path.lineToPoint_(NSMakePoint(x, bounds.size.height))
        path.setLineWidth_(1)
        path.stroke()


class StatBlockAbilityButton(NSButton):
    ability_name = objc.ivar()
    score_text = objc.ivar()
    bonus_text = objc.ivar()
    roll_expression = objc.ivar()
    roll_target = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(StatBlockAbilityButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.ability_name = ""
        self.score_text = ""
        self.bonus_text = ""
        self.roll_expression = ""
        self.roll_target = None
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def configure_stat(self, name, score, bonus, target):
        bonus_value = int(bonus)
        self.ability_name = str(name)
        self.score_text = str(score)
        self.bonus_text = f"{bonus_value:+d}"
        self.roll_expression = f"1d20+{bonus_value}" if bonus_value >= 0 else f"1d20{bonus_value}"
        self.roll_target = target
        self.setToolTip_(f"Roll {self.ability_name} {self.roll_expression}")
        self.setNeedsDisplay_(True)

    @objc.python_method
    def _bonusRect(self):
        bounds = self.bounds()
        inset = 2
        return NSMakeRect(inset, bounds.size.height * 0.27, bounds.size.width - inset * 2, bounds.size.height * 0.71)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        fill = theme_color("surface_soft")
        stroke = theme_color("border") if highlighted else theme_color("border_soft")
        circle_fill = theme_color("panel_alt")
        text = theme_color("text_strong")
        muted = theme_color("muted")
        green = theme_color("dice")

        rect = self._bonusRect()
        draw_rounded_rect(rect, fill, stroke, 7, 1.25)
        circle_side = min(bounds.size.width - 4, bounds.size.height * 0.43)
        circle = NSMakeRect(
            (bounds.size.width - circle_side) / 2,
            1,
            circle_side,
            circle_side,
        )
        oval = NSBezierPath.bezierPathWithOvalInRect_(circle)
        circle_fill.set()
        oval.fill()

        stroke.set()
        oval.setLineWidth_(1.25)
        oval.stroke()

        draw_center_fitted_text(self.ability_name, NSMakeRect(5, bounds.size.height - 20, bounds.size.width - 10, 14), 9.5, muted, True)
        draw_center_fitted_text(self.bonus_text, NSMakeRect(5, bounds.size.height * 0.46, bounds.size.width - 10, 22), 16, green, True)
        draw_center_fitted_text(self.score_text, NSMakeRect(5, circle.origin.y + (circle.size.height - 19) / 2, bounds.size.width - 10, 20), 14, text, True)

    def mouseDown_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        if self.roll_expression and self.roll_target is not None and point_in_rect(point, self._bonusRect()):
            self.roll_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                "rollDice:",
                self.roll_expression,
                False,
            )
            return
        objc.super(StatBlockAbilityButton, self).mouseDown_(event)


class RowAddButton(NSButton):
    def initWithFrame_(self, frame):
        self = objc.super(RowAddButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        icon_color = theme_color("text_strong") if highlighted else theme_color("text")
        fill = theme_color("surface_hover") if highlighted else theme_color("surface")
        stroke = theme_color("border") if highlighted else theme_color("border_soft")
        side = min(30, bounds.size.width, bounds.size.height)
        draw_rounded_rect(
            NSMakeRect((bounds.size.width - side) / 2, (bounds.size.height - side) / 2, side, side),
            fill,
            stroke,
            8,
            1,
        )
        attributes = text_attributes(16, icon_color, True)
        glyph = NSString.stringWithString_("+")
        glyph_size = glyph.sizeWithAttributes_(attributes)
        glyph.drawAtPoint_withAttributes_(
            NSMakePoint(
                (bounds.size.width - glyph_size.width) / 2,
                (bounds.size.height - glyph_size.height) / 2 - 1,
            ),
            attributes,
        )


class StyledPopUpButton(NSPopUpButton):
    def initWithFrame_(self, frame):
        self = objc.super(StyledPopUpButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setBordered_(False)
        return self

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        fill = theme_color("surface_hover") if highlighted else theme_color("surface")
        stroke = theme_color("border") if highlighted else theme_color("border_soft")
        draw_rounded_rect(
            NSMakeRect(0.5, 0.5, max(1, bounds.size.width - 1), max(1, bounds.size.height - 1)),
            fill,
            stroke,
            7,
            1,
        )
        item = self.selectedItem()
        title = str(item.title()) if item is not None else str(self.title())
        draw_fitted_text(title, NSMakeRect(12, 8, max(20, bounds.size.width - 42), 18), 13, theme_color("text"), True)
        draw_right_fitted_text("⌄", NSMakeRect(bounds.size.width - 28, 7, 16, 18), 14, theme_color("muted"), True)


MONSTER_RESULT_ROW_HEIGHT = 42
MONSTER_RESULT_ROW_STEP = 50
SPELL_RESULT_ROW_HEIGHT = 42
SPELL_RESULT_ROW_STEP = 50


class CombatTrackerView(NSView):
    combatants: list[dict[str, Any]]
    current_turn_index: int
    name_rects: list[tuple[Any, int]]
    hp_button_rects: list[tuple[Any, int]]
    status_rects: list[tuple[Any, int]]
    target: Any
    tracking_area: Any

    def initWithFrame_(self, frame):
        self = objc.super(CombatTrackerView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.combatants = []
        self.current_turn_index = 0
        self.name_rects = []
        self.hp_button_rects = []
        self.status_rects = []
        self.target = None
        self.tracking_area = None
        return self

    def isFlipped(self):
        return True

    def setTarget_(self, target):
        self.target = target

    def setPayload_(self, payload):
        self.combatants = list(payload.get("combatants", []))
        self.current_turn_index = int(payload.get("current_turn_index", 0))
        width = max(780, self.frame().size.width)
        height = max(420, 144 + len(self.combatants) * 70 + 96)
        self.setFrame_(NSMakeRect(0, 0, width, height))
        self.setNeedsDisplay_(True)

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseMoved
            | NSTrackingMouseEnteredAndExited
            | NSTrackingActiveAlways
            | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(CombatTrackerView, self).updateTrackingAreas()

    @objc.python_method
    def _hp_values(self, combatant: dict[str, Any]) -> tuple[int | None, int | None]:
        try:
            current = int(str(combatant.get("hp") or "").strip())
        except ValueError:
            current = None
        try:
            maximum = int(str(combatant.get("max_hp") or "").strip())
        except ValueError:
            maximum = None
        return current, maximum

    @objc.python_method
    def _hit_test(self, event) -> tuple[str, int, int | None] | None:
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        for rect, index in self.status_rects:
            if point_in_rect(point, rect):
                return ("status", index, None)
        for rect, index in self.hp_button_rects:
            if point_in_rect(point, rect):
                return ("hp", index, None)
        for rect, index in self.name_rects:
            if point_in_rect(point, rect):
                return ("name", index, None)
        return None

    def mouseMoved_(self, event):
        hit = self._hit_test(event)
        if hit is not None:
            NSCursor.pointingHandCursor().set()
        else:
            NSCursor.arrowCursor().set()

    def mouseExited_(self, _event):
        NSCursor.arrowCursor().set()

    def mouseDown_(self, event):
        hit = self._hit_test(event)
        if hit is not None and hit[0] == "name":
            index = hit[1]
            if self.target is not None:
                self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantIndex:",
                    index,
                    False,
                )
            return
        if hit is not None and hit[0] == "hp":
            _kind, index, _delta = hit
            if self.target is not None:
                point = event.locationInWindow()
                self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantHpMenu:",
                    {"index": index, "x": float(point.x), "y": float(point.y)},
                    False,
                )
            return
        if hit is not None and hit[0] == "status":
            _kind, index, _delta = hit
            if self.target is not None:
                point = self.convertPoint_fromView_(event.locationInWindow(), None)
                self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantStatusMenu:",
                    {"index": index, "x": float(point.x), "y": float(point.y)},
                    False,
                )
            return
        if self.target is not None:
            self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                "closeCombatantHpMenu:",
                None,
                False,
            )
        objc.super(CombatTrackerView, self).mouseDown_(event)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        theme_color("panel").set()
        NSBezierPath.bezierPathWithRect_(bounds).fill()

        muted = theme_color("muted")
        card_border = theme_color("border_soft")
        current_border = theme_color("border")
        green = theme_color("dice")
        temp_blue = theme_color("blue_temp")
        pink = theme_color("monster")
        red = theme_color("danger")
        dead_red = theme_color("danger")
        white = theme_color("text_strong")

        left = 24
        width = bounds.size.width - 48
        right = left + width
        status_w = 116 if width >= 900 else 98
        status_x = right - status_w - 18
        ac_w = 44
        ac_x = status_x - ac_w - 18
        name_x = left + 132
        max_display_name = "Adult Green Dragon"
        max_name_chars = len(max_display_name)
        name_w = max_name_chars * 8 + 8
        hp_text_x = name_x + name_w + 16
        hp_text_w = 76
        hp_action_w = 44
        hp_action_x = ac_x - hp_action_w - 18
        bar_x = hp_text_x + hp_text_w + 14
        bar_right = hp_action_x - 18
        bar_w = max(110, bar_right - bar_x)

        if not self.combatants:
            draw_text("No combatants yet.", left + 24, 36, 18, white, True)
            draw_text("Select a party, add creatures, then start the fight.", left + 24, 66, 13, muted, False)
            self.name_rects = []
            self.hp_button_rects = []
            self.status_rects = []
            return

        self.name_rects = []
        self.hp_button_rects = []
        self.status_rects = []
        draw_text("Init", left + 30, 22, 11, muted, True)
        draw_text("Type", left + 86, 22, 11, muted, True)
        draw_text("Name", name_x, 22, 11, muted, True)
        draw_right_fitted_text_centered("HP", NSMakeRect(hp_text_x, 18, hp_text_w, 20), 11, muted, True)
        draw_centered_text_in_rect("AC", NSMakeRect(ac_x, 18, ac_w, 20), 11, muted, True)
        draw_text("Status", status_x + 10, 22, 11, muted, True)

        row_y = 54
        row_h = 56
        gap = 12
        for index, combatant in enumerate(self.combatants):
            initiative = int(combatant.get("initiative") or 0)
            rect = NSMakeRect(left, row_y, width, row_h)
            is_current = index == self.current_turn_index
            is_down = self._hp_values(combatant)[0] is not None and self._hp_values(combatant)[0] <= 0
            is_dead = combatant_is_dead(combatant)
            conditions = normalized_conditions(combatant)
            row_fill = theme_color("surface_soft", 0.62 if is_down else 1.0)
            if conditions and not is_down:
                tint_source = condition_color(conditions[0], 1.0)
                row_fill = tint_source.colorWithAlphaComponent_(0.18)
            draw_rounded_rect(
                rect,
                row_fill,
                current_border if is_current else card_border,
                8,
                2.0 if is_current else 1.0,
            )
            draw_text(str(initiative), left + 36, row_y + 17, 17, white, True)
            if combatant.get("kind") == "Monster":
                icon_name = "Monster"
                fallback_icon = MONSTER_ICON
                fallback_color = pink
                subtitle = "Monstrosity" if not combatant.get("cr") else f"CR {combatant.get('cr')}"
                self.name_rects.append((NSMakeRect(name_x, row_y + 8, name_w, 36), index))
            else:
                class_name = str(combatant.get("class") or "Fighter")
                icon_name = class_name
                fallback_icon = CLASS_ICONS.get(class_name, "◆")
                fallback_color = white
                subtitle = class_name
            icon_rect = NSMakeRect(left + 84, row_y + 13, 26, 26)
            if not draw_icon(icon_name, icon_rect):
                draw_text(fallback_icon, left + 92, row_y + 15, 22, fallback_color, True)
            display_name = ellipsize(str(combatant.get("name") or "Unnamed"), max_name_chars)
            draw_text(display_name, name_x, row_y + 10, 14, white, True)
            draw_text(subtitle[:22], name_x, row_y + 30, 12, muted, False)

            is_monster = combatant.get("kind") == "Monster"
            bar_y = row_y + 24
            bar_h = 8
            if is_monster:
                hp_button_w = hp_action_w
                hp_button_h = 28
                hp_button_y = row_y + (row_h - hp_button_h) / 2
                hp_button_rect = NSMakeRect(hp_action_x, hp_button_y, hp_button_w, hp_button_h)
                self.hp_button_rects.append((hp_button_rect, index))
                draw_rounded_rect(
                    hp_button_rect,
                    theme_color("surface"),
                    theme_color("border"),
                    7,
                    1,
                )
                draw_centered_text_in_rect("+/-", hp_button_rect, 13, white, True)

                current_hp, max_hp = self._hp_values(combatant)
                bar_rect = NSMakeRect(bar_x, bar_y, bar_w, bar_h)
                if current_hp is not None and max_hp is not None and max_hp > 0:
                    try:
                        temp_hp = max(0, int(str(combatant.get("temp_hp") or "0")))
                    except ValueError:
                        temp_hp = 0
                    effective_max = max_hp + temp_hp
                    hp_ratio = max(0.0, min(1.0, current_hp / effective_max))
                    temp_ratio = max(0.0, min(1.0 - hp_ratio, temp_hp / effective_max))
                    fill_color = red if current_hp <= 0 else pink if current_hp / max_hp <= 0.35 else green
                    draw_segmented_rounded_bar(
                        bar_rect,
                        [
                            (bar_w * hp_ratio, fill_color),
                            (bar_w * temp_ratio, temp_blue),
                        ],
                        theme_color("panel_alt"),
                        4,
                    )
                    hp_text = f"{current_hp}/{max_hp}"
                else:
                    draw_segmented_rounded_bar(bar_rect, [], theme_color("panel_alt"), 4)
                    hp_text = "-"
                draw_right_fitted_text_centered(hp_text, NSMakeRect(hp_text_x, bar_y, hp_text_w, bar_h), 12, muted, False)
            else:
                pass

            draw_centered_text_in_rect(str(combatant.get("ac") or "?"), NSMakeRect(ac_x, row_y + 14, ac_w, 28), 15, white, False)

            status_label = combatant_status_label(combatant)
            status_color = dead_red if is_dead else condition_color(conditions[0]) if conditions else muted
            status_rect = NSMakeRect(status_x, row_y + 14, status_w, 28)
            self.status_rects.append((status_rect, index))
            draw_rounded_rect(
                status_rect,
                theme_color("surface", 0.88 if not is_down else 0.52),
                theme_color("border_soft"),
                7,
                1,
            )
            draw_center_fitted_text(status_label, NSMakeRect(status_x + 8, row_y + 19, status_w - 16, 18), 12, status_color, True)

            row_y += row_h + gap
