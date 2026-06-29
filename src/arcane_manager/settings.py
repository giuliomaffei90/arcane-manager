from __future__ import annotations

from .controllers._shared import *


class SettingsController(NSObject):
    panel: NSPanel
    app_delegate: Any
    scroll: NSScrollView
    content: FlippedView
    color_well_keys: dict[int, tuple[str, str]]
    color_wells: list[Any]
    theme_subsection_buttons: list[NSButton]
    theme_subsection_names: list[str]
    theme_subsection_expanded: dict[str, bool]

    def initWithAppDelegate_(self, app_delegate):
        self = objc.super(SettingsController, self).init()
        if self is None:
            return None
        self.app_delegate = app_delegate
        self.color_well_keys = {}
        self.color_wells = []
        self.theme_subsection_buttons = []
        self.theme_subsection_names = []
        self.theme_subsection_expanded = {
            "Surfaces": True,
            "Text": True,
            "Accents": True,
            "Adventure": True,
            "Dice": True,
        }

        width = 520
        height = 620
        screen = NSScreen.mainScreen().visibleFrame()
        x = screen.origin.x + (screen.size.width - width) / 2
        y = screen.origin.y + (screen.size.height - height) / 2
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setTitle_("Arcane Manager Settings")
        self.panel.setFloatingPanel_(True)
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setLevel_(24)
        self.panel.setBackgroundColor_(theme_color("panel_alt", 0.98))

        self.scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        self.scroll.setHasVerticalScroller_(True)
        self.scroll.setAutohidesScrollers_(False)
        self.scroll.setDrawsBackground_(False)
        self.scroll.setBorderType_(0)
        self.panel.setContentView_(self.scroll)
        self.rebuildSettingsContent_scrollToTop_(True)
        return self

    @objc.python_method
    def themeSubsections(self):
        return [
            (
                "Surfaces",
                "app",
                [
                    ("app_bg", "App background"),
                    ("panel", "Main panels"),
                    ("panel_alt", "Sidebar panels"),
                    ("surface_soft", "Soft surfaces"),
                    ("surface", "Controls and rows"),
                    ("surface_hover", "Hover and selected controls"),
                ],
            ),
            (
                "Text",
                "app",
                [
                    ("text", "Body text"),
                    ("text_strong", "Heading text"),
                    ("muted", "Muted text"),
                ],
            ),
            (
                "Accents",
                "app",
                [
                    ("border_soft", "Subtle borders"),
                    ("border", "Strong borders"),
                    ("link", "Links"),
                    ("dice", "Dice and HP"),
                    ("gold", "Spell metadata"),
                    ("danger", "Danger states"),
                    ("monster", "Monster emphasis"),
                    ("blue_temp", "Temporary HP"),
                    ("selection", "Selection"),
                ],
            ),
            (
                "Adventure",
                "app",
                [
                    ("adventure_reader_bg", "Reader background"),
                ],
            ),
            (
                "Dice",
                "dice",
                DICE_THEME_COLOR_LABELS,
            ),
        ]

    @objc.python_method
    def rebuildSettingsContent_scrollToTop_(self, scroll_to_top: bool):
        width = int(self.scroll.frame().size.width)
        y_cursor = 24
        row_height = 34
        section_gap = 18
        color_rows = 0
        for name, _section, rows in self.themeSubsections():
            color_rows += 1
            if self.theme_subsection_expanded.get(name, True):
                color_rows += len(rows)
        content_height = max(
            int(self.scroll.frame().size.height) + 1,
            24 + 66 + section_gap + 32 + color_rows * row_height + 34,
        )
        self.content = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, width, content_height))
        self.scroll.setDocumentView_(self.content)
        self.color_well_keys = {}
        self.color_wells = []
        self.theme_subsection_buttons = []
        self.theme_subsection_names = []

        y_cursor = self._addAdventureSectionAtY_(y_cursor)
        y_cursor += section_gap
        y_cursor = self._addThemeSectionAtY_(y_cursor)
        self.content.setFrame_(NSMakeRect(0, 0, width, max(content_height, y_cursor + 24)))
        self.syncColorWells()
        if scroll_to_top:
            self.scroll.contentView().scrollToPoint_(NSMakePoint(0, 0))
            self.scroll.reflectScrolledClipView_(self.scroll.contentView())

    @objc.python_method
    def _addAdventureSectionAtY_(self, y_cursor):
        section_label = make_label("Adventure", (24, y_cursor, 240, 24), 15, True)
        section_label.setTextColor_(theme_color("gold"))
        self.content.addSubview_(section_label)
        y_cursor += 32
        label = make_label("Markdown folder", (40, y_cursor + 5, 230, 20), 13, True)
        label.setTextColor_(theme_color("text"))
        button = StyledButton.alloc().initWithFrame_(NSMakeRect(300, y_cursor - 3, 174, 30))
        button.setTitle_("Change Folder")
        button.setTarget_(self)
        button.setAction_("chooseAdventureFolder:")
        style_button_layer(button)
        self.content.addSubview_(label)
        self.content.addSubview_(button)
        return y_cursor + 42

    @objc.python_method
    def _addThemeSectionAtY_(self, y_cursor):
        section_label = make_label("App Theme", (24, y_cursor, 240, 24), 15, True)
        section_label.setTextColor_(theme_color("gold"))
        self.content.addSubview_(section_label)
        y_cursor += 32
        for name, section, rows in self.themeSubsections():
            y_cursor = self._addThemeSubsection_name_section_rows_y_(name, section, rows, y_cursor)
        return y_cursor

    @objc.python_method
    def _addThemeSubsection_name_section_rows_y_(self, name, section, rows, y_cursor):
        expanded = self.theme_subsection_expanded.get(str(name), True)
        button = StyledButton.alloc().initWithFrame_(NSMakeRect(40, y_cursor, 260, 26))
        button.setTitle_(f"{'v' if expanded else '>'} {name}")
        button.setTarget_(self)
        button.setAction_("toggleThemeSubsection:")
        button.setTag_(len(self.theme_subsection_names))
        button.setBordered_(False)
        button.setSoftBackground_(True)
        style_button_layer(button, soft=True)
        self.theme_subsection_names.append(str(name))
        self.theme_subsection_buttons.append(button)
        self.content.addSubview_(button)
        y_cursor += 34
        if not expanded:
            return y_cursor
        for key, label_text in rows:
            label = make_label(str(label_text), (62, y_cursor + 5, 238, 20), 13, True)
            label.setTextColor_(theme_color("text"))
            well = NSColorWell.alloc().initWithFrame_(NSMakeRect(330, y_cursor, 44, 24))
            well.setTarget_(self)
            well.setAction_("themeColorChanged:")
            tag = len(self.color_wells) + 1
            well.setTag_(tag)
            self.color_well_keys[tag] = (str(section), str(key))
            self.color_wells.append(well)
            self.content.addSubview_(label)
            self.content.addSubview_(well)
            y_cursor += 34
        return y_cursor

    @objc.python_method
    def syncColorWells(self):
        for well in self.color_wells:
            section, key = self.color_well_keys.get(int(well.tag()), ("", ""))
            if section == "app" and key in THEME_RGB:
                well.setColor_(theme_color(key))
            elif section == "dice" and key in DICE_THEME_RGB:
                red, green, blue = DICE_THEME_RGB[key]
                well.setColor_(ui_color(red, green, blue, 1.0))

    def show_(self, _sender):
        self.panel.setBackgroundColor_(theme_color("panel_alt", 0.98))
        self.rebuildSettingsContent_scrollToTop_(True)
        NSApp.activateIgnoringOtherApps_(True)
        self.panel.makeKeyAndOrderFront_(None)

    def toggleThemeSubsection_(self, sender):
        index = int(sender.tag())
        if index < 0 or index >= len(self.theme_subsection_names):
            return
        name = self.theme_subsection_names[index]
        self.theme_subsection_expanded[name] = not self.theme_subsection_expanded.get(name, True)
        self.rebuildSettingsContent_scrollToTop_(False)

    def themeColorChanged_(self, sender):
        section, key = self.color_well_keys.get(int(sender.tag()), ("", ""))
        rgb = hex_to_rgb(color_to_hex(sender.color()))
        if rgb is None:
            return
        if section == "app" and key in THEME_RGB:
            THEME_RGB[key] = rgb
        elif section == "dice" and key in DICE_THEME_RGB:
            DICE_THEME_RGB[key] = rgb
        else:
            return
        save_theme_overrides()
        self.app_delegate.applyThemeFromSettings()

    def chooseAdventureFolder_(self, _sender):
        if self.app_delegate.main_controller is not None:
            self.app_delegate.main_controller.chooseAdventureFolder_(None)
