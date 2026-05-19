#!/usr/bin/env python3
# =========================================================
# AUTO DOWNLOAD LOGO CLUB BOLA (lengkap)
# Sumber: TheSportsDB + Wikipedia + flagcdn (timnas)
# =========================================================
#   py -3 scripts/auto_logo.py
#   py -3 scripts/auto_logo.py --fresh
# =========================================================

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    from tqdm import tqdm
except ImportError:
    print("Install: pip install requests tqdm beautifulsoup4")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
TEAMS_DIR = ROOT / "assets" / "logos" / "teams"
LEAGUES_DIR = ROOT / "assets" / "logos" / "leagues"
LOGOS_JSON = ROOT / "logos.json"
SOURCES_JSON = ROOT / "logos.sources.json"
ALIASES_JSON = ROOT / "logos.aliases.json"
JADWAL_JSON = ROOT / "data" / "jadwal.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JadwalBola/1.0)"}
API = "https://www.thesportsdb.com/api/v1/json/3"

# Liga TheSportsDB (search_all_teams.php?l=) — ~10 klub/liga di API gratis
LEAGUES = [
    "English Premier League",
    "English League Championship",
    "English Womens Super League",
    "Spanish La Liga",
    "Spanish Segunda Division",
    "Italian Serie A",
    "Italian Serie B",
    "German Bundesliga",
    "German 2. Bundesliga",
    "French Ligue 1",
    "French Ligue 2",
    "Dutch Eredivisie",
    "Dutch Eerste Divisie",
    "Portuguese Primeira Liga",
    "Scottish Premiership",
    "Scottish Championship",
    "Belgian Pro League",
    "Turkish Super Lig",
    "Greek Super League",
    "Polish Ekstraklasa",
    "Danish Superliga",
    "Swedish Allsvenskan",
    "Norwegian Eliteserien",
    "Finnish Veikkausliiga",
    "Austrian Bundesliga",
    "Swiss Super League",
    "Ukrainian Premier League",
    "Romanian Liga I",
    "Croatian First Football League",
    "Serbian SuperLiga",
    "Hungarian NB I",
    "Slovak Super Liga",
    "Czech First League",
    "Welsh Premier League",
    "Irish Premier Division",
    "Indonesian Super League",
    "Malaysian Super League",
    "Singapore Premier League",
    "Thai League 1",
    "Vietnamese V.League 1",
    "Japanese J1 League",
    "Korean K League 1",
    "Chinese Super League",
    "Indian Super League",
    "Australian A-League",
    "Saudi Professional League",
    "UAE Pro League",
    "Qatar Stars League",
    "Egyptian Premier League",
    "South African Premier Division",
    "Moroccan Botola",
    "Argentine Primera Division",
    "Brazilian Serie A",
    "Chilean Primera División",
    "Colombian Categoría Primera A",
    "Mexican Primera League",
    "Major League Soccer",
    "USL Championship",
    "Russian Premier League",
]

# Nama di jadwal Goal.com → (judul Wikipedia, bahasa)
WIKI_PAGES: dict[str, tuple[str, str]] = {
    "Arema FC": ("Arema_F.C.", "id"),
    "PSBS Biak": ("PSBS_Biak", "id"),
    "Persija Jakarta": ("Persija_Jakarta", "id"),
    "Persik Kediri": ("Persik_Kediri", "id"),
    "Persebaya Surabaya": ("Persebaya", "id"),
    "Borneo FC Samarinda": ("Borneo_FC", "id"),
    "Persijap Jepara": ("Persijap_Jepara", "id"),
    "PSM Makassar": ("PSM_Makassar", "id"),
    "Persib Bandung": ("Persib_Bandung", "id"),
    "Madura United": ("Madura_United", "id"),
    "Persita Tangerang": ("Persita_Tangerang", "id"),
    "Persis Solo": ("Persis_Solo", "id"),
    "Dewa United Banten": ("Dewa_United", "id"),
    "Malut United": ("Malut_United", "id"),
    "Bali United": ("Bali_United", "id"),
    "Bhayangkara Presisi Lampung": ("Bhayangkara_Presisi_Indonesia_FC", "id"),
    "PSIM Yogyakarta": ("PSIM_Yogyakarta", "id"),
    "Semen Padang": ("Semen_Padang_F.C.", "id"),
    "Al-Nassr": ("Al-Nassr_FC", "en"),
    "Al-Hilal": ("Al-Hilal_SFC", "en"),
    "Lecce": ("US_Lecce", "en"),
    "LAFC": ("Los_Angeles_FC", "en"),
    "Nashville SC": ("Nashville_SC", "en"),
    "Buriram United": ("Buriram_United_F.C.", "en"),
    "Mamelodi Sundowns": ("Mamelodi_Sundowns_F.C.", "en"),
    "Zamalek": ("Zamalek_SC", "en"),
    "USM Alger": ("USM_Alger", "en"),
    "Selangor": ("Selangor_FC", "en"),
    "FAR Rabat": ("AS_FAR_(football)", "en"),
    "London City Lionesses": ("London_City_Lionesses", "en"),
    "Brighton & Hove Albion": ("Brighton_&_Hove_Albion_F.C.", "en"),
    "Tottenham Hotspur": ("Tottenham_Hotspur_F.C.", "en"),
    "West Ham United": ("West_Ham_United_F.C.", "en"),
    "Newcastle United": ("Newcastle_United_F.C.", "en"),
    "Leeds United": ("Leeds_United_F.C.", "en"),
    "Nottingham Forest": ("Nottingham_Forest_F.C.", "en"),
    "Wolverhampton Wanderers": ("Wolverhampton_Wanderers_F.C.", "en"),
    "Crystal Palace": ("Crystal_Palace_F.C.", "en"),
    "Manchester City": ("Manchester_City_F.C.", "en"),
    "Manchester United": ("Manchester_United_F.C.", "en"),
    "Inter Milan": ("Inter_Milan", "en"),
    "AC Milan": ("A.C._Milan", "en"),
    "AS Roma": ("A.S._Roma", "en"),
    "Bayern Munich": ("FC_Bayern_Munich", "en"),
    "Borussia Dortmund": ("Borussia_Dortmund", "en"),
    "Borussia Monchengladbach": ("Borussia_Mönchengladbach", "en"),
    "RB Leipzig": ("RB_Leipzig", "en"),
    "Atletico Madrid": ("Atlético_Madrid", "en"),
    "Athletic Bilbao": ("Athletic_Bilbao", "en"),
    "Real Sociedad": ("Real_Sociedad", "en"),
    "Rayo Vallecano": ("Rayo_Vallecano", "en"),
    "Deportivo Alaves": ("Deportivo_Alavés", "en"),
    "Inter Miami": ("Inter_Miami_CF", "en"),
    "Besiktas": ("Beşiktaş_J.K.", "en"),
    "Rizespor": ("Çaykur_Rizespor", "en"),
}

# Timnas / negara di jadwal → kode ISO flagcdn
FLAG_ISO: dict[str, str] = {
    "Korea Selatan": "kr",
    "Jepang": "jp",
    "Arab Saudi": "sa",
    "Afrika Selatan": "za",
    "RD Kongo": "cd",
    "Pantai Gading": "ci",
    "Aljazair": "dz",
    "Mesir": "eg",
    "Maroko": "ma",
    "Ghana": "gh",
    "Senegal": "sn",
    "Angola": "ao",
    "Kamerun": "cm",
    "Mali": "ml",
    "Pantai Gading": "ci",
    "Mozambik": "mz",
    "Tunisia": "tn",
    "Tanzania": "tz",
    "Uganda": "ug",
    "Etiopia": "et",
    "China": "cn",
    "Vietnam": "vn",
    "Uzbekistan": "uz",
    "Tajikistan": "tj",
    "Australia": "au",
}

DEFAULT_ALIASES = {
    "Arema FC": "Arema",
    "PSBS Biak": "PSBS Biak",
    "Persija Jakarta": "Persija Jakarta",
    "Persik Kediri": "Persik Kediri",
    "Persebaya Surabaya": "Persebaya Surabaya",
    "Borneo FC Samarinda": "Borneo Samarinda",
    "Borneo FC": "Borneo Samarinda",
    "Persijap Jepara": "Persijap Jepara",
    "PSM Makassar": "PSM Makassar",
    "Persib Bandung": "Persib Bandung",
    "Madura United": "Madura United",
    "Persita Tangerang": "Persita",
    "Persis Solo": "Persis Solo",
    "Dewa United Banten": "Dewa United Banten",
    "Malut United": "Malut United",
    "Bali United": "Bali United",
    "Bhayangkara Presisi Lampung": "Bhayangkara Presisi Lampung",
    "PSIM Yogyakarta": "PSIM Yogyakarta",
    "Semen Padang": "Semen Padang",
    "Brighton & Hove Albion": "Brighton and Hove Albion",
    "St. Pauli": "St Pauli",
    "Mainz 05": "Mainz",
    "Koln": "1. FC Köln",
    "Hellas Verona": "Verona",
    "LAFC": "Los Angeles FC",
    "Korea Selatan": "South Korea",
    "Arab Saudi": "Saudi Arabia",
    "Afrika Selatan": "South Africa",
    "RD Kongo": "DR Congo",
    "Pantai Gading": "Ivory Coast",
    "Aljazair": "Algeria",
    "Mesir": "Egypt",
    "Maroko": "Morocco",
    "Jepang": "Japan",
    "Heidenheim": "FC Heidenheim",
    "Hoffenheim": "TSG Hoffenheim",
    "West Ham United": "West Ham United",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers",
    "Pantai Gading": "Ivory Coast",
    "Mali": "Mali",
    "Persebaya Surabaya": "Persebaya Surabaya",
}

# URL langsung (hindari rate-limit Wikipedia thumb) untuk tim yang sering gagal
MANUAL_BADGES: dict[str, str] = {
    "PSBS Biak": "https://upload.wikimedia.org/wikipedia/id/9/9b/Logo_PSBS_Biak_baru.png",
    "PSIM Yogyakarta": "https://upload.wikimedia.org/wikipedia/id/9/9c/Logo_PSIM_Yogyakarta.png",
    "PSM Makassar": "https://upload.wikimedia.org/wikipedia/id/b/b8/Logo_PSM_Makasar_Baru.png",
    "Persik Kediri": "https://upload.wikimedia.org/wikipedia/id/c/cd/Logo_Persik_Kediri.png",
    "Persis Solo": "https://id.wikipedia.org/wiki/Special:FilePath/Persis_Solo_logo.svg",
    "Persita Tangerang": "https://id.wikipedia.org/wiki/Special:FilePath/Persita_logo_(2020).svg",
    "Semen Padang": "https://id.wikipedia.org/wiki/Special:FilePath/Semen_Padang_FC.png",
    "West Ham United": "https://crests.football-data.org/563.png",
    "Wolverhampton Wanderers": "https://crests.football-data.org/76.png",
    "Mali": "https://flagcdn.com/w160/ml.png",
    "Pantai Gading": "https://flagcdn.com/w160/ci.png",
    "Heidenheim": "https://r2.thesportsdb.com/images/media/team/badge/lbj7g01608236988.png",
    "Hoffenheim": "https://r2.thesportsdb.com/images/media/team/badge/2n2m7t1617113125.png",
}

LEAGUE_BADGE_URLS = {
    "Liga Inggris": "https://crests.football-data.org/PL.png",
    "Liga Inggris Wanita": "https://crests.football-data.org/PL.png",
    "Liga Spanyol": "https://crests.football-data.org/PD.png",
    "Liga Italia": "https://crests.football-data.org/SA.png",
    "Liga Jerman": "https://crests.football-data.org/BL1.png",
    "Liga Prancis": "https://crests.football-data.org/FL1.png",
    "Liga Turki": "https://crests.football-data.org/PL.png",
    "BRI Super League": "https://r2.thesportsdb.com/images/media/league/badge/qoz13e1630265283.png",
    "Piala FA": "https://crests.football-data.org/FLC.png",
    "Liga Champions": "https://crests.football-data.org/CL.png",
    "Liga Europa": "https://crests.football-data.org/EL.png",
    "MLS": "https://crests.football-data.org/MLS.png",
    "Saudi Pro League": "https://crests.football-data.org/SA.png",
    "Liga Champions Afrika": "https://crests.football-data.org/CL.png",
    "Liga Champions Asia Two": "https://crests.football-data.org/CL.png",
    "Piala Konfederasi Afrika": "https://crests.football-data.org/ACN.png",
    "Piala Afrika U-17 2026": "https://crests.football-data.org/ACN.png",
    "Piala Asia U-17 2026": "https://crests.football-data.org/AS.png",
    "ASEAN Club Championship": "https://r2.thesportsdb.com/images/media/league/badge/qoz13e1630265283.png",
}


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def team_badge_url(team: dict) -> str | None:
    return team.get("strTeamBadge") or team.get("strBadge") or team.get("strLogo") or None


def ext_for_url(url: str, content_type: str = "") -> str:
    u = url.lower().split("?")[0]
    if ".svg" in u or "svg" in content_type.lower():
        return ".svg"
    if ".jpg" in u or "jpeg" in content_type.lower():
        return ".jpg"
    return ".png"


def download_bytes(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=35, headers=HEADERS, stream=True)
        r.raise_for_status()
        data = r.content
        if len(data) < 200:
            return False
        ct = r.headers.get("Content-Type", "")
        ext = ext_for_url(url, ct)
        if dest.suffix != ext:
            dest = dest.with_suffix(ext)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest.stat().st_size > 200
    except Exception as e:
        print(f"  GAGAL unduh {dest.name}: {e}")
        return False


def api_get(path: str, params: dict | None = None, retries: int = 4) -> dict:
    url = f"{API}/{path}"
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=45, headers=HEADERS)
            if not r.text.strip():
                raise ValueError("empty response")
            return r.json()
        except Exception as e:
            wait = 2 + attempt * 2
            if attempt < retries - 1:
                time.sleep(wait)
            else:
                print(f"  API gagal {path}: {e}")
    return {}


def get_teams(league_name: str) -> list[dict]:
    data = api_get("search_all_teams.php", {"l": league_name})
    teams = data.get("teams") or []
    print(f"  {league_name}: {len(teams)} klub")
    return teams


def fetch_all_teams() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for league in LEAGUES:
        for team in get_teams(league):
            tid = team.get("idTeam")
            if tid:
                by_id[tid] = team
        time.sleep(0.5)
    return by_id


def save_team_logo(name: str, url: str, sources: dict) -> str | None:
    slug = slugify(name)
    ext = ext_for_url(url)
    dest = TEAMS_DIR / f"{slug}{ext}"
    sources[name] = url
    if dest.exists() and dest.stat().st_size > 200:
        return f"assets/logos/teams/{dest.name}".replace("\\", "/")
    if download_bytes(url, dest):
        actual = dest
        if not dest.exists():
            for p in TEAMS_DIR.glob(f"{slug}.*"):
                actual = p
                break
        return f"assets/logos/teams/{actual.name}".replace("\\", "/")
    return None


def wiki_infobox_image(title: str, lang: str) -> str | None:
    url = f"https://{lang}.wikipedia.org/wiki/{title}"
    try:
        r = requests.get(url, timeout=25, headers=HEADERS)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        img = soup.select_one(".infobox img")
        if not img:
            return None
        src = img.get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        return src or None
    except Exception:
        return None


def guess_wiki_titles(name: str) -> list[tuple[str, str]]:
    if name in WIKI_PAGES:
        return [WIKI_PAGES[name]]
    base = re.sub(r"[^a-zA-Z0-9\s]", "", name).strip().replace(" ", "_")
    candidates = [
        (base, "id"),
        (f"{base}_F.C.", "id"),
        (f"{base}_FC", "id"),
        (base, "en"),
        (f"{base}_F.C.", "en"),
        (f"{base}_FC", "en"),
    ]
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def download_from_wikipedia(name: str, sources: dict) -> str | None:
    slug = slugify(name)
    for p in TEAMS_DIR.glob(f"{slug}.*"):
        if p.stat().st_size > 200:
            return f"assets/logos/teams/{p.name}".replace("\\", "/")

    for title, lang in guess_wiki_titles(name):
        img_url = wiki_infobox_image(title, lang)
        if img_url:
            path = save_team_logo(name, img_url, sources)
            if path:
                print(f"  Wiki OK: {name}")
                return path
        time.sleep(0.35)
    return None


def download_flag(name: str, iso: str, sources: dict) -> str | None:
    url = f"https://flagcdn.com/w160/{iso.lower()}.png"
    sources[name] = url
    return save_team_logo(name, url, sources)


def jadwal_team_names() -> set[str]:
    names: set[str] = set()
    if not JADWAL_JSON.exists():
        return names
    data = json.loads(JADWAL_JSON.read_text(encoding="utf-8"))
    for day_matches in data.get("schedules", {}).values():
        for m in day_matches:
            for key in ("home", "away"):
                n = (m.get(key) or "").strip()
                if n:
                    names.add(n)
    return names


def clear_assets() -> None:
    print("Menghapus logo lama...")
    for folder in (TEAMS_DIR, LEAGUES_DIR):
        folder.mkdir(parents=True, exist_ok=True)
        for f in folder.iterdir():
            if f.is_file():
                f.unlink()


def load_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    if ALIASES_JSON.exists():
        aliases.update(json.loads(ALIASES_JSON.read_text(encoding="utf-8")))
    aliases.update(DEFAULT_ALIASES)
    for name in jadwal_team_names():
        if name not in aliases:
            aliases[name] = name
    return aliases


def index_team_files() -> dict[str, str]:
    index: dict[str, str] = {}
    for f in TEAMS_DIR.iterdir():
        if not f.is_file():
            continue
        rel = f"assets/logos/teams/{f.name}".replace("\\", "/")
        index[f.stem] = rel
        index[normalize(f.stem)] = rel
        index[slugify(f.stem)] = rel
    return index


def resolve_path(name: str, team_paths: dict[str, str], file_index: dict[str, str]) -> str | None:
    if not name:
        return None
    if name in team_paths:
        return team_paths[name]
    for key in (slugify(name), normalize(name)):
        if key in file_index:
            return file_index[key]
    norm = normalize(name)
    for stem, path in file_index.items():
        if normalize(stem) == norm:
            return path
    return None


def build_logos_json(team_paths: dict[str, str], sources: dict) -> None:
    aliases = load_aliases()
    file_index = index_team_files()
    teams_out: dict[str, str] = {}

    for name, path in team_paths.items():
        if path:
            teams_out[name] = path
            teams_out[slugify(name)] = path

    for goal_name, api_name in aliases.items():
        path = resolve_path(api_name, team_paths, file_index) or resolve_path(goal_name, team_paths, file_index)
        if path:
            teams_out[goal_name] = path
            teams_out[api_name] = path

    for f in TEAMS_DIR.iterdir():
        if not f.is_file():
            continue
        rel = f"assets/logos/teams/{f.name}".replace("\\", "/")
        teams_out[f.stem] = rel
        teams_out[normalize(f.stem.replace("-", " "))] = rel

    leagues_out: dict[str, str] = {}
    league_sources: dict[str, str] = {}

    if JADWAL_JSON.exists():
        data = json.loads(JADWAL_JSON.read_text(encoding="utf-8"))
        for day_matches in data.get("schedules", {}).values():
            for m in day_matches:
                comp = (m.get("competition") or "").strip()
                if comp and comp not in LEAGUE_BADGE_URLS:
                    LEAGUE_BADGE_URLS.setdefault(comp, "https://crests.football-data.org/PL.png")

    for league_name, url in LEAGUE_BADGE_URLS.items():
        league_sources[league_name] = url
        dest = LEAGUES_DIR / f"{slugify(league_name)}.png"
        if download_bytes(url, dest):
            leagues_out[league_name] = f"assets/logos/leagues/{dest.name}".replace("\\", "/")
        else:
            leagues_out[league_name] = url
        time.sleep(0.15)

    LOGOS_JSON.write_text(
        json.dumps({"teams": teams_out, "leagues": leagues_out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    SOURCES_JSON.write_text(
        json.dumps({"teams": sources, "leagues": league_sources}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ALIASES_JSON.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nlogos.json: {len(teams_out)} entri tim, {len(leagues_out)} liga")


def count_missing() -> list[str]:
    logos = json.loads(LOGOS_JSON.read_text(encoding="utf-8"))["teams"] if LOGOS_JSON.exists() else {}
    missing = []
    for name in sorted(jadwal_team_names()):
        if not resolve_path(name, logos, index_team_files()):
            missing.append(name)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true", help="Hapus semua logo lama dulu")
    args = parser.parse_args()

    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    LEAGUES_DIR.mkdir(parents=True, exist_ok=True)

    if args.fresh:
        clear_assets()

    print("=" * 50)
    print("DOWNLOAD LOGO LENGKAP")
    print("=" * 50)

    team_paths: dict[str, str] = {}
    sources: dict[str, str] = {}

    print("\n[1/3] TheSportsDB — daftar liga...")
    all_teams = fetch_all_teams()
    print(f"Total klub API: {len(all_teams)}")

    for team in tqdm(list(all_teams.values()), desc="Unduh API", unit="tim"):
        name = team.get("strTeam")
        url = team_badge_url(team)
        if name and url:
            path = save_team_logo(name, url, sources)
            if path:
                team_paths[name] = path
        time.sleep(0.2)

    print("\n[2/3] Wikipedia + bendera — tim di jadwal...")
    for name, url in MANUAL_BADGES.items():
        if not resolve_path(name, team_paths, index_team_files()):
            path = save_team_logo(name, url, sources)
            if path:
                team_paths[name] = path
        time.sleep(0.5)

    for name in tqdm(sorted(jadwal_team_names()), desc="Lengkapi jadwal", unit="tim"):
        if resolve_path(name, team_paths, index_team_files()):
            continue
        if name in MANUAL_BADGES:
            continue
        if name in FLAG_ISO:
            path = download_flag(name, FLAG_ISO[name], sources)
            if path:
                team_paths[name] = path
            continue
        path = download_from_wikipedia(name, sources)
        if path:
            team_paths[name] = path
        time.sleep(0.25)

    print("\n[3/3] Membuat logos.json...")
    build_logos_json(team_paths, sources)

    missing = count_missing()
    files = list(TEAMS_DIR.glob("*"))
    print(f"\nFile logo: {len(files)}")
    print(f"Tim jadwal tanpa logo: {len(missing)}")
    if missing:
        print("  ", ", ".join(missing[:30]), ("..." if len(missing) > 30 else ""))

    print("\n===================================")
    print("SELESAI — commit assets/ + logos.json")
    print("===================================")
    return 0 if not missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
