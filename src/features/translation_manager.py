"""
Multi-Language Support System - Internationalization (i18n)
Supports multiple languages with easy translation management
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
from typing import Dict, Optional, List
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    JAPANESE = "ja"
    CHINESE = "zh"
    PORTUGUESE = "pt"


class TranslationManager:
    """Manages translations for multi-language support."""
    
    # Default English translations (fallback)
    DEFAULT_TRANSLATIONS = {
        # Application
        'app_title': 'PS2 Texture Sorter',
        'app_version': 'Version {version}',
        
        # Main menu
        'menu_file': 'File',
        'menu_edit': 'Edit',
        'menu_view': 'View',
        'menu_tools': 'Tools',
        'menu_help': 'Help',
        
        # File menu
        'file_open': 'Open',
        'file_save': 'Save',
        'file_export': 'Export',
        'file_exit': 'Exit',
        
        # Buttons
        'btn_start': 'Start',
        'btn_stop': 'Stop',
        'btn_pause': 'Pause',
        'btn_resume': 'Resume',
        'btn_cancel': 'Cancel',
        'btn_ok': 'OK',
        'btn_apply': 'Apply',
        'btn_close': 'Close',
        'btn_save': 'Save',
        'btn_load': 'Load',
        'btn_reset': 'Reset',
        
        # Processing
        'processing_title': 'Processing Textures',
        'processing_status': 'Processing {current} of {total} files',
        'processing_complete': 'Processing Complete!',
        'processing_cancelled': 'Processing Cancelled',
        'processing_error': 'Processing Error',
        
        # Settings
        'settings_title': 'Settings',
        'settings_general': 'General',
        'settings_ui': 'User Interface',
        'settings_performance': 'Performance',
        'settings_language': 'Language',
        'settings_hotkeys': 'Keyboard Shortcuts',
        
        # Panda
        'panda_title': 'Panda Companion',
        'panda_mood': 'Mood: {mood}',
        'panda_level': 'Level {level}',
        'panda_xp': '{current} / {max} XP',
        'panda_click_me': 'Click me! 🐼',
        'panda_happy': 'Happy',
        'panda_working': 'Working',
        'panda_celebrating': 'Celebrating',
        'panda_tired': 'Tired',
        'panda_playing': 'Playing',
        'panda_eating': 'Eating',
        
        # Mini-games
        'minigame_title': 'Mini-Games',
        'minigame_click': 'Panda Click Challenge',
        'minigame_memory': 'Panda Memory Match',
        'minigame_reflex': 'Panda Reflex Test',
        'minigame_score': 'Score: {score}',
        'minigame_time': 'Time: {time}s',
        'minigame_difficulty': 'Difficulty: {difficulty}',
        'minigame_start': 'Start Game',
        'minigame_game_over': 'Game Over!',
        'minigame_you_win': 'You Win!',
        
        # Panda Widgets
        'widgets_title': 'Panda Toys & Food',
        'widgets_toys': 'Toys',
        'widgets_food': 'Food',
        'widgets_accessories': 'Accessories',
        'widgets_use': 'Use',
        'widgets_unlocked': 'Unlocked',
        'widgets_locked': 'Locked',
        
        # Panda Closet
        'closet_title': 'Panda Closet',
        'closet_fur_style': 'Fur Style',
        'closet_fur_color': 'Fur Color',
        'closet_clothing': 'Clothing',
        'closet_hat': 'Hat',
        'closet_shoes': 'Shoes',
        'closet_accessories': 'Accessories',
        'closet_equip': 'Equip',
        'closet_unequip': 'Unequip',
        'closet_purchase': 'Purchase',
        'closet_cost': 'Cost: {cost}',
        
        # Common
        'common_yes': 'Yes',
        'common_no': 'No',
        'common_confirm': 'Confirm',
        'common_warning': 'Warning',
        'common_error': 'Error',
        'common_success': 'Success',
        'common_loading': 'Loading...',
        'common_saving': 'Saving...',
        
        # Tooltips
        'tooltip_start': 'Start processing textures',
        'tooltip_stop': 'Stop current operation',
        'tooltip_settings': 'Open settings',
        'tooltip_help': 'Show help',
        
        # Messages
        'msg_welcome': 'Welcome to PS2 Texture Sorter! 🐼',
        'msg_ready': 'Ready to sort textures',
        'msg_no_files': 'No files selected',
        'msg_operation_complete': 'Operation completed successfully',
        'msg_operation_failed': 'Operation failed: {error}',
    }
    
    def __init__(self, default_language: Language = Language.ENGLISH):
        """
        Initialize translation manager.
        
        Args:
            default_language: Default language to use
        """
        self.current_language = default_language
        self.translations: Dict[Language, Dict[str, str]] = {
            Language.ENGLISH: self.DEFAULT_TRANSLATIONS.copy()
        }
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translations from resource files."""
        # Try to load from resources directory
        resources_dir = Path(__file__).parent.parent / 'resources' / 'translations'
        
        if not resources_dir.exists():
            logger.warning(f"Translations directory not found: {resources_dir}")
            self._create_default_translations(resources_dir)
            return
        
        # Load translation files
        for lang in Language:
            if lang == Language.ENGLISH:
                continue  # Already have English as default
            
            lang_file = resources_dir / f"{lang.value}.json"
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                    logger.info(f"Loaded translations for {lang.value}")
                except Exception as e:
                    logger.error(f"Failed to load {lang.value} translations: {e}")
    
    def _create_default_translations(self, resources_dir: Path) -> None:
        """
        Create default translation files.
        
        Args:
            resources_dir: Directory to create translation files in
        """
        try:
            resources_dir.mkdir(parents=True, exist_ok=True)
            
            # Save English translations
            en_file = resources_dir / "en.json"
            with open(en_file, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_TRANSLATIONS, f, indent=2, ensure_ascii=False)
            
            # Create Spanish translations
            es_translations = self._get_spanish_translations()
            es_file = resources_dir / "es.json"
            with open(es_file, 'w', encoding='utf-8') as f:
                json.dump(es_translations, f, indent=2, ensure_ascii=False)
            
            # Create French translations
            fr_translations = self._get_french_translations()
            fr_file = resources_dir / "fr.json"
            with open(fr_file, 'w', encoding='utf-8') as f:
                json.dump(fr_translations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created default translation files in {resources_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create translation files: {e}")
    
    def _get_spanish_translations(self) -> Dict[str, str]:
        """Get Spanish translations."""
        return {
            # Application
            'app_title': 'Clasificador de Texturas PS2',
            'app_version': 'Versión {version}',
            
            # Main menu
            'menu_file': 'Archivo',
            'menu_edit': 'Editar',
            'menu_view': 'Ver',
            'menu_tools': 'Herramientas',
            'menu_help': 'Ayuda',
            
            # File menu
            'file_open': 'Abrir',
            'file_save': 'Guardar',
            'file_export': 'Exportar',
            'file_exit': 'Salir',
            
            # Buttons
            'btn_start': 'Iniciar',
            'btn_stop': 'Detener',
            'btn_pause': 'Pausar',
            'btn_resume': 'Reanudar',
            'btn_cancel': 'Cancelar',
            'btn_ok': 'Aceptar',
            'btn_apply': 'Aplicar',
            'btn_close': 'Cerrar',
            'btn_save': 'Guardar',
            'btn_load': 'Cargar',
            'btn_reset': 'Restablecer',
            
            # Processing
            'processing_title': 'Procesando Texturas',
            'processing_status': 'Procesando {current} de {total} archivos',
            'processing_complete': '¡Procesamiento Completo!',
            'processing_cancelled': 'Procesamiento Cancelado',
            'processing_error': 'Error de Procesamiento',
            
            # Settings
            'settings_title': 'Configuración',
            'settings_general': 'General',
            'settings_ui': 'Interfaz de Usuario',
            'settings_performance': 'Rendimiento',
            'settings_language': 'Idioma',
            'settings_hotkeys': 'Atajos de Teclado',
            
            # Panda
            'panda_title': 'Compañero Panda',
            'panda_mood': 'Estado de ánimo: {mood}',
            'panda_level': 'Nivel {level}',
            'panda_xp': '{current} / {max} XP',
            'panda_click_me': '¡Haz clic en mí! 🐼',
            'panda_happy': 'Feliz',
            'panda_working': 'Trabajando',
            'panda_celebrating': 'Celebrando',
            'panda_tired': 'Cansado',
            'panda_playing': 'Jugando',
            'panda_eating': 'Comiendo',
            
            # Common
            'common_yes': 'Sí',
            'common_no': 'No',
            'common_confirm': 'Confirmar',
            'common_warning': 'Advertencia',
            'common_error': 'Error',
            'common_success': 'Éxito',
            'common_loading': 'Cargando...',
            'common_saving': 'Guardando...',
            
            # Messages
            'msg_welcome': '¡Bienvenido al Clasificador de Texturas PS2! 🐼',
            'msg_ready': 'Listo para clasificar texturas',
            'msg_no_files': 'No se seleccionaron archivos',
            'msg_operation_complete': 'Operación completada con éxito',
            'msg_operation_failed': 'Operación fallida: {error}',
        }
    
    def _get_french_translations(self) -> Dict[str, str]:
        """Get French translations."""
        return {
            # Application
            'app_title': 'Trieur de Textures PS2',
            'app_version': 'Version {version}',
            
            # Main menu
            'menu_file': 'Fichier',
            'menu_edit': 'Éditer',
            'menu_view': 'Afficher',
            'menu_tools': 'Outils',
            'menu_help': 'Aide',
            
            # File menu
            'file_open': 'Ouvrir',
            'file_save': 'Enregistrer',
            'file_export': 'Exporter',
            'file_exit': 'Quitter',
            
            # Buttons
            'btn_start': 'Démarrer',
            'btn_stop': 'Arrêter',
            'btn_pause': 'Pause',
            'btn_resume': 'Reprendre',
            'btn_cancel': 'Annuler',
            'btn_ok': 'OK',
            'btn_apply': 'Appliquer',
            'btn_close': 'Fermer',
            'btn_save': 'Enregistrer',
            'btn_load': 'Charger',
            'btn_reset': 'Réinitialiser',
            
            # Processing
            'processing_title': 'Traitement des Textures',
            'processing_status': 'Traitement de {current} sur {total} fichiers',
            'processing_complete': 'Traitement Terminé!',
            'processing_cancelled': 'Traitement Annulé',
            'processing_error': 'Erreur de Traitement',
            
            # Settings
            'settings_title': 'Paramètres',
            'settings_general': 'Général',
            'settings_ui': 'Interface Utilisateur',
            'settings_performance': 'Performance',
            'settings_language': 'Langue',
            'settings_hotkeys': 'Raccourcis Clavier',
            
            # Panda
            'panda_title': 'Compagnon Panda',
            'panda_mood': 'Humeur: {mood}',
            'panda_level': 'Niveau {level}',
            'panda_xp': '{current} / {max} XP',
            'panda_click_me': 'Cliquez sur moi! 🐼',
            'panda_happy': 'Heureux',
            'panda_working': 'Travaillant',
            'panda_celebrating': 'Célébrant',
            'panda_tired': 'Fatigué',
            'panda_playing': 'Jouant',
            'panda_eating': 'Mangeant',
            
            # Common
            'common_yes': 'Oui',
            'common_no': 'Non',
            'common_confirm': 'Confirmer',
            'common_warning': 'Avertissement',
            'common_error': 'Erreur',
            'common_success': 'Succès',
            'common_loading': 'Chargement...',
            'common_saving': 'Enregistrement...',
            
            # Messages
            'msg_welcome': 'Bienvenue dans le Trieur de Textures PS2! 🐼',
            'msg_ready': 'Prêt à trier les textures',
            'msg_no_files': 'Aucun fichier sélectionné',
            'msg_operation_complete': 'Opération terminée avec succès',
            'msg_operation_failed': 'Échec de l'opération: {error}',
        }
    
    def set_language(self, language: Language) -> bool:
        """
        Set the current language.
        
        Args:
            language: Language to set
            
        Returns:
            True if language was set successfully
        """
        if language not in self.translations:
            logger.warning(f"Translations not available for {language.value}")
            return False
        
        self.current_language = language
        logger.info(f"Language set to {language.value}")
        return True
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        Get translated text for a key.
        
        Args:
            key: Translation key
            **kwargs: Format arguments for the translation string
            
        Returns:
            Translated and formatted text
        """
        # Get translation for current language
        translations = self.translations.get(self.current_language, self.DEFAULT_TRANSLATIONS)
        text = translations.get(key)
        
        # Fallback to English if not found
        if text is None:
            text = self.DEFAULT_TRANSLATIONS.get(key, f"[{key}]")
            logger.debug(f"Translation not found for key '{key}' in {self.current_language.value}")
        
        # Format with arguments if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format argument for '{key}': {e}")
        
        return text
    
    def get_available_languages(self) -> List[Language]:
        """Get list of available languages."""
        return list(self.translations.keys())
    
    def export_translations(self, filepath: str, language: Language) -> bool:
        """
        Export translations to a file.
        
        Args:
            filepath: Path to export file
            language: Language to export
            
        Returns:
            True if exported successfully
        """
        try:
            translations = self.translations.get(language)
            if not translations:
                logger.error(f"No translations available for {language.value}")
                return False
            
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {language.value} translations to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export translations: {e}")
            return False
    
    def import_translations(self, filepath: str, language: Language) -> bool:
        """
        Import translations from a file.
        
        Args:
            filepath: Path to import file
            language: Language to import
            
        Returns:
            True if imported successfully
        """
        try:
            path = Path(filepath)
            if not path.exists():
                logger.error(f"Translation file not found: {filepath}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            
            self.translations[language] = translations
            logger.info(f"Imported {language.value} translations from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import translations: {e}")
            return False


# Global translation manager instance
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get the global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def t(key: str, **kwargs) -> str:
    """
    Shorthand function to get translated text.
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated text
    """
    return get_translation_manager().get_text(key, **kwargs)
