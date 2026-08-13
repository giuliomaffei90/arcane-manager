# Arcane Manager

A desktop **Dungeons & Dragons 5e table companion**, built to run a whole
session - notes, initiative, dice, video, music - from one app instead of
several.

## Why

Running games the old way meant juggling a handful of unrelated apps at
once: Obsidian for notes, OBS for the video feed on the TV, a separate
audio tool for music/ambience/SFX. Every scene change or sound cue was a
context-switch away from the table. Arcane Manager started as an attempt to
fold all of that into one place, with the pieces actually talking to each
other instead of living in separate windows - a note's map can broadcast
straight to the external display, a spell's dice roll uses the same 3D
roller as combat, and so on. From there the scope kept growing: pretty much
any DM utility that came to mind got added, with the long-term goal of it
becoming *the* one-stop app for running a 5e table.

Everything runs locally; there is no backend.

## Features

Fourteen tabs, all backed by local SRD data and local files - no accounts, no
cloud sync.

### Adventure

An Obsidian‑style Markdown vault for session notes: folder tree with
colors, wiki‑links, a themed reader, and an editor with find & replace
(current file or vault-wide). A note can embed a full creature statblock
inline or a live‑updating link into a Calendar event, and an encounter
table rolls its own dice with a "Launch" link that stages the listed
creatures straight into Initiative. A map image can also broadcast
full-screen to the external display as a pan/zoomable overlay.

![Adventure notes, with an embedded campaign map](assets/readme/adventure-map.png)
![Adventure notes, with a rendered encounter table and Launch-to-Initiative buttons](assets/readme/adventure-notes.png)

### Calendar

A Calendar of Harptos tracker on its simplified 360‑day year: browse/
advance the campaign date, add DM events with tenday/month/year recurrence,
and link any event into an Adventure note as a live‑updating reference.
Each day's weather is procedurally rolled from the campaign's chosen biome,
with a manual per‑day override for when the story needs specific weather.

![Calendar of Harptos month view](assets/readme/calendar.png)

### Initiative

The combat tracker: rolled initiative, HP/status/conditions, turn
navigation, and a live DMG encounter‑difficulty readout before the fight
starts. A creature's statblock opens in a drawer with an interactive Cast
table - spells and limited‑use abilities roll their own dice and apply
damage or healing to a picked target, and a summon spell can drop its
creatures straight into the initiative order, bound to the caster's
concentration. Death saves, auto‑Unconscious at 0 HP, and massive‑damage
instant death are all handled without DM bookkeeping.

![Initiative tracker mid-fight, with a creature statblock open](assets/readme/initiative.png)

### Party

Manage parties and characters (class, AC, level, HP), toggle "ready"
before a session, and assign each character a combat video for the
external display. HP, conditions, and exhaustion level stay live‑synced
with the Initiative tracker, and a party‑wide Long Rest button heals
everyone, clears conditions, and steps exhaustion down in one click.

![Party Manager roster](assets/readme/party.png)

### Spells

Fuzzy bilingual (EN/IT) search with a detail view whose inline dice follow
that spell's actual scaling - a damage roll grows with slot level or
caster level exactly as written, not a flat approximation. DMs can author
and edit homebrew spells that live right alongside the bundled SRD list.

![Spells tab detail view](assets/readme/spells.png)

### Items

A searchable equipment browser with manual/book pricing. Most magic items
intentionally show no price until they're rolled into a generated shop's
stock, since 5e itself gives most of them no official one; DMs can author
custom items and named variants, printable to a reference-card PDF.

![Items tab detail view](assets/readme/items.png)

### Feats

A bilingual, searchable feat browser with prerequisites and full
descriptions, plus DM-authored custom feats alongside the bundled list.

![Feats tab detail view](assets/readme/feats.png)

### Races

A bilingual race/subrace browser with lore and structured mechanics
(ability bonuses, darkvision, languages, combat traits) that also feed the
NPC generator, not just the page here. DMs can author custom races and
subraces the same way.

![Races tab detail view](assets/readme/races.png)

### Classes

A class/subclass browser with level-by-level features and progression
tables, named option pools (Eldritch Invocations, Metamagic, ...), and
starting-equipment/multiclassing data alongside the table. Searching a
subclass name (e.g. "Battle Master") jumps straight to its parent class
with that subclass pre-selected, and a DM can author whole custom
classes/subclasses.

![Classes tab progression table](assets/readme/classes.png)

### Generators

Randomized content for the table, five generators sharing one
lock/reroll/favorite pattern and a favorites drawer:

**NPCs** - a full NPC with appearance, personality, occupation and daily
life, per‑field lock/reroll, and a lightweight ability-score/attack
character sheet.

![NPC generator](assets/readme/generators-npcs.png)

**Settlements** - a settlement with population, an authority figure,
notable citizens, a tavern, shops, and a procedurally composed coat of
arms; a ruined settlement type shows a reduced "abandoned" card instead of
the full roster.

![Settlement generator](assets/readme/generators-settlements.png)

**Taverns** - an innkeeper, patrons, and a printable in‑fiction drinks/food
menu with its own prices and ABV.

![Tavern generator with a printable menu](assets/readme/generators-taverns.png)

**Businesses** - an owner and current wares, with a shared shopping cart,
merchant‑mood/city‑wealth sliders that shift prices, and a scroll‑price
calculator.

![Business generator with a shopping cart receipt](assets/readme/generators-businesses.png)

**Bookshops** - an owner and a searchable, sortable list of stock (by
title, genre, year, or price), each book's synopsis a tap away, sharing
the Businesses cart.

![Bookshop generator with a searchable book list](assets/readme/generators-bookshops.png)

### Calculators

Standalone DM math: travel time by pace/vehicle, fall damage, bounty
rewards, mercenary hire cost, a feet/meters/miles/kilometers distance
converter using D&D's own rounding, and a coin‑split calculator that pays
out without ever breaking a coin into smaller change.

![Calculators tab](assets/readme/calculators.png)

### Dice Roller

Build a dice pool and roll it with real **3D physics dice** in a WebView
overlay, with one-click Advantage/Disadvantage and a built-in Wild Magic
Surge d100 table. Every clickable dice link elsewhere in the app (spells,
statblocks, notes, feats) rolls in the same overlay, which can also go
full-screen on the external display for the whole table to see.

![Dice pool builder](assets/readme/dice-roller.png)
![3D dice roll overlay](assets/readme/dice-roller-3d.png)

### Video

A local video library that plays out to a second monitor, automatically
switching to whichever combatant is acting during a fight (a PC's own
video, a monster/ally/lair-actions video, or an idle image), with
crossfade/stinger transitions. A clip that's been moved or renamed on disk
is flagged as offline and can be batch-relinked from a folder instead of
silently breaking.

![Video library](assets/readme/video.png)

### Soundboard

Music, Ambient and SFX side by side, each with its own volume and its own
clip groups. Music crossfades between tracks and can auto-start shuffled
when a fight begins; any number of Ambient clips loop and layer at once;
SFX overlap freely on top of everything else.

![Soundboard](assets/readme/soundboard.png)

Plus a **Settings** panel (theme, vault/display pickers, sourcebook
filters, tab visibility) and a global **Command Palette** for jumping
straight to any spell, item, creature, race or feat.

The app ships with no bundled spell/creature/item/race/feat/class data - a DM
imports whichever SRD dataset(s) they want via Settings > Import/Export,
either one data type at a time or all six at once from a single folder.

## Tech

- Flutter (desktop: macOS / Windows / Linux), Riverpod for state,
  `shared_preferences` for persistence, `flutter_inappwebview` + a small local
  HTTP server for the 3D dice, the Markdown reader and Mermaid diagrams,
  `file_picker` for the vault folder, `media_kit` for soundboard/video
  playback, `window_manager` / `desktop_multi_window` / `screen_retriever`
  for the external‑display output, `desktop_drop` for drag‑and‑drop imports,
  `flutter_localizations` + `intl` for the (currently EN/IT) UI
  localization, `pdf` for the printable tavern menu and item reference
  card, and `package_info_plus` + `http` for the GitHub‑release update
  check.

## Credits

For the third‑party libraries this app bundles and their licenses, see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

*Fully vibecoded, zero shame about it - I designed every feature and
personally beat on every corner of this app until it held up. AI were
involved, but so was a lot of human love.*

Developed by **Giulio Maffei**, with heartfelt thanks to Francesco D., Alice,
Fabio, Benedetta, Cristina, Giorgio, Davide, Daniele, Michele, Ilaria,
Antonio, Lorenzo, and Ismael, for welcoming him into this wonderful game and
making it something worth building a whole app for.

Special thanks to Francesco M. for all his help with debugging and testing
the app.
