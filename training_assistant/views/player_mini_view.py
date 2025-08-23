# views/player_mini_view.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import base64
import io

# Helper function to get base path for resources
def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class PlayerMiniView:
    """Handles the UI for the tutorial playback."""

    def __init__(self, parent, next_step_callback, previous_step_callback, toggle_pause_callback, end_playback_callback):
        self.parent = parent
        self.control_window = None
        self.overlay_window = None
        self.play_pause_btn = None
        self.step_label_var = None
        self.action_label_var = None # New variable for the action type label
        self.thumbnail_label = None
        self.full_screenshot_window = None
        self.full_screenshot_photo = None
        self.current_step_data = None
        self.next_step_callback = next_step_callback
        self.previous_step_callback = previous_step_callback
        self.toggle_pause_callback = toggle_pause_callback
        self.end_playback_callback = end_playback_callback
        self.drag_x = 0
        self.drag_y = 0
        self.thumbnail_photo = None

    def create_control_window(self):
        """Creates a small, always-on-top control window for playback."""
        if self.control_window:
            self.destroy_control_window()
        
        self.control_window = tk.Toplevel(self.parent)
        self.control_window.title("Tutorial Controls")
        self.control_window.attributes('-topmost', True)
        self.control_window.overrideredirect(True)
        self.control_window.resizable(False, False)

        style = ttk.Style()
        style.configure("Borderless.TFrame", padding=0)

        main_frame = ttk.Frame(self.control_window, padding=5)
        main_frame.pack(fill="both", expand=True)
        
        header_frame = ttk.Frame(main_frame, width=20)
        header_frame.pack(side="left", fill="y", padx=(0, 5))
        
        header_frame.bind("<ButtonPress-1>", self.on_drag_start)
        header_frame.bind("<B1-Motion>", self.on_drag_motion)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="left", fill="both", expand=True)

        # New Label for action type
        self.action_label_var = tk.StringVar()
        action_label = ttk.Label(control_frame, textvariable=self.action_label_var, font=("Arial", 10, "italic"))
        action_label.pack(pady=(0, 5))

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
        self.control_window.update_idletasks()
        win_width = self.control_window.winfo_reqwidth()
        self.control_window.geometry(f"+{screen_width - win_width - 10}+10")
        
    def on_drag_start(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag_motion(self, event):
        x = self.control_window.winfo_x() + event.x - self.drag_x
        y = self.control_window.winfo_y() + event.y - self.drag_y
        self.control_window.geometry(f"+{x}+{y}")
        
    def update_play_pause_button(self, text):
        if self.play_pause_btn:
            self.play_pause_btn.config(text=text)

    def get_control_window_rect(self):
        if not self.control_window:
            return None
        self.control_window.update_idletasks()
        x = self.control_window.winfo_x()
        y = self.control_window.winfo_y()
        width = self.control_window.winfo_width()
        height = self.control_window.winfo_height()
        return (x, y, x + width, y + height)
    
    def destroy_control_window(self):
        if self.control_window:
            self.control_window.destroy()
            self.control_window = None
        self.hide_full_screenshot()

    def update_step_display(self, step_info):
        if self.control_window:
            self.current_step_data = step_info
            
            info_text = f"Step {step_info['index'] + 1}/{step_info['total']}"
            if step_info.get("notes"):
                info_text += f"\n{step_info['notes']}"
            self.step_label_var.set(info_text)

            # Update the new action label
            action_text = step_info.get("action_type", "click").capitalize()
            self.action_label_var.set(action_text)

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

    def on_info_press(self, event):
        if self.current_step_data:
            full_screenshot_base64 = self.current_step_data.get("screenshot_base64")
            coordinates = self.current_step_data.get("recorded_coordinates")
            
            if full_screenshot_base64 and coordinates:
                full_data = base64.b64decode(full_screenshot_base64)
                full_screenshot = Image.open(io.BytesIO(full_data))
                self.show_full_screenshot(full_screenshot, coordinates)
            else:
                print("Full screenshot data is not available.")

    def on_info_release(self, event):
        self.hide_full_screenshot()

    def show_full_screenshot(self, screenshot_image, coordinates):
        if self.full_screenshot_window:
            return
            
        self.full_screenshot_window = tk.Toplevel(self.parent)
        self.full_screenshot_window.attributes('-topmost', True)
        self.full_screenshot_window.overrideredirect(True)

        draw = ImageDraw.Draw(screenshot_image)
        radius = 50
        x, y = coordinates
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="red", width=10)
        
        self.full_screenshot_photo = ImageTk.PhotoImage(screenshot_image)
        label = tk.Label(self.full_screenshot_window, image=self.full_screenshot_photo)
        label.pack()
        
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        win_width = screenshot_image.width
        win_height = screenshot_image.height
        x_pos = (screen_width - win_width) // 2
        y_pos = (screen_height - win_height) // 2
        self.full_screenshot_window.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")

    def hide_full_screenshot(self):
        if self.full_screenshot_window:
            self.full_screenshot_window.destroy()
            self.full_screenshot_window = None