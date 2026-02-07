"""
Speech Recognition Module using Vosk
Real-time, offline speech-to-text for RIPIS
"""
import queue
import threading
import json
import os
import sys
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOSK_MODEL_PATH, SAMPLE_RATE, AUDIO_CHUNK_SIZE, SILENCE_THRESHOLD

# Lazy imports to handle missing dependencies gracefully
vosk = None
sounddevice = None


def _import_dependencies():
    """Import audio dependencies lazily."""
    global vosk, sounddevice
    if vosk is None:
        try:
            import vosk as _vosk
            vosk = _vosk
            vosk.SetLogLevel(-1)  # Reduce logging
        except ImportError:
            raise ImportError("Vosk not installed. Run: pip install vosk")
    if sounddevice is None:
        try:
            import sounddevice as _sd
            sounddevice = _sd
        except ImportError:
            raise ImportError("sounddevice not installed. Run: pip install sounddevice")


class VoskSpeechRecognition:
    """Handles real-time speech recognition using Vosk."""
    
    def __init__(self, model_path: str = None):
        _import_dependencies()
        
        self.model_path = model_path or VOSK_MODEL_PATH
        self.sample_rate = SAMPLE_RATE
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None
        
        # Callbacks
        self.on_partial_result: Optional[Callable[[str], None]] = None
        self.on_final_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Silence detection
        self.silence_threshold = SILENCE_THRESHOLD
        self.last_speech_time = None
        
        # Debug mode
        self.debug = True
        
    def initialize(self) -> bool:
        """Initialize the Vosk model."""
        if not os.path.exists(self.model_path):
            error_msg = f"Vosk model not found at: {self.model_path}\nDownload from: https://alphacephei.com/vosk/models"
            if self.on_error:
                self.on_error(error_msg)
            print(error_msg)
            return False
        
        try:
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            print("✓ Vosk model loaded successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to load Vosk model: {e}"
            if self.on_error:
                self.on_error(error_msg)
            print(error_msg)
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean recognized text by removing common Vosk artifacts."""
        if not text:
            return ""
        
        original = text
        
        # Common false positives that Vosk picks up from background noise
        noise_words = ["the", "a", "uh", "um", "hmm", "ah", "oh", "eh", "huh"]
        
        # Remove leading noise words
        words = text.split()
        while words and words[0].lower() in noise_words and len(words) > 1:
            words = words[1:]
        
        # Remove trailing noise words
        while words and words[-1].lower() in noise_words and len(words) > 1:
            words = words[:-1]
        
        # If only noise words or too short, return empty
        if not words or len(words) == 0:
            return ""
        
        # Rejoin the cleaned text
        cleaned = " ".join(words)
        
        # Filter out very short results (likely noise)
        if len(cleaned) <= 2:
            return ""
        
        # Debug logging
        if self.debug and original != cleaned:
            print(f"[Speech] Cleaned: '{original}' -> '{cleaned}'")
        
        return cleaned
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def start_listening(self):
        """Start listening for speech."""
        if self.is_listening:
            return
        
        if not self.recognizer:
            if not self.initialize():
                return
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        print("🎤 Listening started...")
    
    def _listen_loop(self):
        """Main listening loop."""
        try:
            with sounddevice.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=AUDIO_CHUNK_SIZE,
                dtype='int16',
                channels=1,
                callback=self._audio_callback
            ):
                while self.is_listening:
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()
                        
                        # Debug: show raw recognition
                        if self.debug and text:
                            print(f"[Speech RAW] '{text}'")
                        
                        # Clean the result - remove common Vosk artifacts
                        text = self._clean_text(text)
                        
                        if text and self.on_final_result:
                            print(f"[Speech FINAL] '{text}'")
                            self.on_final_result(text)
                    else:
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get("partial", "").strip()
                        if partial_text and self.on_partial_result:
                            self.on_partial_result(partial_text)

                            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Listening error: {e}")
            print(f"Listening error: {e}")
        finally:
            self.is_listening = False
    
    def stop_listening(self):
        """Stop listening for speech."""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        print("🎤 Listening stopped")
    
    def get_final_result(self) -> str:
        """Get any remaining result from the recognizer."""
        if self.recognizer:
            result = json.loads(self.recognizer.FinalResult())
            return result.get("text", "").strip()
        return ""
    
    def test_microphone(self) -> bool:
        """Test if microphone is working."""
        _import_dependencies()
        try:
            # List available devices
            devices = sounddevice.query_devices()
            print("Available audio devices:")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"  [{i}] {device['name']}")
            
            # Test recording
            print("\nTesting microphone for 2 seconds...")
            recording = sounddevice.rec(
                int(2 * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16'
            )
            sounddevice.wait()
            
            # Check if we got audio
            import numpy as np
            max_amplitude = np.max(np.abs(recording))
            if max_amplitude > 100:
                print(f"✓ Microphone working! Max amplitude: {max_amplitude}")
                return True
            else:
                print(f"⚠ Microphone detected but very quiet. Max amplitude: {max_amplitude}")
                return True
                
        except Exception as e:
            print(f"✗ Microphone test failed: {e}")
            return False


class SimpleSpeechRecognition:
    """Simplified speech recognition for systems without Vosk model.
    Uses a mock implementation for testing UI flow."""
    
    def __init__(self):
        self.is_listening = False
        self.on_partial_result: Optional[Callable[[str], None]] = None
        self.on_final_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def initialize(self) -> bool:
        print("⚠ Using simplified speech recognition (mock mode)")
        return True
    
    def start_listening(self):
        self.is_listening = True
        print("🎤 Mock listening started (type in console to simulate speech)")
    
    def stop_listening(self):
        self.is_listening = False
        print("🎤 Mock listening stopped")
    
    def simulate_speech(self, text: str):
        """Simulate speech input for testing."""
        if self.on_final_result:
            self.on_final_result(text)


# Factory function to get the appropriate speech recognizer
def get_speech_recognizer(use_mock: bool = False):
    """Get a speech recognizer instance."""
    if use_mock:
        return SimpleSpeechRecognition()
    return VoskSpeechRecognition()


if __name__ == "__main__":
    # Test the speech recognition
    recognizer = VoskSpeechRecognition()
    
    # Test microphone first
    if recognizer.test_microphone():
        print("\nInitializing Vosk model...")
        if recognizer.initialize():
            print("Starting recognition test (speak for 10 seconds)...")
            
            def on_result(text):
                print(f"Recognized: {text}")
            
            recognizer.on_final_result = on_result
            recognizer.start_listening()
            
            import time
            time.sleep(10)
            
            recognizer.stop_listening()
            print("Test complete!")
