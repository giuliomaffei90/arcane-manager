#!/usr/bin/env python3
"""Build Arcane Manager's bundled bestiary from 5etools monster JSON."""

from __future__ import annotations

import copy
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "ebd1827660ee61d1a59227d5979a137494dce1c8"
BASE_URL = f"https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/{SOURCE_COMMIT}/data"
ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "bestiary_srd.json"
REPORT_FILE = ROOT_DIR / "reports" / "5etools_bestiary_import.json"
TODO_FILE = ROOT_DIR / "reports" / "5etools_bestiary_todo.md"

ABILITY_KEYS = ("str", "dex", "con", "int", "wis", "cha")
ABILITY_NAMES = {
    "str": "strength",
    "dex": "dexterity",
    "con": "constitution",
    "int": "intelligence",
    "wis": "wisdom",
    "cha": "charisma",
}
SIZE_NAMES = {
    "T": "Tiny",
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "H": "Huge",
    "G": "Gargantuan",
    "V": "Varies",
}
ALIGNMENT_NAMES = {
    "L": "lawful",
    "N": "neutral",
    "NX": "neutral",
    "NY": "neutral",
    "C": "chaotic",
    "G": "good",
    "E": "evil",
    "U": "unaligned",
    "A": "any alignment",
}
ATTACK_TYPES = {
    "mw": "Melee Weapon Attack:",
    "rw": "Ranged Weapon Attack:",
    "ms": "Melee Spell Attack:",
    "rs": "Ranged Spell Attack:",
    "mw,rw": "Melee or Ranged Weapon Attack:",
    "rw,mw": "Melee or Ranged Weapon Attack:",
    "ms,rs": "Melee or Ranged Spell Attack:",
    "rs,ms": "Melee or Ranged Spell Attack:",
    "m": "Melee Attack:",
    "r": "Ranged Attack:",
    "m,r": "Melee or Ranged Attack:",
}
MEDIA_KEYS = {
    "altArt",
    "attachedItems",
    "fluff",
    "hasFluff",
    "hasFluffImages",
    "hasToken",
    "image",
    "images",
    "soundClip",
    "token",
    "tokenCredit",
    "tokenCustom",
}
EXCLUDED_SOURCES = {"XMM", "XPHB", "XDMG"}
EXCLUDED_CREATURE_NAMES = {"mechanical bird"}

TAG_RE = re.compile(r"\{@([a-zA-Z][a-zA-Z0-9]*)\s*([^{}]*?)?\}")
DICE_RE = re.compile(r"\b\d+d\d+(?:\s*[+-]\s*\d+)?\b")
HIT_RE = re.compile(r"(?:Attack:\s*)?([+-]\d+)\s+to hit", re.I)


def fetch_json(path: str) -> Any:
    with urllib.request.urlopen(f"{BASE_URL}/{path}", timeout=60) as response:
        return json.load(response)


def fetch_text(path: str) -> str:
    with urllib.request.urlopen(f"{BASE_URL.rsplit('/data', 1)[0]}/{path}", timeout=60) as response:
        return response.read().decode("utf-8")


def normalize_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(text).lower())).strip()


def monster_key(name: str, source: str) -> str:
    return f"{normalize_key(name)}|{source}"


def parse_ref(ref: str) -> tuple[str, str] | None:
    parts = str(ref).split("|")
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def source_metadata() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
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

    parser_map: dict[str, str] = {}
    try:
        parser = fetch_text("js/parser.js")
    except Exception:
        return metadata, parser_map

    constants = dict(re.findall(r"Parser\.([A-Za-z0-9_]+)\s*=\s*\"([^\"]+)\";", parser))
    assignments = re.findall(r"Parser\.([A-Za-z0-9_]+)\s*=\s*([^;]+);", parser)
    for _ in range(5):
        changed = False
        for const_name, expression in assignments:
            value = eval_parser_expression(expression.strip(), constants)
            if value and constants.get(const_name) != value:
                constants[const_name] = value
                changed = True
        if not changed:
            break

    for const_name, expression in re.findall(
        r"Parser\.SOURCE_JSON_TO_FULL\[Parser\.([A-Za-z0-9_]+)\]\s*=\s*([^;]+);",
        parser,
    ):
        source = constants.get(const_name)
        full_name = eval_parser_expression(expression.strip(), constants)
        if source and full_name:
            parser_map[source] = full_name
            metadata.setdefault(source, {"name": full_name, "published": "", "group": ""})
    return metadata, parser_map


def eval_parser_expression(expression: str, constants: dict[str, str]) -> str:
    expression = expression.strip()
    if expression.startswith('"') and expression.endswith('"'):
        return expression.strip('"')
    parser_ref = re.fullmatch(r"Parser\.([A-Za-z0-9_]+)", expression)
    if parser_ref:
        return constants.get(parser_ref.group(1), "")
    if expression.startswith("`") and expression.endswith("`"):
        template = expression.strip("`")
        return re.sub(
            r"\$\{Parser\.([A-Za-z0-9_]+)\}",
            lambda match: constants.get(match.group(1), match.group(0)),
            template,
        )
    return ""


def is_pre_2024_source(source: str, metadata: dict[str, dict[str, str]]) -> bool:
    if source in EXCLUDED_SOURCES:
        return False
    published = metadata.get(source, {}).get("published", "")
    if published >= "2024-01-01":
        return False
    return True


def source_name(source: str, metadata: dict[str, dict[str, str]], parser_map: dict[str, str]) -> str:
    return metadata.get(source, {}).get("name") or parser_map.get(source) or source


def clean_text(text: Any) -> str:
    value = str(text if text is not None else "")
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


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
    if tag in {"atk", "atkr"}:
        return ATTACK_TYPES.get(first.replace(" ", ""), "Attack:")
    if tag == "h":
        return "Hit: "
    if tag == "recharge":
        return f"(Recharge {first}-6)" if first else "(Recharge 6)"
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
    return clean_text(TAG_RE.sub(lambda match: tag_text(match.group(1), match.group(2)), str(text)))


def render_entry(entry: Any) -> str:
    if entry is None:
        return ""
    if isinstance(entry, str):
        return render_tags(entry)
    if isinstance(entry, (int, float)):
        return str(entry)
    if isinstance(entry, list):
        return clean_text("\n".join(part for part in (render_entry(item) for item in entry) if part))
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

    parts = []
    if "entries" in entry:
        parts.append(render_entry(entry.get("entries")))
    if "entry" in entry:
        parts.append(render_entry(entry.get("entry")))
    body = clean_text("\n".join(part for part in parts if part))
    return clean_text(f"{name}. {body}" if name and body else name or body)


def render_list_value(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return render_tags(value)
    if isinstance(value, list):
        return ", ".join(part for part in (render_list_value(item) for item in value) if part)
    if isinstance(value, dict):
        if "special" in value:
            return render_tags(value.get("special", ""))
        inner = value.get("resist") or value.get("immune") or value.get("vulnerable") or value.get("conditionImmune")
        note = render_tags(value.get("note", ""))
        pre_note = render_tags(value.get("preNote", ""))
        rendered = render_list_value(inner)
        return clean_text(" ".join(part for part in (pre_note, rendered, note) if part))
    return render_tags(value)


def clean_armor_note(text: str) -> str:
    parts = [part.strip() for part in text.split(",")]
    kept = [part for part in parts if part.lower() != "natural armor"]
    return ", ".join(kept)


def clean_ac_text(text: str) -> str:
    text = re.sub(r"\s*\(\s*(?:see\s+)?natural armor(?:\s+feature)?\s*\)", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def render_ac(raw_ac: Any) -> tuple[int | str, str]:
    if not isinstance(raw_ac, list):
        value = clean_ac_text(render_tags(raw_ac))
        return value, value
    parts: list[str] = []
    base_value: int | str = ""
    for item in raw_ac:
        if isinstance(item, int):
            text = str(item)
            if base_value == "":
                base_value = item
            parts.append(text)
        elif isinstance(item, dict):
            if "special" in item:
                text = clean_ac_text(render_tags(item.get("special", "")))
                if base_value == "":
                    base_value = text
                parts.append(text)
                continue
            ac = str(item.get("ac", "")).strip()
            from_text = clean_armor_note(render_list_value(item.get("from", [])))
            condition = render_tags(item.get("condition", ""))
            text = ac
            if from_text:
                text = f"{text} ({from_text})"
            if condition:
                text = f"{text} {condition}"
            if text.strip():
                text = clean_ac_text(text)
                if base_value == "":
                    try:
                        base_value = int(ac)
                    except (TypeError, ValueError):
                        base_value = text
                parts.append(text)
        else:
            text = clean_ac_text(render_tags(item))
            if base_value == "":
                base_value = text
            parts.append(text)
    detail = "; ".join(part for part in parts if part)
    if base_value == "" and detail:
        base_value = detail
    return base_value, detail


def render_hp(raw_hp: Any) -> tuple[int | str, str]:
    if isinstance(raw_hp, dict):
        if "special" in raw_hp:
            return render_tags(raw_hp.get("special", "")), ""
        average = raw_hp.get("average")
        formula = render_tags(raw_hp.get("formula", ""))
        try:
            return int(average), formula
        except (TypeError, ValueError):
            return 0, formula
    try:
        return int(raw_hp or 0), ""
    except (TypeError, ValueError):
        return render_tags(raw_hp), ""


def render_speed(raw_speed: Any) -> str:
    if isinstance(raw_speed, str):
        return render_tags(raw_speed)
    if not isinstance(raw_speed, dict):
        return ""
    parts: list[str] = []
    for key, value in raw_speed.items():
        if key in {"canHover", "alternate"}:
            continue
        label = "walk" if key == "walk" else key
        if isinstance(value, int):
            parts.append(f"{label} {value} ft." if label != "walk" else f"{value} ft.")
        elif isinstance(value, dict):
            number = value.get("number")
            condition = render_tags(value.get("condition", ""))
            if number:
                base = f"{label} {number} ft." if label != "walk" else f"{number} ft."
                parts.append(f"{base} {condition}".strip())
        else:
            rendered = render_tags(value)
            if rendered:
                parts.append(f"{label} {rendered}" if label != "walk" else rendered)
    if raw_speed.get("canHover") and parts:
        parts[-1] = f"{parts[-1]} (hover)"
    return ", ".join(parts)


def render_alignment(raw_alignment: Any) -> str:
    if isinstance(raw_alignment, str):
        return ALIGNMENT_NAMES.get(raw_alignment, raw_alignment)
    if not isinstance(raw_alignment, list):
        return ""
    if len(raw_alignment) == 1:
        item = raw_alignment[0]
        if isinstance(item, dict):
            return render_tags(item.get("special", ""))
        return ALIGNMENT_NAMES.get(str(item), str(item))
    return " ".join(ALIGNMENT_NAMES.get(str(item), str(item).lower()) for item in raw_alignment)


def render_type(raw_type: Any) -> tuple[str, str]:
    if isinstance(raw_type, str):
        return raw_type, ""
    if not isinstance(raw_type, dict):
        return "", ""
    creature_type = render_tags(raw_type.get("type", ""))
    tags = raw_type.get("tags", [])
    tag_parts = []
    for item in tags if isinstance(tags, list) else [tags]:
        if isinstance(item, dict):
            tag_parts.append(render_tags(item.get("tag") or item.get("prefix") or item.get("name", "")))
        else:
            tag_parts.append(render_tags(item))
    return creature_type, ", ".join(part for part in tag_parts if part)


def render_bonus_map(raw: Any, ability_labels: bool = False) -> list[dict[str, int]]:
    if not isinstance(raw, dict):
        return []
    entries: list[dict[str, int]] = []
    for key, value in raw.items():
        label = ABILITY_NAMES.get(key, key) if ability_labels else key.replace(" ", "_")
        try:
            number = int(str(value).replace("+", "").strip())
        except (TypeError, ValueError):
            continue
        entries.append({label: number})
    return entries


def first_damage_dice(desc: str) -> str:
    match = DICE_RE.search(desc)
    return re.sub(r"\s+", "", match.group(0)) if match else ""


def attack_bonus(desc: str) -> int:
    match = HIT_RE.search(desc)
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0


def convert_entries(raw_entries: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_entries, list):
        return []
    converted: list[dict[str, Any]] = []
    for item in raw_entries:
        if not isinstance(item, dict):
            text = render_entry(item)
            if text:
                converted.append({"name": "", "desc": text, "attack_bonus": 0})
            continue
        name = render_tags(item.get("name", ""))
        desc = render_entry(item.get("entries", []))
        if not desc:
            desc = render_entry(item)
        entry: dict[str, Any] = {"name": name, "desc": desc, "attack_bonus": attack_bonus(desc)}
        dice = first_damage_dice(desc)
        if dice:
            entry["damage_dice"] = dice
        spell_links = spell_links_for_text(json.dumps(item, ensure_ascii=False))
        if spell_links:
            entry["spell_links"] = spell_links
        converted.append(entry)
    return converted


def spell_links_for_text(text: str) -> list[dict[str, str]]:
    links = []
    for match in re.finditer(r"\{@spell\s+([^}|]+)(?:\|([^}|]+))?(?:\|([^}]+))?\}", text):
        spell_name = match.group(3) or match.group(1)
        links.append({"text": render_tags(spell_name), "spell_id": ""})
    return links


def render_spellcasting(raw_spellcasting: Any) -> list[str]:
    if not isinstance(raw_spellcasting, list):
        return []
    blocks: list[str] = []
    for block in raw_spellcasting:
        if not isinstance(block, dict):
            continue
        lines = []
        name = render_tags(block.get("name", "Spellcasting"))
        header = render_entry(block.get("headerEntries", []))
        if header:
            lines.append(f"{name}. {header}")
        for key, label in (("will", "At will"), ("constant", "Constant")):
            spells = render_list_value(block.get(key, []))
            if spells:
                lines.append(f"{label}: {spells}")
        daily = block.get("daily", {})
        if isinstance(daily, dict):
            for amount, spells in sorted(daily.items()):
                lines.append(f"{amount}/day: {render_list_value(spells)}")
        spells = block.get("spells", {})
        if isinstance(spells, dict):
            for level, payload in sorted(spells.items(), key=lambda item: str(item[0])):
                if not isinstance(payload, dict):
                    continue
                spell_list = render_list_value(payload.get("spells", []))
                if spell_list:
                    slots = payload.get("slots")
                    label = f"Level {level}"
                    if slots:
                        label = f"{label} ({slots} slots)"
                    lines.append(f"{label}: {spell_list}")
        footer = render_entry(block.get("footerEntries", []))
        if footer:
            lines.append(footer)
        text = clean_text("\n".join(lines))
        if text:
            blocks.append(text)
    return blocks


def apply_replace_text(target: Any, replace: str, replacement: str, flags: str = "") -> Any:
    pattern_flags = re.I if "i" in flags else 0
    if isinstance(target, str):
        return re.sub(replace, replacement, target, flags=pattern_flags)
    if isinstance(target, list):
        return [apply_replace_text(item, replace, replacement, flags) for item in target]
    if isinstance(target, dict):
        return {key: apply_replace_text(value, replace, replacement, flags) for key, value in target.items()}
    return target


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def apply_array_mod(items: Any, mod: dict[str, Any], warnings: list[str]) -> list[Any]:
    current = as_list(items)
    mode = mod.get("mode")
    new_items = as_list(mod.get("items"))
    if mode == "appendArr":
        return current + new_items
    if mode == "prependArr":
        return new_items + current
    if mode == "appendIfNotExistsArr":
        names = {normalize_key(item.get("name", "")) for item in current if isinstance(item, dict)}
        for item in new_items:
            name = normalize_key(item.get("name", "")) if isinstance(item, dict) else normalize_key(item)
            if name not in names:
                current.append(item)
        return current
    if mode == "replaceArr":
        replace = normalize_key(mod.get("replace", ""))
        replaced = False
        output = []
        for item in current:
            item_name = normalize_key(item.get("name", "")) if isinstance(item, dict) else normalize_key(item)
            if replace and item_name == replace:
                output.extend(new_items)
                replaced = True
            else:
                output.append(item)
        if not replaced:
            output.extend(new_items)
            warnings.append(f"replaceArr target not found: {mod.get('replace')}")
        return output
    if mode == "removeArr":
        names = {normalize_key(name) for name in as_list(mod.get("names") or mod.get("items") or mod.get("remove"))}
        return [
            item for item in current
            if (normalize_key(item.get("name", "")) if isinstance(item, dict) else normalize_key(item)) not in names
        ]
    if mode == "insertArr":
        index = int(mod.get("index", len(current)))
        return current[:index] + new_items + current[index:]
    warnings.append(f"unsupported array mode: {mode}")
    return current


def apply_mods(creature: dict[str, Any], mods: Any, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(mods, dict):
        return creature
    for prop, raw_mods in mods.items():
        for mod in as_list(raw_mods):
            if not isinstance(mod, dict):
                continue
            mode = mod.get("mode")
            if mode == "replaceTxt":
                replace = mod.get("replace", "")
                replacement = mod.get("with", "")
                if prop == "*":
                    creature = apply_replace_text(creature, replace, replacement, mod.get("flags", ""))
                else:
                    creature[prop] = apply_replace_text(creature.get(prop), replace, replacement, mod.get("flags", ""))
            elif mode in {"appendArr", "prependArr", "appendIfNotExistsArr", "replaceArr", "removeArr", "insertArr"}:
                creature[prop] = apply_array_mod(creature.get(prop, []), mod, warnings)
            elif mode == "setProp":
                creature[prop] = mod.get("value")
            elif mode == "addSkills":
                skills = dict(creature.get("skill", {}) if isinstance(creature.get("skill"), dict) else {})
                for key, value in mod.get("skills", {}).items():
                    skills[key] = value
                creature["skill"] = skills
            else:
                warnings.append(f"unsupported mod mode on {prop}: {mode}")
    return creature


def strip_media(raw: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in raw.items() if key not in MEDIA_KEYS}


def convert_creature(raw: dict[str, Any], metadata: dict[str, dict[str, str]], parser_map: dict[str, str]) -> dict[str, Any]:
    raw = strip_media(raw)
    source = raw.get("source", "")
    hp, hit_dice = render_hp(raw.get("hp"))
    ac, ac_detail = render_ac(raw.get("ac", []))
    creature_type, subtype = render_type(raw.get("type", ""))
    senses = render_list_value(raw.get("senses", []))
    passive = raw.get("passive")
    if passive and "passive Perception" not in senses:
        senses = f"{senses}, passive Perception {passive}" if senses else f"passive Perception {passive}"

    converted: dict[str, Any] = {
        "name": render_tags(raw.get("name", "")),
        "source": source_name(source, metadata, parser_map),
        "source_abbreviation": source,
        "source_page": raw.get("page", 0) or 0,
        "source_commit": SOURCE_COMMIT,
        "size": render_list_value([SIZE_NAMES.get(str(size), str(size)) for size in as_list(raw.get("size"))]),
        "type": creature_type,
        "subtype": subtype,
        "alignment": render_alignment(raw.get("alignment")),
        "ac": ac,
        "ac_detail": ac_detail,
        "hp": hp,
        "hit_dice": hit_dice,
        "speed": render_speed(raw.get("speed", {})),
        "stats": [int(raw.get(key, 10) or 10) for key in ABILITY_KEYS],
        "saves": render_bonus_map(raw.get("save"), ability_labels=True),
        "skillsaves": render_bonus_map(raw.get("skill")),
        "damage_vulnerabilities": render_list_value(raw.get("vulnerable", [])),
        "damage_resistances": render_list_value(raw.get("resist", [])),
        "damage_immunities": render_list_value(raw.get("immune", [])),
        "condition_immunities": render_list_value(raw.get("conditionImmune", [])),
        "senses": senses,
        "languages": render_list_value(raw.get("languages", [])) or "--",
        "cr": render_cr(raw.get("cr", "")),
        "bestiary": True,
        "traits": convert_entries(raw.get("trait", [])),
        "actions": convert_entries(raw.get("action", [])),
        "bonus_actions": convert_entries(raw.get("bonus", [])),
        "reactions": convert_entries(raw.get("reaction", [])),
        "legendary_actions": convert_entries(raw.get("legendary", [])),
        "mythic_actions": convert_entries(raw.get("mythic", [])),
        "spells": render_spellcasting(raw.get("spellcasting", [])),
    }
    return converted


def render_cr(raw_cr: Any) -> str:
    if isinstance(raw_cr, dict):
        return render_tags(raw_cr.get("cr", ""))
    return render_tags(raw_cr)


def has_variable_hp_or_ac(raw: dict[str, Any]) -> bool:
    hp = raw.get("hp")
    if isinstance(hp, dict) and "special" in hp:
        return True
    ac = raw.get("ac")
    if isinstance(ac, list):
        return any(isinstance(item, dict) and "special" in item for item in ac)
    return False


def source_priority(source: str, metadata: dict[str, dict[str, str]]) -> tuple[str, str]:
    published = metadata.get(source, {}).get("published", "")
    return published, source


def main() -> int:
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    index = fetch_json("bestiary/index.json")
    metadata, parser_map = source_metadata()
    allowed_sources = {source for source in index if is_pre_2024_source(source, metadata)}
    excluded_sources = sorted(set(index) - allowed_sources)

    raw_entries: list[dict[str, Any]] = []
    for manifest_source, file_name in index.items():
        payload = fetch_json(f"bestiary/{file_name}")
        for monster in payload.get("monster", []):
            if not isinstance(monster, dict):
                continue
            source = monster.get("source", manifest_source)
            if source not in allowed_sources:
                continue
            monster = dict(monster)
            monster.setdefault("source", source)
            raw_entries.append(monster)

    raw_by_key: dict[str, dict[str, Any]] = {}
    duplicate_keys: list[str] = []
    for monster in raw_entries:
        key = monster_key(monster.get("name", ""), monster.get("source", ""))
        if key in raw_by_key:
            duplicate_keys.append(key)
        raw_by_key[key] = monster

    skipped_reprints: list[dict[str, str]] = []
    skipped_manual: list[dict[str, str]] = []
    skip_keys: set[str] = set()
    present_keys = set(raw_by_key)
    for monster in raw_entries:
        source = monster.get("source", "")
        key = monster_key(monster.get("name", ""), source)
        if normalize_key(monster.get("name", "")) in EXCLUDED_CREATURE_NAMES:
            skip_keys.add(key)
            skipped_manual.append({"name": monster.get("name", ""), "source": source, "reason": "manual exclusion"})
            continue
        for ref in monster.get("reprintedAs", []) or []:
            parsed = parse_ref(ref)
            if not parsed:
                continue
            target_name, target_source = parsed
            if target_source in allowed_sources and monster_key(target_name, target_source) in present_keys:
                skip_keys.add(key)
                skipped_reprints.append(
                    {
                        "name": monster.get("name", ""),
                        "source": source,
                        "reprinted_as": ref,
                    }
                )
                break

    library: dict[str, dict[str, Any]] = {}
    copy_warnings: list[dict[str, Any]] = []
    for key, monster in raw_by_key.items():
        if "_copy" not in monster:
            library[key] = copy.deepcopy(monster)

    pending = {key: monster for key, monster in raw_by_key.items() if "_copy" in monster}
    while pending:
        progressed = False
        for key, monster in list(pending.items()):
            copy_spec = monster.get("_copy", {})
            base_key = monster_key(copy_spec.get("name", ""), copy_spec.get("source", ""))
            base = library.get(base_key)
            if base is None:
                continue
            warnings: list[str] = []
            if copy_spec.get("_templates"):
                warnings.append("templates present; copied base values and explicit overrides, template rules require manual review")
            resolved = copy.deepcopy(base)
            resolved = apply_mods(resolved, copy_spec.get("_mod"), warnings)
            for raw_key, value in monster.items():
                if raw_key == "_copy":
                    continue
                resolved[raw_key] = value
            library[key] = resolved
            if warnings:
                copy_warnings.append({"name": monster.get("name", ""), "source": monster.get("source", ""), "warnings": warnings})
            del pending[key]
            progressed = True
        if not progressed:
            for key, monster in sorted(pending.items()):
                copy_spec = monster.get("_copy", {})
                copy_warnings.append(
                    {
                        "name": monster.get("name", ""),
                        "source": monster.get("source", ""),
                        "warnings": [f"missing base creature {copy_spec.get('name')}|{copy_spec.get('source')}"],
                    }
                )
            break

    converted_by_name: dict[str, dict[str, Any]] = {}
    duplicate_names: list[dict[str, str]] = []
    special_statblocks: list[dict[str, str]] = []
    included_keys = [key for key in raw_by_key if key not in skip_keys and key in library]
    for key in included_keys:
        raw = library[key]
        converted = convert_creature(raw, metadata, parser_map)
        if not converted.get("name"):
            continue
        name_key = normalize_key(converted["name"])
        existing = converted_by_name.get(name_key)
        if existing is not None:
            old_source = existing.get("source_abbreviation", "")
            new_source = converted.get("source_abbreviation", "")
            duplicate_names.append(
                {
                    "name": converted["name"],
                    "kept_source": "",
                    "discarded_source": "",
                }
            )
            if source_priority(new_source, metadata) > source_priority(old_source, metadata):
                duplicate_names[-1]["kept_source"] = new_source
                duplicate_names[-1]["discarded_source"] = old_source
                converted_by_name[name_key] = converted
            else:
                duplicate_names[-1]["kept_source"] = old_source
                duplicate_names[-1]["discarded_source"] = new_source
            continue
        converted_by_name[name_key] = converted
        if has_variable_hp_or_ac(raw):
            special_statblocks.append(
                {
                    "name": converted.get("name", ""),
                    "source": converted.get("source_abbreviation", ""),
                    "hp": str(converted.get("hp", "")),
                    "ac": str(converted.get("ac", "")),
                }
            )

    creatures = sorted(converted_by_name.values(), key=lambda item: normalize_key(item["name"]))
    special_statblocks = sorted(
        {f"{item['name']}|{item['source']}": item for item in special_statblocks}.values(),
        key=lambda item: normalize_key(item["name"]),
    )

    payload = {
        "source": "https://github.com/5etools-mirror-3/5etools-src/tree/main/data/bestiary",
        "source_commit": SOURCE_COMMIT,
        "license_note": "Creature data generated from the 5etools mirror requested for Arcane Manager.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "creatures": creatures,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    report = {
        "source_commit": SOURCE_COMMIT,
        "raw_entries": len(raw_entries),
        "creatures_written": len(creatures),
        "allowed_sources": sorted(allowed_sources),
        "excluded_sources": excluded_sources,
        "skipped_manual": skipped_manual,
        "skipped_reprints": skipped_reprints,
        "duplicate_keys": duplicate_keys,
        "duplicate_names": duplicate_names,
        "copy_warnings": copy_warnings,
        "unresolved_copies": sorted(pending),
        "special_statblocks": special_statblocks,
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    TODO_FILE.write_text(todo_text(report), encoding="utf-8")

    print(f"Wrote {len(creatures)} creatures to {OUTPUT_FILE}")
    print(f"Wrote import report to {REPORT_FILE}")
    print(f"Wrote TODO notes to {TODO_FILE}")
    return 0


def todo_text(report: dict[str, Any]) -> str:
    lines = [
        "# 5etools Bestiary TODO",
        "",
        "Ricordami di migliorare la gestione degli statblock con HP o AC variabili.",
        "Per ora vengono inclusi nel JSON e visualizzati nello statblock, ma l'iniziativa usa 0 HP quando non c'e un valore numerico stabile.",
        "",
        f"- Statblock speciali rilevati: {len(report.get('special_statblocks', []))}",
        f"- `_copy` da rivedere: {len(report.get('copy_warnings', []))}",
        "",
    ]
    if report.get("special_statblocks"):
        lines.append("## HP/AC Speciali")
        for item in report["special_statblocks"][:80]:
            lines.append(f"- {item['name']} ({item['source']}): HP `{item['hp']}`, AC `{item['ac']}`")
        if len(report["special_statblocks"]) > 80:
            lines.append(f"- ...altri {len(report['special_statblocks']) - 80} nel report JSON.")
        lines.append("")
    if report.get("copy_warnings"):
        lines.append("## Copy/Template Da Verificare")
        for item in report["copy_warnings"][:80]:
            warnings = "; ".join(item.get("warnings", []))
            lines.append(f"- {item.get('name')} ({item.get('source')}): {warnings}")
        if len(report["copy_warnings"]) > 80:
            lines.append(f"- ...altri {len(report['copy_warnings']) - 80} nel report JSON.")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
