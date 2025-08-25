# views/player_mini_view.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import base64
import io
import logging
from .mini_view_base import MiniViewBase

logger = logging.getLogger(__name__)

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class PlayerMiniView(MiniViewBase):
    """Handles the UI for the tutorial playback."""

    def __init__(self, parent, next_step_callback, previous_step_callback, toggle_pause_callback, end_playback_callback):
        super().__init__(parent)
        self.control_window = None
        self.overlay_window = None
        self.play_pause_btn = None
        self.step_label_var = None
        self.action_label_var = None
        self.action_detail_var = None
        self.thumbnail_label = None
        self.next_step_callback = next_step_callback
        self.previous_step_callback = previous_step_callback
        self.toggle_pause_callback = toggle_pause_callback
        self.end_playback_callback = end_playback_callback
        self.thumbnail_photo = None

    def create_control_window(self):
        """Creates a small, always-on-top control window for playback."""
        main_frame, header_frame = self.create_base_window("Tutorial Controls")
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="left", fill="both", expand=True)

        self.action_label_var = tk.StringVar()
        action_label = ttk.Label(control_frame, textvariable=self.action_label_var, font=("Arial", 10, "italic"))
        action_label.pack(pady=(0, 2))
        
        self.action_detail_var = tk.StringVar()
        action_detail_label = ttk.Label(control_frame, textvariable=self.action_detail_var, font=("Arial", 10, "bold"))
        action_detail_label.pack(pady=(0, 5))

        self.thumbnail_label = ttk.Label(control_frame)
        self.thumbnail_label.pack(pady=(0, 10))
        
        self.step_label_var = tk.StringVar()
        step_label = ttk.Label(control_frame, textvariable=self.step_label_var, font=("Arial", 12, "bold"))
        step_label.pack(pady=(0, 10))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        self.info_btn = ttk.Button(button_frame, text="ℹ️", width=3)
        self.info_btn.pack(side=tk.LEFT, padx=5)
        self.info_btn.bind("<ButtonPress-1>", self.on_info_press)
        self.info_btn.bind("<ButtonRelease-1>", self.on_info_release)
        
        nav_button_frame = ttk.Frame(button_frame)
        nav_button_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(nav_button_frame, text="⏪ Back", command=self.previous_step_callback, width=6).pack(side=tk.LEFT, padx=2)
        self.play_pause_btn = ttk.Button(nav_button_frame, text="⏸ Pause", command=self.toggle_pause_callback, width=6)
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_button_frame, text="⏩ Next", command=self.next_step_callback, width=6).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(control_frame, text="⏹ Stop", command=self.end_playback_callback, width=10).pack(pady=(10, 0))
        
        screen_width = self.parent.winfo_screenwidth()
        self.window.update_idletasks()
        win_width = self.window.winfo_reqwidth()
        self.window.geometry(f"+{screen_width - win_width - 10}+10")
        
    def update_play_pause_button(self, text):
        if self.play_pause_btn:
            self.play_pause_btn.config(text=text)

    def get_control_window_rect(self):
        if not self.window:
            return None
        self.window.update_idletasks()
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        return (x, y, x + width, y + height)
    
    def destroy_control_window(self):
        self.destroy_window()

    def update_step_display(self, step_info, allowed_size=8):
        if self.window:
            self.set_current_step_data(step_info)
            
            info_text = f"Step {step_info['index'] + 1}/{step_info['total']}"
            if step_info.get("notes"):
                info_text += f"\n{step_info['notes']}"
            self.step_label_var.set(info_text)

            action_type = step_info.get("action_type", "click").capitalize()
            self.action_label_var.set(action_type)

            action_detail_text = ""
            if action_type.lower() == "typing":
                text = step_info.get('text', '')
                display_text = text[:allowed_size]
                if len(text) > allowed_size:
                    display_text += "..."
                action_detail_text = f'Text: "{display_text}"\n(press: ctrl+v)'
            elif action_type.lower() == "shortcut":
                action_detail_text = f"Keys: {step_info.get('keys', '')}"
            self.action_detail_var.set(action_detail_text)

            if step_info.get("thumb") and self.thumbnail_label:
                thumb_img = step_info["thumb"]
                self.thumbnail_photo = ImageTk.PhotoImage(thumb_img)
                self.thumbnail_label.config(image=self.thumbnail_photo)
    
    def create_overlay(self, step_info):
        if self.overlay_window:
            self.destroy_overlay()
        
        self.overlay_window = tk.Toplevel(self.parent)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.wm_attributes('-transparentcolor', 'SystemButtonFace')
        
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        self.overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        canvas = tk.Canvas(self.overlay_window, bg='SystemButtonFace', highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        x, y = step_info["coordinates"]
        radius = 40
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline='red', width=5, fill='')
        
    def destroy_overlay(self, event=None):
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None