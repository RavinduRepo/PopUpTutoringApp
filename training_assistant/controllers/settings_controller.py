# controllers/settings_controller.py
from .base_controller import BaseController
import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)

class SettingsController(BaseController):
    """Manages the logic for the settings view, including hotkey capturing."""

    def __init__(self, main_controller, event_listener):
        super().__init__(main_controller, event_listener)
        self.view = None
        self.current_capture_key = None
        
    def set_view(self, view):
        """Sets the reference to the SettingsView instance."""
        self.view = view

    def on_show(self):
        """Called when the settings view is shown. Subscribes to events."""
        logger.info("Settings view shown, subscribing to hotkey events.")
        self.event_listener.subscribe_keyboard('hotkey', self.handle_hotkey_capture)
        self.start_event_listener()

    def on_hide(self):
        """Called when the settings view is hidden. Unsubscribes from events."""
        logger.info("Settings view hidden, unsubscribing from hotkey events.")
        self.stop_event_listener()
        self.current_capture_key = None
        if self.view:
            self.view.reset_capture_state()
        
    def start_hotkey_capture(self, full_key):
        """Sets the target shortcut key for capture."""
        self.current_capture_key = full_key
        self.view.update_status("Press a hotkey...")

    def handle_hotkey_capture(self, data):
        """Handles a hotkey event from the listener and updates the UI."""
        if self.current_capture_key and self.view:
            hotkey_combo = data.get('combination')
            if hotkey_combo:
                # Update the button with the captured shortcut
                self.view.update_shortcut_button(self.current_capture_key, hotkey_combo)
                self.view.update_status(f"Hotkey '{hotkey_combo}' captured. Click Apply to save.")
                self.current_capture_key = None

    def apply_settings(self, new_theme, new_shortcuts):
        """Saves the settings to the model and updates the theme."""
        self.main_controller.model.update_setting("theme", new_theme)
        self.main_controller.model.update_setting("shortcuts", new_shortcuts)
        self.main_controller.update_theme()
        messagebox.showinfo("Settings", "Settings applied successfully!")