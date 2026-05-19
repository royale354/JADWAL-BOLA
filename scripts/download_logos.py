#!/usr/bin/env python3
"""Unduh semua logo ke folder assets/ dan perbarui logos.json ke path lokal."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
LOGOS_JSON = ROOT / "logos.json"
TEAMS_DIR = ROOT / "assets" / "logos" / "teams"
LEAGUES_DIR = ROOT / "assets" / "logos" / "leagues"
SOURCES_JSON = ROOT / "logos.sources.json"


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def ext_from_url(url: str, content_type: str | None) -> str:
    if "svg" in (content_type or "").lower() or url.lower().endswith(".svg"):
        return ".png" if ".png" in url.lower() else ".svg"
    if "jpeg" in (content_type or "").lower() or url.lower().endswith(".jpg"):
        return ".jpg"
    if url.lower().endswith(".webp"):
        return ".webp"
    return ".png"


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 200:
        return True
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; JadwalBola/1.0)"})
        with urlopen(req, timeout=25) as resp:
            data = resp.read()
            if len(data) < 100:
                return False
            ct = resp.headers.get("Content-Type", "")
            ext = ext_from_url(url, ct)
            if dest.suffix != ext and dest.suffix in (".png", ".jpg", ".svg", ".webp"):
                dest = dest.with_suffix(ext)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return True
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  FAIL {dest.name}: {e}")
        return False


def process_category(items: dict, folder: Path, prefix: str) -> dict:
    sources = {}
    local = {}
    ok = fail = 0

    for name, url in items.items():
        if not url or not url.startswith("http"):
            continue
        sources[name] = url
        fname = f"{slugify(name)}{ext_from_url(url, None)}"
        dest = folder / fname
        rel = f"assets/logos/{prefix}/{fname}"

        if download(url, dest):
            actual = dest
            if not dest.exists():
                for p in folder.glob(slugify(name) + ".*"):
                    actual = p
                    rel = f"assets/logos/{prefix}/{p.name}"
                    break
            local[name] = rel.replace("\\", "/")
            ok += 1
            print(f"  OK {name}")
        else:
            local[name] = url
            fail += 1
        time.sleep(0.15)

    return local, sources, ok, fail


def main() -> int:
    if not LOGOS_JSON.exists():
        print("logos.json tidak ditemukan", file=sys.stderr)
        return 1

    data = json.loads(LOGOS_JSON.read_text(encoding="utf-8"))
    teams_src = data.get("teams", {})
    leagues_src = data.get("leagues", {})

    print("Unduh logo klub...")
    teams_local, teams_sources, tok, tfk = process_category(teams_src, TEAMS_DIR, "teams")
    print(f"\nUnduh logo liga...")
    leagues_local, leagues_sources, lok, lfk = process_category(leagues_src, LEAGUES_DIR, "leagues")

    out = {"teams": teams_local, "leagues": leagues_local}
    LOGOS_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    sources = {"teams": teams_sources, "leagues": leagues_sources}
    SOURCES_JSON.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSelesai: klub {tok} OK / {tfk} gagal (pakai URL), liga {lok} OK / {lfk} gagal")
    print(f"Disimpan: {LOGOS_JSON}")
    print(f"Sumber asli: {SOURCES_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
