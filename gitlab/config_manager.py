"""
config_manager.py - Configuration manager for Selenium Recorder

This module handles loading, saving, and managing application configuration settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class ConfigManager:
    """
    Manager for application configuration settings.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self._get_default_config()
        self.logger = logging.getLogger("ConfigManager")
        
        # Load configuration if file exists
        if os.path.exists(config_file):
            self.load_config()
        else:
            self.save_config()
            
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                
            # Merge with default config to ensure all keys exist
            self._merge_config(self.config, loaded_config)
            
            self.logger.info(f"Loaded configuration from {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return False
            
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(self.config_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Add last updated timestamp
            self.config["last_updated"] = datetime.now().isoformat()
                
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            self.logger.info(f"Saved configuration to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
            
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config
        
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.
        
        Args:
            new_config: New configuration values
            
        Returns:
            True if updated and saved successfully, False otherwise
        """
        # Update config
        self._merge_config(self.config, new_config)
        
        # Save to file
        return self.save_config()
        
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            value = self.config
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
                    
            return value
        else:
            return self.config.get(key, default)
            
    def set_value(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Value to set
            
        Returns:
            True if set and saved successfully, False otherwise
        """
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            config = self.config
            
            # Navigate to the nested dictionary
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                elif not isinstance(config[part], dict):
                    config[part] = {}
                    
                config = config[part]
                
            # Set the value
            config[parts[-1]] = value
        else:
            self.config[key] = value
            
        # Save to file
        return self.save_config()
        
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.
        
        Returns:
            True if reset and saved successfully, False otherwise
        """
        self.config = self._get_default_config()
        return self.save_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            
            # Browser settings
            "browser": {
                "type": "chrome",
                "driver_path": "",
                "headless": False,
                "window_width": 1280,
                "window_height": 800,
                "user_agent": "",
                "additional_options": {}
            },
            
            # Recording settings
            "recording": {
                "take_screenshots": True,
                "record_mouse": False,
                "record_keyboard": True,
                "smart_detection": True
            },
            
            # Playback settings
            "playback": {
                "highlight_elements": True,
                "wait_for_page_load": True,
                "wait_timeout": 30
            },
            
            # Script generation options
            "script_options": {
                "framework": "selenium",
                "include_comments": True,
                "include_timestamps": False,
                "use_explicit_waits": True,
                "generate_assertions": False,
                "test_framework": "pytest"
            },
            
            # UI settings
            "ui": {
                "theme": "system",
                "font_size": 10,
                "show_line_numbers": True,
                "auto_save": True,
                "confirm_exit": True
            },
            
            # Paths
            "recent_files": [],
            "screenshot_dir": "screenshots",
            "export_dir": "exports",
            
            # Other settings
            "playback_delay": 0.5,
            "max_recent_files": 10
        }
        
    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]):
        """
        Recursively merge source dictionary into target dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_config(target[key], value)
            else:
                # Update or add value
                target[key] = value
