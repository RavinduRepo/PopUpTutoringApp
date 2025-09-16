# main.py
import tkinter as tk
from tkinter import PhotoImage
from models.models import AppModel
from views.home_view import HomeView
from views.recorder_view import RecordView
from views.player_view import PlayerView
from views.settings_view import SettingsView
from controllers.recorder_controller import RecorderController
from controllers.player_controller import PlayerController
from controllers.settings_controller import SettingsController
from utils.event_listener.event_listener import EventListener
import os
import sys
import logging

logger = logging.getLogger(__name__)

# Configure the logger
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "data")
    return os.getcwd()


class TrainingAssistantController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.model = AppModel()
        self.event_listener = EventListener()
        # Initialize controllers with a reference to the main app
        self.recorder = RecorderController(self, self.event_listener)
        self.player = PlayerController(self, self.event_listener)
        self.settings_controller = SettingsController(self, self.event_listener)
        self.setup_window()
        self.create_views()
        self.show_home()
        self.update_theme()

    def setup_window(self):
        self.title("Interactive Training Assistant")
        self.geometry("900x600")
        self.resizable(True, True)
        self.minsize(800, 500)

        base_path = get_base_path()
        if sys.platform.startswith("win"):
            # Use .ico on Windows
            icon_path = os.path.join(base_path, "assets", "myIcon.ico")
            if os.path.exists(icon_path):
                try:
                    self.iconbitmap(icon_path)
                except Exception as e:
                    logger.warning(f"Could not load .ico icon: {e}")
            else:
                logger.info(f"Icon file not found at: {icon_path}")
        else:
            # Use .png on Linux/macOS
            icon_path = os.path.join(base_path, "assets", "myIcon.png")
            if os.path.exists(icon_path):
                try:
                    img = PhotoImage(file=icon_path)
                    self.iconphoto(False, img)
                except Exception as e:
                    logger.warning(f"Could not load .png icon: {e}")
            else:
                logger.info(f"Icon file not found at: {icon_path}")

        self.create_menu()

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Preferences", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.show_settings)

    def create_views(self):
        self.views = {}

        view_classes = {
            "home": HomeView,
            "record": RecordView,
            "play": PlayerView,
            "settings": SettingsView,
        }

        for name, view_class in view_classes.items():
            # Pass the correct controller to each view
            if name == "settings":
                view = view_class(
                    self.container, self, self.model, self.settings_controller
                )
                self.settings_controller.set_view(
                    view
                )  # Set the view reference in the controller
            else:
                view = view_class(self.container, self, self.model)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[name] = view

    def show_frame(self, frame_name):
        # Notify views about their state change
        for name, view in self.views.items():
            if name == frame_name:
                if hasattr(view, "on_show"):
                    view.on_show()
            else:
                if hasattr(view, "on_hide"):
                    view.on_hide()

        self.views[frame_name].tkraise()

    def show_home(self):
        self.show_frame("home")

    def show_record(self):
        self.show_frame("record")

    def show_play(self):
        self.show_frame("play")

    def show_settings(self):
        self.show_frame("settings")

    def quit_app(self):
        self.quit()

    def update_theme(self):
        for view in self.views.values():
            view.update_theme()


if __name__ == "__main__":
    app = TrainingAssistantController()
    app.mainloop()
