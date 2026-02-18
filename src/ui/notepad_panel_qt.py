"""
Notepad Panel - Quick note-taking for project management
Simple text editor for recording notes, reminders, and project info
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QListWidget, QListWidgetItem, QMessageBox,
        QInputDialog, QSplitter, QFrame, QFileDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QTextCharFormat, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object

logger = logging.getLogger(__name__)


class NotepadPanelQt(QWidget):
    """
    Notepad Panel - Simple note-taking interface
    
    Features:
    - Create, edit, save, delete notes
    - Multiple notes with list view
    - Auto-save on changes
    - Export to text file
    - Timestamp on creation
    """
    
    note_changed = pyqtSignal(str)  # Emits note title when changed
    
    def __init__(self, config=None, tooltip_manager=None, parent=None):
        super().__init__(parent)
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for NotepadPanelQt")
        
        self.config = config
        self.tooltip_manager = tooltip_manager
        self.current_note_id: Optional[str] = None
        self.notes: dict = {}  # {note_id: {title, content, created, modified}}
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.setInterval(2000)  # Auto-save every 2 seconds
        
        # Data directory
        self.data_dir = Path.home() / '.ps2_texture_sorter' / 'notes'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / 'notes.json'
        
        self.setup_ui()
        self.load_notes()
    
    def _set_tooltip(self, widget, tooltip_id: str):
        """Helper to set tooltip from manager"""
        if self.tooltip_manager:
            self.tooltip_manager.set_tooltip(widget, tooltip_id)
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("📝 Notepad")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # === TOP CONTROLS ===
        controls_layout = QHBoxLayout()
        
        # New note button
        self.new_btn = QPushButton("➕ New Note")
        self.new_btn.clicked.connect(self.create_new_note)
        self._set_tooltip(self.new_btn, 'notepad_new')
        controls_layout.addWidget(self.new_btn)
        
        # Save button
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_current_note)
        self.save_btn.setEnabled(False)
        self._set_tooltip(self.save_btn, 'notepad_save')
        controls_layout.addWidget(self.save_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_current_note)
        self.delete_btn.setEnabled(False)
        self._set_tooltip(self.delete_btn, 'notepad_delete')
        controls_layout.addWidget(self.delete_btn)
        
        # Export button
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_note)
        self.export_btn.setEnabled(False)
        self._set_tooltip(self.export_btn, 'export_note_button')
        controls_layout.addWidget(self.export_btn)
        
        controls_layout.addStretch()
        
        # Word count label
        self.word_count_label = QLabel("0 words")
        self.word_count_label.setStyleSheet("color: #666; font-style: italic;")
        controls_layout.addWidget(self.word_count_label)
        
        layout.addLayout(controls_layout)
        
        # === SPLITTER FOR NOTE LIST AND EDITOR ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === NOTE LIST (LEFT) ===
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("📋 Your Notes")
        list_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 5px;")
        list_layout.addWidget(list_label)
        
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.on_note_selected)
        list_layout.addWidget(self.notes_list)
        
        splitter.addWidget(list_container)
        
        # === NOTE EDITOR (RIGHT) ===
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Note title
        self.note_title_label = QLabel("No note selected")
        self.note_title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        editor_layout.addWidget(self.note_title_label)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Write your notes here...")
        self.text_editor.textChanged.connect(self.on_text_changed)
        self.text_editor.setEnabled(False)
        
        # Set font
        font = QFont("Consolas", 11)
        if not font.exactMatch():
            font = QFont("Courier New", 11)
        self.text_editor.setFont(font)
        
        editor_layout.addWidget(self.text_editor)
        
        # Metadata label
        self.metadata_label = QLabel("")
        self.metadata_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic; padding: 5px;")
        editor_layout.addWidget(self.metadata_label)
        
        splitter.addWidget(editor_container)
        splitter.setStretchFactor(0, 1)  # Note list
        splitter.setStretchFactor(1, 3)  # Editor gets more space
        
        layout.addWidget(splitter)
        
        # === STATUS BAR ===
        self.status_label = QLabel("Ready - Create a new note to get started")
        self.status_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        layout.addWidget(self.status_label)
    
    def create_new_note(self):
        """Create a new note"""
        title, ok = QInputDialog.getText(
            self,
            "New Note",
            "Enter note title:"
        )
        
        if not ok or not title.strip():
            return
        
        # Generate note ID
        note_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create note
        self.notes[note_id] = {
            'title': title.strip(),
            'content': '',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }
        
        # Add to list
        self.refresh_notes_list()
        
        # Select the new note
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == note_id:
                self.notes_list.setCurrentItem(item)
                self.on_note_selected(item)
                break
        
        self.save_notes_to_disk()
        self.status_label.setText(f"Created note: {title}")
    
    def delete_current_note(self):
        """Delete the current note"""
        if not self.current_note_id:
            return
        
        note = self.notes.get(self.current_note_id)
        if not note:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Note",
            f"Are you sure you want to delete '{note['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            title = note['title']
            del self.notes[self.current_note_id]
            self.current_note_id = None
            self.text_editor.clear()
            self.text_editor.setEnabled(False)
            self.note_title_label.setText("No note selected")
            self.metadata_label.setText("")
            self.save_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.refresh_notes_list()
            self.save_notes_to_disk()
            self.status_label.setText(f"Deleted note: {title}")
    
    def save_current_note(self):
        """Save the current note"""
        if not self.current_note_id:
            return
        
        note = self.notes.get(self.current_note_id)
        if note:
            note['content'] = self.text_editor.toPlainText()
            note['modified'] = datetime.now().isoformat()
            self.save_notes_to_disk()
            self.update_metadata()
            self.status_label.setText("Note saved")
            self.note_changed.emit(note['title'])
    
    def auto_save(self):
        """Auto-save current note"""
        if self.current_note_id and self.text_editor.isEnabled():
            self.save_current_note()
    
    def on_note_selected(self, item: QListWidgetItem):
        """Handle note selection"""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self.notes.get(note_id)
        
        if not note:
            return
        
        # Save previous note if any
        if self.current_note_id and self.current_note_id != note_id:
            self.save_current_note()
        
        self.current_note_id = note_id
        self.text_editor.setEnabled(True)
        self.text_editor.setPlainText(note['content'])
        self.note_title_label.setText(f"📝 {note['title']}")
        self.save_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        self.update_metadata()
        self.update_word_count()
        self.status_label.setText(f"Editing: {note['title']}")
    
    def on_text_changed(self):
        """Handle text changes"""
        self.update_word_count()
        # Restart auto-save timer
        self.auto_save_timer.stop()
        self.auto_save_timer.start()
    
    def update_word_count(self):
        """Update word count label"""
        text = self.text_editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"{words} words, {chars} characters")
    
    def update_metadata(self):
        """Update metadata label"""
        if not self.current_note_id:
            self.metadata_label.setText("")
            return
        
        note = self.notes.get(self.current_note_id)
        if note:
            created = datetime.fromisoformat(note['created']).strftime("%Y-%m-%d %H:%M")
            modified = datetime.fromisoformat(note['modified']).strftime("%Y-%m-%d %H:%M")
            self.metadata_label.setText(f"Created: {created} | Modified: {modified}")
    
    def refresh_notes_list(self):
        """Refresh the notes list"""
        self.notes_list.clear()
        
        # Sort notes by modified time (newest first)
        sorted_notes = sorted(
            self.notes.items(),
            key=lambda x: x[1]['modified'],
            reverse=True
        )
        
        for note_id, note in sorted_notes:
            item = QListWidgetItem()
            item.setText(note['title'])
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            
            # Add icon
            item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
            
            self.notes_list.addItem(item)
    
    def export_note(self):
        """Export current note to text file"""
        if not self.current_note_id:
            return
        
        note = self.notes.get(self.current_note_id)
        if not note:
            return
        
        # Get file name
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Note",
            f"{note['title']}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {note['title']}\n")
                    f.write(f"Created: {note['created']}\n")
                    f.write(f"Modified: {note['modified']}\n")
                    f.write("\n" + "=" * 50 + "\n\n")
                    f.write(note['content'])
                
                self.status_label.setText(f"Exported to: {Path(filename).name}")
                QMessageBox.information(self, "Success", f"Note exported to:\n{filename}")
                
            except Exception as e:
                logger.error(f"Error exporting note: {e}", exc_info=True)
                QMessageBox.warning(self, "Error", f"Failed to export note:\n{e}")
    
    def load_notes(self):
        """Load notes from disk"""
        try:
            if self.notes_file.exists():
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
                logger.info(f"Loaded {len(self.notes)} notes")
            else:
                self.notes = {}
            
            self.refresh_notes_list()
            
        except Exception as e:
            logger.error(f"Error loading notes: {e}", exc_info=True)
            self.notes = {}
    
    def save_notes_to_disk(self):
        """Save notes to disk"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.notes)} notes")
            
        except Exception as e:
            logger.error(f"Error saving notes: {e}", exc_info=True)
    
    def closeEvent(self, event):
        """Handle window close - save current note"""
        if self.current_note_id:
            self.save_current_note()
        event.accept()
