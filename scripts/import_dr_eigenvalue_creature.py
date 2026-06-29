#!/usr/bin/env python3
"""Convert one dr-eigenvalue bestiary creature page to Arcane Manager JSON."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://dr-eigenvalue.github.io/bestiary/creature/"
INDEX_URL = "https://dr-eigenvalue.github.io/bestiary/"
SOURCE_LABEL = "Tyranny of Dragons / dr-eigenvalue bestiary"
ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BESTIARY = ROOT_DIR / "dataset" / "bestiary.json"
DEFAULT_REPORT = ROOT_DIR / "reports" / "skipped_dr_eigenvalue_import.txt"
ABILITY_KEYS = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
ABILITY_LABELS = {
    "str": "strength",
    "dex": "dexterity",
    "con": "constitution",
    "int": "intelligence",
    "wis": "wisdom",
    "cha": "charisma",
}
CR_PATTERN = re.compile(r"^(?:0|[1-9]\d*|1/[248])$")
VARIABLE_MARKERS = (
    "level",
    "pb",
    "caregiver",
    "mentor",
    "summoner",
    "bonus",
    "hit dice equal",
)


class CreatureIndexParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items: list[tuple[str, str]] = []
        self._in_creature_link = False
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href") or ""
        if tag == "a" and href.startswith("/bestiary/creature/"):
            self._in_creature_link = True
            self._href = href
            self._text = []

    def handle_data(self, data: str):
        if self._in_creature_link:
            self._text.append(data)

    def handle_endtag(self, tag: str):
        if tag == "a" and self._in_creature_link:
            self.items.append((normalize_spaces("".join(self._text)), self._href))
            self._in_creature_link = False
            self._href = ""
            self._text = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug_or_url", nargs="?", help="Creature slug or full dr-eigenvalue creature URL")
    parser.add_argument("--bulk", action="store_true", help="Import all missing dr-eigenvalue creatures into the bestiary")
    parser.add_argument("--dry-run", action="store_true", help="Parse bulk import without writing bestiary changes")
    parser.add_argument("--bestiary", default=str(DEFAULT_BESTIARY), help="Bestiary JSON path for --bulk")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Skipped creature report path for --bulk")
    parser.add_argument("--workers", type=int, default=16, help="Parallel fetch workers for --bulk")
    parser.add_argument("--retries", type=int, default=3, help="Fetch retries per creature for --bulk")
    parser.add_argument("--source", default=SOURCE_LABEL)
    return parser.parse_args()


def creature_url(slug_or_url: str) -> str:
    if slug_or_url.startswith(("http://", "https://")):
        return slug_or_url
    return f"{BASE_URL}{slug_or_url.strip('/')}"


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u2019", "'")).strip()


def creature_key(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", normalize_spaces(name).lower())).strip()


def number_before_paren(text: str) -> int:
    match = re.match(r"\s*(\d+)", text)
    return int(match.group(1)) if match else 0


def is_variable_text(text: str) -> bool:
    normalized = normalize_spaces(text).lower()
    return any(marker in normalized for marker in VARIABLE_MARKERS)


def hit_dice_from_hp(text: str) -> str:
    match = re.search(r"\(([^)]+)\)", text)
    if not match:
        return ""
    return re.sub(r"\s*([+-])\s*", r" \1 ", match.group(1)).strip()


def parse_heading(text: str) -> tuple[str, str, str, str]:
    first, _, alignment = text.partition(",")
    parts = first.strip().split(" ", 1)
    size = parts[0] if parts else ""
    type_text = parts[1] if len(parts) > 1 else ""
    subtype = ""
    match = re.match(r"([^(]+)\(([^)]+)\)", type_text)
    if match:
        creature_type = match.group(1).strip()
        subtype = match.group(2).strip()
    else:
        creature_type = type_text.strip()
    return size, creature_type, subtype, alignment.strip()


def parse_bonus_entries(text: str, ability_labels: bool = False) -> list[dict[str, int]]:
    entries: list[dict[str, int]] = []
    for label, value in re.findall(r"([A-Za-z][A-Za-z ]*?)\s*([+-]\d+)", text):
        normalized_label = label.strip().lower()
        if ability_labels:
            normalized_label = ABILITY_LABELS.get(normalized_label[:3], normalized_label)
        else:
            normalized_label = normalized_label.replace(" ", "_")
        entries.append({normalized_label: int(value)})
    return entries


def attack_bonus(desc: str) -> int:
    match = re.search(r"(?:Weapon|Spell) Attack:\s*([+-]\d+)\s+to hit", desc)
    return int(match.group(1)) if match else 0


def first_damage_dice(desc: str) -> str | None:
    match = re.search(r"\((\d+d\d+(?:\s*[+-]\s*\d+)?)\)", desc)
    if not match:
        return None
    dice = re.match(r"(\d+d\d+)", match.group(1).replace(" ", ""))
    return dice.group(1) if dice else None


def first_damage_bonus(desc: str) -> int | None:
    match = re.search(r"\(\d+d\d+\s*([+-])\s*(\d+)\)", desc)
    if not match:
        return None
    value = int(match.group(2))
    return value if match.group(1) == "+" else -value


def entry_from_paragraph(node: Tag) -> dict[str, Any] | None:
    strong = node.find("strong")
    if strong is None:
        return None
    name = normalize_spaces(strong.get_text(" ", strip=True)).rstrip(".")
    text = normalize_spaces(node.get_text(" ", strip=True))
    desc = re.sub(rf"^{re.escape(name)}\.\s*", "", text)
    entry: dict[str, Any] = {"name": name, "desc": desc, "attack_bonus": attack_bonus(desc)}
    dice = first_damage_dice(desc)
    if dice:
        entry["damage_dice"] = dice
    bonus = first_damage_bonus(desc)
    if bonus is not None:
        entry["damage_bonus"] = bonus
    return entry


def is_spellcasting_entry(entry: dict[str, Any]) -> bool:
    return entry.get("name", "").startswith(("Spellcasting", "Innate Spellcasting"))


def spell_list_from_ul(node: Tag) -> list[dict[str, str]]:
    spells: list[dict[str, str]] = []
    for item in node.find_all("li", recursive=False):
        text = normalize_spaces(item.get_text(" ", strip=True))
        heading, separator, spell_text = text.partition(":")
        if separator and heading.strip() and spell_text.strip():
            spells.append({heading.strip(): spell_text.strip()})
    return spells


def passive_perception(skillsaves: list[dict[str, int]]) -> int | None:
    for entry in skillsaves:
        if "perception" in entry:
            return 10 + int(entry["perception"])
    return None


def parse_creature(html: str, source: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    block = soup.select_one(".stat-block .section-left")
    if block is None:
        raise ValueError("Could not find stat block.")

    name = normalize_spaces(block.select_one(".creature-heading h1").get_text(" ", strip=True))
    size, creature_type, subtype, alignment = parse_heading(
        normalize_spaces(block.select_one(".creature-heading h2").get_text(" ", strip=True))
    )

    properties: dict[str, str] = {}
    for line in block.select(".top-stats .property-line"):
        label = line.find("h4")
        value = line.find("p")
        if label is not None and value is not None:
            properties[normalize_spaces(label.get_text(" ", strip=True))] = normalize_spaces(value.get_text(" ", strip=True))

    stats: list[int] = []
    for key in ABILITY_KEYS:
        value = block.select_one(f".ability-{key} p")
        stats.append(number_before_paren(value.get_text(" ", strip=True)) if value is not None else 10)

    saves = parse_bonus_entries(properties.get("Saving Throws", ""), ability_labels=True)
    skillsaves = parse_bonus_entries(properties.get("Skills", ""))
    senses = properties.get("Senses", "")
    passive = passive_perception(skillsaves)
    if passive is not None and "passive Perception" not in senses:
        senses = f"{senses}, passive Perception {passive}" if senses else f"passive Perception {passive}"

    traits: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    legendary_actions: list[dict[str, Any]] = []
    spells: list[Any] = []
    current_entries = traits
    pending_spellcasting: dict[str, Any] | None = None

    for child in block.children:
        if not isinstance(child, Tag):
            continue
        if child.name == "h3":
            heading = normalize_spaces(child.get_text(" ", strip=True)).lower()
            if heading == "actions":
                current_entries = actions
            elif heading == "legendary actions":
                current_entries = legendary_actions
            pending_spellcasting = None
            continue
        if child.name == "p":
            entry = entry_from_paragraph(child)
            if entry is None:
                pending_spellcasting = None
                continue
            if current_entries is traits and is_spellcasting_entry(entry):
                spells = [entry["desc"]]
                pending_spellcasting = entry
            else:
                current_entries.append(entry)
                pending_spellcasting = None
            continue
        if child.name == "ul" and pending_spellcasting is not None:
            spells.extend(spell_list_from_ul(child))
            pending_spellcasting = None

    creature: dict[str, Any] = {
        "name": name,
        "source": source,
        "size": size,
        "type": creature_type,
        "subtype": subtype,
        "alignment": alignment,
        "ac": number_before_paren(properties.get("Armor Class", "")),
        "hp": number_before_paren(properties.get("Hit Points", "")),
        "hit_dice": hit_dice_from_hp(properties.get("Hit Points", "")),
        "speed": properties.get("Speed", ""),
        "stats": stats,
        "saves": saves,
        "skillsaves": skillsaves,
        "damage_vulnerabilities": properties.get("Damage Vulnerabilities", ""),
        "damage_resistances": properties.get("Damage Resistances", ""),
        "damage_immunities": properties.get("Damage Immunities", ""),
        "condition_immunities": properties.get("Condition Immunities", ""),
        "senses": senses,
        "languages": properties.get("Languages", ""),
        "cr": properties.get("Challenge", "").split(" ", 1)[0],
        "bestiary": True,
        "traits": traits,
        "actions": actions,
        "legendary_actions": legendary_actions,
    }
    if spells:
        creature["spells"] = spells
    return creature


def index_creatures() -> list[tuple[str, str]]:
    response = requests.get(INDEX_URL, timeout=30)
    response.raise_for_status()
    parser = CreatureIndexParser()
    parser.feed(response.text)
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, href in parser.items:
        key = creature_key(name)
        if not name or key in seen:
            continue
        seen.add(key)
        items.append((name, urljoin(INDEX_URL, href)))
    return items


def load_bestiary(path: Path) -> tuple[Any, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    creatures = payload.get("creatures") if isinstance(payload, dict) else payload
    if not isinstance(creatures, list):
        raise ValueError("Bestiary must be a list or an object with a creatures list.")
    return payload, creatures


def skip_reason(creature: dict[str, Any], properties: dict[str, str]) -> str | None:
    hp_text = properties.get("Hit Points", "")
    ac_text = properties.get("Armor Class", "")
    cr_text = properties.get("Challenge", "")
    cr = str(creature.get("cr", ""))
    if is_variable_text(hp_text) or is_variable_text(ac_text) or is_variable_text(cr_text):
        return f"variable statblock (AC={ac_text!r}, HP={hp_text!r}, CR={cr_text!r})"
    if not creature.get("name"):
        return "missing name"
    if creature.get("hp", 0) <= 0:
        return f"missing or zero HP (HP={hp_text!r})"
    if not cr or not CR_PATTERN.fullmatch(cr):
        return f"missing or unsupported CR (CR={cr_text!r})"
    if not creature.get("size") or not creature.get("type"):
        return "missing size or type"
    return None


def parse_creature_with_properties(html: str, source: str) -> tuple[dict[str, Any], dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    block = soup.select_one(".stat-block .section-left")
    if block is None:
        raise ValueError("Could not find stat block.")
    properties: dict[str, str] = {}
    for line in block.select(".top-stats .property-line"):
        label = line.find("h4")
        value = line.find("p")
        if label is not None and value is not None:
            properties[normalize_spaces(label.get_text(" ", strip=True))] = normalize_spaces(value.get_text(" ", strip=True))
    return parse_creature(html, source), properties


def fetch_text(url: str, retries: int) -> str:
    last_error: Exception | None = None
    for _attempt in range(max(1, retries)):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error) if last_error else "unknown fetch error")


def fetch_parse_importable(item: tuple[str, str], source: str, retries: int) -> tuple[dict[str, Any] | None, str | None]:
    expected_name, url = item
    try:
        creature, properties = parse_creature_with_properties(fetch_text(url, retries), source)
    except Exception as exc:
        return None, f"{expected_name}\t{url}\tfetch/parse failed: {type(exc).__name__}: {exc}"
    reason = skip_reason(creature, properties)
    if reason:
        return None, f"{expected_name}\t{url}\t{reason}"
    if creature_key(creature.get("name", "")) != creature_key(expected_name):
        return None, f"{expected_name}\t{url}\tname mismatch parsed={creature.get('name')!r}"
    return creature, None


def write_skip_report(path: Path, skipped: list[str], dry_run: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "Skipped dr-eigenvalue bestiary import entries",
        f"Mode: {'dry-run' if dry_run else 'import'}",
        "Format: name<TAB>url<TAB>reason",
        "",
    ]
    path.write_text("\n".join(header + sorted(skipped)) + "\n", encoding="utf-8")


def run_bulk(args: argparse.Namespace) -> int:
    bestiary_path = Path(args.bestiary).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    payload, creatures = load_bestiary(bestiary_path)
    existing_keys = {creature_key(item.get("name", "")) for item in creatures if isinstance(item, dict)}
    missing = [(name, url) for name, url in index_creatures() if creature_key(name) not in existing_keys]

    imported: list[dict[str, Any]] = []
    skipped: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(fetch_parse_importable, item, args.source, args.retries): item
            for item in missing
        }
        for future in as_completed(futures):
            creature, skip = future.result()
            if creature is not None:
                imported.append(creature)
            elif skip is not None:
                skipped.append(skip)

    new_keys: set[str] = set()
    duplicate_imports: list[str] = []
    deduped_imports: list[dict[str, Any]] = []
    for creature in sorted(imported, key=lambda item: creature_key(item.get("name", ""))):
        key = creature_key(creature.get("name", ""))
        if key in existing_keys or key in new_keys:
            duplicate_imports.append(f"{creature.get('name', '')}\tduplicate after parsing")
            continue
        new_keys.add(key)
        deduped_imports.append(creature)
    skipped.extend(duplicate_imports)

    write_skip_report(report_path, skipped, args.dry_run)
    if not args.dry_run:
        creatures.extend(deduped_imports)
        creatures.sort(key=lambda item: creature_key(item.get("name", "")) if isinstance(item, dict) else "")
        bestiary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        f"missing={len(missing)} importable={len(deduped_imports)} "
        f"skipped={len(skipped)} dry_run={args.dry_run} report={report_path}"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.bulk:
        return run_bulk(args)
    if not args.slug_or_url:
        raise SystemExit("Provide a slug/URL or use --bulk.")
    response = requests.get(creature_url(args.slug_or_url), timeout=30)
    response.raise_for_status()
    creature = parse_creature(response.text, args.source)
    print(json.dumps(creature, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
