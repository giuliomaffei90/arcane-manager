from __future__ import annotations

from .controllers._shared import *

class SettingsController(NSObject):
    panel: NSPanel
    app_delegate: Any
    color_well_keys: dict[int, tuple[str, str]]
    color_wells: list[Any]

    def initWithAppDelegate_(self, app_delegate):
        self = objc.super(SettingsController, self).init()
        if self is None:
            return None
        self.app_delegate = app_delegate
        self.color_well_keys = {}
        self.color_wells = []

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

        content_height = 58 + (len(THEME_COLOR_LABELS) + len(DICE_THEME_COLOR_LABELS)) * 34 + 96
        scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(False)
        scroll.setDrawsBackground_(False)
        scroll.setBorderType_(0)
        content = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, width, content_height))
        scroll.setDocumentView_(content)

        y_cursor = 24
        title = make_label("Theme Colors", (24, y_cursor, 260, 28), 20, True)
        content.addSubview_(title)
        reset_button = NSButton.alloc().initWithFrame_(NSMakeRect(width - 150, y_cursor, 126, 30))
        reset_button.setTitle_("Reset Theme")
        reset_button.setTarget_(self)
        reset_button.setAction_("resetTheme:")
        style_layer(reset_button, theme_color("surface"), theme_color("border_soft"), 8, 1)
        content.addSubview_(reset_button)
        y_cursor += 46

        y_cursor = self._addSection_title_rows_originY_content_("App Theme", THEME_COLOR_LABELS, y_cursor, content)
        y_cursor += 18
        self._addSection_title_rows_originY_content_("Dice Overlay", DICE_THEME_COLOR_LABELS, y_cursor, content)

        self.panel.setContentView_(scroll)
        return self

    @objc.python_method
    def _addSection_title_rows_originY_content_(self, title_text, rows, y_cursor, content):
        section_label = make_label(str(title_text), (24, y_cursor, 240, 24), 15, True)
        section_label.setTextColor_(theme_color("gold"))
        content.addSubview_(section_label)
        y_cursor += 32
        section = "app" if str(title_text) == "App Theme" else "dice"
        for key, label_text in rows:
            label = make_label(str(label_text), (40, y_cursor + 5, 260, 20), 13, True)
            label.setTextColor_(theme_color("text"))
            well = NSColorWell.alloc().initWithFrame_(NSMakeRect(330, y_cursor, 44, 24))
            well.setTarget_(self)
            well.setAction_("themeColorChanged:")
            tag = len(self.color_wells) + 1
            well.setTag_(tag)
            self.color_well_keys[tag] = (section, key)
            self.color_wells.append(well)
            content.addSubview_(label)
            content.addSubview_(well)
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
        self.syncColorWells()
        NSApp.activateIgnoringOtherApps_(True)
        self.panel.makeKeyAndOrderFront_(None)

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

    def resetTheme_(self, _sender):
        reset_theme_overrides()
        self.syncColorWells()
        self.app_delegate.applyThemeFromSettings()
