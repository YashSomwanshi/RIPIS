@echo off
echo ============================================
echo RIPIS - Setup Script
echo ============================================
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
echo.

pip install PyQt6 PyQt6-QScintilla vosk sounddevice numpy requests pyttsx3 ollama

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Some packages failed to install.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Dependencies installed successfully!
echo ============================================
echo.
echo Next steps:
echo 1. Download Vosk model from: https://alphacephei.com/vosk/models
echo    - Get "vosk-model-small-en-us" (about 40MB)
echo    - Extract to: ripis\models\vosk-model-small-en-us\
echo.
echo 2. Make sure Ollama is running:
echo    - Install from: https://ollama.com/download
echo    - Run: ollama pull deepseek-r1:7b
echo    - Run: ollama serve
echo.
echo 3. Run the application:
echo    python main.py
echo.
pause
