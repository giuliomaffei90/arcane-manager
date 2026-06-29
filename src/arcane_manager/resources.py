from __future__ import annotations

from .platform import Any, Path, sys


def resource_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    package_dir = Path(__file__).resolve().parent
    for candidate in (package_dir.parents[1], package_dir.parent, package_dir):
        if (candidate / "dataset" / "spells.json").exists() or (candidate / "resources").exists():
            return candidate
    return package_dir.parents[1]


def bundled_resource_path(name: str) -> Path:
    direct_path = BASE_DIR / name
    if direct_path.exists():
        return direct_path
    return BASE_DIR / "resources" / name


BASE_DIR = resource_base_dir()
DEFAULT_SPELLS_FILE = bundled_resource_path("dataset/spells.json")
DEFAULT_BESTIARY_FILE = bundled_resource_path("dataset/bestiary.json")
DEFAULT_ITEMS_FILE = bundled_resource_path("dataset/items.json")
DEFAULT_DICE_ROLLER_HTML = bundled_resource_path("assets/dice_roller/index.html")
DEFAULT_ICON_DIR = bundled_resource_path("assets/icons")
LOG_FILE = Path.home() / "Library" / "Logs" / "Arcane Manager" / "arcane_manager.log"
APP_RETAINED_OBJECTS: list[Any] = []
MAX_SPELL_FILE_BYTES = 12 * 1024 * 1024
MAX_ITEM_FILE_BYTES = 12 * 1024 * 1024
MAX_SPELLS = 2500
MAX_ITEMS = 3000
MAX_TEXT_FIELD_CHARS = 50000
MAX_SHORT_FIELD_CHARS = 500
MAX_ALIAS_CHARS = 140
MAX_ALIASES_PER_SPELL = 80
