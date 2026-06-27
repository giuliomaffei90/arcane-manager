from __future__ import annotations

from .platform import Any, Path, SequenceMatcher, dataclass, json
from .logging_utils import log
from .resources import MAX_ALIAS_CHARS, MAX_ALIASES_PER_SPELL, MAX_SHORT_FIELD_CHARS, MAX_SPELL_FILE_BYTES, MAX_SPELLS, MAX_TEXT_FIELD_CHARS
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
    hp: int
    speed: str
    stats: tuple[int, int, int, int, int, int]
    cr: str
    traits: tuple[dict[str, Any], ...]
    actions: tuple[dict[str, Any], ...]
    legendary_actions: tuple[dict[str, Any], ...]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Creature":
        stats = raw.get("stats", [])
        if not isinstance(stats, list):
            stats = []
        padded_stats = [int(value or 10) for value in stats[:6]]
        padded_stats.extend([10] * (6 - len(padded_stats)))
        return cls(
            name=clean_text(raw.get("name", ""), MAX_SHORT_FIELD_CHARS),
            source=clean_text(raw.get("source", ""), MAX_SHORT_FIELD_CHARS),
            size=clean_text(raw.get("size", ""), MAX_SHORT_FIELD_CHARS),
            creature_type=clean_text(raw.get("type", ""), MAX_SHORT_FIELD_CHARS),
            alignment=clean_text(raw.get("alignment", ""), MAX_SHORT_FIELD_CHARS),
            ac=raw.get("ac", ""),
            hp=int(raw.get("hp") or 0),
            speed=clean_text(raw.get("speed", ""), MAX_SHORT_FIELD_CHARS),
            stats=tuple(padded_stats),  # type: ignore[arg-type]
            cr=clean_text(raw.get("cr", ""), MAX_SHORT_FIELD_CHARS),
            traits=tuple(item for item in raw.get("traits", []) if isinstance(item, dict)),
            actions=tuple(item for item in raw.get("actions", []) if isinstance(item, dict)),
            legendary_actions=tuple(item for item in raw.get("legendary_actions", []) if isinstance(item, dict)),
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


def creature_summary(creature: Creature) -> str:
    return f"{creature.name}   HP: {creature.hp}   AC: {display_ac(creature.ac)}   CR: {creature.cr}"


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

    matched: list[Creature] = []
    compact_query = normalized_query.replace(" ", "")
    for creature in filtered_creatures:
        normalized_name = normalize(creature.name)
        compact_name = normalized_name.replace(" ", "")
        if normalized_name == normalized_query:
            score = 1.0
        elif normalized_name.startswith(normalized_query):
            score = 0.94
        elif normalized_query in normalized_name:
            score = 0.86
        elif compact_query and compact_query in compact_name:
            score = 0.82
        else:
            score = SequenceMatcher(None, normalized_query, normalized_name).ratio() * 0.78
        if score >= 0.45:
            matched.append(creature)
    matched.sort(key=lambda creature: normalize(creature.name))
    return matched if limit is None else matched[:limit]
