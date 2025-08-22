# main.py

import tkinter as tk
from tkinter import messagebox
from models.models import AppModel
from views.home_view import HomeView
from views.recorder_view import RecordView
from views.player_view import PlayerView
from views.settings_view import SettingsView
from controllers.recorder_controller import RecorderController
from controllers.player_controller import PlayerController
import os
import sys

def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class TrainingAssistantController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.model = AppModel()
        # Initialize controllers with a reference to the main app
        self.recorder = RecorderController(self)
        self.player = PlayerController(self)
        self.setup_window()
        self.create_views()
        self.show_home()
        self.update_theme()
    
    def setup_window(self):
        self.title("Interactive Training Assistant")
        self.geometry("900x600")
        self.resizable(True, True)
        self.minsize(800, 500)
        
        # Get the path to the icon file
        icon_path = os.path.join(get_base_path(), 'assets', 'myIcon.ico')
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            print(f"Icon file not found at: {icon_path}")
            
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
            'home': HomeView,
            'record': RecordView,
            'play': PlayerView,
            'settings': SettingsView
        }
        
        for name, view_class in view_classes.items():
            view = view_class(self.container, self, self.model)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[name] = view
    
    def show_frame(self, frame_name):
        self.views[frame_name].tkraise()
    
    def show_home(self):
        self.show_frame('home')
    
    def show_record(self):
        self.show_frame('record')
    
    def show_play(self):
        self.show_frame('play')
    
    def show_settings(self):
        self.show_frame('settings')
    
    def start_recording(self, tutorial_name, file_path):
        """Starts a new recording session with a specified save path."""
        self.recorder.start_recording(tutorial_name, file_path)
    
    def stop_recording(self):
        """Stops the recording session and saves the tutorial to the predetermined path."""
        self.recorder.stop_recording()
    
    def load_tutorial(self):
        """Prompts the user to load a tutorial file."""
        self.player.load_tutorial()
    
    def start_playback(self):
        """Starts playback of the loaded tutorial."""
        self.player.start_playback()
    
    def quit_app(self):
        self.quit()
    
    def update_theme(self):
        for view in self.views.values():
            view.update_theme()
    
    def rebind_shortcuts(self):
        self.unbind_all("<Key>")
        for view in self.views.values():
            if hasattr(view, 'bind_shortcuts'):
                view.bind_shortcuts()

if __name__ == "__main__":
    app = TrainingAssistantController()
    app.mainloop()
