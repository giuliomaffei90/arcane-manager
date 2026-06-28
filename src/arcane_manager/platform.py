from __future__ import annotations

import argparse
import functools
import html
import http.server
import json
import random
import re
import sys
import threading
import unicodedata
import warnings
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - startup dependency message covers installs
    BeautifulSoup = None

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - Adventure tab shows a friendly message
    MarkdownIt = None

try:
    import objc
    warnings.filterwarnings("ignore", category=objc.ObjCPointerWarning)
    from AppKit import (
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyRegular,
        NSAlert,
        NSBackingStoreBuffered,
        NSBezierPath,
        NSButton,
        NSButtonTypeSwitch,
        NSColor,
        NSColorWell,
        NSControlStateValueOff,
        NSControlStateValueOn,
        NSCursor,
        NSFont,
        NSFontAttributeName,
        NSFontManager,
        NSForegroundColorAttributeName,
        NSGraphicsContext,
        NSImage,
        NSImageView,
        NSItalicFontMask,
        NSMakeRect,
        NSMenu,
        NSMenuItem,
        NSOpenPanel,
        NSMutableParagraphStyle,
        NSPanel,
        NSParagraphStyleAttributeName,
        NSPopUpButton,
        NSScrollView,
        NSScreen,
        NSStatusBar,
        NSTrackingActiveAlways,
        NSTrackingArea,
        NSTrackingInVisibleRect,
        NSTrackingMouseEnteredAndExited,
        NSTrackingMouseMoved,
        NSTextView,
        NSTextFieldCell,
        NSVariableStatusItemLength,
        NSView,
        NSWindow,
        NSWindowCollectionBehaviorCanJoinAllSpaces,
        NSWindowCollectionBehaviorFullScreenAuxiliary,
        NSWindowStyleMaskBorderless,
        NSWindowStyleMaskClosable,
        NSWindowStyleMaskMiniaturizable,
        NSWindowStyleMaskResizable,
        NSWindowStyleMaskTitled,
        NSWindowStyleMaskUtilityWindow,
        NSWorkspace,
        NSWorkspaceRecycleOperation,
        NSTextField,
        NSCompositingOperationSourceOver,
        NSViewBoundsDidChangeNotification,
    )
    from WebKit import (
        WKUserContentController,
        WKUserScript,
        WKUserScriptInjectionTimeAtDocumentStart,
        WKWebView,
        WKWebViewConfiguration,
    )
    from Foundation import (
        NSMutableAttributedString,
        NSString,
        NSURL,
        NSURLRequest,
        NSMakePoint,
        NSMakeRange,
        NSMakeSize,
        NSObject,
        NSNotificationCenter,
        NSTimer,
        NSUserDefaults,
    )
except ImportError as exc:  # pragma: no cover - helpful startup error
    raise SystemExit(
        "Missing macOS dependency. Run:\n"
        "  .venv/bin/python -m pip install -r requirements.txt\n"
    ) from exc
