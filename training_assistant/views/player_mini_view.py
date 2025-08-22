# views/player_view.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

class PlayerView:
    """Handles the UI for the tutorial playback."""

    def __init__(self, parent, next_step_callback, previous_step_callback, toggle_pause_callback, end_playback_callback):
        self.parent = parent
        self.control_window = None
        self.overlay_window = None
        self.play_pause_btn = None
        self.step_label_var = None
        self.next_step_callback = next_step_callback
        self.previous_step_callback = previous_step_callback
        self.toggle_pause_callback = toggle_pause_callback
        self.end_playback_callback = end_playback_callback
        
        # Variables for dragging the window
        self.drag_x = 0
        self.drag_y = 0

    def create_control_window(self):
        """Creates a small, always-on-top control window for playback."""
        if self.control_window:
            self.destroy_control_window()
        
        self.control_window = tk.Toplevel(self.parent)
        self.control_window.title("Tutorial Controls")
        self.control_window.attributes('-topmost', True)
        self.control_window.overrideredirect(True) # Remove window decorations
        self.control_window.resizable(False, False) # Non-resizable

        # Main frame for content with a grid layout
        main_frame = ttk.Frame(self.control_window, padding=5)
        main_frame.pack(fill="both", expand=True)
        
        # Draggable header frame on the left
        header_frame = ttk.Frame(main_frame, width=30)
        header_frame.pack(side="left", fill="y", padx=(0, 5))
        
        # Bind dragging events to the header frame
        header_frame.bind("<ButtonPress-1>", self.on_drag_start)
        header_frame.bind("<B1-Motion>", self.on_drag_motion)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="left", fill="both", expand=True)
        
        self.step_label_var = tk.StringVar()
        step_label = ttk.Label(control_frame, textvariable=self.step_label_var, font=("Arial", 12, "bold"))
        step_label.pack(pady=(0, 10))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="⏪ Back", command=self.previous_step_callback, width=6).pack(side=tk.LEFT, padx=2)
        self.play_pause_btn = ttk.Button(button_frame, text="⏸ Pause", command=self.toggle_pause_callback, width=6)
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="⏩ Next", command=self.next_step_callback, width=6).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(control_frame, text="⏹ Stop", command=self.end_playback_callback, style="Record.TButton", width=10).pack(pady=(10, 0))
        
        # Position the window in the top-right corner
        screen_width = self.parent.winfo_screenwidth()
        self.control_window.update_idletasks()
        win_width = self.control_window.winfo_reqwidth()
        self.control_window.geometry(f"+{screen_width - win_width - 10}+10")
        
    def on_drag_start(self, event):
        """Records the initial position of the mouse for dragging."""
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag_motion(self, event):
        """Moves the window as the mouse is dragged."""
        # Calculate the new position of the window
        x = self.control_window.winfo_x() + event.x - self.drag_x
        y = self.control_window.winfo_y() + event.y - self.drag_y
        self.control_window.geometry(f"+{x}+{y}")
        
    def update_play_pause_button(self, text):
        """Updates the text on the play/pause button."""
        if self.play_pause_btn:
            self.play_pause_btn.config(text=text)

    def get_control_window_rect(self):
        """Returns the geometry of the control window."""
        if not self.control_window:
            return None
        self.parent.update_idletasks()
        x = self.control_window.winfo_x()
        y = self.control_window.winfo_y()
        width = self.control_window.winfo_width()
        height = self.control_window.winfo_height()
        return (x, y, x + width, y + height)
    
    def destroy_control_window(self):
        """Destroys the control window."""
        if self.control_window:
            self.control_window.destroy()
            self.control_window = None

    def create_overlay(self, step_info):
        """
        Creates a top-level window with a highlighted circle and no darkening.
        The window is transparent to clicks but provides visual feedback.
        """
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
        
        info_text = f"Step {step_info['index'] + 1}/{step_info['total']}"
        if step_info.get("notes"):
            info_text += f"\nNote: {step_info['notes']}"
        
        self.step_label_var.set(info_text)
        canvas.create_text(x, y - 60, text=info_text, fill='red', font=('Arial', 14, 'bold'), anchor='s')
        
    def destroy_overlay(self):
        """Destroys the transparent overlay window."""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
