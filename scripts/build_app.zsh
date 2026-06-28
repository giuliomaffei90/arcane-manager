#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/bin/python3.13}"
APP_NAME="Arcane Manager"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [ ! -x ".venv/bin/python" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

if [ -f requirements.lock.txt ]; then
  .venv/bin/python -m pip install -r requirements.lock.txt
else
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt pyinstaller
fi

rm -rf build dist "$APP_NAME.app" "$APP_NAME.spec" "$APP_NAME.zip" "$APP_NAME"*.dmg(N) pyinstaller_build.log

.venv/bin/pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier "local.arcanemanager.overlay" \
  --icon "assets/ArcaneManager.icns" \
  --add-data=spells.json:resources \
  --add-data=bestiary_srd.json:resources \
  --add-data=assets/icons:resources/assets/icons \
  --add-data=assets/dice_roller:resources/assets/dice_roller \
  --add-data=assets/three-dice:resources/assets/three-dice \
  --collect-all pyobjc_core \
  --collect-all pyobjc_framework_Cocoa \
  --collect-all WebKit \
  --collect-all JavaScriptCore \
  --hidden-import objc \
  --hidden-import Cocoa \
  --hidden-import WebKit \
  --hidden-import JavaScriptCore \
  --paths src \
  main.py > pyinstaller_build.log 2>&1

PLIST="dist/$APP_NAME.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :LSUIElement" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $APP_NAME" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleName $APP_NAME" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$PLIST" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST"

codesign --force --deep --sign - "dist/$APP_NAME.app"
cp -R "dist/$APP_NAME.app" .
codesign --force --deep --sign - "$APP_NAME.app"

rm -rf build dist "$APP_NAME.spec" pyinstaller_build.log

du -sh "$APP_NAME.app"
