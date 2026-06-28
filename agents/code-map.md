# Code Map

Use this map to edit the feature-specific module first instead of searching the
whole app.

## Entry Points And App Shell

* `main.py`: thin launcher only. It adds `src/` to `sys.path` and calls
  `arcane_manager.app.main`.
* `src/arcane_manager/app.py`: CLI args, application startup, `AppDelegate`,
  main menu, status menu, About, Settings entry point, and app shutdown.
* `src/arcane_manager/settings.py`: theme settings panel, color wells, reset
  theme action, and propagation of theme changes.

## Main Window Controllers

* `src/arcane_manager/controllers/main_window.py`: creates the main window,
  owns shared UI objects, initializes app state, builds base panels and
  controls, and registers controller categories.
* `src/arcane_manager/controllers/main_window_core.py`: window show/close,
  resize handling, tab switching, current-tab visibility, and text-change
  routing for live search/editing.
* `src/arcane_manager/controllers/main_window_layout.py`: `applyTheme` and
  `layoutMainWindow`; edit here for responsive layout, frames, panel sizing,
  and theme application across visible controls.
* `src/arcane_manager/controllers/party_controller.py`: party persistence,
  party popup, party editor panel, character add/edit/remove, and party member
  rows in the left initiative panel.
* `src/arcane_manager/controllers/combat_controller.py`: initiative prompts,
  starting combat, adding monsters, turn navigation, combatant sorting, HP
  adjustment, conditions/status menus, tracker refresh, and monster detail
  sheet.
* `src/arcane_manager/controllers/spell_controller.py`: monster search result
  rows, spell search filters/results, spell detail rendering, and opening a
  linked spell from another surface.
* `src/arcane_manager/controllers/dice_controller.py`: Dice Roller tab state,
  clicked dice pool, formula label, roll button, inline roll dispatch, and roll
  history display.
* `src/arcane_manager/controllers/adventure_controller.py`: Adventure tab,
  vault selection, note tree, note open/edit/save, Markdown rendering, wiki
  links, local asset resolution, file colors, rename/delete, and Finder actions.
* `src/arcane_manager/controllers/_shared.py`: imports shared by controller
  category modules. Keep it boring; avoid putting behavior here.

## Domain And Utility Modules

* `src/arcane_manager/data.py`: `Spell` and `Creature` models, JSON loading,
  bestiary search, challenge-rating helpers, ability modifiers, and safe display
  helpers for creature fields.
* `src/arcane_manager/spell_search.py`: spell level/school filter values and
  bilingual spell search ranking.
* `src/arcane_manager/spell_format.py`: spell detail title/meta/body formatting
  and component parsing.
* `src/arcane_manager/dice.py`: dice expression parsing, rolling, mixed formula
  support, roll formatting, and roll history storage/listeners.
* `src/arcane_manager/content_links.py`: detection ranges for clickable dice,
  monster attack/check bonuses, spell sections, and linked spell names in text.
* `src/arcane_manager/text_rendering.py`: attributed strings for spell bodies,
  monster bodies, tracker bodies, component badges, and HP bar text coloring.
* `src/arcane_manager/theme.py`: default theme colors, dice overlay theme
  payload, theme persistence, reset/load/save, and color conversion.
* `src/arcane_manager/adventure_utils.py`: `AdventureNode`, Adventure Markdown
  CSS, frontmatter/callout cleanup, natural sorting, Markdown parser setup, and
  safe path checks.
* `src/arcane_manager/text_utils.py`: normalization for search/transcripts and
  sanitization/bounding of untrusted JSON/display strings.
* `src/arcane_manager/resources.py`: bundled resource path resolution, default
  data/asset paths, log path, app retained object list, and file-size limits.
* `src/arcane_manager/logging_utils.py`: file/stdout logging helper.
* `src/arcane_manager/constants.py`: user-default keys, class and condition
  options, class icons, monster icon constants, and transcript normalization
  replacements.
* `src/arcane_manager/platform.py`: all PyObjC, AppKit, WebKit, Foundation, and
  standard-library imports shared across modules.

## UI Modules

* `src/arcane_manager/ui/core.py`: small reusable views and UI helpers such as
  labels, colors, input styling, drawing primitives, icon loading, text fitting,
  and combatant status helpers.
* `src/arcane_manager/ui/custom_views.py`: custom interactive/drawn controls:
  `DiceTextView`, search result rows, adventure tree rows, stat ability buttons,
  add buttons, styled popups, and `CombatTrackerView`.
* `src/arcane_manager/ui/dice_overlay.py`: protected dice UI subsystem:
  fallback dice animation, local `127.0.0.1` asset server, `WKWebView` overlay,
  `Dice3DRollerController`, and `show_3d_dice_roll`.

## PyObjC Structure Rules

* AppKit target/action and WebKit callback methods must live on `NSObject`
  subclasses or PyObjC categories such as the `MainWindowController` category
  modules.
* Do not move selector methods into plain Python mixins; inherited mixin methods
  do not register as Objective-C selectors.
* Helper-only methods inside PyObjC classes should use `@objc.python_method`
  when they are not intended to become selectors.
* Future large features may get a new dedicated module or controller file when
  they have distinct state, UI actions, data flow, or domain logic.
