from __future__ import annotations

from ..platform import *
from ..constants import *
from ..resources import DEFAULT_ICON_DIR
from ..theme import THEME_RGB

class CheckboxSquareView(NSView):
    checked: bool
    fill_color: Any
    stroke_color: Any

    def initWithFrame_(self, frame):
        self = objc.super(CheckboxSquareView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.checked = False
        self.fill_color = ui_color(1.0, 0.82, 0.26, 0.95)
        self.stroke_color = ui_color(1.0, 0.82, 0.26, 0.82)
        return self

    def setChecked_(self, checked):
        self.checked = bool(checked)
        self.setNeedsDisplay_(True)

    def setFillColor_strokeColor_(self, fill_color, stroke_color):
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        box = NSMakeRect(1.5, 1.5, bounds.size.width - 3, bounds.size.height - 3)

        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(box, 3, 3)
        if self.checked:
            self.fill_color.set()
            path.fill()
        self.stroke_color.set()
        path.setLineWidth_(1.5)
        path.stroke()


class FlippedView(NSView):
    def isFlipped(self):
        return True


class ContextInputPanel(NSPanel):
    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return False


class CenteredTextFieldCell(NSTextFieldCell):
    @objc.python_method
    def _centeredRectForBounds_(self, rect):
        draw_rect = objc.super(CenteredTextFieldCell, self).drawingRectForBounds_(rect)
        text_size = self.cellSizeForBounds_(rect)
        if draw_rect.size.height > text_size.height:
            draw_rect.origin.y += (draw_rect.size.height - text_size.height) / 2
            draw_rect.size.height = text_size.height
        return draw_rect

    def drawingRectForBounds_(self, rect):
        return self._centeredRectForBounds_(rect)

    def editWithFrame_inView_editor_delegate_event_(self, rect, control_view, text_obj, delegate, event):
        objc.super(CenteredTextFieldCell, self).editWithFrame_inView_editor_delegate_event_(
            self._centeredRectForBounds_(rect),
            control_view,
            text_obj,
            delegate,
            event,
        )

    def selectWithFrame_inView_editor_delegate_start_length_(self, rect, control_view, text_obj, delegate, start, length):
        objc.super(CenteredTextFieldCell, self).selectWithFrame_inView_editor_delegate_start_length_(
            self._centeredRectForBounds_(rect),
            control_view,
            text_obj,
            delegate,
            start,
            length,
        )


class PaddedCenteredTextFieldCell(CenteredTextFieldCell):
    @objc.python_method
    def _centeredRectForBounds_(self, rect):
        inset = 10
        padded = NSMakeRect(rect.origin.x + inset, rect.origin.y, max(1, rect.size.width - inset * 2), rect.size.height)
        return objc.super(PaddedCenteredTextFieldCell, self)._centeredRectForBounds_(padded)

def make_label(text: str, frame: tuple[int, int, int, int], size: float, bold: bool = False):
    label = NSTextField.labelWithString_(text)
    label.setFrame_(NSMakeRect(*frame))
    label.setTextColor_(theme_color("text_strong"))
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
    return label


def make_multiline(label: NSTextField):
    label.setLineBreakMode_(0)
    label.setUsesSingleLineMode_(False)
    return label


def ui_color(red: float, green: float, blue: float, alpha: float = 1.0):
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(red, green, blue, alpha)


def theme_color(name: str, alpha: float = 1.0):
    red, green, blue = THEME_RGB[name]
    return ui_color(red, green, blue, alpha)


def condition_color(condition: str, alpha: float = 1.0):
    red, green, blue = CONDITION_COLOR_VALUES.get(condition, (0.86, 0.86, 0.88))
    return ui_color(red, green, blue, alpha)


def normalized_conditions(combatant: dict[str, Any]) -> list[str]:
    raw_conditions = combatant.get("conditions", [])
    if isinstance(raw_conditions, str):
        raw_conditions = [raw_conditions]
    if not isinstance(raw_conditions, list):
        return []
    cleaned = []
    for condition in raw_conditions:
        name = str(condition).strip()
        if name in CONDITION_OPTIONS and name not in cleaned:
            cleaned.append(name)
    return cleaned


def combatant_is_dead(combatant: dict[str, Any]) -> bool:
    try:
        hp = int(str(combatant.get("hp") or "").strip())
    except ValueError:
        return False
    return hp == 0


def combatant_status_label(combatant: dict[str, Any]) -> str:
    if combatant_is_dead(combatant):
        return "Dead"
    conditions = normalized_conditions(combatant)
    return ", ".join(conditions) if conditions else "Normal"


def style_layer(view, background=None, border=None, radius: float = 10.0, border_width: float = 1.0):
    view.setWantsLayer_(True)
    layer = view.layer()
    layer.setCornerRadius_(radius)
    layer.setMasksToBounds_(True)
    if background is not None:
        layer.setBackgroundColor_(background.CGColor())
    if border is not None:
        layer.setBorderColor_(border.CGColor())
        layer.setBorderWidth_(border_width)


def style_text_input(field):
    placeholder = field.placeholderString()
    cell = PaddedCenteredTextFieldCell.alloc().initTextCell_(str(field.stringValue()))
    if placeholder is not None:
        cell.setPlaceholderString_(placeholder)
    cell.setScrollable_(True)
    cell.setFont_(NSFont.systemFontOfSize_(14))
    cell.setEditable_(True)
    cell.setSelectable_(True)
    field.setBezeled_(True)
    field.setBordered_(False)
    field.setDrawsBackground_(True)
    field.setCell_(cell)
    field.setEditable_(True)
    field.setSelectable_(True)
    field.setBackgroundColor_(theme_color("surface_soft"))
    field.setFocusRingType_(1)
    field.setTextColor_(theme_color("text"))
    field.setFont_(NSFont.systemFontOfSize_(14))
    field.setUsesSingleLineMode_(True)
    field.cell().setScrollable_(True)
    style_layer(field, theme_color("surface_soft"), theme_color("border_soft"), 8, 1)


def style_number_input(field):
    cell = CenteredTextFieldCell.alloc().initTextCell_(str(field.stringValue()))
    cell.setAlignment_(1)
    cell.setScrollable_(True)
    cell.setFont_(NSFont.systemFontOfSize_(15))
    field.setCell_(cell)
    field.setBezeled_(False)
    field.setBordered_(False)
    field.setDrawsBackground_(True)
    field.setEditable_(True)
    field.setSelectable_(True)
    field.setAlignment_(1)
    field.setBackgroundColor_(theme_color("surface"))
    field.setFocusRingType_(1)
    field.setTextColor_(theme_color("text"))
    field.setFont_(NSFont.systemFontOfSize_(15))
    field.setUsesSingleLineMode_(True)
    field.cell().setScrollable_(True)
    style_layer(field, theme_color("surface"), theme_color("border"), 8, 1)


def draw_text(text: str, x: float, y: float, size: float = 13, color=None, bold: bool = False):
    attributes = {
        NSFontAttributeName: NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size),
        NSForegroundColorAttributeName: color or theme_color("text_strong"),
    }
    NSString.stringWithString_(str(text)).drawAtPoint_withAttributes_(NSMakePoint(x, y), attributes)


def text_attributes(size: float = 13, color=None, bold: bool = False):
    return {
        NSFontAttributeName: NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size),
        NSForegroundColorAttributeName: color or theme_color("text_strong"),
    }


def text_width(text: str, attributes) -> float:
    return NSString.stringWithString_(str(text)).sizeWithAttributes_(attributes).width


def fit_text_to_width(text: str, width: float, attributes) -> str:
    text = str(text)
    if width <= 0:
        return ""
    if text_width(text, attributes) <= width:
        return text
    suffix = "..."
    if text_width(suffix, attributes) > width:
        return ""
    low = 0
    high = len(text)
    best = suffix
    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid].rstrip() + suffix
        if text_width(candidate, attributes) <= width:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best


def draw_fitted_text(text: str, rect, size: float = 13, color=None, bold: bool = False):
    attributes = text_attributes(size, color, bold)
    fitted = fit_text_to_width(text, rect.size.width, attributes)
    NSString.stringWithString_(fitted).drawInRect_withAttributes_(rect, attributes)


def draw_right_fitted_text(text: str, rect, size: float = 13, color=None, bold: bool = False):
    attributes = text_attributes(size, color, bold)
    fitted = fit_text_to_width(text, rect.size.width, attributes)
    fitted_width = min(rect.size.width, text_width(fitted, attributes))
    draw_rect = NSMakeRect(rect.origin.x + rect.size.width - fitted_width, rect.origin.y, fitted_width, rect.size.height)
    NSString.stringWithString_(fitted).drawInRect_withAttributes_(draw_rect, attributes)


def draw_right_fitted_text_centered(text: str, rect, size: float = 13, color=None, bold: bool = False):
    attributes = text_attributes(size, color, bold)
    fitted = fit_text_to_width(text, rect.size.width, attributes)
    string = NSString.stringWithString_(fitted)
    text_size = string.sizeWithAttributes_(attributes)
    fitted_width = min(rect.size.width, text_size.width)
    draw_rect = NSMakeRect(
        rect.origin.x + rect.size.width - fitted_width,
        rect.origin.y + (rect.size.height - text_size.height) / 2,
        fitted_width,
        text_size.height,
    )
    string.drawInRect_withAttributes_(draw_rect, attributes)


def draw_centered_text_in_rect(text: str, rect, size: float = 13, color=None, bold: bool = False):
    attributes = text_attributes(size, color, bold)
    string = NSString.stringWithString_(str(text))
    text_size = string.sizeWithAttributes_(attributes)
    draw_rect = NSMakeRect(
        rect.origin.x + (rect.size.width - text_size.width) / 2,
        rect.origin.y + (rect.size.height - text_size.height) / 2,
        text_size.width,
        text_size.height,
    )
    string.drawInRect_withAttributes_(draw_rect, attributes)


def draw_center_fitted_text(text: str, rect, size: float = 13, color=None, bold: bool = False):
    attributes = text_attributes(size, color, bold)
    fitted = fit_text_to_width(text, rect.size.width, attributes)
    fitted_width = min(rect.size.width, text_width(fitted, attributes))
    draw_rect = NSMakeRect(rect.origin.x + (rect.size.width - fitted_width) / 2, rect.origin.y, fitted_width, rect.size.height)
    NSString.stringWithString_(fitted).drawInRect_withAttributes_(draw_rect, attributes)


def point_in_rect(point, rect) -> bool:
    return (
        rect.origin.x <= point.x <= rect.origin.x + rect.size.width
        and rect.origin.y <= point.y <= rect.origin.y + rect.size.height
    )


def icon_image(name: str):
    filename = name
    if name in CLASS_ICON_FILES:
        filename = CLASS_ICON_FILES[name]
    elif name == "Monster":
        filename = MONSTER_ICON_FILE
    path = DEFAULT_ICON_DIR / filename
    key = str(path)
    if key not in ICON_IMAGE_CACHE:
        image = NSImage.alloc().initWithContentsOfFile_(key) if path.exists() else None
        ICON_IMAGE_CACHE[key] = image
    return ICON_IMAGE_CACHE.get(key)


def draw_icon(name: str, rect):
    image = icon_image(name)
    if image is None:
        return False
    image.drawInRect_fromRect_operation_fraction_respectFlipped_hints_(
        rect,
        NSMakeRect(0, 0, 0, 0),
        NSCompositingOperationSourceOver,
        1.0,
        True,
        None,
    )
    return True


def draw_rounded_rect(rect, fill, stroke=None, radius: float = 8, stroke_width: float = 1):
    path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
    fill.set()
    path.fill()
    if stroke is not None:
        stroke.set()
        path.setLineWidth_(stroke_width)
        path.stroke()


def draw_segmented_rounded_bar(rect, segments: list[tuple[float, Any]], background, radius: float = 4):
    path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
    NSGraphicsContext.saveGraphicsState()
    path.addClip()
    background.set()
    NSBezierPath.bezierPathWithRect_(rect).fill()
    cursor_x = rect.origin.x
    for width, color in segments:
        segment_w = max(0, min(width, rect.origin.x + rect.size.width - cursor_x))
        if segment_w <= 0:
            continue
        color.set()
        NSBezierPath.bezierPathWithRect_(NSMakeRect(cursor_x, rect.origin.y, segment_w, rect.size.height)).fill()
        cursor_x += segment_w
    NSGraphicsContext.restoreGraphicsState()


def ellipsize(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return "." * max_chars
    return text[: max_chars - 3].rstrip() + "..."
