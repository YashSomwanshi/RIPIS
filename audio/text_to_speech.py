"""
Text-to-Speech Module using Piper
Natural offline voice synthesis for RIPIS
"""
import subprocess
import threading
import queue
import os
import sys
import wave
import tempfile
from typing import Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PIPER_MODEL_PATH, PIPER_VOICE

# Try to import audio playback libraries
try:
    import sounddevice as sd
    import numpy as np
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class PiperTTS:
    """Handles text-to-speech using Piper."""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or PIPER_MODEL_PATH
        self.voice = PIPER_VOICE
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speak_thread = None
        self.stop_requested = False
        
        # Callbacks
        self.on_speech_start: Optional[Callable[[], None]] = None
        self.on_speech_end: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Find Piper executable
        self.piper_exe = self._find_piper_executable()
        self.model_file = self._find_model_file()
    
    def _find_piper_executable(self) -> Optional[str]:
        """Find the Piper executable."""
        possible_paths = [
            os.path.join(self.model_path, "piper.exe"),
            os.path.join(self.model_path, "piper"),
            "piper.exe",
            "piper",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Check if piper is in PATH
        try:
            result = subprocess.run(["piper", "--help"], capture_output=True, timeout=5)
            if result.returncode == 0:
                return "piper"
        except:
            pass
        
        return None
    
    def _find_model_file(self) -> Optional[str]:
        """Find the Piper model file."""
        if not os.path.exists(self.model_path):
            return None
        
        # Look for .onnx model files
        for file in os.listdir(self.model_path):
            if file.endswith(".onnx"):
                return os.path.join(self.model_path, file)
        
        return None
    
    def initialize(self) -> bool:
        """Initialize TTS engine."""
        if not self.piper_exe:
            print("⚠ Piper not found. TTS will use fallback.")
            return self._initialize_fallback()
        
        if not self.model_file:
            print("⚠ Piper model not found. TTS will use fallback.")
            return self._initialize_fallback()
        
        print(f"✓ Piper TTS initialized with model: {os.path.basename(self.model_file)}")
        return True
    
    def _initialize_fallback(self) -> bool:
        """Initialize fallback TTS (Windows SAPI or print-only)."""
        # Try Windows SAPI
        try:
            import pyttsx3
            self.fallback_engine = pyttsx3.init()
            self.fallback_engine.setProperty('rate', 150)
            print("✓ Using pyttsx3 fallback TTS")
            return True
        except:
            pass
        
        print("⚠ No TTS available. Speech will be printed to console.")
        self.fallback_engine = None
        return True
    
    def speak(self, text: str, priority: bool = False):
        """Add text to speech queue."""
        if priority:
            # For priority messages, clear the queue and speak immediately
            self._clear_queue()
        
        self.speech_queue.put(text)
        
        if not self.is_speaking:
            self._start_speak_thread()
    
    def _start_speak_thread(self):
        """Start the background speaking thread."""
        if self.speak_thread and self.speak_thread.is_alive():
            return
        
        self.stop_requested = False
        self.speak_thread = threading.Thread(target=self._speak_loop, daemon=True)
        self.speak_thread.start()
    
    def _speak_loop(self):
        """Main speaking loop."""
        self.is_speaking = True
        
        while not self.stop_requested:
            try:
                text = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                break
            
            if self.on_speech_start:
                self.on_speech_start()
            
            try:
                self._synthesize_and_play(text)
            except Exception as e:
                if self.on_error:
                    self.on_error(f"TTS error: {e}")
                print(f"TTS error: {e}")
            
            if self.on_speech_end:
                self.on_speech_end()
        
        self.is_speaking = False
    
    def _synthesize_and_play(self, text: str):
        """Synthesize speech and play it."""
        # Try Piper first
        if self.piper_exe and self.model_file:
            self._piper_speak(text)
            return
        
        # Try fallback engine
        if hasattr(self, 'fallback_engine') and self.fallback_engine:
            self.fallback_engine.say(text)
            self.fallback_engine.runAndWait()
            return
        
        # Last resort: print to console
        print(f"🔊 [AI]: {text}")
    
    def _piper_speak(self, text: str):
        """Speak using Piper TTS."""
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Run Piper to generate audio
            process = subprocess.run(
                [
                    self.piper_exe,
                    "--model", self.model_file,
                    "--output_file", tmp_path
                ],
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=30
            )
            
            if process.returncode != 0:
                raise Exception(f"Piper failed: {process.stderr.decode()}")
            
            # Play the audio
            self._play_wav(tmp_path)
            
            # Cleanup
            os.unlink(tmp_path)
            
        except Exception as e:
            # Fallback to console output
            print(f"🔊 [AI]: {text}")
            raise
    
    def _play_wav(self, wav_path: str):
        """Play a WAV file."""
        if HAS_SOUNDDEVICE:
            self._play_with_sounddevice(wav_path)
        elif HAS_PYDUB:
            self._play_with_pydub(wav_path)
        else:
            # Windows fallback
            self._play_with_windows(wav_path)
    
    def _play_with_sounddevice(self, wav_path: str):
        """Play using sounddevice."""
        with wave.open(wav_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            audio_data = wf.readframes(wf.getnframes())
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            sd.play(audio_array, sample_rate)
            sd.wait()
    
    def _play_with_pydub(self, wav_path: str):
        """Play using pydub."""
        audio = AudioSegment.from_wav(wav_path)
        pydub_play(audio)
    
    def _play_with_windows(self, wav_path: str):
        """Play using Windows native player."""
        try:
            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        except:
            print(f"Could not play audio: {wav_path}")
    
    def stop(self):
        """Stop current speech and clear queue."""
        self.stop_requested = True
        self._clear_queue()
    
    def _clear_queue(self):
        """Clear the speech queue."""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
    
    def wait_until_done(self):
        """Wait until all speech is complete."""
        if self.speak_thread:
            self.speak_thread.join()


class SimpleTTS:
    """Simple TTS using pyttsx3 (Windows SAPI) - no external dependencies."""
    
    def __init__(self):
        self.engine = None
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speak_thread = None
        self.stop_requested = False
        
        self.on_speech_start: Optional[Callable[[], None]] = None
        self.on_speech_end: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def initialize(self) -> bool:
        """Initialize the TTS engine."""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice
            self.engine.setProperty('rate', 160)  # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
            
            # Try to use a better voice if available
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'david' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            print("✓ pyttsx3 TTS initialized")
            return True
        except ImportError:
            print("⚠ pyttsx3 not installed. Run: pip install pyttsx3")
            return False
        except Exception as e:
            print(f"⚠ TTS initialization failed: {e}")
            return False
    
    def speak(self, text: str, priority: bool = False):
        """Add text to speech queue."""
        if priority:
            self._clear_queue()
        
        self.speech_queue.put(text)
        
        if not self.is_speaking:
            self._start_speak_thread()
    
    def _start_speak_thread(self):
        """Start background speaking thread."""
        if self.speak_thread and self.speak_thread.is_alive():
            return
        
        self.stop_requested = False
        self.speak_thread = threading.Thread(target=self._speak_loop, daemon=True)
        self.speak_thread.start()
    
    def _speak_loop(self):
        """Main speaking loop."""
        self.is_speaking = True
        
        while not self.stop_requested:
            try:
                text = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                break
            
            if self.on_speech_start:
                self.on_speech_start()
            
            try:
                if self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
                else:
                    print(f"🔊 [AI]: {text}")
            except Exception as e:
                print(f"TTS error: {e}")
            
            if self.on_speech_end:
                self.on_speech_end()
        
        self.is_speaking = False
    
    def stop(self):
        """Stop speaking."""
        self.stop_requested = True
        self._clear_queue()
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
    
    def _clear_queue(self):
        """Clear speech queue."""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
    
    def wait_until_done(self):
        """Wait until speech is complete."""
        if self.speak_thread:
            self.speak_thread.join()


def get_tts_engine(use_piper: bool = True):
    """Factory function to get TTS engine."""
    if use_piper:
        tts = PiperTTS()
        if tts.initialize():
            return tts
    
    # Fallback to simple TTS
    tts = SimpleTTS()
    tts.initialize()
    return tts


if __name__ == "__main__":
    print("Testing TTS...")
    tts = get_tts_engine(use_piper=False)  # Use simple TTS for testing
    
    if tts.initialize():
        print("Speaking test message...")
        tts.speak("Hello! I am Alex, your interviewer today. Let's begin the technical interview.")
        tts.wait_until_done()
        print("TTS test complete!")
