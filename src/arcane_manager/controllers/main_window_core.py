from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    def windowDidResize_(self, _notification):
        self.layoutMainWindow()

    def show_(self, _sender):
        NSApp.activateIgnoringOtherApps_(True)
        self.layoutMainWindow()
        self.window.makeKeyAndOrderFront_(None)

    def showInitiativeTab_(self, _sender):
        self.current_tab = "initiative"
        self.applyCurrentTab()

    def showSpellsTab_(self, _sender):
        self.current_tab = "spells"
        self.applyCurrentTab()
        self.refreshSpellResults()

    def showItemsTab_(self, _sender):
        self.current_tab = "items"
        self.applyCurrentTab()
        self.refreshItemResults()

    def showDiceTab_(self, _sender):
        self.current_tab = "dice"
        self.applyCurrentTab()
        self.refreshDiceFormula_(None)

    def showAdventureTab_(self, _sender):
        self.current_tab = "adventure"
        self.applyCurrentTab()
        self.refreshAdventureWorkspace()

    def applyCurrentTab(self):
        show_initiative = self.current_tab == "initiative"
        show_spells = self.current_tab == "spells"
        show_items = self.current_tab == "items"
        show_dice = self.current_tab == "dice"
        show_adventure = self.current_tab == "adventure"
        for view in self.initiative_views:
            view.setHidden_(not show_initiative)
        self.monster_search_button.setHidden_(True)
        for view in self.spell_views:
            view.setHidden_(not show_spells)
        for view in self.item_views:
            view.setHidden_(not show_items)
        for view in self.dice_views:
            view.setHidden_(not show_dice)
        for view in self.adventure_views:
            view.setHidden_(not show_adventure)
        for view in self.cart_overlay_views:
            view.setHidden_(not (show_items and self.cart_overlay_visible))
        self.cart_empty_label.setHidden_(not (show_items and self.cart_overlay_visible and self.cartItemCount() == 0))
        if show_adventure:
            self.adventure_web_view.setHidden_(self.adventure_is_editing)
            self.adventure_editor_scroll.setHidden_(not self.adventure_is_editing)
        self.initiative_tab_button.setActive_(show_initiative)
        self.spells_tab_button.setActive_(show_spells)
        self.items_tab_button.setActive_(show_items)
        self.dice_tab_button.setActive_(show_dice)
        self.adventure_tab_button.setActive_(show_adventure)
        self.layoutMainWindow()

    def controlTextDidChange_(self, notification):
        field = notification.object()
        if field == self.monster_search_field:
            self.searchMonsters_(None)
        elif field == self.spell_search_field:
            self.refreshSpellResults()
        elif field == self.item_search_field:
            self.refreshItemResults()
        elif field == self.scroll_calculator_spell_field:
            self.refreshScrollCalculator()

    def textDidChange_(self, notification):
        if notification.object() == self.adventure_editor_view:
            current = str(self.adventure_editor_view.string())
            self.adventure_dirty = current != self.adventure_last_saved_text
            self.refreshAdventureControls()

    def windowShouldClose_(self, _sender):
        return self.confirmAdventureCanDiscardOrSave()

    def windowWillClose_(self, _notification):
        if self in DICE_HISTORY_LISTENERS:
            DICE_HISTORY_LISTENERS.remove(self)
        NSApp.terminate_(None)
