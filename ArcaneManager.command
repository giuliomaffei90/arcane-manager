#!/bin/zsh
cd "$(dirname "$0")"

if [ "$1" = "stop" ] || [ "$1" = "kill" ]; then
  pkill -f "Arcane Manager.app/Contents/MacOS/Arcane Manager" 2>/dev/null || true
  pkill -f "Arcane Manager.app/Contents/MacOS/ArcaneManager" 2>/dev/null || true
  pkill -f "SpellAudio.py" 2>/dev/null || true
  exit 0
fi

if [ "$1" = "debug" ] || [ "$1" = "transcript" ]; then
  shift
  echo "Arcane Manager debug mode. Press Ctrl+C to quit."
  echo "Printing every phrase transcribed by Whisper."
  exec "Arcane Manager.app/Contents/MacOS/Arcane Manager" --backend whisper --debug "$@"
fi

open -n "Arcane Manager.app"
