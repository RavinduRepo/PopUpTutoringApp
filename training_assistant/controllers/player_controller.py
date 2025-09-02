# controllers/player_controller.py
import json
import threading
from tkinter import messagebox, filedialog
from views.player_mini_view import PlayerMiniView
import cv2
import numpy as np
import mss
from PIL import Image
import base64
import io
import logging
# Import the pyperclip library
import pyperclip 

logger = logging.getLogger(__name__)

from .base_controller import BaseController
from utils.pdf_utility import convert_to_pdf

class PlayerController(BaseController):
    """Manages the playback of a recorded tutorial."""

    def __init__(self, main_controller, event_listener):
        super().__init__(main_controller, event_listener)
        self.current_tutorial = None
        self.current_step_index = 0
        self.is_playing = False
        self.is_paused = False
        
        # Create the mini-view window
        self.player_mini_view = PlayerMiniView(
            parent=self.main_controller,
            next_step_callback=self.next_step,
            previous_step_callback=self.previous_step,
            toggle_pause_callback=self.toggle_pause,
            end_playback_callback=self.end_playback
        )

    def setup_subscriptions(self):
        """Subscribes to events from the EventListener."""
        self.event_listener.subscribe_mouse('single_click', self.on_single_click)
        self.event_listener.subscribe_mouse('double_click', self.on_double_click)
        self.event_listener.subscribe_keyboard('hotkey', self.on_hotkey)
        self.event_listener.subscribe_keyboard('typing', self.on_typing)
        
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
        
        self.player_mini_view.create_control_window()
        
        self.main_controller.iconify() 
        
        self.show_step()
        self.main_controller.views['play'].update_buttons_on_playback(True)
        self.main_controller.views['play'].update_status("Playing")
        self.setup_subscriptions()
        self.start_event_listener() # Use the method from the base class

    def end_playback(self):
        """Ends the tutorial playback."""
        if not self.is_playing:
            return

        self.is_playing = False
        self.is_paused = False
        
        self.stop_event_listener() # Use the method from the base class

        self.player_mini_view.destroy_overlay()
        self.player_mini_view.destroy_control_window()

        self.main_controller.deiconify()
        
        messagebox.showinfo("Tutorial Complete", "Tutorial playback finished.")
        self.main_controller.views['play'].update_buttons_on_playback(False)
        self.main_controller.views['play'].update_status("Idle")
        self.main_controller.show_home() 

    def toggle_pause(self):
        """Toggles the playback pause state."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.player_mini_view.update_play_pause_button("▶ Resume")
            self.player_mini_view.destroy_overlay()
            self.main_controller.views['play'].update_status("Playback Paused")
        else:
            self.player_mini_view.update_play_pause_button("⏸ Pause")
            self.show_step()
            self.main_controller.views['play'].update_status("Playing")
    
    def next_step(self):
        """Moves to the next step in the tutorial."""
        if self.is_playing and not self.is_paused:
            self.player_mini_view.destroy_overlay()
            self.current_step_index += 1
            threading.Timer(0.3, self.show_step).start()

    def previous_step(self):
        """Moves to the previous step."""
        if self.is_playing and not self.is_paused:
            if self.current_step_index > 0:
                self.player_mini_view.destroy_overlay()
                self.current_step_index -= 1
                self.show_step()
            else:
                messagebox.showinfo("Start of Tutorial", "You are at the first step.")
    
    def on_single_click(self, data):
        """Handles a single click event from the listener."""
        if self.is_paused or self.current_tutorial["steps"][self.current_step_index]["action_type"].lower() not in ['left_click', 'right_click']:
            return
        x, y = data['x'], data['y']
        
        if self.is_click_on_app_window(x, y):
            logger.info("Click detected on app window, ignoring.")
            return

        self.main_controller.after(100, self.next_step)
        
    def on_double_click(self, data):
        """Handles all double clicks"""
        if self.is_paused or self.current_tutorial["steps"][self.current_step_index]["action_type"].lower() not in ['double_click']:
            return
        x, y = data['x'], data['y']
        
        if self.is_click_on_app_window(x, y):
            logger.info("Click detected on app window, ignoring.")
            return

        self.main_controller.after(100, self.next_step)

    def on_typing(self, data):
        """Handles a typing event from the listener."""
        if self.is_paused or self.current_tutorial["steps"][self.current_step_index]["action_type"].lower() not in ['typing']:
            return
        
        self.main_controller.after(100, self.next_step)
        
    def on_hotkey(self, data):
        """Handles a hotkey event from the listener.
        This is where the player would react to specific playback hotkeys.
        """
        current_step = self.current_tutorial["steps"][self.current_step_index]
        action_type = current_step["action_type"].lower()
        key_combo = data.get('key')
        if self.is_my_shortcut(key_combo):
            logger.info(f"Ignored shortcut: {key_combo}")
            return
        if not self.is_paused and (action_type == 'shortcut' or (action_type == 'typing' and key_combo == 'ctrl+v')):
            self.main_controller.after(100, self.next_step)
    # --------------------------------------------------------------------------------------------------------------
    def is_my_shortcut(self, key_combo):# change this functuon based on available shortcuutws from key combos 
        """Returns True if the given key_combo is in the ignored shortcuts.
            and executes the associated action.
        """
        if key_combo == 'f9':
            self.toggle_pause()
        elif key_combo == 'f10':
            self.undo_last_step()
        return key_combo in self.ignored_shortcuts
    # --------------------------------------------------------------------------------------------------------------
    
    def is_click_on_app_window(self, x, y):
        """Checks if the click coordinates are within any of the app's windows."""
        if super().is_click_on_app_window(x, y): # Call the parent method first
            return True
            
        if self.player_mini_view and self.player_mini_view.window:
            mini_view_rect = self.get_window_rect(self.player_mini_view.window)
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
        
        action_type = step.get("action_type", "click")
        
        thumb_data = base64.b64decode(step["thumb"])
        thumb_image = Image.open(io.BytesIO(thumb_data))
        
        full_screenshot_base64 = step.get("screenshot")
        
        detected_coordinates = self._find_match_on_screen(thumb_image)
        
        if detected_coordinates:
            logger.info(f"Match found for step {self.current_step_index + 1} at {detected_coordinates}")
            thumb_w, thumb_h = thumb_image.size
            highlight_coordinates = (
                detected_coordinates[0] + thumb_w // 2,
                detected_coordinates[1] + thumb_h // 2
            )
            highlight_color = "red"
            highlight_radius = max(thumb_w, thumb_h) // 2 + 10
        else:
            logger.info(f"No match found for step {self.current_step_index + 1}. Using recorded coordinates.")
            highlight_coordinates = recorded_coordinates
            highlight_color = "gray"
            highlight_radius = 20

        logger.debug(f"\nusing cordinates are: {detected_coordinates}\n")
        step_info = {
            "index": self.current_step_index,
            "total": len(self.current_tutorial['steps']),
            "action_type": action_type, # Pass the action type to the view
            "notes": step.get("notes"),
            "text": step.get("text", ""), # Pass the typed text
            "keys": step.get("keys", ""), # Pass the keys
            "highlight_coordinates": highlight_coordinates, # coordinates to circle on play time
            "thumb": thumb_image,
            "highlight_color": highlight_color,
            "highlight_radius": highlight_radius,
            "screenshot": full_screenshot_base64,
            "recorded_coordinates": recorded_coordinates # coordinates recorded on record time
        }
        
        self.player_mini_view.update_step_display(step_info)
        
        if action_type.lower() in ['left_click', 'right_click', 'double_click']:
            self.player_mini_view.create_overlay(step_info)
        else:
            self.player_mini_view.destroy_overlay()
            if action_type.lower() == 'typing':
                # Get the text to be typed from the current step
                text_to_copy = self.current_tutorial["steps"][self.current_step_index].get("text", "")
                # Call the copy function
                self._copy_text_to_clipboard(text_to_copy)
    
    def _copy_text_to_clipboard(self, text):
        """Copies the given text to the system clipboard."""
        try:
            pyperclip.copy(text)
            logger.info(f"Copied text to clipboard: '{text}'")
        except Exception as e:
            logger.error(f"Failed to copy text to clipboard: {e}")

    def convert_to_pdf(self):
        """Calls the utility function to create a PDF from the current tutorial."""
        if not self.current_tutorial:
            messagebox.showerror("Error", "No tutorial has been loaded to convert.")
            return

        convert_to_pdf(self.current_tutorial)
        