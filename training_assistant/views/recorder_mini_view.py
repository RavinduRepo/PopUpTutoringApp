# views/recorder_mini_view.py
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
import os
import sys
import logging
from .mini_view_base import MiniViewBase

logger = logging.getLogger(__name__)

def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class RecorderMiniView(MiniViewBase):
    """A minimal, always-on-top control window for the recorder."""

    def __init__(
        self,
        parent,
        toggle_pause_callback,
        stop_recording_callback,
        undo_last_step_callback,
        audio_option="No Audio",
    ):
        super().__init__(parent)
        self.pause_btn = None
        self.toggle_pause_callback = toggle_pause_callback
        self.stop_recording_callback = stop_recording_callback
        self.undo_last_step_callback = undo_last_step_callback
        self.audio_option = audio_option

        self.step_label_var = None
        self.thumbnail_label = None
        self.thumbnail_photo = None
        self.info_btn = None
        self.audio_for_step_var = tk.BooleanVar(value=True)
        self.audio_checkbutton = None

    def create_window(self):
        """Creates and displays the mini control window."""
        main_frame, header_frame = self.create_base_window("Recorder Controls")
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="left", fill="both", expand=True)
        
        self.step_label_var = tk.StringVar()
        step_label = ttk.Label(control_frame, textvariable=self.step_label_var, font=("Arial", 12, "bold"))
        step_label.pack(pady=(0, 10))
        
        self.thumbnail_label = ttk.Label(control_frame)
        self.thumbnail_label.pack(pady=(0, 10))

        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.info_btn = ttk.Button(button_frame, text="ℹ️", width=3)
        self.info_btn.pack(side=tk.LEFT, padx=5)
        self.info_btn.bind("<ButtonPress-1>", self.on_info_press)
        self.info_btn.bind("<ButtonRelease-1>", self.on_info_release)

        self.pause_btn = ttk.Button(
            button_frame,
            text="⏸ Pause",
            command=self.toggle_pause_callback
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        self.undo_btn = ttk.Button(
            button_frame,
            text="← Back",
            command=self.undo_last_step_callback
        )
        self.undo_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_recording_callback
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        if self.audio_option == "Include Audio":
            self.audio_checkbutton = ttk.Checkbutton(
                control_frame,
                text="Record Audio",
                variable=self.audio_for_step_var,
                onvalue=True,
                offvalue=False,
            )
            self.audio_checkbutton.pack(pady=5)

        self.parent.update_idletasks()
        self.window.geometry(f"+10+10")

    def get_audio_var(self):
        return self.audio_for_step_var
        
    def update_pause_button(self, is_paused):
        """Updates the text on the pause button based on state."""
        if self.pause_btn:
            self.pause_btn.config(text="▶ Resume" if is_paused else "⏸ Pause")

    def update_view(self, step_count, is_paused, thumbnail_image=None):
        """Updates the step count, pause button text, and thumbnail image."""
        self.update_pause_button(is_paused)
        self.step_label_var.set(f"Step: {step_count}")
        
        if thumbnail_image:
            self.thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)
            self.thumbnail_label.config(image=self.thumbnail_photo)
        else:
            self.thumbnail_label.config(image='')