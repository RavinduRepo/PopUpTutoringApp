import json
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from pynput import mouse
from views.player_mini_view import PlayerMiniView
import cv2
import numpy as np
import mss
from PIL import Image

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
        self.screenshots_dir = os.path.join(os.getcwd(), 'screenshots')

        self.player_view = PlayerMiniView(
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
    
    def get_window_rect(self, window):
        """Gets the bounding box of a Tkinter window."""
        window.update_idletasks()
        x = window.winfo_rootx()
        y = window.winfo_rooty()
        width = window.winfo_width()
        height = window.winfo_height()
        return (x, y, x + width, y + height)
        
    def is_click_on_app_window(self, x, y):
        """Checks if the click coordinates are within any of the app's windows."""
        # Check main window
        main_window_rect = self.get_window_rect(self.main_controller)
        if main_window_rect[0] <= x <= main_window_rect[2] and \
           main_window_rect[1] <= y <= main_window_rect[3]:
            return True
            
        # Check mini-view window
        if self.player_view and self.player_view.control_window:
            mini_view_rect = self.get_window_rect(self.player_view.control_window)
            if mini_view_rect[0] <= x <= mini_view_rect[2] and \
               mini_view_rect[1] <= y <= mini_view_rect[3]:
                return True
                
        return False

    def show_step(self):
        """Displays the current tutorial step with a transparent overlay."""
        if not self.is_playing or self.is_paused or self.current_step_index >= len(self.current_tutorial["steps"]):
            self.end_playback()
            return
        
        step = self.current_tutorial["steps"][self.current_step_index]
        current_coordinates = list(step["coordinates"])
        
        thumbnail_path = os.path.join(self.screenshots_dir, step["thumb_path"])
        
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                screenshot = sct.grab(monitor)
            
            # Convert the screenshot from BGRA to grayscale
            current_screen_np = np.array(screenshot, dtype=np.uint8)
            current_screen_gray = cv2.cvtColor(current_screen_np, cv2.COLOR_BGRA2GRAY)

            # Load the thumbnail and convert it to grayscale
            thumbnail = cv2.imread(thumbnail_path)
            
            if thumbnail is not None:
                thumbnail_gray = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2GRAY)

                # Perform template matching on grayscale images
                result = cv2.matchTemplate(current_screen_gray, thumbnail_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if max_val > 0.8:
                    thumb_h, thumb_w = thumbnail_gray.shape
                    new_x = max_loc[0] + thumb_w // 2
                    new_y = max_loc[1] + thumb_h // 2
                    current_coordinates = [new_x, new_y]
                    print(f"Match found! New coordinates: ({new_x}, {new_y})")
                else:
                    print("No strong match found, using recorded coordinates.")
            else:
                print(f"Thumbnail image not found at {thumbnail_path}, using recorded coordinates.")
        except Exception as e:
            print(f"Error during template matching: {e}. Using recorded coordinates.")
            
        step_info = {
            "index": self.current_step_index,
            "total": len(self.current_tutorial['steps']),
            "notes": step.get("notes"),
            "coordinates": current_coordinates,
            "thumb_path": thumbnail_path
        }
        
        self.player_view.update_step_display(step_info)
        self.player_view.create_overlay(step_info)
        self.waiting_for_click = True
        
    def on_click(self, x, y, button, pressed):
        """Callback for the pynput mouse listener."""
        if not self.waiting_for_click or not pressed or button != mouse.Button.left or self.is_paused:
            return
        
        if self.is_click_on_app_window(x, y):
            print("Click detected on app window, ignoring.")
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