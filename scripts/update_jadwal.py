#!/usr/bin/env python3
"""Ambil jadwal Goal.com, bersihkan nama klub, dan perbarui database logo otomatis."""

from __future__ import annotations

import json
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

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

# Kamus translasi manual untuk sinkronisasi nama Goal.com ke database logos.json Anda
KAMUS_ALIAS = {
    "dewa united": "Dewa United Banten",
    "bhayangkara fc": "Bhayangkara Presisi Lampung",
    "bhayangkara": "Bhayangkara Presisi Lampung",
    "psbs": "PSBS Biak",
    "psbs biak numfor": "PSBS Biak",
    "persik": "Persik Kediri",
    "persija": "Persija Jakarta",
    "persita": "Persita Tangerang",
    "persis": "Persis Solo",
    "bali united fc": "Bali United",
    "borneo fc": "Borneo FC Samarinda",
}

def fetch_html() -> str:
    req = Request(
        GOAL_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req) as res:
        return res.read().decode("utf-8")


def parse_indo_date(text: str) -> str | None:
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text, re.I)
    if not m:
        return None
    day, month_str, year = m.groups()
    month = BULAN.get(month_str.lower())
    if not month:
        return None
    return f"{year}-{int(month):02d}-{int(day):02d}"


def parse_matchup(text: str) -> tuple[str, str]:
    for sep in (" vs ", " VS ", " v "):
        if sep in text:
            parts = text.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return text.strip(), ""


def classify_tv(stations: str) -> tuple[list[str], list[str]]:
    if not stations or stations == "-" or stations == "TBC":
        return [], []
    parts = [p.strip() for p in stations.split("/") if p.strip()]
    free, paid = [], []
    for part in parts:
        lower = part.lower()
        if any(k in lower for k in PAID_KW):
            paid.append(part)
        elif any(t in lower for t in FREE_TV):
            free.append(part)
        elif "sport" in lower or any(c.isdigit() for c in lower):
            paid.append(part)
        else:
            free.append(part)
    return free, paid


def bersihkan_dan_sinkronkan_nama(nama: str, database_logos: dict) -> str:
    """Membersihkan nama klub dan mendeteksi apakah ada kecocokan di database logos.json."""
    nama_clean = nama.strip()
    nama_lower = nama_clean.lower()
    
    # 1. Cek kamus alias manual terlebih dahulu
    if nama_lower in KAMUS_ALIAS:
        return KAMUS_ALIAS[nama_lower]
        
    # 2. Fitur Auto-Update Logo: Cek apakah nama ini mirip dengan entri yang sudah ada di logos.json
    for nama_db in database_logos.get("teams", {}).keys():
        if nama_lower in nama_db.lower() or nama_db.lower() in nama_lower:
            return nama_db
            
    return nama_clean


def parse_schedules(html: str, database_logos: dict, tanggal_paksa: str | None = None) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    schedules = {}
    current_date = None

    content = soup.find("div", class_="article-body") or soup
    
    for el in content.find_all(["h3", "table"]):
        if el.name == "h3":
            parsed_date = parse_indo_date(el.get_text())
            # Jika user memaksa mengubah tanggal lewat fitur --date, gunakan tanggal paksa
            current_date = tanggal_paksa if tanggal_paksa else parsed_date
        elif el.name == "table" and current_date:
            for tr in el.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) < 4 or re.search(r"kick-off", cells[0], re.I):
                    continue
                
                raw_home, raw_away = parse_matchup(cells[1])
                
                # Gunakan fitur sinkronisasi logo & pembersihan nama
                home = bersihkan_dan_sinkronkan_nama(raw_home, database_logos)
                away = bersihkan_dan_sinkronkan_nama(raw_away, database_logos)
                
                tv_free, tv_paid = classify_tv(cells[3])
                schedules.setdefault(current_date, []).append({
                    "kickoff": cells[0],
                    "matchup": f"{home} vs {away}",
                    "home": home,
                    "away": away,
                    "competition": cells[2],
                    "tv": cells[3],
                    "tvFree": tv_free,
                    "tvPaid": tv_paid,
                })
    return schedules


def main() -> int:
    parser = argparse.ArgumentParser(description="Scraper Jadwal Bola Goal.com dengan Auto-Mapping Logo")
    parser.add_argument("--date", type=str, help="Paksa semua jadwal masuk ke tanggal tertentu (Format: YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_jadwal = root / "data" / "jadwal.json"
    out_logos = root / "logos.json"

    out_jadwal.parent.mkdir(parents=True, exist_ok=True)

    # Muat database logo yang ada untuk referensi fuzzy matching
    database_logos = {"teams": {}, "leagues": {}}
    if out_logos.exists():
        try:
            database_logos = json.loads(out_logos.read_text(encoding="utf-8"))
            print(f"✓ Berhasil memuat {len(database_logos.get('teams', {}))} database logo untuk validasi.")
        except Exception as e:
            print(f"⚠️ Gagal membaca logos.json, menggunakan pencocokan standar: {e}")

    print("→ Mengambil data dari Goal.com...")
    html = fetch_html()
    
    schedules = parse_schedules(html, database_logos, tanggal_paksa=args.date)
    
    total = sum(len(v) for v in schedules.values())
    if not total:
        print("ERROR: Tidak ada jadwal ditemukan.", file=sys.stderr)
        return 1

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": GOAL_URL,
        "schedules": schedules,
    }
    
    out_jadwal.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Berhasil menyimpan {total} pertandingan ke data/jadwal.json")
    
    if args.date:
        print(f"📢 Fitur Ubah Tanggal Aktif: Semua jadwal telah diarahkan ke tanggal [{args.date}]")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
