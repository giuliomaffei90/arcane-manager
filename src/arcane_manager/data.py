from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .platform import Any, Path, SequenceMatcher, dataclass, json, re
from .logging_utils import log
from .resources import MAX_ALIAS_CHARS, MAX_ALIASES_PER_SPELL, MAX_ITEM_FILE_BYTES, MAX_ITEMS, MAX_SHORT_FIELD_CHARS, MAX_SPELL_FILE_BYTES, MAX_SPELLS, MAX_TEXT_FIELD_CHARS
from .text_utils import clean_text, clean_text_list, normalize


@dataclass(frozen=True)
class Spell:
    id: str
    name: str
    italian_name: str
    aliases: tuple[str, ...]
    level: str
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    higher_levels: str = ""
    spell_lists: tuple[str, ...] = ()
    source: str = ""
    ritual: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Spell":
        if not isinstance(raw, dict):
            raise ValueError("Spell entries must be JSON objects.")

        raw_names = raw.get("names", {})
        names = raw_names if isinstance(raw_names, dict) else {}
        aliases = list(clean_text_list(raw.get("aliases", []), MAX_ALIASES_PER_SPELL, MAX_ALIAS_CHARS))
        for value in (raw.get("name"), names.get("en"), names.get("it")):
            if value:
                aliases.append(clean_text(value, MAX_ALIAS_CHARS))

        visible_name = clean_text(raw.get("name") or names.get("it") or names.get("en"), MAX_SHORT_FIELD_CHARS)
        if not visible_name:
            raise ValueError(f"Spell entry without a name: {raw!r}")

        return cls(
            id=clean_text(raw.get("id") or normalize(visible_name).replace(" ", "-"), MAX_SHORT_FIELD_CHARS),
            name=visible_name,
            italian_name=clean_text(names.get("it", ""), MAX_SHORT_FIELD_CHARS),
            aliases=tuple(dict.fromkeys(a.strip() for a in aliases if a.strip())),
            level=clean_text(raw.get("level", ""), MAX_SHORT_FIELD_CHARS),
            school=clean_text(raw.get("school", ""), MAX_SHORT_FIELD_CHARS),
            casting_time=clean_text(raw.get("casting_time", ""), MAX_SHORT_FIELD_CHARS),
            range=clean_text(raw.get("range", ""), MAX_SHORT_FIELD_CHARS),
            components=clean_text(raw.get("components", ""), MAX_SHORT_FIELD_CHARS),
            duration=clean_text(raw.get("duration", ""), MAX_SHORT_FIELD_CHARS),
            description=clean_text(raw.get("description", ""), MAX_TEXT_FIELD_CHARS),
            higher_levels=clean_text(raw.get("higher_levels", ""), MAX_TEXT_FIELD_CHARS),
            spell_lists=clean_text_list(raw.get("spell_lists", []), 40, MAX_SHORT_FIELD_CHARS),
            source=clean_text(raw.get("source", ""), MAX_SHORT_FIELD_CHARS),
            ritual=bool(raw.get("ritual", False)),
        )


def load_spells(path: Path) -> tuple[list[Spell], dict[str, Spell]]:
    path = path.expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Spell file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Spell path is not a regular file: {path}")
    if path.stat().st_size > MAX_SPELL_FILE_BYTES:
        raise ValueError(f"Spell file is too large: {path}")

    with path.open("r", encoding="utf-8") as handle:
        try:
            payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid spell JSON: {exc}") from exc

    raw_spells = payload.get("spells", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_spells, list):
        raise ValueError("Spell file must contain a list or an object with a 'spells' list.")
    if len(raw_spells) > MAX_SPELLS:
        raise ValueError(f"Spell file contains too many entries: {len(raw_spells)}")

    spells = [Spell.from_dict(item) for item in raw_spells]
    lookup: dict[str, Spell] = {}
    for spell in spells:
        for alias in spell.aliases:
            key = normalize(alias)
            if key:
                lookup[key] = spell
    return spells, lookup


@dataclass(frozen=True)
class Creature:
    name: str
    source: str
    size: str
    creature_type: str
    alignment: str
    ac: int | str
    hp: int | str
    speed: str
    stats: tuple[int, int, int, int, int, int]
    cr: str
    traits: tuple[dict[str, Any], ...]
    actions: tuple[dict[str, Any], ...]
    bonus_actions: tuple[dict[str, Any], ...]
    reactions: tuple[dict[str, Any], ...]
    legendary_actions: tuple[dict[str, Any], ...]
    mythic_actions: tuple[dict[str, Any], ...]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Creature":
        stats = raw.get("stats", [])
        if not isinstance(stats, list):
            stats = []
        padded_stats = [int(value or 10) for value in stats[:6]]
        padded_stats.extend([10] * (6 - len(padded_stats)))
        raw_hp = raw.get("hp") or 0
        try:
            hp: int | str = int(raw_hp)
        except (TypeError, ValueError):
            hp = clean_text(raw_hp, MAX_SHORT_FIELD_CHARS)
        return cls(
            name=clean_text(raw.get("name", ""), MAX_SHORT_FIELD_CHARS),
            source=clean_text(raw.get("source", ""), MAX_SHORT_FIELD_CHARS),
            size=clean_text(raw.get("size", ""), MAX_SHORT_FIELD_CHARS),
            creature_type=clean_text(raw.get("type", ""), MAX_SHORT_FIELD_CHARS),
            alignment=clean_text(raw.get("alignment", ""), MAX_SHORT_FIELD_CHARS),
            ac=raw.get("ac", ""),
            hp=hp,
            speed=clean_text(raw.get("speed", ""), MAX_SHORT_FIELD_CHARS),
            stats=tuple(padded_stats),  # type: ignore[arg-type]
            cr=clean_text(raw.get("cr", ""), MAX_SHORT_FIELD_CHARS),
            traits=tuple(item for item in raw.get("traits", []) if isinstance(item, dict)),
            actions=tuple(item for item in raw.get("actions", []) if isinstance(item, dict)),
            bonus_actions=tuple(item for item in raw.get("bonus_actions", []) if isinstance(item, dict)),
            reactions=tuple(item for item in raw.get("reactions", []) if isinstance(item, dict)),
            legendary_actions=tuple(item for item in raw.get("legendary_actions", []) if isinstance(item, dict)),
            mythic_actions=tuple(item for item in raw.get("mythic_actions", []) if isinstance(item, dict)),
            raw=dict(raw),
        )


def load_bestiary(path: Path) -> list[Creature]:
    path = path.expanduser()
    if not path.exists():
        log(f"Bestiary file not found: {path}")
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    raw_creatures = payload.get("creatures", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_creatures, list):
        raise ValueError("Bestiary file must contain a list or an object with a 'creatures' list.")
    creatures = [Creature.from_dict(item) for item in raw_creatures if isinstance(item, dict)]
    return [creature for creature in creatures if creature.name]


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def display_ac(value: int | str) -> str:
    if isinstance(value, int):
        return str(value)
    return clean_text(value, MAX_SHORT_FIELD_CHARS) or "?"


def display_hp(value: int | str) -> str:
    if isinstance(value, int):
        return str(value)
    return clean_text(value, MAX_SHORT_FIELD_CHARS) or "0"


def numeric_hp(value: int | str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def display_cr(value: str) -> str:
    return clean_text(value, MAX_SHORT_FIELD_CHARS) or "-"


def creature_summary(creature: Creature) -> str:
    return f"{creature.name}   HP: {display_hp(creature.hp)}   AC: {display_ac(creature.ac)}   CR: {display_cr(creature.cr)}"


def cr_sort_value(value: str) -> float:
    text = clean_text(value, MAX_SHORT_FIELD_CHARS)
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        try:
            return float(numerator) / float(denominator)
        except (TypeError, ValueError, ZeroDivisionError):
            return 999.0
    try:
        return float(text)
    except (TypeError, ValueError):
        return 999.0


def creature_cr_values(creatures: list[Creature]) -> list[str]:
    values = {creature.cr for creature in creatures if creature.cr}
    return sorted(values, key=lambda value: (cr_sort_value(value), value))


def search_creatures(query: str, creatures: list[Creature], cr_filter: str | None = None, limit: int | None = None) -> list[Creature]:
    filtered_creatures = [creature for creature in creatures if not cr_filter or creature.cr == cr_filter]
    normalized_query = normalize(query)
    if not normalized_query:
        results = sorted(filtered_creatures, key=lambda creature: normalize(creature.name))
        return results if limit is None else results[:limit]

    query_words = normalized_query.split()
    ranked: list[tuple[int, str, Creature]] = []
    for creature in filtered_creatures:
        normalized_name = normalize(creature.name)
        name_words = normalized_name.split()
        if not query_words or not all(
            any(name_word == query_word or name_word.startswith(query_word) for name_word in name_words)
            for query_word in query_words
        ):
            continue

        if normalized_name == normalized_query:
            tier = 0
        elif normalized_name.startswith(normalized_query):
            tier = 1
        elif all(query_word in name_words for query_word in query_words):
            tier = 2
        else:
            tier = 3
        ranked.append((tier, normalized_name, creature))

    ranked.sort(key=lambda item: (item[0], item[1]))
    results = [creature for _tier, _name, creature in ranked]
    return results if limit is None else results[:limit]


@dataclass(frozen=True)
class ItemVariant:
    id: str
    name: str
    category: str
    description: str
    cost: str
    ac: str = ""
    classification: str = ""
    damage: str = ""
    properties: str = ""
    rarity: str = ""
    source_page: int = 0
    source: str = ""
    source_abbreviation: str = ""
    source_commit: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ItemVariant":
        if not isinstance(raw, dict):
            raise ValueError("Item variant entries must be JSON objects.")
        name = clean_text(raw.get("name", ""), MAX_SHORT_FIELD_CHARS)
        if not name:
            raise ValueError(f"Item variant without a name: {raw!r}")
        try:
            source_page = int(raw.get("source_page") or 0)
        except (TypeError, ValueError):
            source_page = 0
        return cls(
            id=clean_text(raw.get("id") or normalize(name).replace(" ", "-"), MAX_SHORT_FIELD_CHARS),
            name=name,
            category=clean_text(raw.get("category", ""), MAX_SHORT_FIELD_CHARS),
            description=clean_text(raw.get("description", ""), MAX_TEXT_FIELD_CHARS),
            cost=clean_text(raw.get("cost", ""), MAX_SHORT_FIELD_CHARS),
            ac=clean_text(raw.get("ac", ""), MAX_SHORT_FIELD_CHARS),
            classification=clean_text(raw.get("classification", ""), MAX_SHORT_FIELD_CHARS),
            damage=clean_text(raw.get("damage", ""), MAX_SHORT_FIELD_CHARS),
            properties=clean_text(raw.get("properties", ""), MAX_SHORT_FIELD_CHARS),
            rarity=clean_text(raw.get("rarity", ""), MAX_SHORT_FIELD_CHARS),
            source_page=source_page,
            source=clean_text(raw.get("source", ""), MAX_SHORT_FIELD_CHARS),
            source_abbreviation=clean_text(raw.get("source_abbreviation", ""), MAX_SHORT_FIELD_CHARS),
            source_commit=clean_text(raw.get("source_commit", ""), MAX_SHORT_FIELD_CHARS),
        )


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    category: str
    description: str
    cost: str
    ac: str = ""
    classification: str = ""
    damage: str = ""
    properties: str = ""
    rarity: str = ""
    source_page: int = 0
    source: str = ""
    source_abbreviation: str = ""
    source_commit: str = ""
    variants: tuple[ItemVariant, ...] = ()
    selected_variant_id: str = ""
    variant_only: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Item":
        if not isinstance(raw, dict):
            raise ValueError("Item entries must be JSON objects.")
        base = ItemVariant.from_dict(raw)
        variants = tuple(
            ItemVariant.from_dict(item)
            for item in raw.get("variants", [])
            if isinstance(item, dict)
        )
        return cls(
            id=base.id,
            name=base.name,
            category=base.category,
            description=base.description,
            cost=base.cost,
            ac=base.ac,
            classification=base.classification,
            damage=base.damage,
            properties=base.properties,
            rarity=base.rarity,
            source_page=base.source_page,
            source=base.source,
            source_abbreviation=base.source_abbreviation,
            source_commit=base.source_commit,
            variants=variants,
            variant_only=bool(raw.get("variant_only", False)),
        )

    def with_selected_variant(self, variant_id: str) -> "Item":
        return Item(
            id=self.id,
            name=self.name,
            category=self.category,
            description=self.description,
            cost=self.cost,
            ac=self.ac,
            classification=self.classification,
            damage=self.damage,
            properties=self.properties,
            rarity=self.rarity,
            source_page=self.source_page,
            source=self.source,
            source_abbreviation=self.source_abbreviation,
            source_commit=self.source_commit,
            variants=self.variants,
            selected_variant_id=variant_id,
            variant_only=self.variant_only,
        )


def load_items(path: Path) -> list[Item]:
    path = path.expanduser()
    if not path.exists():
        log(f"Items file not found: {path}")
        return []
    if not path.is_file():
        raise ValueError(f"Items path is not a regular file: {path}")
    if path.stat().st_size > MAX_ITEM_FILE_BYTES:
        raise ValueError(f"Items file is too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        try:
            payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid items JSON: {exc}") from exc
    raw_items = payload.get("items", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_items, list):
        raise ValueError("Items file must contain a list or an object with an 'items' list.")
    if len(raw_items) > MAX_ITEMS:
        raise ValueError(f"Items file contains too many entries: {len(raw_items)}")
    items = [Item.from_dict(item) for item in raw_items if isinstance(item, dict)]
    return [item for item in items if item.name]


def item_category_values(items: list[Item]) -> list[str]:
    values = {item.category for item in items if item.category}
    return sorted(values, key=lambda value: normalize(value))


def item_summary(item: Item) -> str:
    parts = [item.name]
    if item.category:
        parts.append(item.category)
    if item.cost:
        parts.append(item.cost)
    return " - ".join(parts)


def item_display_cost(cost: str) -> str:
    return cost.strip() if cost and cost.strip() else "-"


def item_cost_to_copper(cost: str) -> int | None:
    text = str(cost or "").strip()
    if not text:
        return None
    if not re.fullmatch(r"(?:\d+(?:\.\d+)?\s+(?:Gold|Silver|Copper)\s*)+", text, re.IGNORECASE):
        return None
    multipliers = {"gold": Decimal(100), "silver": Decimal(10), "copper": Decimal(1)}
    total = Decimal(0)
    try:
        for value_text, unit_text in re.findall(r"(\d+(?:\.\d+)?)\s+(Gold|Silver|Copper)", text, re.IGNORECASE):
            total += Decimal(value_text) * multipliers[unit_text.lower()]
    except InvalidOperation:
        return None
    if total != total.to_integral_value():
        return None
    return int(total)


def copper_value_text(copper: int) -> str:
    copper = max(0, int(copper))
    gold, remainder = divmod(copper, 100)
    silver, copper = divmod(remainder, 10)
    parts = []
    if gold:
        parts.append(f"{gold} Gold")
    if silver:
        parts.append(f"{silver} Silver")
    if copper or not parts:
        parts.append(f"{copper} Copper")
    return " ".join(parts)


def item_value_text(cost: str) -> str:
    return item_display_cost(cost)


def item_display_properties(properties: str, description: str) -> str:
    parts = [part.strip() for part in str(properties or "").split(",") if part.strip()]
    if not parts:
        return ""
    description_text = str(description or "")
    visible_parts = []
    for part in parts:
        normalized_part = normalize(part)
        if normalized_part == "none":
            continue
        if normalized_part.startswith(("weight ", "range ", "requires attunement")):
            visible_parts.append(part)
            continue
        label = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
        if label and re.search(rf"(?:^|\n\n){re.escape(label)}\.", description_text, re.IGNORECASE):
            continue
        visible_parts.append(part)
    return ", ".join(visible_parts)


def item_property_rule_labels(properties: str) -> set[str]:
    labels = set()
    for part in (part.strip() for part in str(properties or "").split(",") if part.strip()):
        normalized_part = normalize(part)
        if not normalized_part or normalized_part == "none":
            continue
        if normalized_part.startswith("weight "):
            continue
        if normalized_part.startswith("range "):
            labels.add("range")
            continue
        if normalized_part.startswith("requires attunement"):
            continue
        label = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
        normalized_label = normalize(label)
        if normalized_label:
            labels.add(normalized_label)
    return labels


def item_property_rule_display_names(properties: str) -> dict[str, str]:
    display_names = {}
    for part in (part.strip() for part in str(properties or "").split(",") if part.strip()):
        normalized_part = normalize(part)
        if not normalized_part or normalized_part == "none":
            continue
        if normalized_part.startswith("weight ") or normalized_part.startswith("requires attunement"):
            continue
        if normalized_part.startswith("range "):
            display_names["range"] = part
            continue
        label = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
        normalized_label = normalize(label)
        if normalized_label:
            display_names[normalized_label] = part
    return display_names


def item_description_sections(description: str, properties: str) -> tuple[str, str]:
    property_display_names = item_property_rule_display_names(properties)
    if not property_display_names:
        return str(description or "").strip(), ""
    practical_parts = []
    property_parts = []
    in_property_block = False
    for paragraph in [part.strip() for part in str(description or "").split("\n\n") if part.strip()]:
        heading = paragraph.split(".", 1)[0].strip()
        normalized_heading = normalize(heading)
        if normalized_heading in property_display_names:
            rest = paragraph.split(".", 1)[1] if "." in paragraph else ""
            display_name = property_display_names[normalized_heading]
            property_parts.append(f"{display_name}{rest}" if display_name.endswith(".") else f"{display_name}.{rest}")
            in_property_block = True
        elif in_property_block:
            property_parts.append(paragraph)
        else:
            practical_parts.append(paragraph)
    return "\n\n".join(practical_parts), "\n\n".join(property_parts)


def item_practical_description(item: Item | ItemVariant) -> str:
    practical_description, _property_description = item_description_sections(item.description, item.properties)
    if practical_description:
        return practical_description
    if item.category == "Weapon":
        classification = normalize(item.classification)
        if "martial" in classification and "melee" in classification:
            return f"A {item.name.lower()} is a martial melee weapon."
        if "martial" in classification and "ranged" in classification:
            return f"A {item.name.lower()} is a martial ranged weapon."
        if "simple" in classification and "melee" in classification:
            return f"A {item.name.lower()} is a simple melee weapon."
        if "simple" in classification and "ranged" in classification:
            return f"A {item.name.lower()} is a simple ranged weapon."
        return f"A {item.name.lower()} is a weapon."
    return ""


def merchant_value_text(cost: str) -> str:
    copper = item_cost_to_copper(cost)
    if copper is None:
        return ""
    return copper_value_text((copper * 60) // 100)


def item_cost_color_name(cost: str) -> str:
    if not cost or not cost.strip() or cost.strip() == "-":
        return "no_cost"
    copper = item_cost_to_copper(cost)
    if copper is None:
        return "gold"
    if copper >= 100:
        return "gold"
    if copper >= 10:
        return "muted"
    return "copper"


def search_items(query: str, items: list[Item], category_filter: str | None = None, limit: int | None = None) -> list[Item]:
    filtered_items = [item for item in items if not category_filter or item.category == category_filter]
    normalized_query = normalize(query)
    if not normalized_query:
        results = sorted(filtered_items, key=lambda item: normalize(item.name))
        return results if limit is None else results[:limit]

    matched: list[tuple[float, str, Item]] = []
    compact_query = normalized_query.replace(" ", "")
    for item in filtered_items:
        best_score = 0.0
        best_variant_id = ""
        for candidate in (item, *item.variants):
            searchable_values = [
                candidate.name,
                candidate.category,
                candidate.cost,
                candidate.rarity,
                candidate.classification,
                candidate.damage,
                candidate.properties,
                candidate.description,
                candidate.source,
                candidate.source_abbreviation,
            ]
            normalized_name = normalize(candidate.name)
            compact_name = normalized_name.replace(" ", "")
            haystack = normalize(" ".join(value for value in searchable_values if value))
            if normalized_name == normalized_query:
                score = 1.0
            elif normalized_name.startswith(normalized_query):
                score = 0.94
            elif normalized_query in normalized_name:
                score = 0.88
            elif compact_query and compact_query in compact_name:
                score = 0.84
            elif normalized_query in haystack:
                score = 0.72
            else:
                score = SequenceMatcher(None, normalized_query, normalized_name).ratio() * 0.55
            if score > best_score:
                best_score = score
                best_variant_id = candidate.id if isinstance(candidate, ItemVariant) else ""
        if best_score >= 0.45:
            matched.append((best_score, best_variant_id, item.with_selected_variant(best_variant_id)))
    matched.sort(key=lambda pair: (-pair[0], normalize(pair[2].name), pair[1]))
    results = [item for _score, _variant_id, item in matched]
    return results if limit is None else results[:limit]
