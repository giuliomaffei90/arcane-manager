#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/bin/python3.13}"
APP_NAME="Arcane Whisperer"

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

rm -rf build dist "$APP_NAME.app" "$APP_NAME.spec" "$APP_NAME.zip" pyinstaller_build.log

.venv/bin/pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier "local.arcanewhisperer.overlay" \
  --icon "assets/ArcaneWhisperer.icns" \
  --add-data=spells.json:resources \
  --collect-all faster_whisper \
  --collect-all huggingface_hub \
  --collect-all tqdm \
  --collect-all ctranslate2 \
  --collect-all av \
  --collect-all sounddevice \
  --collect-all numpy \
  --collect-all pyobjc_core \
  --collect-all pyobjc_framework_Cocoa \
  --collect-all pyobjc_framework_AVFoundation \
  --collect-all pyobjc_framework_Speech \
  --hidden-import objc \
  --hidden-import Cocoa \
  --hidden-import AVFoundation \
  --hidden-import Speech \
  SpellAudio.py > pyinstaller_build.log 2>&1

PLIST="dist/$APP_NAME.app/Contents/Info.plist"
for key in NSMicrophoneUsageDescription NSSpeechRecognitionUsageDescription LSUIElement; do
  /usr/libexec/PlistBuddy -c "Delete :$key" "$PLIST" 2>/dev/null || true
done
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $APP_NAME" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleName $APP_NAME" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$PLIST" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string Arcane Whisperer uses the microphone to listen for spell names during your session." "$PLIST"
/usr/libexec/PlistBuddy -c "Add :NSSpeechRecognitionUsageDescription string Arcane Whisperer uses speech recognition to transcribe spell names." "$PLIST"

codesign --force --deep --sign - "dist/$APP_NAME.app"
cp -R "dist/$APP_NAME.app" .
codesign --force --deep --sign - "$APP_NAME.app"
ditto -c -k --sequesterRsrc --keepParent "$APP_NAME.app" "$APP_NAME.zip"

rm -rf build dist "$APP_NAME.spec" pyinstaller_build.log

du -sh "$APP_NAME.app" "$APP_NAME.zip"
