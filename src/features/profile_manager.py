"""
Profile Management System
Save, load, and manage organization profiles and presets
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class OrganizationProfile:
    """Represents an organization profile/preset."""
    name: str
    description: str = ""
    game_name: str = ""
    
    # Game identification (NEW)
    game_serial: str = ""  # PS2 serial (SLUS-xxxxx, SCUS-xxxxx, etc.)
    game_crc: str = ""  # PCSX2 game CRC hash
    game_region: str = ""  # NTSC-U, PAL, NTSC-J, etc.
    
    # Organization settings
    style: str = "by_category"  # by_category, by_type, by_size, flat, custom
    folder_structure: Dict[str, Any] = field(default_factory=dict)
    naming_pattern: str = "{category}/{name}"
    
    # Classification settings
    auto_classify: bool = True
    custom_categories: Dict[str, List[str]] = field(default_factory=dict)
    
    # Processing settings
    convert_formats: bool = False
    target_format: str = "png"
    create_thumbnails: bool = False
    thumbnail_size: tuple = (256, 256)
    
    # Metadata
    created_at: str = ""
    modified_at: str = ""
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = self.created_at


@dataclass
class GameTemplate:
    """Template for game-specific organization."""
    game_name: str
    patterns: List[str]  # Filename patterns to detect game
    profile: OrganizationProfile


class ProfileManager:
    """
    Profile management system for PS2 texture organization.
    
    Features:
    - Save/load organization presets
    - Export/import profiles as JSON
    - Game-specific templates
    - Auto-detect game from filename patterns
    - Custom profile creation
    - Profile versioning and validation
    - Thread-safe operations
    """
    
    # Built-in game templates
    GAME_TEMPLATES = {
        'god_of_war': GameTemplate(
            game_name='God of War',
            patterns=[
                r'kratos', r'gow\d*', r'god.*war', r'olympus',
                r'blade.*chaos', r'medusa', r'athena'
            ],
            profile=OrganizationProfile(
                name='God of War',
                description='Organization preset for God of War series',
                game_name='God of War',
                style='by_category',
                folder_structure={
                    'characters': ['kratos', 'gods', 'enemies', 'npcs'],
                    'weapons': ['blades', 'magic', 'items'],
                    'environments': ['olympus', 'underworld', 'greece'],
                    'ui': ['hud', 'menus', 'icons']
                },
                naming_pattern="{category}/{subcategory}/{name}",
                tags=['god_of_war', 'action', 'mythology']
            )
        ),
        'gta_sa': GameTemplate(
            game_name='Grand Theft Auto: San Andreas',
            patterns=[
                r'gta.*sa', r'san.*andreas', r'cj', r'grove.*street',
                r'los.*santos', r'vehicle\d+', r'ped\d+'
            ],
            profile=OrganizationProfile(
                name='GTA San Andreas',
                description='Organization preset for GTA San Andreas',
                game_name='Grand Theft Auto: San Andreas',
                style='by_type',
                folder_structure={
                    'vehicles': ['cars', 'bikes', 'planes', 'boats'],
                    'characters': ['player', 'gang', 'civilians', 'police'],
                    'world': ['buildings', 'roads', 'vegetation', 'props'],
                    'hud': ['radar', 'weapons', 'stats']
                },
                naming_pattern="{type}/{category}/{name}",
                tags=['gta', 'open_world', 'vehicles']
            )
        ),
        'final_fantasy': GameTemplate(
            game_name='Final Fantasy',
            patterns=[
                r'ff\d*', r'final.*fantasy', r'cloud', r'sephiroth',
                r'summon', r'materia', r'limit.*break'
            ],
            profile=OrganizationProfile(
                name='Final Fantasy',
                description='Organization preset for Final Fantasy series',
                game_name='Final Fantasy',
                style='by_category',
                folder_structure={
                    'characters': ['party', 'enemies', 'npcs', 'summons'],
                    'magic': ['spells', 'abilities', 'effects'],
                    'items': ['weapons', 'armor', 'accessories', 'consumables'],
                    'world': ['locations', 'dungeons', 'towns']
                },
                naming_pattern="{category}/{name}",
                tags=['final_fantasy', 'rpg', 'jrpg']
            )
        ),
        'metal_gear': GameTemplate(
            game_name='Metal Gear Solid',
            patterns=[
                r'mgs\d*', r'metal.*gear', r'snake', r'solid.*snake',
                r'stealth', r'codec', r'shadow.*moses'
            ],
            profile=OrganizationProfile(
                name='Metal Gear Solid',
                description='Organization preset for Metal Gear Solid series',
                game_name='Metal Gear Solid',
                style='by_category',
                folder_structure={
                    'characters': ['snake', 'bosses', 'soldiers', 'support'],
                    'equipment': ['weapons', 'items', 'gadgets'],
                    'environments': ['indoor', 'outdoor', 'vehicles'],
                    'ui': ['codec', 'radar', 'inventory']
                },
                naming_pattern="{category}/{subcategory}/{name}",
                tags=['metal_gear', 'stealth', 'tactical']
            )
        ),
        'silent_hill': GameTemplate(
            game_name='Silent Hill',
            patterns=[
                r'sh\d*', r'silent.*hill', r'pyramid.*head', r'alessa',
                r'fog', r'otherworld', r'radio'
            ],
            profile=OrganizationProfile(
                name='Silent Hill',
                description='Organization preset for Silent Hill series',
                game_name='Silent Hill',
                style='by_category',
                folder_structure={
                    'characters': ['protagonists', 'monsters', 'npcs'],
                    'environments': ['town', 'otherworld', 'indoors'],
                    'items': ['weapons', 'keys', 'health'],
                    'effects': ['fog', 'darkness', 'blood']
                },
                naming_pattern="{category}/{name}",
                tags=['silent_hill', 'horror', 'psychological']
            )
        )
    }
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory to store profiles (defaults to config/profiles)
        """
        self.profiles_dir = profiles_dir or Path("config/profiles")
        self.profiles: Dict[str, OrganizationProfile] = {}
        self._lock = Lock()
        
        logger.debug(f"ProfileManager initialized with profiles_dir={self.profiles_dir}")
        self._ensure_profiles_dir()
        self._load_all_profiles()
    
    def _ensure_profiles_dir(self):
        """Ensure profiles directory exists."""
        try:
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Profiles directory ready: {self.profiles_dir}")
        except Exception as e:
            logger.error(f"Error creating profiles directory: {e}", exc_info=True)
    
    def create_profile(
        self,
        name: str,
        description: str = "",
        game_name: str = "",
        **kwargs
    ) -> OrganizationProfile:
        """
        Create a new organization profile.
        
        Args:
            name: Profile name
            description: Profile description
            game_name: Associated game name
            **kwargs: Additional profile settings
            
        Returns:
            Created OrganizationProfile
        """
        try:
            profile = OrganizationProfile(
                name=name,
                description=description,
                game_name=game_name,
                **kwargs
            )
            
            with self._lock:
                self.profiles[name] = profile
            
            self.save_profile(name)
            
            logger.info(f"Created profile: {name}")
            return profile
                
        except Exception as e:
            logger.error(f"Error creating profile '{name}': {e}", exc_info=True)
            raise
    
    def save_profile(self, name: str) -> bool:
        """
        Save a profile to disk.
        
        Args:
            name: Profile name to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if name not in self.profiles:
                    logger.warning(f"Profile not found: {name}")
                    return False
                
                profile = self.profiles[name]
                profile.modified_at = datetime.now().isoformat()
                
                profile_file = self.profiles_dir / f"{self._sanitize_filename(name)}.json"
                data = asdict(profile)
                
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Saved profile: {name} to {profile_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving profile '{name}': {e}", exc_info=True)
            return False
    
    def load_profile(self, name: str) -> Optional[OrganizationProfile]:
        """
        Load a profile from disk.
        
        Args:
            name: Profile name to load
            
        Returns:
            OrganizationProfile if found, None otherwise
        """
        try:
            profile_file = self.profiles_dir / f"{self._sanitize_filename(name)}.json"
            
            if not profile_file.exists():
                logger.warning(f"Profile file not found: {profile_file}")
                return None
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = OrganizationProfile(**data)
            
            with self._lock:
                self.profiles[name] = profile
            
            logger.info(f"Loaded profile: {name}")
            return profile
            
        except Exception as e:
            logger.error(f"Error loading profile '{name}': {e}", exc_info=True)
            return None
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            with self._lock:
                if name not in self.profiles:
                    logger.warning(f"Profile not found: {name}")
                    return False
                
                del self.profiles[name]
            
            profile_file = self.profiles_dir / f"{self._sanitize_filename(name)}.json"
            if profile_file.exists():
                profile_file.unlink()
            
            logger.info(f"Deleted profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting profile '{name}': {e}", exc_info=True)
            return False
    
    def export_profile(self, name: str, export_path: Path) -> bool:
        """
        Export a profile to a JSON file.
        
        Args:
            name: Profile name to export
            export_path: Path to export to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if name not in self.profiles:
                    logger.warning(f"Profile not found: {name}")
                    return False
                
                profile = self.profiles[name]
                data = asdict(profile)
            
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported profile '{name}' to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting profile '{name}': {e}", exc_info=True)
            return False
    
    def import_profile(self, import_path: Path, name: Optional[str] = None) -> Optional[OrganizationProfile]:
        """
        Import a profile from a JSON file.
        
        Args:
            import_path: Path to import from
            name: Optional new name for the profile
            
        Returns:
            Imported OrganizationProfile if successful, None otherwise
        """
        try:
            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return None
            
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate profile data
            if not self._validate_profile_data(data):
                logger.error(f"Invalid profile data in {import_path}")
                return None
            
            profile = OrganizationProfile(**data)
            
            # Use provided name or original name
            if name:
                profile.name = name
            
            with self._lock:
                self.profiles[profile.name] = profile
            
            self.save_profile(profile.name)
            
            logger.info(f"Imported profile: {profile.name} from {import_path}")
            return profile
            
        except Exception as e:
            logger.error(f"Error importing profile from {import_path}: {e}", exc_info=True)
            return None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        Get list of all profiles.
        
        Returns:
            List of profile info dictionaries
        """
        with self._lock:
            return [
                {
                    'name': name,
                    'description': profile.description,
                    'game_name': profile.game_name,
                    'style': profile.style,
                    'created_at': profile.created_at,
                    'modified_at': profile.modified_at,
                    'tags': profile.tags
                }
                for name, profile in self.profiles.items()
            ]
    
    def get_profile(self, name: str) -> Optional[OrganizationProfile]:
        """
        Get a profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            OrganizationProfile if found, None otherwise
        """
        with self._lock:
            return self.profiles.get(name)
    
    def auto_detect_game(self, files: List[Path]) -> Optional[str]:
        """
        Auto-detect game from filename patterns.
        
        Args:
            files: List of texture files to analyze
            
        Returns:
            Game template key if detected, None otherwise
        """
        try:
            # Count pattern matches for each game
            match_counts: Dict[str, int] = {game: 0 for game in self.GAME_TEMPLATES}
            
            for file_path in files:
                filename = file_path.stem.lower()
                
                for game_key, template in self.GAME_TEMPLATES.items():
                    for pattern in template.patterns:
                        if re.search(pattern, filename, re.IGNORECASE):
                            match_counts[game_key] += 1
                            break
            
            # Find game with most matches
            if max(match_counts.values()) > 0:
                detected_game = max(match_counts, key=match_counts.get)
                confidence = match_counts[detected_game] / len(files) * 100
                
                logger.info(
                    f"Auto-detected game: {detected_game} "
                    f"({match_counts[detected_game]}/{len(files)} matches, "
                    f"{confidence:.1f}% confidence)"
                )
                return detected_game
            
            logger.debug("No game auto-detected from file patterns")
            return None
            
        except Exception as e:
            logger.error(f"Error auto-detecting game: {e}", exc_info=True)
            return None
    
    def identify_game_from_path(
        self,
        path: Path,
        gameindex_path: Optional[Path] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Identify game using serial/CRC detection from GameIdentifier.
        
        Args:
            path: Directory path to analyze
            gameindex_path: Optional path to GameIndex.yaml
            
        Returns:
            Dictionary with game info if identified, None otherwise
        """
        try:
            # Import GameIdentifier (lazy import to avoid circular dependencies)
            from .game_identifier import GameIdentifier, GameInfo
            
            # Create identifier
            identifier = GameIdentifier(gameindex_path=gameindex_path)
            
            # Identify game
            game_info = identifier.identify_game(path, scan_files=True)
            
            if game_info:
                return {
                    'serial': game_info.serial,
                    'crc': game_info.crc,
                    'title': game_info.title,
                    'region': game_info.region,
                    'confidence': game_info.confidence,
                    'source': game_info.source,
                    'texture_profile': game_info.texture_profile
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error identifying game from path: {e}", exc_info=True)
            return None
    
    def create_profile_from_game_info(
        self,
        game_info: Dict[str, Any],
        custom_name: Optional[str] = None
    ) -> Optional[OrganizationProfile]:
        """
        Create a profile from identified game information.
        
        Args:
            game_info: Game information dictionary from identify_game_from_path
            custom_name: Optional custom name for the profile
            
        Returns:
            Created OrganizationProfile if successful, None otherwise
        """
        try:
            name = custom_name or game_info.get('title', 'Unknown Game')
            
            # Create profile with game identification
            profile = OrganizationProfile(
                name=name,
                description=f"Auto-generated profile for {game_info.get('title', 'Unknown')}",
                game_name=game_info.get('title', ''),
                game_serial=game_info.get('serial', ''),
                game_crc=game_info.get('crc', ''),
                game_region=game_info.get('region', ''),
                style='by_category',
                auto_classify=True,
                tags=[game_info.get('region', '').lower(), 'auto_detected']
            )
            
            # Apply texture profile if available
            texture_profile = game_info.get('texture_profile', {})
            if texture_profile:
                # Set custom categories based on common categories
                common_categories = texture_profile.get('common_categories', [])
                if common_categories:
                    profile.custom_categories = {
                        cat: [] for cat in common_categories
                    }
            
            with self._lock:
                self.profiles[profile.name] = profile
            
            self.save_profile(profile.name)
            
            logger.info(
                f"Created profile from game info: {name} "
                f"(Serial: {profile.game_serial}, Region: {profile.game_region})"
            )
            return profile
            
        except Exception as e:
            logger.error(f"Error creating profile from game info: {e}", exc_info=True)
            return None
    
    def create_from_template(self, template_key: str, custom_name: Optional[str] = None) -> Optional[OrganizationProfile]:
        """
        Create a profile from a game template.
        
        Args:
            template_key: Key of the game template
            custom_name: Optional custom name for the profile
            
        Returns:
            Created OrganizationProfile if successful, None otherwise
        """
        try:
            if template_key not in self.GAME_TEMPLATES:
                logger.error(f"Template not found: {template_key}")
                return None
            
            template = self.GAME_TEMPLATES[template_key]
            profile = OrganizationProfile(**asdict(template.profile))
            
            if custom_name:
                profile.name = custom_name
            
            # Reset timestamps
            profile.created_at = datetime.now().isoformat()
            profile.modified_at = profile.created_at
            
            with self._lock:
                self.profiles[profile.name] = profile
            
            self.save_profile(profile.name)
            
            logger.info(f"Created profile from template '{template_key}': {profile.name}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating profile from template '{template_key}': {e}", exc_info=True)
            return None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of available game templates.
        
        Returns:
            List of template info dictionaries
        """
        return [
            {
                'key': key,
                'game_name': template.game_name,
                'description': template.profile.description,
                'style': template.profile.style,
                'tags': template.profile.tags
            }
            for key, template in self.GAME_TEMPLATES.items()
        ]
    
    def update_profile(self, name: str, **kwargs) -> bool:
        """
        Update profile settings.
        
        Args:
            name: Profile name
            **kwargs: Settings to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if name not in self.profiles:
                    logger.warning(f"Profile not found: {name}")
                    return False
                
                profile = self.profiles[name]
                
                # Update allowed fields
                for key, value in kwargs.items():
                    if hasattr(profile, key) and key not in ['name', 'created_at']:
                        setattr(profile, key, value)
                
                profile.modified_at = datetime.now().isoformat()
            
            # Save outside the lock to avoid deadlock
            self.save_profile(name)
            logger.info(f"Updated profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating profile '{name}': {e}", exc_info=True)
            return False
    
    def _load_all_profiles(self):
        """Load all profiles from profiles directory."""
        try:
            if not self.profiles_dir.exists():
                logger.debug("Profiles directory does not exist, no profiles to load")
                return
            
            loaded_count = 0
            for profile_file in self.profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if self._validate_profile_data(data):
                        profile = OrganizationProfile(**data)
                        with self._lock:
                            self.profiles[profile.name] = profile
                        loaded_count += 1
                    else:
                        logger.warning(f"Invalid profile data in {profile_file}")
                        
                except Exception as e:
                    logger.error(f"Error loading profile from {profile_file}: {e}")
            
            logger.info(f"Loaded {loaded_count} profiles from {self.profiles_dir}")
            
        except Exception as e:
            logger.error(f"Error loading profiles: {e}", exc_info=True)
    
    def _validate_profile_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate profile data structure.
        
        Args:
            data: Profile data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'style']
        return all(field in data for field in required_fields)
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize profile name for use as filename.
        
        Args:
            name: Profile name
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        return sanitized or 'unnamed_profile'
