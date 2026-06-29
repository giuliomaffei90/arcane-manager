from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    @objc.python_method
    def _valid_party_characters(self, party: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if party is None:
            party = self.selectedParty()
        characters = party.get("characters", [])
        if not isinstance(characters, list):
            party["characters"] = []
            return []
        return [character for character in characters if isinstance(character, dict)]

    @objc.python_method
    def _ensure_party_enabled_state(self, party_index: int | None = None) -> list[bool]:
        if party_index is None:
            party_index = self.selectedPartyIndex()
        while len(self.party_member_enabled) < len(self.parties):
            self.party_member_enabled.append([])
        if party_index < 0 or party_index >= len(self.parties):
            return []
        characters = self._valid_party_characters(self.parties[party_index])
        enabled = self.party_member_enabled[party_index]
        if len(enabled) < len(characters):
            enabled.extend([True] * (len(characters) - len(enabled)))
        elif len(enabled) > len(characters):
            del enabled[len(characters):]
        return enabled

    @objc.python_method
    def _ensure_party_member_rows(self, count: int):
        while len(self.party_member_labels) < count:
            label = make_label("", (0, 0, 100, 38), 13, True)
            label.setHidden_(True)
            style_layer(label, theme_color("surface"), theme_color("border_soft"), 8, 1)
            self.party_member_labels.append(label)
            self.sidebar_content.addSubview_(label)

            checkbox = ReadyToggleButton.alloc().initWithFrame_(NSMakeRect(0, 0, 22, 22))
            checkbox.setTarget_(self)
            checkbox.setAction_("togglePartyMemberEnabled:")
            checkbox.setHidden_(True)
            self.party_member_checkboxes.append(checkbox)
            self.sidebar_content.addSubview_(checkbox)

            icon_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, 0, 20, 20))
            icon_view.setHidden_(True)
            self.party_member_icon_views.append(icon_view)
            self.sidebar_content.addSubview_(icon_view)

            name_label = make_label("", (0, 0, 80, 20), 13, True)
            class_label = make_label("", (0, 0, 80, 20), 12, True)
            ac_label = make_label("", (0, 0, 56, 20), 12, True)
            for row_label in (name_label, class_label, ac_label):
                row_label.setUsesSingleLineMode_(True)
                row_label.setLineBreakMode_(4)
                row_label.setHidden_(True)
                self.sidebar_content.addSubview_(row_label)
            self.party_member_name_labels.append(name_label)
            self.party_member_class_labels.append(class_label)
            self.party_member_ac_labels.append(ac_label)

    def loadParties(self) -> list[dict[str, Any]]:
        raw = NSUserDefaults.standardUserDefaults().stringForKey_(PARTIES_PREF)
        if raw:
            try:
                parties = json.loads(str(raw))
                if isinstance(parties, list):
                    return [party for party in parties if isinstance(party, dict)]
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        return [{"name": "Default Party", "characters": []}]

    def saveParties(self):
        defaults = NSUserDefaults.standardUserDefaults()
        defaults.setObject_forKey_(json.dumps(self.parties), PARTIES_PREF)
        defaults.synchronize()

    def selectedPartyIndex(self) -> int:
        index = int(self.party_popup.indexOfSelectedItem())
        if index < 0 or index >= len(self.parties):
            return 0
        return index

    def selectedParty(self) -> dict[str, Any]:
        if not self.parties:
            self.parties.append({"name": "Default Party", "characters": []})
        return self.parties[self.selectedPartyIndex()]

    def refreshPartyPopup(self):
        self.party_popup.removeAllItems()
        for party in self.parties:
            self.party_popup.addItemWithTitle_(str(party.get("name") or "Unnamed Party"))
        self.party_popup.selectItemAtIndex_(min(self.selectedPartyIndex(), max(0, len(self.parties) - 1)))
        self.party_popup.setNeedsDisplay_(True)
        self.syncPartyFields()
        self.layoutMainWindow()

    def syncPartyFields(self):
        party = self.selectedParty()
        visible_characters = self._valid_party_characters(party)
        self._ensure_party_member_rows(len(visible_characters))
        enabled_state = self._ensure_party_enabled_state()
        for index, label in enumerate(self.party_member_labels):
            icon_view = self.party_member_icon_views[index] if index < len(self.party_member_icon_views) else None
            checkbox = self.party_member_checkboxes[index] if index < len(self.party_member_checkboxes) else None
            row_labels = (
                self.party_member_name_labels[index],
                self.party_member_class_labels[index],
                self.party_member_ac_labels[index],
            )
            if index >= len(visible_characters):
                label.setHidden_(True)
                if checkbox is not None:
                    checkbox.setHidden_(True)
                if icon_view is not None:
                    icon_view.setHidden_(True)
                for row_label in row_labels:
                    row_label.setHidden_(True)
                continue
            character = visible_characters[index]
            name = str(character.get("name") or "Unnamed")
            class_name = str(character.get("class") or "Fighter")
            ac = str(character.get("ac") or "?")
            label.setStringValue_("")
            label.setHidden_(False)
            if checkbox is not None:
                checkbox.setTag_(index)
                checkbox.setState_(NSControlStateValueOn if enabled_state[index] else NSControlStateValueOff)
                checkbox.setHidden_(False)
            if icon_view is not None:
                image = icon_image(class_name)
                icon_view.setImage_(image)
                icon_view.setHidden_(image is None)
            self.party_member_name_labels[index].setStringValue_(name)
            self.party_member_class_labels[index].setStringValue_(class_name)
            self.party_member_ac_labels[index].setStringValue_(f"AC: {ac[:4]}")
            for row_label in row_labels:
                row_label.setHidden_(False)
        if visible_characters:
            selected_count = sum(1 for enabled in enabled_state[: len(visible_characters)] if enabled)
            self.party_status_label.setStringValue_(f"{selected_count}/{len(visible_characters)} member(s) ready")
        else:
            self.party_status_label.setStringValue_("No characters yet. Create or edit a party.")

    def selectParty_(self, _sender):
        self.party_popup.setNeedsDisplay_(True)
        self.syncPartyFields()
        self.layoutMainWindow()

    def togglePartyMemberEnabled_(self, sender):
        index = int(sender.tag())
        enabled = self._ensure_party_enabled_state()
        if index < 0 or index >= len(enabled):
            return
        enabled[index] = int(sender.state()) == NSControlStateValueOn
        self.syncPartyFields()
        self.layoutMainWindow()

    def newParty_(self, _sender):
        self.openPartyEditorForIndex_(-1)

    def editParty_(self, _sender):
        self.openPartyEditorForIndex_(self.selectedPartyIndex())

    def deleteParty_(self, _sender):
        if not self.parties:
            return
        index = self.selectedPartyIndex()
        party_name = str(self.parties[index].get("name") or "Unnamed Party")
        alert = NSAlert.alloc().init()
        alert.setMessageText_(f"Delete {party_name}?")
        alert.setInformativeText_("This removes the party from Arcane Manager. Current combatants already in the tracker are not changed.")
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        NSApp.activateIgnoringOtherApps_(True)
        if int(alert.runModal()) != 1000:
            return
        del self.parties[index]
        if index < len(self.party_member_enabled):
            del self.party_member_enabled[index]
        if not self.parties:
            self.parties.append({"name": "Default Party", "characters": []})
            self.party_member_enabled.append([])
        self.saveParties()
        self.refreshPartyPopup()
        self.party_popup.selectItemAtIndex_(min(index, len(self.parties) - 1))
        self.syncPartyFields()
        self.layoutMainWindow()

    def openPartyEditorForIndex_(self, index: int):
        self.editing_party_index = int(index)
        if 0 <= self.editing_party_index < len(self.parties):
            party = self.parties[self.editing_party_index]
            title = "Edit Party"
        else:
            party = {"name": "New Party", "characters": []}
            title = "New Party"

        characters = party.get("characters", [])
        self.editing_characters = [
            {
                "name": str(character.get("name") or ""),
                "class": str(character.get("class") or "Fighter"),
                "ac": str(character.get("ac") or "?"),
            }
            for character in characters
            if isinstance(character, dict)
        ]

        width = 520
        height = 420
        parent_frame = self.window.frame()
        x = parent_frame.origin.x + (parent_frame.size.width - width) / 2
        y = parent_frame.origin.y + (parent_frame.size.height - height) / 2
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
        self.party_editor_panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self.party_editor_panel.setTitle_(title)
        self.party_editor_panel.setFloatingPanel_(True)
        self.party_editor_panel.setHidesOnDeactivate_(False)
        self.party_editor_panel.setLevel_(24)
        self.party_editor_panel.setBackgroundColor_(theme_color("panel_alt", 0.97))

        content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        title_label = make_label(title, (24, 362, 472, 28), 18, True)
        name_label = make_label("Party name", (24, 322, 100, 24), 13, True)
        self.editor_party_name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(132, 322, 250, 26))
        self.editor_party_name_field.setStringValue_(str(party.get("name") or "New Party"))

        character_label = make_label("Character", (24, 278, 100, 24), 13, True)
        self.editor_character_name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(132, 278, 150, 26))
        self.editor_character_name_field.setPlaceholderString_("Name")
        self.editor_character_class_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(292, 278, 106, 26))
        for class_name in CLASS_OPTIONS:
            self.editor_character_class_popup.addItemWithTitle_(class_name)
        self.editor_character_class_popup.selectItemWithTitle_("Fighter")
        self.editor_character_ac_field = NSTextField.alloc().initWithFrame_(NSMakeRect(406, 278, 44, 26))
        self.editor_character_ac_field.setPlaceholderString_("AC")
        add_button = self._make_button("Add", (458, 278, 44, 26), "addEditorCharacter:")

        edit_label = make_label("Edit member", (24, 236, 100, 24), 13, True)
        self.editor_character_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(132, 236, 190, 26))
        self.editor_character_popup.setTarget_(self)
        self.editor_character_popup.setAction_("selectEditorCharacter:")
        update_button = self._make_button("Update", (334, 236, 70, 26), "updateEditorCharacter:")
        remove_button = self._make_button("Remove", (414, 236, 80, 26), "removeEditorCharacter:")

        list_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(24, 70, 472, 150))
        list_scroll.setHasVerticalScroller_(True)
        list_scroll.setAutohidesScrollers_(False)
        self.editor_character_list = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 448, 150))
        self.editor_character_list.setEditable_(False)
        self.editor_character_list.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        self.editor_character_list.setTextColor_(theme_color("text"))
        self.editor_character_list.setBackgroundColor_(theme_color("surface"))
        list_scroll.setDocumentView_(self.editor_character_list)

        save_button = self._make_button("Save Party", (284, 24, 100, 30), "saveEditorParty:")
        cancel_button = self._make_button("Cancel", (396, 24, 80, 30), "cancelEditorParty:")

        for view in (
            title_label,
            name_label,
            self.editor_party_name_field,
            character_label,
            self.editor_character_name_field,
            self.editor_character_class_popup,
            self.editor_character_ac_field,
            add_button,
            edit_label,
            self.editor_character_popup,
            update_button,
            remove_button,
            list_scroll,
            save_button,
            cancel_button,
        ):
            content.addSubview_(view)
        self.party_editor_panel.setContentView_(content)
        self.refreshEditorCharacterList()
        self.refreshEditorCharacterPopup()
        self.party_editor_panel.makeKeyAndOrderFront_(None)

    def refreshEditorCharacterPopup(self):
        if self.editor_character_popup is None:
            return
        selected = int(self.editor_character_popup.indexOfSelectedItem())
        self.editor_character_popup.removeAllItems()
        if not self.editing_characters:
            self.editor_character_popup.addItemWithTitle_("No members")
            self.editor_character_popup.setEnabled_(False)
            return
        self.editor_character_popup.setEnabled_(True)
        for character in self.editing_characters:
            self.editor_character_popup.addItemWithTitle_(str(character.get("name") or "Unnamed"))
        selected = min(max(0, selected), len(self.editing_characters) - 1)
        self.editor_character_popup.selectItemAtIndex_(selected)

    def selectedEditorCharacterIndex(self) -> int:
        if self.editor_character_popup is None or not self.editing_characters:
            return -1
        index = int(self.editor_character_popup.indexOfSelectedItem())
        if index < 0 or index >= len(self.editing_characters):
            return -1
        return index

    def selectEditorCharacter_(self, _sender):
        index = self.selectedEditorCharacterIndex()
        if index < 0:
            return
        character = self.editing_characters[index]
        self.editor_character_name_field.setStringValue_(str(character.get("name") or ""))
        self.editor_character_class_popup.selectItemWithTitle_(str(character.get("class") or "Fighter"))
        self.editor_character_ac_field.setStringValue_(str(character.get("ac") or ""))

    def refreshEditorCharacterList(self):
        if not self.editing_characters:
            self.editor_character_list.setString_("No characters yet. Add one with name and AC.")
            return
        rows = ["NAME                       CLASS       AC", "-------------------------  ----------  ----"]
        for character in self.editing_characters:
            name = str(character.get("name") or "")[:25].ljust(25)
            class_name = str(character.get("class") or "Fighter")[:10].ljust(10)
            ac = str(character.get("ac") or "?")[:4]
            rows.append(f"{name}  {class_name}  {ac}")
        self.editor_character_list.setString_("\n".join(rows))

    def addEditorCharacter_(self, _sender):
        name = str(self.editor_character_name_field.stringValue()).strip()
        class_name = str(self.editor_character_class_popup.titleOfSelectedItem() or "Fighter")
        ac = str(self.editor_character_ac_field.stringValue()).strip()
        if not name:
            return
        self.editing_characters.append({"name": name, "class": class_name, "ac": ac or "?"})
        self.editor_character_name_field.setStringValue_("")
        self.editor_character_class_popup.selectItemWithTitle_("Fighter")
        self.editor_character_ac_field.setStringValue_("")
        self.refreshEditorCharacterList()
        self.refreshEditorCharacterPopup()

    def updateEditorCharacter_(self, _sender):
        index = self.selectedEditorCharacterIndex()
        if index < 0:
            return
        name = str(self.editor_character_name_field.stringValue()).strip()
        class_name = str(self.editor_character_class_popup.titleOfSelectedItem() or "Fighter")
        ac = str(self.editor_character_ac_field.stringValue()).strip()
        if not name:
            return
        self.editing_characters[index] = {"name": name, "class": class_name, "ac": ac or "?"}
        self.refreshEditorCharacterList()
        self.refreshEditorCharacterPopup()
        self.editor_character_popup.selectItemAtIndex_(index)

    def removeEditorCharacter_(self, _sender):
        index = self.selectedEditorCharacterIndex()
        if index < 0:
            return
        del self.editing_characters[index]
        self.editor_character_name_field.setStringValue_("")
        self.editor_character_class_popup.selectItemWithTitle_("Fighter")
        self.editor_character_ac_field.setStringValue_("")
        self.refreshEditorCharacterList()
        self.refreshEditorCharacterPopup()

    def saveEditorParty_(self, _sender):
        name = str(self.editor_party_name_field.stringValue()).strip() or "Unnamed Party"
        party = {"name": name, "characters": list(self.editing_characters)}
        if 0 <= self.editing_party_index < len(self.parties):
            self.parties[self.editing_party_index] = party
            selected_index = self.editing_party_index
        else:
            self.parties.append(party)
            self.party_member_enabled.append([])
            selected_index = len(self.parties) - 1
        self.saveParties()
        self.refreshPartyPopup()
        self.party_popup.selectItemAtIndex_(selected_index)
        self.syncPartyFields()
        self.layoutMainWindow()
        self.party_editor_panel.orderOut_(None)

    def cancelEditorParty_(self, _sender):
        self.party_editor_panel.orderOut_(None)
