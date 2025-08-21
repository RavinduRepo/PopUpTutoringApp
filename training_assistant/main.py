# main.py

import tkinter as tk
from tkinter import messagebox
from models.models import AppModel
from views.home_view import HomeView
from views.record_view import RecordView
from views.play_view import PlayView
from views.settings_view import SettingsView
from controllers.recorder_controller import RecorderController
from controllers.player_controller import PlayerController

class TrainingAssistantController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.model = AppModel()
        self.recorder = RecorderController(self, self.model)
        self.player = PlayerController(self, self.model)
        self.setup_window()
        self.create_views()
        self.show_home()
        self.update_theme()
        self.iconbitmap("assets/myIcon.ico")
    
    def setup_window(self):
        self.title("Interactive Training Assistant")
        self.geometry("900x600")
        self.resizable(True, True)
        self.minsize(800, 500)
        
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
        # file_menu.add_separator()
        # file_menu.add_command(label="Exit", command=self.quit_app)
    
    def create_views(self):
        self.views = {}
        
        view_classes = {
            'home': HomeView,
            'record': RecordView,
            'play': PlayView,
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
    
    def start_recording(self, tutorial_name):
        self.recorder.start_recording(tutorial_name)
    
    def stop_recording(self):
        self.recorder.stop_recording()
    
    def load_tutorial(self, tutorial_path):
        self.player.load_tutorial(tutorial_path)
    
    def start_playback(self):
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
