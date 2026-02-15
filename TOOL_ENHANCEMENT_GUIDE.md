# Comprehensive Tool Enhancement Implementation Guide

## Overview
This document provides complete specifications and implementation templates for the requested enhancements to the PS2 Texture Sorter tool suite.

---

## 1. Background Remover - Alpha Presets (COMPLETED ✓)

### Implementation Status
**File**: `src/tools/background_remover.py`
- ✅ Added `AlphaPreset` dataclass
- ✅ Created `AlphaPresets` class with 8 optimized presets
- ✅ Each preset includes detailed "why use" explanations
- ✅ Added `apply_preset()` method to BackgroundRemover

### Presets Available
1. **PS2 Textures** - Optimized for pixelated game textures
2. **Gaming Sprites** - Sharp edges for 2D assets
3. **Art/Illustration** - Smooth gradients for artwork
4. **Photography** - Natural subject isolation
5. **UI Elements** - Crisp boundaries for interface graphics
6. **3D Character Models** - Hair/fur blending
7. **Transparent Objects** - Glass/smoke/water
8. **Pixel Art** - Exact pixel preservation

### UI Integration Needed
Update `src/ui/background_remover_panel.py` to add preset selector:

```python
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

# Add after model selection in _create_widgets()
preset_frame = QFrame(settings_frame)
preset_layout = QHBoxLayout(preset_frame)

preset_label = QLabel("Alpha Preset:")
preset_label.setFixedWidth(120)
preset_layout.addWidget(preset_label)

preset_names = [p.name for p in AlphaPresets.get_all_presets()]
self.preset_combo = QComboBox()
self.preset_combo.addItems(preset_names)
self.preset_combo.setCurrentText("Gaming Sprites")
self.preset_combo.currentTextChanged.connect(self._on_preset_change)
preset_layout.addWidget(self.preset_combo)

# Info button
self.preset_info_btn = QPushButton("ℹ️")
self.preset_info_btn.setFixedWidth(30)
self.preset_info_btn.clicked.connect(self._show_preset_info)
preset_layout.addWidget(self.preset_info_btn)

# Description label
self.preset_desc_label = QLabel()
self.preset_desc_label.setStyleSheet("color: gray;")
self.preset_desc_label.setWordWrap(True)

def _on_preset_change(self, preset_name):
    preset = AlphaPresets.get_preset_by_name(preset_name)
    if preset:
        self.remover.apply_preset(preset)
        self.preset_desc_label.setText(preset.description)
        # Update UI controls to match preset
        self.edge_slider.setValue(int(preset.edge_refinement * 100))

def _show_preset_info(self):
    preset = AlphaPresets.get_preset_by_name(self.preset_combo.currentText())
    if preset:
        QMessageBox.information(
            self,
            f"Preset: {preset.name}",
            f"{preset.description}\n\n"
            f"Why Use This:\n{preset.why_use}\n\n"
            f"Settings:\n"
            f"• Foreground Threshold: {preset.foreground_threshold}\n"
            f"• Background Threshold: {preset.background_threshold}\n"
            f"• Erode Size: {preset.erode_size}\n"
            f"• Edge Refinement: {preset.edge_refinement * 100:.0f}%"
        )
```

---

## 2. Batch Rename Tool (TODO)

### Core Module: `src/tools/batch_renamer.py`

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
"""
Batch File Renamer with Metadata Injection
Rename files by date, resolution, custom templates with privacy/organization features
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass
from datetime import datetime
from PIL import Image
import piexif

logger = logging.getLogger(__name__)


@dataclass
class RenamePattern:
    """Rename pattern definition."""
    name: str
    description: str
    template: str
    example: str


class RenamePatterns:
    """Predefined rename patterns."""
    
    BY_DATE_CREATED = RenamePattern(
        name="Date Created",
        description="Rename using file creation date",
        template="{date_created}_{original_name}",
        example="2024-02-14_texture001.png"
    )
    
    BY_DATE_MODIFIED = RenamePattern(
        name="Date Modified",
        description="Rename using last modification date",
        template="{date_modified}_{index:04d}",
        example="2024-02-14_0001.png"
    )
    
    BY_RESOLUTION = RenamePattern(
        name="Resolution",
        description="Include image resolution in filename",
        template="{width}x{height}_{original_name}",
        example="1920x1080_screenshot.png"
    )
    
    BY_SEQUENTIAL = RenamePattern(
        name="Sequential Numbering",
        description="Simple sequential numbers",
        template="{index:05d}_{original_name}",
        example="00001_image.png"
    )
    
    CUSTOM_PREFIX = RenamePattern(
        name="Custom Prefix",
        description="Add custom prefix to all files",
        template="{prefix}_{original_name}",
        example="mytextures_diffuse.png"
    )
    
    PRIVACY_MODE = RenamePattern(
        name="Privacy (Hash)",
        description="Replace filenames with hash for privacy",
        template="file_{hash:8}",
        example="file_a3f5b2c1.png"
    )
    
    @classmethod
    def get_all_patterns(cls) -> List[RenamePattern]:
        return [
            cls.BY_DATE_CREATED,
            cls.BY_DATE_MODIFIED,
            cls.BY_RESOLUTION,
            cls.BY_SEQUENTIAL,
            cls.CUSTOM_PREFIX,
            cls.PRIVACY_MODE
        ]


class BatchRenamer:
    """Batch file renamer with metadata injection."""
    
    def __init__(self):
        self.files: List[Path] = []
        self.preview: Dict[str, str] = {}
    
    def add_files(self, file_paths: List[str]):
        """Add files to rename queue."""
        self.files = [Path(p) for p in file_paths]
    
    def generate_new_name(self, file_path: Path, pattern: RenamePattern, 
                         index: int, **kwargs) -> str:
        """Generate new filename based on pattern."""
        template = pattern.template
        
        # Get file metadata
        stat = file_path.stat()
        created = datetime.fromtimestamp(stat.st_ctime)
        modified = datetime.fromtimestamp(stat.st_mtime)
        
        # Get image resolution if image file
        width, height = None, None
        try:
            with Image.open(file_path) as img:
                width, height = img.size
        except:
            pass
        
        # Template variables
        variables = {
            'original_name': file_path.stem,
            'extension': file_path.suffix,
            'index': index,
            'date_created': created.strftime('%Y-%m-%d'),
            'date_modified': modified.strftime('%Y-%m-%d'),
            'time_created': created.strftime('%H-%M-%S'),
            'time_modified': modified.strftime('%H-%M-%S'),
            'width': width or 'unknown',
            'height': height or 'unknown',
            'hash': hex(hash(file_path))[2:10],
            **kwargs
        }
        
        # Format template
        try:
            new_name = template.format(**variables)
            return f"{new_name}{file_path.suffix}"
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            return file_path.name
    
    def preview_rename(self, pattern: RenamePattern, **kwargs) -> Dict[str, str]:
        """Preview rename operation."""
        self.preview = {}
        for i, file_path in enumerate(self.files, 1):
            new_name = self.generate_new_name(file_path, pattern, i, **kwargs)
            self.preview[str(file_path)] = new_name
        return self.preview
    
    def execute_rename(self, dry_run: bool = False) -> List[Tuple[str, str, bool]]:
        """Execute the rename operation."""
        results = []
        for old_path_str, new_name in self.preview.items():
            old_path = Path(old_path_str)
            new_path = old_path.parent / new_name
            
            success = False
            if not dry_run:
                try:
                    old_path.rename(new_path)
                    success = True
                except Exception as e:
                    logger.error(f"Failed to rename {old_path}: {e}")
            else:
                success = True  # Dry run always succeeds
            
            results.append((str(old_path), str(new_path), success))
        
        return results
    
    def inject_metadata(self, file_path: Path, copyright_text: str = None,
                       author: str = None, description: str = None):
        """Inject metadata into image file."""
        try:
            # For PNG files
            if file_path.suffix.lower() == '.png':
                from PIL import PngImagePlugin
                img = Image.open(file_path)
                meta = PngImagePlugin.PngInfo()
                
                if copyright_text:
                    meta.add_text("Copyright", copyright_text)
                if author:
                    meta.add_text("Author", author)
                if description:
                    meta.add_text("Description", description)
                
                img.save(file_path, pnginfo=meta)
            
            # For JPG files (use EXIF)
            elif file_path.suffix.lower() in ['.jpg', '.jpeg']:
                img = Image.open(file_path)
                
                # Load existing EXIF or create new
                try:
                    exif_dict = piexif.load(img.info.get('exif', b''))
                except:
                    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
                
                if copyright_text:
                    exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright_text.encode('utf-8')
                if author:
                    exif_dict["0th"][piexif.ImageIFD.Artist] = author.encode('utf-8')
                if description:
                    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = description.encode('utf-8')
                
                exif_bytes = piexif.dump(exif_dict)
                img.save(file_path, exif=exif_bytes, quality=95)
            
            logger.info(f"Metadata injected into {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to inject metadata into {file_path}: {e}")
            return False
```

### UI Panel: `src/ui/batch_rename_panel.py`

```python
"""
Batch Rename UI Panel
"""

from PyQt6.QtWidgets import QFrame, QFileDialog, QMessageBox
from pathlib import Path
from typing import List
import logging

from src.tools.batch_renamer import BatchRenamer, RenamePatterns

logger = logging.getLogger(__name__)


class BatchRenamePanel(QFrame):
    """UI panel for batch file renaming."""
    
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        
        self.renamer = BatchRenamer()
        self.selected_files: List[str] = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Title
        title = ctk.CTkLabel(self, text="📝 Batch Rename Tool", font=("Arial Bold", 18))
        title.pack(pady=(10, 5))
        
        subtitle = ctk.CTkLabel(
            self,
            text="Organize files with custom naming patterns and metadata",
            font=("Arial", 12),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 10))
        
        # File selection
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(file_frame, text="📁 Files:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(btn_frame, text="Select Files", command=self._select_files, width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Select Folder", command=self._select_folder, width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Clear", command=self._clear_files, width=100, fg_color="gray40").pack(side="left", padx=5)
        
        self.file_count_label = ctk.CTkLabel(file_frame, text="No files selected", font=("Arial", 10), text_color="gray")
        self.file_count_label.pack(anchor="w", padx=10, pady=5)
        
        # Pattern selection
        pattern_frame = ctk.CTkFrame(self)
        pattern_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(pattern_frame, text="🎯 Rename Pattern:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        pattern_select_frame = ctk.CTkFrame(pattern_frame)
        pattern_select_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(pattern_select_frame, text="Pattern:", width=80).pack(side="left", padx=5)
        
        patterns = RenamePatterns.get_all_patterns()
        pattern_names = [p.name for p in patterns]
        self.pattern_var = ctk.StringVar(value=pattern_names[0])
        self.pattern_menu = ctk.CTkOptionMenu(
            pattern_select_frame,
            variable=self.pattern_var,
            values=pattern_names,
            command=self._on_pattern_change
        )
        self.pattern_menu.pack(side="left", fill="x", expand=True, padx=5)
        
        self.pattern_desc = ctk.CTkLabel(
            pattern_frame,
            text="",
            font=("Arial", 9),
            text_color="gray",
            wraplength=600
        )
        self.pattern_desc.pack(fill="x", padx=10, pady=(0, 5))
        
        # Custom fields
        custom_frame = ctk.CTkFrame(pattern_frame)
        custom_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(custom_frame, text="Prefix:", width=80).pack(side="left", padx=5)
        self.prefix_entry = ctk.CTkEntry(custom_frame, placeholder_text="Optional prefix")
        self.prefix_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Metadata injection
        metadata_frame = ctk.CTkFrame(self)
        metadata_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(metadata_frame, text="📋 Metadata Injection:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.inject_metadata_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            metadata_frame,
            text="Inject metadata into files",
            variable=self.inject_metadata_var
        ).pack(anchor="w", padx=10, pady=5)
        
        meta_fields = ctk.CTkFrame(metadata_frame)
        meta_fields.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(meta_fields, text="Copyright:", width=80).pack(side="left", padx=5)
        self.copyright_entry = ctk.CTkEntry(meta_fields, placeholder_text="© 2024 Your Name")
        self.copyright_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        meta_fields2 = ctk.CTkFrame(metadata_frame)
        meta_fields2.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(meta_fields2, text="Author:", width=80).pack(side="left", padx=5)
        self.author_entry = ctk.CTkEntry(meta_fields2, placeholder_text="Your Name")
        self.author_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Preview
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(preview_frame, text="👁️ Preview:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.preview_text = ctk.CTkTextbox(preview_frame, height=200)
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            action_frame,
            text="🔍 Preview Rename",
            command=self._preview_rename,
            height=35,
            fg_color="#2196F3"
        ).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            action_frame,
            text="✅ Execute Rename",
            command=self._execute_rename,
            height=40,
            font=("Arial Bold", 14),
            fg_color="#2B7A0B",
            hover_color="#1F5808"
        ).pack(fill="x", padx=10, pady=5)
    
    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Select Files to Rename",
            filetypes=[("All files", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.renamer.add_files(self.selected_files)
            self._update_file_count()
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            folder_path = Path(folder)
            self.selected_files = [str(f) for f in folder_path.iterdir() if f.is_file()]
            self.renamer.add_files(self.selected_files)
            self._update_file_count()
    
    def _clear_files(self):
        self.selected_files = []
        self.renamer.add_files([])
        self._update_file_count()
        self.preview_text.delete("1.0", "end")
    
    def _update_file_count(self):
        count = len(self.selected_files)
        self.file_count_label.configure(
            text=f"{count} file{'s' if count != 1 else ''} selected",
            text_color="white" if count > 0 else "gray"
        )
    
    def _on_pattern_change(self, pattern_name):
        for pattern in RenamePatterns.get_all_patterns():
            if pattern.name == pattern_name:
                self.pattern_desc.configure(
                    text=f"{pattern.description}\nExample: {pattern.example}"
                )
                break
    
    def _preview_rename(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to rename")
            return
        
        pattern_name = self.pattern_var.get()
        pattern = next((p for p in RenamePatterns.get_all_patterns() if p.name == pattern_name), None)
        
        if not pattern:
            return
        
        prefix = self.prefix_entry.get()
        preview = self.renamer.preview_rename(pattern, prefix=prefix)
        
        self.preview_text.delete("1.0", "end")
        for old, new in preview.items():
            old_name = Path(old).name
            self.preview_text.insert("end", f"{old_name} → {new}\n")
    
    def _execute_rename(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to rename")
            return
        
        if not self.renamer.preview:
            messagebox.showwarning("No Preview", "Please preview the rename operation first")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Rename",
            f"Rename {len(self.selected_files)} files?\n\nThis action cannot be undone."
        )
        
        if not confirm:
            return
        
        results = self.renamer.execute_rename(dry_run=False)
        
        # Inject metadata if enabled
        if self.inject_metadata_var.get():
            copyright_text = self.copyright_entry.get()
            author = self.author_entry.get()
            
            for old, new, success in results:
                if success and (copyright_text or author):
                    self.renamer.inject_metadata(
                        Path(new),
                        copyright_text=copyright_text,
                        author=author
                    )
        
        successful = sum(1 for _, _, s in results if s)
        messagebox.showinfo(
            "Rename Complete",
            f"Successfully renamed {successful}/{len(results)} files"
        )
```

---

## 3. Color Correction & Enhancement Tool (TODO)

### Core Module: `src/tools/color_corrector.py`

```python
"""
Color Correction & Enhancement Tool
Auto white balance, exposure correction, vibrance, clarity, LUT support
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import cv2

logger = logging.getLogger(__name__)


class ColorCorrector:
    """Image color correction and enhancement."""
    
    def __init__(self):
        self.lut_cache = {}
    
    def auto_white_balance(self, image: Image.Image) -> Image.Image:
        """
        Apply automatic white balance using gray world algorithm.
        
        Args:
            image: Input PIL Image
        
        Returns:
            White balanced image
        """
        try:
            # Convert to RGB numpy array
            img_array = np.array(image.convert('RGB'), dtype=np.float32)
            
            # Calculate average per channel
            avg_r = np.mean(img_array[:, :, 0])
            avg_g = np.mean(img_array[:, :, 1])
            avg_b = np.mean(img_array[:, :, 2])
            
            # Calculate gray world average
            gray = (avg_r + avg_g + avg_b) / 3
            
            # Calculate scaling factors
            scale_r = gray / avg_r if avg_r > 0 else 1.0
            scale_g = gray / avg_g if avg_g > 0 else 1.0
            scale_b = gray / avg_b if avg_b > 0 else 1.0
            
            # Apply scaling
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * scale_r, 0, 255)
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * scale_g, 0, 255)
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * scale_b, 0, 255)
            
            # Convert back to PIL
            corrected = Image.fromarray(img_array.astype(np.uint8), 'RGB')
            
            logger.info("Applied auto white balance")
            return corrected
        
        except Exception as e:
            logger.error(f"Auto white balance failed: {e}")
            return image
    
    def adjust_exposure(self, image: Image.Image, ev: float) -> Image.Image:
        """
        Adjust exposure by EV stops.
        
        Args:
            image: Input PIL Image
            ev: Exposure value adjustment (-2.0 to +2.0)
        
        Returns:
            Exposure-adjusted image
        """
        try:
            # Convert EV to brightness factor
            factor = 2 ** ev
            
            enhancer = ImageEnhance.Brightness(image)
            adjusted = enhancer.enhance(factor)
            
            logger.info(f"Adjusted exposure by {ev:.2f} EV")
            return adjusted
        
        except Exception as e:
            logger.error(f"Exposure adjustment failed: {e}")
            return image
    
    def enhance_vibrance(self, image: Image.Image, amount: float) -> Image.Image:
        """
        Enhance color vibrance (smart saturation).
        
        Args:
            image: Input PIL Image
            amount: Vibrance amount (0.0 to 2.0, 1.0 = no change)
        
        Returns:
            Vibrance-enhanced image
        """
        try:
            # Convert to HSV for selective saturation boost
            img_array = np.array(image.convert('RGB'))
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV).astype(np.float32)
            
            # Boost saturation more for less saturated colors (vibrance effect)
            saturation = hsv[:, :, 1]
            boost = amount - 1.0
            
            # Apply non-linear boost (less saturated colors get more boost)
            saturation_boost = saturation + boost * (255 - saturation) / 255 * saturation
            hsv[:, :, 1] = np.clip(saturation_boost, 0, 255)
            
            # Convert back to RGB
            rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
            enhanced = Image.fromarray(rgb, 'RGB')
            
            logger.info(f"Enhanced vibrance by {amount:.2f}")
            return enhanced
        
        except Exception as e:
            logger.error(f"Vibrance enhancement failed: {e}")
            return image
    
    def enhance_clarity(self, image: Image.Image, amount: float) -> Image.Image:
        """
        Enhance mid-tone contrast (clarity).
        
        Args:
            image: Input PIL Image
            amount: Clarity amount (0.0 to 2.0, 1.0 = no change)
        
        Returns:
            Clarity-enhanced image
        """
        try:
            if amount == 1.0:
                return image
            
            # Apply unsharp mask for clarity effect
            radius = 5.0
            percent = (amount - 1.0) * 100
            threshold = 3
            
            if percent > 0:
                # Sharpen
                blurred = image.filter(ImageFilter.GaussianBlur(radius))
                img_array = np.array(image, dtype=np.float32)
                blur_array = np.array(blurred, dtype=np.float32)
                
                # Unsharp mask
                sharpened = img_array + percent/100 * (img_array - blur_array)
                enhanced = Image.fromarray(np.clip(sharpened, 0, 255).astype(np.uint8))
            else:
                # Slight blur for negative clarity
                enhanced = image.filter(ImageFilter.GaussianBlur(-percent / 50))
            
            logger.info(f"Enhanced clarity by {amount:.2f}")
            return enhanced
        
        except Exception as e:
            logger.error(f"Clarity enhancement failed: {e}")
            return image
    
    def apply_lut(self, image: Image.Image, lut_path: str) -> Image.Image:
        """
        Apply a LUT (Look-Up Table) to the image.
        
        Args:
            image: Input PIL Image
            lut_path: Path to LUT file (.cube format)
        
        Returns:
            LUT-applied image
        """
        try:
            # Load LUT if not cached
            if lut_path not in self.lut_cache:
                lut = self._load_cube_lut(lut_path)
                if lut is None:
                    return image
                self.lut_cache[lut_path] = lut
            
            lut = self.lut_cache[lut_path]
            
            # Apply LUT
            img_array = np.array(image.convert('RGB'), dtype=np.float32) / 255.0
            
            # Apply 3D LUT interpolation
            result = self._apply_3d_lut(img_array, lut)
            
            enhanced = Image.fromarray((result * 255).astype(np.uint8), 'RGB')
            
            logger.info(f"Applied LUT: {Path(lut_path).name}")
            return enhanced
        
        except Exception as e:
            logger.error(f"LUT application failed: {e}")
            return image
    
    def _load_cube_lut(self, lut_path: str) -> Optional[np.ndarray]:
        """Load a .cube LUT file."""
        try:
            with open(lut_path, 'r') as f:
                lines = f.readlines()
            
            # Parse cube file
            size = None
            data = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('LUT_3D_SIZE'):
                    size = int(line.split()[-1])
                elif line and not line.startswith('#') and not line.startswith('TITLE'):
                    try:
                        values = [float(x) for x in line.split()]
                        if len(values) == 3:
                            data.append(values)
                    except:
                        pass
            
            if size and len(data) == size ** 3:
                lut = np.array(data).reshape((size, size, size, 3))
                return lut
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to load LUT {lut_path}: {e}")
            return None
    
    def _apply_3d_lut(self, image: np.ndarray, lut: np.ndarray) -> np.ndarray:
        """Apply 3D LUT with trilinear interpolation."""
        size = lut.shape[0]
        
        # Scale image values to LUT indices
        r = image[:, :, 0] * (size - 1)
        g = image[:, :, 1] * (size - 1)
        b = image[:, :, 2] * (size - 1)
        
        # Get integer indices
        r0 = np.floor(r).astype(int)
        g0 = np.floor(g).astype(int)
        b0 = np.floor(b).astype(int)
        
        r1 = np.minimum(r0 + 1, size - 1)
        g1 = np.minimum(g0 + 1, size - 1)
        b1 = np.minimum(b0 + 1, size - 1)
        
        # Get fractional parts
        dr = r - r0
        dg = g - g0
        db = b - b0
        
        # Trilinear interpolation (8 corners of cube)
        c000 = lut[r0, g0, b0]
        c001 = lut[r0, g0, b1]
        c010 = lut[r0, g1, b0]
        c011 = lut[r0, g1, b1]
        c100 = lut[r1, g0, b0]
        c101 = lut[r1, g0, b1]
        c110 = lut[r1, g1, b0]
        c111 = lut[r1, g1, b1]
        
        # Interpolate
        dr = dr[:, :, np.newaxis]
        dg = dg[:, :, np.newaxis]
        db = db[:, :, np.newaxis]
        
        result = (
            c000 * (1 - dr) * (1 - dg) * (1 - db) +
            c001 * (1 - dr) * (1 - dg) * db +
            c010 * (1 - dr) * dg * (1 - db) +
            c011 * (1 - dr) * dg * db +
            c100 * dr * (1 - dg) * (1 - db) +
            c101 * dr * (1 - dg) * db +
            c110 * dr * dg * (1 - db) +
            c111 * dr * dg * db
        )
        
        return np.clip(result, 0, 1)
```

---

## 4. Image Format Repair Tool (TODO)

### Core Module: `src/tools/image_repairer.py`

```python
"""
Image Format Repair Tool
Fix corrupted PNG/JPG files and recover partial images
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import struct

logger = logging.getLogger(__name__)


class ImageRepairer:
    """Repair corrupted image files."""
    
    def __init__(self):
        pass
    
    def diagnose(self, file_path: str) -> dict:
        """
        Diagnose image file for corruption.
        
        Returns:
            Dict with diagnosis results
        """
        path = Path(file_path)
        result = {
            'file': str(path),
            'format': None,
            'can_open': False,
            'issues': [],
            'repairable': False
        }
        
        # Try to determine format
        try:
            with Image.open(path) as img:
                result['format'] = img.format
                result['can_open'] = True
                result['size'] = img.size
                result['mode'] = img.mode
        except Exception as e:
            result['issues'].append(f"Cannot open: {str(e)}")
            
            # Try to detect format from header
            with open(path, 'rb') as f:
                header = f.read(16)
                
                if header.startswith(b'\x89PNG\r\n\x1a\n'):
                    result['format'] = 'PNG'
                    result['issues'].append("PNG header present but file corrupted")
                    result['repairable'] = True
                elif header.startswith(b'\xFF\xD8\xFF'):
                    result['format'] = 'JPEG'
                    result['issues'].append("JPEG header present but file corrupted")
                    result['repairable'] = True
        
        return result
    
    def repair_png(self, file_path: str, output_path: Optional[str] = None) -> bool:
        """
        Attempt to repair corrupted PNG file.
        
        Args:
            file_path: Path to corrupted PNG
            output_path: Output path for repaired file
        
        Returns:
            True if repair successful
        """
        try:
            path = Path(file_path)
            if output_path is None:
                output_path = path.parent / f"{path.stem}_repaired{path.suffix}"
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check PNG signature
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                logger.error("Not a PNG file")
                return False
            
            # Find chunks
            pos = 8  # After signature
            chunks = []
            
            while pos < len(data) - 12:
                try:
                    # Read chunk length
                    chunk_len = struct.unpack('>I', data[pos:pos+4])[0]
                    chunk_type = data[pos+4:pos+8]
                    chunk_data = data[pos+8:pos+8+chunk_len]
                    chunk_crc = data[pos+8+chunk_len:pos+12+chunk_len]
                    
                    chunks.append((chunk_type, chunk_data, chunk_crc))
                    pos += 12 + chunk_len
                    
                    # Stop at IEND
                    if chunk_type == b'IEND':
                        break
                except:
                    break
            
            # Reconstruct PNG with valid chunks
            repaired = b'\x89PNG\r\n\x1a\n'
            
            for chunk_type, chunk_data, chunk_crc in chunks:
                chunk_len = len(chunk_data)
                repaired += struct.pack('>I', chunk_len)
                repaired += chunk_type
                repaired += chunk_data
                repaired += chunk_crc
            
            # Add IEND if missing
            if not chunks or chunks[-1][0] != b'IEND':
                repaired += struct.pack('>I', 0)
                repaired += b'IEND'
                repaired += struct.pack('>I', 0xAE426082)  # IEND CRC
            
            # Write repaired file
            with open(output_path, 'wb') as f:
                f.write(repaired)
            
            # Verify it can be opened
            with Image.open(output_path) as img:
                img.verify()
            
            logger.info(f"Successfully repaired PNG: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"PNG repair failed: {e}")
            return False
    
    def repair_jpeg(self, file_path: str, output_path: Optional[str] = None) -> bool:
        """
        Attempt to repair corrupted JPEG file.
        
        Args:
            file_path: Path to corrupted JPEG
            output_path: Output path for repaired file
        
        Returns:
            True if repair successful
        """
        try:
            path = Path(file_path)
            if output_path is None:
                output_path = path.parent / f"{path.stem}_repaired{path.suffix}"
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check JPEG signature
            if not data.startswith(b'\xFF\xD8\xFF'):
                logger.error("Not a JPEG file")
                return False
            
            # Find end of image marker
            eoi_pos = data.rfind(b'\xFF\xD9')
            
            if eoi_pos == -1:
                # Add EOI marker if missing
                repaired = data + b'\xFF\xD9'
            else:
                # Truncate at EOI
                repaired = data[:eoi_pos+2]
            
            # Write repaired file
            with open(output_path, 'wb') as f:
                f.write(repaired)
            
            # Verify it can be opened
            with Image.open(output_path) as img:
                img.verify()
            
            logger.info(f"Successfully repaired JPEG: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"JPEG repair failed: {e}")
            return False
    
    def recover_partial_image(self, file_path: str, output_path: Optional[str] = None) -> Optional[Image.Image]:
        """
        Try to recover whatever is readable from a partial/corrupted image.
        
        Args:
            file_path: Path to corrupted image
            output_path: Optional output path to save recovered portion
        
        Returns:
            Recovered Image or None
        """
        try:
            # Try to load with PIL error handling disabled
            img = Image.open(file_path)
            img.load()
            
            if output_path:
                img.save(output_path)
            
            logger.info(f"Recovered partial image: {file_path}")
            return img
        
        except Exception as e:
            logger.error(f"Partial recovery failed: {e}")
            return None
```

---

## 5. Comprehensive Tooltip System

### Tooltip Categories & Count Per Mode

Based on the existing tooltip system, here are the required tooltip categories and counts:

#### Background Remover (NEW)
- **Preset Selector**: 8 tooltips x 3 modes = 24 tooltips
- **Edge Refinement Slider**: 8 tooltips x 3 modes = 24 tooltips
- **Alpha Matting Toggle**: 8 tooltips x 3 modes = 24 tooltips
- **Model Selector**: 6 tooltips x 3 modes = 18 tooltips
- **Process Button**: 10 tooltips x 3 modes = 30 tooltips

**Total**: ~120 tooltips

#### Batch Renamer (NEW)
- **Pattern Selector**: 8 tooltips x 3 modes = 24 tooltips
- **Prefix/Custom Fields**: 6 tooltips x 3 modes = 18 tooltips
- **Metadata Injection Toggle**: 8 tooltips x 3 modes = 24 tooltips
- **Preview Button**: 6 tooltips x 3 modes = 18 tooltips
- **Execute Button**: 10 tooltips x 3 modes = 30 tooltips

**Total**: ~114 tooltips

#### Color Corrector (NEW)
- **White Balance Button**: 8 tooltips x 3 modes = 24 tooltips
- **Exposure Slider**: 8 tooltips x 3 modes = 24 tooltips
- **Vibrance Slider**: 8 tooltips x 3 modes = 24 tooltips
- **Clarity Slider**: 8 tooltips x 3 modes = 24 tooltips
- **LUT Selector**: 6 tooltips x 3 modes = 18 tooltips

**Total**: ~114 tooltips

#### Image Repairer (NEW)
- **Diagnose Button**: 8 tooltips x 3 modes = 24 tooltips
- **Repair PNG Button**: 8 tooltips x 3 modes = 24 tooltips
- **Repair JPEG Button**: 8 tooltips x 3 modes = 24 tooltips
- **Recover Partial Button**: 8 tooltips x 3 modes = 24 tooltips

**Total**: ~96 tooltips

#### AI Settings (ORGANIZATION)
- **Vision Models Section**: 10 tooltips x 3 modes = 30 tooltips
- **Background Removal Models**: 6 tooltips x 3 modes = 18 tooltips
- **Model Download/Update**: 6 tooltips x 3 modes = 18 tooltips

**Total**: ~66 tooltips

### Grand Total New Tooltips: ~510 tooltips across all 3 modes

### Tooltip Mode Examples

#### NORMAL Mode (Professional)
```python
"Select an alpha preset optimized for your image type. PS2 Textures work best for pixelated game assets."
```

#### DUMBED_DOWN Mode (Simple)
```python
"Pick the type of picture you have. If it's from a PS2 game, pick PS2 Textures."
```

#### CURSING/UNHINGED Mode (Profane but Helpful)
```python
"Holy f*ck, just pick PS2 Textures if you're working with crusty old PlayStation 2 garbage. "
"It's literally designed for those blocky-ass sprites. Don't overthink it, genius."
```

### Implementation in `src/features/unlockables_system.py`

Add new tooltip collections:

```python
# Add to TOOLTIP_COLLECTIONS in UnlockablesSystem

"background_remover": TooltipCollection(
    id="background_remover",
    name="Background Remover Tips",
    category="tools",
    tooltips=[
        "Alpha presets save time - each one is tuned for specific content types",
        "PS2 Textures preset: aggressive thresholds for pixel-perfect edges",
        "Higher edge refinement = softer edges. Use 0.8+ for photos, 0.2 for sprites",
        # ... 12 more normal tooltips
    ],
    unlock_condition=UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
    unlocked=True
),

"batch_renamer": TooltipCollection(
    id="batch_renamer",
    name="Batch Rename Tips",
    category="tools",
    tooltips=[
        "Date patterns help organize chronologically - great for game dev assets",
        "Privacy mode replaces filenames with hashes - perfect for sharing work samples",
        "Metadata injection adds copyright info directly into PNG/JPG files",
        # ... 12 more normal tooltips
    ],
    unlock_condition=UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
    unlocked=True
),

"color_corrector": TooltipCollection(
    id="color_corrector",
    name="Color Correction Tips",
    category="tools",
    tooltips=[
        "Auto white balance uses gray world algorithm - works best on photos",
        "Exposure in EV stops: +1 = double brightness, -1 = half brightness",
        "Vibrance boosts muted colors more than saturated ones - natural look",
        # ... 12 more normal tooltips
    ],
    unlock_condition=UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
    unlocked=True
),

"image_repairer": TooltipCollection(
    id="image_repairer",
    name="Image Repair Tips",
    category="tools",
    tooltips=[
        "PNG corruption usually means missing or invalid chunks - often fixable",
        "JPEG files need SOI (start) and EOI (end) markers to be valid",
        "Partial recovery extracts whatever data is readable - may lose bottom portion",
        # ... 12 more normal tooltips
    ],
    unlock_condition=UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
    unlocked=True
)
```

### Implementation in `src/features/tutorial_system.py`

Extend `_PANDA_TOOLTIPS` dictionary with new tool tooltips in all 3 modes.

---

## 6. AI Settings Organization

### Settings Structure

Current AI settings are in a single tab. Reorganize into subcategories:

```python
# In main.py or settings panel

ai_settings_frame = ctk.CTkScrollableFrame(tab_ai)
ai_settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Vision Models Section
vision_frame = ctk.CTkFrame(ai_settings_frame)
vision_frame.pack(fill="x", padx=5, pady=5)

ctk.CTkLabel(vision_frame, text="🔍 Vision Models", font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)

# CLIP settings
clip_subsection = ctk.CTkFrame(vision_frame)
clip_subsection.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(clip_subsection, text="CLIP:", width=100).pack(side="left", padx=5)
# Add CLIP model selector, enable toggle, etc.

# ViT settings
vit_subsection = ctk.CTkFrame(vision_frame)
vit_subsection.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(vit_subsection, text="ViT:", width=100).pack(side="left", padx=5)
# Add ViT model selector, enable toggle, etc.

# DINOv2 settings
dino_subsection = ctk.CTkFrame(vision_frame)
dino_subsection.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(dino_subsection, text="DINOv2:", width=100).pack(side="left", padx=5)
# Add DINOv2 settings

# SAM settings
sam_subsection = ctk.CTkFrame(vision_frame)
sam_subsection.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(sam_subsection, text="SAM:", width=100).pack(side="left", padx=5)
# Add SAM settings

# Background Removal Models Section
bg_removal_frame = ctk.CTkFrame(ai_settings_frame)
bg_removal_frame.pack(fill="x", padx=5, pady=5)

ctk.CTkLabel(bg_removal_frame, text="🎭 Background Removal", font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)

# Model selector
model_subsection = ctk.CTkFrame(bg_removal_frame)
model_subsection.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(model_subsection, text="Model:", width=100).pack(side="left", padx=5)

models = ["u2net", "u2netp", "u2net_human_seg", "silueta"]
bg_model_var = ctk.StringVar(value="u2net")
ctk.CTkOptionMenu(model_subsection, variable=bg_model_var, values=models).pack(side="left", padx=5)

# Download button
ctk.CTkButton(model_subsection, text="Download Model", width=120).pack(side="left", padx=5)

# Color Correction Models Section (if AI-based in future)
# ...
```

---

## 7. Implementation Priority

Given the extensive scope, implement in this order:

1. ✅ **Background Remover Alpha Presets** (COMPLETED)
2. **Update Background Remover UI** with preset selector
3. **Batch Rename Tool** (core + UI)
4. **Color Correction Tool** (core + UI)
5. **Image Repair Tool** (core + UI)
6. **AI Settings Organization**
7. **Comprehensive Tooltip System** for all new tools

---

## 8. Testing Checklist

- [ ] Background remover preset application works
- [ ] UI preset selector updates parameters correctly
- [ ] Batch renamer preview shows correct filenames
- [ ] Batch renamer metadata injection works (PNG + JPEG)
- [ ] Color corrector white balance improves images
- [ ] Color corrector LUT loading and application works
- [ ] Image repairer diagnoses corrupted files correctly
- [ ] Image repairer fixes PNG corruption
- [ ] Image repairer fixes JPEG corruption
- [ ] All tooltips display in all 3 modes
- [ ] AI settings organized into proper sections
- [ ] All new tools accessible from main UI

---

## 9. Documentation

Each tool needs:
- User guide (markdown file)
- API documentation (docstrings)
- Examples for common use cases
- Tooltip explanations

---

## 10. Dependencies

Add to `requirements.txt`:

```
# Image repair and manipulation
piexif>=1.1.3  # EXIF metadata handling
opencv-python>=4.8.0  # Advanced image processing
```

The existing dependencies (PIL/Pillow, numpy, rembg) are already sufficient for most functionality.
