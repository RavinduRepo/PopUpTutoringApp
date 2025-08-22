# controllers/player_controller.py

import json
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
from views.player_mini_view import PlayerView # Import the new PlayerView

class PlayerController:
    """Manages the playback of a recorded tutorial."""

    def __init__(self, main_controller, model):
        self.main_controller = main_controller
        self.model = model
        self.current_tutorial = None
        self.current_step_index = 0
        self.is_playing = False
        self.is_paused = False
        self.waiting_for_click = False
        self.mouse_listener = None
        self.control_window_rect = None
        
        self.tutorials_dir = os.path.join(os.getcwd(), 'tutorials')

        # Instantiate the view and pass necessary callbacks
        self.player_view = PlayerView(
            parent=self.main_controller,
            next_step_callback=self.next_step,
            previous_step_callback=self.previous_step,
            toggle_pause_callback=self.toggle_pause,
            end_playback_callback=self.end_playback
        )
        
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
        
        # Create the control window and get its geometry
        self.player_view.create_control_window()
        self.control_window_rect = self.player_view.get_control_window_rect()
        
        self.show_step()
        self.main_controller.views['play'].update_status("Playing")
        self.start_listener()

    def end_playback(self):
        """Ends the tutorial playback."""
        if not self.is_playing:
            return

        self.is_playing = False
        self.is_paused = False
        self.waiting_for_click = False
        self.stop_listener()
        self.player_view.destroy_overlay()
        self.player_view.destroy_control_window()
        
        messagebox.showinfo("Tutorial Complete", "Tutorial playback finished.")
        self.main_controller.views['play'].update_status("Idle")
        self.main_controller.show_play()

    def toggle_pause(self):
        """Toggles the playback pause state."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.player_view.update_play_pause_button("▶ Resume")
            self.player_view.destroy_overlay()
            self.main_controller.views['play'].update_status("Playback Paused")
        else:
            self.player_view.update_play_pause_button("⏸ Pause")
            self.show_step()
            self.main_controller.views['play'].update_status("Playing")
    
    def next_step(self):
        """Moves to the next step in the tutorial."""
        if self.is_playing and not self.is_paused:
            self.player_view.destroy_overlay()
            self.current_step_index += 1
            threading.Timer(0.3, self.show_step).start()

    def previous_step(self):
        """Moves to the previous step."""
        if self.is_playing and not self.is_paused:
            if self.current_step_index > 0:
                self.player_view.destroy_overlay()
                self.current_step_index -= 1
                self.show_step()
            else:
                messagebox.showinfo("Start of Tutorial", "You are at the first step.")
    
    def show_step(self):
        """Displays the current tutorial step with a transparent overlay."""
        if not self.is_playing or self.is_paused or self.current_step_index >= len(self.current_tutorial["steps"]):
            self.end_playback()
            return
        
        step = self.current_tutorial["steps"][self.current_step_index]
        step_info = {
            "index": self.current_step_index,
            "total": len(self.current_tutorial['steps']),
            "notes": step.get("notes"),
            "coordinates": step["coordinates"]
        }
        self.player_view.create_overlay(step_info)
        self.waiting_for_click = True
        
    def on_click(self, x, y, button, pressed):
        """Callback for the pynput mouse listener."""
        if not self.waiting_for_click or not pressed or button != mouse.Button.left or self.is_paused:
            return
        
        if self.control_window_rect and \
           self.control_window_rect[0] <= x <= self.control_window_rect[2] and \
           self.control_window_rect[1] <= y <= self.control_window_rect[3]:
            return
        
        self.waiting_for_click = False
        self.main_controller.after(100, self.next_step)
            
    def start_listener(self):
        """Starts a listener to detect clicks near the target coordinates."""
        self.stop_listener()
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
    
    def stop_listener(self): 
        """Stops the pynput listener."""
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
            self.mouse_listener = None
