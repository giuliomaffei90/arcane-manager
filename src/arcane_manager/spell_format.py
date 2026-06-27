from __future__ import annotations

from .data import Spell
from .resources import MAX_SHORT_FIELD_CHARS
from .text_utils import clean_text, normalize

def format_spell_for_detail(spell: Spell) -> tuple[str, str, str]:
    title = spell.name
    meta_parts = [
        part
        for part in (
            spell.level,
            spell.school,
            spell.casting_time,
        )
        if part
    ]

    body_parts = []
    if spell.description.strip():
        body_parts.append(spell.description.strip())
    if spell.higher_levels.strip():
        body_parts.append(f"At Higher Levels. {spell.higher_levels.strip()}")

    return title, " | ".join(meta_parts) or "Spell found", "\n\n".join(body_parts)


def component_flags(components: str) -> dict[str, bool]:
    normalized = normalize(components)
    tokens = normalized.split()
    return {
        "V": "v" in tokens,
        "S": "s" in tokens,
        "M": "m" in tokens,
    }


def component_material(components: str) -> str:
    material = ""
    material_start = components.find("(")
    if material_start >= 0:
        material = components[material_start:].strip()
    return material
