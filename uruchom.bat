@echo off
rem Uruchamia gre z kodu zrodlowego (wymaga zainstalowanego Pythona 3).
cd /d "%~dp0"
python -m pip install --quiet -r requirements.txt
python em.py
if errorlevel 1 pause
