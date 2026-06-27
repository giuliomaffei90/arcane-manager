from __future__ import annotations

from .platform import NSUserDefaults, json, re

THEME_COLORS_PREF = "arcaneManagerThemeColors"


DEFAULT_THEME_RGB: dict[str, tuple[float, float, float]] = {
    "app_bg": (0x1A / 255, 0x1E / 255, 0x24 / 255),
    "panel": (0x1F / 255, 0x23 / 255, 0x2B / 255),
    "panel_alt": (0x1B / 255, 0x20 / 255, 0x27 / 255),
    "surface": (0x25 / 255, 0x29 / 255, 0x32 / 255),
    "surface_hover": (0x2B / 255, 0x30 / 255, 0x38 / 255),
    "surface_soft": (0x22 / 255, 0x26 / 255, 0x2E / 255),
    "border": (0x36 / 255, 0x3C / 255, 0x47 / 255),
    "border_soft": (0x2B / 255, 0x30 / 255, 0x38 / 255),
    "text": (0xE0 / 255, 0xE2 / 255, 0xE6 / 255),
    "text_strong": (0xF0 / 255, 0xF1 / 255, 0xF4 / 255),
    "muted": (0x8F / 255, 0x96 / 255, 0xA3 / 255),
    "link": (0x5A / 255, 0xA7 / 255, 0xF0 / 255),
    "dice": (0x6D / 255, 0xD6 / 255, 0x74 / 255),
    "gold": (0xE4 / 255, 0xC1 / 255, 0x61 / 255),
    "danger": (0xE1 / 255, 0x57 / 255, 0x63 / 255),
    "monster": (0xDC / 255, 0x5F / 255, 0x77 / 255),
    "blue_temp": (0x63 / 255, 0xA8 / 255, 0xF5 / 255),
    "selection": (0x3A / 255, 0x5F / 255, 0x94 / 255),
}


DEFAULT_DICE_THEME_RGB: dict[str, tuple[float, float, float]] = {
    "overlay_panel": (0x1F / 255, 0x23 / 255, 0x2B / 255),
    "overlay_border": (0x56 / 255, 0x60 / 255, 0x70 / 255),
    "overlay_stage": (0x1A / 255, 0x1E / 255, 0x24 / 255),
    "overlay_fallback": (0x1A / 255, 0x1E / 255, 0x24 / 255),
    "dice_red": (0xE1 / 255, 0x57 / 255, 0x63 / 255),
    "dice_text": (0xF0 / 255, 0xF1 / 255, 0xF4 / 255),
    "dice_green": (0x6D / 255, 0xD6 / 255, 0x74 / 255),
}


THEME_RGB = dict(DEFAULT_THEME_RGB)
DICE_THEME_RGB = dict(DEFAULT_DICE_THEME_RGB)


THEME_COLOR_LABELS = [
    ("app_bg", "App background"),
    ("panel", "Main panels"),
    ("panel_alt", "Sidebar panels"),
    ("surface_soft", "Soft surfaces"),
    ("surface", "Controls and rows"),
    ("surface_hover", "Hover and selected controls"),
    ("border_soft", "Subtle borders"),
    ("border", "Strong borders"),
    ("text", "Body text"),
    ("text_strong", "Heading text"),
    ("muted", "Muted text"),
    ("link", "Links"),
    ("dice", "Dice and HP"),
    ("gold", "Spell metadata"),
    ("danger", "Danger states"),
    ("monster", "Monster emphasis"),
    ("blue_temp", "Temporary HP"),
    ("selection", "Selection"),
]


DICE_THEME_COLOR_LABELS = [
    ("overlay_panel", "Overlay panel"),
    ("overlay_border", "Overlay border"),
    ("overlay_stage", "Stage tint"),
    ("overlay_fallback", "Fallback background"),
    ("dice_red", "Dice body"),
    ("dice_text", "Dice text"),
    ("dice_green", "Result green"),
]


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    values = [max(0, min(255, int(round(component * 255)))) for component in rgb]
    return "#{:02x}{:02x}{:02x}".format(*values)


def hex_to_rgb(value: str) -> tuple[float, float, float] | None:
    text = str(value or "").strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", text):
        return None
    return (
        int(text[1:3], 16) / 255.0,
        int(text[3:5], 16) / 255.0,
        int(text[5:7], 16) / 255.0,
    )


def color_to_hex(color) -> str:
    converted = color
    if hasattr(color, "colorUsingColorSpaceName_"):
        try:
            converted = color.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace") or color
        except Exception:
            converted = color
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(round(float(converted.redComponent()) * 255)))),
        max(0, min(255, int(round(float(converted.greenComponent()) * 255)))),
        max(0, min(255, int(round(float(converted.blueComponent()) * 255)))),
    )


def theme_snapshot() -> dict[str, dict[str, str]]:
    return {
        "app": {key: rgb_to_hex(THEME_RGB[key]) for key in DEFAULT_THEME_RGB},
        "dice": {key: rgb_to_hex(DICE_THEME_RGB[key]) for key in DEFAULT_DICE_THEME_RGB},
    }


def load_theme_overrides():
    THEME_RGB.clear()
    THEME_RGB.update(DEFAULT_THEME_RGB)
    DICE_THEME_RGB.clear()
    DICE_THEME_RGB.update(DEFAULT_DICE_THEME_RGB)
    raw = NSUserDefaults.standardUserDefaults().stringForKey_(THEME_COLORS_PREF)
    if not raw:
        return
    try:
        data = json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError):
        return
    if not isinstance(data, dict):
        return
    for section, target, defaults in (
        ("app", THEME_RGB, DEFAULT_THEME_RGB),
        ("dice", DICE_THEME_RGB, DEFAULT_DICE_THEME_RGB),
    ):
        values = data.get(section)
        if not isinstance(values, dict):
            continue
        for key in defaults:
            rgb = hex_to_rgb(str(values.get(key, "")))
            if rgb is not None:
                target[key] = rgb


def save_theme_overrides():
    defaults = NSUserDefaults.standardUserDefaults()
    defaults.setObject_forKey_(json.dumps(theme_snapshot()), THEME_COLORS_PREF)
    defaults.synchronize()


def reset_theme_overrides():
    THEME_RGB.clear()
    THEME_RGB.update(DEFAULT_THEME_RGB)
    DICE_THEME_RGB.clear()
    DICE_THEME_RGB.update(DEFAULT_DICE_THEME_RGB)
    defaults = NSUserDefaults.standardUserDefaults()
    defaults.removeObjectForKey_(THEME_COLORS_PREF)
    defaults.synchronize()


def css_rgba(name: str, alpha: float) -> str:
    red, green, blue = DICE_THEME_RGB[name]
    return f"rgba({int(round(red * 255))}, {int(round(green * 255))}, {int(round(blue * 255))}, {alpha:.2f})"


def dice_theme_payload() -> dict[str, str]:
    return {
        "overlayPanel": rgb_to_hex(DICE_THEME_RGB["overlay_panel"]),
        "overlayBorder": rgb_to_hex(DICE_THEME_RGB["overlay_border"]),
        "overlayStage": rgb_to_hex(DICE_THEME_RGB["overlay_stage"]),
        "overlayFallback": rgb_to_hex(DICE_THEME_RGB["overlay_fallback"]),
        "diceRed": rgb_to_hex(DICE_THEME_RGB["dice_red"]),
        "diceText": rgb_to_hex(DICE_THEME_RGB["dice_text"]),
        "diceGreen": rgb_to_hex(DICE_THEME_RGB["dice_green"]),
    }
