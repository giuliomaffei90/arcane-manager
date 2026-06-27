#!/bin/zsh
cd "$(dirname "$0")"

if [ "$1" = "stop" ] || [ "$1" = "kill" ]; then
  pkill -f "Arcane Manager.app/Contents/MacOS/Arcane Manager" 2>/dev/null || true
  pkill -f "Arcane Manager.app/Contents/MacOS/ArcaneManager" 2>/dev/null || true
  pkill -f "main.py" 2>/dev/null || true
  exit 0
fi

if [ "$1" = "debug" ]; then
  shift
  echo "Arcane Manager debug mode. Press Ctrl+C to quit."
  exec .venv/bin/python main.py "$@"
fi

open -n "Arcane Manager.app"
