"""
Backup and Restore System
Create and manage backups with restore points and compression
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from threading import Lock
import zipfile

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    name: str
    description: str
    created_at: str
    backup_path: Path
    source_path: Path
    file_count: int
    total_size: int
    compressed: bool
    compression_ratio: float = 1.0
    checksum: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class RestorePoint:
    """Represents a restore point."""
    point_id: str
    name: str
    description: str
    created_at: str
    backup_metadata: BackupMetadata
    state_snapshot: Dict[str, Any]


class BackupManager:
    """
    Backup and restore system for PS2 texture operations.
    
    Features:
    - Create restore points before operations
    - Automatic backups before risky operations
    - Restore to previous state
    - Backup metadata tracking
    - Compress backups to save space
    - Verify backup integrity
    - Thread-safe operations
    - Incremental backup support
    """
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups (defaults to 'backups')
        """
        self.backup_dir = backup_dir or Path("backups")
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.backups: Dict[str, BackupMetadata] = {}
        self.restore_points: Dict[str, RestorePoint] = {}
        self._lock = Lock()
        self._backup_counter = 0
        
        logger.debug(f"BackupManager initialized with backup_dir={self.backup_dir}")
        self._ensure_backup_dir()
        self._load_metadata()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Backup directory ready: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Error creating backup directory: {e}", exc_info=True)
    
    def create_backup(
        self,
        source_path: Path,
        name: Optional[str] = None,
        description: str = "",
        compress: bool = True,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a backup of files or directory.
        
        Args:
            source_path: Path to backup (file or directory)
            name: Optional backup name (auto-generated if None)
            description: Backup description
            compress: Whether to compress the backup
            tags: Optional tags for categorization
            
        Returns:
            Backup ID if successful, None otherwise
        """
        try:
            if not source_path.exists():
                logger.error(f"Source path does not exist: {source_path}")
                return None
            
            # Generate backup ID and name
            with self._lock:
                self._backup_counter += 1
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_id = f"backup_{self._backup_counter}_{timestamp}"
                
                if name is None:
                    name = f"Backup {timestamp}"
            
            logger.info(f"Creating backup: {name} (ID: {backup_id})")
            
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            file_count = 0
            total_size = 0
            
            if source_path.is_file():
                dest = backup_path / source_path.name
                shutil.copy2(source_path, dest)
                file_count = 1
                total_size = source_path.stat().st_size
            else:
                # Copy entire directory
                for item in source_path.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(source_path)
                        dest = backup_path / rel_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest)
                        file_count += 1
                        total_size += item.stat().st_size
            
            # Compress if requested
            compression_ratio = 1.0
            compressed_size = total_size
            
            if compress:
                compressed_path = self._compress_backup(backup_path, backup_id)
                if compressed_path:
                    # Remove uncompressed backup
                    shutil.rmtree(backup_path)
                    backup_path = compressed_path
                    compressed_size = compressed_path.stat().st_size
                    compression_ratio = compressed_size / total_size if total_size > 0 else 1.0
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                name=name,
                description=description,
                created_at=datetime.now().isoformat(),
                backup_path=backup_path,
                source_path=source_path,
                file_count=file_count,
                total_size=total_size,
                compressed=compress,
                compression_ratio=compression_ratio,
                checksum=checksum,
                tags=tags or []
            )
            
            with self._lock:
                self.backups[backup_id] = metadata
            
            self._save_metadata()
            
            logger.info(
                f"Backup created: {name} (ID: {backup_id})\n"
                f"  Files: {file_count}, Size: {total_size:,} bytes\n"
                f"  Compressed: {compress}, Ratio: {compression_ratio:.2%}"
            )
            
            return backup_id
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return None
    
    def restore_backup(
        self,
        backup_id: str,
        restore_path: Optional[Path] = None,
        verify_checksum: bool = True
    ) -> bool:
        """
        Restore a backup.
        
        Args:
            backup_id: ID of backup to restore
            restore_path: Optional custom restore location (uses original if None)
            verify_checksum: Whether to verify backup integrity before restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if backup_id not in self.backups:
                    logger.error(f"Backup not found: {backup_id}")
                    return False
                
                metadata = self.backups[backup_id]
            
            logger.info(f"Restoring backup: {metadata.name} (ID: {backup_id})")
            
            # Verify checksum if requested
            if verify_checksum and metadata.checksum:
                current_checksum = self._calculate_checksum(metadata.backup_path)
                if current_checksum != metadata.checksum:
                    logger.error(f"Backup checksum mismatch! Backup may be corrupted.")
                    return False
            
            # Determine restore location
            if restore_path is None:
                restore_path = metadata.source_path
            
            # Decompress if needed
            if metadata.compressed:
                temp_dir = self.backup_dir / f"temp_restore_{backup_id}"
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(metadata.backup_path, 'r') as zf:
                    zf.extractall(temp_dir)
                
                source_for_restore = temp_dir
            else:
                source_for_restore = metadata.backup_path
            
            # Restore files
            if restore_path.exists() and restore_path.is_dir():
                # Backup existing files before overwriting
                temp_backup_id = self.create_backup(
                    restore_path,
                    name=f"Pre-restore backup of {restore_path.name}",
                    description="Automatic backup before restore",
                    tags=['auto', 'pre-restore']
                )
                logger.info(f"Created pre-restore backup: {temp_backup_id}")
            
            # Copy files to restore location
            restore_path.parent.mkdir(parents=True, exist_ok=True)
            
            source_contents = list(source_for_restore.iterdir())
            if not source_contents:
                logger.error(f"Backup source directory is empty: {source_for_restore}")
                return False
            
            if len(source_contents) == 1:
                # Single file backup
                src_file = source_contents[0]
                shutil.copy2(src_file, restore_path)
            else:
                # Directory backup
                if restore_path.exists():
                    shutil.rmtree(restore_path)
                shutil.copytree(source_for_restore, restore_path)
            
            # Clean up temp directory if used
            if metadata.compressed:
                shutil.rmtree(temp_dir)
            
            logger.info(f"Backup restored successfully: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}", exc_info=True)
            return False
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        
        Args:
            backup_id: ID of backup to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if backup_id not in self.backups:
                    logger.warning(f"Backup not found: {backup_id}")
                    return False
                
                metadata = self.backups[backup_id]
                del self.backups[backup_id]
            
            # Delete backup files
            if metadata.backup_path.exists():
                if metadata.backup_path.is_file():
                    metadata.backup_path.unlink()
                else:
                    shutil.rmtree(metadata.backup_path)
            
            self._save_metadata()
            
            logger.info(f"Deleted backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}", exc_info=True)
            return False
    
    def create_restore_point(
        self,
        source_path: Path,
        name: str,
        description: str = "",
        state_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a restore point with state snapshot.
        
        Args:
            source_path: Path to backup
            name: Restore point name
            description: Description
            state_data: Optional additional state data to save
            
        Returns:
            Restore point ID if successful, None otherwise
        """
        try:
            # Create backup
            backup_id = self.create_backup(
                source_path,
                name=f"RestorePoint: {name}",
                description=description,
                compress=True,
                tags=['restore_point']
            )
            
            if not backup_id:
                return None
            
            # Create restore point
            point_id = f"rp_{int(datetime.now().timestamp())}"
            
            restore_point = RestorePoint(
                point_id=point_id,
                name=name,
                description=description,
                created_at=datetime.now().isoformat(),
                backup_metadata=self.backups[backup_id],
                state_snapshot=state_data or {}
            )
            
            with self._lock:
                self.restore_points[point_id] = restore_point
            
            self._save_metadata()
            
            logger.info(f"Created restore point: {name} (ID: {point_id})")
            return point_id
            
        except Exception as e:
            logger.error(f"Error creating restore point: {e}", exc_info=True)
            return None
    
    def restore_to_point(self, point_id: str, restore_path: Optional[Path] = None) -> bool:
        """
        Restore to a specific restore point.
        
        Args:
            point_id: Restore point ID
            restore_path: Optional custom restore location
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if point_id not in self.restore_points:
                    logger.error(f"Restore point not found: {point_id}")
                    return False
                
                restore_point = self.restore_points[point_id]
            
            logger.info(f"Restoring to point: {restore_point.name} (ID: {point_id})")
            
            # Restore the associated backup
            return self.restore_backup(
                restore_point.backup_metadata.backup_id,
                restore_path
            )
            
        except Exception as e:
            logger.error(f"Error restoring to point {point_id}: {e}", exc_info=True)
            return False
    
    def list_backups(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get list of all backups.
        
        Args:
            tags: Optional filter by tags
            
        Returns:
            List of backup info dictionaries
        """
        with self._lock:
            backups = self.backups.values()
            
            if tags:
                backups = [
                    b for b in backups
                    if any(tag in b.tags for tag in tags)
                ]
            
            return [
                {
                    'backup_id': b.backup_id,
                    'name': b.name,
                    'description': b.description,
                    'created_at': b.created_at,
                    'file_count': b.file_count,
                    'total_size': b.total_size,
                    'compressed': b.compressed,
                    'compression_ratio': b.compression_ratio,
                    'tags': b.tags
                }
                for b in sorted(backups, key=lambda x: x.created_at, reverse=True)
            ]
    
    def list_restore_points(self) -> List[Dict[str, Any]]:
        """
        Get list of all restore points.
        
        Returns:
            List of restore point info dictionaries
        """
        with self._lock:
            return [
                {
                    'point_id': rp.point_id,
                    'name': rp.name,
                    'description': rp.description,
                    'created_at': rp.created_at,
                    'backup_id': rp.backup_metadata.backup_id
                }
                for rp in sorted(
                    self.restore_points.values(),
                    key=lambda x: x.created_at,
                    reverse=True
                )
            ]
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a backup.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Backup info dictionary or None if not found
        """
        with self._lock:
            if backup_id not in self.backups:
                return None
            
            metadata = self.backups[backup_id]
            return {
                'backup_id': metadata.backup_id,
                'name': metadata.name,
                'description': metadata.description,
                'created_at': metadata.created_at,
                'source_path': str(metadata.source_path),
                'backup_path': str(metadata.backup_path),
                'file_count': metadata.file_count,
                'total_size': metadata.total_size,
                'compressed': metadata.compressed,
                'compression_ratio': metadata.compression_ratio,
                'checksum': metadata.checksum,
                'tags': metadata.tags
            }
    
    def cleanup_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> int:
        """
        Clean up old backups, keeping only recent ones.
        
        Args:
            keep_count: Minimum number of backups to keep
            keep_days: Keep backups from last N days
            
        Returns:
            Number of backups deleted
        """
        try:
            from datetime import timedelta
            
            with self._lock:
                # Sort backups by creation date
                sorted_backups = sorted(
                    self.backups.values(),
                    key=lambda b: b.created_at,
                    reverse=True
                )
                
                # Determine which backups to delete
                cutoff_date = datetime.now() - timedelta(days=keep_days)
                to_delete = []
                
                for i, backup in enumerate(sorted_backups):
                    # Keep recent backups by count
                    if i < keep_count:
                        continue
                    
                    # Keep backups within time window
                    created_at = datetime.fromisoformat(backup.created_at)
                    if created_at > cutoff_date:
                        continue
                    
                    # Don't delete restore points
                    if 'restore_point' in backup.tags:
                        continue
                    
                    to_delete.append(backup.backup_id)
            
            # Delete backups
            deleted_count = 0
            for backup_id in to_delete:
                if self.delete_backup(backup_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}", exc_info=True)
            return 0
    
    def _compress_backup(self, backup_path: Path, backup_id: str) -> Optional[Path]:
        """
        Compress a backup directory.
        
        Args:
            backup_path: Path to backup directory
            backup_id: Backup ID
            
        Returns:
            Path to compressed file or None on error
        """
        try:
            zip_path = self.backup_dir / f"{backup_id}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if backup_path.is_file():
                    zf.write(backup_path, backup_path.name)
                else:
                    for file in backup_path.rglob('*'):
                        if file.is_file():
                            arcname = file.relative_to(backup_path)
                            zf.write(file, arcname)
            
            logger.debug(f"Compressed backup to: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error compressing backup: {e}", exc_info=True)
            return None
    
    def _calculate_checksum(self, path: Path) -> str:
        """
        Calculate checksum for a file or directory.
        
        Args:
            path: Path to calculate checksum for
            
        Returns:
            SHA256 checksum as hex string
        """
        try:
            hasher = hashlib.sha256()
            
            if path.is_file():
                with open(path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        hasher.update(chunk)
            else:
                # For directories, hash all files in sorted order
                for file_path in sorted(path.rglob('*')):
                    if file_path.is_file():
                        with open(file_path, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b''):
                                hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def _save_metadata(self):
        """Save backup metadata to file."""
        try:
            data = {
                'backups': {
                    backup_id: {
                        **asdict(metadata),
                        'backup_path': str(metadata.backup_path),
                        'source_path': str(metadata.source_path)
                    }
                    for backup_id, metadata in self.backups.items()
                },
                'restore_points': {
                    point_id: {
                        'point_id': rp.point_id,
                        'name': rp.name,
                        'description': rp.description,
                        'created_at': rp.created_at,
                        'backup_id': rp.backup_metadata.backup_id,
                        'state_snapshot': rp.state_snapshot
                    }
                    for point_id, rp in self.restore_points.items()
                }
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved backup metadata to {self.metadata_file}")
            
        except Exception as e:
            logger.error(f"Error saving backup metadata: {e}", exc_info=True)
    
    def _load_metadata(self):
        """Load backup metadata from file."""
        try:
            if not self.metadata_file.exists():
                logger.debug("No backup metadata file found")
                return
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load backups
            for backup_id, backup_data in data.get('backups', {}).items():
                backup_data['backup_path'] = Path(backup_data['backup_path'])
                backup_data['source_path'] = Path(backup_data['source_path'])
                self.backups[backup_id] = BackupMetadata(**backup_data)
            
            # Load restore points
            for point_id, rp_data in data.get('restore_points', {}).items():
                backup_metadata = self.backups.get(rp_data['backup_id'])
                if backup_metadata:
                    restore_point = RestorePoint(
                        point_id=rp_data['point_id'],
                        name=rp_data['name'],
                        description=rp_data['description'],
                        created_at=rp_data['created_at'],
                        backup_metadata=backup_metadata,
                        state_snapshot=rp_data.get('state_snapshot', {})
                    )
                    self.restore_points[point_id] = restore_point
            
            logger.info(
                f"Loaded backup metadata: "
                f"{len(self.backups)} backups, "
                f"{len(self.restore_points)} restore points"
            )
            
        except Exception as e:
            logger.error(f"Error loading backup metadata: {e}", exc_info=True)
