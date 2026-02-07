"""
Status Panel Widget for RIPIS
Shows interview status, transcript, and controls
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QProgressBar
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal


class StatusPanel(QWidget):
    """Panel showing interview status, controls, and transcript."""
    
    # Signals for button clicks
    start_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    end_clicked = pyqtSignal()
    hint_clicked = pyqtSignal()
    mic_toggled = pyqtSignal(bool)  # True = mic on, False = mic off
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the status panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # AI Assistance Indicator
        self.ai_indicator = self._create_ai_indicator()
        layout.addWidget(self.ai_indicator)
        
        # Current Status
        self.status_label = QLabel("Status: Ready to start")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.status_label)
        
        # Topic/State info
        self.topic_label = QLabel("Topic: Not selected")
        self.topic_label.setFont(QFont("Segoe UI", 10))
        self.topic_label.setStyleSheet("color: #858585;")
        layout.addWidget(self.topic_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start Interview")
        self.start_btn.setStyleSheet(self._button_style("#4CAF50"))
        self.start_btn.clicked.connect(self.start_clicked.emit)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet(self._button_style("#FF9800"))
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.end_btn = QPushButton("⏹ End Session")
        self.end_btn.setStyleSheet(self._button_style("#f44336"))
        self.end_btn.clicked.connect(self.end_clicked.emit)
        self.end_btn.setEnabled(False)
        button_layout.addWidget(self.end_btn)
        
        layout.addLayout(button_layout)
        
        # Hint button
        self.hint_btn = QPushButton("💡 Request Hint")
        self.hint_btn.setStyleSheet(self._button_style("#2196F3"))
        self.hint_btn.clicked.connect(self.hint_clicked.emit)
        self.hint_btn.setEnabled(False)
        layout.addWidget(self.hint_btn)
        
        # Mic toggle button
        self.mic_btn = QPushButton("🎤 Mic ON")
        self.mic_btn.setStyleSheet(self._toggle_button_style(True))
        self.mic_btn.clicked.connect(self._toggle_mic)
        self.mic_btn.setEnabled(False)
        self.mic_on = True
        layout.addWidget(self.mic_btn)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Transcript area
        transcript_label = QLabel("📝 Conversation Transcript:")
        transcript_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        transcript_label.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(transcript_label)
        
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setFont(QFont("Consolas", 9))
        self.transcript.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        self.transcript.setMaximumHeight(150)
        layout.addWidget(self.transcript)
        
        # Speaking indicator
        self.speaking_indicator = QLabel("🔇 Idle")
        self.speaking_indicator.setStyleSheet("color: #858585;")
        layout.addWidget(self.speaking_indicator)
        
        # Add stretch to push everything up
        layout.addStretch()
    
    def _create_ai_indicator(self) -> QFrame:
        """Create the AI assistance indicator."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #264f78;
                border: 2px solid #569cd6;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        
        icon = QLabel("⚡")
        icon.setFont(QFont("Segoe UI", 14))
        layout.addWidget(icon)
        
        text = QLabel("AI ASSISTANCE ACTIVE")
        text.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        text.setStyleSheet("color: #ffffff;")
        layout.addWidget(text)
        
        layout.addStretch()
        
        info = QLabel("Practice Mode")
        info.setStyleSheet("color: #a0c4ff;")
        layout.addWidget(info)
        
        return frame
    
    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #3c3c3c;")
        return line
    
    def _button_style(self, color: str) -> str:
        """Generate button stylesheet."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}cc;
            }}
            QPushButton:disabled {{
                background-color: #3c3c3c;
                color: #858585;
            }}
        """
    
    def _toggle_button_style(self, is_on: bool) -> str:
        """Generate toggle button stylesheet."""
        if is_on:
            return self._button_style("#4CAF50")  # Green when mic is on
        else:
            return self._button_style("#f44336")  # Red when mic is off
    
    def _toggle_mic(self):
        """Toggle the microphone on/off."""
        self.mic_on = not self.mic_on
        if self.mic_on:
            self.mic_btn.setText("🎤 Mic ON")
            self.mic_btn.setStyleSheet(self._toggle_button_style(True))
        else:
            self.mic_btn.setText("🔇 Mic OFF")
            self.mic_btn.setStyleSheet(self._toggle_button_style(False))
        self.mic_toggled.emit(self.mic_on)
    
    def set_status(self, status: str):
        """Update the status text."""
        self.status_label.setText(f"Status: {status}")
    
    def set_topic(self, topic: str):
        """Update the topic text."""
        self.topic_label.setText(f"Topic: {topic}")
    
    def set_interview_started(self, started: bool):
        """Update button states based on interview status."""
        self.start_btn.setEnabled(not started)
        self.pause_btn.setEnabled(started)
        self.end_btn.setEnabled(started)
        self.hint_btn.setEnabled(started)
        self.mic_btn.setEnabled(started)
        if started:
            self.mic_on = True
            self.mic_btn.setText("🎤 Mic ON")
            self.mic_btn.setStyleSheet(self._toggle_button_style(True))
    
    def add_transcript_entry(self, speaker: str, text: str):
        """Add an entry to the transcript."""
        color = "#4CAF50" if speaker == "AI" else "#2196F3"
        self.transcript.append(f'<span style="color: {color}; font-weight: bold;">{speaker}:</span> {text}')
    
    def clear_transcript(self):
        """Clear the transcript."""
        self.transcript.clear()
    
    def set_speaking(self, is_speaking: bool):
        """Update the speaking indicator."""
        if is_speaking:
            self.speaking_indicator.setText("🔊 AI Speaking...")
            self.speaking_indicator.setStyleSheet("color: #4CAF50;")
        else:
            self.speaking_indicator.setText("🎤 Listening...")
            self.speaking_indicator.setStyleSheet("color: #2196F3;")
    
    def set_idle(self):
        """Set to idle state."""
        self.speaking_indicator.setText("🔇 Idle")
        self.speaking_indicator.setStyleSheet("color: #858585;")
