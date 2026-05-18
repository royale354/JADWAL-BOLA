#!/usr/bin/env python3
"""Ambil jadwal Goal.com dan simpan ke data/jadwal.json untuk GitHub Pages."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

GOAL_URL = (
    "https://www.goal.com/id/berita/"
    "jadwal-tv-siaran-langsung-sepakbola-hari-ini/"
    "1qomojcjyge9n1nr2voxutdc1n"
)

FREE_TV = {
    "rcti", "mnctv", "gtv", "sctv", "indosiar", "antv", "tvone",
    "kompas tv", "inews", "inews tv", "tvri", "trans tv", "trans7", "metro tv",
}
PAID_KW = {
    "vidio", "bein", "vision+", "vision plus", "mola", "spotv",
    "apple tv", "disney", "netflix", "prime video", "hbo", "espn", "dazn",
}

BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
}


def fetch_html() -> str:
    req = Request(
        GOAL_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; JadwalBolaBot/1.0)",
            "Accept-Language": "id-ID,id;q=0.9",
        },
    )
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_indo_date(text: str) -> str | None:
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text.strip(), re.I)
    if not m:
        return None
    month = BULAN.get(m.group(2).lower())
    if not month:
        return None
    return f"{m.group(3)}-{month:02d}-{int(m.group(1)):02d}"


def parse_matchup(text: str) -> tuple[str, str]:
    lower = text.lower()
    for sep in (" vs ", " v "):
        idx = lower.find(sep)
        if idx >= 0:
            return text[:idx].strip(), text[idx + len(sep):].strip()
    return text.strip(), ""


def classify_tv(stations: str) -> tuple[list[str], list[str]]:
    if not stations or stations.strip() in ("-", "TBC", "N/A"):
        return [], []
    parts = [p.strip() for p in re.split(r"\s*/\s*", stations) if p.strip()]
    free, paid = [], []
    for part in parts:
        lower = part.lower()
        is_paid = any(k in lower for k in PAID_KW)
        is_free = any(t in lower for t in FREE_TV)
        if is_paid:
            paid.append(part)
        elif is_free:
            free.append(part)
        elif re.search(r"sport|\d", part, re.I):
            paid.append(part)
        else:
            free.append(part)
    return free, paid


def parse_schedules(html: str) -> dict[str, list[dict]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    schedules: dict[str, list[dict]] = {}
    current_date: str | None = None

    for el in soup.find_all(["h3", "table"]):
        if el.name == "h3":
            current_date = parse_indo_date(el.get_text(strip=True))
        elif el.name == "table" and current_date:
            for tr in el.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) < 4 or re.search(r"kick-off", cells[0], re.I):
                    continue
                home, away = parse_matchup(cells[1])
                tv_free, tv_paid = classify_tv(cells[3])
                schedules.setdefault(current_date, []).append({
                    "kickoff": cells[0],
                    "matchup": cells[1],
                    "home": home,
                    "away": away,
                    "competition": cells[2],
                    "tv": cells[3],
                    "tvFree": tv_free,
                    "tvPaid": tv_paid,
                })
    return schedules


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    out = root / "data" / "jadwal.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    html = fetch_html()
    schedules = parse_schedules(html)
    total = sum(len(v) for v in schedules.values())
    if not total:
        print("ERROR: Tidak ada jadwal ditemukan.", file=sys.stderr)
        return 1

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": GOAL_URL,
        "schedules": schedules,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {total} pertandingan -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
