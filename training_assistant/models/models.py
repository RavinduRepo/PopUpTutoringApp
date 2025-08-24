# ------------------ MODEL ------------------
import json
import os

class AppModel:
    def __init__(self):
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
    
    def load_settings(self):
        default_settings = {
            "theme": "dark",
            "shortcuts": {
                "record": "ctrl+r",
                "play": "ctrl+p",
                "settings": "ctrl+,",
                "back": "esc"
            }   
            }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
            except:
                pass
        
        return default_settings
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    def update_setting(self, key, value):
        if key == "shortcuts":
            self.settings[key].update(value)
        else:
            self.settings[key] = value
        self.save_settings()
