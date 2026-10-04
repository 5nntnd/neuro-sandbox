@echo off
rem Double-click to open the raw EEG trace browser (channel checklist, notes).
rem Optional: run from a terminal with subject numbers, e.g.  browse_raw.bat 9 5 2
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
".venv\Scripts\python.exe" experiments\week1_browse_raw.py %SUBJECTS%
if errorlevel 1 pause
