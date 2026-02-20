"""
Feature modules for Game Texture Sorter
Includes statistics tracking, texture analysis, search/filter, profiles, batch operations, LOD replacement, backups,
hotkeys, sound system, and achievements
Author: Dead On The Inside / JosephsDeadish
"""

import logging
_log = logging.getLogger(__name__)

__all__ = []

from .statistics import StatisticsTracker
__all__.append('StatisticsTracker')

from .texture_analysis import TextureAnalyzer
__all__.append('TextureAnalyzer')

from .search_filter import SearchFilter, FilterCriteria, SearchPreset
__all__.extend(['SearchFilter', 'FilterCriteria', 'SearchPreset'])

from .profile_manager import ProfileManager, OrganizationProfile, GameTemplate
__all__.extend(['ProfileManager', 'OrganizationProfile', 'GameTemplate'])

from .batch_operations import BatchQueue, Operation, OperationStatus, OperationPriority, BatchOperationHelper
__all__.extend(['BatchQueue', 'Operation', 'OperationStatus', 'OperationPriority', 'BatchOperationHelper'])

from .lod_replacement import LODReplacer, LODTexture, LODGroup
LODReplacement = LODReplacer  # backward-compat alias
__all__.extend(['LODReplacer', 'LODReplacement', 'LODTexture', 'LODGroup'])

from .backup_system import BackupManager, BackupMetadata, RestorePoint
__all__.extend(['BackupManager', 'BackupMetadata', 'RestorePoint'])

# pynput is an optional runtime dep; guard so the package is importable without it
try:
    from .hotkey_manager import HotkeyManager, Hotkey
    __all__.extend(['HotkeyManager', 'Hotkey'])
except ImportError as _e:
    _log.warning(f"HotkeyManager unavailable (pynput missing?): {_e}")
    HotkeyManager = None  # type: ignore[assignment,misc]
    Hotkey = None         # type: ignore[assignment,misc]

# pygame / sounddevice are optional audio deps
try:
    from .sound_manager import SoundManager, SoundEvent, SoundPack
    __all__.extend(['SoundManager', 'SoundEvent', 'SoundPack'])
except ImportError as _e:
    _log.warning(f"SoundManager unavailable (audio library missing?): {_e}")
    SoundManager = None  # type: ignore[assignment,misc]
    SoundEvent = None    # type: ignore[assignment,misc]
    SoundPack = None     # type: ignore[assignment,misc]

from .achievements import AchievementSystem, Achievement, AchievementTier
__all__.extend(['AchievementSystem', 'Achievement', 'AchievementTier'])

from .panda_character import PandaCharacter, PandaFacing, PandaGender, PandaMood
__all__.extend(['PandaCharacter', 'PandaFacing', 'PandaGender', 'PandaMood'])

from .panda_stats import PandaStats
__all__.append('PandaStats')

from .panda_widgets import WidgetCollection, WidgetType, WidgetRarity, PandaWidget, ItemPhysics, WidgetStats
__all__.extend(['WidgetCollection', 'WidgetType', 'WidgetRarity', 'PandaWidget', 'ItemPhysics', 'WidgetStats'])

from .shop_system import ShopSystem, ShopItem, ShopCategory
__all__.extend(['ShopSystem', 'ShopItem', 'ShopCategory'])

from .currency_system import CurrencySystem, MoneyTransaction
__all__.extend(['CurrencySystem', 'MoneyTransaction'])

from .minigame_system import (MiniGameManager, MiniGame, PandaClickGame,
                               PandaMemoryGame, PandaReflexGame,
                               GameDifficulty, GameResult)
__all__.extend(['MiniGameManager', 'MiniGame', 'PandaClickGame',
                'PandaMemoryGame', 'PandaReflexGame', 'GameDifficulty', 'GameResult'])

from .level_system import LevelSystem, UserLevelSystem, PandaLevelSystem, Level, LevelReward
__all__.extend(['LevelSystem', 'UserLevelSystem', 'PandaLevelSystem', 'Level', 'LevelReward'])

from .game_identifier import GameIdentifier, GameInfo
__all__.extend(['GameIdentifier', 'GameInfo'])

from .auto_backup import AutoBackupSystem, BackupConfig
__all__.extend(['AutoBackupSystem', 'BackupConfig'])

from .translation_manager import TranslationManager, Language
__all__.extend(['TranslationManager', 'Language'])

from .tutorial_system import (TutorialManager, TutorialStep, TooltipMode,
                               TooltipVerbosityManager)
__all__.extend(['TutorialManager', 'TutorialStep', 'TooltipMode', 'TooltipVerbosityManager'])

from .panda_mood_system import PandaMoodSystem
__all__.append('PandaMoodSystem')

from .panda_closet import (CustomizationCategory, ClothingSubCategory,
                            AccessorySubCategory, ItemRarity, CustomizationItem)
__all__.extend(['CustomizationCategory', 'ClothingSubCategory',
                'AccessorySubCategory', 'ItemRarity', 'CustomizationItem'])

from .quest_system import QuestSystem, Quest, QuestType, QuestStatus
__all__.extend(['QuestSystem', 'Quest', 'QuestType', 'QuestStatus'])

# ---------------------------------------------------------------------------
# Extended game / dungeon / panda-interaction feature modules
# ---------------------------------------------------------------------------

from .unlockables_system import (
    UnlockablesSystem, UnlockableCursor, PandaOutfit, UnlockableTheme,
    WaveAnimation, TooltipCollection, UnlockCondition, UnlockConditionType,
)
__all__.extend([
    'UnlockablesSystem', 'UnlockableCursor', 'PandaOutfit', 'UnlockableTheme',
    'WaveAnimation', 'TooltipCollection', 'UnlockCondition', 'UnlockConditionType',
])

from .skill_tree import SkillNode, SkillTree
__all__.extend(['SkillNode', 'SkillTree'])

from .travel_system import (
    Location, LocationType, DungeonDifficulty, DungeonRoom,
    ProceduralDungeon, TravelScene, TravelSceneType,
)
__all__.extend([
    'Location', 'LocationType', 'DungeonDifficulty', 'DungeonRoom',
    'ProceduralDungeon', 'TravelScene', 'TravelSceneType',
])

from .tutorial_categories import TutorialCategory, CategorizedTutorialStep
__all__.extend(['TutorialCategory', 'CategorizedTutorialStep'])

from .widget_detector import WidgetDetector
__all__.append('WidgetDetector')

from .panda_clothing_3d import (
    AccessoryType, Bone, BoneType, ClothingMesh, ClothingSystem, ClothingType, LODLevel,
)
__all__.extend(['AccessoryType', 'Bone', 'BoneType', 'ClothingMesh',
                'ClothingSystem', 'ClothingType', 'LODLevel'])

from .panda_interaction_behavior import InteractionBehavior, PandaInteractionBehavior
__all__.extend(['InteractionBehavior', 'PandaInteractionBehavior'])

from .combat_system import AdventureLevel, CombatStats, DamageType
CombatSystem = AdventureLevel  # backward-compat alias (AdventureLevel IS the combat system)
__all__.extend(['AdventureLevel', 'CombatSystem', 'CombatStats', 'DamageType'])

from .damage_system import (
    DamageCategory, DamageStage, DamageTracker, LimbDamage, LimbType, ProjectileStuck,
)
__all__.extend([
    'DamageCategory', 'DamageStage', 'DamageTracker',
    'LimbDamage', 'LimbType', 'ProjectileStuck',
])

from .dungeon_generator import BSPNode, Corridor, DungeonFloor, DungeonGenerator, Room
__all__.extend(['BSPNode', 'Corridor', 'DungeonFloor', 'DungeonGenerator', 'Room'])

from .enemy_manager import EnemyManager
__all__.append('EnemyManager')

from .enemy_system import Enemy, EnemyBehavior, EnemyCollection, EnemyTemplate, EnemyType
__all__.extend(['Enemy', 'EnemyBehavior', 'EnemyCollection', 'EnemyTemplate', 'EnemyType'])

from .environment_monitor import EnvironmentMonitor, EnvironmentalEvent
__all__.extend(['EnvironmentMonitor', 'EnvironmentalEvent'])

from .integrated_dungeon import IntegratedDungeon, LootItem, SpawnedEnemy
__all__.extend(['IntegratedDungeon', 'LootItem', 'SpawnedEnemy'])

from .projectile_system import Projectile, ProjectileManager, ProjectilePhysics, ProjectileType
__all__.extend(['Projectile', 'ProjectileManager', 'ProjectilePhysics', 'ProjectileType'])

from .weapon_system import Weapon, WeaponCollection, WeaponRarity, WeaponStats, WeaponType
__all__.extend(['Weapon', 'WeaponCollection', 'WeaponRarity', 'WeaponStats', 'WeaponType'])

from .preview_viewer import PreviewViewer
__all__.append('PreviewViewer')

# PreviewViewerWidget is Qt-specific; guard so headless imports still work
try:
    from .preview_viewer_qt import PreviewViewerWidget
    __all__.append('PreviewViewerWidget')
except ImportError as _e:
    _log.debug(f"PreviewViewerWidget unavailable (PyQt6 missing?): {_e}")
    PreviewViewerWidget = None  # type: ignore[assignment,misc]
