from __future__ import annotations

from ._shared import *

class MainWindowController(NSObject):
    window: NSWindow
    content_view: NSView
    initiative_tab_button: NSButton
    spells_tab_button: NSButton
    items_tab_button: NSButton
    dice_tab_button: NSButton
    adventure_tab_button: NSButton
    sidebar_panel: NSView
    sidebar_scroll: NSScrollView
    sidebar_content: NSView
    combat_panel: NSView
    spell_panel: NSView
    item_panel: NSView
    dice_panel: NSView
    adventure_panel: NSView
    sidebar_logo_label: NSTextField
    sidebar_footer_label: NSTextField
    creatures: list[Creature]
    spells: list[Spell]
    items: list[Item]
    spell_lookup: dict[str, Spell]
    parties: list[dict[str, Any]]
    combatants: list[dict[str, Any]]
    monster_results: list[Creature]
    current_turn_index: int
    editing_party_index: int
    editing_characters: list[dict[str, str]]
    party_editor_panel: NSPanel
    hp_adjust_panel: NSPanel
    hp_adjust_index: int
    hp_adjust_amount_field: NSTextField
    hp_adjust_temp_field: NSTextField
    editor_party_name_field: NSTextField
    editor_character_name_field: NSTextField
    editor_character_class_popup: NSPopUpButton
    editor_character_ac_field: NSTextField
    editor_character_popup: NSPopUpButton
    editor_character_list: NSTextView
    monster_sheet_drawer: NSView
    monster_sheet_title: NSTextField
    monster_sheet_close_button: NSButton
    monster_sheet_scroll: NSScrollView
    monster_sheet_body: DiceTextView
    monster_sheet_hp_label: NSTextField
    monster_sheet_hp_field: NSTextField
    monster_sheet_save_button: NSButton
    monster_sheet_roll_label: NSTextField
    monster_sheet_ability_buttons: list[StatBlockAbilityButton]
    monster_sheet_combatant_index: int
    monster_sheet_creature: Creature | None
    notes_title: NSTextField
    notes_hint: NSTextField
    notes_scroll: NSScrollView
    tracker_title: NSTextField
    party_label: NSTextField
    party_popup: NSPopUpButton
    new_party_button: NSButton
    edit_party_button: NSButton
    delete_party_button: NSButton
    start_fight_button: NSButton
    party_member_labels: list[NSTextField]
    party_member_checkboxes: list[NSButton]
    party_member_icon_views: list[NSImageView]
    party_member_name_labels: list[NSTextField]
    party_member_class_labels: list[NSTextField]
    party_member_ac_labels: list[NSTextField]
    party_member_enabled: list[list[bool]]
    notes_view: NSTextView
    monster_label: NSTextField
    monster_search_field: NSTextField
    monster_cr_filter_popup: NSPopUpButton
    monster_search_button: NSButton
    monster_results_scroll: NSScrollView
    monster_results_content: FlippedView
    monster_results_indicator: PersistentScrollIndicator
    monster_result_buttons: list[NSButton]
    monster_add_buttons: list[NSButton]
    spell_search_field: NSTextField
    spell_level_filter_popup: NSPopUpButton
    spell_school_filter_popup: NSPopUpButton
    spell_results_scroll: NSScrollView
    spell_results_content: FlippedView
    spell_detail_title_label: NSTextField
    spell_detail_italian_label: NSTextField
    spell_detail_meta_label: NSTextField
    spell_components_label: NSTextField
    spell_component_material_label: NSTextField
    spell_v_label: NSTextField
    spell_s_label: NSTextField
    spell_m_label: NSTextField
    spell_v_box: CheckboxSquareView
    spell_s_box: CheckboxSquareView
    spell_m_box: CheckboxSquareView
    spell_stats_label: NSTextField
    spell_detail_header_views: list[Any]
    spell_result_buttons: list[NSButton]
    spell_detail_scroll: NSScrollView
    spell_detail_view: DiceTextView
    current_spell_school: str
    item_search_field: NSTextField
    item_category_filter_popup: NSPopUpButton
    item_results_scroll: NSScrollView
    item_results_content: FlippedView
    item_detail_title_label: NSTextField
    item_detail_meta_label: NSTextField
    item_detail_fields_label: NSTextField
    item_detail_header_views: list[Any]
    item_result_buttons: list[NSButton]
    item_detail_scroll: NSScrollView
    item_detail_view: DiceTextView
    displayed_items: list[Item]
    selected_item: Item | None
    dice_title_label: NSTextField
    dice_hint_label: NSTextField
    dice_formula_label: NSTextField
    dice_result_label: NSTextField
    dice_history_title_label: NSTextField
    dice_history_scroll: NSScrollView
    dice_history_view: NSTextView
    dice_roll_button: NSButton
    dice_clear_button: NSButton
    dice_preset_buttons: list[NSButton]
    dice_pool: dict[int, int]
    adventure_vault_path: Path | None
    adventure_selected_note: Path | None
    adventure_root_node: AdventureNode | None
    adventure_flat_nodes: list[AdventureNode]
    adventure_expanded_paths: set[str]
    adventure_note_index: dict[str, list[Path]]
    adventure_asset_index: dict[str, list[Path]]
    adventure_file_colors: dict[str, str]
    adventure_tree_buttons: list[AdventureTreeButton]
    adventure_views: list[Any]
    adventure_tree_scroll: NSScrollView
    adventure_tree_content: FlippedView
    adventure_divider_view: AdventureDividerView
    adventure_title_label: NSTextField
    adventure_status_label: NSTextField
    adventure_toggle_button: NSButton
    adventure_save_button: NSButton
    adventure_dirty_label: NSTextField
    adventure_web_view: WKWebView
    adventure_editor_scroll: NSScrollView
    adventure_editor_view: NSTextView
    adventure_is_editing: bool
    adventure_dirty: bool
    adventure_last_saved_text: str
    adventure_tree_width: int
    displayed_spells: list[Spell]
    initiative_views: list[Any]
    spell_views: list[Any]
    item_views: list[Any]
    dice_views: list[Any]
    current_tab: str
    previous_turn_button: NSButton
    next_turn_button: NSButton
    clear_tracker_button: NSButton
    tracker_scroll: NSScrollView
    tracker_view: CombatTrackerView
    party_status_label: NSTextField
    turn_label: NSTextField

    def initWithBestiary_spells_spellLookup_items_(self, creatures, spells, spell_lookup, items):
        self = objc.super(MainWindowController, self).init()
        if self is None:
            return None

        self.creatures = list(creatures)
        self.spells = list(spells)
        self.items = list(items)
        self.spell_lookup = dict(spell_lookup)
        self.parties = self.loadParties()
        self.party_member_enabled = []
        self.combatants = []
        self.monster_results = []
        self.monster_result_buttons = []
        self.monster_add_buttons = []
        self.displayed_spells = []
        self.spell_result_buttons = []
        self.current_spell_school = ""
        self.displayed_items = []
        self.selected_item = None
        self.item_result_buttons = []
        self.dice_preset_buttons = []
        self.dice_pool = {4: 0, 6: 0, 8: 0, 10: 0, 12: 0, 20: 0}
        self.adventure_vault_path = None
        self.adventure_selected_note = None
        self.adventure_root_node = None
        self.adventure_flat_nodes = []
        self.adventure_expanded_paths = set()
        self.adventure_note_index = {}
        self.adventure_asset_index = {}
        self.adventure_file_colors = {}
        self.adventure_tree_buttons = []
        self.adventure_views = []
        self.adventure_is_editing = False
        self.adventure_dirty = False
        self.adventure_last_saved_text = ""
        self.adventure_tree_width = int(NSUserDefaults.standardUserDefaults().integerForKey_(ADVENTURE_TREE_WIDTH_PREF)) or 260
        if self not in DICE_HISTORY_LISTENERS:
            DICE_HISTORY_LISTENERS.append(self)
        self.party_member_labels = []
        self.party_member_checkboxes = []
        self.party_member_icon_views = []
        self.party_member_name_labels = []
        self.party_member_class_labels = []
        self.party_member_ac_labels = []
        self.initiative_views = []
        self.spell_views = []
        self.item_views = []
        self.dice_views = []
        self.current_tab = "initiative"
        self.current_turn_index = 0
        self.round_number = 1
        self.editing_party_index = -1
        self.editing_characters = []
        self.hp_adjust_panel = None
        self.hp_adjust_index = -1
        self.hp_adjust_amount_field = None
        self.hp_adjust_temp_field = None
        self.monster_sheet_drawer = None
        self.monster_sheet_title = None
        self.monster_sheet_close_button = None
        self.monster_sheet_scroll = None
        self.monster_sheet_body = None
        self.monster_sheet_hp_label = None
        self.monster_sheet_hp_field = None
        self.monster_sheet_save_button = None
        self.monster_sheet_roll_label = None
        self.monster_sheet_ability_buttons = []
        self.monster_sheet_combatant_index = -1
        self.monster_sheet_creature = None

        screen = NSScreen.mainScreen().visibleFrame()
        width = int(screen.size.width)
        height = int(screen.size.height)

        style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskResizable
        )
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(screen.origin.x, screen.origin.y, width, height),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_("Arcane Manager")
        self.window.setMinSize_(NSMakeSize(1060, 660))
        self.window.setDelegate_(self)
        self.window.setBackgroundColor_(theme_color("app_bg"))

        self.content_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        style_layer(self.content_view, theme_color("app_bg"), None, 0)
        self.initiative_tab_button = self._make_tab_button("Initiative Tracker", (20, height - 38, 150, 30), "showInitiativeTab:")
        self.spells_tab_button = self._make_tab_button("Spells", (178, height - 38, 86, 30), "showSpellsTab:")
        self.items_tab_button = self._make_tab_button("Items", (272, height - 38, 82, 30), "showItemsTab:")
        self.dice_tab_button = self._make_tab_button("Dice Roller", (362, height - 38, 112, 30), "showDiceTab:")
        self.adventure_tab_button = self._make_tab_button("Adventure", (482, height - 38, 104, 30), "showAdventureTab:")
        self.sidebar_panel = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 340, height))
        style_layer(self.sidebar_panel, theme_color("panel_alt"), None, 0)
        self.sidebar_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 340, height))
        self.sidebar_scroll.setHasVerticalScroller_(True)
        self.sidebar_scroll.setAutohidesScrollers_(False)
        self.sidebar_scroll.setDrawsBackground_(False)
        self.sidebar_scroll.setBorderType_(0)
        self.sidebar_content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 340, height))
        self.sidebar_scroll.setDocumentView_(self.sidebar_content)
        self.combat_panel = NSView.alloc().initWithFrame_(NSMakeRect(360, 24, 896, height - 48))
        style_layer(self.combat_panel, theme_color("panel"), theme_color("border_soft"), 14, 1)
        self.spell_panel = NSView.alloc().initWithFrame_(NSMakeRect(20, 20, width - 40, height - 74))
        style_layer(self.spell_panel, theme_color("panel"), theme_color("border_soft"), 14, 1)
        self.item_panel = NSView.alloc().initWithFrame_(NSMakeRect(20, 20, width - 40, height - 74))
        style_layer(self.item_panel, theme_color("panel"), theme_color("border_soft"), 14, 1)
        self.dice_panel = NSView.alloc().initWithFrame_(NSMakeRect(20, 20, width - 40, height - 74))
        style_layer(self.dice_panel, theme_color("panel"), theme_color("border_soft"), 14, 1)
        self.adventure_panel = NSView.alloc().initWithFrame_(NSMakeRect(20, 20, width - 40, height - 74))
        style_layer(self.adventure_panel, theme_color("panel"), theme_color("border_soft"), 14, 1)

        self.monster_sheet_drawer = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 360, height - 48))
        style_layer(self.monster_sheet_drawer, theme_color("panel_alt"), theme_color("border_soft"), 12, 1)
        self.monster_sheet_drawer.setHidden_(True)
        self.monster_sheet_title = make_label("", (0, 0, 260, 36), 24, True)
        self.monster_sheet_title.setUsesSingleLineMode_(True)
        self.monster_sheet_title.setLineBreakMode_(4)
        self.monster_sheet_close_button = self._make_button("Close", (0, 0, 72, 28), "closeMonsterSheet:")
        self.monster_sheet_hp_label = make_label("Current HP", (0, 0, 90, 24), 13, True)
        self.monster_sheet_hp_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 72, 26))
        self.monster_sheet_save_button = self._make_button("Save HP", (0, 0, 84, 26), "saveMonsterHp:")
        self.monster_sheet_roll_label = make_label("", (0, 0, 300, 22), 12, True)
        self.monster_sheet_roll_label.setTextColor_(theme_color("dice"))
        self.monster_sheet_hp_label.setHidden_(True)
        self.monster_sheet_hp_field.setHidden_(True)
        self.monster_sheet_save_button.setHidden_(True)
        self.monster_sheet_roll_label.setHidden_(True)
        self.monster_sheet_ability_buttons = []
        for _index in range(6):
            button = StatBlockAbilityButton.alloc().initWithFrame_(NSMakeRect(0, 0, 44, 72))
            self.monster_sheet_ability_buttons.append(button)
        self.monster_sheet_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 400))
        self.monster_sheet_scroll.setHasVerticalScroller_(True)
        self.monster_sheet_scroll.setAutohidesScrollers_(False)
        self.monster_sheet_scroll.setDrawsBackground_(False)
        self.monster_sheet_scroll.setBorderType_(0)
        self.monster_sheet_body = DiceTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 400))
        self.monster_sheet_body.setFont_(NSFont.systemFontOfSize_(13))
        self.monster_sheet_body.setTextColor_(theme_color("text"))
        self.monster_sheet_body.setRollTarget_(self)
        self.monster_sheet_body.setSpellTarget_(self)
        self.monster_sheet_scroll.setDocumentView_(self.monster_sheet_body)
        for view in (
            self.monster_sheet_title,
            self.monster_sheet_close_button,
            self.monster_sheet_scroll,
        ):
            self.monster_sheet_drawer.addSubview_(view)
        for button in self.monster_sheet_ability_buttons:
            self.monster_sheet_drawer.addSubview_(button)

        self.notes_title = make_label("Initiative Tracker", (0, 0, 220, 28), 18, True)
        self.notes_hint = make_label("Combat Round Tracker", (0, 0, 220, 20), 12)
        self.notes_hint.setTextColor_(theme_color("muted"))
        self.sidebar_logo_label = make_label("✦", (0, 0, 36, 36), 20, True)
        self.sidebar_logo_label.setAlignment_(1)
        style_layer(self.sidebar_logo_label, theme_color("selection"), theme_color("link"), 10, 1)
        self.notes_title.setHidden_(True)
        self.notes_hint.setHidden_(True)
        self.sidebar_logo_label.setHidden_(True)
        self.sidebar_footer_label = make_label("", (0, 0, 300, 24), 13)
        self.sidebar_footer_label.setTextColor_(theme_color("muted"))
        self.sidebar_footer_label.setHidden_(True)
        self.notes_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.notes_scroll.setHasVerticalScroller_(True)
        self.notes_scroll.setAutohidesScrollers_(False)
        self.notes_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.notes_view.setFont_(NSFont.systemFontOfSize_(14))
        self.notes_view.setTextColor_(theme_color("text"))
        self.notes_view.setBackgroundColor_(theme_color("surface"))
        self.notes_scroll.setDocumentView_(self.notes_view)
        self.notes_scroll.setHidden_(True)

        self.tracker_title = make_label("Round 1", (0, 0, 300, 28), 18, True)
        self.party_label = make_label("Party", (0, 0, 60, 24), 16, True)
        self.party_popup = StyledPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 180, 28))
        self.party_popup.setTarget_(self)
        self.party_popup.setAction_("selectParty:")
        self.new_party_button = self._make_button("+", (0, 0, 32, 28), "newParty:")
        self.edit_party_button = self._make_button("Edit", (0, 0, 64, 28), "editParty:")
        self.delete_party_button = self._make_button("Delete", (0, 0, 70, 28), "deleteParty:")
        self.start_fight_button = self._make_button("Go", (0, 0, 34, 28), "startFight:")
        self.start_fight_button.setToolTip_("Add party to initiative")

        self.party_status_label = make_multiline(make_label("", (0, 0, 300, 40), 11))
        self.party_status_label.setTextColor_(theme_color("muted"))

        self.monster_label = make_label("Creatures", (0, 0, 100, 24), 16, True)
        self.monster_search_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 26))
        self.monster_search_field.setPlaceholderString_("Search SRD monster")
        self.monster_search_field.setTarget_(self)
        self.monster_search_field.setAction_("searchMonsters:")
        self.monster_search_field.setDelegate_(self)
        style_text_input(self.monster_search_field)
        self.monster_cr_filter_popup = StyledPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 28))
        self.monster_cr_filter_popup.addItemWithTitle_("Any CR")
        for cr_value in creature_cr_values(self.creatures):
            self.monster_cr_filter_popup.addItemWithTitle_(f"CR {cr_value}")
        self.monster_cr_filter_popup.setTarget_(self)
        self.monster_cr_filter_popup.setAction_("searchMonsters:")
        self.monster_search_button = self._make_button("Search", (0, 0, 80, 26), "searchMonsters:")
        self.monster_search_button.setHidden_(True)
        self.monster_results_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.monster_results_scroll.setHasVerticalScroller_(False)
        self.monster_results_scroll.setAutohidesScrollers_(False)
        self.monster_results_scroll.setDrawsBackground_(False)
        self.monster_results_scroll.setBorderType_(0)
        self.monster_results_content = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.monster_results_scroll.setDocumentView_(self.monster_results_content)
        self.monster_results_scroll.contentView().setPostsBoundsChangedNotifications_(True)
        self.monster_results_indicator = PersistentScrollIndicator.alloc().initWithFrame_(NSMakeRect(0, 0, 8, 100))
        self.monster_results_indicator.setScrollView_(self.monster_results_scroll)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "monsterResultsBoundsDidChange:",
            NSViewBoundsDidChangeNotification,
            self.monster_results_scroll.contentView(),
        )

        self.spell_search_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 28))
        self.spell_search_field.setPlaceholderString_("Search spells in English or Italian")
        self.spell_search_field.setDelegate_(self)
        style_text_input(self.spell_search_field)
        self.spell_level_filter_popup = StyledPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 28))
        self.spell_level_filter_popup.addItemWithTitle_("Any Level")
        for level in spell_level_values(self.spells):
            self.spell_level_filter_popup.addItemWithTitle_(level)
        self.spell_level_filter_popup.setTarget_(self)
        self.spell_level_filter_popup.setAction_("refreshSpellResults:")
        self.spell_school_filter_popup = StyledPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 150, 28))
        self.spell_school_filter_popup.addItemWithTitle_("Any School")
        for school in spell_school_values(self.spells):
            self.spell_school_filter_popup.addItemWithTitle_(school)
        self.spell_school_filter_popup.setTarget_(self)
        self.spell_school_filter_popup.setAction_("refreshSpellResults:")
        self.spell_results_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.spell_results_scroll.setHasVerticalScroller_(True)
        self.spell_results_scroll.setAutohidesScrollers_(False)
        self.spell_results_scroll.setDrawsBackground_(False)
        self.spell_results_scroll.setBorderType_(0)
        self.spell_results_content = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.spell_results_scroll.setDocumentView_(self.spell_results_content)
        self.spell_results_scroll.contentView().setPostsBoundsChangedNotifications_(True)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "spellResultsBoundsDidChange:",
            NSViewBoundsDidChangeNotification,
            self.spell_results_scroll.contentView(),
        )
        self.spell_detail_title_label = make_label("", (0, 0, 320, 34), 26, True)
        self.spell_detail_title_label.setLineBreakMode_(4)
        self.spell_detail_italian_label = make_label("", (0, 0, 320, 22), 15)
        italic_font = NSFontManager.sharedFontManager().convertFont_toHaveTrait_(
            NSFont.systemFontOfSize_(15),
            NSItalicFontMask,
        )
        self.spell_detail_italian_label.setFont_(italic_font)
        self.spell_detail_italian_label.setTextColor_(theme_color("muted"))
        self.spell_detail_italian_label.setLineBreakMode_(4)
        self.spell_detail_meta_label = make_label("", (0, 0, 320, 24), 15, True)
        self.spell_detail_meta_label.setTextColor_(theme_color("gold"))
        self.spell_detail_meta_label.setLineBreakMode_(4)
        self.spell_components_label = make_label("Components", (0, 0, 100, 22), 13, True)
        self.spell_components_label.setTextColor_(theme_color("text"))
        self.spell_v_label = make_label("V", (0, 0, 14, 20), 13, True)
        self.spell_s_label = make_label("S", (0, 0, 14, 20), 13, True)
        self.spell_m_label = make_label("M", (0, 0, 16, 20), 13, True)
        for label in (self.spell_v_label, self.spell_s_label, self.spell_m_label):
            label.setTextColor_(theme_color("gold"))
        self.spell_v_box = CheckboxSquareView.alloc().initWithFrame_(NSMakeRect(0, 0, 16, 16))
        self.spell_s_box = CheckboxSquareView.alloc().initWithFrame_(NSMakeRect(0, 0, 16, 16))
        self.spell_m_box = CheckboxSquareView.alloc().initWithFrame_(NSMakeRect(0, 0, 16, 16))
        self.spell_component_material_label = make_multiline(make_label("", (0, 0, 320, 36), 13))
        self.spell_component_material_label.setTextColor_(theme_color("text"))
        self.spell_stats_label = make_multiline(make_label("", (0, 0, 320, 42), 13))
        self.spell_stats_label.setTextColor_(theme_color("text"))
        self.spell_detail_header_views = [
            self.spell_detail_title_label,
            self.spell_detail_italian_label,
            self.spell_detail_meta_label,
            self.spell_components_label,
            self.spell_v_label,
            self.spell_v_box,
            self.spell_s_label,
            self.spell_s_box,
            self.spell_m_label,
            self.spell_m_box,
            self.spell_component_material_label,
            self.spell_stats_label,
        ]
        self.spell_detail_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.spell_detail_scroll.setHasVerticalScroller_(True)
        self.spell_detail_scroll.setAutohidesScrollers_(False)
        self.spell_detail_scroll.setDrawsBackground_(False)
        self.spell_detail_scroll.setBorderType_(0)
        self.spell_detail_view = DiceTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.spell_detail_view.setFont_(NSFont.systemFontOfSize_(13))
        self.spell_detail_view.setTextColor_(theme_color("text"))
        self.spell_detail_view.setRollTarget_(self)
        self.spell_detail_scroll.setDocumentView_(self.spell_detail_view)

        self.item_search_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 28))
        self.item_search_field.setPlaceholderString_("Search items")
        self.item_search_field.setDelegate_(self)
        style_text_input(self.item_search_field)
        self.item_category_filter_popup = StyledPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 150, 28))
        self.item_category_filter_popup.addItemWithTitle_("Any Category")
        for category in item_category_values(self.items):
            self.item_category_filter_popup.addItemWithTitle_(category)
        self.item_category_filter_popup.setTarget_(self)
        self.item_category_filter_popup.setAction_("refreshItemResults:")
        self.item_results_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.item_results_scroll.setHasVerticalScroller_(True)
        self.item_results_scroll.setAutohidesScrollers_(False)
        self.item_results_scroll.setDrawsBackground_(False)
        self.item_results_scroll.setBorderType_(0)
        self.item_results_content = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.item_results_scroll.setDocumentView_(self.item_results_content)
        self.item_results_scroll.contentView().setPostsBoundsChangedNotifications_(True)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "itemResultsBoundsDidChange:",
            NSViewBoundsDidChangeNotification,
            self.item_results_scroll.contentView(),
        )
        self.item_detail_title_label = make_label("", (0, 0, 320, 34), 26, True)
        self.item_detail_title_label.setLineBreakMode_(4)
        self.item_detail_meta_label = make_label("", (0, 0, 320, 24), 15, True)
        self.item_detail_meta_label.setTextColor_(theme_color("gold"))
        self.item_detail_meta_label.setLineBreakMode_(4)
        self.item_detail_fields_label = make_multiline(make_label("", (0, 0, 320, 80), 13))
        self.item_detail_fields_label.setTextColor_(theme_color("text"))
        self.item_detail_header_views = [
            self.item_detail_title_label,
            self.item_detail_meta_label,
            self.item_detail_fields_label,
        ]
        self.item_detail_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.item_detail_scroll.setHasVerticalScroller_(True)
        self.item_detail_scroll.setAutohidesScrollers_(False)
        self.item_detail_scroll.setDrawsBackground_(False)
        self.item_detail_scroll.setBorderType_(0)
        self.item_detail_view = DiceTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.item_detail_view.setFont_(NSFont.systemFontOfSize_(13))
        self.item_detail_view.setTextColor_(theme_color("text"))
        self.item_detail_view.setRollTarget_(self)
        self.item_detail_scroll.setDocumentView_(self.item_detail_view)

        self.dice_title_label = make_label("Dice Roller", (0, 0, 240, 32), 24, True)
        self.dice_hint_label = make_label("", (0, 0, 720, 24), 13)
        self.dice_hint_label.setTextColor_(theme_color("muted"))
        self.dice_hint_label.setHidden_(True)
        self.dice_control_labels = []
        self.dice_clear_button = self._make_button("Clear", (0, 0, 100, 34), "clearDicePool:")
        self.dice_roll_button = self._make_button("Roll Dice", (0, 0, 130, 34), "rollCustomDice:")
        self.dice_formula_label = make_label("Click a die", (0, 0, 520, 42), 30, True)
        self.dice_formula_label.setAlignment_(1)
        self.dice_formula_label.setTextColor_(theme_color("dice"))
        self.dice_result_label = make_label("", (0, 0, 520, 24), 13, True)
        self.dice_result_label.setAlignment_(1)
        self.dice_result_label.setTextColor_(theme_color("muted"))
        self.dice_history_title_label = make_label("Recent Rolls", (0, 0, 220, 24), 16, True)
        self.dice_history_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 320, 260))
        self.dice_history_scroll.setHasVerticalScroller_(True)
        self.dice_history_scroll.setAutohidesScrollers_(False)
        self.dice_history_scroll.setDrawsBackground_(False)
        self.dice_history_scroll.setBorderType_(0)
        style_layer(self.dice_history_scroll, theme_color("surface_soft"), theme_color("border_soft"), 8, 1)
        self.dice_history_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 260))
        self.dice_history_view.setEditable_(False)
        self.dice_history_view.setSelectable_(True)
        self.dice_history_view.setFont_(NSFont.systemFontOfSize_(12))
        self.dice_history_view.setTextColor_(theme_color("text"))
        self.dice_history_view.setBackgroundColor_(theme_color("surface_soft"))
        self.dice_history_view.setTextContainerInset_(NSMakeSize(10, 10))
        self.dice_history_scroll.setDocumentView_(self.dice_history_view)
        self.refreshDiceHistory()
        self.dice_presets = (4, 6, 8, 10, 12, 20)
        for sides in self.dice_presets:
            button = self._make_button(f"d{sides}", (0, 0, 76, 58), "addDieToPool:")
            button.setTag_(sides)
            self.dice_preset_buttons.append(button)

        self.adventure_title_label = make_label("Adventure", (0, 0, 360, 32), 24, True)
        self.adventure_status_label = make_label("Choose a folder of Markdown notes.", (0, 0, 520, 24), 13)
        self.adventure_status_label.setTextColor_(theme_color("muted"))
        self.adventure_toggle_button = self._make_button("Edit", (0, 0, 86, 32), "toggleAdventureMode:")
        self.adventure_save_button = self._make_button("Save", (0, 0, 82, 32), "saveAdventureNote:")
        self.adventure_dirty_label = make_label("", (0, 0, 120, 22), 12, True)
        self.adventure_dirty_label.setTextColor_(theme_color("gold"))

        self.adventure_tree_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 420))
        self.adventure_tree_scroll.setHasVerticalScroller_(True)
        self.adventure_tree_scroll.setAutohidesScrollers_(False)
        self.adventure_tree_scroll.setDrawsBackground_(False)
        self.adventure_tree_scroll.setBorderType_(0)
        style_layer(self.adventure_tree_scroll, theme_color("surface_soft"), theme_color("border_soft"), 8, 1)
        self.adventure_tree_content = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 420))
        self.adventure_tree_scroll.setDocumentView_(self.adventure_tree_content)
        self.adventure_divider_view = AdventureDividerView.alloc().initWithFrame_(NSMakeRect(0, 0, 8, 420))
        self.adventure_divider_view.setTarget_(self)

        adventure_user_content = WKUserContentController.alloc().init()
        adventure_user_content.addScriptMessageHandler_name_(self, "adventure")
        adventure_config = WKWebViewConfiguration.alloc().init()
        adventure_config.setUserContentController_(adventure_user_content)
        self.adventure_web_view = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, 620, 420), adventure_config)
        self.adventure_web_view.setValue_forKey_(False, "drawsBackground")
        style_layer(self.adventure_web_view, theme_color("adventure_reader_bg"), theme_color("border_soft"), 8, 1)

        self.adventure_editor_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 620, 420))
        self.adventure_editor_scroll.setHasVerticalScroller_(True)
        self.adventure_editor_scroll.setHasHorizontalScroller_(False)
        self.adventure_editor_scroll.setAutohidesScrollers_(False)
        self.adventure_editor_scroll.setDrawsBackground_(False)
        self.adventure_editor_scroll.setBorderType_(0)
        style_layer(self.adventure_editor_scroll, theme_color("surface_soft"), theme_color("border_soft"), 8, 1)
        self.adventure_editor_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 620, 420))
        self.adventure_editor_view.setEditable_(True)
        self.adventure_editor_view.setSelectable_(True)
        self.adventure_editor_view.setFont_(NSFont.monospacedSystemFontOfSize_weight_(13, 0))
        self.adventure_editor_view.setTextColor_(theme_color("text"))
        self.adventure_editor_view.setBackgroundColor_(theme_color("surface_soft"))
        self.adventure_editor_view.setTextContainerInset_(NSMakeSize(14, 14))
        self.adventure_editor_view.textContainer().setLineFragmentPadding_(0)
        self.adventure_editor_view.setDelegate_(self)
        self.adventure_editor_scroll.setDocumentView_(self.adventure_editor_view)
        self.adventure_editor_scroll.setHidden_(True)

        self.previous_turn_button = self._make_button("Previous", (0, 0, 110, 34), "previousTurn:")
        self.next_turn_button = self._make_button("Next", (0, 0, 100, 34), "nextTurn:")
        self.clear_tracker_button = self._make_button("Finish Combat", (0, 0, 130, 34), "clearTracker:")
        self.turn_label = make_label("", (0, 0, 300, 24), 13, True)
        self.turn_label.setTextColor_(theme_color("gold"))
        self.turn_label.setAlignment_(2)
        self.turn_label.setHidden_(True)

        self.tracker_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.tracker_scroll.setHasVerticalScroller_(True)
        self.tracker_scroll.setHasHorizontalScroller_(True)
        self.tracker_scroll.setAutohidesScrollers_(False)
        self.tracker_view = CombatTrackerView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.tracker_view.setTarget_(self)
        self.tracker_scroll.setDocumentView_(self.tracker_view)
        self.tracker_scroll.setDrawsBackground_(False)
        self.tracker_scroll.setBorderType_(0)

        self.content_view.addSubview_(self.sidebar_panel)
        self.content_view.addSubview_(self.sidebar_scroll)
        self.content_view.addSubview_(self.combat_panel)
        self.content_view.addSubview_(self.monster_sheet_drawer)
        self.content_view.addSubview_(self.spell_panel)
        self.content_view.addSubview_(self.item_panel)
        self.content_view.addSubview_(self.dice_panel)
        self.content_view.addSubview_(self.adventure_panel)
        self.content_view.addSubview_(self.initiative_tab_button)
        self.content_view.addSubview_(self.spells_tab_button)
        self.content_view.addSubview_(self.items_tab_button)
        self.content_view.addSubview_(self.dice_tab_button)
        self.content_view.addSubview_(self.adventure_tab_button)
        for view in (
            self.notes_title,
            self.notes_hint,
            self.sidebar_logo_label,
            self.sidebar_footer_label,
            self.notes_scroll,
            self.party_label,
            self.party_popup,
            self.new_party_button,
            self.edit_party_button,
            self.delete_party_button,
            self.start_fight_button,
            self.party_status_label,
            self.monster_label,
            self.monster_search_field,
            self.monster_cr_filter_popup,
            self.monster_search_button,
            self.monster_results_scroll,
            self.monster_results_indicator,
        ):
            self.sidebar_content.addSubview_(view)
        for label in self.party_member_labels:
            self.sidebar_content.addSubview_(label)
        for checkbox in self.party_member_checkboxes:
            self.sidebar_content.addSubview_(checkbox)
        for icon_view in self.party_member_icon_views:
            self.sidebar_content.addSubview_(icon_view)
        for labels in (
            self.party_member_name_labels,
            self.party_member_class_labels,
            self.party_member_ac_labels,
        ):
            for label in labels:
                self.sidebar_content.addSubview_(label)
        for view in (
            self.tracker_title,
            self.previous_turn_button,
            self.next_turn_button,
            self.clear_tracker_button,
            self.turn_label,
            self.tracker_scroll,
        ):
            self.content_view.addSubview_(view)
        for view in (
            self.spell_search_field,
            self.spell_level_filter_popup,
            self.spell_school_filter_popup,
            self.spell_results_scroll,
            *self.spell_detail_header_views,
            self.spell_detail_scroll,
        ):
            self.content_view.addSubview_(view)
        for view in (
            self.item_search_field,
            self.item_category_filter_popup,
            self.item_results_scroll,
            *self.item_detail_header_views,
            self.item_detail_scroll,
        ):
            self.content_view.addSubview_(view)
        for view in (
            self.dice_title_label,
            self.dice_hint_label,
            self.dice_formula_label,
            self.dice_result_label,
            self.dice_history_title_label,
            self.dice_history_scroll,
            self.dice_clear_button,
            self.dice_roll_button,
        ):
            self.content_view.addSubview_(view)
        for button in self.dice_preset_buttons:
            self.content_view.addSubview_(button)
        for view in (
            self.adventure_title_label,
            self.adventure_status_label,
            self.adventure_toggle_button,
            self.adventure_save_button,
            self.adventure_dirty_label,
            self.adventure_tree_scroll,
            self.adventure_divider_view,
            self.adventure_web_view,
            self.adventure_editor_scroll,
        ):
            self.content_view.addSubview_(view)

        self.initiative_views = [
            self.sidebar_panel,
            self.sidebar_scroll,
            self.combat_panel,
            self.tracker_title,
            self.previous_turn_button,
            self.next_turn_button,
            self.clear_tracker_button,
            self.turn_label,
            self.tracker_scroll,
            self.monster_sheet_drawer,
        ]
        self.spell_views = [
            self.spell_panel,
            self.spell_search_field,
            self.spell_level_filter_popup,
            self.spell_school_filter_popup,
            self.spell_results_scroll,
            *self.spell_detail_header_views,
            self.spell_detail_scroll,
        ]
        self.item_views = [
            self.item_panel,
            self.item_search_field,
            self.item_category_filter_popup,
            self.item_results_scroll,
            *self.item_detail_header_views,
            self.item_detail_scroll,
        ]
        self.dice_views = [
            self.dice_panel,
            self.dice_title_label,
            self.dice_formula_label,
            self.dice_result_label,
            self.dice_history_title_label,
            self.dice_history_scroll,
            self.dice_clear_button,
            self.dice_roll_button,
            *self.dice_preset_buttons,
        ]
        self.adventure_views = [
            self.adventure_panel,
            self.adventure_title_label,
            self.adventure_status_label,
            self.adventure_toggle_button,
            self.adventure_save_button,
            self.adventure_dirty_label,
            self.adventure_tree_scroll,
            self.adventure_divider_view,
            self.adventure_web_view,
            self.adventure_editor_scroll,
        ]

        self.window.setContentView_(self.content_view)
        self.loadAdventureVaultFromDefaults()
        self.layoutMainWindow()
        self.refreshPartyPopup()
        self.searchMonsters_(None)
        self.refreshSpellResults()
        self.refreshItemResults()
        self.refreshDiceFormula_(None)
        self.refreshTracker()
        self.applyCurrentTab()
        return self

    @objc.python_method
    def _make_button(self, title: str, frame: tuple[int, int, int, int], action: str):
        button = StyledButton.alloc().initWithFrame_(NSMakeRect(*frame))
        button.setTitle_(title)
        button.setTarget_(self)
        button.setAction_(action)
        button.setBordered_(False)
        style_button_layer(button)
        return button

    @objc.python_method
    def _make_tab_button(self, title: str, frame: tuple[int, int, int, int], action: str):
        button = TabButton.alloc().initWithFrame_(NSMakeRect(*frame))
        button.setTitle_(title)
        button.setTarget_(self)
        button.setAction_(action)
        return button

    @objc.python_method
    def _make_tab_button(self, title: str, frame: tuple[int, int, int, int], action: str):
        button = TabButton.alloc().initWithFrame_(NSMakeRect(*frame))
        button.setTitle_(title)
        button.setTarget_(self)
        button.setAction_(action)
        return button


def _register_categories():
    from . import main_window_layout  # noqa: F401
    from . import main_window_core  # noqa: F401
    from . import adventure_controller  # noqa: F401
    from . import dice_controller  # noqa: F401
    from . import party_controller  # noqa: F401
    from . import combat_controller  # noqa: F401
    from . import spell_controller  # noqa: F401
    from . import item_controller  # noqa: F401


_register_categories()
