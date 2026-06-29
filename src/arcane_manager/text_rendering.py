from __future__ import annotations

import re

from .platform import Any, NSMutableAttributedString, NSMutableParagraphStyle, NSFont, NSFontAttributeName, NSFontManager, NSForegroundColorAttributeName, NSItalicFontMask, NSMakeRange, NSParagraphStyleAttributeName
from .content_links import COMPONENT_BADGE_PATTERN, dice_ranges_for_body
from .data import Spell
from .spell_format import component_flags, component_material
from .ui.core import theme_color

MONSTER_SECTION_HEADINGS = {"traits", "spells", "actions", "bonus actions", "reactions", "legendary actions", "mythic actions"}

TABLE_SEPARATOR = "  |  "

def component_badge_text(components: str) -> str:
    flags = component_flags(components)
    badges = [f"[{key}]" if flags[key] else f"{key}-" for key in ("V", "S", "M")]
    material = component_material(components)
    suffix = f"  {material}" if material else ""
    return " ".join(badges) + suffix


def add_colored_ranges(attributed, ranges: list[tuple[int, int, Any]], color):
    for start, length, _payload in ranges:
        attributed.addAttribute_value_range_(NSForegroundColorAttributeName, color, NSMakeRange(start, length))


def attributed_spell_stats(lines: list[tuple[str, str]]):
    text = "\n".join(f"{label}: {value}" for label, value in lines)
    paragraph_style = NSMutableParagraphStyle.alloc().init()
    paragraph_style.setLineSpacing_(4.0)
    attributes = {
        NSFontAttributeName: NSFont.systemFontOfSize_(13),
        NSForegroundColorAttributeName: theme_color("text"),
        NSParagraphStyleAttributeName: paragraph_style,
    }
    attributed = NSMutableAttributedString.alloc().initWithString_attributes_(text, attributes)
    cursor = 0
    for label, value in lines:
        attributed.addAttribute_value_range_(
            NSFontAttributeName,
            NSFont.boldSystemFontOfSize_(13),
            NSMakeRange(cursor, len(label) + 1),
        )
        cursor += len(label) + len(value) + 3
    return attributed


def attributed_spell_body(body: str):
    dice_color = theme_color("dice")
    component_color = theme_color("gold")
    attributes = {
        NSFontAttributeName: NSFont.systemFontOfSize_(14),
        NSForegroundColorAttributeName: theme_color("text"),
    }
    attributed = NSMutableAttributedString.alloc().initWithString_attributes_(body, attributes)
    for marker in ("At Higher Levels.", "Classes:"):
        marker_start = body.find(marker)
        if marker_start >= 0:
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                NSFont.boldSystemFontOfSize_(15),
                NSMakeRange(marker_start, len(marker)),
            )

    for start, length, _expression in dice_ranges_for_body(body):
        attributed.addAttribute_value_range_(
            NSForegroundColorAttributeName,
            dice_color,
            NSMakeRange(start, length),
        )
    for match in COMPONENT_BADGE_PATTERN.finditer(body):
        attributed.addAttribute_value_range_(
            NSForegroundColorAttributeName,
            component_color,
            NSMakeRange(match.start(), match.end() - match.start()),
        )
        attributed.addAttribute_value_range_(
            NSFontAttributeName,
            NSFont.boldSystemFontOfSize_(14),
            NSMakeRange(match.start(), match.end() - match.start()),
        )
    return attributed


def _table_cells(line: str) -> list[str] | None:
    if " | " not in line:
        return None
    cells = [part.strip() for part in line.split("|")]
    if len(cells) < 2 or not any(cells):
        return None
    return cells


def _is_numeric_table_cell(value: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:[-–]\d+)?|0?\d|00|[A-Za-z]?\d+(?:[+-]\d+)?", value.strip()))


def _format_item_body_tables(body: str) -> tuple[str, list[dict[str, Any]]]:
    output_lines = []
    tables: list[dict[str, Any]] = []
    source_lines = body.splitlines()
    index = 0
    while index < len(source_lines):
        first_row = _table_cells(source_lines[index])
        if first_row is None:
            output_lines.append(source_lines[index])
            index += 1
            continue

        rows = [first_row]
        index += 1
        while index < len(source_lines):
            next_row = _table_cells(source_lines[index])
            if next_row is None:
                break
            rows.append(next_row)
            index += 1

        column_count = max(len(row) for row in rows)
        normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
        widths = [max(len(row[column]) for row in normalized_rows) for column in range(column_count)]
        start_line = len(output_lines)
        for row in normalized_rows:
            formatted_cells = []
            for column, cell in enumerate(row):
                if column == 0 and _is_numeric_table_cell(cell):
                    formatted_cells.append(cell.rjust(widths[column]))
                else:
                    formatted_cells.append(cell.ljust(widths[column]))
            output_lines.append(TABLE_SEPARATOR.join(formatted_cells).rstrip())
        tables.append({"start_line": start_line, "line_count": len(normalized_rows)})

    text = "\n".join(output_lines)
    line_starts = []
    cursor = 0
    for line in output_lines:
        line_starts.append(cursor)
        cursor += len(line) + 1
    for table in tables:
        start_line = table["start_line"]
        line_count = table["line_count"]
        start = line_starts[start_line]
        last_line = start_line + line_count - 1
        end = line_starts[last_line] + len(output_lines[last_line])
        table["start"] = start
        table["length"] = end - start
        table["header_start"] = start
        table["header_length"] = len(output_lines[start_line])
        separators = []
        for line_index in range(start_line, start_line + line_count):
            line = output_lines[line_index]
            search_start = 0
            while True:
                separator_index = line.find("|", search_start)
                if separator_index < 0:
                    break
                separators.append((line_starts[line_index] + separator_index, 1))
                search_start = separator_index + 1
        table["separators"] = separators
    return text, tables


def attributed_item_body(body: str):
    formatted_body, tables = _format_item_body_tables(body)
    dice_color = theme_color("dice")
    paragraph_style = NSMutableParagraphStyle.alloc().init()
    paragraph_style.setLineSpacing_(3.0)
    attributes = {
        NSFontAttributeName: NSFont.systemFontOfSize_(14),
        NSForegroundColorAttributeName: theme_color("text"),
        NSParagraphStyleAttributeName: paragraph_style,
    }
    attributed = NSMutableAttributedString.alloc().initWithString_attributes_(formatted_body, attributes)
    cursor = 0
    for line in formatted_body.splitlines():
        line_start = cursor
        cursor += len(line) + 1
        if line == "Properties:":
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                NSFont.boldSystemFontOfSize_(15),
                NSMakeRange(line_start, len(line)),
            )
            attributed.addAttribute_value_range_(
                NSForegroundColorAttributeName,
                theme_color("gold"),
                NSMakeRange(line_start, len(line)),
            )
        elif line.startswith("Damage:"):
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                NSFont.boldSystemFontOfSize_(14),
                NSMakeRange(line_start, len("Damage:")),
            )
            attributed.addAttribute_value_range_(
                NSForegroundColorAttributeName,
                theme_color("gold"),
                NSMakeRange(line_start, len("Damage:")),
            )
    for table in tables:
        attributed.addAttribute_value_range_(
            NSFontAttributeName,
            NSFont.monospacedSystemFontOfSize_weight_(13, 0),
            NSMakeRange(table["start"], table["length"]),
        )
        attributed.addAttribute_value_range_(
            NSFontAttributeName,
            NSFont.monospacedSystemFontOfSize_weight_(13, 0.35),
            NSMakeRange(table["header_start"], table["header_length"]),
        )
        attributed.addAttribute_value_range_(
            NSForegroundColorAttributeName,
            theme_color("gold"),
            NSMakeRange(table["header_start"], table["header_length"]),
        )
        for separator_start, separator_length in table["separators"]:
            attributed.addAttribute_value_range_(
                NSForegroundColorAttributeName,
                theme_color("muted"),
                NSMakeRange(separator_start, separator_length),
            )
    for start, length, _expression in dice_ranges_for_body(formatted_body):
        attributed.addAttribute_value_range_(
            NSForegroundColorAttributeName,
            dice_color,
            NSMakeRange(start, length),
        )
    return attributed, formatted_body


def attributed_monster_body(body: str, spell_ranges: list[tuple[int, int, Spell]], roll_ranges: list[tuple[int, int, str]] | None = None):
    dice_color = theme_color("dice")
    spell_color = theme_color("gold")
    base_font_size = 13.0
    base_font = NSFont.systemFontOfSize_(base_font_size)
    italic_font = NSFontManager.sharedFontManager().convertFont_toHaveTrait_(NSFont.userFontOfSize_(base_font_size), NSItalicFontMask)
    paragraph_style = NSMutableParagraphStyle.alloc().init()
    paragraph_style.setLineSpacing_(2.0)
    attributes = {
        NSFontAttributeName: base_font,
        NSForegroundColorAttributeName: theme_color("text"),
        NSParagraphStyleAttributeName: paragraph_style,
    }
    attributed = NSMutableAttributedString.alloc().initWithString_attributes_(body, attributes)
    cursor = 0
    for line in body.splitlines():
        start = cursor
        cursor += len(line) + 1
        if not line:
            continue
        if line.rstrip(":").lower() in MONSTER_SECTION_HEADINGS:
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                NSFont.boldSystemFontOfSize_(18),
                NSMakeRange(start, len(line)),
            )
            continue
        if line.endswith(":") and len(line) <= 80 and "." not in line:
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                NSFont.boldSystemFontOfSize_(15),
                NSMakeRange(start, len(line)),
            )
            continue
        lower_line = line.lower()
        first_period = line.find(".")
        if 0 < first_period <= 42 and ":" not in line[:first_period]:
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                NSFont.boldSystemFontOfSize_(base_font_size),
                NSMakeRange(start, first_period + 1),
            )
    for start, length, _expression in (roll_ranges if roll_ranges is not None else dice_ranges_for_body(body)):
        attributed.addAttribute_value_range_(
            NSForegroundColorAttributeName,
            dice_color,
            NSMakeRange(start, length),
        )
    add_colored_ranges(attributed, spell_ranges, spell_color)
    cursor = 0
    for line in body.splitlines():
        start = cursor
        cursor += len(line) + 1
        lower_line = line.lower()
        if "spellcasting ability" in lower_line or "spell casting ability" in lower_line:
            attributed.addAttribute_value_range_(
                NSFontAttributeName,
                italic_font,
                NSMakeRange(start, len(line)),
            )
    return attributed


def hp_bar(current: int | None, maximum: int | None, width: int = 12) -> tuple[str, float | None]:
    if current is None or maximum is None or maximum <= 0:
        return "─" * width, None
    ratio = max(0.0, min(1.0, current / maximum))
    filled = int(round(ratio * width))
    return "█" * filled + "░" * (width - filled), ratio


def attributed_tracker_body(body: str, bar_ranges: list[tuple[int, int, float | None]], current_ranges: list[tuple[int, int]]):
    attributes = {
        NSFontAttributeName: NSFont.monospacedSystemFontOfSize_weight_(13, 0),
        NSForegroundColorAttributeName: theme_color("text"),
    }
    attributed = NSMutableAttributedString.alloc().initWithString_attributes_(body, attributes)
    muted = theme_color("muted")
    healthy = theme_color("dice")
    danger = theme_color("monster")
    down = theme_color("danger")
    current_color = theme_color("gold")
    for start, length, ratio in bar_ranges:
        color = muted if ratio is None else down if ratio <= 0 else danger if ratio <= 0.35 else healthy
        attributed.addAttribute_value_range_(NSForegroundColorAttributeName, color, NSMakeRange(start, length))
    for start, length in current_ranges:
        attributed.addAttribute_value_range_(NSForegroundColorAttributeName, current_color, NSMakeRange(start, length))
        attributed.addAttribute_value_range_(NSFontAttributeName, NSFont.monospacedSystemFontOfSize_weight_(13, 0.35), NSMakeRange(start, length))
    return attributed
