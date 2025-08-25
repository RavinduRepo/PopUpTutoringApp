# controllers/base_controller.py
import json
import threading
import tkinter as tk
import os
import logging
logger = logging.getLogger(__name__)

class BaseController:
    """A base class for controllers to manage common functionality."""

    def __init__(self, main_controller, event_listener):
        self.main_controller = main_controller
        self.event_listener = event_listener
        self.listener_thread = None
        self.ignored_shortcuts = set()
        self.load_shortcuts()

    def start_event_listener(self):
        """Starts the event listener in a new thread."""
        if self.listener_thread is None or not self.listener_thread.is_alive():
            self.listener_thread = threading.Thread(target=self.event_listener.start_listening, daemon=True)
            self.listener_thread.start()

    def stop_event_listener(self):
        """Stops the event listener thread."""
        if self.listener_thread and self.listener_thread.is_alive():
            self.event_listener.stop_listening()
            self.listener_thread.join()
            self.listener_thread = None

    def load_shortcuts(self):
        """Loads shortcut key combinations from settings.json to be ignored during recording."""
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'settings.json')
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            shortcuts = settings.get('shortcuts', {})
            self.ignored_shortcuts = set(shortcuts.values())
            logger.info(f"Ignored shortcuts: {self.ignored_shortcuts}")
        except Exception as e:
            logger.warning(f"Could not load shortcuts from settings.json: {e}")
            self.ignored_shortcuts = set()

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
        if main_window_rect[0] <= x <= main_window_rect[2] and \
           main_window_rect[1] <= y <= main_window_rect[3]:
            return True
        return False