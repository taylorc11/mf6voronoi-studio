@echo off
REM ===================================================================
REM  Build mf6Voronoi Studio for Windows (exe -> portable ZIP -> installer)
REM ===================================================================
setlocal EnableDelayedExpansion

echo.
echo === mf6Voronoi Studio - Windows build ===
echo.

REM 0) Find a REAL Python (avoid the Microsoft Store stub)
set "PY="
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 --version >nul 2>nul
    if !ERRORLEVEL!==0 set "PY=py -3"
)
if not defined PY (
    python --version >nul 2>nul
    if !ERRORLEVEL!==0 set "PY=python"
)
if not defined PY (
    python3 --version >nul 2>nul
    if !ERRORLEVEL!==0 set "PY=python3"
)
if not defined PY (
    echo ============================ PYTHON NOT FOUND ============================
    echo  Python is not installed, or not on PATH. The "Python was not found"
    echo  message from Windows is a Microsoft Store placeholder - NOT real Python.
    echo.
    echo  Install Python 3.10 - 3.12 ^(64-bit^) from:
    echo      https://www.python.org/downloads/windows/
    echo  During setup, TICK  "Add python.exe to PATH".
    echo.
    echo  Then close this window and run build_windows.bat again.
    echo  ^(See INSTALL_WINDOWS.txt for details, or run CHECK_PYTHON.bat.^)
    echo =========================================================================
    pause
    exit /b 1
)

echo Using Python:  %PY%
%PY% --version
echo.

REM 1) Create + activate a virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment .venv ...
    %PY% -m venv .venv
    if !ERRORLEVEL! NEQ 0 ( echo Failed to create venv. & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
set "VPY=.venv\Scripts\python.exe"

REM 2) Install dependencies + PyInstaller
echo Installing dependencies (this can take a few minutes) ...
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install -r requirements.txt
"%VPY%" -m pip install pyinstaller
if %ERRORLEVEL% NEQ 0 ( echo Dependency install failed. & pause & exit /b %ERRORLEVEL% )

REM 3) Build the executable
echo Building executable ...
"%VPY%" -m PyInstaller --noconfirm mf6voronoi_studio.spec
if %ERRORLEVEL% NEQ 0 ( echo. & echo BUILD FAILED. See output above. & pause & exit /b %ERRORLEVEL% )

echo.
echo === Executable build complete ===
echo Your app is here:  dist\mf6VoronoiStudio\mf6VoronoiStudio.exe
echo.

REM 4) Optional portable ZIP
choice /M "Build the portable ZIP now"
if %ERRORLEVEL%==1 ( echo Building portable ZIP ... & "%VPY%" build_portable.py )

REM 5) Optional installer (needs Inno Setup 6)
choice /M "Build the Windows installer now (requires Inno Setup 6)"
if %ERRORLEVEL%==1 ( echo Building installer ... & "%VPY%" build_installer.py )

echo.
echo All done. Outputs:
echo   Executable   : dist\mf6VoronoiStudio\mf6VoronoiStudio.exe
echo   Portable ZIP : portable_output\
echo   Installer    : installer_output\
echo.
pause
endlocal
