#!/usr/bin/env python3
"""Isi logo tim yang masih kosong setelah auto_logo.py."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_logo import (  # noqa: E402
    ALIASES_JSON,
    FLAG_ISO,
    JADWAL_JSON,
    LOGOS_JSON,
    TEAMS_DIR,
    WIKI_PAGES,
    build_logos_json,
    count_missing,
    download_bytes,
    download_flag,
    download_from_wikipedia,
    index_team_files,
    jadwal_team_names,
    resolve_path,
    save_team_logo,
    slugify,
    team_badge_url,
    api_get,
)

# Tim yang sering gagal + mapping Wikipedia eksplisit
EXTRA_WIKI = {
    **WIKI_PAGES,
    "Persebaya Surabaya": ("Persebaya", "id"),
    "Bhayangkara Presisi Lampung": ("Bhayangkara_Presisi_Indonesia_FC", "id"),
    "Heidenheim": ("1._FC_Heidenheim", "en"),
    "Hoffenheim": ("TSG_1899_Hoffenheim", "en"),
    "West Ham United": ("West_Ham_United_F.C.", "en"),
    "Wolverhampton Wanderers": ("Wolverhampton_Wanderers_F.C.", "en"),
    "Neom": ("Neom_SC", "en"),
    "Pantai Gading": ("Ivory_Coast_national_football_team", "en"),
}

EXTRA_FLAGS = {**FLAG_ISO, "Mali": "ml", "Pantai Gading": "ci"}


def fetch_indonesian_teams(sources: dict, team_paths: dict) -> None:
    data = api_get("search_all_teams.php", {"l": "Indonesian Super League"})
    for team in data.get("teams") or []:
        name = team.get("strTeam")
        url = team_badge_url(team)
        if name and url:
            path = save_team_logo(name, url, sources)
            if path:
                team_paths[name] = path
        time.sleep(0.3)


def main() -> int:
    sources: dict = {}
    if (Path(__file__).resolve().parent.parent / "logos.sources.json").exists():
        sources = json.loads(
            (Path(__file__).resolve().parent.parent / "logos.sources.json").read_text(encoding="utf-8")
        ).get("teams", {})

    team_paths: dict[str, str] = {}
    for f in TEAMS_DIR.iterdir():
        if f.is_file():
            team_paths[f.stem] = f"assets/logos/teams/{f.name}".replace("\\", "/")

    print("Ambil ulang Liga Indonesia...")
    fetch_indonesian_teams(sources, team_paths)

    # Patch WIKI_PAGES sementara
    import auto_logo as mod

    old = mod.WIKI_PAGES
    mod.WIKI_PAGES = EXTRA_WIKI
    old_flag = mod.FLAG_ISO
    mod.FLAG_ISO = EXTRA_FLAGS

    missing = count_missing()
    print(f"Perlu diisi: {len(missing)}")
    for name in missing:
        print(f"  -> {name}")
        if name in EXTRA_FLAGS:
            path = download_flag(name, EXTRA_FLAGS[name], sources)
        else:
            path = download_from_wikipedia(name, sources)
        if path:
            team_paths[name] = path
        time.sleep(3.5)

    mod.WIKI_PAGES = old
    mod.FLAG_ISO = old_flag

    # Alias heidenheim
    hei = TEAMS_DIR / "fc-heidenheim.png"
    if hei.exists():
        dest = TEAMS_DIR / "heidenheim.png"
        if not dest.exists():
            dest.write_bytes(hei.read_bytes())
        team_paths["Heidenheim"] = "assets/logos/teams/heidenheim.png"

    build_logos_json(team_paths, sources)
    still = count_missing()
    print(f"\nSisa tanpa logo: {len(still)}")
    if still:
        print(", ".join(still))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
