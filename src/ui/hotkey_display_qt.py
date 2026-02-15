"""
PyQt6 Hotkey Display
Replaces canvas-based hotkey settings display
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QTableWidget, QTableWidgetItem, QHeaderView,
                                 QLabel, QKeySequenceEdit, QMessageBox)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QKeySequence
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class HotkeyDisplayWidget(QWidget):
    """Hotkey display and configuration"""
    
    hotkey_changed = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkeys = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Keyboard Shortcuts")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Category", "Action", "Current Key", "Default"])
        
        # Make table fill width
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def load_hotkeys(self, hotkeys_dict):
        """Load hotkey configuration"""
        self.hotkeys = hotkeys_dict
        self.display_hotkeys()
        
    def display_hotkeys(self):
        """Display hotkeys in table"""
        self.table.setRowCount(0)
        
        # Default hotkeys structure
        categories = {
            'File': [
                ('open_file', 'Open File', 'Ctrl+O'),
                ('save_file', 'Save File', 'Ctrl+S'),
                ('quit', 'Quit', 'Ctrl+Q'),
            ],
            'Edit': [
                ('undo', 'Undo', 'Ctrl+Z'),
                ('redo', 'Redo', 'Ctrl+Y'),
                ('copy', 'Copy', 'Ctrl+C'),
                ('paste', 'Paste', 'Ctrl+V'),
            ],
            'View': [
                ('zoom_in', 'Zoom In', 'Ctrl++'),
                ('zoom_out', 'Zoom Out', 'Ctrl+-'),
                ('fit_window', 'Fit to Window', 'Ctrl+0'),
            ],
            'Tools': [
                ('select_tool', 'Select Tool', 'V'),
                ('brush_tool', 'Brush Tool', 'B'),
                ('eraser_tool', 'Eraser Tool', 'E'),
            ]
        }
        
        for category, actions in categories.items():
            for action_id, action_name, default_key in actions:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Category
                self.table.setItem(row, 0, QTableWidgetItem(category))
                
                # Action name
                self.table.setItem(row, 1, QTableWidgetItem(action_name))
                
                # Current key
                current_key = self.hotkeys.get(action_id, default_key)
                self.table.setItem(row, 2, QTableWidgetItem(current_key))
                
                # Default key
                self.table.setItem(row, 3, QTableWidgetItem(default_key))
                
    def on_cell_double_clicked(self, row, col):
        """Handle cell double-click to edit hotkey"""
        if col != 2:  # Only edit current key column
            return
            
        action_item = self.table.item(row, 1)
        current_item = self.table.item(row, 2)
        
        if not action_item or not current_item:
            return
            
        # Show key sequence edit dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Hotkey for {action_item.text()}")
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Press key combination:"))
        
        key_edit = QKeySequenceEdit()
        key_edit.setKeySequence(QKeySequence(current_item.text()))
        layout.addWidget(key_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = key_edit.keySequence().toString()
            if new_key:
                # Check for conflicts
                if self.check_conflict(new_key, row):
                    QMessageBox.warning(self, "Conflict", 
                                      f"Key combination '{new_key}' is already in use!")
                    return
                    
                current_item.setText(new_key)
                # Get action_id from row
                action_id = self.get_action_id_from_row(row)
                self.hotkey_changed.emit(action_id, new_key)
                
    def check_conflict(self, key_sequence, exclude_row):
        """Check if key sequence conflicts with existing"""
        for row in range(self.table.rowCount()):
            if row == exclude_row:
                continue
            item = self.table.item(row, 2)
            if item and item.text() == key_sequence:
                return True
        return False
        
    def get_action_id_from_row(self, row):
        """Get action ID from row (simplified)"""
        action_name = self.table.item(row, 1).text()
        return action_name.lower().replace(' ', '_')
        
    def reset_to_defaults(self):
        """Reset all hotkeys to defaults"""
        for row in range(self.table.rowCount()):
            default_item = self.table.item(row, 3)
            current_item = self.table.item(row, 2)
            if default_item and current_item:
                current_item.setText(default_item.text())
                
    def save_config(self):
        """Save hotkey configuration"""
        config = {}
        for row in range(self.table.rowCount()):
            action_id = self.get_action_id_from_row(row)
            current_key = self.table.item(row, 2).text()
            config[action_id] = current_key
        self.hotkeys = config
        QMessageBox.information(self, "Saved", "Hotkey configuration saved!")


def create_hotkey_display(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return HotkeyDisplayWidget(parent)
