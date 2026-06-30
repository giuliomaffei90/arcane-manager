from __future__ import annotations

from ..platform import *
from ..constants import *
from ..data import Creature, Item, Spell, creature_summary, display_ac, display_cr, display_hp, item_effective_cost_color_name, item_effective_value_text, item_display_name, item_summary
from ..resources import DEFAULT_FONT_DIR, DEFAULT_ICON_DIR
from ..text_utils import normalize
from .core import *


class PersistentScrollIndicator(NSView):
    scroll_view = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(PersistentScrollIndicator, self).initWithFrame_(frame)
        if self is None:
            return None
        self.scroll_view = None
        self.setWantsLayer_(True)
        return self

    def isFlipped(self):
        return True

    def setScrollView_(self, scroll_view):
        self.scroll_view = scroll_view
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        if bounds.size.height <= 1 or self.scroll_view is None:
            return

        document_view = self.scroll_view.documentView()
        clip_view = self.scroll_view.contentView()
        if document_view is None or clip_view is None:
            return

        document_height = float(document_view.frame().size.height)
        viewport_height = float(clip_view.bounds().size.height)
        if document_height <= viewport_height + 1:
            return

        track_width = min(6.0, max(3.0, float(bounds.size.width) - 2.0))
        track_x = (float(bounds.size.width) - track_width) / 2.0
        track_rect = NSMakeRect(track_x, 0.0, track_width, float(bounds.size.height))
        draw_rounded_rect(track_rect, theme_color("border_soft", 0.55), None, track_width / 2.0, 0)

        max_offset = max(1.0, document_height - viewport_height)
        offset = min(max(0.0, float(clip_view.bounds().origin.y)), max_offset)
        thumb_height = max(28.0, float(bounds.size.height) * viewport_height / document_height)
        thumb_y = offset / max_offset * max(0.0, float(bounds.size.height) - thumb_height)
        thumb_rect = NSMakeRect(track_x, thumb_y, track_width, thumb_height)
        draw_rounded_rect(thumb_rect, theme_color("muted", 0.95), None, track_width / 2.0, 0)


CART_ICON_FALLBACK_PATH = (
    "M24 48C10.7 48 0 58.7 0 72C0 85.3 10.7 96 24 96L69.3 96C73.2 96 76.5 98.8 77.2 102.6"
    "L129.3 388.9C135.5 423.1 165.3 448 200.1 448L456 448C469.3 448 480 437.3 480 424"
    "C480 410.7 469.3 400 456 400L200.1 400C188.5 400 178.6 391.7 176.5 380.3L171.4 352"
    "L475 352C505.8 352 532.2 330.1 537.9 299.8L568.9 133.9C572.6 114.2 557.5 96 537.4 96"
    "L124.7 96L124.3 94C119.5 67.4 96.3 48 69.2 48L24 48z"
    "M208 576C234.5 576 256 554.5 256 528C256 501.5 234.5 480 208 480C181.5 480 160 501.5 160 528"
    "C160 554.5 181.5 576 208 576z"
    "M432 576C458.5 576 480 554.5 480 528C480 501.5 458.5 480 432 480C405.5 480 384 501.5 384 528"
    "C384 554.5 405.5 576 432 576z"
)
_CART_ICON_PATH_DATA = None
_SVG_ASSET_CACHE = {}
_RECEIPT_LOGO_IMAGE = None
_RECEIPT_FONTS_REGISTERED = False


def register_receipt_fonts():
    global _RECEIPT_FONTS_REGISTERED
    if _RECEIPT_FONTS_REGISTERED:
        return
    _RECEIPT_FONTS_REGISTERED = True
    if CTFontManagerRegisterFontsForURL is None:
        return
    for filename in ("typewcond_regular.otf", "typewcond_bold.otf"):
        font_path = DEFAULT_FONT_DIR / filename
        if not font_path.exists():
            continue
        try:
            CTFontManagerRegisterFontsForURL(
                NSURL.fileURLWithPath_(str(font_path)),
                kCTFontManagerScopeProcess,
                None,
            )
        except Exception:
            pass


def receipt_font(size: float, bold: bool = False):
    register_receipt_fonts()
    candidates = (
        ("Typewriter_Condensed-Bold", "Typewriter_Condensed Bold")
        if bold
        else ("Typewriter_Condensed", "Typewriter_CondensedNormal")
    )
    for font_name in candidates:
        font = NSFont.fontWithName_size_(font_name, size)
        if font is not None:
            return font
    fallback_name = "Menlo-Bold" if bold else "Menlo"
    fallback = NSFont.fontWithName_size_(fallback_name, size)
    if fallback is not None:
        return fallback
    return NSFont.boldSystemFontOfSize_(size) if bold else NSFont.userFixedPitchFontOfSize_(size)


def receipt_currency_text(copper: int) -> str:
    value = int(copper)
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    gold = value // 100
    silver = (value % 100) // 10
    copper_part = value % 10
    parts = []
    if gold:
        parts.append(f"{gold} gp")
    if silver:
        parts.append(f"{silver} sp")
    if copper_part:
        parts.append(f"{copper_part} cp")
    return sign + " ".join(parts)


def _svg_asset_path_and_viewbox(filename: str, fallback_path: str = "", fallback_viewbox=(0.0, 0.0, 640.0, 640.0)):
    if filename in _SVG_ASSET_CACHE:
        return _SVG_ASSET_CACHE[filename]
    svg_path = DEFAULT_ICON_DIR / filename
    path_data = fallback_path
    viewbox = tuple(float(value) for value in fallback_viewbox)
    try:
        svg = svg_path.read_text(encoding="utf-8")
        path_match = re.search(r'<path[^>]+d="([^"]+)"', svg)
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg)
        if path_match is not None:
            path_data = path_match.group(1)
        if viewbox_match is not None:
            values = [float(value) for value in re.findall(r"-?(?:\d+(?:\.\d*)?|\.\d+)", viewbox_match.group(1))]
            if len(values) == 4:
                viewbox = tuple(values)
    except OSError:
        pass
    result = (path_data, viewbox)
    _SVG_ASSET_CACHE[filename] = result
    return result


def _cart_icon_path_data() -> str:
    global _CART_ICON_PATH_DATA
    if _CART_ICON_PATH_DATA is not None:
        return _CART_ICON_PATH_DATA
    icon_path = DEFAULT_ICON_DIR / "cart-shopping-solid.svg"
    try:
        svg = icon_path.read_text(encoding="utf-8")
        match = re.search(r'<path[^>]+d="([^"]+)"', svg)
        _CART_ICON_PATH_DATA = match.group(1) if match is not None else CART_ICON_FALLBACK_PATH
    except OSError:
        _CART_ICON_PATH_DATA = CART_ICON_FALLBACK_PATH
    return _CART_ICON_PATH_DATA


def _svg_bezier_path(path_data: str, viewbox, rect, preserve_aspect: bool = True) -> NSBezierPath:
    tokens = re.findall(r"[MmLlHhVvCcZz]|-?(?:\d+(?:\.\d*)?|\.\d+)", path_data)
    path = NSBezierPath.bezierPath()
    if hasattr(path, "setWindingRule_"):
        path.setWindingRule_(NSEvenOddWindingRule)
    index = 0
    command = ""
    cursor_x = 0.0
    cursor_y = 0.0
    start_x = 0.0
    start_y = 0.0
    view_x, view_y, view_w, view_h = [float(value) for value in viewbox]
    if preserve_aspect:
        scale = min(rect.size.width / max(1.0, view_w), rect.size.height / max(1.0, view_h))
        scale_x = scale
        scale_y = scale
        draw_w = view_w * scale
        draw_h = view_h * scale
        offset_x = rect.origin.x + (rect.size.width - draw_w) / 2.0
        offset_y = rect.origin.y + (rect.size.height - draw_h) / 2.0
    else:
        scale_x = rect.size.width / max(1.0, view_w)
        scale_y = rect.size.height / max(1.0, view_h)
        offset_x = rect.origin.x
        offset_y = rect.origin.y

    def point(svg_x: float, svg_y: float):
        return NSMakePoint(
            offset_x + (svg_x - view_x) * scale_x,
            offset_y + (view_h - (svg_y - view_y)) * scale_y,
        )

    while index < len(tokens):
        if re.match(r"[A-Za-z]", tokens[index]):
            command = tokens[index]
            index += 1
        if command in ("M", "m"):
            while index + 1 < len(tokens) and not re.match(r"[A-Za-z]", tokens[index]):
                x = float(tokens[index])
                y = float(tokens[index + 1])
                if command == "m":
                    x += cursor_x
                    y += cursor_y
                path.moveToPoint_(point(x, y))
                cursor_x, cursor_y = x, y
                start_x, start_y = x, y
                index += 2
                command = "L" if command == "M" else "l"
        elif command in ("L", "l"):
            while index + 1 < len(tokens) and not re.match(r"[A-Za-z]", tokens[index]):
                x = float(tokens[index])
                y = float(tokens[index + 1])
                if command == "l":
                    x += cursor_x
                    y += cursor_y
                path.lineToPoint_(point(x, y))
                cursor_x, cursor_y = x, y
                index += 2
        elif command in ("H", "h"):
            while index < len(tokens) and not re.match(r"[A-Za-z]", tokens[index]):
                x = float(tokens[index])
                if command == "h":
                    x += cursor_x
                path.lineToPoint_(point(x, cursor_y))
                cursor_x = x
                index += 1
        elif command in ("V", "v"):
            while index < len(tokens) and not re.match(r"[A-Za-z]", tokens[index]):
                y = float(tokens[index])
                if command == "v":
                    y += cursor_y
                path.lineToPoint_(point(cursor_x, y))
                cursor_y = y
                index += 1
        elif command in ("C", "c"):
            while index + 5 < len(tokens) and not re.match(r"[A-Za-z]", tokens[index]):
                x1, y1, x2, y2, x, y = [float(value) for value in tokens[index : index + 6]]
                if command == "c":
                    x1 += cursor_x
                    y1 += cursor_y
                    x2 += cursor_x
                    y2 += cursor_y
                    x += cursor_x
                    y += cursor_y
                path.curveToPoint_controlPoint1_controlPoint2_(point(x, y), point(x1, y1), point(x2, y2))
                cursor_x, cursor_y = x, y
                index += 6
        elif command in ("Z", "z"):
            path.closePath()
            cursor_x, cursor_y = start_x, start_y
        else:
            break
    return path


def _cart_icon_bezier_path(rect) -> NSBezierPath:
    return _svg_bezier_path(_cart_icon_path_data(), (0.0, 0.0, 640.0, 640.0), rect)


def _fit_bezier_path_to_rect(path: NSBezierPath, rect) -> NSBezierPath:
    bounds = path.bounds()
    if bounds.size.width <= 0 or bounds.size.height <= 0:
        return path
    scale = min(rect.size.width / bounds.size.width, rect.size.height / bounds.size.height)
    fitted_width = bounds.size.width * scale
    fitted_height = bounds.size.height * scale
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(
        rect.origin.x + (rect.size.width - fitted_width) / 2.0,
        rect.origin.y + (rect.size.height - fitted_height) / 2.0,
    )
    transform.scaleBy_(scale)
    transform.translateXBy_yBy_(-bounds.origin.x, -bounds.origin.y)
    fitted = path.copy()
    fitted.transformUsingAffineTransform_(transform)
    return fitted


def _receipt_logo_bezier_path(rect) -> NSBezierPath:
    path_data, viewbox = _svg_asset_path_and_viewbox("arcane_receipt_logo_transparente.svg", "", (0.0, 0.0, 1562.0, 825.0))
    base_path = _svg_bezier_path(path_data, viewbox, NSMakeRect(0, 0, viewbox[2], viewbox[3]), False)
    return _fit_bezier_path_to_rect(base_path, rect)


def _receipt_logo_image():
    global _RECEIPT_LOGO_IMAGE
    if _RECEIPT_LOGO_IMAGE is not None:
        return _RECEIPT_LOGO_IMAGE
    image_path = DEFAULT_ICON_DIR / "arcane_receipt_logo_horizontal.png"
    image = NSImage.alloc().initWithContentsOfFile_(str(image_path))
    _RECEIPT_LOGO_IMAGE = image
    return image


class CartIconButton(NSButton):
    badge_count = objc.ivar()
    hovered = objc.ivar()
    tracking_area = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(CartIconButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.badge_count = 0
        self.hovered = False
        self.tracking_area = None
        self.setTitle_("")
        self.setBordered_(False)
        self.setToolTip_("Shopping cart")
        return self

    def isFlipped(self):
        return False

    def setBadgeCount_(self, count):
        self.badge_count = max(0, int(count))
        self.setNeedsDisplay_(True)

    @objc.python_method
    def clearHoverState(self):
        if self.hovered:
            self.hovered = False
            self.setNeedsDisplay_(True)

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(CartIconButton, self).updateTrackingAreas()

    def mouseEntered_(self, _event):
        if self.isEnabled():
            self.hovered = True
            self.setNeedsDisplay_(True)

    def mouseExited_(self, _event):
        self.hovered = False
        self.setNeedsDisplay_(True)

    def highlight_(self, flag):
        objc.super(CartIconButton, self).highlight_(flag)
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        pressed = bool(self.isHighlighted())
        fill = theme_color("surface_hover" if self.hovered or pressed else "surface")
        stroke = theme_color("muted" if self.hovered or pressed else "border_soft")
        draw_rounded_rect(
            NSMakeRect(0.5, 0.5, max(1, bounds.size.width - 1), max(1, bounds.size.height - 1)),
            fill,
            stroke,
            min(14, bounds.size.height / 2),
            1.2,
        )

        width = bounds.size.width
        height = bounds.size.height
        icon_size = min(width * 0.60, height * 0.58)
        icon_rect = NSMakeRect(width * 0.18, height * 0.18, icon_size, icon_size)
        icon_path = _cart_icon_bezier_path(icon_rect)
        shadow_path = _cart_icon_bezier_path(NSMakeRect(icon_rect.origin.x, icon_rect.origin.y - 1, icon_rect.size.width, icon_rect.size.height))
        ui_color(0.0, 0.0, 0.0, 0.20).set()
        shadow_path.fill()
        icon_color = theme_color("text_strong")
        icon_color.set()
        icon_path.fill()

        if self.badge_count > 0:
            badge_text = "99+" if int(self.badge_count) > 99 else str(int(self.badge_count))
            badge_w = max(22, 13 + len(badge_text) * 7)
            badge_h = 22
            badge_x = width - badge_w - 2
            badge_y = height - badge_h - 2
            draw_rounded_rect(
                NSMakeRect(badge_x, badge_y, badge_w, badge_h),
                ui_color(1.0, 0.17, 0.20, 1.0),
                ui_color(1.0, 0.88, 0.88, 1.0),
                badge_h / 2,
                1.5,
            )
            draw_centered_text_in_rect(
                badge_text,
                NSMakeRect(badge_x + 2, badge_y + 3, badge_w - 4, badge_h - 5),
                11,
                ui_color(1, 1, 1, 1),
                True,
            )


def _receipt_attributes(size: float, bold: bool = False, color=None):
    return {
        NSFontAttributeName: receipt_font(size, bold),
        NSForegroundColorAttributeName: color or ui_color(0.12, 0.13, 0.14, 1.0),
    }


def _draw_receipt_text(text: str, rect, size: float, bold: bool = False, color=None, alignment: str = "left"):
    attributes = _receipt_attributes(size, bold, color)
    string = NSString.stringWithString_(str(text))
    text_size = string.sizeWithAttributes_(attributes)
    draw_width = min(rect.size.width, text_size.width)
    if alignment == "center":
        x = rect.origin.x + (rect.size.width - draw_width) / 2
    elif alignment == "right":
        x = rect.origin.x + rect.size.width - draw_width
    else:
        x = rect.origin.x
    draw_rect = NSMakeRect(
        x,
        rect.origin.y + (rect.size.height - text_size.height) / 2,
        draw_width,
        text_size.height,
    )
    string.drawInRect_withAttributes_(draw_rect, attributes)


def _draw_receipt_text_fit(text: str, rect, size: float, minimum_size: float, bold: bool = False, color=None, alignment: str = "left"):
    draw_size = float(size)
    string = NSString.stringWithString_(str(text))
    while draw_size > minimum_size:
        attributes = _receipt_attributes(draw_size, bold, color)
        if string.sizeWithAttributes_(attributes).width <= rect.size.width:
            break
        draw_size -= 1.0
    _draw_receipt_text(text, rect, draw_size, bold, color, alignment)


def _receipt_separator(width: float, size: float = 24, bold: bool = True) -> str:
    attributes = _receipt_attributes(size, bold, ui_color(0.12, 0.12, 0.11, 1.0))
    dash_width = max(1.0, NSString.stringWithString_("-").sizeWithAttributes_(attributes).width)
    return "-" * max(8, int(width / dash_width) + 1)


def _receipt_header_metrics(width: float):
    line_width = min(520.0, max(420.0, width - 160.0))
    line_x = (width - line_width) / 2.0
    return line_x, line_width


def _receipt_row_text_metrics(width: float):
    line_x = 48.0
    line_width = max(340.0, width - 288.0)
    return line_x, line_width


def _receipt_full_lane_metrics(width: float):
    line_x = 48.0
    scroll_width = max(240.0, width - 96.0)
    row_width = max(220.0, scroll_width - 20.0)
    remove_right_x = line_x + row_width - 6.0
    return line_x, max(340.0, remove_right_x - line_x)


class CartReceiptPanelView(NSView):
    total_text = objc.ivar()
    tax_text = objc.ivar()
    item_count = objc.ivar()
    total_top_y = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(CartReceiptPanelView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.total_text = "0 Copper"
        self.tax_text = "0"
        self.item_count = 0
        self.total_top_y = 210.0
        return self

    def setTotalText_taxText_itemCount_totalTopY_(self, total_text, tax_text, item_count, total_top_y):
        self.total_text = str(total_text)
        self.tax_text = str(tax_text)
        self.item_count = max(0, int(item_count))
        self.total_top_y = float(total_top_y)
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        shadow_color = ui_color(0.0, 0.0, 0.0, 0.28)
        paper_color = ui_color(0.99, 0.98, 0.93, 1.0)
        stroke_color = ui_color(0.58, 0.56, 0.48, 1.0)
        ink_color = ui_color(0.16, 0.19, 0.27, 1.0)
        soft_ink = ui_color(0.32, 0.32, 0.30, 1.0)

        draw_rounded_rect(NSMakeRect(7, 15, bounds.size.width - 14, bounds.size.height - 18), shadow_color, None, 8, 0)

        bottom_wave = 14
        paper = NSBezierPath.bezierPath()
        paper.moveToPoint_(NSMakePoint(18, bounds.size.height - 1))
        paper.lineToPoint_(NSMakePoint(bounds.size.width - 18, bounds.size.height - 1))
        paper.curveToPoint_controlPoint1_controlPoint2_(
            NSMakePoint(bounds.size.width - 8, bounds.size.height - 11),
            NSMakePoint(bounds.size.width - 8, bounds.size.height - 1),
            NSMakePoint(bounds.size.width - 8, bounds.size.height - 4),
        )
        paper.lineToPoint_(NSMakePoint(bounds.size.width - 8, bottom_wave))
        x = bounds.size.width - 8
        wave = 8
        while x > 8:
            paper.curveToPoint_controlPoint1_controlPoint2_(
                NSMakePoint(max(8, x - wave), bottom_wave),
                NSMakePoint(x - wave * 0.25, 4),
                NSMakePoint(x - wave * 0.75, bottom_wave + 10),
            )
            x -= wave
        paper.lineToPoint_(NSMakePoint(8, bounds.size.height - 11))
        paper.curveToPoint_controlPoint1_controlPoint2_(
            NSMakePoint(18, bounds.size.height - 1),
            NSMakePoint(8, bounds.size.height - 4),
            NSMakePoint(8, bounds.size.height - 1),
        )
        paper.closePath()
        paper_color.set()
        paper.fill()
        stroke_color.set()
        paper.setLineWidth_(1.2)
        paper.stroke()

        header_x, header_width = _receipt_header_metrics(bounds.size.width)
        row_text_x, row_text_width = _receipt_row_text_metrics(bounds.size.width)
        line_x, line_width = _receipt_full_lane_metrics(bounds.size.width)
        logo_image = _receipt_logo_image()
        logo_width = min(bounds.size.width - 230.0, 500.0)
        logo_height = min(116.0, logo_width * 486.0 / 2087.0)
        logo_rect = NSMakeRect((bounds.size.width - logo_width) / 2.0, bounds.size.height - 132.0, logo_width, logo_height)
        if logo_image is not None:
            logo_image.drawInRect_fromRect_operation_fraction_(
                logo_rect,
                NSMakeRect(0, 0, 0, 0),
                NSCompositingOperationSourceOver,
                1.0,
            )
        else:
            logo_path = _receipt_logo_bezier_path(logo_rect)
            if logo_path.elementCount() > 0:
                ink_color.set()
                logo_path.fill()
            else:
                _draw_receipt_text("ARCANE RECEIPT", NSMakeRect(header_x, bounds.size.height - 88, header_width, 44), 34, True, ink_color, "center")

        _draw_receipt_text("*** SHOPPING CART ***", NSMakeRect(header_x, bounds.size.height - 160, header_width, 30), 22, True, ink_color, "center")
        _draw_receipt_text(_receipt_separator(line_width, 22, True), NSMakeRect(line_x, bounds.size.height - 190, line_width, 26), 22, True, ink_color, "center")

        if int(self.item_count) == 0:
            _draw_receipt_text("YOUR CART IS EMPTY", NSMakeRect(row_text_x, bounds.size.height - 245, row_text_width, 28), 20, False, soft_ink, "center")

        total_y = max(150.0, min(float(self.total_top_y), bounds.size.height - 225.0))
        _draw_receipt_text(_receipt_separator(line_width, 24, True), NSMakeRect(line_x, total_y, line_width, 24), 24, True, soft_ink, "center")
        amount_width = min(330.0, line_width * 0.58)
        label_width = line_width - amount_width
        _draw_receipt_text("TOTAL", NSMakeRect(line_x, total_y - 40, label_width, 34), 29, False, ui_color(0.10, 0.11, 0.12, 1.0), "left")
        _draw_receipt_text_fit(str(self.total_text), NSMakeRect(line_x + label_width, total_y - 40, amount_width, 34), 29, 21, False, ui_color(0.10, 0.11, 0.12, 1.0), "right")
        _draw_receipt_text("TAX", NSMakeRect(line_x, total_y - 67, label_width, 26), 23, False, soft_ink, "left")
        _draw_receipt_text(str(self.tax_text), NSMakeRect(line_x + label_width, total_y - 67, amount_width, 26), 23, False, soft_ink, "right")
        _draw_receipt_text(_receipt_separator(line_width, 24, True), NSMakeRect(line_x, total_y - 94, line_width, 24), 24, True, soft_ink, "center")
        _draw_receipt_text("THANK YOU!", NSMakeRect(line_x, 30, line_width, 22), 17, True, ink_color.colorWithAlphaComponent_(0.45), "center")


class CartReceiptRowView(NSView):
    line_number = objc.ivar()
    quantity = objc.ivar()
    name = objc.ivar()
    subtotal_text = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(CartReceiptRowView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.line_number = 0
        self.quantity = 0
        self.name = ""
        self.subtotal_text = ""
        return self

    def configureLineNumber_quantity_name_subtotalText_(self, line_number, quantity, name, subtotal_text):
        self.line_number = int(line_number)
        self.quantity = int(quantity)
        self.name = str(name)
        self.subtotal_text = str(subtotal_text)
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        ink = ui_color(0.12, 0.12, 0.11, 1.0)
        muted = ui_color(0.42, 0.40, 0.35, 1.0)
        lane_width = max(120.0, bounds.size.width - 172.0)
        left_x = 0.0
        line_height = bounds.size.height
        number_text = f"{int(self.line_number)}."
        item_text = f"{int(self.quantity)}x {self.name}"
        price_text = str(self.subtotal_text)

        number_attrs = _receipt_attributes(22, False, muted)
        item_attrs = _receipt_attributes(22, False, ink)
        price_attrs = _receipt_attributes(22, False, ink)
        leader_attrs = _receipt_attributes(22, False, ink)
        number_width = NSString.stringWithString_(number_text).sizeWithAttributes_(number_attrs).width + 12.0
        price_width = min(150.0, NSString.stringWithString_(price_text).sizeWithAttributes_(price_attrs).width + 6.0)
        min_leader_width = 42.0
        item_max_width = max(56.0, lane_width - number_width - price_width - min_leader_width - 24.0)
        fitted_item = fit_text_to_width(item_text, item_max_width, item_attrs)
        item_width = NSString.stringWithString_(fitted_item).sizeWithAttributes_(item_attrs).width
        price_x = left_x + lane_width - price_width
        leader_x = left_x + number_width + item_width + 8.0
        leader_width = max(14.0, price_x - leader_x - 8.0)
        dot_width = max(1.0, NSString.stringWithString_(".").sizeWithAttributes_(leader_attrs).width)
        leader_text = "." * max(3, int(leader_width / dot_width))
        text_y = (line_height - 28.0) / 2.0

        NSString.stringWithString_(number_text).drawInRect_withAttributes_(NSMakeRect(left_x, text_y, number_width, 28), number_attrs)
        NSString.stringWithString_(fitted_item).drawInRect_withAttributes_(NSMakeRect(left_x + number_width, text_y, item_width + 4, 28), item_attrs)
        NSString.stringWithString_(leader_text).drawInRect_withAttributes_(NSMakeRect(leader_x, text_y, leader_width, 28), leader_attrs)
        NSString.stringWithString_(price_text).drawInRect_withAttributes_(NSMakeRect(price_x, text_y, price_width, 28), price_attrs)


class DiceTextView(NSTextView):
    dice_ranges: list[tuple[int, int, str]]
    spell_ranges: list[tuple[int, int, Spell]]
    combatant_ranges: list[tuple[int, int, int]]
    roll_target: Any
    spell_target: Any
    combatant_target: Any
    tracking_area: Any

    def initWithFrame_(self, frame):
        self = objc.super(DiceTextView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.dice_ranges = []
        self.spell_ranges = []
        self.combatant_ranges = []
        self.roll_target = None
        self.spell_target = None
        self.combatant_target = None
        self.tracking_area = None
        self.setEditable_(False)
        self.setSelectable_(False)
        self.setDrawsBackground_(False)
        self.setTextContainerInset_(NSMakeSize(0, 0))
        self.setHorizontallyResizable_(False)
        self.setVerticallyResizable_(True)
        self.textContainer().setLineFragmentPadding_(0)
        return self

    def setDiceRanges_(self, dice_ranges):
        self.dice_ranges = list(dice_ranges)

    def setRollTarget_(self, target):
        self.roll_target = target

    def setSpellRanges_(self, spell_ranges):
        self.spell_ranges = list(spell_ranges)

    def setSpellTarget_(self, target):
        self.spell_target = target

    def setCombatantRanges_(self, combatant_ranges):
        self.combatant_ranges = list(combatant_ranges)

    def setCombatantTarget_(self, target):
        self.combatant_target = target

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseMoved
            | NSTrackingMouseEnteredAndExited
            | NSTrackingActiveAlways
            | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(DiceTextView, self).updateTrackingAreas()

    def diceExpressionAtEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.characterIndexForInsertionAtPoint_(point)
        for start, length, expression in self.dice_ranges:
            if start <= index < start + length:
                return expression
        return None

    def spellAtEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.characterIndexForInsertionAtPoint_(point)
        for start, length, spell in self.spell_ranges:
            if start <= index < start + length:
                return spell
        return None

    def combatantIndexAtEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.characterIndexForInsertionAtPoint_(point)
        for start, length, combatant_index in self.combatant_ranges:
            if start <= index < start + length:
                return combatant_index
        return None

    def mouseMoved_(self, event):
        if (
            self.diceExpressionAtEvent_(event) is not None
            or self.spellAtEvent_(event) is not None
            or self.combatantIndexAtEvent_(event) is not None
        ):
            NSCursor.pointingHandCursor().set()
        else:
            NSCursor.arrowCursor().set()

    def mouseExited_(self, _event):
        NSCursor.arrowCursor().set()

    def mouseDown_(self, event):
        expression = self.diceExpressionAtEvent_(event)
        if expression is not None:
            if self.roll_target is not None:
                self.roll_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "rollDice:",
                    expression,
                    False,
                )
            return
        spell = self.spellAtEvent_(event)
        if spell is not None:
            if self.spell_target is not None:
                self.spell_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openSpell:",
                    spell,
                    False,
                )
            return
        combatant_index = self.combatantIndexAtEvent_(event)
        if combatant_index is not None:
            if self.combatant_target is not None:
                self.combatant_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantIndex:",
                    combatant_index,
                    False,
                )
            return
        objc.super(DiceTextView, self).mouseDown_(event)


SPELL_SCHOOL_RGB: dict[str, tuple[float, float, float]] = {
    "Abjuration": (0x72 / 255, 0xC7 / 255, 0xF7 / 255),
    "Conjuration": (0x62 / 255, 0xD7 / 255, 0xC7 / 255),
    "Divination": (0x9C / 255, 0xA8 / 255, 0xFF / 255),
    "Enchantment": (0xF0 / 255, 0x85 / 255, 0xC8 / 255),
    "Evocation": (0xF2 / 255, 0x7A / 255, 0x5E / 255),
    "Illusion": (0xC4 / 255, 0x99 / 255, 0xF2 / 255),
    "Necromancy": (0x9A / 255, 0xD8 / 255, 0x5F / 255),
    "Transmutation": (0xE7 / 255, 0xB9 / 255, 0x56 / 255),
}


def spell_school_color(school: str):
    rgb = SPELL_SCHOOL_RGB.get(str(school or "").strip())
    if rgb is None:
        return theme_color("gold")
    return ui_color(*rgb, 1.0)


class TabButton(NSButton):
    is_active = objc.ivar()
    is_hovered = objc.ivar()
    tracking_area = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(TabButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.is_active = False
        self.is_hovered = False
        self.tracking_area = None
        self.setBordered_(False)
        return self

    def setActive_(self, active):
        self.is_active = bool(active)
        self.setNeedsDisplay_(True)

    @objc.python_method
    def clearHoverState(self):
        if self.is_hovered:
            self.is_hovered = False
            self.setNeedsDisplay_(True)

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(TabButton, self).updateTrackingAreas()

    def mouseEntered_(self, _event):
        self.is_hovered = True
        self.setNeedsDisplay_(True)

    def mouseExited_(self, _event):
        self.is_hovered = False
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        active = bool(self.is_active)
        hovered = bool(self.is_hovered)
        if active:
            fill = theme_color("surface_hover")
        elif highlighted or hovered:
            fill = theme_color("surface")
        else:
            fill = theme_color("surface_soft")
        text_color = theme_color("text_strong") if active else theme_color("muted")
        draw_rounded_rect(
            NSMakeRect(0.5, 0.5, max(1, bounds.size.width - 1), max(1, bounds.size.height - 1)),
            fill,
            theme_color("border_soft"),
            8,
            1,
        )
        draw_center_fitted_text(str(self.title()), NSMakeRect(10, 6, bounds.size.width - 20, 18), 12, text_color, True)


class SearchResultButton(StyledButton):
    row_kind = objc.ivar()
    primary_text = objc.ivar()
    secondary_text = objc.ivar()
    hp_text = objc.ivar()
    ac_text = objc.ivar()
    cr_text = objc.ivar()
    meta_text = objc.ivar()
    spell_school = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(SearchResultButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.row_kind = ""
        self.primary_text = ""
        self.secondary_text = ""
        self.hp_text = ""
        self.ac_text = ""
        self.cr_text = ""
        self.meta_text = ""
        self.spell_school = ""
        self.setBordered_(False)
        self.setTitle_("")
        self.setSoftBackground_(True)
        return self

    def configureMonsterResult_(self, creature: Creature):
        self.row_kind = "monster"
        self.primary_text = creature.name
        self.secondary_text = ""
        self.hp_text = f"HP {display_hp(creature.hp)}"
        self.ac_text = ""
        self.cr_text = f"CR {display_cr(creature.cr)}"
        self.meta_text = ""
        self.spell_school = ""
        self.setToolTip_(creature_summary(creature))
        self.setNeedsDisplay_(True)

    def configureSpellResult_(self, spell: Spell):
        self.row_kind = "spell"
        self.primary_text = spell.name
        self.secondary_text = spell.italian_name if normalize(spell.italian_name) != normalize(spell.name) else ""
        self.hp_text = ""
        self.ac_text = ""
        self.cr_text = ""
        self.meta_text = " | ".join(part for part in (spell.level, spell.school) if part)
        self.spell_school = spell.school
        tooltip_parts = [spell.name]
        if self.secondary_text:
            tooltip_parts.append(f"({self.secondary_text})")
        if self.meta_text:
            tooltip_parts.append(f"- {self.meta_text}")
        self.setToolTip_(" ".join(tooltip_parts))
        self.setNeedsDisplay_(True)

    def configureItemResult_(self, item: Item):
        self.row_kind = "item"
        self.primary_text = item_display_name(item)
        self.secondary_text = item.category
        self.hp_text = item_effective_cost_color_name(item)
        self.ac_text = ""
        self.cr_text = ""
        self.meta_text = item_effective_value_text(item)
        self.spell_school = ""
        self.setToolTip_(item_summary(item))
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        draw_button_background(
            NSMakeRect(0.5, 0.5, max(1, bounds.size.width - 1), max(1, bounds.size.height - 1)),
            bool(self.hovered),
            bool(self.isHighlighted()),
            bool(self.isEnabled()),
            False,
            True,
            7,
        )
        if self.row_kind == "monster":
            self._drawMonsterResult_(bounds)
        elif self.row_kind == "spell":
            self._drawSpellResult_(bounds)
        elif self.row_kind == "item":
            self._drawItemResult_(bounds)

    def mouseDown_(self, event):
        objc.super(SearchResultButton, self).mouseDown_(event)

    @objc.python_method
    def _drawMonsterResult_(self, bounds):
        width = bounds.size.width
        primary = theme_color("text_strong")
        muted = theme_color("muted")
        name_attrs = text_attributes(14, primary, True)
        meta_attrs = text_attributes(11, muted, True)
        cr_text = self.cr_text.replace("CR ", "CR: ")
        cr_width = text_width(cr_text, meta_attrs)
        gap = 6
        x = 14
        y = max(0, (bounds.size.height - 19) / 2 - 1)
        metadata_width = cr_width
        meta_x = width - x - metadata_width
        name_width = max(54, meta_x - x - gap)
        fitted_name = fit_text_to_width(self.primary_text, name_width, name_attrs)
        NSString.stringWithString_(fitted_name).drawInRect_withAttributes_(NSMakeRect(x, y, name_width, 20), name_attrs)
        draw_right_fitted_text(cr_text, NSMakeRect(meta_x, y + 2, cr_width, 17), 11, muted, True)

    @objc.python_method
    def _drawSpellResult_(self, bounds):
        width = bounds.size.width
        primary = theme_color("text")
        muted = theme_color("muted")
        metadata_color = spell_school_color(self.spell_school)
        draw_fitted_text(self.primary_text, NSMakeRect(14, 7, width - 28, 17), 13.5, primary, True)
        if width >= 340 and self.meta_text:
            meta_w = min(172, max(120, width * 0.40))
            secondary_w = width - meta_w - 38
            draw_fitted_text(self.secondary_text, NSMakeRect(14, 25, secondary_w, 15), 11.5, muted, False)
            draw_right_fitted_text(self.meta_text, NSMakeRect(width - meta_w - 14, 25, meta_w, 15), 11.5, metadata_color, True)
            return
        bottom = self.meta_text
        if self.secondary_text and self.meta_text:
            bottom = f"{self.secondary_text} - {self.meta_text}"
        elif self.secondary_text:
            bottom = self.secondary_text
        draw_fitted_text(bottom, NSMakeRect(14, 25, width - 28, 15), 11.5, muted, False)

    @objc.python_method
    def _drawItemResult_(self, bounds):
        width = bounds.size.width
        primary = theme_color("text")
        metadata_color = theme_color(self.hp_text)
        draw_fitted_text(self.primary_text, NSMakeRect(14, 7, width - 28, 17), 13.5, primary, True)
        if width >= 340 and self.meta_text:
            meta_w = min(130, max(82, width * 0.30))
            secondary_w = width - meta_w - 38
            draw_fitted_text(self.secondary_text, NSMakeRect(14, 25, secondary_w, 15), 11.5, metadata_color, False)
            draw_right_fitted_text(self.meta_text, NSMakeRect(width - meta_w - 14, 25, meta_w, 15), 11.5, metadata_color, True)
            return
        bottom = self.secondary_text
        if self.secondary_text and self.meta_text:
            bottom = f"{self.secondary_text} - {self.meta_text}"
        elif self.meta_text:
            bottom = self.meta_text
        draw_fitted_text(bottom, NSMakeRect(14, 25, width - 28, 15), 11.5, metadata_color, False)


def color_from_hex(value: str, fallback=None):
    text = str(value or "").strip().lstrip("#")
    if len(text) != 6:
        return fallback or theme_color("text")
    try:
        red = int(text[0:2], 16) / 255.0
        green = int(text[2:4], 16) / 255.0
        blue = int(text[4:6], 16) / 255.0
    except ValueError:
        return fallback or theme_color("text")
    return ui_color(red, green, blue, 1.0)


class AdventureTreeButton(NSButton):
    display_name = objc.ivar()
    node_path = objc.ivar()
    depth = objc.ivar()
    is_dir = objc.ivar()
    is_expanded = objc.ivar()
    is_selected = objc.ivar()
    color_hex = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(AdventureTreeButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.display_name = ""
        self.node_path = ""
        self.depth = 0
        self.is_dir = False
        self.is_expanded = False
        self.is_selected = False
        self.color_hex = ""
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def configureName_path_depth_isDir_expanded_selected_color_(
        self,
        name,
        path,
        depth,
        is_dir,
        expanded,
        selected,
        color_hex,
    ):
        self.display_name = str(name)
        self.node_path = str(path)
        self.depth = int(depth)
        self.is_dir = bool(is_dir)
        self.is_expanded = bool(expanded)
        self.is_selected = bool(selected)
        self.color_hex = str(color_hex or "")
        self.setToolTip_(str(path))
        self.setNeedsDisplay_(True)

    def menuForEvent_(self, _event):
        target = self.target()
        if target is not None and hasattr(target, "adventureContextMenuForButton_"):
            return target.adventureContextMenuForButton_(self)
        return objc.super(AdventureTreeButton, self).menuForEvent_(_event)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        highlighted = self.isHighlighted()
        if self.is_selected:
            fill = theme_color("selection")
        elif highlighted:
            fill = theme_color("surface_hover")
        else:
            fill = None
        if fill is not None:
            draw_rounded_rect(
                NSMakeRect(4, 1, max(1, bounds.size.width - 8), max(1, bounds.size.height - 2)),
                fill,
                None,
                5,
                0,
            )

        indent = 10 + int(self.depth) * 18
        text_x = indent + 20
        text_color = color_from_hex(self.color_hex, theme_color("text"))
        if self.is_selected:
            text_color = theme_color("text_strong")
        muted = theme_color("muted")

        if self.is_dir:
            arrow = "⌄" if self.is_expanded else "›"
            draw_center_fitted_text(arrow, NSMakeRect(indent, 5, 14, 16), 14, muted, True)
            draw_fitted_text(self.display_name, NSMakeRect(text_x, 5, bounds.size.width - text_x - 10, 18), 13, text_color, True)
        else:
            draw_fitted_text(self.display_name, NSMakeRect(text_x, 5, bounds.size.width - text_x - 10, 18), 13, text_color, False)


class AdventureDividerView(NSView):
    target = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(AdventureDividerView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.target = None
        self.setToolTip_("Drag to resize")
        return self

    def setTarget_(self, target):
        self.target = target

    def resetCursorRects(self):
        self.addCursorRect_cursor_(self.bounds(), NSCursor.resizeLeftRightCursor())

    def mouseEntered_(self, _event):
        NSCursor.resizeLeftRightCursor().set()

    def mouseDown_(self, event):
        NSCursor.resizeLeftRightCursor().set()
        self._sendDragLocation_(event)

    def mouseDragged_(self, event):
        self._sendDragLocation_(event)

    def mouseUp_(self, _event):
        NSCursor.arrowCursor().set()

    @objc.python_method
    def _sendDragLocation_(self, event):
        if self.target is None or not hasattr(self.target, "resizeAdventureTreeToWindowX_"):
            return
        self.target.resizeAdventureTreeToWindowX_(event.locationInWindow().x)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        x = bounds.size.width / 2 - 0.5
        theme_color("border").set()
        path = NSBezierPath.bezierPath()
        path.moveToPoint_(NSMakePoint(x, 0))
        path.lineToPoint_(NSMakePoint(x, bounds.size.height))
        path.setLineWidth_(1)
        path.stroke()


class StatBlockAbilityButton(StyledButton):
    ability_name = objc.ivar()
    score_text = objc.ivar()
    bonus_text = objc.ivar()
    roll_expression = objc.ivar()
    roll_target = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(StatBlockAbilityButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.ability_name = ""
        self.score_text = ""
        self.bonus_text = ""
        self.roll_expression = ""
        self.roll_target = None
        self.setBordered_(False)
        self.setTitle_("")
        self.setSoftBackground_(True)
        return self

    def configure_stat(self, name, score, bonus, target):
        bonus_value = int(bonus)
        self.ability_name = str(name)
        self.score_text = str(score)
        self.bonus_text = f"{bonus_value:+d}"
        self.roll_expression = f"1d20+{bonus_value}" if bonus_value >= 0 else f"1d20{bonus_value}"
        self.roll_target = target
        self.setToolTip_(f"Roll {self.ability_name} {self.roll_expression}")
        self.setNeedsDisplay_(True)

    @objc.python_method
    def _bonusRect(self):
        bounds = self.bounds()
        inset = 2
        return NSMakeRect(inset, bounds.size.height * 0.27, bounds.size.width - inset * 2, bounds.size.height * 0.71)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        state = button_visual_state(
            bool(self.hovered),
            bool(self.isHighlighted()),
            bool(self.isEnabled()),
            False,
            True,
        )
        circle_fill = theme_color("panel_alt")
        text = theme_color("text_strong")
        muted = theme_color("muted")
        green = theme_color("dice")

        rect = self._bonusRect()
        draw_rounded_rect(rect, state["fill"], state["stroke"], 7, state["stroke_width"])
        circle_side = min(bounds.size.width - 4, bounds.size.height * 0.43)
        circle = NSMakeRect(
            (bounds.size.width - circle_side) / 2,
            1,
            circle_side,
            circle_side,
        )
        oval = NSBezierPath.bezierPathWithOvalInRect_(circle)
        circle_fill.set()
        oval.fill()

        state["stroke"].set()
        oval.setLineWidth_(1.25)
        oval.stroke()

        draw_center_fitted_text(self.ability_name, NSMakeRect(5, bounds.size.height - 20, bounds.size.width - 10, 14), 9.5, muted, True)
        draw_center_fitted_text(self.bonus_text, NSMakeRect(5, bounds.size.height * 0.46, bounds.size.width - 10, 22), 16, green, True)
        draw_center_fitted_text(self.score_text, NSMakeRect(5, circle.origin.y + (circle.size.height - 19) / 2, bounds.size.width - 10, 20), 14, text, True)

    def mouseDown_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        if self.roll_expression and self.roll_target is not None and point_in_rect(point, self._bonusRect()):
            self.roll_target.performSelectorOnMainThread_withObject_waitUntilDone_(
                "rollDice:",
                self.roll_expression,
                False,
            )
            return
        objc.super(StatBlockAbilityButton, self).mouseDown_(event)


class RowAddButton(StyledButton):
    def initWithFrame_(self, frame):
        self = objc.super(RowAddButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def drawRect_(self, _rect):
        bounds = self.bounds()
        side = min(30, bounds.size.width, bounds.size.height)
        state = draw_button_background(
            NSMakeRect((bounds.size.width - side) / 2, (bounds.size.height - side) / 2, side, side),
            bool(self.hovered),
            bool(self.isHighlighted()),
            bool(self.isEnabled()),
            False,
            False,
            8,
        )
        attributes = text_attributes(16, state["text"], True)
        glyph = NSString.stringWithString_("+")
        glyph_size = glyph.sizeWithAttributes_(attributes)
        glyph.drawAtPoint_withAttributes_(
            NSMakePoint(
                (bounds.size.width - glyph_size.width) / 2,
                (bounds.size.height - glyph_size.height) / 2 - 1,
            ),
            attributes,
        )


class StyledPopUpButton(NSPopUpButton):
    hovered = objc.ivar()
    tracking_area = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(StyledPopUpButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.hovered = False
        self.tracking_area = None
        self.setBordered_(False)
        return self

    @objc.python_method
    def clearHoverState(self):
        if self.hovered:
            self.hovered = False
            self.setNeedsDisplay_(True)

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(StyledPopUpButton, self).updateTrackingAreas()

    def mouseEntered_(self, _event):
        if self.isEnabled():
            self.hovered = True
            self.setNeedsDisplay_(True)

    def mouseExited_(self, _event):
        self.hovered = False
        self.setNeedsDisplay_(True)

    def highlight_(self, flag):
        objc.super(StyledPopUpButton, self).highlight_(flag)
        self.setNeedsDisplay_(True)

    def setEnabled_(self, enabled):
        objc.super(StyledPopUpButton, self).setEnabled_(enabled)
        if not enabled:
            self.clearHoverState()
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        state = draw_button_background(
            NSMakeRect(0.5, 0.5, max(1, bounds.size.width - 1), max(1, bounds.size.height - 1)),
            bool(self.hovered),
            bool(self.isHighlighted()),
            bool(self.isEnabled()),
            False,
            False,
            7,
        )
        item = self.selectedItem()
        title = str(item.title()) if item is not None else str(self.title())
        draw_fitted_text(title, NSMakeRect(12, 8, max(20, bounds.size.width - 42), 18), 13, state["text"], True)
        draw_right_fitted_text("⌄", NSMakeRect(bounds.size.width - 28, 7, 16, 18), 14, state["text"], True)


MONSTER_RESULT_ROW_HEIGHT = 42
MONSTER_RESULT_ROW_STEP = 50
SPELL_RESULT_ROW_HEIGHT = 42
SPELL_RESULT_ROW_STEP = 50
TRACKER_NAME_COLUMN_WIDTH = 172.0
TRACKER_HP_TEXT_WIDTH = 52.0
TRACKER_MIN_HP_BAR_WIDTH = 110.0
TRACKER_NAME_TO_HP_GAP = 10.5


class CombatTrackerView(NSView):
    combatants: list[dict[str, Any]]
    current_turn_index: int
    name_rects: list[tuple[Any, int]]
    hp_button_rects: list[tuple[Any, int]]
    status_rects: list[tuple[Any, int]]
    target: Any
    tracking_area: Any
    hovered_hit: Any

    def initWithFrame_(self, frame):
        self = objc.super(CombatTrackerView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.combatants = []
        self.current_turn_index = 0
        self.name_rects = []
        self.hp_button_rects = []
        self.status_rects = []
        self.target = None
        self.tracking_area = None
        self.hovered_hit = None
        return self

    def isFlipped(self):
        return True

    def setTarget_(self, target):
        self.target = target

    def setPayload_(self, payload):
        self.combatants = list(payload.get("combatants", []))
        self.current_turn_index = int(payload.get("current_turn_index", 0))
        self.hovered_hit = None
        width = max(780, self.frame().size.width)
        height = max(420, 144 + len(self.combatants) * 70 + 96)
        self.setFrame_(NSMakeRect(0, 0, width, height))
        self.setNeedsDisplay_(True)

    def updateTrackingAreas(self):
        if self.tracking_area is not None:
            self.removeTrackingArea_(self.tracking_area)
        self.tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseMoved
            | NSTrackingMouseEnteredAndExited
            | NSTrackingActiveAlways
            | NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self.tracking_area)
        objc.super(CombatTrackerView, self).updateTrackingAreas()

    @objc.python_method
    def _hp_values(self, combatant: dict[str, Any]) -> tuple[int | None, int | None]:
        try:
            current = int(str(combatant.get("hp") or "").strip())
        except ValueError:
            current = None
        try:
            maximum = int(str(combatant.get("max_hp") or "").strip())
        except ValueError:
            maximum = None
        return current, maximum

    @objc.python_method
    def _hit_test(self, event) -> tuple[str, int, int | None] | None:
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        for rect, index in self.status_rects:
            if point_in_rect(point, rect):
                return ("status", index, None)
        for rect, index in self.hp_button_rects:
            if point_in_rect(point, rect):
                return ("hp", index, None)
        for rect, index in self.name_rects:
            if point_in_rect(point, rect):
                return ("name", index, None)
        return None

    def mouseMoved_(self, event):
        hit = self._hit_test(event)
        if hit != self.hovered_hit:
            self.hovered_hit = hit
            self.setNeedsDisplay_(True)
        if hit is not None:
            NSCursor.pointingHandCursor().set()
        else:
            NSCursor.arrowCursor().set()

    def mouseExited_(self, _event):
        self.hovered_hit = None
        self.setNeedsDisplay_(True)
        NSCursor.arrowCursor().set()

    def mouseDown_(self, event):
        hit = self._hit_test(event)
        if hit is not None and hit[0] == "name":
            index = hit[1]
            if self.target is not None:
                self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantIndex:",
                    index,
                    False,
                )
            return
        if hit is not None and hit[0] == "hp":
            _kind, index, _delta = hit
            if self.target is not None:
                point = event.locationInWindow()
                self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantHpMenu:",
                    {"index": index, "x": float(point.x), "y": float(point.y)},
                    False,
                )
            return
        if hit is not None and hit[0] == "status":
            _kind, index, _delta = hit
            if self.target is not None:
                point = self.convertPoint_fromView_(event.locationInWindow(), None)
                self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "openCombatantStatusMenu:",
                    {"index": index, "x": float(point.x), "y": float(point.y)},
                    False,
                )
            return
        if self.target is not None:
            self.target.performSelectorOnMainThread_withObject_waitUntilDone_(
                "closeCombatantHpMenu:",
                None,
                False,
            )
        objc.super(CombatTrackerView, self).mouseDown_(event)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        theme_color("panel").set()
        NSBezierPath.bezierPathWithRect_(bounds).fill()

        muted = theme_color("muted")
        card_border = theme_color("border_soft")
        current_border = theme_color("border")
        green = theme_color("dice")
        temp_blue = theme_color("blue_temp")
        pink = theme_color("monster")
        red = theme_color("danger")
        dead_red = theme_color("danger")
        white = theme_color("text_strong")

        left = 24
        width = bounds.size.width - 48
        right = left + width
        status_w = 116 if width >= 900 else 98
        status_x = right - status_w - 18
        ac_w = 44
        ac_x = status_x - ac_w - 18
        name_x = left + 132
        hp_text_w = TRACKER_HP_TEXT_WIDTH
        hp_action_w = 44
        hp_action_x = ac_x - hp_action_w - 18
        max_name_w = (
            hp_action_x
            - 18
            - TRACKER_MIN_HP_BAR_WIDTH
            - name_x
            - hp_text_w
            - TRACKER_NAME_TO_HP_GAP
            - 14
        )
        name_w = min(TRACKER_NAME_COLUMN_WIDTH, max(60.0, max_name_w))
        hp_text_x = name_x + name_w + TRACKER_NAME_TO_HP_GAP
        bar_x = hp_text_x + hp_text_w + 14
        bar_right = hp_action_x - 18
        bar_w = max(TRACKER_MIN_HP_BAR_WIDTH, bar_right - bar_x)

        if not self.combatants:
            draw_text("No combatants yet.", left + 24, 36, 18, white, True)
            draw_text("Select a party, add creatures, then start the fight.", left + 24, 66, 13, muted, False)
            self.name_rects = []
            self.hp_button_rects = []
            self.status_rects = []
            self.hovered_hit = None
            return

        self.name_rects = []
        self.hp_button_rects = []
        self.status_rects = []
        draw_text("Init", left + 30, 22, 11, muted, True)
        draw_text("Type", left + 86, 22, 11, muted, True)
        draw_text("Name", name_x, 22, 11, muted, True)
        draw_right_fitted_text_centered("HP", NSMakeRect(hp_text_x, 18, hp_text_w, 20), 11, muted, True)
        draw_centered_text_in_rect("AC", NSMakeRect(ac_x, 18, ac_w, 20), 11, muted, True)
        draw_text("Status", status_x + 10, 22, 11, muted, True)

        row_y = 54
        row_h = 56
        gap = 12
        for index, combatant in enumerate(self.combatants):
            initiative = int(combatant.get("initiative") or 0)
            rect = NSMakeRect(left, row_y, width, row_h)
            is_current = index == self.current_turn_index
            is_down = self._hp_values(combatant)[0] is not None and self._hp_values(combatant)[0] <= 0
            is_dead = combatant_is_dead(combatant)
            conditions = normalized_conditions(combatant)
            row_fill = theme_color("surface_soft", 0.62 if is_down else 1.0)
            if conditions and not is_down:
                tint_source = condition_color(conditions[0], 1.0)
                row_fill = tint_source.colorWithAlphaComponent_(0.18)
            draw_rounded_rect(
                rect,
                row_fill,
                current_border if is_current else card_border,
                8,
                2.0 if is_current else 1.0,
            )
            draw_text(str(initiative), left + 36, row_y + 17, 17, white, True)
            if combatant.get("kind") == "Monster":
                icon_name = "Monster"
                fallback_icon = MONSTER_ICON
                fallback_color = pink
                subtitle = "Monstrosity" if not combatant.get("cr") else f"CR {combatant.get('cr')}"
                self.name_rects.append((NSMakeRect(name_x, row_y + 8, name_w, 36), index))
            else:
                class_name = str(combatant.get("class") or "Fighter")
                icon_name = class_name
                fallback_icon = CLASS_ICONS.get(class_name, "◆")
                fallback_color = white
                subtitle = class_name
            icon_rect = NSMakeRect(left + 84, row_y + 13, 26, 26)
            if not draw_icon(icon_name, icon_rect):
                draw_text(fallback_icon, left + 92, row_y + 15, 22, fallback_color, True)
            display_name = str(combatant.get("name") or "Unnamed")
            draw_fitted_text(display_name, NSMakeRect(name_x, row_y + 8, name_w, 20), 14, white, True)
            draw_fitted_text(subtitle, NSMakeRect(name_x, row_y + 29, name_w, 18), 12, muted, False)

            is_monster = combatant.get("kind") == "Monster"
            bar_y = row_y + 24
            bar_h = 8
            if is_monster:
                hp_button_w = hp_action_w
                hp_button_h = 28
                hp_button_y = row_y + (row_h - hp_button_h) / 2
                hp_button_rect = NSMakeRect(hp_action_x, hp_button_y, hp_button_w, hp_button_h)
                self.hp_button_rects.append((hp_button_rect, index))
                hp_button_state = draw_button_background(
                    hp_button_rect,
                    self.hovered_hit == ("hp", index, None),
                    False,
                    True,
                    False,
                    False,
                    7,
                )
                draw_centered_text_in_rect("+/-", hp_button_rect, 13, hp_button_state["text"], True)

                current_hp, max_hp = self._hp_values(combatant)
                bar_rect = NSMakeRect(bar_x, bar_y, bar_w, bar_h)
                if current_hp is not None and max_hp is not None and max_hp > 0:
                    try:
                        temp_hp = max(0, int(str(combatant.get("temp_hp") or "0")))
                    except ValueError:
                        temp_hp = 0
                    effective_max = max_hp + temp_hp
                    hp_ratio = max(0.0, min(1.0, current_hp / effective_max))
                    temp_ratio = max(0.0, min(1.0 - hp_ratio, temp_hp / effective_max))
                    fill_color = red if current_hp <= 0 else pink if current_hp / max_hp <= 0.35 else green
                    draw_segmented_rounded_bar(
                        bar_rect,
                        [
                            (bar_w * hp_ratio, fill_color),
                            (bar_w * temp_ratio, temp_blue),
                        ],
                        theme_color("panel_alt"),
                        4,
                    )
                    hp_text = f"{current_hp}/{max_hp}"
                else:
                    draw_segmented_rounded_bar(bar_rect, [], theme_color("panel_alt"), 4)
                    hp_text = "-"
                draw_right_fitted_text_centered(hp_text, NSMakeRect(hp_text_x, bar_y, hp_text_w, bar_h), 12, muted, False)
            else:
                pass

            draw_centered_text_in_rect(str(combatant.get("ac") or "?"), NSMakeRect(ac_x, row_y + 14, ac_w, 28), 15, white, False)

            status_label = combatant_status_label(combatant)
            status_color = dead_red if is_dead else condition_color(conditions[0]) if conditions else muted
            status_rect = NSMakeRect(status_x, row_y + 14, status_w, 28)
            self.status_rects.append((status_rect, index))
            draw_button_background(
                status_rect,
                self.hovered_hit == ("status", index, None),
                False,
                True,
                False,
                False,
                7,
            )
            draw_center_fitted_text(status_label, NSMakeRect(status_x + 8, row_y + 19, status_w - 16, 18), 12, status_color, True)

            row_y += row_h + gap
