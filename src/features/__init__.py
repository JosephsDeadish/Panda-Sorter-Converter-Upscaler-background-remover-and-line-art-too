"""
Feature modules for PS2 Texture Sorter
Includes statistics tracking, texture analysis, search/filter, profiles, batch operations, LOD replacement, backups,
hotkeys, sound system, and achievements
Author: Dead On The Inside / JosephsDeadish
"""

# Use lazy imports with fallbacks to avoid cascading failures
# when optional dependencies (e.g., cv2, numpy) are missing

__all__ = []

try:
    from .statistics import StatisticsTracker
    __all__.append('StatisticsTracker')
except ImportError:
    pass

try:
    from .texture_analysis import TextureAnalyzer
    __all__.append('TextureAnalyzer')
except ImportError:
    pass

try:
    from .search_filter import SearchFilter, FilterCriteria, SearchPreset
    __all__.extend(['SearchFilter', 'FilterCriteria', 'SearchPreset'])
except ImportError:
    pass

try:
    from .profile_manager import ProfileManager, OrganizationProfile, GameTemplate
    __all__.extend(['ProfileManager', 'OrganizationProfile', 'GameTemplate'])
except ImportError:
    pass

try:
    from .batch_operations import BatchQueue, Operation, OperationStatus, OperationPriority, BatchOperationHelper
    __all__.extend(['BatchQueue', 'Operation', 'OperationStatus', 'OperationPriority', 'BatchOperationHelper'])
except ImportError:
    pass

try:
    from .lod_replacement import LODReplacer, LODTexture, LODGroup
    __all__.extend(['LODReplacer', 'LODTexture', 'LODGroup'])
except ImportError:
    pass

try:
    from .backup_system import BackupManager, BackupMetadata, RestorePoint
    __all__.extend(['BackupManager', 'BackupMetadata', 'RestorePoint'])
except ImportError:
    pass

try:
    from .hotkey_manager import HotkeyManager, Hotkey
    __all__.extend(['HotkeyManager', 'Hotkey'])
except ImportError:
    pass

try:
    from .sound_manager import SoundManager, SoundEvent, SoundPack
    __all__.extend(['SoundManager', 'SoundEvent', 'SoundPack'])
except ImportError:
    pass

try:
    from .achievements import AchievementSystem, Achievement, AchievementTier
    __all__.extend(['AchievementSystem', 'Achievement', 'AchievementTier'])
except ImportError:
    pass

try:
    from .panda_character import PandaMood
    __all__.extend(['PandaMood'])
except ImportError:
    pass
