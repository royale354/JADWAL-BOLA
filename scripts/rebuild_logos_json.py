#!/usr/bin/env python3
"""Bangun ulang logos.json dari file di assets/ + logos.sources.json."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_logo import (  # noqa: E402
    MANUAL_BADGES,
    SOURCES_JSON,
    TEAMS_DIR,
    build_logos_json,
    count_missing,
    save_team_logo,
    slugify,
)

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    sources: dict = {}
    if SOURCES_JSON.exists():
        sources = json.loads(SOURCES_JSON.read_text(encoding="utf-8")).get("teams", {})

    team_paths: dict[str, str] = {}
    for api_name, url in sources.items():
        slug = slugify(api_name)
        for ext in (".png", ".svg", ".jpg", ".webp"):
            p = TEAMS_DIR / f"{slug}{ext}"
            if p.exists() and p.stat().st_size > 200:
                team_paths[api_name] = f"assets/logos/teams/{p.name}".replace("\\", "/")
                break

    for name, url in MANUAL_BADGES.items():
        slug = slugify(name)
        found = any((TEAMS_DIR / f"{slug}{e}").exists() for e in (".png", ".svg", ".jpg"))
        if not found:
            save_team_logo(name, url, sources)
            time.sleep(2)
        for f in TEAMS_DIR.glob(f"{slug}.*"):
            if f.stat().st_size > 200:
                team_paths[name] = f"assets/logos/teams/{f.name}".replace("\\", "/")

    build_logos_json(team_paths, sources)
    missing = count_missing()
    print(f"File tim: {len(list(TEAMS_DIR.glob('*')))}")
    print(f"Entri logos.json tim: {len(json.loads((ROOT / 'logos.json').read_text())['teams'])}")
    print(f"Jadwal tanpa logo: {len(missing)}")
    if missing:
        print(", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
