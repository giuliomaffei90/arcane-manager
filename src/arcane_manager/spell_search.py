from __future__ import annotations

from .platform import SequenceMatcher
from .data import Spell
from .text_utils import normalize, normalize_transcript_for_matching

SPELL_LEVEL_ORDER = (
    "Cantrip",
    "1st Level",
    "2nd Level",
    "3rd Level",
    "4th Level",
    "5th Level",
    "6th Level",
    "7th Level",
    "8th Level",
    "9th Level",
)

SPELL_SCHOOL_ORDER = (
    "Abjuration",
    "Conjuration",
    "Divination",
    "Enchantment",
    "Evocation",
    "Illusion",
    "Necromancy",
    "Transmutation",
)


def spell_level_values(spells: list[Spell]) -> list[str]:
    values = {spell.level for spell in spells if spell.level}
    return [level for level in SPELL_LEVEL_ORDER if level in values]


def spell_school_values(spells: list[Spell]) -> list[str]:
    values = {spell.school for spell in spells if spell.school}
    ordered = [school for school in SPELL_SCHOOL_ORDER if school in values]
    extras = sorted(values - set(SPELL_SCHOOL_ORDER), key=normalize)
    return [*ordered, *extras]


def _spell_name_match(normalized_query: str, normalized_name: str, compact_query: str) -> tuple[int, float] | None:
    compact_name = normalized_name.replace(" ", "")
    if normalized_name == normalized_query:
        return (0, 1.0)
    if normalized_name.startswith(normalized_query):
        return (1, 0.94)
    if normalized_query in normalized_name.split() or f" {normalized_query} " in f" {normalized_name} ":
        return (2, 0.86)
    if compact_query and compact_query in compact_name:
        return (3, 0.82)

    score = SequenceMatcher(None, normalized_query, normalized_name).ratio()
    query_length = len(compact_query)
    name_length = len(compact_name)
    length_gap = abs(query_length - name_length)
    if score >= 0.78 and length_gap <= max(2, query_length // 4):
        return (4, score)
    return None


def search_spells(
    query: str,
    spells: list[Spell],
    limit: int | None = 8,
    level_filter: str | None = None,
    school_filter: str | None = None,
) -> list[Spell]:
    filtered_spells = [
        spell
        for spell in spells
        if (not level_filter or spell.level == level_filter)
        and (not school_filter or spell.school == school_filter)
    ]
    normalized_query = normalize_transcript_for_matching(query)
    if not normalized_query:
        results = sorted(filtered_spells, key=lambda spell: normalize(spell.name))
        return results if limit is None else results[:limit]

    ranked: list[tuple[int, float, int, str, Spell]] = []
    compact_query = normalized_query.replace(" ", "")
    for spell in filtered_spells:
        names = [spell.name, spell.italian_name, *spell.aliases]
        best_tier = 9999
        best_score = -1.0
        best_length = 9999
        for name in names:
            normalized_name = normalize(name)
            if not normalized_name:
                continue
            match = _spell_name_match(normalized_query, normalized_name, compact_query)
            if match is None:
                continue
            tier, score = match
            if (
                tier < best_tier
                or (tier == best_tier and score > best_score)
                or (tier == best_tier and score == best_score and len(normalized_name) < best_length)
            ):
                best_tier = tier
                best_score = score
                best_length = len(normalized_name)

        if best_tier < 9999:
            ranked.append((best_tier, best_score, best_length, spell.name, spell))

    ranked.sort(key=lambda item: (item[0], -item[1], item[2], item[3]))
    results = [spell for _tier, _score, _length, _name, spell in ranked]
    return results if limit is None else results[:limit]
