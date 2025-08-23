# controllers/player_controller.py
import json
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog
from pynput import mouse
from views.player_mini_view import PlayerMiniView
import cv2
import numpy as np
import mss
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import sys

from utils.pdf_utility import convert_to_pdf

def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class PlayerController:
    """Manages the playback of a recorded tutorial."""

    def __init__(self, main_controller):
        self.main_controller = main_controller
        self.current_tutorial = None
        self.current_step_index = 0
        self.is_playing = False
        self.is_paused = False
        self.waiting_for_click = False
        self.mouse_listener = None
        
        self.player_view = PlayerMiniView(
            parent=self.main_controller,
            next_step_callback=self.next_step,
            previous_step_callback=self.previous_step,
            toggle_pause_callback=self.toggle_pause,
            end_playback_callback=self.end_playback
        )
        
    def load_tutorial_from_dialog(self):
        """Opens a file dialog and loads a tutorial from the selected file."""
        file_path = filedialog.askopenfilename(
            title="Select Tutorial File",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            if self.load_tutorial_by_path(file_path):
                self.main_controller.views['play'].update_ui_on_load(self.current_tutorial)

    def load_tutorial_by_path(self, file_path):
        """Loads a tutorial from a given JSON file path."""
        if self.is_playing:
            messagebox.showwarning("Playback in Progress", "Please stop the current playback before loading a new tutorial.")
            return False

        try:
            with open(file_path, 'r') as f:
                self.current_tutorial = json.load(f)
            self.current_step_index = 0
            messagebox.showinfo("Tutorial Loaded", f"Tutorial '{self.current_tutorial['name']}' loaded successfully.")
            return True
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load tutorial from '{file_path}': {e}")
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
        
        self.show_step()
        self.main_controller.views['play'].update_buttons_on_playback(True)
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
        self.main_controller.views['play'].update_buttons_on_playback(False)
        self.main_controller.views['play'].update_status("Idle")
        # Go back to the main view, not the play view
        self.main_controller.show_home() 

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
        main_window_rect = self.get_window_rect(self.main_controller)
        if main_window_rect[0] <= x <= main_window_rect[2] and \
           main_window_rect[1] <= y <= main_window_rect[3]:
            return True
            
        if self.player_view and self.player_view.control_window:
            mini_view_rect = self.get_window_rect(self.player_view.control_window)
            if mini_view_rect[0] <= x <= mini_view_rect[2] and \
               mini_view_rect[1] <= y <= mini_view_rect[3]:
                return True
                
        return False
        
    def _find_match_on_screen(self, template_image):
        """
        Finds the location of a smaller template image (thumbnail) on the live screen.
        Returns the top-left coordinates (x, y) of the best match.
        """
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[0])
            full_image_pil = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        
        full_image_np = np.array(full_image_pil)
        template_np = np.array(template_image)

        full_image_gray = cv2.cvtColor(full_image_np, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_np, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(full_image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.8:
            return max_loc
        else:
            return None

    def show_step(self):
        """
        Displays the current tutorial step.
        If a match is found, it will highlight the detected location.
        Otherwise, it will fall back to the recorded coordinates.
        """
        if not self.is_playing or self.is_paused or self.current_step_index >= len(self.current_tutorial["steps"]):
            self.end_playback()
            return
        
        step = self.current_tutorial["steps"][self.current_step_index]
        recorded_coordinates = list(step["coordinates"])
        
        thumb_data = base64.b64decode(step["thumb"])
        thumb_image = Image.open(io.BytesIO(thumb_data))
        
        full_screenshot_base64 = step.get("screenshot")
        
        detected_coordinates = self._find_match_on_screen(thumb_image)
        
        if detected_coordinates:
            print(f"Match found for step {self.current_step_index + 1} at {detected_coordinates}")
            thumb_w, thumb_h = thumb_image.size
            highlight_coordinates = (
                detected_coordinates[0] + thumb_w // 2,
                detected_coordinates[1] + thumb_h // 2
            )
            highlight_color = "green"
            highlight_radius = max(thumb_w, thumb_h) // 2 + 10
        else:
            print(f"No match found for step {self.current_step_index + 1}. Using recorded coordinates.")
            highlight_coordinates = recorded_coordinates
            highlight_color = "red"
            highlight_radius = 20

        step_info = {
            "index": self.current_step_index,
            "total": len(self.current_tutorial['steps']),
            "notes": step.get("notes"),
            "coordinates": highlight_coordinates,
            "thumb": thumb_image,
            "highlight_color": highlight_color,
            "highlight_radius": highlight_radius,
            "screenshot_base64": full_screenshot_base64,
            "recorded_coordinates": recorded_coordinates
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
    
    def convert_to_pdf(self):
        """Calls the utility function to create a PDF from the current tutorial."""
        if not self.current_tutorial:
            messagebox.showerror("Error", "No tutorial has been loaded to convert.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save PDF As",
            initialfile=f"{self.current_tutorial.get('name', 'tutorial')}.pdf"
        )
        
        if file_path:
            try:
                convert_to_pdf(self.current_tutorial, file_path)
                messagebox.showinfo("Success", f"PDF saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Conversion Error", f"An error occurred while creating the PDF: {e}")