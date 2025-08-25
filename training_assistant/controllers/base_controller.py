# controllers/base_controller.py
import threading
import tkinter as tk

class BaseController:
    """A base class for controllers to manage common functionality."""

    def __init__(self, main_controller, event_listener):
        self.main_controller = main_controller
        self.event_listener = event_listener
        self.listener_thread = None

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