"""
Main Window for RIPIS
The primary application window integrating all components
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QSplitter, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WINDOW_TITLE, STATUS_UPDATE_INTERVAL


class InterviewWorker(QThread):
    """Worker thread for handling AI responses using a task queue."""
    
    response_ready = pyqtSignal(str)  # AI response text
    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    task_complete = pyqtSignal()  # Signal when a task is done
    
    def __init__(self, interview_state, tts_engine):
        super().__init__()
        self.interview_state = interview_state
        self.tts_engine = tts_engine
        self.task_queue = []
        self.running = True
        self.is_busy = False
        
    def queue_action(self, action: str, user_input: str = "", code: str = ""):
        """Queue an action to perform."""
        self.task_queue.append({
            "action": action,
            "user_input": user_input,
            "code": code
        })
        print(f"[Worker] Queued action: {action}")
        
    def run(self):
        """Main worker loop - processes tasks from queue."""
        print("[Worker] Thread started")
        import time
        
        while self.running:
            if self.task_queue and not self.is_busy:
                task = self.task_queue.pop(0)
                self.is_busy = True
                self._process_task(task)
                self.is_busy = False
                self.task_complete.emit()
            else:
                time.sleep(0.1)  # Small sleep to prevent CPU spinning
        
        print("[Worker] Thread stopped")
    
    def _process_task(self, task):
        """Process a single task."""
        action = task["action"]
        user_input = task["user_input"]
        code = task["code"]
        
        print(f"[Worker] Processing action: {action}")
        
        try:
            response = ""
            
            if action == "start":
                response = self.interview_state.start_interview()
            elif action == "process":
                response = self.interview_state.process_user_input(user_input, code)
            elif action == "hint":
                response = self.interview_state.request_hint()
            elif action == "end":
                response = self.interview_state.end_interview()
            
            print(f"[Worker] Got response: {response[:100] if response else 'None'}...")
            
            if response:
                self.response_ready.emit(response)
                
                # Speak the response
                if self.tts_engine:
                    self.speaking_started.emit()
                    try:
                        self.tts_engine.speak(response)
                        self.tts_engine.wait_until_done()
                    except Exception as e:
                        print(f"[Worker] TTS Error: {e}")
                    self.speaking_finished.emit()
                    
        except Exception as e:
            print(f"[Worker] Error: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Stop the worker thread."""
        self.running = False


class MainWindow(QMainWindow):
    """Main application window for RIPIS."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components (will be set up in initialize())
        self.ai_engine = None
        self.interview_state = None
        self.speech_recognition = None
        self.tts_engine = None
        self.interview_worker = None
        
        # UI Components
        self.code_editor = None
        self.status_panel = None
        
        # State
        self.is_interview_active = False
        self.is_paused = False
        self.is_mic_muted = False  # Mic mute state for controlling speech input
        
        # Set up UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(1200, 800)
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Code editor (left side, larger)
        try:
            from ui.code_editor import get_code_editor
            self.code_editor = get_code_editor()
        except Exception as e:
            print(f"Error loading code editor: {e}")
            from ui.code_editor import SimpleCodeEditor
            self.code_editor = SimpleCodeEditor()
        
        splitter.addWidget(self.code_editor)
        
        # Status panel (right side)
        from ui.status_panel import StatusPanel
        self.status_panel = StatusPanel()
        splitter.addWidget(self.status_panel)
        
        # Set splitter sizes (70% editor, 30% status)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        
        # Connect signals
        self._connect_signals()
    
    def _create_header(self) -> QWidget:
        """Create the header widget."""
        header = QWidget()
        header.setMaximumHeight(50)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # App title
        title = QLabel("🎙️ RIPIS - Real-Time Interview Practice")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Ethical notice
        notice = QLabel("📋 Practice Mode Only | AI Assistance Disclosed")
        notice.setStyleSheet("color: #858585;")
        layout.addWidget(notice)
        
        return header
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Status panel buttons
        self.status_panel.start_clicked.connect(self.start_interview)
        self.status_panel.pause_clicked.connect(self.toggle_pause)
        self.status_panel.end_clicked.connect(self.end_interview)
        self.status_panel.hint_clicked.connect(self.request_hint)
        self.status_panel.mic_toggled.connect(self._on_mic_toggled)
        
        # Code editor changes
        self.code_editor.text_changed.connect(self._on_code_changed)
    
    def initialize(self) -> bool:
        """Initialize all backend components."""
        try:
            # Initialize AI Engine
            from core.ai_engine import AIEngine
            self.ai_engine = AIEngine()
            
            if not self.ai_engine.test_connection():
                QMessageBox.warning(
                    self, 
                    "Ollama Not Running",
                    "Could not connect to Ollama. Please ensure:\n\n"
                    "1. Ollama is installed\n"
                    "2. Ollama is running (ollama serve)\n"
                    "3. DeepSeek model is pulled (ollama pull deepseek-r1:7b)\n\n"
                    "The app will continue but AI features won't work."
                )
            
            # Initialize Interview State Machine
            from core.interview_state import InterviewStateMachine
            self.interview_state = InterviewStateMachine(self.ai_engine)
            self.interview_state.on_editor_write = self._on_ai_editor_write
            
            # Initialize TTS
            from audio.text_to_speech import get_tts_engine
            self.tts_engine = get_tts_engine(use_piper=False)  # Use pyttsx3 for now
            
            # Initialize Speech Recognition
            from audio.speech_recognition import get_speech_recognizer
            self.speech_recognition = get_speech_recognizer(use_mock=False)
            
            # Set up speech recognition callbacks
            self.speech_recognition.on_final_result = self._on_speech_result
            self.speech_recognition.on_partial_result = self._on_partial_speech
            
            # Try to initialize (may fail if no model)
            if not self.speech_recognition.initialize():
                self.status_panel.set_status("⚠ Speech recognition unavailable - type responses")
            
            # Create worker thread and START it (runs continuously)
            self.interview_worker = InterviewWorker(self.interview_state, self.tts_engine)
            self.interview_worker.response_ready.connect(self._on_ai_response)
            self.interview_worker.speaking_started.connect(lambda: self.status_panel.set_speaking(True))
            self.interview_worker.speaking_finished.connect(self._on_speaking_finished)
            self.interview_worker.error_occurred.connect(self._on_error)
            self.interview_worker.start()  # Start the worker thread loop
            
            self.status_panel.set_status("Ready - Click 'Start Interview' to begin")
            print("[Main] Initialization complete")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize: {e}")
            return False
    
    def start_interview(self):
        """Start a new interview session."""
        if self.interview_worker.is_busy:
            print("[Main] Worker is busy, ignoring start")
            return
        
        print("[Main] Starting interview...")
        self.is_interview_active = True
        self.status_panel.set_interview_started(True)
        self.status_panel.clear_transcript()
        self.code_editor.clear()
        
        self.status_panel.set_status("🎤 Starting interview...")
        
        # Queue the start action
        self.interview_worker.queue_action("start")
        
        # Start listening for speech
        if self.speech_recognition:
            self.speech_recognition.start_listening()
    
    def toggle_pause(self):
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.status_panel.set_status("⏸ Paused")
            if self.speech_recognition:
                self.speech_recognition.stop_listening()
        else:
            self.status_panel.set_status("🎤 Listening...")
            if self.speech_recognition:
                self.speech_recognition.start_listening()
    
    def end_interview(self):
        """End the current interview session."""
        if not self.is_interview_active:
            return
        
        reply = QMessageBox.question(
            self,
            "End Interview",
            "Are you sure you want to end the interview?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.is_interview_active = False
            
            if self.speech_recognition:
                self.speech_recognition.stop_listening()
            
            # Queue end action
            self.interview_worker.queue_action("end")
            
            self.status_panel.set_interview_started(False)
            self.status_panel.set_idle()
    
    def request_hint(self):
        """Request a hint from the AI."""
        if not self.is_interview_active or self.interview_worker.is_busy:
            return
        
        self.status_panel.set_status("💡 Getting hint...")
        self.interview_worker.queue_action("hint", code=self.code_editor.get_text())
    
    def _on_code_changed(self, code: str):
        """Handle code changes in the editor."""
        # Could be used for real-time analysis
        pass
    
    def _on_speech_result(self, text: str):
        """Handle final speech recognition result."""
        print(f"[Main] Speech result: {text}")
        
        if not self.is_interview_active or self.is_paused:
            print("[Main] Ignoring - not active or paused")
            return
        
        # Check if mic is muted - ignore speech input when muted
        if self.is_mic_muted:
            print("[Main] Ignoring - mic muted")
            return
        
        if self.interview_worker.is_busy:
            print("[Main] Ignoring - worker busy")
            return
        
        # Add to transcript
        self.status_panel.add_transcript_entry("You", text)
        self.status_panel.set_status("🤔 Thinking...")
        
        # Process the input
        self.interview_worker.queue_action(
            "process", 
            user_input=text, 
            code=self.code_editor.get_text()
        )
    
    def _on_partial_speech(self, text: str):
        """Handle partial speech recognition (real-time)."""
        if self.is_interview_active and not self.is_paused and not self.is_mic_muted:
            self.status_panel.set_status(f"🎤 Hearing: {text[:50]}...")
    
    def _on_ai_response(self, response: str):
        """Handle AI response."""
        self.status_panel.add_transcript_entry("AI", response)
    
    def _on_ai_editor_write(self, text: str):
        """Handle AI writing to the editor."""
        self.code_editor.set_text(text)
    
    def _on_speaking_finished(self):
        """Handle TTS finished speaking."""
        self.status_panel.set_speaking(False)
        self.status_panel.set_status("🎤 Listening...")
    
    def _on_error(self, error: str):
        """Handle errors."""
        self.status_panel.set_status(f"❌ Error: {error}")
        print(f"Error: {error}")
    
    def _on_mic_toggled(self, is_on: bool):
        """Handle mic toggle - mute/unmute speech input."""
        self.is_mic_muted = not is_on
        if is_on:
            self.status_panel.set_status("🎤 Mic ON - Listening...")
        else:
            self.status_panel.set_status("🔇 Mic OFF - Speech input muted")
    
    def closeEvent(self, event):
        """Handle window close."""
        print("[Main] Closing application...")
        if self.interview_worker:
            self.interview_worker.stop()
            self.interview_worker.wait(2000)  # Wait up to 2 seconds
        if self.speech_recognition:
            self.speech_recognition.stop_listening()
        if self.tts_engine:
            self.tts_engine.stop()
        event.accept()


def create_app():
    """Create and return the application."""
    app = QApplication(sys.argv)
    
    # Set application-wide style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    # Initialize after showing (for better UX)
    QTimer.singleShot(100, window.initialize)
    
    return app, window
