"""
Image Repair Tool
Repairs corrupted PNG and JPEG image files.
"""

import os
import struct
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
from PIL import Image
import io

logger = logging.getLogger(__name__)


class CorruptionType(Enum):
    """Types of image corruption."""
    NONE = "none"
    HEADER = "header"
    CHUNK = "chunk"
    CRC = "crc"
    MARKER = "marker"
    TRUNCATED = "truncated"
    UNKNOWN = "unknown"


class RepairMode(Enum):
    """Repair aggressiveness modes."""
    SAFE = "safe"              # Conservative - only PIL recovery
    BALANCED = "balanced"      # Try PIL first, then basic manual repairs
    AGGRESSIVE = "aggressive"  # Attempt all recovery methods including risky ones


class RepairResult(Enum):
    """Result of repair attempt."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_CORRUPTED = "not_corrupted"


class DiagnosticReport:
    """Diagnostic report for an image file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file_type = None
        self.file_size = 0
        self.is_corrupted = False
        self.corruption_type = CorruptionType.NONE
        self.corruption_location = None
        self.repairable = False
        self.recovery_percentage = 0.0
        self.notes = []
    
    def add_note(self, note: str):
        """Add a diagnostic note."""
        self.notes.append(note)
        logger.info(f"Diagnostic: {note}")
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'filepath': self.filepath,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'is_corrupted': self.is_corrupted,
            'corruption_type': self.corruption_type.value if self.corruption_type else None,
            'corruption_location': self.corruption_location,
            'repairable': self.repairable,
            'recovery_percentage': self.recovery_percentage,
            'notes': self.notes
        }


class PNGRepairer:
    """Repairs corrupted PNG files."""
    
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def diagnose(self, filepath: str) -> DiagnosticReport:
        """Diagnose PNG file corruption."""
        report = DiagnosticReport(filepath)
        report.file_type = "PNG"
        
        try:
            report.file_size = os.path.getsize(filepath)
            
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Check PNG signature
            if not data.startswith(self.PNG_SIGNATURE):
                report.is_corrupted = True
                report.corruption_type = CorruptionType.HEADER
                report.add_note("Invalid PNG signature")
                report.repairable = len(data) > 8
                return report
            
            # Parse chunks
            pos = 8  # After signature
            chunks_found = []
            has_iend = False
            
            while pos < len(data) - 12:
                try:
                    # Read chunk length
                    chunk_length = struct.unpack('>I', data[pos:pos+4])[0]
                    chunk_type = data[pos+4:pos+8].decode('ascii', errors='ignore')
                    chunks_found.append(chunk_type)
                    
                    if chunk_type == 'IEND':
                        has_iend = True
                        break
                    
                    # Calculate CRC
                    chunk_data = data[pos+4:pos+8+chunk_length]
                    stored_crc = struct.unpack('>I', data[pos+8+chunk_length:pos+12+chunk_length])[0]
                    calculated_crc = self._calculate_crc(chunk_data)
                    
                    if stored_crc != calculated_crc:
                        report.is_corrupted = True
                        report.corruption_type = CorruptionType.CRC
                        report.corruption_location = pos
                        report.add_note(f"CRC mismatch in {chunk_type} chunk at byte {pos}")
                        report.repairable = True
                        return report
                    
                    pos += 12 + chunk_length
                    
                except Exception as e:
                    report.is_corrupted = True
                    report.corruption_type = CorruptionType.CHUNK
                    report.corruption_location = pos
                    report.add_note(f"Chunk parsing error at byte {pos}: {str(e)}")
                    report.repairable = True
                    report.recovery_percentage = (pos / len(data)) * 100
                    return report
            
            if not has_iend:
                report.is_corrupted = True
                report.corruption_type = CorruptionType.TRUNCATED
                report.add_note("Missing IEND chunk (file truncated)")
                report.repairable = True
                report.recovery_percentage = 80.0
                return report
            
            report.add_note("PNG file appears valid")
            report.recovery_percentage = 100.0
            
        except Exception as e:
            report.is_corrupted = True
            report.corruption_type = CorruptionType.UNKNOWN
            report.add_note(f"Error during diagnosis: {str(e)}")
            report.repairable = False
        
        return report
    
    def repair(self, filepath: str, output_path: str, mode: RepairMode = RepairMode.BALANCED) -> Tuple[RepairResult, str]:
        """
        Attempt to repair PNG file.
        
        Args:
            filepath: Path to corrupted PNG file
            output_path: Path for repaired output
            mode: Repair aggressiveness mode
            
        Returns:
            Tuple of (RepairResult, message)
        """
        report = self.diagnose(filepath)
        
        if not report.is_corrupted:
            return RepairResult.NOT_CORRUPTED, "File is not corrupted"
        
        if not report.repairable:
            return RepairResult.FAILED, "File is not repairable"
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Mode: SAFE - Only try PIL recovery
            if mode == RepairMode.SAFE:
                try:
                    img = Image.open(filepath)
                    img.load()
                    img.save(output_path, 'PNG', optimize=True)
                    return RepairResult.SUCCESS, "Repaired using PIL recovery (safe mode)"
                except Exception as e:
                    return RepairResult.FAILED, f"Safe mode PIL recovery failed: {str(e)}"
            
            # Mode: BALANCED or AGGRESSIVE - Try PIL first, then manual repairs
            try:
                img = Image.open(filepath)
                img.load()  # Force load the image data
                img.save(output_path, 'PNG', optimize=True)
                return RepairResult.SUCCESS, "Repaired using PIL recovery"
            except Exception:
                pass
            
            # Manual repair attempts
            if report.corruption_type == CorruptionType.HEADER:
                # Try to fix header
                fixed_data = self.PNG_SIGNATURE + data[8:]
                with open(output_path, 'wb') as f:
                    f.write(fixed_data)
                return RepairResult.PARTIAL, "Header repaired, verify manually"
            
            elif report.corruption_type == CorruptionType.TRUNCATED:
                # Try to add IEND chunk
                fixed_data = data + struct.pack('>I', 0) + b'IEND' + struct.pack('>I', 0xAE426082)
                with open(output_path, 'wb') as f:
                    f.write(fixed_data)
                return RepairResult.PARTIAL, "Added IEND chunk, verify manually"
            
            elif report.corruption_type == CorruptionType.CRC and mode == RepairMode.AGGRESSIVE:
                # Aggressive mode: Try to reconstruct with CRC errors ignored
                try:
                    # Use PIL with error tolerance
                    from PIL import ImageFile
                    ImageFile.LOAD_TRUNCATED_IMAGES = True
                    img = Image.open(filepath)
                    img.load()
                    img.save(output_path, 'PNG', optimize=True)
                    ImageFile.LOAD_TRUNCATED_IMAGES = False
                    return RepairResult.PARTIAL, "Repaired with CRC errors ignored (aggressive mode)"
                except Exception as e:
                    ImageFile.LOAD_TRUNCATED_IMAGES = False
                    return RepairResult.FAILED, f"Aggressive CRC repair failed: {str(e)}"
            
            else:
                return RepairResult.FAILED, f"Cannot repair {report.corruption_type.value} corruption"
                
        except Exception as e:
            return RepairResult.FAILED, f"Repair failed: {str(e)}"
    
    @staticmethod
    def _calculate_crc(data: bytes) -> int:
        """Calculate CRC32 for PNG chunk."""
        import zlib
        return zlib.crc32(data) & 0xffffffff


class JPEGRepairer:
    """Repairs corrupted JPEG files."""
    
    SOI_MARKER = b'\xFF\xD8'  # Start of Image
    EOI_MARKER = b'\xFF\xD9'  # End of Image
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def diagnose(self, filepath: str) -> DiagnosticReport:
        """Diagnose JPEG file corruption."""
        report = DiagnosticReport(filepath)
        report.file_type = "JPEG"
        
        try:
            report.file_size = os.path.getsize(filepath)
            
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Check SOI marker
            if not data.startswith(self.SOI_MARKER):
                report.is_corrupted = True
                report.corruption_type = CorruptionType.HEADER
                report.add_note("Missing SOI marker (0xFFD8)")
                report.repairable = len(data) > 2
                return report
            
            # Check for EOI marker
            if not data.endswith(self.EOI_MARKER):
                # Try to find EOI in the file
                eoi_pos = data.rfind(self.EOI_MARKER)
                if eoi_pos > 0:
                    report.add_note(f"EOI marker found at byte {eoi_pos}, but extra data after")
                    report.recovery_percentage = (eoi_pos / len(data)) * 100
                else:
                    report.is_corrupted = True
                    report.corruption_type = CorruptionType.TRUNCATED
                    report.add_note("Missing EOI marker (file truncated)")
                    report.repairable = True
                    
                    # Try to estimate recovery percentage by finding last valid marker
                    last_marker_pos = 0
                    for i in range(len(data) - 1, 0, -1):
                        if data[i] == 0xFF and data[i+1] >= 0xC0:
                            last_marker_pos = i
                            break
                    report.recovery_percentage = (last_marker_pos / len(data)) * 100
                    return report
            
            # Try to open with PIL
            try:
                img = Image.open(filepath)
                img.verify()
                report.add_note("JPEG file appears valid")
                report.recovery_percentage = 100.0
            except Exception as e:
                report.is_corrupted = True
                report.corruption_type = CorruptionType.UNKNOWN
                report.add_note(f"PIL verification failed: {str(e)}")
                report.repairable = True
                report.recovery_percentage = 50.0
            
        except Exception as e:
            report.is_corrupted = True
            report.corruption_type = CorruptionType.UNKNOWN
            report.add_note(f"Error during diagnosis: {str(e)}")
            report.repairable = False
        
        return report
    
    def repair(self, filepath: str, output_path: str, mode: RepairMode = RepairMode.BALANCED) -> Tuple[RepairResult, str]:
        """
        Attempt to repair JPEG file.
        
        Args:
            filepath: Path to corrupted JPEG file
            output_path: Path for repaired output
            mode: Repair aggressiveness mode
            
        Returns:
            Tuple of (RepairResult, message)
        """
        report = self.diagnose(filepath)
        
        if not report.is_corrupted:
            return RepairResult.NOT_CORRUPTED, "File is not corrupted"
        
        if not report.repairable:
            return RepairResult.FAILED, "File is not repairable"
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Mode: SAFE - Only try PIL recovery
            if mode == RepairMode.SAFE:
                try:
                    img = Image.open(io.BytesIO(data))
                    img.load()
                    img.save(output_path, 'JPEG', quality=95, optimize=True)
                    return RepairResult.SUCCESS, "Repaired using PIL recovery (safe mode)"
                except Exception as e:
                    return RepairResult.FAILED, f"Safe mode PIL recovery failed: {str(e)}"
            
            # Mode: BALANCED or AGGRESSIVE - Try PIL first
            try:
                img = Image.open(io.BytesIO(data))
                img.load()
                img.save(output_path, 'JPEG', quality=95, optimize=True)
                return RepairResult.SUCCESS, "Repaired using PIL recovery"
            except Exception:
                pass
            
            # Manual repair attempts (BALANCED and AGGRESSIVE modes)
            if report.corruption_type == CorruptionType.HEADER:
                # Add SOI marker
                fixed_data = self.SOI_MARKER + data
                with open(output_path, 'wb') as f:
                    f.write(fixed_data)
                return RepairResult.PARTIAL, "Added SOI marker, verify manually"
            
            elif report.corruption_type == CorruptionType.TRUNCATED:
                # Add EOI marker
                fixed_data = data + self.EOI_MARKER
                with open(output_path, 'wb') as f:
                    f.write(fixed_data)
                return RepairResult.PARTIAL, "Added EOI marker, verify manually"
            
            elif mode == RepairMode.AGGRESSIVE:
                # Aggressive mode: Try to salvage partial data more aggressively
                # Look for multiple segments and attempt reconstruction
                segments = []
                pos = 0
                while pos < len(data) - 1:
                    # Find next SOI marker
                    soi_pos = data.find(self.SOI_MARKER, pos)
                    if soi_pos == -1:
                        break
                    
                    # Find corresponding EOI marker
                    eoi_pos = data.find(self.EOI_MARKER, soi_pos + 2)
                    if eoi_pos > soi_pos:
                        segments.append(data[soi_pos:eoi_pos+2])
                        pos = eoi_pos + 2
                    else:
                        pos = soi_pos + 2
                
                if segments:
                    # Try to save the largest valid segment
                    largest = max(segments, key=len)
                    try:
                        img = Image.open(io.BytesIO(largest))
                        img.load()
                        img.save(output_path, 'JPEG', quality=95, optimize=True)
                        return RepairResult.PARTIAL, f"Recovered largest segment ({len(largest)} bytes) in aggressive mode"
                    except Exception as e:
                        # Save raw segment as fallback
                        with open(output_path, 'wb') as f:
                            f.write(largest)
                        return RepairResult.PARTIAL, f"Extracted largest segment ({len(largest)} bytes), may need manual review"
                
                # Try to salvage partial data up to last marker
                eoi_pos = data.rfind(self.EOI_MARKER)
                if eoi_pos > 0:
                    fixed_data = data[:eoi_pos+2]
                    with open(output_path, 'wb') as f:
                        f.write(fixed_data)
                    return RepairResult.PARTIAL, "Extracted data up to last valid EOI (aggressive mode)"
                
                return RepairResult.FAILED, "No recoverable data found in aggressive mode"
            
            else:
                # BALANCED mode - standard salvage
                eoi_pos = data.rfind(self.EOI_MARKER)
                if eoi_pos > 0:
                    fixed_data = data[:eoi_pos+2]
                    with open(output_path, 'wb') as f:
                        f.write(fixed_data)
                    return RepairResult.PARTIAL, "Extracted data up to last valid EOI"
                
                return RepairResult.FAILED, f"Cannot repair {report.corruption_type.value} corruption"
                
        except Exception as e:
            return RepairResult.FAILED, f"Repair failed: {str(e)}"


class ImageRepairer:
    """Main image repair class."""
    
    def __init__(self):
        self.png_repairer = PNGRepairer()
        self.jpeg_repairer = JPEGRepairer()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def diagnose_file(self, filepath: str) -> DiagnosticReport:
        """Diagnose any image file."""
        try:
            # Detect file type
            with open(filepath, 'rb') as f:
                header = f.read(8)
            
            if header.startswith(b'\x89PNG'):
                return self.png_repairer.diagnose(filepath)
            elif header.startswith(b'\xFF\xD8'):
                return self.jpeg_repairer.diagnose(filepath)
            else:
                report = DiagnosticReport(filepath)
                report.file_type = "Unknown"
                report.is_corrupted = True
                report.corruption_type = CorruptionType.UNKNOWN
                report.add_note("Unknown or unsupported file format")
                report.repairable = False
                return report
                
        except Exception as e:
            report = DiagnosticReport(filepath)
            report.is_corrupted = True
            report.corruption_type = CorruptionType.UNKNOWN
            report.add_note(f"Error reading file: {str(e)}")
            report.repairable = False
            return report
    
    def repair_file(self, filepath: str, output_path: str = None, mode: RepairMode = RepairMode.BALANCED) -> Tuple[RepairResult, str]:
        """
        Repair any image file.
        
        Args:
            filepath: Path to corrupted image file
            output_path: Optional output path (auto-generated if None)
            mode: Repair aggressiveness mode
            
        Returns:
            Tuple of (RepairResult, message)
        """
        if output_path is None:
            base, ext = os.path.splitext(filepath)
            output_path = f"{base}_repaired{ext}"
        
        report = self.diagnose_file(filepath)
        
        if report.file_type == "PNG":
            return self.png_repairer.repair(filepath, output_path, mode)
        elif report.file_type == "JPEG":
            return self.jpeg_repairer.repair(filepath, output_path, mode)
        else:
            return RepairResult.FAILED, "Unsupported file format"
    
    def batch_repair(
        self,
        files: List[str],
        output_dir: str,
        progress_callback: Optional[Callable] = None,
        mode: RepairMode = RepairMode.BALANCED
    ) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Repair multiple files.
        
        Args:
            files: List of file paths to repair
            output_dir: Output directory for repaired files
            progress_callback: Optional callback(current, total, filename)
            mode: Repair aggressiveness mode
        
        Returns:
            Tuple of (successful_files, failed_files_with_reasons)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        successes = []
        failures = []
        
        for i, filepath in enumerate(files):
            if progress_callback:
                progress_callback(i + 1, len(files), os.path.basename(filepath))
            
            try:
                filename = os.path.basename(filepath)
                output_path = os.path.join(output_dir, filename)
                
                result, message = self.repair_file(filepath, output_path, mode)
                
                if result in (RepairResult.SUCCESS, RepairResult.PARTIAL):
                    successes.append(output_path)
                    self.logger.info(f"Repaired: {filename} - {message}")
                else:
                    failures.append((filepath, message))
                    self.logger.warning(f"Failed: {filename} - {message}")
                    
            except Exception as e:
                failures.append((filepath, str(e)))
                self.logger.error(f"Error repairing {filepath}: {e}")
        
        return successes, failures
