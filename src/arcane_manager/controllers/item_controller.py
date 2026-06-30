from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    def selectedItemCategoryFilter(self) -> str | None:
        selected = self.item_category_filter_popup.selectedItem()
        title = str(selected.title()) if selected is not None else ""
        if not title or title == "Any Category":
            return None
        return title

    def ensureItemResultRows_(self, count: int):
        while len(self.item_result_buttons) < count:
            index = len(self.item_result_buttons)
            button = SearchResultButton.alloc().initWithFrame_(NSMakeRect(0, 0, 100, SPELL_RESULT_ROW_HEIGHT))
            button.setTarget_(self)
            button.setAction_("selectItemResult:")
            button.setTag_(index)
            button.setHidden_(True)
            self.item_result_buttons.append(button)
            self.item_results_content.addSubview_(button)

        for index in range(count, len(self.item_result_buttons)):
            self.item_result_buttons[index].setHidden_(True)
            self.item_result_buttons[index].clearHoverState()

    @objc.python_method
    def updateItemResultRows_(self, force_configure: bool):
        if self.item_results_scroll is None:
            return
        clip_view = self.item_results_scroll.contentView()
        viewport_height = max(0, float(clip_view.bounds().size.height))
        visible_count = min(len(self.displayed_items), int(viewport_height // SPELL_RESULT_ROW_STEP) + 4)
        self.ensureItemResultRows_(visible_count)

        content_width = max(120, float(self.item_results_content.frame().size.width))
        first_index = max(0, int(float(clip_view.bounds().origin.y) // SPELL_RESULT_ROW_STEP) - 1)
        first_index = min(first_index, max(0, len(self.displayed_items) - visible_count))

        for pool_index, button in enumerate(self.item_result_buttons):
            result_index = first_index + pool_index
            if pool_index >= visible_count or result_index >= len(self.displayed_items):
                button.setHidden_(True)
                button.clearHoverState()
                continue

            row_y = result_index * SPELL_RESULT_ROW_STEP
            if force_configure or int(button.tag()) != result_index or button.isHidden():
                button.configureItemResult_(self.displayed_items[result_index])
            button.setTag_(result_index)
            button.setFrame_(NSMakeRect(0, row_y, content_width, SPELL_RESULT_ROW_HEIGHT))
            button.setHidden_(False)

    def itemResultsBoundsDidChange_(self, _notification):
        self.clearHoverStatesForViews_(self.item_result_buttons)
        self.updateItemResultRows_(False)

    def refreshItemResults_(self, _sender):
        self.refreshItemResults()

    def selectScrollCalculatorLevel_(self, _sender):
        self.renderScrollCalculatorPrice()

    @objc.python_method
    def selectedScrollCalculatorLevel(self) -> int | None:
        index = int(self.scroll_calculator_level_popup.indexOfSelectedItem())
        if 0 <= index < len(self.scroll_calculator_level_values):
            return self.scroll_calculator_level_values[index]
        return None

    @objc.python_method
    def configureScrollCalculatorLevelPopupForSpell_(self, spell):
        previous_level = self.selectedScrollCalculatorLevel()
        self.scroll_calculator_level_values = valid_scroll_levels_for_spell(spell)
        self.scroll_calculator_level_popup.removeAllItems()
        for level in self.scroll_calculator_level_values:
            self.scroll_calculator_level_popup.addItemWithTitle_(scroll_level_label(level))
        self.scroll_calculator_level_popup.setEnabled_(True)
        if previous_level in self.scroll_calculator_level_values:
            self.scroll_calculator_level_popup.selectItemAtIndex_(self.scroll_calculator_level_values.index(previous_level))
        else:
            self.scroll_calculator_level_popup.selectItemAtIndex_(0)

    @objc.python_method
    def resetScrollCalculator_(self, status: str):
        self.scroll_calculator_spell = None
        self.scroll_calculator_level_values = []
        self.scroll_calculator_level_popup.removeAllItems()
        self.scroll_calculator_level_popup.addItemWithTitle_("Choose spell")
        self.scroll_calculator_level_popup.setEnabled_(False)
        self.scroll_calculator_match_label.setStringValue_("")
        self.scroll_calculator_rarity_value_label.setStringValue_("-")
        self.scroll_calculator_price_value_label.setStringValue_("-")
        self.scroll_calculator_status_label.setStringValue_(status)

    def refreshScrollCalculator_(self, _sender):
        self.refreshScrollCalculator()

    @objc.python_method
    def refreshScrollCalculator(self):
        query = str(self.scroll_calculator_spell_field.stringValue()).strip()
        if not query:
            self.resetScrollCalculator_("Enter a spell.")
            return

        matches = search_spells(query, self.spells, limit=1)
        if not matches:
            self.resetScrollCalculator_("No matching spell.")
            return

        spell = matches[0]
        previous_spell_id = self.scroll_calculator_spell.id if self.scroll_calculator_spell is not None else ""
        self.scroll_calculator_spell = spell
        if previous_spell_id != spell.id or not self.scroll_calculator_level_values:
            self.configureScrollCalculatorLevelPopupForSpell_(spell)
        self.renderScrollCalculatorPrice()

    @objc.python_method
    def renderScrollCalculatorPrice(self):
        spell = self.scroll_calculator_spell
        if spell is None:
            return
        selected_level = self.selectedScrollCalculatorLevel()
        if selected_level is None:
            self.configureScrollCalculatorLevelPopupForSpell_(spell)
            selected_level = self.selectedScrollCalculatorLevel()
        if selected_level is None:
            self.resetScrollCalculator_("No valid scroll level.")
            return

        result = price_scroll(spell, selected_level)
        self.scroll_calculator_match_label.setStringValue_(f"Matched: {spell.name}")
        self.scroll_calculator_rarity_value_label.setStringValue_(result.rarity)
        self.scroll_calculator_price_value_label.setStringValue_(f"{result.price_gp:,} gp")
        self.scroll_calculator_status_label.setStringValue_(f"{scroll_level_label(result.scroll_level)} scroll")

    def setItemDetailHeaderHidden_(self, hidden: bool):
        for view in self.item_detail_header_views:
            view.setHidden_(hidden)

    @objc.python_method
    def configureItemVariantPopupForItem_(self, item):
        self.item_variant_popup.removeAllItems()
        if not item.variant_only:
            self.item_variant_popup.addItemWithTitle_("Base")
        for variant in item.variants:
            self.item_variant_popup.addItemWithTitle_(variant.name)
        self.item_variant_popup.setHidden_(not bool(item.variants))
        if item.selected_variant_id:
            start_index = 0 if item.variant_only else 1
            for index, variant in enumerate(item.variants, start=start_index):
                if variant.id == item.selected_variant_id:
                    self.item_variant_popup.selectItemAtIndex_(index)
                    return
        self.item_variant_popup.selectItemAtIndex_(0)

    @objc.python_method
    def selectedItemDisplay(self):
        item = self.selected_item
        if item is None or self.item_variant_popup.isHidden():
            return item
        index = int(self.item_variant_popup.indexOfSelectedItem())
        if index <= 0 and not item.variant_only:
            return item
        variant_index = index if item.variant_only else index - 1
        if 0 <= variant_index < len(item.variants):
            return item.variants[variant_index]
        return item

    def selectItemVariant_(self, _sender):
        self.renderSelectedItemDetail()

    def resizeItemDetailBody(self):
        if self.item_detail_scroll is None:
            return
        self.item_detail_view.layoutManager().ensureLayoutForTextContainer_(self.item_detail_view.textContainer())
        height = max(
            self.item_detail_scroll.frame().size.height,
            self.item_detail_view.layoutManager().usedRectForTextContainer_(self.item_detail_view.textContainer()).size.height + 24,
        )
        self.item_detail_view.setFrame_(NSMakeRect(0, 0, self.item_detail_scroll.frame().size.width - 24, height))
        self.item_detail_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
        self.item_detail_scroll.reflectScrolledClipView_(self.item_detail_scroll.contentView())

    def refreshItemResults(self):
        query = str(self.item_search_field.stringValue()).strip()
        self.displayed_items = search_items(query, self.items, self.selectedItemCategoryFilter())
        self.clearHoverStatesForViews_(self.item_result_buttons)
        if self.item_results_scroll is not None:
            self.layoutMainWindow()
            self.item_results_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.item_results_scroll.reflectScrolledClipView_(self.item_results_scroll.contentView())
            self.updateItemResultRows_(True)
        if self.displayed_items:
            self.showItemInDetail_(self.displayed_items[0])
        else:
            self.setItemDetailHeaderHidden_(True)
            self.layoutMainWindow()
            self.item_detail_view.setString_("No matching items.")
            self.item_detail_view.setDiceRanges_([])
            self.resizeItemDetailBody()

    def selectItemResult_(self, sender):
        index = int(sender.tag())
        if index < 0 or index >= len(self.displayed_items):
            return
        self.showItemInDetail_(self.displayed_items[index])

    def showItemInDetail_(self, item):
        self.selected_item = item
        self.setItemDetailHeaderHidden_(False)
        self.configureItemVariantPopupForItem_(item)
        self.renderSelectedItemDetail()

    @objc.python_method
    def renderSelectedItemDetail(self):
        item = self.selectedItemDisplay()
        if item is None:
            return
        self.item_detail_title_label.setStringValue_(item.name)
        self.item_detail_meta_label.setStringValue_(item.category)
        self.item_detail_meta_label.setTextColor_(theme_color("gold"))

        fields = []
        if item.cost and item.cost.strip():
            fields.append(("Cost", item_display_cost(item.cost)))
            merchant_value = merchant_value_text(item.cost)
            if merchant_value:
                fields.append(("Merchant Buys", merchant_value))
        if item.ac:
            fields.append(("AC", item.ac))
        if item.rarity:
            fields.append(("Rarity", item.rarity))
        if item.classification and normalize(item.classification) not in {normalize(item.category), normalize(item.rarity)}:
            fields.append(("Classification", item.classification))
        display_properties = item_display_properties(item.properties, item.description)
        if display_properties:
            fields.append(("Properties", display_properties))
        if fields:
            self.item_detail_fields_label.setAttributedStringValue_(attributed_spell_stats(fields))
        else:
            self.item_detail_fields_label.setStringValue_("")

        body_parts = []
        practical_description = item_practical_description(item)
        _raw_practical_description, property_description = item_description_sections(item.description, item.properties)
        if practical_description:
            body_parts.append(practical_description)
        if item.damage:
            body_parts.append(f"Damage: {item.damage}")
        if property_description:
            body_parts.append(f"Properties:\n{property_description}")
        body = "\n\n".join(body_parts)
        attributed, rendered_body = attributed_item_body(body)
        self.item_detail_view.textStorage().setAttributedString_(attributed)
        self.item_detail_view.setDiceRanges_(dice_ranges_for_body(rendered_body))
        self.layoutMainWindow()
        self.resizeItemDetailBody()
