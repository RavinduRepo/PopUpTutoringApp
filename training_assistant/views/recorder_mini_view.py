# views/recorder_mini_view.py
import tkinter as tk
from tkinter import ttk

class RecorderMiniView:
    """A minimal, always-on-top control window for the recorder."""

    def __init__(self, parent, toggle_pause_callback, stop_recording_callback, undo_last_step_callback):
        self.parent = parent
        self.window = None
        self.pause_btn = None # Make a reference to the pause button
        self.toggle_pause_callback = toggle_pause_callback
        self.stop_recording_callback = stop_recording_callback
        self.undo_last_step_callback = undo_last_step_callback
        
        # Variables for dragging the window
        self.drag_x = 0
        self.drag_y = 0

    def create_window(self):
        """Creates and displays the mini control window."""
        if self.window:
            self.destroy_window()

        self.window = tk.Toplevel(self.parent)
        self.window.title("Recorder Controls")
        self.window.attributes('-topmost', True)
        self.window.overrideredirect(True) # Remove window decorations
        self.window.resizable(False, False)
        
        main_frame = ttk.Frame(self.window, padding=5)
        main_frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_frame, width=30)
        header_frame.pack(side="left", fill="y", padx=(0, 5))
        
        header_frame.bind("<ButtonPress-1>", self.on_drag_start)
        header_frame.bind("<B1-Motion>", self.on_drag_motion)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="left", fill="both", expand=True)

        # Pause/Resume button
        self.pause_btn = ttk.Button(
            control_frame,
            text="⏸ Pause",
            command=self.toggle_pause_callback
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        # Undo button
        self.undo_btn = ttk.Button(
            control_frame,
            text="← Back",
            command=self.undo_last_step_callback
        )
        self.undo_btn.pack(side=tk.LEFT, padx=2)

        # Stop button
        self.stop_btn = ttk.Button(
            control_frame,
            text="⏹ Stop",
            command=self.stop_recording_callback
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.parent.update_idletasks()
        self.window.geometry(f"+10+10")
        
    def update_pause_button(self, is_paused):
        """Updates the text on the pause button based on state."""
        if self.pause_btn:
            self.pause_btn.config(text="▶ Resume" if is_paused else "⏸ Pause")

    def destroy_window(self, event=None):
        """Destroys the mini control window."""
        if self.window:
            self.window.destroy()
            self.window = None

    def on_drag_start(self, event):
        """Records the initial position of the mouse for dragging."""
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag_motion(self, event):
        """Moves the window as the mouse is dragged."""
        x = self.window.winfo_x() + event.x - self.drag_x
        y = self.window.winfo_y() + event.y - self.drag_y
        self.window.geometry(f"+{x}+{y}")