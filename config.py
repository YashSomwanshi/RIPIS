"""
RIPIS Configuration Settings
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
QUESTIONS_DIR = os.path.join(BASE_DIR, "assets", "questions")

# FFmpeg path (for pydub audio processing)
FFMPEG_PATH = r"C:\ffmpeg-2026-02-04-git-627da1111c-full_build\bin"
if FFMPEG_PATH not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")

# Vosk Speech Recognition - using larger lgraph model for better accuracy
VOSK_MODEL_PATH = os.path.join(MODELS_DIR, "vosk-model-en-us-0.22-lgraph")
SAMPLE_RATE = 16000

# Piper TTS
PIPER_MODEL_PATH = os.path.join(MODELS_DIR, "Piper")
PIPER_VOICE = "en_US-lessac-high"

# Ollama LLM
# Using mistral for better conversational responses (deepseek-r1 is a reasoning model)
OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_HOST = "http://127.0.0.1:11434"

# Interview Settings
INTERVIEW_TYPES = ["DSA", "System Design", "DBMS", "Operating Systems", "OOP Concepts"]
HINT_LEVELS = 3  # Progressive hint depth

# UI Settings
WINDOW_TITLE = "RIPIS - Real-Time Interview Practice Intelligence System"
EDITOR_FONT_SIZE = 14
STATUS_UPDATE_INTERVAL = 100  # ms

# Audio Settings
AUDIO_CHUNK_SIZE = 8000
SILENCE_THRESHOLD = 1.5  # seconds of silence before processing
