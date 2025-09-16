# controllers/base_controller.py
import json
import threading
import os
import logging
import time
import sys
from audio_controller import AudioController

logger = logging.getLogger(__name__)


class BaseController:
    """A base class for controllers to manage common functionality."""

    def __init__(self, main_controller, event_listener):
        self.main_controller = main_controller
        self.event_listener = event_listener
        self.listener_thread = None
        self.ignored_shortcuts_recorder = {}  # Dictionary for recorder shortcuts
        self.ignored_shortcuts_player = {}  # Dictionary for player shortcuts
        self.load_shortcuts()
        self.audio_controller = AudioController()

    def start_event_listener(self):
        """Starts the event listener in a new thread."""
        if self.listener_thread is None or not self.listener_thread.is_alive():
            self.listener_thread = threading.Thread(
                target=self.event_listener.start_listening, daemon=True
            )
            self.listener_thread.start()

    def stop_event_listener(self):
        """Stops the event listener thread in a separate thread."""

        def stop_listener():
            if self.listener_thread and self.listener_thread.is_alive():
                time.sleep(0.5)  # delay to wait until pending actions complete
                self.event_listener.stop_listening()
                self.listener_thread.join()
                self.listener_thread = None

        threading.Thread(target=stop_listener, daemon=True).start()

    def load_shortcuts(self):
        """
        Loads shortcut key combinations from settings.json.
        If the file does not exist, it creates a new one with default values.
        """
        # Detect PyInstaller bundle and set settings_path accordingly
        if getattr(sys, "frozen", False):
            # Running in a PyInstaller bundle
            base_path = os.path.dirname(sys.executable)
        else:
            # Running from source
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.abspath(os.path.join(base_path, ".."))
        settings_path = os.path.join(base_path, "settings.json")

        # Define default settings
        default_settings = {
            "theme": "light",
            "shortcuts": {
                "player": {
                    "info": "ctrl+e",
                    "back": "ctrl+a",
                    "pause": "ctrl+s",
                    "next": "ctrl+d",
                    "stop": "ctrl+q",
                },
                "recorder": {
                    "info": "ctrl+e",
                    "pause": "ctrl+s",
                    "back": "ctrl+a",
                    "stop": "ctrl+q",
                },
            },
        }

        try:
            if not os.path.exists(settings_path):
                logger.info(
                    f"settings.json not found. Creating default file at: {settings_path}"
                )
                with open(settings_path, "w") as f:
                    json.dump(default_settings, f, indent=4)

            with open(settings_path, "r") as f:
                settings = json.load(f)

            # Load and map recorder shortcuts
            recorder_shortcuts = settings.get("shortcuts", {}).get("recorder", {})
            for action, key in recorder_shortcuts.items():
                self.ignored_shortcuts_recorder[key] = action

            # Load and map player shortcuts
            player_shortcuts = settings.get("shortcuts", {}).get("player", {})
            for action, key in player_shortcuts.items():
                self.ignored_shortcuts_player[key] = action

            logger.info(f"Recorder shortcuts: {self.ignored_shortcuts_recorder}")
            logger.info(f"Player shortcuts: {self.ignored_shortcuts_player}")

        except Exception as e:
            logger.warning(f"Could not load or create settings.json: {e}")
            self.ignored_shortcuts_recorder = {}
            self.ignored_shortcuts_player = {}

    def get_window_rect(self, window):
        """Gets the bounding box of a Tkinter window."""
        window.update_idletasks()
        x = window.winfo_rootx()
        y = window.winfo_rooty()
        width = window.winfo_width()
        height = window.winfo_height()
        return (x, y, x + width, y + height)

    def is_click_on_app_window(self, x, y):
        """Checks if the click coordinates are within the main app window."""
        main_window_rect = self.get_window_rect(self.main_controller)
        if (
            main_window_rect[0] <= x <= main_window_rect[2]
            and main_window_rect[1] <= y <= main_window_rect[3]
        ):
            return True
        return False

