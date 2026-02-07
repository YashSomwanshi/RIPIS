# RIPIS - Real-Time Interview Practice Intelligence System

A desktop-based AI mock interview system with real-time voice interaction.

## Features

- 🎙️ **Voice Interaction** - Speak naturally with the AI interviewer
- 💻 **Code Editor** - Write code with syntax highlighting
- 🤖 **AI Feedback** - Get real-time hints and feedback
- ⚡ **Ethical AI** - AI assistance is always visible and disclosed

## Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Ollama** installed and running
3. **Mistral model** pulled

### Setup

```bash
# 1. Install dependencies
pip install PyQt6 PyQt6-QScintilla vosk sounddevice numpy requests pyttsx3 ollama

# 2. Pull the AI model (in a separate terminal)
ollama pull mistral-r1:7b
ollama serve

# 3. Download Vosk model (optional, for better speech recognition)
# Download from: https://alphacephei.com/vosk/models
# Get: vosk-model-en-us-0.22-lgraph 
# Extract to: ripis/models/vosk-model-en-us-0.22-lgraph/

# 4. Run the application
python main.py
```

Or use the setup script (Windows):
```bash
setup.bat
```

## Usage

1. Click **"Start Interview"** to begin
2. The AI interviewer (Alex) will greet you
3. Say what type of interview you want (e.g., "DSA interview")
4. Solve the problem while explaining your approach
5. Click **"Request Hint"** if you're stuck
6. Click **"End Session"** when done

## Project Structure

```
ripis/
├── main.py                 # Entry point
├── config.py              # Configuration
├── setup.bat              # Windows setup script
├── core/
│   ├── ai_engine.py       # Ollama/DeepSeek integration
│   ├── interview_state.py # Interview flow management
│   └── prompt_templates.py # AI prompts
├── audio/
│   ├── speech_recognition.py # Vosk STT
│   └── text_to_speech.py     # TTS output
├── ui/
│   ├── main_window.py     # Main application
│   ├── code_editor.py     # Syntax-highlighted editor
│   └── status_panel.py    # Controls and transcript
├── assets/questions/      # Question bank
└── models/               # Voice models (Vosk, Piper)
```

## Ethical Notice

This tool is designed for **practice and learning only**:
- AI assistance is always visible
- Not intended for actual interviews or assessments
- All AI activity is disclosed

## Troubleshooting

**"Ollama not running"**
- Make sure Ollama is installed and run `ollama serve`

**"Vosk model not found"**
- Download the model from https://alphacephei.com/vosk/models
- Or the app will work with keyboard input

**"No audio output"**
- The app uses Windows SAPI by default
- Check your speaker settings

