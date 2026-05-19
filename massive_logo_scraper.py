# =========================================================
# MASSIVE FOOTBALL LOGO SCRAPER
# Wikimedia Commons Version
# =========================================================
#
# INSTALL:
# pip install requests beautifulsoup4 tqdm
#
# =========================================================

import os
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# CONFIG
# =========================================================

SAVE_FOLDER = "LOGO_DUNIA"
MAX_THREADS = 30

os.makedirs(SAVE_FOLDER, exist_ok=True)

session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================================================
# KEYWORD PENCARIAN
# =========================================================

SEARCH_KEYWORDS = [
    "football club logo",
    "soccer club logo",
    "national football team logo",
    "fc logo",
    "football badge"
]

# =========================================================
# SAFE FILENAME
# =========================================================

def safe_name(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# =========================================================
# DOWNLOAD IMAGE
# =========================================================

def download_image(url):

    try:

        filename = url.split("/")[-1].split("?")[0]

        filename = safe_name(filename)

        filepath = os.path.join(SAVE_FOLDER, filename)

        if os.path.exists(filepath):
            return

        response = session.get(url, stream=True, timeout=30)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)

    except:
        pass

# =========================================================
# SCRAPE IMAGE URL
# =========================================================

def scrape_keyword(keyword):

    print(f"\nSearching: {keyword}")

    urls = []

    for page in range(1, 20):

        url = (
            "https://commons.wikimedia.org/w/index.php?"
            f"search={keyword}"
            "&title=Special:MediaSearch"
            "&type=image"
            f"&page={page}"
        )

        try:

            response = session.get(url, headers=HEADERS, timeout=30)

            soup = BeautifulSoup(response.text, "html.parser")

            imgs = soup.find_all("img")

            for img in imgs:

                src = img.get("src")

                if not src:
                    continue

                if any(x in src.lower() for x in [
                    ".png",
                    ".svg",
                    ".jpg",
                    ".jpeg",
                    "logo",
                    "badge"
                ]):
                    urls.append(src)

        except:
            pass

    return urls

# =========================================================
# MAIN
# =========================================================

all_urls = []

for keyword in SEARCH_KEYWORDS:

    urls = scrape_keyword(keyword)

    all_urls.extend(urls)

# =========================================================
# HAPUS DUPLIKAT
# =========================================================

all_urls = list(set(all_urls))

print(f"\nTotal gambar ditemukan: {len(all_urls)}")

# =========================================================
# DOWNLOAD
# =========================================================

with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:

    list(
        tqdm(
            executor.map(download_image, all_urls),
            total=len(all_urls),
            desc="Downloading"
        )
    )

print("\nSELESAI SEMUA")