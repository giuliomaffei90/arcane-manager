#!/usr/bin/env python3
"""Build Arcane Manager's bundled spell JSON from 5etools spell data."""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "ebd1827660ee61d1a59227d5979a137494dce1c8"
BASE_URL = f"https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/{SOURCE_COMMIT}/data"
ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "spells.json"
REPORT_FILE = ROOT_DIR / "reports" / "5etools_spells_import.json"

EXCLUDED_SOURCES = {"XPHB", "FRHoF", "EFA"}
SOURCE_CUTOFF = "2024-01-01"

SCHOOL_NAMES = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "V": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
}
LEVEL_NAMES = {
    0: "Cantrip",
    1: "1st Level",
    2: "2nd Level",
    3: "3rd Level",
    4: "4th Level",
    5: "5th Level",
    6: "6th Level",
    7: "7th Level",
    8: "8th Level",
    9: "9th Level",
}
UNIT_NAMES = {
    "action": "action",
    "bonus": "bonus action",
    "reaction": "reaction",
    "minute": "minute",
    "hour": "hour",
}
DISTANCE_TYPES = {
    "self": "Self",
    "touch": "Touch",
    "sight": "Sight",
    "unlimited": "Unlimited",
    "unlimited_same_plane": "Unlimited on the same plane",
    "special": "Special",
}
MEDIA_KEYS = {
    "hasFluff",
    "hasFluffImages",
    "fluff",
    "images",
    "image",
    "soundClip",
}

TAG_RE = re.compile(r"\{@([a-zA-Z][a-zA-Z0-9]*)\s*([^{}]*?)?\}")
NOTE_RE = re.compile(r"\{@note\s+[^{}]*?\}")


def fetch_text(path: str) -> str:
    url = f"{BASE_URL}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return response.read().decode("utf-8")
    except Exception:
        return subprocess.check_output(["curl", "-fsSL", url], text=True, timeout=90)


def fetch_json(path: str) -> Any:
    return json.loads(fetch_text(path))


def normalize_key(text: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(text).lower())).strip()


def spell_id(name: str) -> str:
    return normalize_key(name).replace(" ", "-")


def clean_text(text: Any) -> str:
    value = str(text if text is not None else "")
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
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


def source_name(source: str, metadata: dict[str, dict[str, str]]) -> str:
    return metadata.get(source, {}).get("name") or source


def is_allowed_source(source: str, metadata: dict[str, dict[str, str]]) -> bool:
    if source in EXCLUDED_SOURCES:
        return False
    published = metadata.get(source, {}).get("published", "")
    return bool(published) and published < SOURCE_CUTOFF


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
    if tag == "note":
        return ""
    if tag in {"spell", "condition", "status", "creature", "item", "sense", "skill", "action", "hazard", "feat"}:
        return display
    if tag in {"book", "adventure", "filter", "quickref", "note", "variantrule"}:
        return display
    if tag in {"hom", "i", "b", "u", "sup", "sub"}:
        return raw
    return display or first or raw


def render_tags(text: Any) -> str:
    if text is None:
        return ""
    rendered = str(text)
    for _ in range(4):
        previous = rendered
        rendered = TAG_RE.sub(lambda match: tag_text(match.group(1), match.group(2)), rendered)
        rendered = NOTE_RE.sub("", rendered)
        if rendered == previous:
            break
    return clean_text(rendered)


def render_entry(entry: Any) -> str:
    if entry is None:
        return ""
    if isinstance(entry, str):
        return render_tags(entry)
    if isinstance(entry, (int, float)):
        return str(entry)
    if isinstance(entry, list):
        return clean_text("\n\n".join(part for part in (render_entry(item) for item in entry) if part))
    if not isinstance(entry, dict):
        return render_tags(entry)

    entry_type = entry.get("type")
    name = render_tags(entry.get("name", ""))
    if entry_type == "list":
        items = [render_entry(item) for item in entry.get("items", [])]
        return clean_text("\n".join(f"- {item}" for item in items if item))
    if entry_type == "table":
        lines = [name] if name else []
        for row in entry.get("rows", []):
            if isinstance(row, list):
                lines.append(" | ".join(render_entry(cell) for cell in row))
            else:
                lines.append(render_entry(row))
        return clean_text("\n".join(line for line in lines if line))
    if entry_type == "item":
        body = render_entry(entry.get("entry") or entry.get("entries", []))
        return clean_text(f"{name}. {body}" if name and body else name or body)
    if entry_type in {"entries", "inset", "quote"}:
        body = render_entry(entry.get("entries", []))
        return clean_text(f"{name}. {body}" if name and body else name or body)

    parts = []
    if "entries" in entry:
        parts.append(render_entry(entry.get("entries")))
    if "entry" in entry:
        parts.append(render_entry(entry.get("entry")))
    body = clean_text("\n".join(part for part in parts if part))
    return clean_text(f"{name}. {body}" if name and body else name or body)


def render_time(raw_time: Any) -> str:
    if not isinstance(raw_time, list):
        return ""
    parts = []
    for item in raw_time:
        if not isinstance(item, dict):
            continue
        number = item.get("number", 1)
        unit = UNIT_NAMES.get(str(item.get("unit", "")), str(item.get("unit", "")))
        condition = render_tags(item.get("condition", ""))
        if unit == "reaction":
            text = "1 reaction"
        else:
            suffix = "s" if number != 1 and unit not in {"bonus action"} else ""
            text = f"{number} {unit}{suffix}".strip()
        if condition:
            text = f"{text}, {condition}"
        parts.append(text)
    return "; ".join(parts)


def render_range(raw_range: Any) -> str:
    if not isinstance(raw_range, dict):
        return ""
    range_type = raw_range.get("type")
    distance = raw_range.get("distance", {})
    if not isinstance(distance, dict):
        distance = {}
    distance_type = str(distance.get("type", ""))
    amount = distance.get("amount")

    if range_type == "point":
        if distance_type in DISTANCE_TYPES:
            return DISTANCE_TYPES[distance_type]
        if amount is not None:
            return f"{amount} {distance_type}".strip()
    if range_type in {"radius", "sphere", "cone", "cube", "line", "hemisphere"}:
        if amount is not None and distance_type:
            shape = range_type.replace("_", " ")
            unit = "foot" if distance_type == "feet" else distance_type.rstrip("s")
            return f"Self ({amount}-{unit} {shape})"
        return f"Self ({range_type})"
    if range_type == "special":
        return "Special"
    return render_tags(raw_range)


def render_components(raw_components: Any) -> str:
    if not isinstance(raw_components, dict):
        return ""
    parts = []
    if raw_components.get("v"):
        parts.append("V")
    if raw_components.get("s"):
        parts.append("S")
    if raw_components.get("m"):
        material = raw_components.get("m")
        if isinstance(material, dict):
            material_text = render_tags(material.get("text", ""))
        else:
            material_text = render_tags(material)
        parts.append(f"M ({material_text})" if material_text else "M")
    return ", ".join(parts)


def render_duration(raw_duration: Any) -> str:
    if not isinstance(raw_duration, list):
        return ""
    parts = []
    for item in raw_duration:
        if not isinstance(item, dict):
            continue
        duration_type = item.get("type")
        concentration = bool(item.get("concentration"))
        if duration_type == "instant":
            text = "Instantaneous"
        elif duration_type == "special":
            text = "Special"
        elif duration_type == "permanent":
            ends = item.get("ends")
            text = "Until dispelled"
            if isinstance(ends, list) and "trigger" in ends:
                text = "Until dispelled or triggered"
        elif duration_type == "timed":
            duration = item.get("duration", {})
            if isinstance(duration, dict):
                amount = duration.get("amount", 1)
                unit = str(duration.get("type", ""))
                text = f"{amount} {unit}{'s' if amount != 1 else ''}".strip()
            else:
                text = render_tags(duration)
        else:
            text = render_tags(item)
        if concentration:
            text = f"Concentration, up to {text}"
        parts.append(text)
    return " or ".join(part for part in parts if part)


def render_higher_levels(raw_entries: Any) -> str:
    if not isinstance(raw_entries, list):
        return ""
    rendered = []
    for entry in raw_entries:
        text = render_entry(entry)
        text = re.sub(r"^At Higher Levels\.\s*", "", text)
        text = re.sub(r"^Using a Higher-Level Spell Slot\.\s*", "", text)
        text = re.sub(r"^Cantrip Upgrade\.\s*", "", text)
        if text:
            rendered.append(text)
    return clean_text("\n\n".join(rendered))


def load_existing_italian() -> tuple[dict[str, str], dict[str, list[str]], dict[str, str]]:
    payload = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    raw_spells = payload.get("spells", payload) if isinstance(payload, dict) else payload
    italian_by_key: dict[str, str] = {}
    aliases_by_key: dict[str, list[str]] = {}
    english_by_key: dict[str, str] = {}
    for spell in raw_spells:
        if not isinstance(spell, dict):
            continue
        names = spell.get("names", {}) if isinstance(spell.get("names"), dict) else {}
        english = spell.get("name") or names.get("en")
        italian = names.get("it", "")
        aliases = [alias for alias in spell.get("aliases", []) if isinstance(alias, str)]
        keys = {normalize_key(english), normalize_key(spell.get("id", "").replace("-", " ")), *(normalize_key(alias) for alias in aliases)}
        for key in keys:
            if not key:
                continue
            if italian:
                italian_by_key[key] = italian
            aliases_by_key[key] = aliases
            if english:
                english_by_key[key] = english

    correction_key = normalize_key("Maximilian's Earthen Grasp")
    old_key = normalize_key("Maximillian's Earthen Grasp")
    if old_key in italian_by_key:
        italian_by_key[correction_key] = italian_by_key[old_key]
        aliases_by_key[correction_key] = aliases_by_key.get(old_key, [])
        english_by_key[correction_key] = english_by_key.get(old_key, "Maximillian's Earthen Grasp")
    return italian_by_key, aliases_by_key, english_by_key


def class_lists_for_spell(source: str, name: str, sources_payload: dict[str, Any], allowed_sources: set[str]) -> list[str]:
    source_block = sources_payload.get(source, {})
    if not isinstance(source_block, dict):
        return []
    spell_block = source_block.get(name, {})
    if not isinstance(spell_block, dict):
        return []
    classes = []
    seen = set()
    base_class_names = {
        item.get("name", "")
        for item in spell_block.get("class", [])
        if isinstance(item, dict) and item.get("source", "") in allowed_sources
    }
    for group_name in ("class", "classVariant"):
        is_variant_group = group_name == "classVariant"
        for item in spell_block.get(group_name, []):
            if not isinstance(item, dict):
                continue
            class_source = item.get("source", "")
            class_name = item.get("name", "")
            if class_source not in allowed_sources or not class_name:
                continue
            label = render_tags(class_name)
            if item.get("definedInSource") and (not is_variant_group or class_name in base_class_names):
                label = f"{label} (Optional)"
            if is_variant_group and class_name in base_class_names and not label.endswith("(Optional)"):
                label = f"{label} (Optional)"
            if label not in seen:
                seen.add(label)
                classes.append(label)
    return classes


def convert_spell(
    raw: dict[str, Any],
    metadata: dict[str, dict[str, str]],
    sources_payload: dict[str, Any],
    allowed_sources: set[str],
    italian_by_key: dict[str, str],
    aliases_by_key: dict[str, list[str]],
) -> dict[str, Any]:
    source = raw.get("source", "")
    name = render_tags(raw.get("name", ""))
    name_key = normalize_key(name)
    italian = italian_by_key.get(name_key, "")
    existing_aliases = aliases_by_key.get(name_key, [])
    aliases = [name]
    if italian:
        aliases.append(italian)
    aliases.extend(existing_aliases)
    raw_alias = raw.get("alias", [])
    if isinstance(raw_alias, str):
        aliases.append(raw_alias)
    elif isinstance(raw_alias, list):
        aliases.extend(alias for alias in raw_alias if isinstance(alias, str))

    level_int = int(raw.get("level", 0) or 0)
    return {
        "id": spell_id(name),
        "name": name,
        "names": {
            "en": name,
            "it": italian,
        },
        "aliases": list(dict.fromkeys(alias.strip() for alias in aliases if alias and alias.strip())),
        "level": LEVEL_NAMES.get(level_int, f"{level_int}th Level"),
        "level_int": level_int,
        "school": SCHOOL_NAMES.get(str(raw.get("school", "")), str(raw.get("school", ""))),
        "casting_time": render_time(raw.get("time", [])),
        "range": render_range(raw.get("range", {})),
        "components": render_components(raw.get("components", {})),
        "duration": render_duration(raw.get("duration", [])),
        "source": source_name(source, metadata),
        "source_abbreviation": source,
        "source_page": raw.get("page", 0) or 0,
        "source_commit": SOURCE_COMMIT,
        "description": render_entry(raw.get("entries", [])),
        "higher_levels": render_higher_levels(raw.get("entriesHigherLevel", [])),
        "spell_lists": class_lists_for_spell(source, name, sources_payload, allowed_sources),
        "ritual": bool(raw.get("meta", {}).get("ritual")) if isinstance(raw.get("meta"), dict) else False,
    }


def parse_ref(ref: str) -> tuple[str, str] | None:
    parts = str(ref).split("|")
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def source_priority(source: str, metadata: dict[str, dict[str, str]]) -> tuple[str, str]:
    return metadata.get(source, {}).get("published", ""), source


def has_media_keys(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in MEDIA_KEYS or has_media_keys(item) for key, item in value.items())
    if isinstance(value, list):
        return any(has_media_keys(item) for item in value)
    return False


def main() -> int:
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    metadata = source_metadata()
    index = fetch_json("spells/index.json")
    sources_payload = fetch_json("spells/sources.json")
    allowed_sources = {source for source in index if is_allowed_source(source, metadata)}
    excluded_sources = sorted(set(index) - allowed_sources)
    italian_by_key, aliases_by_key, english_by_key = load_existing_italian()

    raw_spells: list[dict[str, Any]] = []
    for manifest_source, file_name in index.items():
        if manifest_source not in allowed_sources:
            continue
        payload = fetch_json(f"spells/{file_name}")
        for spell in payload.get("spell", []):
            if not isinstance(spell, dict):
                continue
            source = spell.get("source", manifest_source)
            if source not in allowed_sources:
                continue
            spell = {key: value for key, value in spell.items() if key not in MEDIA_KEYS}
            spell.setdefault("source", source)
            raw_spells.append(spell)

    raw_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_keys: list[dict[str, str]] = []
    for spell in raw_spells:
        key = (normalize_key(spell.get("name", "")), spell.get("source", ""))
        if key in raw_by_key:
            duplicate_keys.append({"name": spell.get("name", ""), "source": spell.get("source", "")})
        raw_by_key[key] = spell

    present_keys = set(raw_by_key)
    skipped_reprints: list[dict[str, str]] = []
    skip_keys: set[tuple[str, str]] = set()
    for key, spell in raw_by_key.items():
        for ref in spell.get("reprintedAs", []) or []:
            parsed = parse_ref(ref)
            if not parsed:
                continue
            target_name, target_source = parsed
            target_key = (normalize_key(target_name), target_source)
            if target_source in allowed_sources and target_key in present_keys:
                skip_keys.add(key)
                skipped_reprints.append({"name": spell.get("name", ""), "source": spell.get("source", ""), "reprinted_as": ref})
                break

    converted_by_name: dict[str, dict[str, Any]] = {}
    duplicate_names: list[dict[str, str]] = []
    for key, raw in raw_by_key.items():
        if key in skip_keys:
            continue
        converted = convert_spell(raw, metadata, sources_payload, allowed_sources, italian_by_key, aliases_by_key)
        name_key = normalize_key(converted["name"])
        existing = converted_by_name.get(name_key)
        if existing is not None:
            old_source = existing.get("source_abbreviation", "")
            new_source = converted.get("source_abbreviation", "")
            if source_priority(new_source, metadata) > source_priority(old_source, metadata):
                converted_by_name[name_key] = converted
                kept_source, discarded_source = new_source, old_source
            else:
                kept_source, discarded_source = old_source, new_source
            duplicate_names.append({"name": converted["name"], "kept_source": kept_source, "discarded_source": discarded_source})
            continue
        converted_by_name[name_key] = converted

    spells = sorted(converted_by_name.values(), key=lambda item: (item["level_int"], normalize_key(item["name"])))
    spell_ids = [spell["id"] for spell in spells]
    duplicate_ids = sorted(name for name in set(spell_ids) if spell_ids.count(name) > 1)
    if duplicate_ids:
        raise ValueError(f"Duplicate spell ids after conversion: {duplicate_ids[:10]}")

    payload = {
        "source": "https://github.com/5etools-mirror-3/5etools-src/tree/main/data/spells",
        "source_commit": SOURCE_COMMIT,
        "license_note": "Spell data generated from the 5etools mirror requested for Arcane Manager.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spell_count": len(spells),
        "spells": spells,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    italian_preserved = [
        {"name": spell["name"], "italian_name": spell["names"]["it"]}
        for spell in spells
        if spell.get("names", {}).get("it")
    ]
    local_italian_names = {normalize_key(value) for value in english_by_key.values() if value}
    corrected_name_keys = {normalize_key("Maximillian's Earthen Grasp")}
    corrected_name_matches = [
        {
            "from": "Maximillian's Earthen Grasp",
            "to": "Maximilian's Earthen Grasp",
            "italian_name": converted_by_name.get(normalize_key("Maximilian's Earthen Grasp"), {}).get("names", {}).get("it", ""),
        }
    ]
    missing_local_italian = sorted(
        english_by_key.get(key, key)
        for key, italian in italian_by_key.items()
        if italian and key in local_italian_names and key not in converted_by_name and key not in corrected_name_keys
    )
    report = {
        "source_commit": SOURCE_COMMIT,
        "raw_entries": len(raw_spells),
        "spells_written": len(spells),
        "allowed_sources": sorted(allowed_sources),
        "excluded_sources": excluded_sources,
        "skipped_reprints": skipped_reprints,
        "duplicate_keys": duplicate_keys,
        "duplicate_names": duplicate_names,
        "duplicate_ids": duplicate_ids,
        "italian_names_preserved": italian_preserved,
        "italian_names_preserved_count": len(italian_preserved),
        "corrected_name_matches": corrected_name_matches,
        "missing_local_italian_spell_names": missing_local_italian,
        "media_keys_present_in_output": has_media_keys(payload),
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(spells)} spells to {OUTPUT_FILE}")
    print(f"Wrote import report to {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
