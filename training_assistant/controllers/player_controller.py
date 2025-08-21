# controllers/player_controller.py

import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import mouse
from PIL import Image, ImageTk, ImageDraw

class PlayerController:
    """Manages the playback of a recorded tutorial."""

    def __init__(self, main_controller, model):
        self.main_controller = main_controller
        self.model = model
        self.current_tutorial = None
        self.current_step_index = 0
        self.is_playing = False
        self.is_paused = False
        self.overlay_window = None
        self.control_window = None
        self.waiting_for_click = False
        self.mouse_listener = None
        self.control_window_rect = None # New attribute to store control window geometry
        
        self.tutorials_dir = os.path.join(os.getcwd(), 'tutorials')

    def load_tutorial(self, tutorial_path):
        """Loads a tutorial from a JSON file."""
        if self.is_playing:
            messagebox.showwarning("Playback in Progress", "Please stop the current playback before loading a new tutorial.")
            return False

        try:
            with open(tutorial_path, 'r') as f:
                self.current_tutorial = json.load(f)
            self.current_step_index = 0
            return True
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load tutorial from '{tutorial_path}': {e}")
            self.current_tutorial = None
            return False

    def start_playback(self, from_start=True):
        """Starts the playback of the loaded tutorial."""
        if not self.current_tutorial:
            messagebox.showerror("Error", "No tutorial has been loaded.")
            return
        
        if self.is_playing:
            return
            
        self.is_playing = True
        self.is_paused = False
        if from_start:
            self.current_step_index = 0
        self.create_control_window()
        self.show_step()
        self.main_controller.views['play'].update_status("Playing")
        self.start_click_listener() # Start the listener here, keep it running

    def end_playback(self):
        """Ends the tutorial playback."""
        if not self.is_playing:
            return

        self.is_playing = False
        self.is_paused = False
        self.waiting_for_click = False
        self.stop_click_listener()
        self.destroy_overlay()
        self.destroy_control_window()
        
        messagebox.showinfo("Tutorial Complete", "Tutorial playback finished.")
        self.main_controller.views['play'].update_status("Idle")
        # Reset the play view to its initial state
        self.main_controller.show_play()

    def toggle_pause(self):
        """Toggles the playback pause state."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.play_pause_btn.config(text="▶ Resume")
            self.destroy_overlay()
            self.main_controller.views['play'].update_status("Playback Paused")
        else:
            self.play_pause_btn.config(text="⏸ Pause")
            self.show_step()
            self.main_controller.views['play'].update_status("Playing")
    
    def next_step(self):
        """Moves to the next step in the tutorial."""
        if self.is_playing and not self.is_paused:
            self.destroy_overlay()
            self.current_step_index += 1
            # Use a timer to prevent race conditions and provide a slight visual delay
            threading.Timer(0.3, self.show_step).start()

    def previous_step(self):
        """Moves to the previous step."""
        if self.is_playing and not self.is_paused:
            if self.current_step_index > 0:
                self.destroy_overlay()
                self.current_step_index -= 1
                self.show_step()
            else:
                messagebox.showinfo("Start of Tutorial", "You are at the first step.")
    
    def create_control_window(self):
        """Creates a small, always-on-top control window for playback."""
        if self.control_window:
            self.destroy_control_window()
        
        self.control_window = tk.Toplevel(self.main_controller)
        self.control_window.title("Tutorial Controls")
        self.control_window.geometry("200x200")
        self.control_window.attributes('-topmost', True)
        self.control_window.protocol("WM_DELETE_WINDOW", self.end_playback)
        self.control_window.resizable(True, True) # Set to True, True to enable resizing
        
        control_frame = ttk.Frame(self.control_window, padding=10)
        control_frame.pack(fill="both", expand=True)
        
        self.step_label_var = tk.StringVar()
        step_label = ttk.Label(control_frame, textvariable=self.step_label_var, font=("Arial", 12, "bold"))
        step_label.pack(pady=(0, 10))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="⏪ Back", command=self.previous_step, width=6).pack(side=tk.LEFT, padx=2)
        self.play_pause_btn = ttk.Button(button_frame, text="⏸ Pause", command=self.toggle_pause, width=6)
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="⏩ Next", command=self.next_step, width=6).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(control_frame, text="⏹ Stop", command=self.end_playback, style="Record.TButton", width=10).pack(pady=(10, 0))
        
        # Position window in the top right corner
        screen_width = self.main_controller.winfo_screenwidth()
        win_width = self.control_window.winfo_reqwidth()
        self.control_window.geometry(f"+{screen_width - win_width - 10}+10")
        
        # Update the control window's geometry
        self.main_controller.update_idletasks()
        x = self.control_window.winfo_x()
        y = self.control_window.winfo_y()
        width = self.control_window.winfo_width()
        height = self.control_window.winfo_height()
        self.control_window_rect = (x, y, x + width, y + height)
    
    def destroy_control_window(self):
        """Destroys the control window."""
        if self.control_window:
            self.control_window.destroy()
            self.control_window = None
            self.control_window_rect = None # Reset the geometry

    def show_step(self):
        """Displays the current tutorial step with a transparent overlay."""
        if not self.is_playing or self.is_paused or self.current_step_index >= len(self.current_tutorial["steps"]):
            self.end_playback()
            return
        
        step = self.current_tutorial["steps"][self.current_step_index]
        self.step_label_var.set(f"Step {self.current_step_index + 1}/{len(self.current_tutorial['steps'])}")
        
        self.create_overlay(step)
        self.waiting_for_click = True
        
    def create_overlay(self, step):
        """
        Creates a top-level window with a highlighted circle and no darkening.
        The window is transparent to clicks but provides visual feedback.
        """
        if self.overlay_window:
            self.destroy_overlay()
        
        self.overlay_window = tk.Toplevel(self.main_controller)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.overrideredirect(True)
        # Make the window transparent to mouse clicks
        self.overlay_window.wm_attributes('-transparentcolor', 'SystemButtonFace')
        
        screen_width = self.main_controller.winfo_screenwidth()
        screen_height = self.main_controller.winfo_screenheight()
        self.overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Use a canvas with a background that matches the transparent color
        canvas = tk.Canvas(self.overlay_window, bg='SystemButtonFace', highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        x, y = step["coordinates"]
        radius = 40
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline='red', width=5, fill='')
        
        info_text = f"Step {self.current_step_index + 1}/{len(self.current_tutorial['steps'])}"
        if step.get("notes"):
            info_text += f"\nNote: {step['notes']}"
        
        # Draw the text label on the canvas with a contrasting color
        canvas.create_text(x, y - 60, text=info_text, fill='white', font=('Arial', 14, 'bold'), anchor='s')
        
    def destroy_overlay(self):
        """Destroys the transparent overlay window."""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

    def on_click(self, x, y, button, pressed):
        """
        Callback for the pynput listener.
        It checks for a click and advances the step, but only if it's not on the control window.
        """
        if not self.waiting_for_click or not pressed or button != mouse.Button.left or self.is_paused:
            return
        
        # Check if the click is within the control window's bounds
        if self.control_window_rect and \
           self.control_window_rect[0] <= x <= self.control_window_rect[2] and \
           self.control_window_rect[1] <= y <= self.control_window_rect[3]:
            # Click is on the control window, do not advance step
            return
        
        # If the click is not on the control window, advance the step
        self.waiting_for_click = False
        self.main_controller.after(100, self.next_step)
        
    def start_click_listener(self):
        """Starts a listener to detect clicks near the target coordinates."""
        self.stop_click_listener()
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
    
    def stop_click_listener(self):
        """Stops the pynput listener."""
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
            self.mouse_listener = None
