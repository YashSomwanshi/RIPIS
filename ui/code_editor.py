"""
Code Editor Widget for RIPIS
Provides syntax-highlighted code editing using QScintilla
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import pyqtSignal
from PyQt6.Qsci import QsciScintilla, QsciLexerPython, QsciLexerJava, QsciLexerCPP, QsciLexerJavaScript
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EDITOR_FONT_SIZE


class CodeEditor(QWidget):
    """A syntax-highlighted code editor widget."""
    
    # Signals
    text_changed = pyqtSignal(str)  # Emitted when code changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the Scintilla editor
        self.editor = QsciScintilla()
        layout.addWidget(self.editor)
        
        # Configure editor appearance
        self._configure_appearance()
        
        # Configure editing features
        self._configure_editing()
        
        # Set default lexer (Python)
        self.set_language("python")
        
        # Connect signals
        self.editor.textChanged.connect(self._on_text_changed)
    
    def _configure_appearance(self):
        """Configure the visual appearance of the editor."""
        # Font
        font = QFont("Consolas", EDITOR_FONT_SIZE)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(font)
        
        # Margins
        self.editor.setMarginsFont(font)
        self.editor.setMarginWidth(0, "0000")  # Line numbers
        self.editor.setMarginLineNumbers(0, True)
        
        # Colors - Dark theme
        self.editor.setMarginsBackgroundColor(QColor("#2b2b2b"))
        self.editor.setMarginsForegroundColor(QColor("#858585"))
        self.editor.setPaper(QColor("#1e1e1e"))
        self.editor.setColor(QColor("#d4d4d4"))
        
        # Caret (cursor)
        self.editor.setCaretForegroundColor(QColor("#ffffff"))
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor("#2a2a2a"))
        
        # Selection
        self.editor.setSelectionBackgroundColor(QColor("#264f78"))
        self.editor.setSelectionForegroundColor(QColor("#ffffff"))
        
        # Matching brackets
        self.editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.editor.setMatchedBraceBackgroundColor(QColor("#3a3d41"))
        self.editor.setMatchedBraceForegroundColor(QColor("#ffffff"))
    
    def _configure_editing(self):
        """Configure editing behavior."""
        # Indentation
        self.editor.setIndentationsUseTabs(False)
        self.editor.setTabWidth(4)
        self.editor.setAutoIndent(True)
        self.editor.setIndentationGuides(True)
        
        # Auto-completion (basic)
        self.editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.editor.setAutoCompletionThreshold(2)
        self.editor.setAutoCompletionCaseSensitivity(False)
        
        # Code folding
        self.editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.editor.setFoldMarginColors(QColor("#2b2b2b"), QColor("#2b2b2b"))
        
        # Edge line (80 chars)
        self.editor.setEdgeMode(QsciScintilla.EdgeMode.EdgeLine)
        self.editor.setEdgeColumn(80)
        self.editor.setEdgeColor(QColor("#3a3a3a"))
        
        # Wrapping
        self.editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)
    
    def set_language(self, language: str):
        """Set the syntax highlighting language."""
        lexer = None
        
        if language.lower() == "python":
            lexer = QsciLexerPython()
        elif language.lower() == "java":
            lexer = QsciLexerJava()
        elif language.lower() in ["cpp", "c++"]:
            lexer = QsciLexerCPP()
        elif language.lower() == "javascript":
            lexer = QsciLexerJavaScript()
        else:
            lexer = QsciLexerPython()  # Default
        
        if lexer:
            # Configure lexer colors (dark theme)
            font = QFont("Consolas", EDITOR_FONT_SIZE)
            lexer.setFont(font)
            lexer.setPaper(QColor("#1e1e1e"))
            lexer.setColor(QColor("#d4d4d4"))
            
            # Python-specific colors
            if isinstance(lexer, QsciLexerPython):
                lexer.setColor(QColor("#608b4e"), QsciLexerPython.Comment)
                lexer.setColor(QColor("#ce9178"), QsciLexerPython.DoubleQuotedString)
                lexer.setColor(QColor("#ce9178"), QsciLexerPython.SingleQuotedString)
                lexer.setColor(QColor("#569cd6"), QsciLexerPython.Keyword)
                lexer.setColor(QColor("#b5cea8"), QsciLexerPython.Number)
                lexer.setColor(QColor("#dcdcaa"), QsciLexerPython.FunctionMethodName)
                lexer.setColor(QColor("#4ec9b0"), QsciLexerPython.ClassName)
                lexer.setColor(QColor("#c586c0"), QsciLexerPython.Decorator)
            
            self.editor.setLexer(lexer)
    
    def get_text(self) -> str:
        """Get the current editor text."""
        return self.editor.text()
    
    def set_text(self, text: str):
        """Set the editor text."""
        self.editor.setText(text)
    
    def append_text(self, text: str):
        """Append text to the editor."""
        self.editor.append(text)
    
    def insert_text(self, text: str):
        """Insert text at current cursor position."""
        self.editor.insert(text)
    
    def clear(self):
        """Clear the editor."""
        self.editor.clear()
    
    def set_read_only(self, read_only: bool):
        """Set the editor to read-only mode."""
        self.editor.setReadOnly(read_only)
    
    def _on_text_changed(self):
        """Handle text changes."""
        self.text_changed.emit(self.get_text())
    
    def goto_end(self):
        """Move cursor to end of document."""
        line_count = self.editor.lines()
        self.editor.setCursorPosition(line_count - 1, len(self.editor.text(line_count - 1)))
    
    def set_ai_section(self, text: str):
        """Add an AI-written section (question) at the start."""
        current = self.get_text()
        self.set_text(text + current)


class SimpleCodeEditor(QWidget):
    """Fallback simple code editor without QScintilla."""
    
    text_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QTextEdit
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", EDITOR_FONT_SIZE))
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        
        layout.addWidget(self.editor)
        
        self.editor.textChanged.connect(lambda: self.text_changed.emit(self.get_text()))
    
    def get_text(self) -> str:
        return self.editor.toPlainText()
    
    def set_text(self, text: str):
        self.editor.setPlainText(text)
    
    def append_text(self, text: str):
        self.editor.append(text)
    
    def insert_text(self, text: str):
        cursor = self.editor.textCursor()
        cursor.insertText(text)
    
    def clear(self):
        self.editor.clear()
    
    def set_read_only(self, read_only: bool):
        self.editor.setReadOnly(read_only)
    
    def set_language(self, language: str):
        pass  # No syntax highlighting in simple editor
    
    def goto_end(self):
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)
    
    def set_ai_section(self, text: str):
        current = self.get_text()
        self.set_text(text + current)


def get_code_editor(parent=None):
    """Factory function to get the best available code editor."""
    try:
        return CodeEditor(parent)
    except ImportError:
        print("QScintilla not available, using simple editor")
        return SimpleCodeEditor(parent)
