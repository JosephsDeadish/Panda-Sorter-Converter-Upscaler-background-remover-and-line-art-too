"""
Notepad Panel - Quick note-taking for project management
Simple text editor for recording notes, reminders, and project info
Author: Dead On The Inside / JosephsDeadish
"""


from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QListWidget, QListWidgetItem, QMessageBox,
        QInputDialog, QSplitter, QFrame, QFileDialog, QLineEdit
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QKeySequence, QShortcut, QTextDocument
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QWidget:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class _SignalStub:  # noqa: E301
        """Stub signal — active only when PyQt6 is absent."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301

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
        self.auto_save_timer.setSingleShot(True)   # debounce: fire once after idle
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.setInterval(2000)  # Auto-save 2 seconds after last change
        
        # Data directory — use the app's canonical data dir so notes are stored
        # alongside other user data (app_data/ in frozen EXE, ~/.ps2_texture_sorter/ in dev).
        try:
            from config import get_data_dir as _get_data_dir
            self.data_dir = _get_data_dir() / 'notes'
        except Exception:
            self.data_dir = Path.home() / '.ps2_texture_sorter' / 'notes'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / 'notes.json'
        
        self.setup_ui()
        self.load_notes()
    
    def _set_tooltip(self, widget, widget_id_or_text: str):
        """Set tooltip via manager (cycling) when available, else plain text."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
            if ' ' not in widget_id_or_text:
                try:
                    tip = self.tooltip_manager.get_tooltip(widget_id_or_text)
                    if tip:
                        widget.setToolTip(tip)
                        self.tooltip_manager.register(widget, widget_id_or_text)
                        return
                except Exception:
                    pass
        widget.setToolTip(str(widget_id_or_text))
    
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

        # Import button
        self.import_btn = QPushButton("📥 Import")
        self.import_btn.clicked.connect(self.import_note_from_file)
        self._set_tooltip(self.import_btn, "Import a text or Markdown file as a new note")
        controls_layout.addWidget(self.import_btn)

        controls_layout.addStretch()

        # Undo / Redo buttons (QTextEdit already supports Ctrl+Z/Ctrl+Y natively;
        # these buttons make the feature visible and discoverable in the toolbar).
        self.undo_btn = QPushButton("↩ Undo")
        self.undo_btn.setEnabled(False)
        self._set_tooltip(self.undo_btn, 'undo_button')
        self.undo_btn.setAccessibleName("Undo")
        controls_layout.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("↪ Redo")
        self.redo_btn.setEnabled(False)
        self._set_tooltip(self.redo_btn, 'redo_button')
        self.redo_btn.setAccessibleName("Redo")
        controls_layout.addWidget(self.redo_btn)
        
        # Word count label
        self.word_count_label = QLabel("0 words")
        self.word_count_label.setStyleSheet("color: #666; font-style: italic;")
        controls_layout.addWidget(self.word_count_label)

        # Markdown preview toggle
        self.preview_btn = QPushButton("👁 Preview")
        self.preview_btn.setCheckable(True)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setToolTip("Toggle Markdown preview (read-only rendered view)")
        self.preview_btn.toggled.connect(self._toggle_markdown_preview)
        controls_layout.addWidget(self.preview_btn)
        
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
        # Wire undo/redo availability to toolbar button states
        self.text_editor.undoAvailable.connect(self.undo_btn.setEnabled)
        self.text_editor.redoAvailable.connect(self.redo_btn.setEnabled)
        self.undo_btn.clicked.connect(self.text_editor.undo)
        self.redo_btn.clicked.connect(self.text_editor.redo)
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

        # === FIND BAR (hidden until Ctrl+F) ===
        self._find_bar = QWidget()
        find_bar_layout = QHBoxLayout(self._find_bar)
        find_bar_layout.setContentsMargins(0, 2, 0, 2)
        find_bar_layout.setSpacing(4)
        find_bar_layout.addWidget(QLabel("🔍 Find:"))
        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("Search in note…")
        self._find_input.textChanged.connect(self._find_in_note)
        self._find_input.returnPressed.connect(self._find_next)
        find_bar_layout.addWidget(self._find_input)
        _find_next_btn = QPushButton("▼")
        _find_next_btn.setFixedWidth(28)
        _find_next_btn.setToolTip("Find next (Enter)")
        _find_next_btn.clicked.connect(self._find_next)
        find_bar_layout.addWidget(_find_next_btn)
        _find_prev_btn = QPushButton("▲")
        _find_prev_btn.setFixedWidth(28)
        _find_prev_btn.setToolTip("Find previous")
        _find_prev_btn.clicked.connect(self._find_prev)
        find_bar_layout.addWidget(_find_prev_btn)
        _find_close_btn = QPushButton("✕")
        _find_close_btn.setFixedWidth(24)
        _find_close_btn.setToolTip("Close find bar (Escape)")
        _find_close_btn.clicked.connect(self._hide_find_bar)
        find_bar_layout.addWidget(_find_close_btn)
        self._find_match_label = QLabel("")
        self._find_match_label.setStyleSheet("color: #888; font-size: 10px;")
        find_bar_layout.addWidget(self._find_match_label)
        self._find_bar.hide()
        layout.addWidget(self._find_bar)

        # Ctrl+F shortcut to open find bar
        _find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        _find_shortcut.activated.connect(self._show_find_bar)
        _esc_shortcut = QShortcut(QKeySequence("Escape"), self._find_bar)
        _esc_shortcut.activated.connect(self._hide_find_bar)
        
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
        if hasattr(self, 'preview_btn'):
            self.preview_btn.setEnabled(True)
            self.preview_btn.setChecked(False)  # reset to edit mode on new note
        
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
        """Export current note to text or Markdown file."""
        if not self.current_note_id:
            return
        
        note = self.notes.get(self.current_note_id)
        if not note:
            return
        
        # Get file name
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Note",
            f"{note['title']}.txt",
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )
        
        if filename:
            try:
                # Ensure correct extension matches filter
                if 'Markdown' in selected_filter and not filename.lower().endswith('.md'):
                    filename += '.md'
                elif 'Text' in selected_filter and not filename.lower().endswith('.txt'):
                    filename += '.txt'

                with open(filename, 'w', encoding='utf-8') as f:
                    if filename.lower().endswith('.md'):
                        f.write(f"# {note['title']}\n\n")
                        f.write(f"*Created: {note['created']}*  \n")
                        f.write(f"*Modified: {note['modified']}*\n\n")
                        f.write("---\n\n")
                        f.write(note['content'])
                    else:
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

    def _toggle_markdown_preview(self, checked: bool) -> None:
        """Switch the editor between plain-text editing and rendered Markdown preview."""
        if checked:
            # Render current content as Markdown (Qt 5.14+ / PyQt6)
            md_text = self.text_editor.toPlainText()
            try:
                self.text_editor.setMarkdown(md_text)
            except AttributeError:
                # Older Qt — fallback to setHtml with minimal formatting
                escaped = md_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                self.text_editor.setHtml(f"<pre>{escaped}</pre>")
            self.text_editor.setReadOnly(True)
            self.preview_btn.setText("✏️ Edit")
        else:
            # Restore plain text for editing
            if self.current_note_id and self.current_note_id in self.notes:
                content = self.notes[self.current_note_id].get('content', '')
            else:
                content = ""
            self.text_editor.setReadOnly(False)
            self.text_editor.setPlainText(content)
            self.preview_btn.setText("👁 Preview")

    def import_note_from_file(self):
        """Import a .txt or .md file as a new note."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Note",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
        )
        if not filename:
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            title = Path(filename).stem
            note_id = datetime.now().strftime("%Y%m%d_%H%M%S_imported")
            self.notes[note_id] = {
                'title': title,
                'content': content,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
            }
            self.refresh_notes_list()
            self.save_notes_to_disk()
            # Select the newly imported note
            self.current_note_id = note_id
            self.title_edit.setText(title)
            self.text_edit.setPlainText(content)
            self.status_label.setText(f"Imported: {Path(filename).name}")
        except Exception as e:
            logger.error(f"Error importing note: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to import file:\n{e}")
    
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

    # ── Find bar ────────────────────────────────────────────────────────────

    def _show_find_bar(self) -> None:
        """Show the find bar and focus the search input."""
        self._find_bar.show()
        self._find_input.setFocus()
        self._find_input.selectAll()

    def _hide_find_bar(self) -> None:
        """Hide the find bar and clear highlights."""
        self._find_bar.hide()
        self._find_input.clear()
        # Remove highlight formatting
        cursor = self.text_editor.textCursor()
        cursor.clearSelection()
        self.text_editor.setExtraSelections([])
        self.text_editor.setFocus()

    def _find_in_note(self, query: str) -> None:
        """Highlight all occurrences of *query* in the current note."""
        extra: list = []
        if query:
            fmt = QTextCharFormat()
            fmt.setBackground(QColor('#f0c040'))
            cursor = self.text_editor.document().find(query)
            count = 0
            while not cursor.isNull():
                sel = QTextEdit.ExtraSelection()
                sel.format = fmt
                sel.cursor = cursor
                extra.append(sel)
                count += 1
                cursor = self.text_editor.document().find(query, cursor)
            self._find_match_label.setText(f"{count} match{'es' if count != 1 else ''}")
        else:
            self._find_match_label.setText("")
        self.text_editor.setExtraSelections(extra)

    def _find_next(self) -> None:
        """Move to the next occurrence of the search term."""
        query = self._find_input.text()
        if query:
            found = self.text_editor.find(query)
            if not found:
                # Wrap around to start
                cursor = self.text_editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                self.text_editor.setTextCursor(cursor)
                self.text_editor.find(query)

    def _find_prev(self) -> None:
        """Move to the previous occurrence of the search term."""
        query = self._find_input.text()
        if query:
            found = self.text_editor.find(query, QTextDocument.FindFlag.FindBackward)
            if not found:
                # Wrap around to end
                cursor = self.text_editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.text_editor.setTextCursor(cursor)
                self.text_editor.find(query, QTextDocument.FindFlag.FindBackward)
