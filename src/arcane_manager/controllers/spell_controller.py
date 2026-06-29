from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    @objc.python_method
    def applySpellDetailSchoolColor(self):
        color = spell_school_color(self.current_spell_school)
        self.spell_detail_meta_label.setTextColor_(color)
        for label in (self.spell_v_label, self.spell_s_label, self.spell_m_label):
            label.setTextColor_(color)
        for box in (self.spell_v_box, self.spell_s_box, self.spell_m_box):
            box.setFillColor_strokeColor_(color, color)

    def selectedMonsterCrFilter(self) -> str | None:
        selected = self.monster_cr_filter_popup.selectedItem()
        title = str(selected.title()) if selected is not None else ""
        if not title or title == "Any CR":
            return None
        return title.removeprefix("CR ").strip() or None

    def ensureMonsterResultRows_(self, count: int):
        while len(self.monster_result_buttons) < count:
            index = len(self.monster_result_buttons)
            button = SearchResultButton.alloc().initWithFrame_(NSMakeRect(0, 0, 100, MONSTER_RESULT_ROW_HEIGHT))
            button.setTarget_(self)
            button.setAction_("selectMonsterResult:")
            button.setTag_(index)
            button.setHidden_(True)
            self.monster_result_buttons.append(button)
            self.monster_results_content.addSubview_(button)

            add_button = RowAddButton.alloc().initWithFrame_(NSMakeRect(0, 0, 28, MONSTER_RESULT_ROW_HEIGHT))
            add_button.setTarget_(self)
            add_button.setAction_("addMonster:")
            add_button.setTag_(index)
            add_button.setHidden_(True)
            add_button.setToolTip_("Add creature to initiative")
            self.monster_add_buttons.append(add_button)
            self.monster_results_content.addSubview_(add_button)

    def monsterResultsBoundsDidChange_(self, _notification):
        self.monster_results_indicator.setNeedsDisplay_(True)

    def searchMonsters_(self, _sender):
        query = str(self.monster_search_field.stringValue()).strip()
        self.monster_results = search_creatures(query, self.creatures, self.selectedMonsterCrFilter())
        self.ensureMonsterResultRows_(len(self.monster_results))
        for index, button in enumerate(self.monster_result_buttons):
            add_button = self.monster_add_buttons[index] if index < len(self.monster_add_buttons) else None
            if index >= len(self.monster_results):
                button.setHidden_(True)
                if add_button is not None:
                    add_button.setHidden_(True)
                continue
            button.configureMonsterResult_(self.monster_results[index])
            button.setHidden_(False)
            if add_button is not None:
                add_button.setHidden_(False)
        if self.monster_results_scroll is not None:
            self.layoutMainWindow()
            self.monster_results_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.monster_results_scroll.reflectScrolledClipView_(self.monster_results_scroll.contentView())
            self.monster_results_indicator.setNeedsDisplay_(True)

    def selectMonsterResult_(self, sender):
        index = int(sender.tag())
        if index < 0 or index >= len(self.monster_results):
            return
        self.openMonsterSheetForCreature_(self.monster_results[index])

    def selectedSpellLevelFilter(self) -> str | None:
        selected = self.spell_level_filter_popup.selectedItem()
        title = str(selected.title()) if selected is not None else ""
        if not title or title == "Any Level":
            return None
        return title

    def selectedSpellSchoolFilter(self) -> str | None:
        selected = self.spell_school_filter_popup.selectedItem()
        title = str(selected.title()) if selected is not None else ""
        if not title or title == "Any School":
            return None
        return title

    def ensureSpellResultRows_(self, count: int):
        while len(self.spell_result_buttons) < count:
            index = len(self.spell_result_buttons)
            button = SearchResultButton.alloc().initWithFrame_(NSMakeRect(0, 0, 100, SPELL_RESULT_ROW_HEIGHT))
            button.setTarget_(self)
            button.setAction_("selectSpellResult:")
            button.setTag_(index)
            button.setHidden_(True)
            self.spell_result_buttons.append(button)
            self.spell_results_content.addSubview_(button)

    def refreshSpellResults_(self, _sender):
        self.refreshSpellResults()

    def setSpellDetailHeaderHidden_(self, hidden: bool):
        for view in self.spell_detail_header_views:
            view.setHidden_(hidden)

    def resizeSpellDetailBody(self):
        if self.spell_detail_scroll is None:
            return
        self.spell_detail_view.layoutManager().ensureLayoutForTextContainer_(self.spell_detail_view.textContainer())
        height = max(
            self.spell_detail_scroll.frame().size.height,
            self.spell_detail_view.layoutManager().usedRectForTextContainer_(self.spell_detail_view.textContainer()).size.height + 24,
        )
        self.spell_detail_view.setFrame_(NSMakeRect(0, 0, self.spell_detail_scroll.frame().size.width - 24, height))
        self.spell_detail_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
        self.spell_detail_scroll.reflectScrolledClipView_(self.spell_detail_scroll.contentView())

    def refreshSpellResults(self):
        query = str(self.spell_search_field.stringValue()).strip()
        self.displayed_spells = search_spells(
            query,
            self.spells,
            None,
            self.selectedSpellLevelFilter(),
            self.selectedSpellSchoolFilter(),
        )
        self.ensureSpellResultRows_(len(self.displayed_spells))
        for index, button in enumerate(self.spell_result_buttons):
            if index >= len(self.displayed_spells):
                button.setHidden_(True)
                continue
            spell = self.displayed_spells[index]
            button.configureSpellResult_(spell)
            button.setHidden_(False)
        if self.spell_results_scroll is not None:
            self.layoutMainWindow()
            self.spell_results_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.spell_results_scroll.reflectScrolledClipView_(self.spell_results_scroll.contentView())
        if self.displayed_spells:
            self.showSpellInDetail_(self.displayed_spells[0])
        else:
            self.setSpellDetailHeaderHidden_(True)
            self.current_spell_school = ""
            self.layoutMainWindow()
            self.spell_detail_view.setString_("No matching spells.")
            self.spell_detail_view.setDiceRanges_([])
            self.resizeSpellDetailBody()

    def selectSpellResult_(self, sender):
        index = int(sender.tag())
        if index < 0 or index >= len(self.displayed_spells):
            return
        self.showSpellInDetail_(self.displayed_spells[index])

    def showSpellInDetail_(self, spell):
        title, meta, body = format_spell_for_detail(spell)
        self.current_spell_school = spell.school
        self.setSpellDetailHeaderHidden_(False)
        self.spell_detail_title_label.setStringValue_(title)
        italian_name = spell.italian_name.strip()
        if italian_name and normalize(italian_name) != normalize(spell.name):
            self.spell_detail_italian_label.setStringValue_(f"({italian_name})")
        else:
            self.spell_detail_italian_label.setStringValue_("")
        self.spell_detail_meta_label.setStringValue_(meta)
        self.applySpellDetailSchoolColor()

        flags = component_flags(spell.components)
        self.spell_v_box.setChecked_(flags["V"])
        self.spell_s_box.setChecked_(flags["S"])
        self.spell_m_box.setChecked_(flags["M"])
        self.spell_component_material_label.setStringValue_(component_material(spell.components))

        stats = [
            f"Range: {spell.range or '-'}",
            f"Duration: {spell.duration or '-'}",
        ]
        if spell.spell_lists:
            stats.append(f"Classes: {', '.join(spell.spell_lists)}")
        self.spell_stats_label.setStringValue_("\n".join(stats))

        attributed = attributed_spell_body(body)
        self.spell_detail_view.textStorage().setAttributedString_(attributed)
        self.spell_detail_view.setDiceRanges_(dice_ranges_for_body(body))
        self.layoutMainWindow()
        self.resizeSpellDetailBody()

    def openSpell_(self, spell):
        if spell is None:
            return
        self.current_tab = "spells"
        self.spell_search_field.setStringValue_(spell.name)
        self.spell_level_filter_popup.selectItemWithTitle_("Any Level")
        self.spell_school_filter_popup.selectItemWithTitle_("Any School")
        self.applyCurrentTab()
        self.refreshSpellResults()
        if spell not in self.displayed_spells:
            self.displayed_spells = [spell, *self.displayed_spells]
            self.ensureSpellResultRows_(len(self.displayed_spells))
            for index, button in enumerate(self.spell_result_buttons):
                if index >= len(self.displayed_spells):
                    button.setHidden_(True)
                    continue
                button.configureSpellResult_(self.displayed_spells[index])
                button.setHidden_(False)
            self.layoutMainWindow()
        self.showSpellInDetail_(spell)
        self.window.makeKeyAndOrderFront_(None)
