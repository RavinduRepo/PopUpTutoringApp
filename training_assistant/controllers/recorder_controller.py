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
    """Manages the recording of user interactions."""

    def __init__(self, main_controller):
        self.main_controller = main_controller
        self.is_recording = False
        self.is_paused = False
        self.steps = []
        self.mouse_listener = None
        self.keyboard_listener = None
        self.hotkey_pressed = False
        self.recorder_mini_view = None
        self.save_file_path = None # Stores the file path for saving
        self.tutorial_name = ""
        
        # New variables for click detection
        self.last_click_time = None
        self.last_click_coords = None
        self.double_click_threshold = 0.4 # Time in seconds to distinguish double clicks
        
        pyautogui.FAILSAFE = False
        
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
        self.hotkey_pressed = False
        self.save_file_path = file_path
        self.tutorial_name = tutorial_name
        self.last_click_time = None # Reset state for new recording
        self.last_click_coords = None # Reset state for new recording
        
        self.recorder_mini_view = RecorderMiniView(
            parent=self.main_controller,
            toggle_pause_callback=self.toggle_pause,
            stop_recording_callback=self.stop_recording,
            undo_last_step_callback=self.undo_last_step
        )
        self.recorder_mini_view.create_window()
        
        self.main_controller.iconify()
        
        self.start_listeners()
        
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
        self.stop_listeners()
        
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
            "version": "2.0"
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
        
        self.save_file_path = None
        self.main_controller.views['record'].update_ui_state(False)
        self.main_controller.views['record'].update_status("Recording stopped.")
        self.main_controller.views['record'].update_step_count(0)
        
        print(f"Tutorial saved to: {self.save_file_path}")
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
            self.steps.pop()
            print("Undone last step.")
        self.main_controller.views['record'].update_step_count(len(self.steps))

    def start_listeners(self):
        """Starts background listeners for mouse and keyboard events."""
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
    
    def stop_listeners(self):
        """Stops the mouse and keyboard listeners."""
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
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

    def on_mouse_click(self, x, y, button, pressed):
        """Handles mouse clicks and captures a step."""
        if not self.is_recording or self.is_paused or not pressed:
            return
            
        if self.is_click_on_app_window(x, y):
            print("Click detected on app window, ignoring.")
            return

        if button == mouse.Button.left:
            current_time = time.time()
            if self.last_click_time and (current_time - self.last_click_time) < self.double_click_threshold:
                # This is a double-click
                self.steps[-1]['action_type'] = "double click"
                print(f"Updated last step to 'double click'")
                self.last_click_time = None
                self.last_click_coords = None
            else:
                # This is a single click. Capture immediately.
                self.capture_step(x, y, "click")
                self.last_click_time = current_time
                self.last_click_coords = (x, y)
        
        elif button == mouse.Button.right:
            # Handle right-click as a separate action
            self.capture_step(x, y, "right click")
            self.last_click_time = None
            self.last_click_coords = None

    def on_key_press(self, key):
        """Handles keyboard shortcuts for recording controls."""
        if not self.is_recording:
            return
            
        try:
            if key == keyboard.Key.f9:
                if not self.hotkey_pressed:
                    self.toggle_pause()
                    self.hotkey_pressed = True
            elif key == keyboard.Key.f10:
                if not self.hotkey_pressed:
                    self.undo_last_step()
                    self.hotkey_pressed = True
        except AttributeError:
            pass

    def on_key_release(self, key):
        """Resets the hotkey state on key release."""
        self.hotkey_pressed = False
    
    def capture_step(self, x, y, action_type):
        """Captures a screenshot and saves the step data as a Base64 string."""
        try:
            with mss.mss() as sct:
                # Capture the full screen first as it's the main reference
                screenshot = sct.grab(sct.monitors[0])
                full_image = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            # Now, generate the thumbnail from the full image for accuracy
            thumb_size = 50
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
                "coordinates": [x, y],
                "timestamp": datetime.now().isoformat(),
                "notes": ""
            }
            
            self.steps.append(step)
            print(f"Captured step {step_num} at ({x}, {y}) with action: {action_type}")
            self.main_controller.views['record'].update_step_count(step_num)

        except Exception as e:
            print(f"Error capturing step: {e}")
            messagebox.showerror("Capture Error", f"An error occurred while capturing a step: {e}")