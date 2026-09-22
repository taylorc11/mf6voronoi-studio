@echo off
REM ===================================================================
REM  Checks whether a real Python 3.10-3.12 (64-bit) is on PATH.
REM  The "Python was not found... Microsoft Store" message is a Windows
REM  placeholder, not real Python - this script tells the difference.
REM ===================================================================
echo.
echo === Checking for Python ===
echo.

set "PY="
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 --version >nul 2>nul
    if %ERRORLEVEL%==0 set "PY=py -3"
)
if not defined PY (
    python --version >nul 2>nul
    if %ERRORLEVEL%==0 set "PY=python"
)

if not defined PY (
    echo Python was NOT found ^(or only the Microsoft Store placeholder is^).
    echo.
    echo Install Python 3.10 - 3.12 ^(64-bit^) from:
    echo     https://www.python.org/downloads/windows/
    echo During setup, TICK  "Add python.exe to PATH".
    echo.
    echo If it still fails afterwards, turn off the Store aliases under:
    echo   Settings ^> Apps ^> Advanced app settings ^> App execution aliases
    echo.
    pause
    exit /b 1
)

echo Found:
%PY% --version
echo.
echo You're ready:  pip install -r requirements.txt  ^&^&  python mf6voronoi_gui.py
echo.
pause
