@echo off
rem Double-click to open the scalp topomap player (time slider, play/pause).
rem Optional: run from a terminal with subject numbers, e.g.  topomap_player.bat 9 5 2
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Could not find .venv\Scripts\python.exe. Set up the environment first:
    echo     python -m venv .venv
    echo     .venv\Scripts\activate
    echo     pip install -r requirements.txt
    pause
    exit /b 1
)
set SUBJECTS=%*
if "%SUBJECTS%"=="" set SUBJECTS=9 5 2
echo Loading subjects %SUBJECTS% (the first load takes a few seconds)...
".venv\Scripts\python.exe" experiments\week1_topomap_player.py %SUBJECTS%
if errorlevel 1 pause
