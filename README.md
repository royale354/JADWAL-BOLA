# Generator Jadwal Bola PNG

Tool HTML untuk jadwal siaran bola + logo klub/liga + export PNG TikTok 9:16.

## Pakai di HP (GitHub Pages)

1. Upload repo ke GitHub
2. **Settings → Pages** → branch **main** → folder **/**
3. Buka `https://USERNAME.github.io/NAMA-REPO/`

Jadwal di-update otomatis tiap hari (GitHub Actions → `data/jadwal.json`).

## Logo disimpan sebagai file (disarankan)

Logo ada di folder **`assets/logos/`** — lebih andal di HP (tanpa masalah CORS).

### Unduh logo (sekali di PC)

Double-click **`download-logos.bat`**

Lalu di GitHub Desktop: **commit + push** folder `assets/` + `logos.json`.

`logos.json` memakai path lokal, contoh:
`assets/logos/teams/real-madrid.png`

URL asli untuk unduh ulang: `logos.sources.json`

### Tambah logo baru

1. Tambah di `logos.sources.json`
2. Jalankan `download-logos.bat`
3. Commit & push

## Pakai di PC

Double-click **`start.bat`** → http://localhost:8788

## Struktur

| File | Fungsi |
|------|--------|
| `index.html` | Aplikasi |
| `logos.json` | Path logo lokal |
| `logos.sources.json` | URL sumber logo |
| `assets/logos/` | File PNG logo |
| `data/jadwal.json` | Jadwal |
| `download-logos.bat` | Unduh logo ke assets |
| `scripts/download_logos.py` | Script unduh logo |
| `scripts/update_jadwal.py` | Script jadwal |
| `.github/workflows/` | Auto-update harian |

