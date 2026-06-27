from __future__ import annotations

from .resources import LOG_FILE


def log(message: str, persist: bool = True):
    line = f"[Arcane Manager] {message}"
    print(line, flush=True)
    if not persist:
        return
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not LOG_FILE.exists():
            LOG_FILE.touch(mode=0o600)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        LOG_FILE.chmod(0o600)
    except OSError:
        pass
