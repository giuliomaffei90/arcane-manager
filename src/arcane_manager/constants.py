from __future__ import annotations

from .platform import Any

TRANSCRIPT_NORMALIZATION_REPLACEMENTS = {
    "appalla": "palla",
    "parla": "palla",
    "fuego": "fuoco",
    "fuega": "fuoco",
    "foco": "fuoco",
    "focca": "fuoco",
    "focco": "fuoco",
    "focore": "fuoco",
    "fogo": "fuoco",
    "forgo": "fuoco",
    "focor": "fuoco",
    "focori": "fuoco",
    "fuoco": "fuoco",
    "retardata": "ritardata",
    "riterdata": "ritardata",
    "ritedata": "ritardata",
    "tardata": "ritardata",
    "ritardato": "ritardata",
    "ritardo": "ritardata",
    "return": "ritardata",
    "focorita": "fuoco ritardata",
    "focoritardata": "fuoco ritardata",
    "ward": "word",
    "wards": "word",
    "words": "word",
}


PARTIES_PREF = "InitiativeParties"
ADVENTURE_VAULT_PREF = "AdventureVaultPath"
ADVENTURE_SELECTED_NOTE_PREF = "AdventureSelectedNotePath"
ADVENTURE_TREE_WIDTH_PREF = "AdventureTreeWidth"
CLASS_OPTIONS = [
    "Artificer",
    "Barbarian",
    "Bard",
    "Cleric",
    "Druid",
    "Fighter",
    "Monk",
    "Paladin",
    "Ranger",
    "Rogue",
    "Sorcerer",
    "Warlock",
    "Wizard",
]
CONDITION_OPTIONS = [
    "Blinded",
    "Charmed",
    "Deafened",
    "Frightened",
    "Grappled",
    "Incapacitated",
    "Invisible",
    "Paralyzed",
    "Petrified",
    "Poisoned",
    "Prone",
    "Restrained",
    "Stunned",
    "Unconscious",
    "Exhaustion",
]
CONDITION_COLOR_VALUES = {
    "Blinded": (0.96, 0.78, 0.28),
    "Charmed": (0.95, 0.45, 0.78),
    "Deafened": (0.56, 0.74, 0.96),
    "Frightened": (1.0, 0.48, 0.36),
    "Grappled": (0.64, 0.86, 0.42),
    "Incapacitated": (0.78, 0.62, 0.94),
    "Invisible": (0.52, 0.88, 0.86),
    "Paralyzed": (0.99, 0.64, 0.28),
    "Petrified": (0.70, 0.72, 0.74),
    "Poisoned": (0.38, 0.82, 0.48),
    "Prone": (0.86, 0.70, 0.46),
    "Restrained": (0.48, 0.68, 0.96),
    "Stunned": (1.0, 0.86, 0.32),
    "Unconscious": (0.80, 0.50, 0.55),
    "Exhaustion": (0.62, 0.58, 0.50),
}
CLASS_ICONS = {
    "Artificer": "◇",
    "Barbarian": "◈",
    "Bard": "♪",
    "Cleric": "✚",
    "Druid": "◌",
    "Fighter": "⚔",
    "Monk": "◍",
    "Paladin": "✦",
    "Ranger": "⌖",
    "Rogue": "◒",
    "Sorcerer": "✹",
    "Warlock": "☾",
    "Wizard": "✧",
}
MONSTER_ICON = "☠"
CLASS_ICON_FILES = {
    class_name: f"{class_name.lower()}.png"
    for class_name in CLASS_OPTIONS
}
MONSTER_ICON_FILE = "monster.png"
ICON_IMAGE_CACHE: dict[str, Any] = {}
