from __future__ import annotations

from .controllers._shared import *
from .controllers.main_window import MainWindowController
from .settings import SettingsController
from .ui import dice_overlay

class AppDelegate(NSObject):
    spells: list[Spell]
    creatures: list[Creature]
    items: list[Item]
    spell_lookup: dict[str, Spell]
    status_item: Any
    main_controller: MainWindowController
    settings_controller: SettingsController

    def initWithSpells_creatures_spellLookup_items_(
        self,
        spells,
        creatures,
        spell_lookup,
        items,
    ):
        self = objc.super(AppDelegate, self).init()
        if self is None:
            return None
        self.spells = list(spells)
        self.creatures = list(creatures)
        self.items = list(items)
        self.spell_lookup = spell_lookup
        self.status_item = None
        self.main_controller = None
        self.settings_controller = None
        return self

    def applicationDidFinishLaunching_(self, _notification):
        load_theme_overrides()
        self.main_controller = MainWindowController.alloc().initWithBestiary_spells_spellLookup_items_(
            self.creatures,
            self.spells,
            self.spell_lookup,
            self.items,
        )
        APP_RETAINED_OBJECTS.append(self.main_controller)
        self.installMainMenu()
        self.installStatusMenu()
        self.main_controller.show_(None)

    def installMainMenu(self):
        main_menu = NSMenu.alloc().init()
        app_menu_item = NSMenuItem.alloc().init()
        main_menu.addItem_(app_menu_item)

        app_menu = NSMenu.alloc().init()
        about_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About Arcane Manager",
            "showAbout:",
            "",
        )
        about_item.setTarget_(self)
        app_menu.addItem_(about_item)
        app_menu.addItem_(NSMenuItem.separatorItem())

        settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings...",
            "showSettings:",
            ",",
        )
        settings_item.setTarget_(self)
        app_menu.addItem_(settings_item)
        app_menu.addItem_(NSMenuItem.separatorItem())

        main_window_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show Main Window",
            "showMainWindow:",
            "0",
        )
        main_window_item.setTarget_(self)
        app_menu.addItem_(main_window_item)
        app_menu.addItem_(NSMenuItem.separatorItem())

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit Arcane Manager", "quit:", "q")
        quit_item.setTarget_(self)
        app_menu.addItem_(quit_item)

        app_menu_item.setSubmenu_(app_menu)

        edit_menu_item = NSMenuItem.alloc().init()
        main_menu.addItem_(edit_menu_item)
        edit_menu = NSMenu.alloc().initWithTitle_("Edit")
        undo_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Undo", "undo:", "z")
        edit_menu.addItem_(undo_item)
        redo_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Redo", "redo:", "Z")
        edit_menu.addItem_(redo_item)
        edit_menu.addItem_(NSMenuItem.separatorItem())
        cut_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
        edit_menu.addItem_(cut_item)
        copy_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Copy", "copy:", "c")
        edit_menu.addItem_(copy_item)
        paste_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
        edit_menu.addItem_(paste_item)
        edit_menu.addItem_(NSMenuItem.separatorItem())
        select_all_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Select All", "selectAll:", "a")
        edit_menu.addItem_(select_all_item)
        edit_menu_item.setSubmenu_(edit_menu)
        NSApp.setMainMenu_(main_menu)

    def installStatusMenu(self):
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        button = self.status_item.button()
        if button is not None:
            button.setTitle_("AW")
            button.setToolTip_("Arcane Manager")

        menu = NSMenu.alloc().init()
        about_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About Arcane Manager",
            "showAbout:",
            "",
        )
        about_item.setTarget_(self)
        menu.addItem_(about_item)
        menu.addItem_(NSMenuItem.separatorItem())

        settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings...",
            "showSettings:",
            "",
        )
        settings_item.setTarget_(self)
        menu.addItem_(settings_item)
        menu.addItem_(NSMenuItem.separatorItem())

        main_window_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show Main Window",
            "showMainWindow:",
            "",
        )
        main_window_item.setTarget_(self)
        menu.addItem_(main_window_item)
        menu.addItem_(NSMenuItem.separatorItem())

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit Arcane Manager", "quit:", "q")
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)
        self.status_item.setMenu_(menu)

    def showMainWindow_(self, _sender):
        self.main_controller.show_(None)

    def showSettings_(self, _sender):
        if self.settings_controller is None:
            self.settings_controller = SettingsController.alloc().initWithAppDelegate_(self)
            APP_RETAINED_OBJECTS.append(self.settings_controller)
        self.settings_controller.show_(None)

    @objc.python_method
    def applyThemeFromSettings(self):
        if self.main_controller is not None:
            self.main_controller.applyTheme()
        if self.settings_controller is not None:
            self.settings_controller.panel.setBackgroundColor_(theme_color("panel_alt", 0.98))
        if dice_overlay.THREE_D_DICE_ROLLER is not None:
            dice_overlay.THREE_D_DICE_ROLLER.applyTheme()

    def showAbout_(self, _sender):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Arcane Manager")
        alert.setInformativeText_(
            "A Dungeons & Dragons 5e table assistant with spells, bestiary, "
            "initiative tracking, and dice rolling.\n\n"
            "Developed by Giulio Maffei and Francesco Di Castri."
        )
        alert.addButtonWithTitle_("OK")
        NSApp.activateIgnoringOtherApps_(True)
        alert.runModal()

    def applicationShouldTerminateAfterLastWindowClosed_(self, _sender):
        return False

    def quit_(self, _sender):
        if self.main_controller is not None and not self.main_controller.confirmAdventureCanDiscardOrSave():
            return
        NSApp.terminate_(None)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Arcane Manager for macOS.")
    parser.add_argument(
        "--spells",
        default=str(DEFAULT_SPELLS_FILE),
        help="Path to a JSON spell database.",
    )
    parser.add_argument(
        "--bestiary",
        default=str(DEFAULT_BESTIARY_FILE),
        help="Path to a JSON SRD bestiary database.",
    )
    parser.add_argument(
        "--items",
        default=str(DEFAULT_ITEMS_FILE),
        help="Path to a JSON item database.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    spells, lookup = load_spells(Path(args.spells).expanduser())
    creatures = load_bestiary(Path(args.bestiary).expanduser())
    items = load_items(Path(args.items).expanduser())
    if not spells:
        raise SystemExit("No spells found in the spell database.")

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    delegate = AppDelegate.alloc().initWithSpells_creatures_spellLookup_items_(
        spells,
        creatures,
        lookup,
        items,
    )
    APP_RETAINED_OBJECTS.append(delegate)
    log(f"Starting app with {len(spells)} spells, {len(creatures)} creatures, and {len(items)} items.")
    app.setDelegate_(delegate)
    app.run()
    return 0
