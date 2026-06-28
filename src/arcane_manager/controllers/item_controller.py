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

    def refreshItemResults_(self, _sender):
        self.refreshItemResults()

    def setItemDetailHeaderHidden_(self, hidden: bool):
        for view in self.item_detail_header_views:
            view.setHidden_(hidden)

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
        self.ensureItemResultRows_(len(self.displayed_items))
        for index, button in enumerate(self.item_result_buttons):
            if index >= len(self.displayed_items):
                button.setHidden_(True)
                continue
            button.configureItemResult_(self.displayed_items[index])
            button.setHidden_(False)
        if self.item_results_scroll is not None:
            self.layoutMainWindow()
            self.item_results_scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.item_results_scroll.reflectScrolledClipView_(self.item_results_scroll.contentView())
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
        self.item_detail_title_label.setStringValue_(item.name)
        self.item_detail_meta_label.setStringValue_(" | ".join(part for part in (item.category, item.cost) if part))
        self.item_detail_meta_label.setTextColor_(theme_color(item_cost_color_name(item.cost)))

        fields = []
        fields.append(f"Merchant buys: {merchant_value_text(item.cost)}")
        if item.ac:
            fields.append(f"AC: {item.ac}")
        if item.damage:
            fields.append(f"Damage: {item.damage}")
        if item.classification:
            fields.append(f"Classification: {item.classification}")
        if item.properties:
            fields.append(f"Properties: {item.properties}")
        self.item_detail_fields_label.setStringValue_("\n".join(fields))

        body = item.description.strip() or "No description."
        attributed = attributed_spell_body(body)
        self.item_detail_view.textStorage().setAttributedString_(attributed)
        self.item_detail_view.setDiceRanges_(dice_ranges_for_body(body))
        self.layoutMainWindow()
        self.resizeItemDetailBody()
