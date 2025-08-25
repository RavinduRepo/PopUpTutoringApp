# controllers/recorder_controller.py
import json
import os
import time
from datetime import datetime
from pathlib import Path
import pynput
from pynput import mouse, keyboard
import pyautogui
import mss
from PIL import Image, ImageDraw
from tkinter import messagebox, filedialog
from views.recorder_mini_view import RecorderMiniView
import cv2
import numpy as np
import base64
import io
import sys
import logging
logger = logging.getLogger(__name__)

from .base_controller import BaseController # New import
# from utils.image_utility import get_base_path # You can move this utility function here
class RecorderController(BaseController): # Inherit from BaseController

    def __init__(self, main_controller, event_listener):
        super().__init__(main_controller, event_listener) # Initialize the parent class
        self.is_recording = False
        self.is_paused = False
        self.steps = []
        self.recorder_mini_view = None
        self.save_file_path = None
        self.tutorial_name = ""
        self.current_step_data = None
        
        pyautogui.FAILSAFE = False
        self.ignored_shortcuts = set()
        self.load_shortcuts()

    def load_shortcuts(self):
        """Loads shortcut key combinations from settings.json to be ignored during recording."""
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'settings.json')
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            shortcuts = settings.get('shortcuts', {})
            self.ignored_shortcuts = set(shortcuts.values())
            logger.info(f"Ignored shortcuts: {self.ignored_shortcuts}")
        except Exception as e:
            logger.warning(f"Could not load shortcuts from settings.json: {e}")
            self.ignored_shortcuts = set()

    def setup_subscriptions(self):
        """Subscribes to events from the EventListener."""
        self.event_listener.subscribe_mouse('single_click', self.on_click)
        self.event_listener.subscribe_mouse('double_click', self.on_click)
        self.event_listener.subscribe_keyboard('hotkey', self.on_hotkey)
        self.event_listener.subscribe_keyboard('typing', self.on_typing)
    
    def start_recording(self):
        """Starts a new tutorial recording and sets the save path."""
        if self.is_recording:
            return False

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Tutorial As"
        )
        if file_path:
            tutorial_name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            tutorial_name = ""
            return False

        self.steps = []
        self.is_recording = True
        self.is_paused = False
        self.save_file_path = file_path
        self.tutorial_name = tutorial_name
        self.current_step_data = None
        
        self.recorder_mini_view = RecorderMiniView(
            parent=self.main_controller,
            toggle_pause_callback=self.toggle_pause,
            stop_recording_callback=self.stop_recording,
            undo_last_step_callback=self.undo_last_step
        )
        self.recorder_mini_view.create_window()
        self.recorder_mini_view.update_view(len(self.steps), self.is_paused, None)
        
        self.main_controller.iconify()

        self.setup_subscriptions()
        self.start_event_listener() # Use the method from the base class
        
        self.main_controller.views['record'].update_ui_state(True)
        self.main_controller.views['record'].update_status(f"Recording '{self.tutorial_name}'... Use F9 to pause/resume, F10 to undo.")
        
        logger.info(f"Recording started. Saving to {self.save_file_path}")
        return True

    def stop_recording(self):
        """Stops the recording and saves the tutorial to the predetermined path."""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        self.is_paused = False

        self.stop_event_listener() # Use the method from the base class

        if self.recorder_mini_view:
            self.recorder_mini_view.destroy_window()

        self.main_controller.deiconify()
        
        if not self.steps:
            messagebox.showinfo("Recording Stopped", "No steps were recorded.")
            logger.info("No steps were recorded.")
            self.save_file_path = None
            self.main_controller.views['record'].update_ui_state(False)
            self.main_controller.views['record'].update_status("Recording stopped.")
            self.main_controller.views['record'].update_step_count(0)
            return None
        
        tutorial_data = {
            "name": self.tutorial_name,
            "created": datetime.now().isoformat(),
            "steps": self.steps,
            "version": "v1.2.0"
        }
        
        try:
            if self.save_file_path:
                with open(self.save_file_path, 'w') as f:
                    json.dump(tutorial_data, f, indent=2)
                messagebox.showinfo("Success", f"Tutorial saved successfully to {self.save_file_path}")
            else:
                messagebox.showerror("Save Error", "No save path was specified.")
        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving the tutorial: {e}")
        logger.info(f"Tutorial saved to: {self.save_file_path}")
        self.save_file_path = None
        self.main_controller.views['record'].update_ui_state(False)
        self.main_controller.views['record'].update_status("Recording stopped.")
        self.main_controller.views['record'].update_step_count(0)
        
        return self.save_file_path

    def toggle_pause(self):
        """Toggles the recording pause state."""
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"
        logger.info(f"Recording {status}")
        self.main_controller.views['record'].update_status(f"Recording {status}.")
        thumb_image = None
        if self.current_step_data and self.current_step_data.get('thumb'):
            thumb_data = base64.b64decode(self.current_step_data['thumb'])
            thumb_image = Image.open(io.BytesIO(thumb_data))
        self.recorder_mini_view.update_view(len(self.steps), self.is_paused, thumb_image)

    def undo_last_step(self):
        """Removes the last recorded step."""
        if self.steps:
            last_step = self.steps.pop()
            self.current_step_data = self.steps[-1] if self.steps else None
            logger.info("Undone last step.")
            logger.debug(last_step)
        
        thumb_image = None
        if self.current_step_data and self.current_step_data.get('thumb'):
            thumb_data = base64.b64decode(self.current_step_data['thumb'])
            thumb_image = Image.open(io.BytesIO(thumb_data))

        self.recorder_mini_view.set_current_step_data(self.current_step_data)
        self.recorder_mini_view.update_view(len(self.steps), self.is_paused, thumb_image)
        self.main_controller.views['record'].update_step_count(len(self.steps))
        return last_step

    def on_click(self, data):
        """Handles a single click event from the listener."""
        if not self.is_recording or self.is_paused:
            return
        
        x, y , type = data['x'], data['y'], data['button']
        
        if self.is_click_on_app_window(x, y):
            logger.debug("Click detected on app window, ignoring.")
            return
        if type == "double_click":
            self.undo_last_step()

        self.capture_step(x, y, type)

    def on_typing(self, data):
        """Handles a typing event from the listener."""
        if not self.is_recording or self.is_paused:
            return
        text = data['message']
        logger.info(f"Recorded typing: {data['message']}")
        self.capture_step(0, 0, action_type="typing", text=text)

    def on_hotkey(self, data):
        """Handles a hotkey event from the listener. Saves pressed keys and ignores shortcuts from settings.json."""
        if not self.is_recording:
            return
        key_combo = data.get('key')
        if self.is_my_shortcut(key_combo):
            logger.info(f"Ignored shortcut: {key_combo}")
            return
        self.capture_step(0, 0, action_type="shortcut", keys=key_combo)

    def is_my_shortcut(self, key_combo):
        """Returns True if the given key_combo is in the ignored shortcuts.
            and executes the associated action.
        """
        if key_combo == 'f9':
            self.toggle_pause()
        elif key_combo == 'f10':
            self.undo_last_step()
        return key_combo in self.ignored_shortcuts
    
    def is_click_on_app_window(self, x, y):
        """Checks if the click coordinates are within any of the app's windows."""
        if super().is_click_on_app_window(x, y): # Call the parent method first
            return True
            
        if self.recorder_mini_view and self.recorder_mini_view.window:
            mini_view_rect = self.get_window_rect(self.recorder_mini_view.window)
            if mini_view_rect[0] <= x <= mini_view_rect[2] and \
               mini_view_rect[1] <= y <= mini_view_rect[3]:
                return True
                
        return False

    def capture_step(self, x, y, action_type='left_click', text='', keys='', notes=''):
        """Captures a screenshot and saves the step data as a Base64 string."""
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[0])
                full_image = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            thumb_size = max(48, min(100, full_image.width // 10, full_image.height // 10))
            left = max(0, x - thumb_size // 2)
            top = max(0, y - thumb_size // 2)
            right = min(full_image.width, x + thumb_size // 2)
            bottom = min(full_image.height, y + thumb_size // 2)
            cropped_image = full_image.crop((left, top, right, bottom))
            
            buffered = io.BytesIO()
            full_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            thumb_buffered = io.BytesIO()
            cropped_image.save(thumb_buffered, format="PNG")
            thumb_str = base64.b64encode(thumb_buffered.getvalue()).decode('utf-8')
            
            step_num = len(self.steps) + 1
            
            step = {
                "step_number": step_num,
                "action_type": action_type,
                "screenshot": img_str,
                "thumb": thumb_str,
                "text": text, # typed text in the step
                "keys": keys, # hot keys
                "coordinates": [x, y],
                "timestamp": datetime.now().isoformat(),
                "notes": notes # additional notes typed
            }
            
            self.steps.append(step)
            self.current_step_data = step
            logger.info(f"Captured step {step_num} at ({x}, {y}) with action: {action_type}, text: {text}, keys: {keys}")
            
            self.recorder_mini_view.set_current_step_data(self.current_step_data)
            self.recorder_mini_view.update_view(len(self.steps), self.is_paused, cropped_image)
            self.main_controller.views['record'].update_step_count(step_num)

        except Exception as e:
            logger.warning(f"Error capturing step: {e}")
            messagebox.showerror("Capture Error", f"An error occurred while capturing a step: {e}")