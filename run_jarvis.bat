@echo off
title J.A.R.V.I.S. - Starting Up...
color 0E
echo.
echo  ============================================
echo   J.A.R.V.I.S. - Just A Rather Very Intelligent System
echo  ============================================
echo.
echo  [*] Initializing systems...
echo.

cd /d "%~dp0"

echo  [*] Updating dependencies...
pip install --upgrade google-genai psutil >nul 2>&1

echo  [*] Launching J.A.R.V.I.S....
echo.
python jarvis.py

echo.
echo  ============================================
echo   J.A.R.V.I.S. has shut down.
echo  ============================================
echo.
echo  Press any key to close this window...
pause >nul
