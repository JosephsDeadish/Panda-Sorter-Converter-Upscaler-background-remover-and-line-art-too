"""
AI Learning System for Texture Organization
Tracks user corrections, manages learning profiles, and enables export/import
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
import hashlib
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from threading import RLock
import re

logger = logging.getLogger(__name__)

# Try to import cryptography for encryption support
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography package not available - profile encryption disabled")


@dataclass
class LearningEntry:
    """Single learned classification mapping."""
    filename_pattern: str
    suggested_folder: str
    user_choice: str
    confidence: float
    accepted: bool
    timestamp: str
    image_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningProfileMetadata:
    """Metadata for a learning profile."""
    version: str = "1.0"
    game: str = ""
    game_serial: str = ""
    author: str = ""
    created_at: str = ""
    updated_at: str = ""
    description: str = ""
    encrypted: bool = False


class AILearningSystem:
    """
    Manages AI learning profiles for texture organization.
    
    Features:
    - Track user corrections (Good/Bad feedback)
    - Save/load learning profiles
    - Export/import profiles with encryption support
    - Pattern-based suggestions
    - Game-specific learning
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the AI learning system.
        
        Args:
            config_dir: Directory for storing learning profiles
        """
        if config_dir is None:
            config_dir = Path.home() / ".ps2_texture_sorter" / "organizer_profiles"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_profile_path: Optional[Path] = None
        self.metadata = LearningProfileMetadata()
        self.learned_mappings: List[LearningEntry] = []
        self.custom_categories: Dict[str, List[str]] = {}
        
        self._lock = RLock()
        
        logger.info(f"AI Learning System initialized: {self.config_dir}")
    
    def create_new_profile(self, game_name: str, game_serial: str = "", 
                          author: str = "", description: str = "") -> None:
        """
        Create a new learning profile.
        
        Args:
            game_name: Name of the game
            game_serial: PS2 serial code (SLUS-xxxxx, etc.)
            author: Profile author name
            description: Profile description
        """
        with self._lock:
            now = datetime.utcnow().isoformat() + "Z"
            
            self.metadata = LearningProfileMetadata(
                version="1.0",
                game=game_name,
                game_serial=game_serial,
                author=author,
                created_at=now,
                updated_at=now,
                description=description,
                encrypted=False
            )
            
            self.learned_mappings = []
            self.custom_categories = {}
            
            logger.info(f"Created new profile: {game_name} ({game_serial})")
    
    def add_learning(self, filename: str, suggested_folder: str, 
                    user_choice: str, confidence: float, accepted: bool,
                    image_hash: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new learning entry from user feedback.
        
        Args:
            filename: Original texture filename
            suggested_folder: AI suggested folder path
            user_choice: User's actual choice
            confidence: AI confidence score (0-1)
            accepted: Whether user accepted the suggestion
            image_hash: Optional hash of the image for deduplication
            metadata: Additional metadata
        """
        with self._lock:
            # Extract pattern from filename
            pattern = self._extract_pattern(filename)
            
            entry = LearningEntry(
                filename_pattern=pattern,
                suggested_folder=suggested_folder,
                user_choice=user_choice,
                confidence=confidence,
                accepted=accepted,
                timestamp=datetime.utcnow().isoformat() + "Z",
                image_hash=image_hash,
                metadata=metadata or {}
            )
            
            self.learned_mappings.append(entry)
            self.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
            
            logger.debug(f"Added learning: {pattern} -> {user_choice} (accepted={accepted})")
    
    def _extract_pattern(self, filename: str) -> str:
        """
        Extract a pattern from a filename for matching similar files.
        
        Args:
            filename: Original filename
            
        Returns:
            Pattern string with wildcards
        """
        # Remove extension
        name_without_ext = Path(filename).stem
        
        # Replace numbers with wildcards
        # e.g., "kratos_head_01" -> "kratos_head_*"
        pattern = re.sub(r'\d+', '*', name_without_ext)
        
        # Remove consecutive wildcards
        pattern = re.sub(r'\*+', '*', pattern)
        
        # Add back wildcard extension
        return pattern + ".*"
    
    def get_suggestion(self, filename: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Get folder suggestions based on learned patterns.
        
        Args:
            filename: Texture filename to classify
            top_n: Number of suggestions to return
            
        Returns:
            List of (folder_path, confidence) tuples
        """
        with self._lock:
            if not self.learned_mappings:
                return []
            
            # Score each learned mapping
            scores = []
            for entry in self.learned_mappings:
                if not entry.accepted:
                    continue
                
                # Calculate similarity score
                score = self._pattern_similarity(filename, entry.filename_pattern)
                if score > 0:
                    scores.append((entry.user_choice, score * entry.confidence))
            
            # Aggregate scores by folder
            folder_scores: Dict[str, float] = {}
            for folder, score in scores:
                folder_scores[folder] = folder_scores.get(folder, 0) + score
            
            # Sort and return top N
            sorted_folders = sorted(folder_scores.items(), 
                                   key=lambda x: x[1], reverse=True)
            return sorted_folders[:top_n]
    
    def _pattern_similarity(self, filename: str, pattern: str) -> float:
        """
        Calculate similarity between filename and pattern.
        
        Args:
            filename: Actual filename
            pattern: Pattern with wildcards
            
        Returns:
            Similarity score (0-1)
        """
        # Convert pattern to regex
        regex_pattern = pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', r'.*')
        regex_pattern = f"^{regex_pattern}$"
        
        try:
            if re.match(regex_pattern, filename, re.IGNORECASE):
                # Exact match
                return 1.0
            
            # Partial match - count matching parts
            pattern_parts = pattern.lower().split('*')
            filename_lower = filename.lower()
            
            matches = sum(1 for part in pattern_parts if part and part in filename_lower)
            total_parts = len([p for p in pattern_parts if p])
            
            if total_parts > 0:
                return matches / total_parts
            
        except re.error:
            logger.warning(f"Invalid regex pattern: {regex_pattern}")
        
        return 0.0
    
    def add_custom_category(self, category_path: str, keywords: List[str]) -> None:
        """
        Add custom category with keywords.
        
        Args:
            category_path: Full category path (e.g., "character/kratos")
            keywords: List of keywords for this category
        """
        with self._lock:
            self.custom_categories[category_path] = keywords
            self.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
            logger.info(f"Added custom category: {category_path}")
    
    def save_profile(self, filepath: Optional[Path] = None) -> Path:
        """
        Save learning profile to JSON file.
        
        Args:
            filepath: Optional custom filepath. If None, auto-generates name.
            
        Returns:
            Path to saved profile file
        """
        with self._lock:
            if filepath is None:
                # Auto-generate filename
                safe_name = re.sub(r'[^\w\-]', '_', self.metadata.game)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"profile_{safe_name}_{timestamp}.json"
                filepath = self.config_dir / filename
            
            profile_data = {
                "metadata": asdict(self.metadata),
                "learned_mappings": [asdict(entry) for entry in self.learned_mappings],
                "custom_categories": self.custom_categories
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            self.current_profile_path = filepath
            logger.info(f"Saved learning profile: {filepath}")
            
            return filepath
    
    def load_profile(self, filepath: Path) -> None:
        """
        Load learning profile from JSON file.
        
        Args:
            filepath: Path to profile JSON file
        """
        with self._lock:
            if not filepath.exists():
                raise FileNotFoundError(f"Profile not found: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Load metadata
            metadata_dict = profile_data.get("metadata", {})
            self.metadata = LearningProfileMetadata(**metadata_dict)
            
            # Load learned mappings
            self.learned_mappings = []
            for entry_dict in profile_data.get("learned_mappings", []):
                entry = LearningEntry(**entry_dict)
                self.learned_mappings.append(entry)
            
            # Load custom categories
            self.custom_categories = profile_data.get("custom_categories", {})
            
            self.current_profile_path = filepath
            logger.info(f"Loaded learning profile: {filepath}")
            logger.info(f"  Game: {self.metadata.game} ({self.metadata.game_serial})")
            logger.info(f"  Entries: {len(self.learned_mappings)}")
    
    def export_profile(self, filepath: Path, password: Optional[str] = None) -> Path:
        """
        Export learning profile for sharing.
        
        Args:
            filepath: Export destination path
            password: Optional password for encryption
            
        Returns:
            Path to exported file
        """
        with self._lock:
            profile_data = {
                "metadata": asdict(self.metadata),
                "learned_mappings": [asdict(entry) for entry in self.learned_mappings],
                "custom_categories": self.custom_categories
            }
            
            if password and CRYPTO_AVAILABLE:
                # Encrypt the profile
                encrypted_data = self._encrypt_profile(profile_data, password)
                
                # Ensure .enc extension
                filepath = Path(str(filepath))
                if not str(filepath).endswith('.enc'):
                    # Add .enc to whatever extension exists
                    filepath = Path(str(filepath) + '.enc')
                
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(encrypted_data)
                
                logger.info(f"Exported encrypted profile: {filepath}")
            else:
                # Save as regular JSON
                if not str(filepath).endswith('.json'):
                    filepath = filepath.with_suffix('.json')
                
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Exported profile: {filepath}")
            
            return filepath
    
    def import_profile(self, filepath: Path, password: Optional[str] = None,
                      merge: bool = False) -> Dict[str, Any]:
        """
        Import learning profile from file.
        
        Args:
            filepath: Path to profile file (.json or .enc)
            password: Password for encrypted files
            merge: If True, merge with existing data. If False, replace.
            
        Returns:
            Import summary dict
        """
        with self._lock:
            if not filepath.exists():
                raise FileNotFoundError(f"Profile not found: {filepath}")
            
            # Determine if encrypted
            is_encrypted = str(filepath).endswith('.enc')
            
            if is_encrypted:
                if not password:
                    raise ValueError("Password required for encrypted profile")
                if not CRYPTO_AVAILABLE:
                    raise RuntimeError("Encryption support not available (install cryptography)")
                
                with open(filepath, 'rb') as f:
                    encrypted_data = f.read()
                
                profile_data = self._decrypt_profile(encrypted_data, password)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            
            # Validate format
            if not self._validate_profile_format(profile_data):
                raise ValueError("Invalid profile format")
            
            # Prepare import summary
            summary = {
                "source_file": str(filepath),
                "game": profile_data["metadata"].get("game", "Unknown"),
                "game_serial": profile_data["metadata"].get("game_serial", ""),
                "entries_imported": 0,
                "entries_skipped": 0,
                "categories_imported": 0
            }
            
            if merge:
                # Merge with existing data
                existing_patterns = {e.filename_pattern for e in self.learned_mappings}
                
                for entry_dict in profile_data.get("learned_mappings", []):
                    entry = LearningEntry(**entry_dict)
                    if entry.filename_pattern not in existing_patterns:
                        self.learned_mappings.append(entry)
                        summary["entries_imported"] += 1
                    else:
                        summary["entries_skipped"] += 1
                
                # Merge custom categories
                for cat_path, keywords in profile_data.get("custom_categories", {}).items():
                    if cat_path not in self.custom_categories:
                        self.custom_categories[cat_path] = keywords
                        summary["categories_imported"] += 1
                
                self.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
            else:
                # Replace all data
                metadata_dict = profile_data.get("metadata", {})
                self.metadata = LearningProfileMetadata(**metadata_dict)
                
                self.learned_mappings = []
                for entry_dict in profile_data.get("learned_mappings", []):
                    entry = LearningEntry(**entry_dict)
                    self.learned_mappings.append(entry)
                
                self.custom_categories = profile_data.get("custom_categories", {})
                
                summary["entries_imported"] = len(self.learned_mappings)
                summary["categories_imported"] = len(self.custom_categories)
            
            logger.info(f"Imported profile: {summary}")
            return summary
    
    def _encrypt_profile(self, profile_data: Dict[str, Any], password: str) -> bytes:
        """Encrypt profile data with password."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Encryption not available")
        
        # Generate random salt for this encryption
        import os
        salt = os.urandom(16)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Encrypt
        fernet = Fernet(key)
        json_data = json.dumps(profile_data).encode('utf-8')
        encrypted = fernet.encrypt(json_data)
        
        # Prepend salt to encrypted data (salt is not secret)
        return salt + encrypted
    
    def _decrypt_profile(self, encrypted_data: bytes, password: str) -> Dict[str, Any]:
        """Decrypt profile data with password."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Encryption not available")
        
        try:
            # Extract salt from beginning of data (first 16 bytes)
            salt = encrypted_data[:16]
            encrypted_content = encrypted_data[16:]
            
            # Derive key from password using extracted salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt
            fernet = Fernet(key)
            json_data = fernet.decrypt(encrypted_content)
            
            return json.loads(json_data.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def _validate_profile_format(self, profile_data: Dict[str, Any]) -> bool:
        """Validate that profile data has correct format."""
        required_keys = ["metadata", "learned_mappings"]
        
        if not all(key in profile_data for key in required_keys):
            return False
        
        # Validate metadata
        metadata = profile_data["metadata"]
        if not isinstance(metadata, dict):
            return False
        
        # Validate learned mappings
        mappings = profile_data["learned_mappings"]
        if not isinstance(mappings, list):
            return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the learning profile.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            total_entries = len(self.learned_mappings)
            accepted_entries = sum(1 for e in self.learned_mappings if e.accepted)
            rejected_entries = total_entries - accepted_entries
            
            # Folder usage stats
            folder_counts: Dict[str, int] = {}
            for entry in self.learned_mappings:
                if entry.accepted:
                    folder_counts[entry.user_choice] = folder_counts.get(entry.user_choice, 0) + 1
            
            return {
                "total_entries": total_entries,
                "accepted_entries": accepted_entries,
                "rejected_entries": rejected_entries,
                "custom_categories": len(self.custom_categories),
                "most_used_folders": sorted(folder_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:10],
                "game": self.metadata.game,
                "game_serial": self.metadata.game_serial,
                "created_at": self.metadata.created_at,
                "updated_at": self.metadata.updated_at
            }
    
    def clear_learning_history(self) -> None:
        """Clear all learned mappings (keeps metadata)."""
        with self._lock:
            self.learned_mappings = []
            self.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
            logger.info("Cleared learning history")
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available learning profiles.
        
        Returns:
            List of profile info dictionaries
        """
        profiles = []
        
        for filepath in self.config_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                metadata = profile_data.get("metadata", {})
                profiles.append({
                    "filepath": filepath,
                    "game": metadata.get("game", "Unknown"),
                    "game_serial": metadata.get("game_serial", ""),
                    "author": metadata.get("author", ""),
                    "entries": len(profile_data.get("learned_mappings", [])),
                    "created_at": metadata.get("created_at", ""),
                    "updated_at": metadata.get("updated_at", "")
                })
            except Exception as e:
                logger.warning(f"Could not read profile {filepath}: {e}")
        
        return sorted(profiles, key=lambda x: x.get("updated_at", ""), reverse=True)
