# views/player_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from views.home_view import BaseView
import os
import sys

def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class PlayerView(BaseView):
    def __init__(self, parent, controller, model):
        super().__init__(parent, controller, model)
        self.create_widgets()
    
    def create_widgets(self):
        # Main container frame
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=40, pady=20)
        
        # Title
        ttk.Label(main_frame, text="Playback Mode", font=("Arial", 18, "bold")).pack(pady=(0, 20))
        
        # Load Tutorial controls
        load_frame = ttk.Frame(main_frame)
        load_frame.pack(pady=10)
        
        self.load_btn = ttk.Button(load_frame, text="📂 Load Tutorial File", command=self.controller.player.load_tutorial_from_dialog, width=25)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar(value="No tutorial loaded.")
        ttk.Label(load_frame, textvariable=self.status_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Tutorial info display
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(pady=20, fill="x")
        
        self.tutorial_name_var = tk.StringVar(value="Tutorial Name: N/A")
        ttk.Label(info_frame, textvariable=self.tutorial_name_var, font=("Arial", 12)).pack()
        
        self.created_date_var = tk.StringVar(value="Created: N/A")
        ttk.Label(info_frame, textvariable=self.created_date_var, font=("Arial", 10)).pack()
        
        # Playback controls
        playback_controls = ttk.Frame(main_frame)
        playback_controls.pack(pady=10)
        
        self.play_btn = ttk.Button(playback_controls, text="▶ Play", command=self.controller.player.start_playback, state="disabled")
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(playback_controls, text="⏹ Stop", command=self.controller.player.end_playback, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Convert to PDF button
        self.convert_btn = ttk.Button(main_frame, text="📄 Convert to PDF", command=self.controller.player.convert_to_pdf, width=25)
        self.convert_btn.pack(pady=10)

        # Back button
        back_btn = ttk.Button(main_frame, text="← Back", command=self.controller.show_home, width=20)
        back_btn.pack(pady=20)
        
        self.create_player_style()
        
    def create_player_style(self):
        style = ttk.Style()
        style.configure("Player.TButton", background="#28a745", foreground="#ffffff")
        style.map("Player.TButton", background=[('active', '#218838')])
        
    def update_ui_on_load(self, tutorial):
        """Updates the main view with tutorial information."""
        self.tutorial_name_var.set(f"Tutorial Name: {tutorial.get('name', 'N/A')}")
        self.created_date_var.set(f"Created: {tutorial.get('created', 'N/A')}")
        self.status_var.set(f"Tutorial '{tutorial.get('name', '')}' loaded successfully.")
        self.play_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def update_buttons_on_playback(self, is_playing):
        """Updates the state of the main view's playback buttons."""
        self.play_btn.config(state="disabled" if is_playing else "normal")
        self.stop_btn.config(state="normal" if is_playing else "disabled")
    
    def update_status(self, status):
        """Updates the status label."""
        self.status_var.set(status)