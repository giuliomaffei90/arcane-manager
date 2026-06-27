from __future__ import annotations

from ..platform import *
from ..dice import DiceRollResult, roll_dice_formula
from ..logging_utils import log
from ..resources import APP_RETAINED_OBJECTS, DEFAULT_DICE_ROLLER_HTML
from ..theme import dice_theme_payload
from .core import theme_color, ui_color

DICE_ROLL_ANIMATOR: Any = None
THREE_D_DICE_ROLLER: Any = None
DICE_ASSET_SERVER: Any = None
DICE_ASSET_SERVER_THREAD: threading.Thread | None = None
DICE_ASSET_SERVER_URL = ""

class DiceRollView(NSView):
    roll_result: DiceRollResult | None
    frame_index: int

    def initWithFrame_(self, frame):
        self = objc.super(DiceRollView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.roll_result = None
        self.frame_index = 0
        return self

    def setRollResult_(self, result):
        self.roll_result = result
        self.frame_index = 0
        self.setNeedsDisplay_(True)

    def setFrameIndex_(self, frame_index: int):
        self.frame_index = int(frame_index)
        self.setNeedsDisplay_(True)

    @objc.python_method
    def _draw_text(self, text: str, rect, size: float, color, bold: bool = False, centered: bool = False):
        paragraph_style = None
        font = NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size)
        attributes = {
            NSFontAttributeName: font,
            NSForegroundColorAttributeName: color,
        }
        if paragraph_style is not None:
            attributes["NSParagraphStyle"] = paragraph_style
        string = NSString.alloc().initWithString_(str(text))
        if centered:
            text_size = string.sizeWithAttributes_(attributes)
            x = rect.origin.x + max(0, (rect.size.width - text_size.width) / 2)
            y = rect.origin.y + max(0, (rect.size.height - text_size.height) / 2)
            string.drawAtPoint_withAttributes_(NSMakePoint(x, y), attributes)
        else:
            string.drawInRect_withAttributes_(rect, attributes)

    @objc.python_method
    def _draw_die(self, x: float, y: float, size: float, value: str, sides: int, active: bool):
        shadow = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(x + 5, y - 5, size, size), 10, 10)
        theme_color("app_bg", 0.42).set()
        shadow.fill()

        side = NSBezierPath.bezierPath()
        side.moveToPoint_(NSMakePoint(x + size, y + 8))
        side.lineToPoint_(NSMakePoint(x + size + 12, y + 18))
        side.lineToPoint_(NSMakePoint(x + size + 12, y + size - 8))
        side.lineToPoint_(NSMakePoint(x + size, y + size))
        side.closePath()
        (theme_color("dice") if active else theme_color("surface")).set()
        side.fill()

        top = NSBezierPath.bezierPath()
        top.moveToPoint_(NSMakePoint(x + 8, y + size))
        top.lineToPoint_(NSMakePoint(x + 20, y + size + 10))
        top.lineToPoint_(NSMakePoint(x + size + 12, y + size + 10))
        top.lineToPoint_(NSMakePoint(x + size, y + size))
        top.closePath()
        (ui_color(0.48, 0.84, 0.56, 1.0) if active else theme_color("surface_hover")).set()
        top.fill()

        face = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(x, y, size, size), 10, 10)
        (ui_color(0.28, 0.70, 0.46, 1.0) if active else theme_color("surface")).set()
        face.fill()
        ui_color(0.74, 0.95, 0.78, 1.0).set()
        face.setLineWidth_(1.5)
        face.stroke()

        self._draw_text(str(value), NSMakeRect(x + 4, y + 4, size - 8, size - 8), 19, theme_color("text_strong"), True, True)
        self._draw_text(f"d{sides}", NSMakeRect(x + 4, y + size - 16, size - 8, 12), 8, theme_color("text", 0.78), False, True)

    def drawRect_(self, _rect):
        bounds = self.bounds()
        background = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 16, 16)
        theme_color("panel_alt", 0.96).set()
        background.fill()

        result = self.roll_result
        if result is None:
            return

        rolling = self.frame_index < 14
        title_color = theme_color("dice")
        self._draw_text(f"Rolling {result.expression}", NSMakeRect(20, bounds.size.height - 48, bounds.size.width - 40, 26), 16, title_color, True)

        dice_to_draw = min(result.count, 24)
        die_size = 50
        gap = 18
        per_row = max(1, min(8, int((bounds.size.width - 60) // (die_size + gap))))
        rows = max(1, (dice_to_draw + per_row - 1) // per_row)
        start_y = max(92, 118 + (rows - 1) * 70)
        for index in range(dice_to_draw):
            row = index // per_row
            column = index % per_row
            row_count = min(per_row, dice_to_draw - row * per_row)
            total_width = row_count * die_size + max(0, row_count - 1) * gap
            start_x = max(24, (bounds.size.width - total_width) / 2)
            die_x = start_x + column * (die_size + gap)
            die_y = start_y - row * 70
            if rolling:
                value = "?"
                wobble = ((self.frame_index + index) % 3 - 1) * 4
            else:
                value = str(result.rolls[index])
                wobble = 0
            self._draw_die(die_x, die_y + wobble, die_size, value, result.sides, rolling or value != "?")

        if result.count > dice_to_draw:
            self._draw_text(f"+ {result.count - dice_to_draw} more dice included in the total", NSMakeRect(24, 80, bounds.size.width - 48, 20), 12, theme_color("muted"), False, True)

        if not rolling:
            dice_sum = sum(result.rolls)
            details = f"Dice: {dice_sum}"
            if result.modifier:
                sign = "+" if result.modifier > 0 else "-"
                details = f"{details} {sign} {abs(result.modifier)}"
            self._draw_text(f"Total: {result.total}", NSMakeRect(24, 32, bounds.size.width - 48, 34), 24, theme_color("text_strong"), True, True)
            self._draw_text(details, NSMakeRect(24, 16, bounds.size.width - 48, 20), 12, theme_color("muted"), False, True)


class DiceRollAnimator(NSObject):
    panel: NSPanel
    view: DiceRollView
    timer: NSTimer | None
    hide_timer: NSTimer | None
    frame_index: int

    def init(self):
        self = objc.super(DiceRollAnimator, self).init()
        if self is None:
            return None
        self.timer = None
        self.hide_timer = None
        self.frame_index = 0
        screen = NSScreen.mainScreen().visibleFrame()
        width = min(820, int(screen.size.width * 0.82))
        height = 380
        x = screen.origin.x + (screen.size.width - width) / 2
        y = screen.origin.y + screen.size.height - height - 90
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskUtilityWindow
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setTitle_("Dice Roll")
        self.panel.setFloatingPanel_(True)
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setLevel_(24)
        self.panel.setBackgroundColor_(theme_color("panel_alt", 0.96))
        self.view = DiceRollView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        self.panel.setContentView_(self.view)
        self.panel.orderOut_(None)
        return self

    def showRoll_(self, result):
        if self.timer is not None:
            self.timer.invalidate()
            self.timer = None
        if self.hide_timer is not None:
            self.hide_timer.invalidate()
            self.hide_timer = None
        self.frame_index = 0
        self.view.setRollResult_(result)
        self.panel.orderFrontRegardless()
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.055,
            self,
            "advance:",
            None,
            True,
        )

    def advance_(self, _timer):
        self.frame_index += 1
        self.view.setFrameIndex_(self.frame_index)
        if self.frame_index >= 22:
            if self.timer is not None:
                self.timer.invalidate()
                self.timer = None
            self.hide_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                6.0,
                self,
                "hide:",
                None,
                False,
            )

    def hide_(self, _timer):
        self.hide_timer = None
        self.panel.orderOut_(None)


def show_dice_roll_animation(result: DiceRollResult):
    global DICE_ROLL_ANIMATOR
    if DICE_ROLL_ANIMATOR is None:
        DICE_ROLL_ANIMATOR = DiceRollAnimator.alloc().init()
        APP_RETAINED_OBJECTS.append(DICE_ROLL_ANIMATOR)
    DICE_ROLL_ANIMATOR.showRoll_(result)


class DiceAssetRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return

    def list_directory(self, _path):
        self.send_error(404, "No directory listing")
        return None


def start_dice_asset_server() -> str:
    global DICE_ASSET_SERVER, DICE_ASSET_SERVER_THREAD, DICE_ASSET_SERVER_URL
    if DICE_ASSET_SERVER_URL:
        return DICE_ASSET_SERVER_URL

    asset_root = DEFAULT_DICE_ROLLER_HTML.parent.parent
    if not asset_root.exists():
        raise FileNotFoundError(f"Dice asset root not found: {asset_root}")

    handler = functools.partial(DiceAssetRequestHandler, directory=str(asset_root))
    DICE_ASSET_SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    DICE_ASSET_SERVER.daemon_threads = True
    host, port = DICE_ASSET_SERVER.server_address
    DICE_ASSET_SERVER_URL = f"http://{host}:{port}"
    DICE_ASSET_SERVER_THREAD = threading.Thread(
        target=DICE_ASSET_SERVER.serve_forever,
        name="ArcaneManagerDiceAssets",
        daemon=True,
    )
    DICE_ASSET_SERVER_THREAD.start()
    log(f"3D dice asset server started: {DICE_ASSET_SERVER_URL}")
    return DICE_ASSET_SERVER_URL


class Dice3DRollerController(NSObject):
    panel: NSPanel
    web_view: WKWebView
    ready: bool
    pending_expression: str
    result_target: Any
    hide_timer: NSTimer | None

    def initWithHTMLPath_(self, html_path):
        self = objc.super(Dice3DRollerController, self).init()
        if self is None:
            return None
        self.ready = False
        self.pending_expression = ""
        self.result_target = None
        self.hide_timer = None

        screen = NSScreen.mainScreen().visibleFrame()
        width = screen.size.width
        height = screen.size.height
        style = NSWindowStyleMaskBorderless
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(screen.origin.x, screen.origin.y, width, height),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setTitle_("Arcane Manager Dice")
        self.panel.setFloatingPanel_(True)
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setLevel_(24)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        user_content = WKUserContentController.alloc().init()
        user_content.addScriptMessageHandler_name_(self, "diceRoll")
        error_script = """
        window.addEventListener('error', function(event) {
          try {
            window.webkit.messageHandlers.diceRoll.postMessage({
              type: 'error',
              text: event.message + ' at ' + event.filename + ':' + event.lineno + ':' + event.colno
            });
          } catch (_) {}
        });
        window.addEventListener('unhandledrejection', function(event) {
          try {
            var reason = event.reason && event.reason.message ? event.reason.message : String(event.reason);
            window.webkit.messageHandlers.diceRoll.postMessage({ type: 'error', text: reason });
          } catch (_) {}
        });
        """
        user_script = WKUserScript.alloc().initWithSource_injectionTime_forMainFrameOnly_(
            error_script,
            WKUserScriptInjectionTimeAtDocumentStart,
            False,
        )
        user_content.addUserScript_(user_script)
        config = WKWebViewConfiguration.alloc().init()
        config.setUserContentController_(user_content)
        self.web_view = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, width, height), config)
        self.web_view.setNavigationDelegate_(self)
        self.web_view.setValue_forKey_(False, "drawsBackground")
        self.panel.setContentView_(self.web_view)

        path = Path(str(html_path))
        if path.exists():
            base_url = start_dice_asset_server()
            request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(f"{base_url}/dice_roller/index.html"))
            self.web_view.loadRequest_(request)
        else:
            log(f"3D dice roller HTML not found: {path}")
        self.panel.orderOut_(None)
        return self

    def webView_didFinishNavigation_(self, _web_view, _navigation):
        return

    def webView_didFailNavigation_withError_(self, _web_view, _navigation, error):
        log(f"3D dice web view navigation failed: {error}")

    def webView_didFailProvisionalNavigation_withError_(self, _web_view, _navigation, error):
        log(f"3D dice web view provisional navigation failed: {error}")

    @objc.python_method
    def applyTheme(self):
        payload = json.dumps(dice_theme_payload())
        script = f"if (window.arcaneApplyTheme) {{ window.arcaneApplyTheme({payload}); }}"
        self.web_view.evaluateJavaScript_completionHandler_(script, None)

    def showRoll_target_(self, expression: str, target):
        self.result_target = target
        self.pending_expression = str(expression).strip()
        if self.hide_timer is not None:
            self.hide_timer.invalidate()
            self.hide_timer = None
        self.panel.orderFrontRegardless()
        if self.ready:
            self.evaluateRollExpression(self.pending_expression)

    @objc.python_method
    def evaluateRollExpression(self, expression: str):
        script = (
            f"if (window.arcaneApplyTheme) {{ window.arcaneApplyTheme({json.dumps(dice_theme_payload())}); }};"
            "if (window.arcanePrepareRoll) { window.arcanePrepareRoll(); }"
            f"window.arcaneRoll({json.dumps(expression)});"
        )
        self.web_view.evaluateJavaScript_completionHandler_(script, None)

    def userContentController_didReceiveScriptMessage_(self, _user_content_controller, message):
        body = message.body()
        if hasattr(body, "items"):
            payload = dict(body)
        elif hasattr(body, "objectForKey_"):
            payload = {
                key: body.objectForKey_(key)
                for key in ("type", "notation", "values", "modifier", "diceTotal", "total", "text")
                if body.objectForKey_(key) is not None
            }
        else:
            payload = {}
        message_type = str(payload.get("type", ""))
        if message_type == "ready":
            self.ready = True
            self.applyTheme()
            if self.pending_expression:
                self.evaluateRollExpression(self.pending_expression)
            return
        if message_type == "error":
            text = str(payload.get("text", "3D dice roll failed."))
            log(f"3D dice error: {text}")
            if self.result_target is not None:
                self.result_target.displayDiceRollResult_(text)
            self.scheduleHideTimer()
            return
        if message_type == "hide":
            if self.hide_timer is not None:
                self.hide_timer.invalidate()
                self.hide_timer = None
            self.panel.orderOut_(None)
            return
        if message_type != "complete":
            return

        text = str(payload.get("text", "Dice roll complete."))
        if self.result_target is not None:
            self.result_target.displayDiceRollResult_(text)
        self.scheduleHideTimer()

    @objc.python_method
    def scheduleHideTimer(self):
        if self.hide_timer is not None:
            self.hide_timer.invalidate()
        self.hide_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            12.0,
            self,
            "hide:",
            None,
            False,
        )

    def hide_(self, _timer):
        self.hide_timer = None
        self.panel.orderOut_(None)


def show_3d_dice_roll(expression: str, target) -> bool:
    global THREE_D_DICE_ROLLER
    if not DEFAULT_DICE_ROLLER_HTML.exists():
        return False
    if THREE_D_DICE_ROLLER is None:
        THREE_D_DICE_ROLLER = Dice3DRollerController.alloc().initWithHTMLPath_(str(DEFAULT_DICE_ROLLER_HTML))
        APP_RETAINED_OBJECTS.append(THREE_D_DICE_ROLLER)
    THREE_D_DICE_ROLLER.showRoll_target_(str(expression), target)
    return True
