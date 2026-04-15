@echo off
title Installing Dependencies...
color 0A
echo.
echo  ============================================
echo   Installing All Dependencies
echo  ============================================
echo.

cd /d "%~dp0"

echo  [1/2] Installing Python packages...
echo.
pip install google-genai python-dotenv elevenlabs PySide6 opencv-python Pillow numpy websockets pyaudio psutil
echo.
echo  [2/2] Verifying installation...
python -c "import google.genai; import elevenlabs; import PySide6; import cv2; import psutil; print('  [OK] All packages installed successfully!')"
echo.
echo  ============================================
echo   Installation Complete!
echo  ============================================
echo.
echo  You can now run:
echo    - run_jarvis.bat  (for J.A.R.V.I.S.)
echo    - run_ada.bat     (for A.D.A.)
echo.
echo  Press any key to close...
pause >nul
