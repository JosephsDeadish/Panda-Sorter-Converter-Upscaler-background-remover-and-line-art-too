"""Organizer Tool Settings Panel - All AI and processing options"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider,
    QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QLineEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class OrganizerSettingsPanel(QWidget):
    """Settings for Organizer Tool"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, config: dict = None, tooltip_manager=None):
        super().__init__()
        self.config = config or {}
        self.tooltip_manager = tooltip_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Create settings UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🤖 Organizer AI Settings")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        # ===== AI MODEL SELECTION =====
        model_group = self.create_group("🧠 AI Model Selection")
        
        model_layout = QVBoxLayout()
        
        # Feature Extractor selector
        extractor_layout = QHBoxLayout()
        extractor_label = QLabel("Feature Extractor:")
        extractor_label.setMinimumWidth(100)
        self.extractor_combo = QComboBox()
        self.extractor_combo.addItems([
            "CLIP (image-to-text classification)",
            "DINOv2 (visual similarity clustering)",
            "timm (PyTorch Image Models)",
            "CLIP+DINOv2 (Combined: text + visual)",
            "CLIP+timm (Combined: text + PyTorch)",
            "DINOv2+timm (Combined: visual + PyTorch)",
            "CLIP+DINOv2+timm (All three combined)"
        ])
        self.extractor_combo.currentTextChanged.connect(self.on_extractor_changed)
        extractor_layout.addWidget(extractor_label)
        extractor_layout.addWidget(self.extractor_combo)
        extractor_layout.addStretch()
        model_layout.addLayout(extractor_layout)
        
        # Performance warning label (initially hidden)
        self.perf_warning_label = QLabel()
        self.perf_warning_label.setStyleSheet("""
            QLabel {
                color: #ff6b00;
                font-weight: bold;
                padding: 8px;
                background-color: #fff3e0;
                border: 1px solid #ffb74d;
                border-radius: 4px;
            }
        """)
        self.perf_warning_label.setWordWrap(True)
        self.perf_warning_label.setVisible(False)
        model_layout.addWidget(self.perf_warning_label)
        
        # CLIP selector
        self.clip_layout = QHBoxLayout()
        clip_label = QLabel("CLIP Model:")
        clip_label.setMinimumWidth(100)
        self.clip_combo = QComboBox()
        self.clip_combo.addItems([
            "CLIP_ViT-B/32 (340 MB - Balanced)",
            "CLIP_ViT-L/14 (427 MB - More Accurate)"
        ])
        self.clip_combo.currentTextChanged.connect(lambda: self.emit_settings())
        self.clip_layout.addWidget(clip_label)
        self.clip_layout.addWidget(self.clip_combo)
        self.clip_layout.addStretch()
        model_layout.addLayout(self.clip_layout)
        
        # DINOv2 selector
        self.dinov2_layout = QHBoxLayout()
        dinov2_label = QLabel("DINOv2 Model:")
        dinov2_label.setMinimumWidth(100)
        self.dinov2_combo = QComboBox()
        self.dinov2_combo.addItems([
            "DINOv2_small (81 MB - Fast)",
            "DINOv2_base (340 MB - Balanced)",
            "DINOv2_large (1100 MB - Most Accurate)"
        ])
        self.dinov2_combo.setCurrentIndex(1)  # Default to base
        self.dinov2_combo.currentTextChanged.connect(lambda: self.emit_settings())
        self.dinov2_layout.addWidget(dinov2_label)
        self.dinov2_layout.addWidget(self.dinov2_combo)
        self.dinov2_layout.addStretch()
        model_layout.addLayout(self.dinov2_layout)
        
        # Organization mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Organization Mode:")
        mode_label.setMinimumWidth(100)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Automatic (AI instantly classifies)",
            "Suggested (AI suggests, you confirm)",
            "Manual (You type, AI suggests)"
        ])
        self.mode_combo.currentTextChanged.connect(lambda: self.emit_settings())
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        model_layout.addLayout(mode_layout)
        
        model_group.setLayout(model_layout)
        scroll_layout.addWidget(model_group)
        
        # ===== CONFIDENCE THRESHOLD =====
        threshold_group = self.create_group("📊 Confidence Settings")
        
        threshold_layout = QVBoxLayout()
        
        # Confidence threshold slider
        conf_label_layout = QHBoxLayout()
        conf_label = QLabel("Confidence Threshold:")
        conf_label.setMinimumWidth(150)
        self.conf_value_label = QLabel("75%")
        self.conf_value_label.setMinimumWidth(50)
        conf_label_layout.addWidget(conf_label)
        conf_label_layout.addStretch()
        conf_label_layout.addWidget(self.conf_value_label)
        threshold_layout.addLayout(conf_label_layout)
        
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setMinimum(0)
        self.conf_slider.setMaximum(100)
        self.conf_slider.setValue(75)
        self.conf_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.conf_slider.setTickInterval(10)
        self.conf_slider.valueChanged.connect(self.on_confidence_changed)
        threshold_layout.addWidget(self.conf_slider)
        
        # Auto-accept checkbox
        self.auto_accept_check = QCheckBox("Auto-accept suggestions above threshold")
        self.auto_accept_check.stateChanged.connect(lambda: self.emit_settings())
        threshold_layout.addWidget(self.auto_accept_check)
        
        # Suggestion sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_label = QLabel("Suggestion Sensitivity:")
        sensitivity_label.setMinimumWidth(150)
        self.sensitivity_spin = QDoubleSpinBox()
        self.sensitivity_spin.setMinimum(0.1)
        self.sensitivity_spin.setMaximum(2.0)
        self.sensitivity_spin.setValue(1.0)
        self.sensitivity_spin.setSingleStep(0.1)
        self.sensitivity_spin.setSuffix("x")
        self.sensitivity_spin.valueChanged.connect(lambda: self.emit_settings())
        sensitivity_layout.addWidget(sensitivity_label)
        sensitivity_layout.addWidget(self.sensitivity_spin)
        sensitivity_layout.addStretch()
        threshold_layout.addLayout(sensitivity_layout)
        
        threshold_group.setLayout(threshold_layout)
        scroll_layout.addWidget(threshold_group)
        
        # ===== LEARNING SYSTEM =====
        learning_group = self.create_group("🧠 Learning System")
        
        learning_layout = QVBoxLayout()
        
        # Enable learning checkbox
        self.learning_enabled_check = QCheckBox("Enable AI Learning from corrections")
        self.learning_enabled_check.setChecked(True)
        self.learning_enabled_check.stateChanged.connect(lambda: self.emit_settings())
        learning_layout.addWidget(self.learning_enabled_check)
        
        # Clear history button
        clear_btn = QPushButton("🗑️  Clear Learning History")
        clear_btn.setMinimumHeight(35)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffcccc;
                border: 1px solid #ff9999;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff9999;
            }
        """)
        clear_btn.clicked.connect(self.on_clear_learning)
        learning_layout.addWidget(clear_btn)
        
        learning_group.setLayout(learning_layout)
        scroll_layout.addWidget(learning_group)
        
        # ===== FILE HANDLING =====
        file_group = self.create_group("📁 File Handling")
        
        file_layout = QVBoxLayout()
        
        # Process subfolders
        self.subfolders_check = QCheckBox("Include subfolders in processing")
        self.subfolders_check.setChecked(True)
        self.subfolders_check.stateChanged.connect(lambda: self.emit_settings())
        file_layout.addWidget(self.subfolders_check)
        
        # Archive input
        self.archive_input_check = QCheckBox("Support archive input (.zip, .7z, .rar, .tar)")
        self.archive_input_check.setChecked(False)
        self.archive_input_check.stateChanged.connect(lambda: self.emit_settings())
        file_layout.addWidget(self.archive_input_check)
        
        # Archive output
        self.archive_output_check = QCheckBox("Save organized result to archive")
        self.archive_output_check.setChecked(False)
        self.archive_output_check.stateChanged.connect(lambda: self.emit_settings())
        file_layout.addWidget(self.archive_output_check)
        
        # Backup original files
        self.backup_check = QCheckBox("Backup original files before moving")
        self.backup_check.setChecked(True)
        self.backup_check.stateChanged.connect(lambda: self.emit_settings())
        file_layout.addWidget(self.backup_check)
        
        file_group.setLayout(file_layout)
        scroll_layout.addWidget(file_group)
        
        # ===== NAMING & CONFLICT RESOLUTION =====
        naming_group = self.create_group("🏷️  Naming & Conflicts")
        
        naming_layout = QVBoxLayout()
        
        # Naming pattern
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Naming Pattern:")
        pattern_label.setMinimumWidth(120)
        self.pattern_input = QLineEdit()
        self.pattern_input.setText("{category}/{filename}")
        self.pattern_input.setToolTip("Use: {category}, {filename}, {game}, {confidence}")
        self.pattern_input.textChanged.connect(lambda: self.emit_settings())
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addWidget(self.pattern_input)
        naming_layout.addLayout(pattern_layout)
        
        # Case sensitivity
        self.case_sensitive_check = QCheckBox("Case-sensitive matching")
        self.case_sensitive_check.stateChanged.connect(lambda: self.emit_settings())
        naming_layout.addWidget(self.case_sensitive_check)
        
        # Conflict resolution
        conflict_layout = QHBoxLayout()
        conflict_label = QLabel("When file exists:")
        conflict_label.setMinimumWidth(120)
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems([
            "Skip (leave existing)",
            "Overwrite (replace)",
            "Number (add suffix: _1, _2, etc.)"
        ])
        self.conflict_combo.setCurrentIndex(2)  # Default to numbering
        self.conflict_combo.currentTextChanged.connect(lambda: self.emit_settings())
        conflict_layout.addWidget(conflict_label)
        conflict_layout.addWidget(self.conflict_combo)
        conflict_layout.addStretch()
        naming_layout.addLayout(conflict_layout)
        
        naming_group.setLayout(naming_layout)
        scroll_layout.addWidget(naming_group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def create_group(self, title: str) -> QGroupBox:
        """Create a styled group box"""
        group = QGroupBox(title)
        font = QFont()
        font.setBold(True)
        group.setFont(font)
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        return group
    
    def on_extractor_changed(self):
        """Update model-specific dropdown visibility based on selected feature extractor"""
        extractor = self.extractor_combo.currentText()
        
        # Hide all model-specific dropdowns first
        self.set_layout_visible(self.clip_layout, False)
        self.set_layout_visible(self.dinov2_layout, False)
        
        # Check if this is a combined model
        is_combined = self.is_combined_model(extractor)
        
        # Show relevant dropdowns based on selection
        if "CLIP" in extractor:
            self.set_layout_visible(self.clip_layout, True)
        if "DINOv2" in extractor:
            self.set_layout_visible(self.dinov2_layout, True)
        # For timm alone, no specific model dropdown is shown
        # For combined models with timm, we show the other model dropdowns
        
        # Show performance warning for combined models
        if is_combined:
            self.show_performance_warning(extractor)
        else:
            self.perf_warning_label.setVisible(False)
        
        self.emit_settings()
    
    def is_combined_model(self, extractor: str) -> bool:
        """Check if the selected extractor is a combined model"""
        return '+' in extractor
    
    def show_performance_warning(self, extractor: str):
        """Show performance warning for combined models"""
        model_count = extractor.count('+') + 1
        
        if model_count == 3:
            warning_text = "⚠️ Warning: Using all three models (CLIP+DINOv2+timm) will significantly impact performance. Processing will be slower but may provide better accuracy for complex categorization tasks."
        elif model_count == 2:
            warning_text = f"⚠️ Warning: {extractor.split(' ')[0]} combines two models, which may reduce processing speed. This provides better accuracy but takes longer than single models."
        else:
            warning_text = ""
        
        if warning_text:
            self.perf_warning_label.setText(warning_text)
            self.perf_warning_label.setVisible(True)
        else:
            self.perf_warning_label.setVisible(False)
    
    def set_layout_visible(self, layout, visible):
        """Set visibility for all widgets in a layout"""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setVisible(visible)
    
    def on_confidence_changed(self, value: int):
        """Update confidence value display"""
        self.conf_value_label.setText(f"{value}%")
        self.emit_settings()
    
    def on_clear_learning(self):
        """Clear learning history"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Clear Learning History",
            "This will delete all learned preferences. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Import learning system and clear history
            try:
                from organizer.learning_system import AILearningSystem
                learning_system = AILearningSystem()
                learning_system.clear_learning_history()
                
                QMessageBox.information(
                    self,
                    "History Cleared",
                    "Learning history has been cleared successfully."
                )
            except ImportError:
                QMessageBox.warning(
                    self,
                    "Not Available",
                    "Learning system is not available. Cannot clear history."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to clear learning history: {str(e)}"
                )
    
    def load_settings(self):
        """Load settings from config"""
        if 'organizer' in self.config:
            org_config = self.config['organizer']
            
            # Load Feature Extractor
            if 'feature_extractor' in org_config:
                extractor_text = org_config['feature_extractor']
                idx = self.extractor_combo.findText(extractor_text, Qt.MatchFlag.MatchContains)
                if idx >= 0:
                    self.extractor_combo.setCurrentIndex(idx)
            
            # Load CLIP model
            if 'clip_model' in org_config:
                clip_text = org_config['clip_model']
                idx = self.clip_combo.findText(clip_text, Qt.MatchFlag.MatchContains)
                if idx >= 0:
                    self.clip_combo.setCurrentIndex(idx)
            
            # Load DINOv2 model
            if 'dinov2_model' in org_config:
                dinov2_text = org_config['dinov2_model']
                idx = self.dinov2_combo.findText(dinov2_text, Qt.MatchFlag.MatchContains)
                if idx >= 0:
                    self.dinov2_combo.setCurrentIndex(idx)
            
            # Load other settings
            if 'organization_mode' in org_config:
                mode_text = org_config['organization_mode']
                idx = self.mode_combo.findText(mode_text, Qt.MatchFlag.MatchContains)
                if idx >= 0:
                    self.mode_combo.setCurrentIndex(idx)
            
            if 'confidence_threshold' in org_config:
                self.conf_slider.setValue(org_config['confidence_threshold'])
            
            if 'auto_accept' in org_config:
                self.auto_accept_check.setChecked(org_config['auto_accept'])
            
            if 'sensitivity' in org_config:
                self.sensitivity_spin.setValue(org_config['sensitivity'])
            
            if 'learning_enabled' in org_config:
                self.learning_enabled_check.setChecked(org_config['learning_enabled'])
            
            if 'process_subfolders' in org_config:
                self.subfolders_check.setChecked(org_config['process_subfolders'])
            
            if 'archive_input' in org_config:
                self.archive_input_check.setChecked(org_config['archive_input'])
            
            if 'archive_output' in org_config:
                self.archive_output_check.setChecked(org_config['archive_output'])
            
            if 'backup_files' in org_config:
                self.backup_check.setChecked(org_config['backup_files'])
            
            if 'naming_pattern' in org_config:
                self.pattern_input.setText(org_config['naming_pattern'])
            
            if 'case_sensitive' in org_config:
                self.case_sensitive_check.setChecked(org_config['case_sensitive'])
            
            if 'conflict_resolution' in org_config:
                conflict_text = org_config['conflict_resolution']
                idx = self.conflict_combo.findText(conflict_text, Qt.MatchFlag.MatchContains)
                if idx >= 0:
                    self.conflict_combo.setCurrentIndex(idx)
    
    def emit_settings(self):
        """Emit current settings"""
        settings = {
            'feature_extractor': self.extractor_combo.currentText(),
            'clip_model': self.clip_combo.currentText(),
            'dinov2_model': self.dinov2_combo.currentText(),
            'organization_mode': self.mode_combo.currentText(),
            'confidence_threshold': self.conf_slider.value(),
            'auto_accept': self.auto_accept_check.isChecked(),
            'sensitivity': self.sensitivity_spin.value(),
            'learning_enabled': self.learning_enabled_check.isChecked(),
            'process_subfolders': self.subfolders_check.isChecked(),
            'archive_input': self.archive_input_check.isChecked(),
            'archive_output': self.archive_output_check.isChecked(),
            'backup_files': self.backup_check.isChecked(),
            'naming_pattern': self.pattern_input.text(),
            'case_sensitive': self.case_sensitive_check.isChecked(),
            'conflict_resolution': self.conflict_combo.currentText(),
        }
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Get current settings as dict"""
        return {
            'feature_extractor': self.extractor_combo.currentText(),
            'clip_model': self.clip_combo.currentText(),
            'dinov2_model': self.dinov2_combo.currentText(),
            'organization_mode': self.mode_combo.currentText(),
            'confidence_threshold': self.conf_slider.value(),
            'auto_accept': self.auto_accept_check.isChecked(),
            'sensitivity': self.sensitivity_spin.value(),
            'learning_enabled': self.learning_enabled_check.isChecked(),
            'process_subfolders': self.subfolders_check.isChecked(),
            'archive_input': self.archive_input_check.isChecked(),
            'archive_output': self.archive_output_check.isChecked(),
            'backup_files': self.backup_check.isChecked(),
            'naming_pattern': self.pattern_input.text(),
            'case_sensitive': self.case_sensitive_check.isChecked(),
            'conflict_resolution': self.conflict_combo.currentText(),
        }
    
    def save_settings(self):
        """Save current settings to config"""
        try:
            # Get current settings
            settings = self.get_settings()
            
            # Update config
            if 'organizer' not in self.config:
                self.config['organizer'] = {}
            
            self.config['organizer'].update(settings)
            
            # Emit settings changed signal
            self.emit_settings()
            
            return True
        except Exception as e:
            logger.error(f"Error saving organizer settings: {e}", exc_info=True)
            return False

    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
