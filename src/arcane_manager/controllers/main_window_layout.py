from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    @objc.python_method
    def applyTheme(self):
        self.window.setBackgroundColor_(theme_color("app_bg"))
        style_layer(self.content_view, theme_color("app_bg"), None, 0)
        style_layer(self.sidebar_panel, theme_color("app_bg"), None, 0)
        for panel in (
            self.combat_panel,
            self.spell_panel,
            self.item_panel,
            self.item_scroll_calculator_panel,
            self.dice_panel,
            self.adventure_panel,
        ):
            style_layer(panel, theme_color("panel"), theme_color("border_soft"), 14, 1)
        style_layer(self.monster_sheet_drawer, theme_color("panel_alt"), theme_color("border_soft"), 12, 1)
        style_layer(self.sidebar_logo_label, theme_color("selection"), theme_color("link"), 10, 1)
        for label in self.party_member_labels:
            style_layer(label, theme_color("surface"), theme_color("border_soft"), 8, 1)
        for scroll in (self.dice_history_scroll, self.adventure_tree_scroll, self.adventure_editor_scroll, self.cart_scroll):
            style_layer(scroll, theme_color("surface_soft"), theme_color("border_soft"), 8, 1)
        style_layer(self.adventure_web_view, theme_color("adventure_reader_bg"), theme_color("border_soft"), 8, 1)
        style_layer(self.cart_overlay_backdrop, theme_color("app_bg", 0.72), None, 0)
        style_layer(self.cart_overlay_panel, theme_color("panel"), theme_color("border"), 14, 1)

        for button in (
            self.initiative_tab_button,
            self.spells_tab_button,
            self.items_tab_button,
            self.dice_tab_button,
            self.adventure_tab_button,
        ):
            if button is not None:
                style_layer(button, theme_color("surface"), theme_color("border_soft"), 8, 1)

        for button in (
            self.new_party_button,
            self.edit_party_button,
            self.delete_party_button,
            self.start_fight_button,
            self.monster_search_button,
            self.dice_clear_button,
            self.dice_roll_button,
            self.adventure_toggle_button,
            self.adventure_save_button,
            self.previous_turn_button,
            self.next_turn_button,
            self.clear_tracker_button,
            self.monster_sheet_close_button,
            self.monster_sheet_save_button,
            self.item_add_to_cart_button,
            self.scroll_add_to_cart_button,
            self.cart_button,
            self.cart_close_button,
            self.cart_checkout_button,
            *self.dice_preset_buttons,
        ):
            if button is not None:
                style_button_layer(button)

        for field in (
            self.monster_search_field,
            self.spell_search_field,
            self.item_search_field,
            self.scroll_calculator_spell_field,
        ):
            style_text_input(field)
        for popup in (
            self.party_popup,
            self.monster_cr_filter_popup,
            self.spell_level_filter_popup,
            self.spell_school_filter_popup,
            self.item_category_filter_popup,
            self.item_variant_popup,
            self.scroll_calculator_level_popup,
        ):
            popup.setNeedsDisplay_(True)

        muted_labels = (
            self.notes_hint,
            self.sidebar_footer_label,
            self.party_status_label,
            self.spell_detail_italian_label,
            self.dice_hint_label,
            self.dice_result_label,
            self.adventure_status_label,
            self.scroll_calculator_spell_label,
            self.scroll_calculator_level_label,
            self.scroll_calculator_match_label,
            self.scroll_calculator_rarity_caption_label,
            self.scroll_calculator_price_caption_label,
            self.scroll_calculator_status_label,
            self.cart_empty_label,
        )
        for label in muted_labels:
            label.setTextColor_(theme_color("muted"))
        for label in (self.turn_label, self.adventure_dirty_label):
            label.setTextColor_(theme_color("gold"))
        self.item_detail_meta_label.setTextColor_(theme_color("gold"))
        self.scroll_calculator_rarity_value_label.setTextColor_(theme_color("gold"))
        self.scroll_calculator_price_value_label.setTextColor_(theme_color("dice"))
        self.cart_total_label.setTextColor_(theme_color("dice"))
        for label in (
            self.spell_components_label,
            self.spell_component_material_label,
            self.spell_stats_label,
            self.item_detail_fields_label,
            self.item_scroll_calculator_title_label,
            self.cart_title_label,
        ):
            label.setTextColor_(theme_color("text"))
        self.applySpellDetailSchoolColor()
        self.monster_sheet_roll_label.setTextColor_(theme_color("dice"))
        self.dice_formula_label.setTextColor_(theme_color("dice"))

        self.notes_view.setTextColor_(theme_color("text"))
        self.notes_view.setBackgroundColor_(theme_color("surface"))
        self.dice_history_view.setTextColor_(theme_color("text"))
        self.dice_history_view.setBackgroundColor_(theme_color("surface_soft"))
        self.adventure_editor_view.setTextColor_(theme_color("text"))
        self.adventure_editor_view.setBackgroundColor_(theme_color("surface_soft"))
        self.spell_detail_view.setTextColor_(theme_color("text"))
        self.item_detail_view.setTextColor_(theme_color("text"))
        self.monster_sheet_body.setTextColor_(theme_color("text"))

        for collection in (
            self.monster_result_buttons,
            self.monster_add_buttons,
            self.spell_result_buttons,
            self.item_result_buttons,
            self.adventure_tree_buttons,
            self.monster_sheet_ability_buttons,
        ):
            for view in collection:
                view.setNeedsDisplay_(True)
        self.tracker_view.setNeedsDisplay_(True)
        self.applyCurrentTab()
        if self.adventure_is_editing:
            self.refreshAdventureControls()
        elif self.adventure_selected_note is not None:
            self.renderAdventureMarkdown_(self.adventure_last_saved_text)
        else:
            self.refreshAdventureWorkspace()

    def layoutMainWindow(self):
        bounds = self.content_view.bounds()
        width = int(bounds.size.width)
        height = int(bounds.size.height)

        def centered_control_rect(x: float, center_y: float, width: float, height: float):
            return NSMakeRect(x, center_y - height / 2, width, height)

        def centered_text_rect(label, x: float, center_y: float, width: float):
            cell_size = label.cell().cellSize()
            return centered_control_rect(x, center_y, width, max(1, cell_size.height))

        tab_y = height - 38
        self.initiative_tab_button.setFrame_(NSMakeRect(20, tab_y, 150, 30))
        self.spells_tab_button.setFrame_(NSMakeRect(178, tab_y, 86, 30))
        self.items_tab_button.setFrame_(NSMakeRect(272, tab_y, 82, 30))
        self.dice_tab_button.setFrame_(NSMakeRect(362, tab_y, 112, 30))
        self.adventure_tab_button.setFrame_(NSMakeRect(482, tab_y, 104, 30))
        content_height = height - 54
        sidebar_width = min(370, max(320, int(width * 0.29)))
        outer_gap = 20
        sidebar_tracker_gap = 12
        sidebar_margin = 24
        panel_x = sidebar_width + sidebar_tracker_gap
        panel_y = 20
        available_panel_width = max(420, width - panel_x - outer_gap)
        drawer_open = self.current_tab == "initiative" and (
            self.monster_sheet_combatant_index >= 0 or self.monster_sheet_creature is not None
        )
        drawer_gap = 16
        drawer_width = 0
        if drawer_open:
            preferred_drawer_width = min(420, max(320, int(width * 0.30)))
            max_drawer_width = available_panel_width - 360 - drawer_gap
            drawer_width = max(280, min(preferred_drawer_width, max_drawer_width))
            panel_width = max(340, available_panel_width - drawer_width - drawer_gap)
        else:
            panel_width = max(560, available_panel_width)
        panel_height = max(560, content_height - panel_y)
        party = self.selectedParty()
        visible_party_rows = len(self._valid_party_characters(party))
        sidebar_document_height = max(
            content_height,
            620 + visible_party_rows * 42,
        )

        self.sidebar_panel.setFrame_(NSMakeRect(0, 0, sidebar_width, content_height))
        self.sidebar_scroll.setFrame_(NSMakeRect(0, 0, sidebar_width, content_height))
        self.sidebar_content.setFrame_(NSMakeRect(0, 0, sidebar_width, sidebar_document_height))
        self.combat_panel.setFrame_(NSMakeRect(panel_x, panel_y, panel_width, panel_height))
        self.monster_sheet_drawer.setHidden_(not drawer_open)
        if drawer_open:
            drawer_x = panel_x + panel_width + drawer_gap
            self.monster_sheet_drawer.setFrame_(NSMakeRect(drawer_x, panel_y, drawer_width, panel_height))
            drawer_margin = 20
            drawer_inner_width = max(240, drawer_width - drawer_margin * 2)
            drawer_top = panel_height - 48
            self.monster_sheet_title.setFrame_(NSMakeRect(drawer_margin, drawer_top - 8, max(120, drawer_inner_width - 88), 40))
            self.monster_sheet_close_button.setFrame_(NSMakeRect(drawer_width - drawer_margin - 72, drawer_top, 72, 28))
            ability_y = panel_height - 156
            ability_button_width = min(44, max(34, (drawer_inner_width - 5 * 6) / 6))
            ability_gap = (drawer_inner_width - ability_button_width * 6) / 5 if len(self.monster_sheet_ability_buttons) > 1 else 0
            for index, button in enumerate(self.monster_sheet_ability_buttons):
                button.setFrame_(NSMakeRect(drawer_margin + index * (ability_button_width + ability_gap), ability_y, ability_button_width, 76))
            scroll_y = 20
            scroll_height = max(300, ability_y - 36)
            self.monster_sheet_scroll.setFrame_(NSMakeRect(drawer_margin, scroll_y, drawer_inner_width, scroll_height))
            body_width = max(220, drawer_inner_width - 24)
            self.monster_sheet_body.textContainer().setContainerSize_(NSMakeSize(body_width, 100000))
            self.monster_sheet_body.layoutManager().ensureLayoutForTextContainer_(self.monster_sheet_body.textContainer())
            body_height = max(
                scroll_height,
                self.monster_sheet_body.layoutManager().usedRectForTextContainer_(self.monster_sheet_body.textContainer()).size.height + 24,
            )
            self.monster_sheet_body.setFrame_(NSMakeRect(0, 0, body_width, body_height))
        self.spell_panel.setFrame_(NSMakeRect(20, 20, width - 40, max(520, content_height - 20)))
        item_tab_x = 20
        item_tab_y = 20
        item_tab_width = max(900, width - 40)
        item_tab_height = max(520, content_height - 20)
        item_panel_gap = 16
        item_calculator_width = min(420, max(300, item_tab_width * 0.30))
        item_left_width = max(560, item_tab_width - item_calculator_width - item_panel_gap)
        self.item_panel.setFrame_(NSMakeRect(item_tab_x, item_tab_y, item_left_width, item_tab_height))
        item_calculator_x = item_tab_x + item_left_width + item_panel_gap
        self.item_scroll_calculator_panel.setFrame_(
            NSMakeRect(item_calculator_x, item_tab_y, item_calculator_width, item_tab_height)
        )
        calculator_margin = 28
        self.item_scroll_calculator_title_label.setFrame_(
            NSMakeRect(
                item_calculator_x + calculator_margin,
                item_tab_y + item_tab_height - calculator_margin - 30,
                max(160, item_calculator_width - calculator_margin * 2),
                30,
            )
        )
        calculator_x = item_calculator_x + calculator_margin
        calculator_width = max(160, item_calculator_width - calculator_margin * 2)
        calculator_top = item_tab_y + item_tab_height - calculator_margin - 46
        self.scroll_calculator_spell_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 28, calculator_width, 18))
        self.scroll_calculator_spell_field.setFrame_(NSMakeRect(calculator_x, calculator_top - 68, calculator_width, 34))
        self.scroll_calculator_level_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 112, calculator_width, 18))
        self.scroll_calculator_level_popup.setFrame_(NSMakeRect(calculator_x, calculator_top - 152, calculator_width, 34))
        self.scroll_calculator_match_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 184, calculator_width, 22))
        self.scroll_calculator_rarity_caption_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 238, calculator_width, 18))
        self.scroll_calculator_rarity_value_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 270, calculator_width, 28))
        self.scroll_calculator_price_caption_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 326, calculator_width, 18))
        self.scroll_calculator_price_value_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 374, calculator_width, 40))
        self.scroll_calculator_status_label.setFrame_(NSMakeRect(calculator_x, calculator_top - 416, calculator_width, 38))
        self.scroll_add_to_cart_button.setFrame_(NSMakeRect(calculator_x, calculator_top - 464, min(160, calculator_width), 34))
        cart_button_width = min(240, max(180, item_calculator_width - calculator_margin * 2))
        self.cart_button.setFrame_(
            NSMakeRect(
                item_calculator_x + item_calculator_width - calculator_margin - cart_button_width,
                item_tab_y + calculator_margin,
                cart_button_width,
                38,
            )
        )

        overlay_panel_width = min(660, max(520, width * 0.58))
        overlay_panel_height = min(540, max(420, height * 0.66))
        overlay_x = (width - overlay_panel_width) / 2
        overlay_y = (height - overlay_panel_height) / 2
        self.cart_overlay_backdrop.setFrame_(NSMakeRect(0, 0, width, height))
        self.cart_overlay_panel.setFrame_(NSMakeRect(overlay_x, overlay_y, overlay_panel_width, overlay_panel_height))
        overlay_margin = 28
        overlay_inner_width = overlay_panel_width - overlay_margin * 2
        overlay_top = overlay_y + overlay_panel_height - overlay_margin
        self.cart_title_label.setFrame_(NSMakeRect(overlay_x + overlay_margin, overlay_top - 34, overlay_inner_width - 112, 34))
        self.cart_close_button.setFrame_(NSMakeRect(overlay_x + overlay_panel_width - overlay_margin - 90, overlay_top - 34, 90, 34))
        footer_y = overlay_y + overlay_margin
        self.cart_checkout_button.setFrame_(NSMakeRect(overlay_x + overlay_panel_width - overlay_margin - 120, footer_y, 120, 34))
        self.cart_total_label.setFrame_(NSMakeRect(overlay_x + overlay_margin, footer_y + 2, overlay_inner_width - 140, 30))
        scroll_y = footer_y + 54
        scroll_height = max(220, overlay_top - 78 - scroll_y)
        self.cart_scroll.setFrame_(NSMakeRect(overlay_x + overlay_margin, scroll_y, overlay_inner_width, scroll_height))
        self.cart_empty_label.setFrame_(NSMakeRect(overlay_x + overlay_margin + 18, scroll_y + scroll_height - 44, overlay_inner_width - 36, 24))
        self.layoutCartRows()

        y = sidebar_document_height - 52
        self.sidebar_logo_label.setFrame_(NSMakeRect(sidebar_margin, y - 2, 36, 36))
        self.notes_title.setFrame_(NSMakeRect(sidebar_margin + 50, y + 4, sidebar_width - sidebar_margin * 2 - 50, 24))
        self.notes_hint.setFrame_(NSMakeRect(sidebar_margin + 50, y - 17, sidebar_width - sidebar_margin * 2 - 50, 20))
        self.sidebar_footer_label.setFrame_(NSMakeRect(sidebar_margin, 18, sidebar_width - sidebar_margin * 2, 24))
        self.notes_scroll.setFrame_(NSMakeRect(sidebar_margin, 20, sidebar_width - sidebar_margin * 2, 120))
        self.notes_view.setFrame_(NSMakeRect(0, 0, sidebar_width - sidebar_margin * 2 - 24, 120))

        y -= 18
        self.party_popup.setFrame_(NSMakeRect(sidebar_margin, y, sidebar_width - sidebar_margin * 2, 34))
        y -= 70
        self.party_label.setFrame_(NSMakeRect(sidebar_margin, y + 4, 120, 24))
        self.new_party_button.setFrame_(NSMakeRect(sidebar_width - sidebar_margin - 34, y, 34, 28))
        self.edit_party_button.setFrame_(NSMakeRect(sidebar_width - sidebar_margin - 104, y, 62, 28))
        self.delete_party_button.setFrame_(NSMakeRect(sidebar_width - sidebar_margin - 180, y, 68, 28))
        self.start_fight_button.setFrame_(NSMakeRect(sidebar_width - sidebar_margin - 222, y, 34, 28))
        y -= 46

        card_width = sidebar_width - sidebar_margin * 2
        party_row_height = 36
        party_row_step = 42
        for index, label in enumerate(self.party_member_labels):
            label.setFrame_(NSMakeRect(sidebar_margin, y - index * party_row_step, card_width, party_row_height))
        checkbox_size = 18
        checkbox_gap = 10
        checkbox_x = sidebar_margin + card_width - checkbox_size - 12
        for index, checkbox in enumerate(self.party_member_checkboxes):
            row_bottom = y - index * party_row_step
            checkbox_y = row_bottom + (party_row_height - checkbox_size) / 2
            checkbox.setFrame_(NSMakeRect(checkbox_x, checkbox_y, checkbox_size, checkbox_size))
        for index, icon_view in enumerate(self.party_member_icon_views):
            row_bottom = y - index * party_row_step
            icon_view.setFrame_(NSMakeRect(sidebar_margin + 18, row_bottom + 8, 20, 20))
        class_w = min(136, max(86, int(card_width * 0.32)))
        icon_column_w = 50
        column_gap = 8
        row_name_x = sidebar_margin + icon_column_w
        row_class_x = checkbox_x - checkbox_gap - class_w
        row_name_w = max(62, row_class_x - row_name_x - column_gap)
        for index in range(len(self.party_member_labels)):
            row_bottom = y - index * party_row_step
            text_height = 20
            row_y = row_bottom + (party_row_height - text_height) / 2
            self.party_member_name_labels[index].setFrame_(NSMakeRect(row_name_x, row_y, row_name_w, text_height))
            self.party_member_class_labels[index].setFrame_(NSMakeRect(row_class_x, row_y, class_w, text_height))
            self.party_member_ac_labels[index].setFrame_(NSMakeRect(checkbox_x, row_y, 0, text_height))
        y -= visible_party_rows * party_row_step + 8
        self.party_status_label.setFrame_(NSMakeRect(sidebar_margin, y, card_width, 38))

        y -= 34
        self.monster_label.setFrame_(NSMakeRect(sidebar_margin, y + 4, 140, 24))
        y -= 40
        cr_filter_w = 90
        cr_filter_gap = 10
        search_w = max(160, card_width - cr_filter_w - cr_filter_gap)
        self.monster_search_field.setFrame_(NSMakeRect(sidebar_margin, y - 3, search_w, 34))
        self.monster_cr_filter_popup.setFrame_(NSMakeRect(sidebar_margin + search_w + cr_filter_gap, y - 3, cr_filter_w, 34))
        self.monster_search_button.setFrame_(NSMakeRect(sidebar_margin + card_width - 76, y, 76, 28))
        y -= 19
        results_height = max(140, y - 18)
        self.monster_results_scroll.setFrame_(NSMakeRect(sidebar_margin, 18, card_width, results_height))
        self.monster_results_indicator.setFrame_(NSMakeRect(sidebar_margin + card_width - 11, 18, 8, results_height))
        results_document_height = max(results_height, len(self.monster_results) * MONSTER_RESULT_ROW_STEP)
        self.monster_results_content.setFrame_(NSMakeRect(0, 0, card_width - 18, results_document_height))
        self.monster_results_indicator.setNeedsDisplay_(True)
        visible_monster_rows = min(len(self.monster_results), int(results_height // MONSTER_RESULT_ROW_STEP) + 4)
        self.ensureMonsterResultRows_(visible_monster_rows)
        self.updateMonsterResultRows_(False)
        top_scroll_y = max(0, sidebar_document_height - content_height)
        self.sidebar_scroll.contentView().scrollToPoint_(NSMakePoint(0, top_scroll_y))
        self.sidebar_scroll.reflectScrolledClipView_(self.sidebar_scroll.contentView())

        header_y = panel_y + panel_height - 58
        title_width = min(220, max(140, panel_width - 64))
        self.tracker_title.setFrame_(NSMakeRect(panel_x + 32, header_y, title_width, 28))
        turn_x = panel_x + 32 + title_width + 12
        turn_width = max(0, panel_x + panel_width - 28 - turn_x)
        self.turn_label.setFrame_(NSMakeRect(turn_x, header_y + 2, turn_width, 24))

        compact_tracker_controls = panel_width < 540
        bottom_height = 102 if compact_tracker_controls else 66
        if compact_tracker_controls:
            self.clear_tracker_button.setFrame_(NSMakeRect(panel_x + 28, panel_y + 18, 132, 34))
            nav_width = 196
            nav_x = panel_x + max(28, panel_width - nav_width - 28)
            self.previous_turn_button.setFrame_(NSMakeRect(nav_x, panel_y + 58, 104, 34))
            self.next_turn_button.setFrame_(NSMakeRect(nav_x + 116, panel_y + 58, 80, 34))
        else:
            self.clear_tracker_button.setFrame_(NSMakeRect(panel_x + 28, panel_y + 18, 150, 34))
            self.previous_turn_button.setFrame_(NSMakeRect(panel_x + panel_width - 244, panel_y + 18, 104, 34))
            self.next_turn_button.setFrame_(NSMakeRect(panel_x + panel_width - 128, panel_y + 18, 100, 34))

        tracker_x = panel_x + 24
        tracker_y = panel_y + bottom_height
        tracker_width = panel_width - 48
        tracker_height = max(320, panel_height - bottom_height - 88)
        self.tracker_scroll.setFrame_(NSMakeRect(tracker_x, tracker_y, tracker_width, tracker_height))
        self.tracker_view.setFrame_(NSMakeRect(0, 0, max(780, tracker_width - 24), max(tracker_height, self.tracker_view.frame().size.height)))

        spell_margin = 44
        spell_panel_frame = self.spell_panel.frame()
        spell_x = spell_panel_frame.origin.x + spell_margin
        spell_y = spell_panel_frame.origin.y + spell_margin
        spell_width = spell_panel_frame.size.width - spell_margin * 2
        spell_height = spell_panel_frame.size.height - spell_margin * 2
        list_width = min(430, max(320, spell_width * 0.38))
        self.spell_search_field.setFrame_(NSMakeRect(spell_x, spell_y + spell_height - 42, list_width, 34))
        filter_gap = 10
        level_filter_w = min(128, max(108, list_width * 0.36))
        school_filter_w = max(140, list_width - level_filter_w - filter_gap)
        filter_y = spell_y + spell_height - 84
        self.spell_level_filter_popup.setFrame_(NSMakeRect(spell_x, filter_y, level_filter_w, 34))
        self.spell_school_filter_popup.setFrame_(NSMakeRect(spell_x + level_filter_w + filter_gap, filter_y, school_filter_w, 34))
        results_height = max(120, filter_y - spell_y - 12)
        self.spell_results_scroll.setFrame_(NSMakeRect(spell_x, spell_y, list_width, results_height))
        results_document_width = max(120, list_width - 18)
        results_document_height = max(results_height, len(self.displayed_spells) * SPELL_RESULT_ROW_STEP)
        self.spell_results_content.setFrame_(NSMakeRect(0, 0, results_document_width, results_document_height))
        visible_spell_rows = min(len(self.displayed_spells), int(results_height // SPELL_RESULT_ROW_STEP) + 4)
        self.ensureSpellResultRows_(visible_spell_rows)
        self.updateSpellResultRows_(False)
        detail_x = spell_x + list_width + 28
        detail_width = max(300, spell_width - list_width - 28)
        if self.spell_detail_title_label.isHidden():
            self.spell_detail_scroll.setFrame_(NSMakeRect(detail_x, spell_y, detail_width, spell_height))
            self.spell_detail_view.textContainer().setContainerSize_(NSMakeSize(max(120, detail_width - 24), 100000))
            self.spell_detail_view.setFrame_(
                NSMakeRect(0, 0, detail_width - 24, max(spell_height, self.spell_detail_view.frame().size.height))
            )
        else:
            detail_top = spell_y + spell_height
            self.spell_detail_title_label.setFrame_(NSMakeRect(detail_x, detail_top - 36, detail_width, 32))
            self.spell_detail_italian_label.setFrame_(NSMakeRect(detail_x, detail_top - 60, detail_width, 22))
            self.spell_detail_meta_label.setFrame_(NSMakeRect(detail_x, detail_top - 92, detail_width, 24))

            component_y = detail_top - 128
            component_row_height = 24
            component_center_y = component_y + component_row_height / 2
            component_box_size = 16
            self.spell_components_label.setFrame_(centered_text_rect(self.spell_components_label, detail_x, component_center_y, 92))
            component_x = detail_x + 104
            for label, box in (
                (self.spell_v_label, self.spell_v_box),
                (self.spell_s_label, self.spell_s_box),
                (self.spell_m_label, self.spell_m_box),
            ):
                label.setFrame_(centered_text_rect(label, component_x, component_center_y, 16))
                box.setFrame_(centered_control_rect(component_x + 20, component_center_y, component_box_size, component_box_size))
                component_x += 52
            material_x = component_x + 2
            material_width = detail_x + detail_width - material_x
            stats_height = 76
            stats_y = component_y - stats_height - 10
            if material_width >= 140:
                self.spell_component_material_label.setFrame_(
                    centered_text_rect(self.spell_component_material_label, material_x, component_center_y, material_width)
                )
            else:
                self.spell_component_material_label.setFrame_(NSMakeRect(detail_x, component_y - 30, detail_width, 28))
                stats_y = component_y - stats_height - 38
            self.spell_stats_label.setFrame_(NSMakeRect(detail_x, stats_y, detail_width, stats_height))

            scroll_top = stats_y - 12
            scroll_height = max(160, scroll_top - spell_y)
            self.spell_detail_scroll.setFrame_(NSMakeRect(detail_x, spell_y, detail_width, scroll_height))
            self.spell_detail_view.textContainer().setContainerSize_(NSMakeSize(max(120, detail_width - 24), 100000))
            self.spell_detail_view.setFrame_(
                NSMakeRect(0, 0, detail_width - 24, max(scroll_height, self.spell_detail_view.frame().size.height))
            )

        item_margin = 32
        item_panel_frame = self.item_panel.frame()
        item_x = item_panel_frame.origin.x + item_margin
        item_y = item_panel_frame.origin.y + item_margin
        item_width = item_panel_frame.size.width - item_margin * 2
        item_height = item_panel_frame.size.height - item_margin * 2
        item_list_width = min(430, max(300, item_width * 0.38))
        item_filter_gap = 10
        item_category_filter_w = min(170, max(134, item_list_width * 0.42))
        item_search_w = max(160, item_list_width - item_category_filter_w - item_filter_gap)
        item_top = item_y + item_height
        self.item_search_field.setFrame_(NSMakeRect(item_x, item_top - 42, item_search_w, 34))
        self.item_category_filter_popup.setFrame_(
            NSMakeRect(item_x + item_search_w + item_filter_gap, item_top - 42, item_category_filter_w, 34)
        )
        item_results_height = max(120, item_height - 54)
        self.item_results_scroll.setFrame_(NSMakeRect(item_x, item_y, item_list_width, item_results_height))
        item_results_document_width = max(120, item_list_width - 18)
        item_results_document_height = max(item_results_height, len(self.displayed_items) * SPELL_RESULT_ROW_STEP)
        self.item_results_content.setFrame_(NSMakeRect(0, 0, item_results_document_width, item_results_document_height))
        visible_item_rows = min(len(self.displayed_items), int(item_results_height // SPELL_RESULT_ROW_STEP) + 4)
        self.ensureItemResultRows_(visible_item_rows)
        self.updateItemResultRows_(False)

        item_detail_gap = 24
        item_detail_x = item_x + item_list_width + item_detail_gap
        item_detail_width = max(240, item_width - item_list_width - item_detail_gap)
        if self.item_detail_title_label.isHidden():
            self.item_detail_scroll.setFrame_(NSMakeRect(item_detail_x, item_y, item_detail_width, item_height))
            self.item_detail_view.textContainer().setContainerSize_(NSMakeSize(max(120, item_detail_width - 24), 100000))
            self.item_detail_view.setFrame_(
                NSMakeRect(0, 0, item_detail_width - 24, max(item_height, self.item_detail_view.frame().size.height))
            )
        else:
            self.item_detail_title_label.setFrame_(NSMakeRect(item_detail_x, item_top - 36, item_detail_width, 32))
            self.item_detail_meta_label.setFrame_(NSMakeRect(item_detail_x, item_top - 68, item_detail_width, 24))
            popup_bottom = item_top - 72
            if not self.item_variant_popup.isHidden():
                popup_width = min(280, max(180, item_detail_width * 0.42))
                self.item_variant_popup.setFrame_(NSMakeRect(item_detail_x, item_top - 106, popup_width, 28))
                popup_bottom = item_top - 110
            action_bottom = popup_bottom
            if not self.item_add_to_cart_button.isHidden():
                self.item_add_to_cart_button.setFrame_(NSMakeRect(item_detail_x, popup_bottom - 38, 132, 32))
                action_bottom = popup_bottom - 42
            fields_text = str(self.item_detail_fields_label.stringValue())
            field_lines = len([line for line in fields_text.splitlines() if line.strip()])
            fields_height = 0 if field_lines == 0 else min(156, max(24, field_lines * 20))
            fields_y = action_bottom - 8 - fields_height
            self.item_detail_fields_label.setFrame_(NSMakeRect(item_detail_x, fields_y, item_detail_width, fields_height))
            scroll_top = fields_y - 14 if fields_height > 0 else item_top - 82
            scroll_height = max(160, scroll_top - item_y)
            self.item_detail_scroll.setFrame_(NSMakeRect(item_detail_x, item_y, item_detail_width, scroll_height))
            self.item_detail_view.textContainer().setContainerSize_(NSMakeSize(max(120, item_detail_width - 24), 100000))
            self.item_detail_view.setFrame_(
                NSMakeRect(0, 0, item_detail_width - 24, max(scroll_height, self.item_detail_view.frame().size.height))
            )

        dice_panel_frame = self.dice_panel.frame()
        if dice_panel_frame.size.width <= 1:
            self.dice_panel.setFrame_(NSMakeRect(20, 20, width - 40, max(520, content_height - 20)))
            dice_panel_frame = self.dice_panel.frame()
        self.dice_panel.setFrame_(NSMakeRect(20, 20, width - 40, max(520, content_height - 20)))
        dice_panel_frame = self.dice_panel.frame()
        dice_top = dice_panel_frame.origin.y + dice_panel_frame.size.height - 78
        self.dice_title_label.setFrame_(NSMakeRect(dice_panel_frame.origin.x + 44, dice_top, 320, 34))
        self.dice_hint_label.setFrame_(NSMakeRect(dice_panel_frame.origin.x + 44, dice_top - 28, min(640, dice_panel_frame.size.width - 88), 24))
        self.dice_hint_label.setHidden_(True)

        history_w = min(380, max(300, dice_panel_frame.size.width * 0.30))
        history_x = dice_panel_frame.origin.x + dice_panel_frame.size.width - history_w - 44
        history_top = dice_top
        history_h = max(250, dice_panel_frame.size.height - 150)
        self.dice_history_title_label.setFrame_(NSMakeRect(history_x, history_top + 4, history_w, 24))
        self.dice_history_scroll.setFrame_(NSMakeRect(history_x, dice_panel_frame.origin.y + 44, history_w, history_h))
        self.dice_history_view.setFrame_(NSMakeRect(0, 0, max(240, history_w - 24), max(history_h, self.dice_history_view.frame().size.height)))

        controls_right = history_x - 34
        controls_left = dice_panel_frame.origin.x + 44
        controls_width = max(420, controls_right - controls_left)
        dice_center_x = controls_left + controls_width / 2
        controls_y = dice_top - 104

        die_button_w = 82
        die_button_gap = 14
        die_total_width = len(self.dice_preset_buttons) * die_button_w + (len(self.dice_preset_buttons) - 1) * die_button_gap
        die_x = dice_center_x - die_total_width / 2
        for index, button in enumerate(self.dice_preset_buttons):
            button.setFrame_(NSMakeRect(die_x + index * (die_button_w + die_button_gap), controls_y, die_button_w, 58))

        formula_width = min(680, dice_panel_frame.size.width - 88)
        formula_width = min(formula_width, max(360, controls_width))
        self.dice_formula_label.setFrame_(NSMakeRect(dice_center_x - formula_width / 2, controls_y - 92, formula_width, 46))
        self.dice_result_label.setFrame_(NSMakeRect(dice_center_x - formula_width / 2, controls_y - 126, formula_width, 24))

        action_y = controls_y - 184
        self.dice_clear_button.setFrame_(NSMakeRect(dice_center_x - 136, action_y, 116, 34))
        self.dice_roll_button.setFrame_(NSMakeRect(dice_center_x + 20, action_y, 136, 34))

        self.adventure_panel.setFrame_(NSMakeRect(20, 20, width - 40, max(520, content_height - 20)))
        adventure_frame = self.adventure_panel.frame()
        adventure_margin = 28
        adventure_x = adventure_frame.origin.x + adventure_margin
        adventure_y = adventure_frame.origin.y + adventure_margin
        adventure_width = adventure_frame.size.width - adventure_margin * 2
        adventure_height = adventure_frame.size.height - adventure_margin * 2
        detail_gap = 22
        divider_width = 8
        min_tree_width = 180
        max_tree_width = max(min_tree_width, min(520, int(adventure_width - detail_gap - 420)))
        tree_width = min(max_tree_width, max(min_tree_width, int(self.adventure_tree_width)))
        if tree_width != int(self.adventure_tree_width):
            self.adventure_tree_width = tree_width
        toolbar_h = 48
        self.adventure_title_label.setFrame_(NSMakeRect(adventure_x, adventure_y + adventure_height - 34, tree_width, 30))
        self.adventure_tree_scroll.setFrame_(NSMakeRect(adventure_x, adventure_y, tree_width, adventure_height - toolbar_h))
        tree_document_width = max(180, tree_width - 18)
        tree_document_height = max(adventure_height - toolbar_h, len(self.adventure_flat_nodes) * 28 + 12)
        self.adventure_tree_content.setFrame_(NSMakeRect(0, 0, tree_document_width, tree_document_height))
        for index, button in enumerate(self.adventure_tree_buttons):
            button.setFrame_(NSMakeRect(4, 6 + index * 28, max(80, tree_document_width - 8), 26))

        divider_x = adventure_x + tree_width + (detail_gap - divider_width) / 2
        self.adventure_divider_view.setFrame_(NSMakeRect(divider_x, adventure_y, divider_width, adventure_height - toolbar_h))
        detail_x = adventure_x + tree_width + detail_gap
        detail_width = max(360, adventure_width - tree_width - detail_gap)
        detail_top = adventure_y + adventure_height
        button_y = detail_top - 36
        save_button_width = 82
        toggle_button_width = 86
        control_gap = 8
        controls_right = detail_x + detail_width
        if self.adventure_is_editing:
            save_x = controls_right - save_button_width
            toggle_x = save_x - control_gap - toggle_button_width
            status_right = toggle_x - 16
            self.adventure_save_button.setFrame_(NSMakeRect(save_x, button_y, save_button_width, 32))
            self.adventure_toggle_button.setFrame_(NSMakeRect(toggle_x, button_y, toggle_button_width, 32))
            self.adventure_dirty_label.setFrame_(NSMakeRect(max(detail_x, toggle_x - 128), button_y + 6, 112, 22))
        else:
            toggle_x = controls_right - toggle_button_width
            status_right = toggle_x - 16
            self.adventure_toggle_button.setFrame_(NSMakeRect(toggle_x, button_y, toggle_button_width, 32))
            self.adventure_save_button.setFrame_(NSMakeRect(controls_right - save_button_width, button_y, save_button_width, 32))
            self.adventure_dirty_label.setFrame_(NSMakeRect(status_right, button_y + 6, 0, 22))
        self.adventure_status_label.setFrame_(NSMakeRect(detail_x, button_y + 5, max(120, status_right - detail_x), 22))
        content_rect = NSMakeRect(detail_x, adventure_y, detail_width, adventure_height - toolbar_h)
        self.adventure_web_view.setFrame_(content_rect)
        self.adventure_editor_scroll.setFrame_(content_rect)
        editor_width = max(200, detail_width - 18)
        editor_height = max(content_rect.size.height, self.adventure_editor_view.frame().size.height)
        self.adventure_editor_view.textContainer().setContainerSize_(NSMakeSize(editor_width - 28, 100000))
        self.adventure_editor_view.setFrame_(NSMakeRect(0, 0, editor_width, editor_height))

    @objc.python_method
    def resizeAdventureTreeToWindowX_(self, window_x: float):
        if self.current_tab != "adventure":
            return
        adventure_frame = self.adventure_panel.frame()
        adventure_margin = 28
        adventure_x = adventure_frame.origin.x + adventure_margin
        adventure_width = adventure_frame.size.width - adventure_margin * 2
        detail_gap = 22
        min_tree_width = 180
        max_tree_width = max(min_tree_width, min(520, int(adventure_width - detail_gap - 420)))
        tree_width = int(min(max_tree_width, max(min_tree_width, float(window_x) - adventure_x - detail_gap / 2)))
        if tree_width == int(self.adventure_tree_width):
            return
        self.adventure_tree_width = tree_width
        defaults = NSUserDefaults.standardUserDefaults()
        defaults.setInteger_forKey_(tree_width, ADVENTURE_TREE_WIDTH_PREF)
        defaults.synchronize()
        self.layoutMainWindow()
