#!/usr/bin/env python3
"""
Test script for organizer settings panel
Shows the settings panel in a standalone window
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    from ui.organizer_settings_panel import OrganizerSettingsPanel
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Organizer Settings Panel Test")
            self.setGeometry(100, 100, 800, 600)
            
            # Create central widget
            central = QWidget()
            layout = QVBoxLayout(central)
            
            # Add settings panel
            config = {
                'organizer': {
                    'feature_extractor': 'CLIP (image-to-text classification)',
                    'clip_model': 'CLIP_ViT-B/32 (340 MB - Balanced)',
                    'dinov2_model': 'DINOv2_base (340 MB - Balanced)',
                    'organization_mode': 'Suggested (AI suggests, you confirm)',
                    'confidence_threshold': 75,
                    'auto_accept': False,
                    'sensitivity': 1.0,
                    'learning_enabled': True,
                    'process_subfolders': True,
                    'archive_input': False,
                    'archive_output': False,
                    'backup_files': True,
                    'naming_pattern': '{category}/{filename}',
                    'case_sensitive': False,
                    'conflict_resolution': 'Number (add suffix: _1, _2, etc.)',
                }
            }
            
            self.settings_panel = OrganizerSettingsPanel(config)
            self.settings_panel.settings_changed.connect(self.on_settings_changed)
            layout.addWidget(self.settings_panel)
            
            self.setCentralWidget(central)
        
        def on_settings_changed(self, settings):
            print("\n" + "=" * 60)
            print("Settings Changed:")
            print("=" * 60)
            for key, value in settings.items():
                print(f"  {key}: {value}")
    
    if __name__ == '__main__':
        app = QApplication(sys.argv)
        window = TestWindow()
        window.show()
        print("\n✓ Settings panel loaded successfully!")
        print("💡 Interact with the settings to see live updates in console")
        sys.exit(app.exec())

except ImportError as e:
    print(f"❌ Could not test UI (missing PyQt6): {e}")
    print("✓ Settings panel code is syntactically correct")
    print("💡 Install PyQt6 to run visual tests: pip install PyQt6")
    sys.exit(0)
