# RIPIS - Real-Time Interview Practice Intelligence System

## Complete Documentation

A desktop-based AI mock interview system featuring real-time voice interaction, intelligent feedback, and comprehensive mistake tracking.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Architecture](#architecture)
8. [Interview Flow](#interview-flow)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

RIPIS (Real-Time Interview Practice Intelligence System) is an AI-powered mock interview application designed to help developers practice technical interviews. It provides a realistic interview experience with:

- **Real-time voice interaction** using Vosk speech recognition
- **AI interviewer (Alex)** powered by Ollama/Mistral
- **Syntax-highlighted code editor** for writing solutions
- **Intelligent feedback** with mistake tracking
- **Edge case follow-ups** to test understanding

---

## Features

### Core Features
| Feature | Description |
|---------|-------------|
| 🎙️ **Voice Interaction** | Speak naturally with the AI interviewer using Vosk STT |
| 💻 **Code Editor** | Write code with Python/Java/C++/JavaScript syntax highlighting |
| 🤖 **AI Feedback** | Real-time feedback with [CORRECT]/[WRONG] tracking |
| 📊 **Mistake Tracking** | Records wrong answers and summarizes them before moving on |
| 🎯 **Edge Case Testing** | AI asks about edge cases after you complete a problem |
| 🔇 **Microphone Toggle** | Mute/unmute mic to prevent unwanted speech recognition |

### Interview Types Supported
- **DSA (Data Structures & Algorithms)** - Coding problems
- **System Design** - Architecture questions
- **DBMS** - Database concepts
- **Operating Systems** - OS fundamentals
- **OOP Concepts** - Object-oriented programming

---

## System Requirements

### Hardware
- Microphone (for voice input)
- Speakers (for AI voice output)
- Minimum 8GB RAM (for AI model)

### Software
- **Python 3.11+**
- **Ollama** (for LLM)
- **FFmpeg** (for audio processing)
- Windows 10/11 (tested)

---

## Installation

### Step 1: Install Python Dependencies

```bash
pip install PyQt6 PyQt6-QScintilla vosk sounddevice numpy requests pyttsx3 ollama pydub
```

### Step 2: Install and Configure Ollama

```bash
# Download Ollama from https://ollama.ai
# Then pull the Mistral model
ollama pull mistral:7b-instruct

# Start Ollama server
ollama serve
```

### Step 3: Download Vosk Model

1. Download from: https://alphacephei.com/vosk/models
2. Recommended: `vosk-model-en-us-0.22-lgraph` (better accuracy)
3. Extract to: `ripis/models/vosk-model-en-us-0.22-lgraph/`

### Step 4: Configure FFmpeg (Optional)

Update `config.py` with your FFmpeg path:
```python
FFMPEG_PATH = r"C:\path\to\ffmpeg\bin"
```

### Step 5: Run the Application

```bash
python main.py
```

---

## Configuration

### config.py Settings

```python
# Vosk Speech Recognition
VOSK_MODEL_PATH = "models/vosk-model-en-us-0.22-lgraph"
SAMPLE_RATE = 16000

# Ollama LLM
OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_HOST = "http://127.0.0.1:11434"

# Interview Settings
INTERVIEW_TYPES = ["DSA", "System Design", "DBMS", "Operating Systems", "OOP Concepts"]
HINT_LEVELS = 3  # Progressive hint depth

# Audio Settings
AUDIO_CHUNK_SIZE = 8000
SILENCE_THRESHOLD = 1.5  # seconds
```

---

## Usage Guide

### Starting an Interview

1. **Click "Start Interview"** - AI (Alex) greets you
2. **Choose interview type** - Say "coding" or "system design"
3. **Solve the problem** - Write code and explain your approach
4. **Get feedback** - AI responds with [CORRECT]/[WRONG] tags
5. **Handle edge cases** - AI asks follow-up edge case questions
6. **Click "End Session"** - Get summary with mistakes review

### Controls

| Button | Function |
|--------|----------|
| **Start Interview** | Begin a new interview session |
| **End Session** | End interview and get feedback summary |
| **Request Hint** | Get a progressive hint (3 levels) |
| **🎤 Mic Toggle** | Mute/unmute voice input |

### Voice Commands

| Say This | What Happens |
|----------|--------------|
| "coding" / "DSA" | Select coding interview |
| "system design" | Select system design interview |
| "I'm done" / "finished" | Move to follow-up questions |
| "hint" / "help" | Request a hint |

---

## Architecture

### Project Structure

```
ripis/
├── main.py                    # Application entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
│
├── core/                      # Core business logic
│   ├── ai_engine.py          # Ollama API integration
│   ├── interview_state.py    # State machine & flow control
│   └── prompt_templates.py   # AI prompt templates
│
├── audio/                     # Audio processing
│   ├── speech_recognition.py # Vosk STT integration
│   └── text_to_speech.py     # pyttsx3 TTS output
│
├── ui/                        # User interface
│   ├── main_window.py        # Main application window
│   ├── code_editor.py        # QScintilla code editor
│   └── status_panel.py       # Controls & transcript
│
├── assets/
│   └── questions/            # Question bank (JSON)
│
├── models/                    # ML models
│   ├── vosk-model-*/         # Vosk speech models
│   └── Piper/                # TTS models (optional)
│
└── utils/                     # Utility functions
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Window                          │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │   Code Editor    │  │       Status Panel              │ │
│  │  (QScintilla)    │  │  - Transcript                   │ │
│  │                  │  │  - Controls                     │ │
│  │                  │  │  - Mic Toggle                   │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
              │                        │
              ▼                        ▼
┌──────────────────────┐    ┌──────────────────────┐
│   Interview Worker   │    │  Speech Recognition  │
│     (QThread)        │    │      (Vosk)          │
└──────────────────────┘    └──────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────┐
│              Interview State Machine             │
│  States: IDLE → GREETING → SOLVING → CLOSING    │
└──────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────┐    ┌──────────────────────┐
│      AI Engine       │───▶│   Text-to-Speech     │
│    (Ollama API)      │    │     (pyttsx3)        │
└──────────────────────┘    └──────────────────────┘
```

---

## Interview Flow

### State Machine

```
IDLE → GREETING → TOPIC_SELECTION → QUESTION_PRESENTING → CANDIDATE_SOLVING
                                                              │
                                    ┌─────────────────────────┤
                                    ▼                         ▼
                              GIVING_HINT              FOLLOW_UP
                                    │                         │
                                    └─────────────────────────┤
                                                              ▼
                                                          CLOSING → ENDED
```

### Interview Logic

1. **Greeting Phase**
   - AI introduces itself
   - Asks for interview type preference

2. **Question Phase**
   - AI generates a problem based on type/difficulty
   - Displays in code editor
   - Speaks the problem explanation

3. **Solving Phase** (5 attempts max)
   - Listens to candidate responses
   - Provides feedback with [CORRECT]/[WRONG]/[UNCLEAR] tags
   - Records mistakes for later review
   - Filters garbage/noise input

4. **Follow-up Phase**
   - Asks edge case questions
   - Tests understanding of solution

5. **Transition Phase**
   - Gives feedback on mistakes from current question
   - Moves to next question OR concludes

6. **Closing Phase**
   - Summarizes all questions covered
   - Lists mistakes with corrections
   - Provides improvement suggestions

---

## API Reference

### AIEngine

```python
class AIEngine:
    def generate_response(prompt: str) -> str
        """Generate AI response using Ollama."""
    
    def reset_conversation() -> None
        """Clear conversation history."""
```

### InterviewStateMachine

```python
class InterviewStateMachine:
    def start_interview() -> str
        """Start new interview, returns greeting."""
    
    def process_user_input(text: str) -> str
        """Process user speech, returns AI response."""
    
    def end_interview() -> str
        """End interview, returns closing summary."""
    
    def request_hint() -> str
        """Get progressive hint (levels 1-3)."""
```

### InterviewContext

```python
@dataclass
class InterviewContext:
    interview_type: str      # DSA, System Design, etc.
    difficulty: str          # easy, medium, hard
    current_question: str    # Active problem
    current_code: str        # User's code
    hints_given: int         # Hint count (0-3)
    mistakes: list           # [{question, wrong_answer, correction}]
    follow_up_attempts: int  # Retry counter
    max_retries: int = 5     # Max attempts before moving on
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **"Ollama not running"** | Run `ollama serve` in terminal |
| **"Vosk model not found"** | Download model from alphacephei.com/vosk/models |
| **"No audio output"** | Check Windows speaker settings |
| **"FFmpeg not found"** | Update `FFMPEG_PATH` in config.py |
| **AI gives empty responses** | Increase API timeout in ai_engine.py |
| **Speech recognition garbled** | Use larger Vosk model (lgraph version) |

### Debug Logging

The application logs extensively. Watch for these prefixes:

- `[Speech RAW]` - Raw speech recognition output
- `[Speech FINAL]` - Cleaned speech text
- `[AI]` - AI engine requests/responses
- `[State]` - Interview state changes
- `[Worker]` - Background thread activity

### Performance Tips

1. **Use larger Vosk model** for better accuracy
2. **Reduce background noise** for cleaner speech input
3. **Speak clearly and at normal pace**
4. **Keep Ollama running** before starting app

---

## Ethical Notice

This tool is designed for **practice and learning only**:

- ✅ AI assistance is always visible and disclosed
- ✅ Intended for self-improvement and practice
- ❌ NOT intended for actual interviews or assessments
- ❌ NOT for cheating in real interview scenarios

---

