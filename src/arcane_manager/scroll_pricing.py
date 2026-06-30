from __future__ import annotations

from .platform import dataclass, re
from .data import Spell
from .text_utils import normalize

SCROLL_LEVEL_LABELS = {
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

SCROLL_PRICE_RANGES = {
    0: ("Common", 50, 100),
    1: ("Common", 50, 100),
    2: ("Uncommon", 101, 500),
    3: ("Uncommon", 101, 500),
    4: ("Rare", 501, 5000),
    5: ("Rare", 501, 5000),
    6: ("Very Rare", 5001, 50000),
    7: ("Very Rare", 5001, 50000),
    8: ("Very Rare", 5001, 50000),
    9: ("Legendary", 50001, 100000),
}

UTILITY_TIERS = ("Low", "Standard", "High", "Premium")
UTILITY_PRICE_POSITIONS = {
    "Low": 0.0,
    "Standard": 0.5,
    "High": 0.8,
    "Premium": 1.0,
}

SCROLL_LEVEL_PRICE_BANDS = {
    0: ("Common", 50, 75),
    1: ("Common", 76, 100),
    2: ("Uncommon", 101, 300),
    3: ("Uncommon", 301, 500),
    4: ("Rare", 501, 2750),
    5: ("Rare", 2751, 5000),
    6: ("Very Rare", 5001, 20000),
    7: ("Very Rare", 20001, 35000),
    8: ("Very Rare", 35001, 50000),
    9: ("Legendary", 50001, 100000),
}

CURATED_UTILITY_TIERS = {
    "alarm": "Low",
    "animate dead": "High",
    "banishment": "Premium",
    "bless": "High",
    "booming blade": "High",
    "counterspell": "Premium",
    "cure wounds": "High",
    "detect magic": "Standard",
    "dispel magic": "High",
    "eldritch blast": "Premium",
    "faerie fire": "High",
    "find familiar": "Premium",
    "fire bolt": "High",
    "fireball": "Premium",
    "fly": "Premium",
    "guidance": "High",
    "healing word": "Premium",
    "hold monster": "Premium",
    "hold person": "High",
    "hypnotic pattern": "Premium",
    "mage armor": "High",
    "magic missile": "High",
    "mass cure wounds": "High",
    "misty step": "Premium",
    "pass without trace": "Premium",
    "polymorph": "Premium",
    "prestidigitation": "Low",
    "raise dead": "Premium",
    "revivify": "Premium",
    "shield": "Premium",
    "silvery barbs": "Premium",
    "spare the dying": "Low",
    "spirit guardians": "Premium",
    "suggestion": "High",
    "teleport": "Premium",
    "tiny hut": "High",
    "true strike": "Low",
    "wish": "Premium",
}

PREMIUM_KEYWORDS = (
    "resurrect",
    "return a dead",
    "dead creature",
    "teleport",
    "counterspell",
    "reaction",
    "incapacitated",
    "paralyzed",
    "stunned",
    "banish",
    "advantage",
)

HIGH_KEYWORDS = (
    "regain hit points",
    "healing",
    "temporary hit points",
    "saving throw",
    "restrained",
    "frightened",
    "charmed",
    "invisible",
    "fly",
    "increase your ac",
    "resistance",
    "area",
    "radius",
    "cone",
    "line",
)

LOW_KEYWORDS = (
    "harmless sensory effect",
    "minor sensory effect",
    "clean or soil",
    "flavor",
    "color",
    "symbol",
    "entertain",
)


@dataclass(frozen=True)
class ScrollPrice:
    spell: Spell
    base_level: int
    scroll_level: int
    rarity: str
    utility_tier: str
    price_gp: int


def spell_level_number(spell: Spell) -> int:
    level = normalize(spell.level)
    if level == "cantrip":
        return 0
    match = re.search(r"\d+", level)
    if match is None:
        return 0
    return max(0, min(9, int(match.group(0))))


def valid_scroll_levels_for_spell(spell: Spell) -> list[int]:
    base_level = spell_level_number(spell)
    if base_level <= 0:
        return [0]
    return list(range(base_level, 10))


def scroll_level_label(level: int) -> str:
    return SCROLL_LEVEL_LABELS.get(int(level), "")


def scroll_rarity_for_level(level: int) -> str:
    rarity, _minimum, _maximum = SCROLL_PRICE_RANGES[int(level)]
    return rarity


def utility_tier_for_spell(spell: Spell) -> str:
    normalized_name = normalize(spell.name)
    if normalized_name in CURATED_UTILITY_TIERS:
        return CURATED_UTILITY_TIERS[normalized_name]

    text = normalize(" ".join((spell.name, spell.school, spell.description, spell.higher_levels)))
    score = 0
    if re.search(r"\d+d\d+", text):
        score += 1
    if "at higher levels" in text or "higher levels" in text:
        score += 1
    score += sum(1 for keyword in HIGH_KEYWORDS if keyword in text)
    score += sum(2 for keyword in PREMIUM_KEYWORDS if keyword in text)
    score -= sum(1 for keyword in LOW_KEYWORDS if keyword in text)
    if spell.ritual:
        score -= 1
    if normalize(spell.school) in {"evocation", "abjuration"} and score > 0:
        score += 1

    if score >= 5:
        return "Premium"
    if score >= 2:
        return "High"
    if score <= -1:
        return "Low"
    return "Standard"


def price_for_tier_and_level(utility_tier: str, scroll_level: int) -> tuple[str, int]:
    rarity, minimum, maximum = SCROLL_LEVEL_PRICE_BANDS[int(scroll_level)]
    position = UTILITY_PRICE_POSITIONS.get(utility_tier, UTILITY_PRICE_POSITIONS["Standard"])
    raw_price = minimum + (maximum - minimum) * position
    return rarity, _round_gp(raw_price, minimum, maximum)


def price_scroll(spell: Spell, scroll_level: int) -> ScrollPrice:
    base_level = spell_level_number(spell)
    valid_levels = valid_scroll_levels_for_spell(spell)
    selected_level = int(scroll_level)
    if selected_level not in valid_levels:
        selected_level = valid_levels[0]
    utility_tier = utility_tier_for_spell(spell)
    rarity, price_gp = price_for_tier_and_level(utility_tier, selected_level)
    return ScrollPrice(
        spell=spell,
        base_level=base_level,
        scroll_level=selected_level,
        rarity=rarity,
        utility_tier=utility_tier,
        price_gp=price_gp,
    )


def _round_gp(value: float, minimum: int, maximum: int) -> int:
    if value < 100:
        scale = 5
    elif value < 1000:
        scale = 10
    elif value < 10000:
        scale = 100
    elif value < 50000:
        scale = 500
    else:
        scale = 1000
    rounded = int(round(value / scale) * scale)
    return max(minimum, min(maximum, rounded))
