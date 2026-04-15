@echo off
title A.D.A. - Starting Up...
color 0B
echo.
echo  ============================================
echo   A.D.A. - Advanced Digital Assistant
echo  ============================================
echo.
echo  [*] Initializing systems...
echo.

cd /d "%~dp0"

echo  [*] Launching A.D.A....
echo.
python ada.py

echo.
echo  ============================================
echo   A.D.A. has shut down.
echo  ============================================
echo.
echo  Press any key to close this window...
pause >nul
