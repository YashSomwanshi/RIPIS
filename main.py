"""
RIPIS - Real-Time Interview Practice Intelligence System

Main entry point for the application.
A desktop-based AI mock interview system with real-time voice interaction.

Author: RIPIS Team
License: MIT
Ethical Notice: This tool is designed for practice and learning only.
              AI assistance is always disclosed and visible.
"""
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import sounddevice
    except ImportError:
        missing.append("sounddevice")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    if missing:
        print("=" * 60)
        print("Missing dependencies detected!")
        print("=" * 60)
        print(f"\nPlease install: {', '.join(missing)}")
        print("\nRun the following command:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr install all dependencies with:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        return False
    
    return True


def check_ollama():
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✓ Ollama is running")
            return True
    except:
        pass
    
    print("⚠ Ollama is not running or not installed")
    print("  To use AI features, install Ollama and run: ollama serve")
    return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("  RIPIS - Real-Time Interview Practice Intelligence System")
    print("  Practice Mode | AI Assistance Disclosed")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Ollama
    check_ollama()
    
    print()
    print("Starting application...")
    print()
    
    # Import and run the application
    from ui.main_window import create_app
    
    app, window = create_app()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
