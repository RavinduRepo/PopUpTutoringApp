# controllers/recorder_controller.py
import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
import pynput
from pynput import mouse, keyboard
import pyautogui
import mss
from PIL import Image
from tkinter import messagebox, filedialog
from views.recorder_mini_view import RecorderMiniView
import cv2
import numpy as np
import base64
import io
import sys

def get_base_path():
    """Gets the base path for resources, whether running in PyInstaller or as a script."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'data')
    return os.getcwd()

class RecorderController:

    def __init__(self, main_controller, event_listener):
        self.main_controller = main_controller
        self.event_listener = event_listener
        self.listener_thread = None # keeps the event listener's new thread of running the listener
        self.is_recording = False
        self.is_paused = False
        self.steps = []
        self.recorder_mini_view = None
        self.save_file_path = None # Stores the file path for saving
        self.tutorial_name = ""
        
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
            # Normalize to a set of key combos (as strings)
            self.ignored_shortcuts = set(shortcuts.values())
            # print the ignored shortcuts for debugging
            print(f"Ignored shortcuts: {self.ignored_shortcuts}")
        except Exception as e:
            print(f"Could not load shortcuts from settings.json: {e}")
            self.ignored_shortcuts = set()
    """Manages the recording of user interactions."""

    def setup_subscriptions(self):
        """Subscribes to events from the EventListener."""
        self.event_listener.subscribe_mouse('single_click', self.on_click) # dispite of the click type as long as its a single click
        self.event_listener.subscribe_mouse('double_click', self.on_click) # for double click
        self.event_listener.subscribe_keyboard('hotkey', self.on_hotkey)
        self.event_listener.subscribe_keyboard('typing', self.on_typing)
    
    def start_recording(self):
        """Starts a new tutorial recording and sets the save path."""
        if self.is_recording:
            return False

        tutorial_name = self.main_controller.views['record'].tutorial_name_var.get().strip()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Tutorial As",
            initialfile=tutorial_name
        )
        
        if not file_path:
            return False

        self.steps = []
        self.is_recording = True
        self.is_paused = False
        self.save_file_path = file_path
        self.tutorial_name = tutorial_name
        
        self.recorder_mini_view = RecorderMiniView(
            parent=self.main_controller,
            toggle_pause_callback=self.toggle_pause,
            stop_recording_callback=self.stop_recording,
            undo_last_step_callback=self.undo_last_step
        )
        self.recorder_mini_view.create_window()
        
        self.main_controller.iconify()

        if self.listener_thread is None or not self.listener_thread.is_alive():
            # Subscribing is now done here, right before the listener starts
            self.setup_subscriptions()
            
            self.listener_thread = threading.Thread(target=self.event_listener.start_listening, daemon=True)
            self.listener_thread.start()
        
        self.main_controller.views['record'].update_ui_state(True)
        self.main_controller.views['record'].update_status(f"Recording '{self.tutorial_name}'... Use F9 to pause/resume, F10 to undo.")
        
        print(f"Recording started. Saving to {self.save_file_path}")
        return True

    def stop_recording(self):
        """Stops the recording and saves the tutorial to the predetermined path."""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        self.is_paused = False

        if self.listener_thread and self.listener_thread.is_alive():
            self.event_listener.stop_listening()
            self.listener_thread.join()
            self.listener_thread = None

        if self.recorder_mini_view:
            self.recorder_mini_view.destroy_window()

        self.main_controller.deiconify()
        
        if not self.steps:
            messagebox.showinfo("Recording Stopped", "No steps were recorded.")
            self.save_file_path = None
            self.main_controller.views['record'].update_ui_state(False)
            self.main_controller.views['record'].update_status("Recording stopped.")
            self.main_controller.views['record'].update_step_count(0)
            return None
        
        tutorial_data = {
            "name": self.tutorial_name,
            "created": datetime.now().isoformat(),
            "steps": self.steps,
            "version": "v1.0.3"
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
        print(f"Tutorial saved to: {self.save_file_path}")
        self.save_file_path = None
        self.main_controller.views['record'].update_ui_state(False)
        self.main_controller.views['record'].update_status("Recording stopped.")
        self.main_controller.views['record'].update_step_count(0)
        
        return self.save_file_path

    def toggle_pause(self):
        """Toggles the recording pause state."""
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"
        print(f"Recording {status}")
        self.main_controller.views['record'].update_status(f"Recording {status}.")
        self.recorder_mini_view.update_pause_button(self.is_paused)

    def undo_last_step(self):
        """Removes the last recorded step."""
        if self.steps:
            last_step = self.steps.pop()
            print("Undone last step.")
            print(last_step)
        self.main_controller.views['record'].update_step_count(len(self.steps))
        return last_step

    def on_click(self, data):
        """Handles a single click event from the listener."""
        if not self.is_recording or self.is_paused:
            return
        
        x, y , type = data['x'], data['y'], data['button']
        
        if self.is_click_on_app_window(x, y):
            print("Click detected on app window, ignoring.")
            return
        if type == "double_click":
            self.undo_last_step() # erasing the single click recorded when double clicks first click

        self.capture_step(x, y, type)

    def on_typing(self, data):
        """Handles a typing event from the listener."""
        if not self.is_recording or self.is_paused:
            return
        text = data['message']
        print(f"Recorded typing: {data['message']}")
        self.capture_step(0, 0, action_type="typing", text=text) # x, y cordinations are 0 since they do not matter

    def on_hotkey(self, data):
        """Handles a hotkey event from the listener. Saves pressed keys and ignores shortcuts from settings.json."""
        if not self.is_recording:
            return
        key_combo = data.get('key')
        # If the key combo is in the ignored shortcuts, do not record it
        if self.is_my_shortcut(key_combo):
            print(f"Ignored shortcut: {key_combo}")
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
                # Capture the full screen first as it's the main reference
                screenshot = sct.grab(sct.monitors[0])
                full_image = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            # Now, generate the thumbnail from the full image for accuracy
            # size dynamic based on screen size
            thumb_size = max(48, min(100, full_image.width // 10, full_image.height // 10))
            left = max(0, x - thumb_size // 2)
            top = max(0, y - thumb_size // 2)
            right = min(full_image.width, x + thumb_size // 2)
            bottom = min(full_image.height, y + thumb_size // 2)
            cropped_image = full_image.crop((left, top, right, bottom))
            
            # Convert images to Base64
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
            print(f"Captured step {step_num} at ({x}, {y}) with action: {action_type}, text: {text}, keys: {keys}")
            self.main_controller.views['record'].update_step_count(step_num)

        except Exception as e:
            print(f"Error capturing step: {e}")
            messagebox.showerror("Capture Error", f"An error occurred while capturing a step: {e}")