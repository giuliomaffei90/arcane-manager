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

    @objc.python_method
    def clearHoverStatesForViews_(self, views):
        for view in views:
            if hasattr(view, "clearHoverState"):
                view.clearHoverState()

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

        for index in range(count, len(self.monster_result_buttons)):
            self.monster_result_buttons[index].setHidden_(True)
            self.monster_result_buttons[index].clearHoverState()
            if index < len(self.monster_add_buttons):
                self.monster_add_buttons[index].setHidden_(True)
                self.monster_add_buttons[index].clearHoverState()

    @objc.python_method
    def updateMonsterResultRows_(self, force_configure: bool):
        if self.monster_results_scroll is None:
            return
        clip_view = self.monster_results_scroll.contentView()
        viewport_height = max(0, float(clip_view.bounds().size.height))
        visible_count = min(len(self.monster_results), int(viewport_height // MONSTER_RESULT_ROW_STEP) + 4)
        self.ensureMonsterResultRows_(visible_count)

        content_width = max(0, float(self.monster_results_content.frame().size.width))
        add_w = 30
        result_gap = 10
        result_w = max(180, content_width - add_w - result_gap)
        first_index = max(0, int(float(clip_view.bounds().origin.y) // MONSTER_RESULT_ROW_STEP) - 1)
        first_index = min(first_index, max(0, len(self.monster_results) - visible_count))

        for pool_index, button in enumerate(self.monster_result_buttons):
            add_button = self.monster_add_buttons[pool_index] if pool_index < len(self.monster_add_buttons) else None
            result_index = first_index + pool_index
            if pool_index >= visible_count or result_index >= len(self.monster_results):
                button.setHidden_(True)
                button.clearHoverState()
                if add_button is not None:
                    add_button.setHidden_(True)
                    add_button.clearHoverState()
                continue

            row_y = result_index * MONSTER_RESULT_ROW_STEP
            if force_configure or int(button.tag()) != result_index or button.isHidden():
                button.configureMonsterResult_(self.monster_results[result_index])
            button.setTag_(result_index)
            button.setFrame_(NSMakeRect(0, row_y, result_w, MONSTER_RESULT_ROW_HEIGHT))
            button.setHidden_(False)
            if add_button is not None:
                add_button.setTag_(result_index)
                add_button.setFrame_(NSMakeRect(result_w + result_gap, row_y, add_w, MONSTER_RESULT_ROW_HEIGHT))
                add_button.setHidden_(False)

    def monsterResultsBoundsDidChange_(self, _notification):
        self.clearHoverStatesForViews_([*self.monster_result_buttons, *self.monster_add_buttons])
        self.updateMonsterResultRows_(False)
        self.monster_results_indicator.setNeedsDisplay_(True)

    def searchMonsters_(self, _sender):
        query = str(self.monster_search_field.stringValue()).strip()
        self.monster_results = search_creatures(query, self.creatures, self.selectedMonsterCrFilter())
        self.clearHoverStatesForViews_([*self.monster_result_buttons, *self.monster_add_buttons])
        if self.monster_results_scroll is not None:
            self.layoutMainWindow()
            self.monster_results_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.monster_results_scroll.reflectScrolledClipView_(self.monster_results_scroll.contentView())
            self.updateMonsterResultRows_(True)
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

        for index in range(count, len(self.spell_result_buttons)):
            self.spell_result_buttons[index].setHidden_(True)
            self.spell_result_buttons[index].clearHoverState()

    @objc.python_method
    def updateSpellResultRows_(self, force_configure: bool):
        if self.spell_results_scroll is None:
            return
        clip_view = self.spell_results_scroll.contentView()
        viewport_height = max(0, float(clip_view.bounds().size.height))
        visible_count = min(len(self.displayed_spells), int(viewport_height // SPELL_RESULT_ROW_STEP) + 4)
        self.ensureSpellResultRows_(visible_count)

        content_width = max(120, float(self.spell_results_content.frame().size.width))
        first_index = max(0, int(float(clip_view.bounds().origin.y) // SPELL_RESULT_ROW_STEP) - 1)
        first_index = min(first_index, max(0, len(self.displayed_spells) - visible_count))

        for pool_index, button in enumerate(self.spell_result_buttons):
            result_index = first_index + pool_index
            if pool_index >= visible_count or result_index >= len(self.displayed_spells):
                button.setHidden_(True)
                button.clearHoverState()
                continue

            row_y = result_index * SPELL_RESULT_ROW_STEP
            if force_configure or int(button.tag()) != result_index or button.isHidden():
                button.configureSpellResult_(self.displayed_spells[result_index])
            button.setTag_(result_index)
            button.setFrame_(NSMakeRect(0, row_y, content_width, SPELL_RESULT_ROW_HEIGHT))
            button.setHidden_(False)

    def spellResultsBoundsDidChange_(self, _notification):
        self.clearHoverStatesForViews_(self.spell_result_buttons)
        self.updateSpellResultRows_(False)

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
        self.clearHoverStatesForViews_(self.spell_result_buttons)
        if self.spell_results_scroll is not None:
            self.layoutMainWindow()
            self.spell_results_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.spell_results_scroll.reflectScrolledClipView_(self.spell_results_scroll.contentView())
            self.updateSpellResultRows_(True)
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
            ("Range", spell.range or "-"),
            ("Duration", spell.duration or "-"),
            ("Ritual", "Yes" if spell.ritual else "No"),
        ]
        if spell.spell_lists:
            stats.append(("Classes", ", ".join(spell.spell_lists)))
        self.spell_stats_label.setAttributedStringValue_(attributed_spell_stats(stats))

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
            self.clearHoverStatesForViews_(self.spell_result_buttons)
            self.layoutMainWindow()
            self.updateSpellResultRows_(True)
        self.showSpellInDetail_(spell)
        self.window.makeKeyAndOrderFront_(None)
