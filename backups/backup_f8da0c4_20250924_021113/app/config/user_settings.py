"""
User Configuration Manager for Contract Analyzer

Manages user-editable settings separate from secure environment variables.
Handles user preferences like model selection, analysis settings, and UI preferences.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UserSettingsManager:
    """
    Manages user-editable configuration settings.
    Separates secure settings (.env) from user preferences (user_config.json).
    """
    
    def __init__(self, config_file: str = "user_config.json"):
        """Initialize the user settings manager"""
        self.config_file = config_file
        self.config_path = Path(config_file)
        self._user_config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._user_config = json.load(f)
                logger.info(f"Loaded user configuration from {self.config_file}")
            else:
                # Create default config if file doesn't exist
                self._create_default_config()
                logger.info(f"Created default user configuration at {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load user config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        self._user_config = {
            "llm_settings": {
                "provider": "openai",
                "openai_model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 512,
                "timeout": 30
            },
            "analysis_settings": {
                "batch_size": 15,
                "use_fast_model": True,
                "max_workers": 5,
                "similarity_threshold": 0.5,
                "enable_caching": True
            },
            "ui_preferences": {
                "theme": "auto",
                "auto_refresh": True,
                "refresh_interval": 30000,
                "pagination_size": 20,
                "show_advanced_options": False
            },
            "report_settings": {
                "default_formats": ["xlsx", "pdf"],
                "include_summary": True,
                "include_details": True,
                "auto_download": False
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "version": "1.1.0"
            }
        }
        self._save_config()
    
    def _save_config(self):
        """Save configuration to JSON file"""
        try:
            # Update last modified timestamp
            if self._user_config and "metadata" in self._user_config:
                self._user_config["metadata"]["last_modified"] = datetime.now().isoformat()
            
            with open(self.config_path, 'w') as f:
                json.dump(self._user_config, f, indent=2)
            logger.info(f"Saved user configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save user config: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete user configuration"""
        return self._user_config.copy() if self._user_config else {}
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM-specific configuration"""
        return self._user_config.get("llm_settings", {}).copy()
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis-specific configuration"""
        return self._user_config.get("analysis_settings", {}).copy()
    
    def get_ui_preferences(self) -> Dict[str, Any]:
        """Get UI preferences"""
        return self._user_config.get("ui_preferences", {}).copy()
    
    def get_report_settings(self) -> Dict[str, Any]:
        """Get report generation settings"""
        return self._user_config.get("report_settings", {}).copy()
    
    def update_llm_config(self, config: Dict[str, Any]) -> bool:
        """Update LLM configuration"""
        try:
            if "llm_settings" not in self._user_config:
                self._user_config["llm_settings"] = {}
            
            self._user_config["llm_settings"].update(config)
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to update LLM config: {e}")
            return False
    
    def update_analysis_config(self, config: Dict[str, Any]) -> bool:
        """Update analysis configuration"""
        try:
            if "analysis_settings" not in self._user_config:
                self._user_config["analysis_settings"] = {}
            
            self._user_config["analysis_settings"].update(config)
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to update analysis config: {e}")
            return False
    
    def update_ui_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update UI preferences"""
        try:
            if "ui_preferences" not in self._user_config:
                self._user_config["ui_preferences"] = {}
            
            self._user_config["ui_preferences"].update(preferences)
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to update UI preferences: {e}")
            return False
    
    def update_report_settings(self, settings: Dict[str, Any]) -> bool:
        """Update report settings"""
        try:
            if "report_settings" not in self._user_config:
                self._user_config["report_settings"] = {}
            
            self._user_config["report_settings"].update(settings)
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to update report settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self._create_default_config()
            return True
        except Exception as e:
            logger.error(f"Failed to reset config to defaults: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to a file"""
        try:
            export_file = Path(export_path)
            with open(export_file, 'w') as f:
                json.dump(self._user_config, f, indent=2)
            logger.info(f"Exported user configuration to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"Import file does not exist: {import_path}")
                return False
            
            with open(import_file, 'r') as f:
                imported_config = json.load(f)
            
            # Validate imported config has required structure
            required_sections = ["llm_settings", "analysis_settings", "ui_preferences"]
            if not all(section in imported_config for section in required_sections):
                logger.error("Invalid configuration format in import file")
                return False
            
            self._user_config = imported_config
            self._save_config()
            logger.info(f"Imported user configuration from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False


# Create global instance
user_settings = UserSettingsManager()

# Export convenience functions
def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration"""
    return user_settings.get_llm_config()

def get_analysis_config() -> Dict[str, Any]:
    """Get analysis configuration"""
    return user_settings.get_analysis_config()

def get_ui_preferences() -> Dict[str, Any]:
    """Get UI preferences"""
    return user_settings.get_ui_preferences()

def get_report_settings() -> Dict[str, Any]:
    """Get report settings"""
    return user_settings.get_report_settings()


__all__ = [
    'UserSettingsManager', 
    'user_settings',
    'get_llm_config',
    'get_analysis_config', 
    'get_ui_preferences',
    'get_report_settings'
]