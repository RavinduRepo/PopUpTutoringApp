import os
import json
import logging

logger = logging.getLogger(__name__)

class AppModel:
    """The central model for the application, handling data and settings."""

    def __init__(self):
        self.settings_file = "settings.json"
        self.settings = self.load_settings()

    def load_settings(self):
        """
        Loads settings from settings.json. If the file is not found or is corrupted,
        it creates a new one with default settings.
        """
        default_settings = {
        "theme": "light",
        "shortcuts": {
                "player": {
                "info": "ctrl+e",
                "back": "ctrl+a",
                "pause": "ctrl+s",
                "next": "ctrl+d",
                "stop": "ctrl+q"
                },
                "recorder": {
                "info": "ctrl+e",
                "pause": "ctrl+s",
                "back": "ctrl+a",
                "stop": "ctrl+q"
                }
            }
        }

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
                logger.info("Successfully loaded settings from settings.json.")
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f"Settings file not found or is corrupted: {e}. Using default settings.")
        else:
            logger.info("Settings file not found. Creating a new one with default settings.")
            self.save_settings(default_settings)

        return default_settings

    def update_setting(self, key, value):
        """Updates a setting and saves it to the file."""
        if key == "shortcuts":
            # This handles the nested dictionary structure for shortcuts
            self.settings[key].update(value)
        else:
            self.settings[key] = value
        self.save_settings(self.settings)
    
    def save_settings(self, settings_to_save):
        """Saves the given settings dictionary to the settings.json file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
            logger.info("Settings saved successfully.")
        except IOError as e:
            logger.error(f"Failed to save settings to settings.json: {e}")
