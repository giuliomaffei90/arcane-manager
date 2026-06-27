from __future__ import annotations

from ._shared import *
from .main_window import MainWindowController as _MainWindowController


class MainWindowController(objc.Category(_MainWindowController)):
    @objc.python_method
    def loadAdventureVaultFromDefaults(self):
        defaults = NSUserDefaults.standardUserDefaults()
        raw_path = defaults.stringForKey_(ADVENTURE_VAULT_PREF)
        if not raw_path:
            self.refreshAdventureWorkspace()
            return
        vault_path = Path(str(raw_path)).expanduser()
        if not vault_path.is_dir():
            self.refreshAdventureWorkspace()
            return
        self.setAdventureVault_(vault_path)
        raw_note = defaults.stringForKey_(ADVENTURE_SELECTED_NOTE_PREF)
        if raw_note:
            note_path = Path(str(raw_note))
            if note_path.is_file() and safe_relative_to(note_path, vault_path):
                self.openAdventureNote_(note_path)
                return
        first_note = self.firstAdventureNote()
        if first_note is not None:
            self.openAdventureNote_(first_note)

    def chooseAdventureFolder_(self, _sender):
        if not self.confirmAdventureCanDiscardOrSave():
            return
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setAllowsMultipleSelection_(False)
        panel.setCanCreateDirectories_(False)
        panel.setMessage_("Choose the folder that contains your Markdown adventure notes.")
        if self.adventure_vault_path is not None:
            panel.setDirectoryURL_(NSURL.fileURLWithPath_(str(self.adventure_vault_path)))
        NSApp.activateIgnoringOtherApps_(True)
        if int(panel.runModal()) not in (1, 1000):
            log("Adventure folder selection cancelled.")
            return
        url = panel.URL()
        if url is None:
            return
        path = Path(str(url.path()))
        if not path.is_dir():
            log(f"Adventure folder selection ignored because path is not a directory: {path}")
            return
        log(f"Adventure folder selected: {path}")
        self.current_tab = "adventure"
        self.setAdventureVault_(path)
        first_note = self.firstAdventureNote()
        if first_note is not None:
            self.openAdventureNote_(first_note)
            log(f"Adventure opened first note: {first_note}")
        else:
            self.adventure_selected_note = None
            self.showAdventureEmpty_("No Markdown notes found in this folder.")
            log(f"Adventure folder has no Markdown notes: {path}")
        self.refreshAdventureWorkspace()
        self.applyCurrentTab()
        self.window.makeKeyAndOrderFront_(None)

    @objc.python_method
    def setAdventureVault_(self, path: Path):
        self.adventure_vault_path = path.resolve()
        defaults = NSUserDefaults.standardUserDefaults()
        defaults.setObject_forKey_(str(self.adventure_vault_path), ADVENTURE_VAULT_PREF)
        defaults.synchronize()
        self.adventure_selected_note = None
        self.adventure_is_editing = False
        self.adventure_dirty = False
        self.adventure_last_saved_text = ""
        self.loadAdventureFileColors()
        self.buildAdventureIndexes()
        self.adventure_root_node = self.buildAdventureNode(self.adventure_vault_path, 0)
        self.adventure_expanded_paths = set()
        if self.adventure_root_node is not None:
            self.collectAdventureDirectoryPaths(self.adventure_root_node, self.adventure_expanded_paths)
        self.refreshAdventureTree()
        self.refreshAdventureControls()
        log(
            "Adventure vault loaded: "
            f"{self.adventure_vault_path} "
            f"({len(self.adventure_note_index)} note keys, {len(self.adventure_flat_nodes)} visible rows)"
        )

    @objc.python_method
    def loadAdventureFileColors(self):
        self.adventure_file_colors = {}
        if self.adventure_vault_path is None:
            return
        path = self.adventure_vault_path / ".obsidian" / "plugins" / "obsidian-file-color" / "data.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return
        palette = {
            str(item.get("id")): str(item.get("value"))
            for item in data.get("palette", [])
            if isinstance(item, dict) and item.get("id") and item.get("value")
        }
        for item in data.get("fileColors", []):
            if not isinstance(item, dict):
                continue
            rel_path = str(item.get("path") or "").strip().strip("/")
            color = palette.get(str(item.get("color") or ""))
            if rel_path and color:
                self.adventure_file_colors[rel_path] = color

    @objc.python_method
    def buildAdventureIndexes(self):
        self.adventure_note_index = {}
        self.adventure_asset_index = {}
        if self.adventure_vault_path is None:
            return
        for path in sorted(self.adventure_vault_path.rglob("*"), key=lambda item: normalize(str(item.relative_to(self.adventure_vault_path)))):
            if any(part.startswith(".") for part in path.relative_to(self.adventure_vault_path).parts):
                continue
            if path.is_file() and path.suffix.lower() in (".md", ".markdown"):
                rel = path.relative_to(self.adventure_vault_path)
                keys = {
                    normalize(path.stem),
                    normalize(str(rel.with_suffix(""))),
                    normalize(str(rel)),
                }
                for key in keys:
                    if key:
                        self.adventure_note_index.setdefault(key, []).append(path)
            elif path.is_file():
                key = normalize(path.name)
                if key:
                    self.adventure_asset_index.setdefault(key, []).append(path)

    @objc.python_method
    def buildAdventureNode(self, path: Path, depth: int) -> AdventureNode | None:
        if path.is_file():
            if path.suffix.lower() not in (".md", ".markdown"):
                return None
            return AdventureNode(path=path, name=path.stem, is_dir=False, depth=depth, children=[])
        if path.name.startswith(".") and path != self.adventure_vault_path:
            return None
        children: list[AdventureNode] = []
        try:
            entries = list(path.iterdir())
        except OSError:
            entries = []
        entries.sort(key=lambda item: (not item.is_dir(), natural_sort_key(item.name)))
        for entry in entries:
            child = self.buildAdventureNode(entry, depth + 1)
            if child is not None:
                children.append(child)
        if path == self.adventure_vault_path or children:
            return AdventureNode(path=path, name=path.name, is_dir=True, depth=depth, children=children)
        return None

    @objc.python_method
    def collectAdventureDirectoryPaths(self, node: AdventureNode, result: set[str]):
        if not node.is_dir:
            return
        result.add(str(node.path))
        for child in node.children:
            self.collectAdventureDirectoryPaths(child, result)

    @objc.python_method
    def firstAdventureNote(self) -> Path | None:
        if self.adventure_root_node is None:
            return None
        stack = list(self.adventure_root_node.children)
        while stack:
            node = stack.pop(0)
            if not node.is_dir:
                return node.path
            stack = list(node.children) + stack
        return None

    @objc.python_method
    def refreshAdventureWorkspace(self):
        self.refreshAdventureTree()
        self.refreshAdventureControls()
        if self.adventure_vault_path is None:
            self.showAdventureEmpty_("Choose a local folder to browse your Markdown adventure notes.")
        elif self.adventure_selected_note is None:
            self.showAdventureEmpty_("Select a Markdown note from the left.")

    @objc.python_method
    def refreshAdventureTree(self):
        self.adventure_flat_nodes = []
        if self.adventure_root_node is not None:
            for child in self.adventure_root_node.children:
                self.flattenAdventureNode(child)
        while len(self.adventure_tree_buttons) < len(self.adventure_flat_nodes):
            button = AdventureTreeButton.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 26))
            button.setTarget_(self)
            button.setAction_("selectAdventureTreeRow:")
            button.setHidden_(True)
            self.adventure_tree_buttons.append(button)
            self.adventure_tree_content.addSubview_(button)
        for index, button in enumerate(self.adventure_tree_buttons):
            if index >= len(self.adventure_flat_nodes):
                button.setHidden_(True)
                continue
            node = self.adventure_flat_nodes[index]
            button.setTag_(index)
            button.configureName_path_depth_isDir_expanded_selected_color_(
                node.name,
                str(node.path),
                node.depth,
                node.is_dir,
                str(node.path) in self.adventure_expanded_paths,
                self.adventure_selected_note is not None and node.path.resolve() == self.adventure_selected_note.resolve(),
                self.adventureColorForPath(node.path),
            )
            button.setHidden_(False)
        self.layoutMainWindow()

    @objc.python_method
    def flattenAdventureNode(self, node: AdventureNode):
        self.adventure_flat_nodes.append(node)
        if not node.is_dir or str(node.path) not in self.adventure_expanded_paths:
            return
        for child in node.children:
            self.flattenAdventureNode(child)

    @objc.python_method
    def adventureColorForPath(self, path: Path) -> str:
        if self.adventure_vault_path is None:
            return ""
        try:
            rel = self.adventureRelativePath(path)
        except ValueError:
            return ""
        candidates = []
        current = rel
        while current:
            candidates.append(current)
            current = str(Path(current).parent).replace("\\", "/")
            if current == ".":
                break
        for candidate in candidates:
            if candidate in self.adventure_file_colors:
                return self.adventure_file_colors[candidate]
        return ""

    def selectAdventureTreeRow_(self, sender):
        index = int(sender.tag())
        if index < 0 or index >= len(self.adventure_flat_nodes):
            return
        node = self.adventure_flat_nodes[index]
        if node.is_dir:
            key = str(node.path)
            if key in self.adventure_expanded_paths:
                self.adventure_expanded_paths.remove(key)
            else:
                self.adventure_expanded_paths.add(key)
            self.refreshAdventureTree()
            return
        if not self.confirmAdventureCanDiscardOrSave():
            return
        self.openAdventureNote_(node.path)

    def adventureContextMenuForButton_(self, button):
        index = int(button.tag())
        if index < 0 or index >= len(self.adventure_flat_nodes):
            return None
        node = self.adventure_flat_nodes[index]
        menu = NSMenu.alloc().init()

        color_menu = NSMenu.alloc().init()
        none_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("None", "setAdventureTreeColor:", "")
        none_item.setTarget_(self)
        none_item.setRepresentedObject_(json.dumps({"path": str(node.path), "color": ""}))
        color_menu.addItem_(none_item)
        color_menu.addItem_(NSMenuItem.separatorItem())
        for color_name, _hex_value in ADVENTURE_COLOR_PALETTE:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(color_name, "setAdventureTreeColor:", "")
            item.setTarget_(self)
            item.setRepresentedObject_(json.dumps({"path": str(node.path), "color": color_name}))
            color_menu.addItem_(item)

        set_color_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Set color", None, "")
        set_color_item.setSubmenu_(color_menu)
        menu.addItem_(set_color_item)
        menu.addItem_(NSMenuItem.separatorItem())

        show_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Show in Finder", "showAdventureTreeItemInFinder:", "")
        show_item.setTarget_(self)
        show_item.setRepresentedObject_(str(node.path))
        menu.addItem_(show_item)
        menu.addItem_(NSMenuItem.separatorItem())

        rename_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Rename", "renameAdventureTreeItem:", "")
        rename_item.setTarget_(self)
        rename_item.setRepresentedObject_(str(node.path))
        menu.addItem_(rename_item)

        delete_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Delete", "deleteAdventureTreeItem:", "")
        delete_item.setTarget_(self)
        delete_item.setRepresentedObject_(str(node.path))
        menu.addItem_(delete_item)
        return menu

    @objc.python_method
    def adventurePathFromMenuItem(self, sender) -> Path | None:
        raw = sender.representedObject() if sender is not None else None
        if raw is None or self.adventure_vault_path is None:
            return None
        path = Path(str(raw)).resolve()
        if not safe_relative_to(path, self.adventure_vault_path):
            return None
        return path

    def showAdventureTreeItemInFinder_(self, sender):
        path = self.adventurePathFromMenuItem(sender)
        if path is None:
            return
        NSWorkspace.sharedWorkspace().activateFileViewerSelectingURLs_([NSURL.fileURLWithPath_(str(path))])

    def setAdventureTreeColor_(self, sender):
        if self.adventure_vault_path is None:
            return
        raw = sender.representedObject() if sender is not None else None
        try:
            payload = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return
        path = Path(str(payload.get("path") or "")).resolve()
        color_name = str(payload.get("color") or "")
        if not safe_relative_to(path, self.adventure_vault_path):
            return
        self.setAdventureColorForPath_color_(path, color_name)

    @objc.python_method
    def adventureRelativePath(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.adventure_vault_path.resolve())).replace("\\", "/")

    @objc.python_method
    def setAdventureColorForPath_color_(self, path: Path, color_name: str):
        data = self.loadAdventureColorData()
        palette_ids = self.ensureAdventureColorPalette(data)
        rel_path = self.adventureRelativePath(path)
        file_colors = [item for item in data.get("fileColors", []) if isinstance(item, dict)]
        file_colors = [item for item in file_colors if str(item.get("path") or "").strip().strip("/") != rel_path]
        if color_name:
            color_id = palette_ids.get(color_name)
            if color_id:
                file_colors.append({"path": rel_path, "color": color_id})
        data["fileColors"] = file_colors
        self.saveAdventureColorData(data)
        self.loadAdventureFileColors()
        self.refreshAdventureTree()

    def renameAdventureTreeItem_(self, sender):
        path = self.adventurePathFromMenuItem(sender)
        if path is None or self.adventure_vault_path is None or not path.exists():
            return
        if not self.confirmAdventureCanDiscardOrSave():
            return

        old_name = path.name
        old_stem = path.stem
        field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 360, 26))
        field.setStringValue_(old_name)
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Rename")
        alert.setInformativeText_(f"Enter a new name for {old_name}.")
        alert.setAccessoryView_(field)
        alert.addButtonWithTitle_("Rename")
        alert.addButtonWithTitle_("Cancel")
        NSApp.activateIgnoringOtherApps_(True)
        if int(alert.runModal()) != 1000:
            return

        new_name = str(field.stringValue()).strip()
        if not new_name:
            self.showAdventureAlert_message_("Rename failed", "Name cannot be empty.")
            return
        if "/" in new_name or "\\" in new_name or new_name in (".", ".."):
            self.showAdventureAlert_message_("Rename failed", "Name cannot contain path separators.")
            return
        if path.is_file() and path.suffix.lower() in (".md", ".markdown") and Path(new_name).suffix == "":
            new_name = f"{new_name}{path.suffix}"
        destination = (path.parent / new_name).resolve()
        if not safe_relative_to(destination, self.adventure_vault_path):
            self.showAdventureAlert_message_("Rename failed", "Destination is outside the selected folder.")
            return
        if destination.exists():
            self.showAdventureAlert_message_("Rename failed", "A file or folder with that name already exists.")
            return
        try:
            path.rename(destination)
        except OSError as exc:
            log(f"Adventure rename failed: {exc}")
            self.showAdventureAlert_message_("Rename failed", str(exc))
            return

        self.updateAdventureColorPathsAfterRename_old_new_(path, destination)
        if path.is_file() and path.suffix.lower() in (".md", ".markdown"):
            self.updateAdventureWikiLinksForRename_oldStem_newStem_oldRel_newRel_(
                old_stem,
                destination.stem,
                str(Path(self.adventureRelativePath(path)).with_suffix("")).replace("\\", "/"),
                str(Path(self.adventureRelativePath(destination)).with_suffix("")).replace("\\", "/"),
            )
        if self.adventure_selected_note is not None and self.pathContainsPath_parent_child_(path, self.adventure_selected_note):
            if path.is_dir():
                rel = self.adventure_selected_note.resolve().relative_to(path.resolve())
                self.adventure_selected_note = (destination / rel).resolve()
            else:
                self.adventure_selected_note = destination
        self.rebuildAdventureAfterFileAction_select_(self.adventure_selected_note if self.adventure_selected_note and self.adventure_selected_note.exists() else destination)

    def deleteAdventureTreeItem_(self, sender):
        path = self.adventurePathFromMenuItem(sender)
        if path is None or self.adventure_vault_path is None or not path.exists():
            return
        if not self.confirmAdventureCanDiscardOrSave():
            return
        alert = NSAlert.alloc().init()
        alert.setMessageText_(f"Delete {path.name}?")
        alert.setInformativeText_("This moves the item to the macOS Trash.")
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        NSApp.activateIgnoringOtherApps_(True)
        if int(alert.runModal()) != 1000:
            return
        source = str(path.parent)
        recycle_result = NSWorkspace.sharedWorkspace().performFileOperation_source_destination_files_tag_(
            NSWorkspaceRecycleOperation,
            source,
            "",
            [path.name],
            None,
        )
        ok = bool(recycle_result[0]) if isinstance(recycle_result, tuple) else bool(recycle_result)
        if not ok:
            self.showAdventureAlert_message_("Delete failed", "The item could not be moved to Trash.")
            return
        self.removeAdventureColorPathsForDeletedPath_(path)
        selected_deleted = self.adventure_selected_note is not None and self.pathContainsPath_parent_child_(path, self.adventure_selected_note)
        self.adventure_selected_note = None if selected_deleted else self.adventure_selected_note
        self.rebuildAdventureAfterFileAction_select_(None if selected_deleted else self.adventure_selected_note)

    @objc.python_method
    def showAdventureAlert_message_(self, title: str, message: str):
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")
        NSApp.activateIgnoringOtherApps_(True)
        alert.runModal()

    @objc.python_method
    def pathContainsPath_parent_child_(self, parent: Path, child: Path) -> bool:
        parent = parent.resolve()
        child = child.resolve()
        if parent == child:
            return True
        if not parent.is_dir():
            return False
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    @objc.python_method
    def rebuildAdventureAfterFileAction_select_(self, selected: Path | None):
        if self.adventure_vault_path is None:
            return
        self.loadAdventureFileColors()
        self.buildAdventureIndexes()
        self.adventure_root_node = self.buildAdventureNode(self.adventure_vault_path, 0)
        if self.adventure_root_node is not None:
            self.collectAdventureDirectoryPaths(self.adventure_root_node, self.adventure_expanded_paths)
        self.refreshAdventureTree()
        if selected is not None and selected.exists() and selected.is_file():
            self.openAdventureNote_(selected)
        elif self.adventure_selected_note is None:
            first = self.firstAdventureNote()
            if first is not None:
                self.openAdventureNote_(first)
            else:
                self.showAdventureEmpty_("Select a Markdown note from the left.")
        self.refreshAdventureControls()

    @objc.python_method
    def adventureColorDataPath(self) -> Path:
        return self.adventure_vault_path / ".obsidian" / "plugins" / "obsidian-file-color" / "data.json"

    @objc.python_method
    def loadAdventureColorData(self) -> dict[str, Any]:
        path = self.adventureColorDataPath()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data.setdefault("cascadeColors", True)
                    data.setdefault("colorBackground", False)
                    data.setdefault("palette", [])
                    data.setdefault("fileColors", [])
                    return data
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        return {"cascadeColors": True, "colorBackground": False, "palette": [], "fileColors": []}

    @objc.python_method
    def saveAdventureColorData(self, data: dict[str, Any]):
        path = self.adventureColorDataPath()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @objc.python_method
    def ensureAdventureColorPalette(self, data: dict[str, Any]) -> dict[str, str]:
        palette = [item for item in data.get("palette", []) if isinstance(item, dict)]
        result: dict[str, str] = {}
        used_ids = {str(item.get("id")) for item in palette if item.get("id")}
        for color_name, hex_value in ADVENTURE_COLOR_PALETTE:
            existing = None
            for item in palette:
                if str(item.get("name") or "") == color_name or str(item.get("value") or "").lower() == hex_value.lower():
                    existing = item
                    break
            if existing is None:
                color_id = f"arcane-{normalize(color_name).replace(' ', '-') or color_name.lower()}"
                suffix = 2
                base_id = color_id
                while color_id in used_ids:
                    color_id = f"{base_id}-{suffix}"
                    suffix += 1
                existing = {"id": color_id, "name": color_name, "value": hex_value}
                palette.append(existing)
                used_ids.add(color_id)
            result[color_name] = str(existing.get("id"))
        data["palette"] = palette
        return result

    @objc.python_method
    def updateAdventureColorPathsAfterRename_old_new_(self, old_path: Path, new_path: Path):
        data = self.loadAdventureColorData()
        old_rel = self.adventureRelativePath(old_path)
        new_rel = self.adventureRelativePath(new_path)
        for item in data.get("fileColors", []):
            if not isinstance(item, dict):
                continue
            rel = str(item.get("path") or "").strip().strip("/")
            if rel == old_rel:
                item["path"] = new_rel
            elif rel.startswith(old_rel + "/"):
                item["path"] = new_rel + rel[len(old_rel) :]
        self.saveAdventureColorData(data)

    @objc.python_method
    def removeAdventureColorPathsForDeletedPath_(self, path: Path):
        data = self.loadAdventureColorData()
        rel_path = self.adventureRelativePath(path)
        data["fileColors"] = [
            item
            for item in data.get("fileColors", [])
            if isinstance(item, dict)
            and (lambda rel: rel != rel_path and not rel.startswith(rel_path + "/"))(str(item.get("path") or "").strip().strip("/"))
        ]
        self.saveAdventureColorData(data)

    @objc.python_method
    def updateAdventureWikiLinksForRename_oldStem_newStem_oldRel_newRel_(self, old_stem: str, new_stem: str, old_rel: str, new_rel: str):
        if self.adventure_vault_path is None:
            return
        pattern = re.compile(r"(?<!!)\[\[([^\]]+)\]\]")

        def replace_link(match):
            inner = match.group(1)
            target_part, alias = (inner.split("|", 1) + [""])[:2] if "|" in inner else (inner, "")
            target_base, heading = (target_part.split("#", 1) + [""])[:2] if "#" in target_part else (target_part, "")
            normalized_target = normalize(target_base.strip())
            if normalized_target == normalize(old_stem):
                replacement_target = new_stem
            elif normalized_target == normalize(old_rel):
                replacement_target = new_rel
            else:
                return match.group(0)
            if heading:
                replacement_target = f"{replacement_target}#{heading}"
            if alias:
                return f"[[{replacement_target}|{alias}]]"
            return f"[[{replacement_target}]]"

        for md_path in self.adventure_vault_path.rglob("*.md"):
            if any(part.startswith(".") for part in md_path.relative_to(self.adventure_vault_path).parts):
                continue
            try:
                original = md_path.read_text(encoding="utf-8")
            except OSError:
                continue
            updated = pattern.sub(replace_link, original)
            if updated != original:
                try:
                    md_path.write_text(updated, encoding="utf-8")
                except OSError as exc:
                    log(f"Adventure wikilink update failed for {md_path}: {exc}")

    @objc.python_method
    def openAdventureNote_(self, path: Path):
        if self.adventure_vault_path is None or not path.is_file() or not safe_relative_to(path, self.adventure_vault_path):
            return
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self.showAdventureEmpty_(f"Could not read note: {exc}")
            return
        self.adventure_selected_note = path.resolve()
        defaults = NSUserDefaults.standardUserDefaults()
        defaults.setObject_forKey_(str(self.adventure_selected_note), ADVENTURE_SELECTED_NOTE_PREF)
        defaults.synchronize()
        for parent in [self.adventure_selected_note.parent, *self.adventure_selected_note.parents]:
            if self.adventure_vault_path is not None and safe_relative_to(parent, self.adventure_vault_path):
                self.adventure_expanded_paths.add(str(parent))
            if parent == self.adventure_vault_path:
                break
        self.adventure_last_saved_text = text
        self.adventure_dirty = False
        if self.adventure_is_editing:
            self.adventure_editor_view.setString_(text)
        else:
            self.renderAdventureMarkdown_(text)
        self.refreshAdventureTree()
        self.refreshAdventureControls()

    @objc.python_method
    def showAdventureEmpty_(self, message: str):
        body = f"<p class='empty'>{html.escape(message)}</p>"
        self.loadAdventureHTMLBody_(body)
        self.adventure_status_label.setStringValue_(message)

    @objc.python_method
    def refreshAdventureControls(self):
        has_vault = self.adventure_vault_path is not None
        has_note = self.adventure_selected_note is not None
        self.adventure_title_label.setStringValue_(self.adventure_vault_path.name if has_vault else "Adventure")
        self.adventure_folder_button.setTitle_("Change Folder" if has_vault else "Choose Folder")
        self.adventure_toggle_button.setEnabled_(has_note)
        self.adventure_toggle_button.setTitle_("Preview" if self.adventure_is_editing else "Edit")
        self.adventure_save_button.setEnabled_(has_note and self.adventure_is_editing and self.adventure_dirty)
        self.adventure_save_button.setHidden_(not self.adventure_is_editing)
        self.adventure_dirty_label.setStringValue_("Unsaved" if self.adventure_dirty else "")
        if has_note and self.adventure_vault_path is not None:
            try:
                rel = str(self.adventure_selected_note.relative_to(self.adventure_vault_path)).replace("/", " / ")
            except ValueError:
                rel = self.adventure_selected_note.name
            self.adventure_status_label.setStringValue_(rel)
        elif has_vault:
            self.adventure_status_label.setStringValue_("Select a Markdown note from the left.")
        else:
            self.adventure_status_label.setStringValue_("Choose a folder of Markdown notes.")
        if self.current_tab == "adventure":
            self.adventure_web_view.setHidden_(self.adventure_is_editing)
            self.adventure_editor_scroll.setHidden_(not self.adventure_is_editing)

    def toggleAdventureMode_(self, _sender):
        if self.adventure_selected_note is None:
            return
        if self.adventure_is_editing:
            text = str(self.adventure_editor_view.string())
            self.adventure_dirty = text != self.adventure_last_saved_text
            self.adventure_is_editing = False
            self.renderAdventureMarkdown_(text)
        else:
            if self.adventure_dirty:
                text = str(self.adventure_editor_view.string())
            else:
                try:
                    text = self.adventure_selected_note.read_text(encoding="utf-8")
                except OSError:
                    text = self.adventure_last_saved_text
                self.adventure_editor_view.setString_(text)
                self.adventure_last_saved_text = text
                self.adventure_dirty = False
            self.adventure_is_editing = True
        self.refreshAdventureControls()
        self.layoutMainWindow()

    def saveAdventureNote_(self, _sender):
        self.saveAdventureCurrentNote()

    @objc.python_method
    def saveAdventureCurrentNote(self) -> bool:
        if self.adventure_selected_note is None or self.adventure_vault_path is None:
            return True
        if not safe_relative_to(self.adventure_selected_note, self.adventure_vault_path):
            return False
        text = str(self.adventure_editor_view.string()) if (self.adventure_is_editing or self.adventure_dirty) else self.adventure_last_saved_text
        try:
            self.adventure_selected_note.write_text(text, encoding="utf-8")
        except OSError as exc:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Could not save Adventure note")
            alert.setInformativeText_(str(exc))
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return False
        self.adventure_last_saved_text = text
        self.adventure_dirty = False
        self.buildAdventureIndexes()
        self.refreshAdventureControls()
        return True

    @objc.python_method
    def confirmAdventureCanDiscardOrSave(self) -> bool:
        if not self.adventure_dirty:
            return True
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Save changes to this Adventure note?")
        alert.setInformativeText_("You have unsaved Markdown edits.")
        alert.addButtonWithTitle_("Save")
        alert.addButtonWithTitle_("Discard")
        alert.addButtonWithTitle_("Cancel")
        NSApp.activateIgnoringOtherApps_(True)
        result = int(alert.runModal())
        if result == 1000:
            return self.saveAdventureCurrentNote()
        if result == 1001:
            self.adventure_dirty = False
            return True
        return False

    @objc.python_method
    def renderAdventureMarkdown_(self, markdown: str):
        if MarkdownIt is None:
            self.loadAdventureHTMLBody_("<p class='missing'>Install markdown-it-py to preview Markdown.</p>")
            return
        parser = markdown_parser()
        source = self.prepareAdventureMarkdown(markdown)
        rendered = parser.render(source) if parser is not None else html.escape(source)
        rendered = self.decorateAdventureHTML(rendered)
        self.loadAdventureHTMLBody_(rendered)

    @objc.python_method
    def prepareAdventureMarkdown(self, markdown: str) -> str:
        source = separate_obsidian_callout_titles(strip_markdown_frontmatter(markdown))

        def image_replace(match):
            target = match.group(1).strip()
            parts = [part.strip() for part in target.split("|", 1)]
            image_path = self.resolveAdventureAsset(parts[0])
            if image_path is None:
                alt = html.escape(parts[-1] if len(parts) > 1 else parts[0])
                return f"<p class=\"missing\">Missing image: {alt}</p>"
            alt = html.escape(parts[-1] if len(parts) > 1 else image_path.name)
            return f'<img src="{html.escape(image_path.as_uri())}" alt="{alt}">'

        def wiki_replace(match):
            target = match.group(1).strip()
            if not target:
                return ""
            label = target
            if "|" in target:
                target, label = [part.strip() for part in target.split("|", 1)]
            elif "#" in target:
                label = target.split("#", 1)[0] or target
            return (
                f'<a href="#" data-note="{html.escape(target, quote=True)}">'
                f"{html.escape(label)}</a>"
            )

        def dice_replace(match):
            expression = re.sub(r"\s+", "", match.group(1).strip())
            if not (DICE_PATTERN.fullmatch(expression) or DICE_FORMULA_PATTERN.fullmatch(expression)):
                return match.group(0)
            return (
                f'<a href="#" class="dice-link" data-dice="{html.escape(expression, quote=True)}">'
                f"🎲 {html.escape(expression)}</a>"
            )

        source = re.sub(r"!\[\[([^\]]+)\]\]", image_replace, source)
        source = re.sub(r"(?<!!)\[\[([^\]]+)\]\]", wiki_replace, source)
        source = re.sub(r"`\s*dice:\s*([^`]+)`", dice_replace, source, flags=re.I)
        return source

    @objc.python_method
    def decorateAdventureHTML(self, rendered: str) -> str:
        if BeautifulSoup is None:
            return rendered
        soup = BeautifulSoup(rendered, "html.parser")
        for blockquote in soup.find_all("blockquote"):
            first = blockquote.find(["p", "strong"])
            if first is None:
                continue
            text = first.get_text(" ", strip=True)
            match = re.match(r"\[!(\w+)\]\s*(.*)", text)
            if not match:
                continue
            kind = normalize(match.group(1)).replace(" ", "-") or "note"
            wrapper = soup.new_tag("div")
            wrapper["class"] = f"callout callout-{kind}"
            title_tag = soup.new_tag("div")
            title_tag["class"] = "callout-title"
            for child in list(first.contents):
                if isinstance(child, str):
                    cleaned = re.sub(r"^\[!\w+\]\s*", "", str(child), count=1)
                    if cleaned:
                        title_tag.append(cleaned)
                    continue
                title_tag.append(child.extract())
            if not title_tag.get_text(strip=True):
                title_tag.string = kind.title()
            wrapper.append(title_tag)
            first.extract()
            for child in list(blockquote.contents):
                wrapper.append(child.extract())
            blockquote.replace_with(wrapper)
        return str(soup)

    @objc.python_method
    def loadAdventureHTMLBody_(self, body: str):
        script = """
        <script>
        document.addEventListener('click', function(event) {
          var note = event.target.closest('a[data-note]');
          if (note) {
            event.preventDefault();
            window.webkit.messageHandlers.adventure.postMessage({type: 'note', target: note.dataset.note || ''});
            return;
          }
          var dice = event.target.closest('a[data-dice]');
          if (dice) {
            event.preventDefault();
            window.webkit.messageHandlers.adventure.postMessage({type: 'dice', expression: dice.dataset.dice || ''});
          }
        });
        </script>
        """
        document = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<style>{adventure_markdown_css()}</style></head><body><main>{body}</main>{script}</body></html>"
        )
        base_url = NSURL.fileURLWithPath_(str(self.adventure_vault_path)) if self.adventure_vault_path is not None else None
        self.adventure_web_view.loadHTMLString_baseURL_(document, base_url)

    @objc.python_method
    def resolveAdventureAsset(self, target: str) -> Path | None:
        if self.adventure_vault_path is None:
            return None
        clean = target.split("#", 1)[0].strip()
        candidates = []
        direct = (self.adventure_vault_path / clean).resolve()
        candidates.append(direct)
        if self.adventure_selected_note is not None:
            candidates.append((self.adventure_selected_note.parent / clean).resolve())
        candidates.extend(self.adventure_asset_index.get(normalize(Path(clean).name), []))
        for candidate in candidates:
            if candidate.exists() and candidate.is_file() and safe_relative_to(candidate, self.adventure_vault_path):
                return candidate.resolve()
        return None

    @objc.python_method
    def resolveAdventureNote(self, target: str) -> Path | None:
        if self.adventure_vault_path is None:
            return None
        clean = target.split("#", 1)[0].strip()
        if not clean:
            return self.adventure_selected_note
        possibilities = []
        raw = Path(clean)
        if raw.suffix.lower() not in (".md", ".markdown"):
            raw = raw.with_suffix(".md")
        possibilities.append((self.adventure_vault_path / raw).resolve())
        if self.adventure_selected_note is not None:
            possibilities.append((self.adventure_selected_note.parent / raw).resolve())
        keys = [normalize(clean), normalize(str(Path(clean).with_suffix(""))), normalize(Path(clean).name)]
        for key in keys:
            possibilities.extend(self.adventure_note_index.get(key, []))
        for candidate in possibilities:
            if candidate.exists() and candidate.is_file() and safe_relative_to(candidate, self.adventure_vault_path):
                return candidate.resolve()
        return None

    def userContentController_didReceiveScriptMessage_(self, _user_content_controller, message):
        body = message.body()
        if hasattr(body, "items"):
            payload = dict(body)
        elif hasattr(body, "objectForKey_"):
            payload = {
                key: body.objectForKey_(key)
                for key in ("type", "target", "expression")
                if body.objectForKey_(key) is not None
            }
        else:
            payload = {}
        message_type = str(payload.get("type") or "")
        if message_type == "dice":
            self.rollDice_(str(payload.get("expression") or ""))
            return
        if message_type != "note":
            return
        if not self.confirmAdventureCanDiscardOrSave():
            return
        note = self.resolveAdventureNote(str(payload.get("target") or ""))
        if note is None:
            self.adventure_status_label.setStringValue_("Linked note not found.")
            return
        self.openAdventureNote_(note)
