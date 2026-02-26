"""
Configuration Loader - Load and validate JSON configuration files
Supports automation workflows and batch processing
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and validate JSON configuration files."""
    
    def __init__(self):
        """Initialize configuration loader."""
        self.loaded_configs: Dict[str, Dict[str, Any]] = {}
        
    def load_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        Load and validate configuration file.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            Configuration dictionary or None if failed
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate configuration structure
            if not self._validate_config(config_data):
                logger.error(f"Invalid configuration structure: {config_path}")
                return None
            
            # Cache loaded config
            self.loaded_configs[str(path)] = config_data
            
            logger.info(f"Successfully loaded configuration: {config_path}")
            return config_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {config_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load configuration {config_path}: {e}")
            return None
    
    def load_profile(self, profile_path: str) -> Optional[Dict[str, Any]]:
        """
        Load organization profile.
        
        Args:
            profile_path: Path to profile JSON file
            
        Returns:
            Profile dictionary or None if failed
        """
        try:
            path = Path(profile_path)
            
            if not path.exists():
                logger.error(f"Profile file not found: {profile_path}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Validate profile structure
            if not self._validate_profile(profile_data):
                logger.error(f"Invalid profile structure: {profile_path}")
                return None
            
            logger.info(f"Successfully loaded profile: {profile_path}")
            return profile_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {profile_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load profile {profile_path}: {e}")
            return None
    
    def save_config(self, config_data: Dict[str, Any], output_path: str) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config_data: Configuration dictionary
            output_path: Path to save configuration
            
        Returns:
            True if successful
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            True if valid
        """
        try:
            # Check for required top-level keys
            required_keys = ['version', 'settings']
            for key in required_keys:
                if key not in config_data:
                    logger.error(f"Missing required key in config: {key}")
                    return False
            
            # Validate version format
            version = config_data.get('version', '')
            if not self._validate_version(version):
                logger.error(f"Invalid version format: {version}")
                return False
            
            # Validate settings section
            settings = config_data.get('settings', {})
            if not isinstance(settings, dict):
                logger.error("Settings must be a dictionary")
                return False
            
            # Validate optional sections
            if 'input' in config_data:
                if not self._validate_input_section(config_data['input']):
                    return False
            
            if 'output' in config_data:
                if not self._validate_output_section(config_data['output']):
                    return False
            
            if 'processing' in config_data:
                if not self._validate_processing_section(config_data['processing']):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def _validate_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Validate profile structure.
        
        Args:
            profile_data: Profile dictionary
            
        Returns:
            True if valid
        """
        try:
            # Check for required profile keys
            required_keys = ['name']
            for key in required_keys:
                if key not in profile_data:
                    logger.error(f"Missing required key in profile: {key}")
                    return False
            
            # Validate style if present
            if 'style' in profile_data:
                valid_styles = ['by_category', 'by_type', 'by_size', 'flat', 'custom']
                if profile_data['style'] not in valid_styles:
                    logger.error(f"Invalid organization style: {profile_data['style']}")
                    return False
            
            # Validate folder structure if present
            if 'folder_structure' in profile_data:
                if not isinstance(profile_data['folder_structure'], dict):
                    logger.error("folder_structure must be a dictionary")
                    return False
            
            # Validate custom categories if present
            if 'custom_categories' in profile_data:
                if not isinstance(profile_data['custom_categories'], dict):
                    logger.error("custom_categories must be a dictionary")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Profile validation error: {e}")
            return False
    
    def _validate_version(self, version: str) -> bool:
        """
        Validate version string format (e.g., "1.0", "2.1.0").
        
        Args:
            version: Version string
            
        Returns:
            True if valid
        """
        pattern = r'^\d+\.\d+(\.\d+)?$'
        return bool(re.match(pattern, version))
    
    def _validate_input_section(self, input_data: Dict[str, Any]) -> bool:
        """Validate input section of configuration."""
        if not isinstance(input_data, dict):
            logger.error("Input section must be a dictionary")
            return False
        
        # Validate paths if present
        if 'paths' in input_data:
            if not isinstance(input_data['paths'], (list, str)):
                logger.error("Input paths must be a string or list")
                return False
        
        # Validate recursive flag
        if 'recursive' in input_data:
            if not isinstance(input_data['recursive'], bool):
                logger.error("recursive must be a boolean")
                return False
        
        # Validate file extensions
        if 'extensions' in input_data:
            if not isinstance(input_data['extensions'], list):
                logger.error("extensions must be a list")
                return False
        
        return True
    
    def _validate_output_section(self, output_data: Dict[str, Any]) -> bool:
        """Validate output section of configuration."""
        if not isinstance(output_data, dict):
            logger.error("Output section must be a dictionary")
            return False
        
        # Validate path if present
        if 'path' in output_data:
            if not isinstance(output_data['path'], str):
                logger.error("Output path must be a string")
                return False
        
        # Validate create_backup flag
        if 'create_backup' in output_data:
            if not isinstance(output_data['create_backup'], bool):
                logger.error("create_backup must be a boolean")
                return False
        
        # Validate overwrite flag
        if 'overwrite' in output_data:
            if not isinstance(output_data['overwrite'], bool):
                logger.error("overwrite must be a boolean")
                return False
        
        return True
    
    def _validate_processing_section(self, processing_data: Dict[str, Any]) -> bool:
        """Validate processing section of configuration."""
        if not isinstance(processing_data, dict):
            logger.error("Processing section must be a dictionary")
            return False
        
        # Validate threads
        if 'threads' in processing_data:
            threads = processing_data['threads']
            if not isinstance(threads, int) or threads < 1:
                logger.error("threads must be a positive integer")
                return False
        
        # Validate batch_size
        if 'batch_size' in processing_data:
            batch_size = processing_data['batch_size']
            if not isinstance(batch_size, int) or batch_size < 1:
                logger.error("batch_size must be a positive integer")
                return False
        
        # Validate dry_run flag
        if 'dry_run' in processing_data:
            if not isinstance(processing_data['dry_run'], bool):
                logger.error("dry_run must be a boolean")
                return False
        
        return True
    
    def create_template_config(self) -> Dict[str, Any]:
        """
        Create a template configuration with default values.
        
        Returns:
            Template configuration dictionary
        """
        return {
            "version": "1.0",
            "description": "Panda Sorter Converter Upscaler Configuration Template",
            "settings": {
                "organization_style": "by_category",
                "auto_classify": True,
                "create_backup": True
            },
            "input": {
                "paths": [],
                "recursive": True,
                "extensions": [".dds", ".png", ".jpg", ".bmp"]
            },
            "output": {
                "path": "",
                "create_subdirs": True,
                "overwrite": False
            },
            "processing": {
                "threads": 4,
                "batch_size": 100,
                "dry_run": False,
                "verbose": False
            },
            "filters": {
                "min_size": 0,
                "max_size": 0,
                "categories": []
            }
        }
    
    def create_template_profile(self) -> Dict[str, Any]:
        """
        Create a template organization profile with default values.
        
        Returns:
            Template profile dictionary
        """
        return {
            "name": "Default Profile",
            "description": "Default organization profile",
            "version": "1.0",
            "style": "by_category",
            "folder_structure": {
                "characters": "Characters",
                "ui": "UI",
                "environment": "Environment",
                "effects": "Effects",
                "weapons": "Weapons"
            },
            "naming_pattern": "{category}/{name}",
            "auto_classify": True,
            "custom_categories": {},
            "processing": {
                "convert_formats": False,
                "target_format": "png",
                "create_thumbnails": False,
                "thumbnail_size": [256, 256]
            },
            "tags": ["default", "general"]
        }
    
    def merge_configs(
        self,
        base_config: Dict[str, Any],
        override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two configurations, with override taking precedence.
        
        Args:
            base_config: Base configuration
            override_config: Override configuration
            
        Returns:
            Merged configuration
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_config_summary(self, config_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of configuration.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            Summary string
        """
        lines = []
        lines.append("Configuration Summary:")
        lines.append(f"  Version: {config_data.get('version', 'Unknown')}")
        
        if 'description' in config_data:
            lines.append(f"  Description: {config_data['description']}")
        
        if 'settings' in config_data:
            lines.append("  Settings:")
            for key, value in config_data['settings'].items():
                lines.append(f"    {key}: {value}")
        
        if 'input' in config_data:
            input_data = config_data['input']
            lines.append("  Input:")
            if 'paths' in input_data:
                paths = input_data['paths']
                if isinstance(paths, list):
                    lines.append(f"    Paths: {len(paths)} directories")
                else:
                    lines.append(f"    Path: {paths}")
        
        if 'processing' in config_data:
            proc = config_data['processing']
            lines.append("  Processing:")
            lines.append(f"    Threads: {proc.get('threads', 'default')}")
            lines.append(f"    Batch Size: {proc.get('batch_size', 'default')}")
            lines.append(f"    Dry Run: {proc.get('dry_run', False)}")
        
        return '\n'.join(lines)


def load_config_file(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load a configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary or None
    """
    loader = ConfigLoader()
    return loader.load_config(config_path)


def load_profile_file(profile_path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load a profile file.
    
    Args:
        profile_path: Path to profile file
        
    Returns:
        Profile dictionary or None
    """
    loader = ConfigLoader()
    return loader.load_profile(profile_path)
