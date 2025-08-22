# views/player_view.py

import tkinter as tk
from tkinter import ttk, filedialog
from views.home_view import BaseView

class PlayerView(BaseView):
    def __init__(self, parent, controller, model):
        super().__init__(parent, controller, model)
        self.create_widgets()
        self.bind_shortcuts()
    
    def create_widgets(self):
        ttk.Label(self, text="Playback Mode", font=("Arial", 18, "bold")).pack(pady=20)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(anchor="center")
        
        self.status_var = tk.StringVar(value="Select a tutorial to play.")
        ttk.Label(content_frame, textvariable=self.status_var, font=("Arial", 12)).pack(pady=(0, 30))
        
        self.load_btn = ttk.Button(content_frame, text="📁 Load Tutorial",
                                   command=self.load_tutorial_file,
                                   width=20, style="Play.TButton")
        self.load_btn.pack(pady=10)
        
        self.play_btn = ttk.Button(content_frame, text="▶ Start Playback",
                                   command=self.start_playback,
                                   width=20, state="disabled")
        self.play_btn.pack(pady=10)
        
        self.back_btn = ttk.Button(content_frame, text="← Back",
                                   command=self.controller.show_home,
                                   width=20)
        self.back_btn.pack(pady=20)
        
        self.create_play_style()

    def load_tutorial_file(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("Tutorial Files", "*.json")],
            initialdir=self.controller.player.tutorials_dir,
            title="Select a Tutorial to Play"
        )
        
        if file_path:
            if self.controller.player.load_tutorial(file_path):
                self.play_btn.config(state="normal")
                self.update_status("Tutorial loaded. Press 'Start Playback' to begin.")
            else:
                self.update_status("Failed to load tutorial.")
    
    def start_playback(self):
        self.controller.player.start_playback()
    
    def update_status(self, status):
        self.status_var.set(status)
    
    def create_play_style(self):
        style = ttk.Style()
        if self.model.settings["theme"] == "dark":
            style.configure("Play.TButton", background="#28a745", foreground="#ffffff")
            style.map("Play.TButton", background=[('active', '#218838')])
        else:
            style.configure("Play.TButton", background="#28a745", foreground="#ffffff")
            style.map("Play.TButton", background=[('active', '#218838')])
    
    def bind_shortcuts(self):
        shortcuts = self.model.settings["shortcuts"]
        self.controller.bind_all(shortcuts["back"], lambda e: self.controller.show_home())
        self.controller.bind_all(shortcuts["settings"], lambda e: self.controller.show_settings())
