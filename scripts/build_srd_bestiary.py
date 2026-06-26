#!/usr/bin/env python3
"""Build the bundled SRD bestiary JSON from Fantasy Statblocks."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import json5


SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "Obsidian-TTRPG-Community/fantasy-statblocks/main/src/bestiary/srd-bestiary.ts"
)
ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "bestiary_srd.json"


def main() -> int:
    source = urllib.request.urlopen(SOURCE_URL, timeout=30).read().decode("utf-8")
    marker = "export const BESTIARY: Monster[] ="
    position = source.index(marker) + len(marker)
    start = source.index("[", position)
    end = source.index("];", start) + 1
    creatures = json5.loads(source[start:end])

    payload = {
        "source": SOURCE_URL,
        "license_note": "SRD/OGL content as bundled by Fantasy Statblocks.",
        "creatures": creatures,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(creatures)} creatures to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
