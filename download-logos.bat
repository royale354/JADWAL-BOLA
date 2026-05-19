@echo off
title Download Logo Klub - TheSportsDB
cd /d "%~dp0"
echo.
echo ==========================================
echo  AUTO DOWNLOAD LOGO CLUB BOLA
echo  Sumber: TheSportsDB + Wikipedia + flagcdn
echo ==========================================
echo.
py -3 -m pip install -r scripts\requirements.txt -q
py -3 scripts\auto_logo.py --fresh
if errorlevel 1 (
  echo.
  echo Gagal. Pastikan Python dan internet aktif.
  pause
  exit /b 1
)
echo.
echo Selesai! Commit folder assets/ + logos.json ke GitHub Desktop.
pause
