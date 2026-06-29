#!/usr/bin/env python3
"""Build Arcane Manager's bundled item JSON from 5etools item data."""

from __future__ import annotations

import copy
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "ebd1827660ee61d1a59227d5979a137494dce1c8"
BASE_URL = f"https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/{SOURCE_COMMIT}/data"
ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "items.json"
REPORT_FILE = ROOT_DIR / "reports" / "5etools_items_import.json"
ITEM_DESCRIPTION_TODO_FILE = ROOT_DIR / "reports" / "items_description_todo.md"

EXCLUDED_SOURCES = {"XPHB", "XDMG", "FRHoF", "EFA"}
EXCLUDED_AGES = {"modern", "futuristic"}
SOURCE_CUTOFF = "2024-01-01"

TAG_RE = re.compile(r"\{@([a-zA-Z][a-zA-Z0-9]*)\s*([^{}]*?)?\}")
NOTE_RE = re.compile(r"\{@note\s+[^{}]*?\}")
ENTRY_REF_RE = re.compile(r"\{#itemEntry\s+([^|{}]+)\|([^{}]+)\}")
TEMPLATE_RE = re.compile(r"\{\{([^{}]+)\}\}")
VAR_RE = re.compile(r"\{=([a-zA-Z][a-zA-Z0-9]*)\}")

DAMAGE_TYPES = {
    "A": "acid",
    "B": "bludgeoning",
    "C": "cold",
    "F": "fire",
    "N": "necrotic",
    "O": "force",
    "P": "piercing",
    "I": "poison",
    "Y": "psychic",
    "R": "radiant",
    "S": "slashing",
    "L": "lightning",
    "T": "thunder",
}

ARMOR_TYPES = {
    "LA": "Light Armor",
    "MA": "Medium Armor",
    "HA": "Heavy Armor",
    "S": "Shield",
}

GENERIC_ITEM_TYPES = {"", "Other", "Unknown", "Unknown (Magic)"}

CANONICAL_ITEM_REPLACEMENTS = {
    "Padded": "Padded Armor",
    "Leather": "Leather Armor",
    "Studded Leather": "Studded Leather Armor",
    "Hide": "Hide Armor",
    "Half Plate": "Half Plate Armor",
    "Splint": "Splint Armor",
    "Plate": "Plate Armor",
    "Clothes, Common": "Common Clothes",
    "Clothes, Costume": "Costume Clothes",
    "Clothes, Fine": "Fine Clothes",
    "Clothes, Traveler's": "Traveler's Clothes",
    "Bottle, Glass": "Glass Bottle",
    "Lantern, Bullseye": "Bullseye Lantern",
    "Lantern, Hooded": "Hooded Lantern",
    "Case, Map or Scroll": "Map or Scroll Case",
    "Scale, Merchant's": "Merchant's Scale",
    "Pick, Miner's": "Miner's Pick",
    "Ram, Portable": "Portable Ram",
    "Tent, two-person": "Two-Person Tent",
    "Hammer, Sledge": "Sledgehammer",
    "Spikes, Iron (10)": "Iron Spikes (10)",
    "Blue Quartz Gem": "Blue Quartz",
    "Ink (1-ounce bottle)": "Ink Bottle",
    "Staff": "Wooden Staff",
}

CANONICAL_MERGE_FIELDS = ("description", "properties", "source", "source_abbreviation", "source_page")

OBVIOUS_ITEM_DESCRIPTIONS = {
    "Abacus": "An abacus is a counting frame used for arithmetic and record keeping.",
    "Airship": "An airship is a flying vehicle used to transport passengers and cargo.",
    "Ale (gallon)": "A gallon of ale is a common alcoholic drink served from a cask or jug.",
    "Ale (mug)": "A mug of ale is a common serving of alcoholic drink.",
    "Amulet": "An amulet is a spellcasting focus worn or carried to channel magical power.",
    "Arrow": "An arrow is ammunition used with a bow.",
    "Arrows (20)": "A bundle of arrows used as ammunition for bows.",
    "Ball of String": "A ball of string is a small coil of cord used for tying, marking, or simple repairs.",
    "Bandage": "A bandage is a strip of cloth used to bind or cover a wound.",
    "Bedroll": "A bedroll is portable bedding used for resting while traveling.",
    "Bell": "A bell is a small metal instrument that rings when struck or shaken.",
    "Bit and bridle": "A bit and bridle are tack used to guide and control a mount.",
    "Blanket": "A blanket is a warm covering used for sleeping or travel.",
    "Blowgun Needle": "A blowgun needle is ammunition used with a blowgun.",
    "Blowgun Needles (50)": "A bundle of blowgun needles used as ammunition for a blowgun.",
    "Camel": "A camel is a desert-ready mount used for travel and carrying gear.",
    "Carriage": "A carriage is a wheeled vehicle used to transport passengers.",
    "Cart": "A cart is a simple wheeled vehicle used to haul goods.",
    "Chalk (1 piece)": "A piece of chalk is used for marking stone, wood, or other surfaces.",
    "Chunk of Meat": "A chunk of meat is a simple portion of food.",
    "Crystal": "A crystal is a spellcasting focus used to channel magical power.",
    "Druidic Focus": "A druidic focus is a natural or crafted focus used to channel druidic magic.",
    "Emblem": "An emblem is a spellcasting focus that bears a sacred or symbolic mark.",
    "Feed (per day)": "Feed is grain or fodder used to sustain a mount or pack animal for a day.",
    "Flail": "A flail is a melee weapon with a striking head attached to a handle by a chain or hinge.",
    "Grappling Hook": "A grappling hook is a hooked tool used with rope for climbing or securing a line.",
    "Hammer": "A hammer is a hand tool used for driving nails, breaking objects, or simple repairs.",
    "Hammer, Sledge": "A sledgehammer is a heavy hammer used for forceful work such as breaking stone or wood.",
    "Hourglass": "An hourglass is a glass timekeeper that measures time with falling sand.",
    "Ink (1-ounce bottle)": "A bottle of ink is used for writing, drawing, or copying text.",
    "Ink Pen": "An ink pen is a writing tool used with ink.",
    "Iron Spike": "An iron spike is a metal peg used for climbing, securing gear, or wedging objects.",
    "Iron Spikes (10)": "A bundle of iron spikes used for climbing, securing gear, or wedging objects.",
    "Lockpicks": "Lockpicks are small tools used to manipulate locks.",
    "Mace": "A mace is a blunt melee weapon with a heavy head and sturdy handle.",
    "Miner's Pick": "A miner's pick is a sturdy tool used for breaking stone or packed earth.",
    "Morningstar": "A morningstar is a melee weapon with a spiked head fixed to a handle.",
    "Orb": "An orb is a spellcasting focus used to channel magical power.",
    "Pack Saddle": "A pack saddle is tack fitted to a mount for carrying supplies or cargo.",
    "Paper (one sheet)": "A sheet of paper is used for writing, drawing, or copying text.",
    "Parchment (one sheet)": "A sheet of parchment is used for writing, maps, or records.",
    "Perfume (vial)": "A vial of perfume contains a scented liquid used as a fragrance.",
    "Pick, Miner's": "A miner's pick is a sturdy tool used for breaking stone or packed earth.",
    "Piton": "A piton is a metal spike used to anchor rope while climbing.",
    "Pole (10-foot)": "A ten-foot pole is a long wooden pole used for probing, reaching, or carrying objects.",
    "Reliquary": "A reliquary is a spellcasting focus that holds or represents a sacred relic.",
    "Renaissance Bullet": "A renaissance bullet is ammunition used with a firearm.",
    "Renaissance Bullets (10)": "A bundle of renaissance bullets used as ammunition for firearms.",
    "Riding Saddle": "A riding saddle is tack fitted to a mount for a rider.",
    "Robes": "Robes are loose garments worn as everyday or ceremonial clothing.",
    "Rod": "A rod is a spellcasting focus used to channel magical power.",
    "Saddlebags": "Saddlebags are paired bags attached to a saddle for carrying supplies.",
    "Scroll Case": "A scroll case is a small protective container for scrolls, maps, or papers.",
    "Sealing Wax": "Sealing wax is used to seal letters, scrolls, or containers with an impressed mark.",
    "Shovel": "A shovel is a hand tool used for digging or moving loose material.",
    "Signal Whistle": "A signal whistle is a small whistle used to make a sharp audible signal.",
    "Signet Ring": "A signet ring bears a personal mark used to stamp seals or identify its owner.",
    "Skyship": "A skyship is a flying vessel used to transport passengers and cargo through the air.",
    "Sled": "A sled is a vehicle used to haul passengers or cargo over snow or ice.",
    "Sledgehammer": "A sledgehammer is a heavy hammer used for forceful work such as breaking stone or wood.",
    "Sling Bullet": "A sling bullet is ammunition used with a sling.",
    "Sling Bullets (20)": "A bundle of sling bullets used as ammunition for a sling.",
    "Soap": "Soap is used for washing and cleaning.",
    "Spikes, Iron (10)": "A bundle of iron spikes used for climbing, securing gear, or wedging objects.",
    "Sprig of Mistletoe": "A sprig of mistletoe is a spellcasting focus used to channel druidic magic.",
    "Stabling (per day)": "Stabling provides shelter and care for a mount or pack animal for a day.",
    "Steel Mirror": "A steel mirror is a polished metal mirror used for grooming, signaling, or inspection.",
    "Totem": "A totem is a spellcasting focus used to channel druidic magic.",
    "Wagon": "A wagon is a sturdy wheeled vehicle used to haul passengers or cargo.",
    "Wand": "A wand is a spellcasting focus used to channel magical power.",
    "War Pick": "A war pick is a melee weapon with a pointed head designed to pierce armor.",
    "Whetstone": "A whetstone is used to sharpen blades and tools.",
    "Yew Wand": "A yew wand is a spellcasting focus used to channel magical power.",
}


def fetch_text(path: str) -> str:
    url = f"{BASE_URL}/{path}"
    return subprocess.check_output(["curl", "-fsSL", url], text=True, timeout=120)


def fetch_json(path: str) -> Any:
    return json.loads(fetch_text(path))


def normalize_key(text: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(text).lower())).strip()


def item_id(name: str) -> str:
    return normalize_key(name).replace(" ", "-")


def clean_name(text: Any) -> str:
    return clean_text(re.sub(r"\s+\(\*\)$", "", str(text if text is not None else "")))


def clean_text(text: Any) -> str:
    value = str(text if text is not None else "")
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" ?\n ?", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def source_metadata() -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for file_name, prop in (("books.json", "book"), ("adventures.json", "adventure")):
        payload = fetch_json(file_name)
        for item in payload.get(prop, []):
            source = item.get("source") or item.get("id")
            if not source:
                continue
            metadata[source] = {
                "name": item.get("name", source),
                "published": item.get("published", ""),
                "group": item.get("group", ""),
            }
    return metadata


def split_source_code(value: Any) -> tuple[str, str]:
    text = str(value or "")
    if "|" not in text:
        return text, ""
    code, source = text.split("|", 1)
    return code, source


def type_code(raw_type: Any) -> str:
    return split_source_code(raw_type)[0]


def source_from_type(raw_type: Any) -> str:
    return split_source_code(raw_type)[1]


def source_for(raw: dict[str, Any]) -> str:
    return str(raw.get("source") or raw.get("inherits", {}).get("source") or source_from_type(raw.get("type")) or "")


def source_name(source: str, metadata: dict[str, dict[str, str]]) -> str:
    return metadata.get(source, {}).get("name") or source


def is_allowed_source(source: str, metadata: dict[str, dict[str, str]]) -> bool:
    if source in EXCLUDED_SOURCES:
        return False
    published = metadata.get(source, {}).get("published", "")
    return bool(published) and published < SOURCE_CUTOFF


def is_excluded_age(raw: dict[str, Any]) -> bool:
    return str(raw.get("age") or raw.get("inherits", {}).get("age") or "").lower() in EXCLUDED_AGES


def is_allowed_record(raw: dict[str, Any], metadata: dict[str, dict[str, str]]) -> bool:
    return is_allowed_source(source_for(raw), metadata) and not is_excluded_age(raw)


def ref_name(value: str) -> str:
    return clean_text(value.split("|", 1)[0])


def tag_text(tag: str, payload: str | None) -> str:
    raw = (payload or "").strip()
    parts = raw.split("|") if raw else []
    first = parts[0] if parts else ""
    display = parts[2] if len(parts) >= 3 and parts[2] else first
    tag = tag.lower()

    if tag in {"damage", "dice", "scaledice", "scaledamage", "chance", "d20"}:
        return first
    if tag == "hit":
        value = first.strip()
        return value if value.startswith(("+", "-")) else f"+{value}" if value else ""
    if tag == "dc":
        return f"DC {first}" if first else ""
    if tag == "recharge":
        return f"(Recharge {first}-6)" if first else "(Recharge 6)"
    if tag in {"item", "spell", "condition", "status", "creature", "sense", "skill", "action", "hazard", "feat"}:
        return display
    if tag in {"book", "adventure", "filter", "quickref", "table", "variantrule"}:
        return display
    if tag in {"hom", "i", "b", "u", "sup", "sub"}:
        return raw
    if tag == "note":
        return ""
    return display or first or raw


def context_value(name: str, context: dict[str, Any]) -> str:
    value = context.get(name, "")
    if isinstance(value, list):
        return ", ".join(clean_text(item) for item in value)
    return clean_text(value)


def render_template(text: Any, context: dict[str, Any]) -> str:
    rendered = str(text)
    rendered = VAR_RE.sub(lambda match: context_value(match.group(1), context), rendered)

    def replace_template(match: re.Match[str]) -> str:
        expr = match.group(1).strip()
        if expr.startswith("item."):
            return context_value(expr[5:], context)
        if expr.startswith("getFullImmRes item."):
            return context_value(expr[len("getFullImmRes item.") :], context)
        return ""

    return TEMPLATE_RE.sub(replace_template, rendered)


def render_tags(text: Any, context: dict[str, Any] | None = None) -> str:
    if text is None:
        return ""
    rendered = render_template(text, context or {})
    for _ in range(4):
        previous = rendered
        rendered = NOTE_RE.sub("", rendered)
        rendered = TAG_RE.sub(lambda match: tag_text(match.group(1), match.group(2)), rendered)
        if rendered == previous:
            break
    return clean_text(rendered)


def render_entry(entry: Any, context: dict[str, Any], item_entries: dict[tuple[str, str], Any]) -> str:
    if entry is None:
        return ""
    if isinstance(entry, str):
        def replace_entry_ref(match: re.Match[str]) -> str:
            key = (normalize_key(match.group(1)), match.group(2).upper())
            template = item_entries.get(key)
            return render_entry(template, context, item_entries) if template is not None else ""

        return render_tags(ENTRY_REF_RE.sub(replace_entry_ref, entry), context)
    if isinstance(entry, (int, float)):
        return str(entry)
    if isinstance(entry, list):
        return clean_text("\n\n".join(part for part in (render_entry(item, context, item_entries) for item in entry) if part))
    if not isinstance(entry, dict):
        return render_tags(entry, context)

    entry_type = entry.get("type")
    name = render_tags(entry.get("name", ""), context)
    if "entriesTemplate" in entry:
        return render_entry(entry.get("entriesTemplate"), context, item_entries)
    if entry_type == "list":
        items = [render_entry(item, context, item_entries) for item in entry.get("items", [])]
        return clean_text("\n".join(f"- {item}" for item in items if item))
    if entry_type == "table":
        lines = [name] if name else []
        labels = entry.get("colLabels", [])
        if isinstance(labels, list) and labels:
            lines.append(" | ".join(render_tags(label, context) for label in labels))
        for row in entry.get("rows", []):
            if isinstance(row, list):
                lines.append(" | ".join(render_entry(cell, context, item_entries) for cell in row))
            else:
                lines.append(render_entry(row, context, item_entries))
        return clean_text("\n".join(line for line in lines if line))
    if entry_type == "item":
        body = render_entry(entry.get("entry") or entry.get("entries", []), context, item_entries)
        return clean_text(f"{name}. {body}" if name and body else name or body)
    if entry_type in {"entries", "inset", "quote", "section"}:
        body = render_entry(entry.get("entries", []), context, item_entries)
        return clean_text(f"{name}. {body}" if name and body else name or body)

    parts = []
    if "entries" in entry:
        parts.append(render_entry(entry.get("entries"), context, item_entries))
    if "entry" in entry:
        parts.append(render_entry(entry.get("entry"), context, item_entries))
    body = clean_text("\n".join(part for part in parts if part))
    return clean_text(f"{name}. {body}" if name and body else name or body)


def money_text(copper: Any) -> str:
    if copper in (None, ""):
        return ""
    try:
        value = int(copper)
    except (TypeError, ValueError):
        return clean_text(copper)
    if value <= 0:
        return "0 Copper"
    gold, remainder = divmod(value, 100)
    silver, copper_value = divmod(remainder, 10)
    parts = []
    if gold:
        parts.append(f"{gold} Gold")
    if silver:
        parts.append(f"{silver} Silver")
    if copper_value or not parts:
        parts.append(f"{copper_value} Copper")
    return " ".join(parts)


def item_type_name(raw: dict[str, Any], item_types: dict[tuple[str, str], str]) -> str:
    code = type_code(raw.get("type"))
    return item_types.get((code, source_from_type(raw.get("type"))), "") or item_types.get((code, ""), "")


def base_item_category(raw: dict[str, Any]) -> str:
    code = type_code(raw.get("type"))
    if raw.get("poison") or code in {"PS"}:
        return "Poisons"
    if raw.get("weapon") or raw.get("weaponCategory") or code in {"M", "R", "A", "AF"}:
        return "Weapon"
    if raw.get("armor") or code in ARMOR_TYPES:
        return "Armor"
    if code in {"AT", "INS", "GS", "T"}:
        return "Tools"
    rarity = str(raw.get("rarity") or "").lower()
    if raw.get("wondrous") or raw.get("tattoo") or (rarity and rarity not in {"none", "unknown", "unknown (magic)"}):
        return "Wondrous Item"
    if code in {"P", "EXP", "SC", "SCF", "G"}:
        return "Adventuring Gear"
    return "Other"


def item_category(raw: dict[str, Any], item_types: dict[tuple[str, str], str]) -> str:
    category = base_item_category(raw)
    type_name = item_type_name(raw, item_types)
    if category == "Other" and type_name and type_name not in GENERIC_ITEM_TYPES:
        return type_name
    return category


def item_rarity(raw: dict[str, Any]) -> str:
    rarity = clean_text(raw.get("rarity", ""))
    return rarity.title() if rarity and rarity.lower() != "none" else ""


def item_classification(raw: dict[str, Any], item_types: dict[tuple[str, str], str], category: str) -> str:
    code = type_code(raw.get("type"))
    if code in ARMOR_TYPES:
        return ARMOR_TYPES[code]
    if raw.get("weaponCategory"):
        direction = "Ranged" if code in {"R", "A", "AF"} else "Melee"
        return f"{str(raw.get('weaponCategory')).title()} {direction} Weapons"
    type_name = item_type_name(raw, item_types)
    if type_name and type_name not in GENERIC_ITEM_TYPES and normalize_key(type_name) != normalize_key(category):
        return type_name
    return ""


def item_damage(raw: dict[str, Any]) -> str:
    damage = clean_text(raw.get("dmg1", ""))
    if not damage:
        return ""
    damage_type = DAMAGE_TYPES.get(str(raw.get("dmgType", "")), clean_text(raw.get("dmgType", "")))
    return clean_text(f"{damage} {damage_type}" if damage_type else damage)


def item_ac(raw: dict[str, Any]) -> str:
    ac = raw.get("ac")
    bonus = clean_text(raw.get("bonusAc", ""))
    if ac in (None, ""):
        return bonus
    try:
        if bonus.startswith(("+", "-")):
            return str(int(ac) + int(bonus))
    except (TypeError, ValueError):
        pass
    return clean_text(ac)


def item_properties(raw: dict[str, Any], item_properties_by_key: dict[tuple[str, str], str]) -> str:
    parts = []
    for prop in raw.get("property", []) or []:
        code, prop_source = split_source_code(prop)
        name = item_properties_by_key.get((code, prop_source), "") or item_properties_by_key.get((code, ""), "") or code
        if code == "V" and raw.get("dmg2"):
            name = f"{name} ({raw.get('dmg2')})"
        if name and name not in parts:
            parts.append(name)
    if raw.get("reqAttune"):
        attune = raw.get("reqAttune")
        parts.append("Requires Attunement" if attune is True else f"Requires Attunement {render_tags(attune)}")
    if raw.get("range"):
        parts.append(f"Range {raw.get('range')} ft.")
    if raw.get("weight") not in (None, ""):
        parts.append(f"Weight {raw.get('weight')} lb.")
    return ", ".join(parts)


def lookup_by_code(
    mapping: dict[tuple[str, str], Any],
    code: str,
    source: str,
) -> Any:
    return mapping.get((code, source)) or mapping.get((code, "")) or mapping.get((code, "PHB"))


def item_description(
    raw: dict[str, Any],
    item_entries: dict[tuple[str, str], Any],
    item_type_entries: dict[tuple[str, str], Any],
    item_property_entries: dict[tuple[str, str], Any],
) -> str:
    parts = []
    if raw.get("entries"):
        parts.append(render_entry(raw.get("entries"), raw, item_entries))
    if raw.get("additionalEntries"):
        parts.append(render_entry(raw.get("additionalEntries"), raw, item_entries))
    code = type_code(raw.get("type"))
    type_entries = lookup_by_code(item_type_entries, code, source_from_type(raw.get("type")))
    if type_entries:
        parts.append(render_entry(type_entries, raw, item_entries))
    for prop in raw.get("property", []) or []:
        prop_code, prop_source = split_source_code(prop)
        prop_entries = lookup_by_code(item_property_entries, prop_code, prop_source)
        if prop_entries:
            rendered = render_entry(prop_entries, raw, item_entries)
            if rendered and rendered not in parts:
                parts.append(rendered)
    return clean_text("\n\n".join(part for part in parts if part))


def public_record(
    raw: dict[str, Any],
    metadata: dict[str, dict[str, str]],
    item_types: dict[tuple[str, str], str],
    item_properties_by_key: dict[tuple[str, str], str],
    item_entries: dict[tuple[str, str], Any],
    item_type_entries: dict[tuple[str, str], Any],
    item_property_entries: dict[tuple[str, str], Any],
) -> dict[str, Any]:
    source = source_for(raw)
    category = item_category(raw, item_types)
    record = {
        "id": item_id(clean_name(raw.get("name", ""))),
        "name": clean_name(raw.get("name", "")),
        "category": category,
        "description": item_description(raw, item_entries, item_type_entries, item_property_entries),
        "cost": money_text(raw.get("value")),
        "source": source_name(source, metadata),
        "source_abbreviation": source,
        "source_commit": SOURCE_COMMIT,
    }
    if raw.get("page"):
        record["source_page"] = int(raw.get("page") or 0)
    ac = item_ac(raw)
    if ac:
        record["ac"] = ac
    damage = item_damage(raw)
    if damage:
        record["damage"] = damage
    rarity = item_rarity(raw)
    if rarity:
        record["rarity"] = rarity
    classification = item_classification(raw, item_types, category)
    if classification:
        record["classification"] = classification
    properties = item_properties(raw, item_properties_by_key)
    if properties:
        record["properties"] = properties
    return {key: value for key, value in record.items() if value not in ("", [], None)}


def index_by_name_source(items: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(normalize_key(item.get("name", "")), source_for(item).upper()): item for item in items if item.get("name")}


def resolve_copies(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = index_by_name_source(items)
    resolved = []
    for item in items:
        copy_spec = item.get("_copy")
        if not isinstance(copy_spec, dict):
            resolved.append(dict(item))
            continue
        base = index.get((normalize_key(copy_spec.get("name", "")), str(copy_spec.get("source", "")).upper()))
        if not base:
            resolved.append(dict(item))
            continue
        merged = copy.deepcopy(base)
        for key, value in item.items():
            if key != "_copy":
                merged[key] = value
        resolved.append(merged)
    return resolved


def load_local_items() -> list[dict[str, Any]]:
    refs = []
    try:
        base_ref = subprocess.check_output(["git", "merge-base", "HEAD", "main"], cwd=ROOT_DIR, text=True).strip()
        if base_ref:
            refs.append(base_ref)
    except Exception:
        pass
    refs.extend(["main", "HEAD"])
    payload = None
    for ref in refs:
        try:
            raw = subprocess.check_output(["git", "show", f"{ref}:items.json"], cwd=ROOT_DIR, text=True)
            payload = json.loads(raw)
            break
        except Exception:
            continue
    if payload is None:
        payload = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    local_items = payload.get("items", payload) if isinstance(payload, dict) else payload
    return [item for item in local_items if isinstance(item, dict)]


def local_name_keys(name: Any) -> set[str]:
    keys = {normalize_key(name)}
    text = str(name or "")
    if "," in text:
        _prefix, suffix = text.split(",", 1)
        suffix_key = normalize_key(suffix)
        if suffix_key:
            keys.add(suffix_key)
    return {key for key in keys if key}


def requirement_matches(raw: dict[str, Any], requirement: dict[str, Any]) -> bool:
    for key, expected in requirement.items():
        if key == "type":
            if type_code(raw.get("type")) != type_code(expected):
                return False
        elif key == "source":
            if source_for(raw).lower() != str(expected).lower():
                return False
        elif key == "name":
            if normalize_key(raw.get("name", "")) != normalize_key(expected):
                return False
        elif key == "weapon":
            if not (raw.get("weapon") or raw.get("weaponCategory") or type_code(raw.get("type")) in {"M", "R", "A", "AF"}):
                return False
        elif key == "armor":
            if not (raw.get("armor") or type_code(raw.get("type")) in ARMOR_TYPES):
                return False
        elif key in {"sword", "bow", "axe", "arrow", "bolt", "polearm", "crossbow", "spear", "net"}:
            if not (raw.get("weapon") or raw.get("weaponCategory") or type_code(raw.get("type")) in {"M", "R", "A", "AF"}):
                return False
            if bool(expected) and key not in normalize_key(raw.get("name", "")).split():
                if key == "sword" and "sword" in normalize_key(raw.get("name", "")):
                    continue
                return False
        elif key == "property":
            properties = {type_code(prop) for prop in raw.get("property", []) or []}
            if type_code(expected) not in properties:
                return False
        elif key == "weaponCategory":
            if str(raw.get("weaponCategory", "")).lower() != str(expected).lower():
                return False
        elif key == "dmgType":
            if str(raw.get("dmgType", "")).lower() != str(expected).lower():
                return False
    return True


def variant_matches(raw: dict[str, Any], variant: dict[str, Any]) -> bool:
    inherits = variant.get("inherits", {})
    if inherits.get("source") != "DMG":
        return False
    if inherits.get("namePrefix") not in {"+1 ", "+2 ", "+3 "}:
        return False
    if variant.get("name") not in {"+1 Weapon", "+2 Weapon", "+3 Weapon", "+1 Armor", "+2 Armor", "+3 Armor", "+1 Shield (*)", "+2 Shield (*)", "+3 Shield (*)", "+1 Ammunition", "+2 Ammunition", "+3 Ammunition"}:
        return False
    requirements = variant.get("requires", []) or []
    if requirements and not any(requirement_matches(raw, req) for req in requirements if isinstance(req, dict)):
        return False
    excludes = variant.get("excludes")
    if isinstance(excludes, dict) and requirement_matches(raw, excludes):
        return False
    return True


def apply_magic_variant(raw: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    inherits = copy.deepcopy(variant.get("inherits", {}))
    merged = copy.deepcopy(raw)
    for key, value in inherits.items():
        if key not in {"namePrefix", "nameSuffix"}:
            merged[key] = value
    name = clean_name(raw.get("name", ""))
    merged["name"] = clean_name(f"{inherits.get('namePrefix', '')}{name}{inherits.get('nameSuffix', '')}")
    if variant.get("entries") and not merged.get("entries"):
        merged["entries"] = variant.get("entries")
    return merged


def add_unique_variant(record: dict[str, Any], variant_record: dict[str, Any]) -> bool:
    variants = record.setdefault("variants", [])
    variant_name = normalize_key(variant_record.get("name", ""))
    if not variant_name or variant_name == normalize_key(record.get("name", "")):
        return False
    if any(normalize_key(item.get("name", "")) == variant_name for item in variants):
        return False
    variants.append(variant_record)
    return True


NUMERIC_VARIANT_RE = re.compile(r"^\+(1|2|3)\s+(.+)$")


def group_numeric_variants(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    by_name = {normalize_key(record.get("name", "")): record for record in records}
    variant_records: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        match = NUMERIC_VARIANT_RE.match(str(record.get("name", "")))
        if not match:
            continue
        base_name = match.group(2)
        variant_records.setdefault(normalize_key(base_name), []).append(record)

    grouped_variant_ids: set[int] = set()
    groups_created = 0
    for base_key, variants in variant_records.items():
        if len(variants) < 2:
            continue
        base = by_name.get(base_key)
        if base is None:
            base = copy.deepcopy(sorted(variants, key=lambda item: normalize_key(item.get("name", "")))[0])
            base["name"] = re.sub(r"^\+[123]\s+", "", str(base.get("name", "")))
            base["id"] = item_id(base["name"])
            base.pop("variants", None)
            base["variant_only"] = True
            base.setdefault("description", "")
            records.append(base)
            by_name[base_key] = base
        added_any = False
        for variant in sorted(variants, key=lambda item: normalize_key(item.get("name", ""))):
            grouped_variant_ids.add(id(variant))
            if add_unique_variant(base, variant):
                added_any = True
        if added_any or variants:
            groups_created += 1

    grouped = [record for record in records if id(record) not in grouped_variant_ids]
    return grouped, groups_created


def inferred_item_description(record: dict[str, Any]) -> str:
    name = str(record.get("name") or "")
    category = str(record.get("category") or "")
    classification = str(record.get("classification") or "")
    if name in OBVIOUS_ITEM_DESCRIPTIONS:
        return OBVIOUS_ITEM_DESCRIPTIONS[name]
    if name.startswith("Coins - "):
        coin = name.removeprefix("Coins - ").lower()
        article = "An" if coin[:1] in {"a", "e", "i", "o", "u"} else "A"
        return f"{article} {coin} coin used as common currency."
    if "Clothes" in name:
        if "Costume" in name:
            return "Costume clothes are garments designed for disguise, performance, or display."
        if "Fine" in name:
            return "Fine clothes are well-made garments suited for formal or wealthy settings."
        if "Traveler" in name:
            return "Traveler's clothes are durable garments suited for road and wilderness travel."
        if "Common" in name:
            return "Common clothes are plain everyday garments."
    if category == "Mount" and name:
        return f"A {name.lower()} is a mount or pack animal used for travel and carrying gear."
    if category.startswith("Vehicle") and name:
        return f"A {name.lower()} is a vehicle used to transport passengers or cargo."
    if category == "Food and Drink" and name:
        return f"{name} is a simple food or drink item."
    if category == "Tack and Harness" and name:
        return f"{name} is tack or stable gear used with mounts and pack animals."
    if classification == "Ammunition" and name:
        return f"{name} is ammunition used with an appropriate weapon."
    if classification == "Spellcasting Focus" and name:
        return f"A {name.lower()} is a spellcasting focus used to channel magical power."
    return ""


def fill_obvious_item_descriptions(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    todo_rows = []
    for record in records:
        if str(record.get("description") or "").strip():
            continue
        description = inferred_item_description(record)
        if description:
            record["description"] = description
            continue
        name = str(record.get("name") or "")
        todo_rows.append(
            {
                "Name": name,
                "Category": str(record.get("category") or ""),
                "Classification": str(record.get("classification") or ""),
                "Cost": str(record.get("cost") or ""),
                "Properties": str(record.get("properties") or ""),
                "Reason": "ambiguous exalted variant" if "(Exalted)" in name else "needs manual description",
            }
        )
    return todo_rows


def write_item_description_todo(rows: list[dict[str, str]]) -> None:
    def escape_cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    lines = [
        "# Item Description TODO",
        "",
        "Items below still need a manual description because the name/category was not obvious enough for a safe one-line fallback.",
        "",
        "| Name | Category | Classification | Cost | Properties | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in sorted(rows, key=lambda item: item["Name"].lower()):
        lines.append("| " + " | ".join(escape_cell(row[key]) for key in ("Name", "Category", "Classification", "Cost", "Properties", "Reason")) + " |")
    ITEM_DESCRIPTION_TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    ITEM_DESCRIPTION_TODO_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_canonical_item_replacements(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    by_name = {str(record.get("name") or ""): record for record in records}
    removed_names = []
    for remove_name, keep_name in CANONICAL_ITEM_REPLACEMENTS.items():
        remove_record = by_name.get(remove_name)
        keep_record = by_name.get(keep_name)
        if remove_record is None or keep_record is None:
            continue
        for field in CANONICAL_MERGE_FIELDS:
            if keep_record.get(field) in ("", [], None) and remove_record.get(field) not in ("", [], None):
                keep_record[field] = remove_record[field]
        removed_names.append(remove_name)
    removed_set = set(removed_names)
    return [record for record in records if record.get("name") not in removed_set], removed_names


def main() -> None:
    metadata = source_metadata()
    base_payload = fetch_json("items-base.json")
    items_payload = fetch_json("items.json")
    variants_payload = fetch_json("magicvariants.json")

    item_types = {}
    item_type_entries = {}
    for item_type in base_payload.get("itemType", []):
        code = item_type.get("abbreviation", "")
        source = item_type.get("source", "")
        item_types[(code, source)] = clean_text(item_type.get("name", ""))
        item_types.setdefault((code, ""), clean_text(item_type.get("name", "")))
        if item_type.get("entries"):
            item_type_entries[(code, source)] = item_type.get("entries")
            item_type_entries.setdefault((code, ""), item_type.get("entries"))

    item_properties_by_key = {}
    item_property_entries = {}
    for prop in base_payload.get("itemProperty", []):
        code = prop.get("abbreviation", "")
        source = prop.get("source", "")
        prop_entries = prop.get("entries", [])
        entry_name = ""
        if prop_entries and isinstance(prop_entries[0], dict):
            entry_name = clean_text(prop_entries[0].get("name", ""))
        name = clean_text(prop.get("name", "")) or entry_name or code
        item_properties_by_key[(code, source)] = name
        item_properties_by_key.setdefault((code, ""), name)
        if prop_entries:
            item_property_entries[(code, source)] = prop_entries
            item_property_entries.setdefault((code, ""), prop_entries)

    item_entries = {
        (normalize_key(entry.get("name", "")), str(entry.get("source", "")).upper()): entry.get("entriesTemplate") or entry.get("entries")
        for entry in base_payload.get("itemEntry", [])
    }

    raw_base_items = resolve_copies(base_payload.get("baseitem", []))
    raw_items = resolve_copies(items_payload.get("item", []))
    raw_remote_items = [item for item in raw_base_items + raw_items if is_allowed_record(item, metadata)]
    base_item_keys = {
        (normalize_key(item.get("name", "")), source_for(item).upper())
        for item in raw_base_items
        if is_allowed_record(item, metadata)
    }
    raw_by_ref = {
        (normalize_key(item.get("name", "")), source_for(item).upper()): item
        for item in raw_remote_items
        if item.get("name")
    }

    item_groups_read = sum(
        1
        for group in items_payload.get("itemGroup", [])
        if is_allowed_record(group, metadata) and group.get("items")
    )

    records: list[dict[str, Any]] = []
    raw_for_variants: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for raw in raw_remote_items:
        key = (normalize_key(raw.get("name", "")), source_for(raw).upper())
        record = public_record(raw, metadata, item_types, item_properties_by_key, item_entries, item_type_entries, item_property_entries)
        records.append(record)
        if key in base_item_keys:
            raw_for_variants.append((raw, record))

    magic_variants = [
        variant
        for variant in variants_payload.get("magicvariant", [])
        if is_allowed_record(variant.get("inherits", variant), metadata) and not is_excluded_age(variant)
    ]
    variant_count = 0
    for raw, record in raw_for_variants:
        if is_excluded_age(raw):
            continue
        for variant in magic_variants:
            if not variant_matches(raw, variant):
                continue
            variant_raw = apply_magic_variant(raw, variant)
            if is_excluded_age(variant_raw):
                continue
            variant_record = public_record(variant_raw, metadata, item_types, item_properties_by_key, item_entries, item_type_entries, item_property_entries)
            if add_unique_variant(record, variant_record):
                variant_count += 1

    duplicate_remote_names: list[str] = []
    deduped: dict[str, dict[str, Any]] = {}
    source_dates = {source_name(source, metadata): metadata.get(source, {}).get("published", "") for source in metadata}
    for record in records:
        key = normalize_key(record.get("name", ""))
        if not key:
            continue
        previous = deduped.get(key)
        if previous is not None:
            duplicate_remote_names.append(record.get("name", ""))
            previous_date = source_dates.get(previous.get("source", ""), "")
            current_date = source_dates.get(record.get("source", ""), "")
            if current_date >= previous_date:
                deduped[key] = record
        else:
            deduped[key] = record

    remote_records, numeric_variant_groups_created = group_numeric_variants(list(deduped.values()))
    remote_top_names = {normalize_key(item.get("name", "")) for item in remote_records}
    remote_variant_names = set()
    for item in remote_records:
        for variant in item.get("variants", []):
            remote_variant_names.add(normalize_key(variant.get("name", "")))
            remote_variant_names.add(normalize_key(f"{item.get('name', '')}, {variant.get('name', '')}"))

    local_items = load_local_items()
    local_kept = []
    local_replaced = []
    for item in local_items:
        if not isinstance(item, dict):
            continue
        keys = local_name_keys(item.get("name", ""))
        if keys & remote_top_names or keys & remote_variant_names:
            local_replaced.append(item.get("name", ""))
            continue
        local_kept.append(item)

    final_items = sorted(remote_records + local_kept, key=lambda item: normalize_key(item.get("name", "")))
    for item in final_items:
        if item.get("variants"):
            item["variants"] = sorted(item["variants"], key=lambda variant: normalize_key(variant.get("name", "")))
    final_items, canonical_removed_items = apply_canonical_item_replacements(final_items)
    item_description_todo_rows = fill_obvious_item_descriptions(final_items)
    write_item_description_todo(item_description_todo_rows)

    duplicate_ids = sorted(
        key
        for key, count in __import__("collections").Counter(item.get("id") for item in final_items).items()
        if key and count > 1
    )
    duplicate_names = sorted(
        key
        for key, count in __import__("collections").Counter(normalize_key(item.get("name", "")) for item in final_items).items()
        if key and count > 1
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "source": "5etools item data plus preserved local Arcane Manager items",
                "source_commit": SOURCE_COMMIT,
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "item_count": len(final_items),
                "items": final_items,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(
            {
                "source_commit": SOURCE_COMMIT,
                "remote_records_written": len(remote_records),
                "local_items_preserved": len(local_kept),
                "local_items_replaced_by_5etools": len(local_replaced),
                "final_item_count": len(final_items),
                "magic_variants_attached": variant_count,
                "numeric_variant_groups_created": numeric_variant_groups_created,
                "item_groups_read": item_groups_read,
                "item_groups_written": 0,
                "excluded_sources": sorted(EXCLUDED_SOURCES),
                "excluded_ages": sorted(EXCLUDED_AGES),
                "duplicate_remote_names_resolved": sorted(set(duplicate_remote_names)),
                "canonical_duplicates_removed": sorted(canonical_removed_items),
                "duplicate_ids": duplicate_ids,
                "duplicate_names": duplicate_names,
                "item_description_todo_count": len(item_description_todo_rows),
                "local_replaced_examples": sorted(local_replaced)[:80],
                "local_preserved_examples": [item.get("name", "") for item in local_kept[:80]],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(final_items)} items to {OUTPUT_FILE}")
    print(f"Attached {variant_count} magic variants and preserved {len(local_kept)} local-only items")
    if duplicate_ids or duplicate_names:
        raise SystemExit("Generated duplicate item ids or names; see report.")


if __name__ == "__main__":
    main()
