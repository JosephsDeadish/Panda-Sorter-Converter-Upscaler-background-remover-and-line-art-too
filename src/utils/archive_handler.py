"""
Archive Handler Module
Handles extraction and compression of various archive formats (ZIP, 7Z, RAR, TAR)
Author: Dead On The Inside / JosephsDeadish
"""

import zipfile
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Set, Callable
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import optional archive libraries
try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False
    logger.debug("py7zr not available. 7z support disabled.")

try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False
    logger.debug("rarfile not available. RAR support disabled.")

try:
    import tarfile
    HAS_TAR = True
except ImportError:
    HAS_TAR = False
    logger.debug("tarfile not available. TAR support disabled.")


class ArchiveFormat(Enum):
    """Supported archive formats"""
    ZIP = "zip"
    SEVEN_ZIP = "7z"
    RAR = "rar"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"
    TAR_XZ = "tar.xz"
    UNKNOWN = "unknown"


class ArchiveHandler:
    """
    Handles extraction and compression of various archive formats.
    Supports: ZIP, 7Z, RAR, TAR (gz/bz2/xz)
    """
    
    # Archive file extensions
    ARCHIVE_EXTENSIONS = {
        '.zip': ArchiveFormat.ZIP,
        '.7z': ArchiveFormat.SEVEN_ZIP,
        '.rar': ArchiveFormat.RAR,
        '.tar': ArchiveFormat.TAR,
        '.tar.gz': ArchiveFormat.TAR_GZ,
        '.tgz': ArchiveFormat.TAR_GZ,
        '.tar.bz2': ArchiveFormat.TAR_BZ2,
        '.tbz2': ArchiveFormat.TAR_BZ2,
        '.tar.xz': ArchiveFormat.TAR_XZ,
        '.txz': ArchiveFormat.TAR_XZ,
    }
    
    def __init__(self):
        self.temp_dirs = []  # Track temp directories for cleanup
    
    def is_archive(self, file_path: Path) -> bool:
        """
        Check if a file is a supported archive format.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file is a supported archive
        """
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check for compound extensions first (.tar.gz, .tar.bz2, etc.)
        file_str = str(file_path).lower()
        for ext in ['.tar.gz', '.tar.bz2', '.tar.xz']:
            if file_str.endswith(ext):
                return True
        
        # Check single extensions
        ext = file_path.suffix.lower()
        return ext in self.ARCHIVE_EXTENSIONS
    
    def get_archive_format(self, file_path: Path) -> ArchiveFormat:
        """
        Detect archive format from file extension.
        
        Args:
            file_path: Path to archive file
            
        Returns:
            ArchiveFormat enum value
        """
        file_str = str(file_path).lower()
        
        # Check compound extensions first
        for ext in ['.tar.gz', '.tar.bz2', '.tar.xz']:
            if file_str.endswith(ext):
                return self.ARCHIVE_EXTENSIONS[ext]
        
        # Check single extension
        ext = file_path.suffix.lower()
        return self.ARCHIVE_EXTENSIONS.get(ext, ArchiveFormat.UNKNOWN)
    
    def list_archive_contents(self, archive_path: Path) -> List[str]:
        """
        List all files in an archive.
        
        Args:
            archive_path: Path to archive file
            
        Returns:
            List of file paths inside archive
        """
        format_type = self.get_archive_format(archive_path)
        
        try:
            if format_type == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    return zf.namelist()
            
            elif format_type == ArchiveFormat.SEVEN_ZIP:
                if not HAS_7Z:
                    logger.error("7z support not available (py7zr not installed)")
                    return []
                with py7zr.SevenZipFile(archive_path, 'r') as archive:
                    return archive.getnames()
            
            elif format_type == ArchiveFormat.RAR:
                if not HAS_RAR:
                    logger.error("RAR support not available (rarfile not installed)")
                    return []
                with rarfile.RarFile(archive_path, 'r') as rf:
                    return rf.namelist()
            
            elif format_type in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ, 
                                ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
                if not HAS_TAR:
                    logger.error("TAR support not available")
                    return []
                with tarfile.open(archive_path, 'r:*') as tf:
                    return tf.getnames()
            
            else:
                logger.error(f"Unsupported archive format: {format_type}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing archive contents: {e}")
            return []
    
    def extract_archive(self, archive_path: Path, 
                       extract_to: Optional[Path] = None,
                       progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Optional[Path]:
        """
        Extract archive to a directory.
        
        Args:
            archive_path: Path to archive file
            extract_to: Target directory (creates temp dir if None)
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Path to extraction directory or None on failure
        """
        if not archive_path.exists():
            logger.error(f"Archive not found: {archive_path}")
            return None
        
        format_type = self.get_archive_format(archive_path)
        
        # Create extraction directory
        if extract_to is None:
            extract_to = Path(tempfile.mkdtemp(prefix="ps2_archive_"))
            self.temp_dirs.append(extract_to)
            logger.info(f"Created temp extraction dir: {extract_to}")
        else:
            extract_to.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Extracting {archive_path.name} ({format_type.value}) to {extract_to}")
            
            if format_type == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    members = zf.namelist()
                    total = len(members)
                    for i, member in enumerate(members):
                        if progress_callback:
                            progress_callback(i + 1, total, member)
                        zf.extract(member, extract_to)
                    logger.info(f"Extracted {total} files from ZIP")
            
            elif format_type == ArchiveFormat.SEVEN_ZIP:
                if not HAS_7Z:
                    logger.error("7z support not available (install py7zr)")
                    return None
                with py7zr.SevenZipFile(archive_path, 'r') as archive:
                    members = archive.getnames()
                    total = len(members)
                    if progress_callback:
                        progress_callback(0, total, "Extracting 7z archive...")
                    archive.extractall(path=extract_to)
                    if progress_callback:
                        progress_callback(total, total, "Complete")
                    logger.info(f"Extracted {total} files from 7Z")
            
            elif format_type == ArchiveFormat.RAR:
                if not HAS_RAR:
                    logger.error("RAR support not available (install rarfile)")
                    return None
                with rarfile.RarFile(archive_path, 'r') as rf:
                    members = rf.namelist()
                    total = len(members)
                    for i, member in enumerate(members):
                        if progress_callback:
                            progress_callback(i + 1, total, member)
                        rf.extract(member, extract_to)
                    logger.info(f"Extracted {total} files from RAR")
            
            elif format_type in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ, 
                                ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
                if not HAS_TAR:
                    logger.error("TAR support not available")
                    return None
                with tarfile.open(archive_path, 'r:*') as tf:
                    members = tf.getmembers()
                    total = len(members)
                    for i, member in enumerate(members):
                        if progress_callback:
                            progress_callback(i + 1, total, member.name)
                        tf.extract(member, extract_to)
                    logger.info(f"Extracted {total} files from TAR")
            
            else:
                logger.error(f"Unsupported archive format: {format_type}")
                return None
            
            return extract_to
            
        except Exception as e:
            logger.error(f"Error extracting archive: {e}")
            return None
    
    def create_archive(self, source_path: Path, archive_path: Path,
                      format_type: Optional[ArchiveFormat] = None,
                      progress_callback: Optional[Callable[[int, int, str], None]] = None) -> bool:
        """
        Create an archive from a directory or files.
        
        Args:
            source_path: Directory or file to archive
            archive_path: Target archive file path
            format_type: Archive format (auto-detect from extension if None)
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            True if successful, False otherwise
        """
        if not source_path.exists():
            logger.error(f"Source path not found: {source_path}")
            return False
        
        # Auto-detect format from extension
        if format_type is None:
            format_type = self.get_archive_format(archive_path)
        
        try:
            # Collect files to archive
            if source_path.is_file():
                files_to_add = [source_path]
            else:
                files_to_add = list(source_path.rglob('*'))
                files_to_add = [f for f in files_to_add if f.is_file()]
            
            total = len(files_to_add)
            logger.info(f"Creating {format_type.value} archive with {total} files: {archive_path}")
            
            if format_type == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for i, file_path in enumerate(files_to_add):
                        arcname = file_path.relative_to(source_path.parent if source_path.is_file() else source_path)
                        if progress_callback:
                            progress_callback(i + 1, total, str(arcname))
                        zf.write(file_path, arcname)
                logger.info(f"Created ZIP archive with {total} files")
            
            elif format_type == ArchiveFormat.SEVEN_ZIP:
                if not HAS_7Z:
                    logger.error("7z support not available (install py7zr)")
                    return False
                with py7zr.SevenZipFile(archive_path, 'w') as archive:
                    if source_path.is_dir():
                        if progress_callback:
                            progress_callback(0, total, "Creating 7z archive...")
                        archive.writeall(source_path, arcname=source_path.name)
                        if progress_callback:
                            progress_callback(total, total, "Complete")
                    else:
                        archive.write(source_path, source_path.name)
                logger.info(f"Created 7Z archive with {total} files")
            
            elif format_type in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ, 
                                ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
                if not HAS_TAR:
                    logger.error("TAR support not available")
                    return False
                
                # Determine compression mode
                mode_map = {
                    ArchiveFormat.TAR: 'w',
                    ArchiveFormat.TAR_GZ: 'w:gz',
                    ArchiveFormat.TAR_BZ2: 'w:bz2',
                    ArchiveFormat.TAR_XZ: 'w:xz',
                }
                mode = mode_map.get(format_type, 'w')
                
                with tarfile.open(archive_path, mode) as tf:
                    for i, file_path in enumerate(files_to_add):
                        arcname = file_path.relative_to(source_path.parent if source_path.is_file() else source_path)
                        if progress_callback:
                            progress_callback(i + 1, total, str(arcname))
                        tf.add(file_path, arcname=arcname)
                logger.info(f"Created TAR archive with {total} files")
            
            else:
                logger.error(f"Unsupported archive format for creation: {format_type}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating archive: {e}")
            return False
    
    def cleanup_temp_dirs(self):
        """Clean up all temporary extraction directories."""
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp dir: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temp dir {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup_temp_dirs()
