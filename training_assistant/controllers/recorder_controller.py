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
from PIL import Image, ImageDraw
from tkinter import messagebox
from views.recorder_mini_view import RecorderMiniView
import cv2
import numpy as np

class RecorderController:
    """Manages the recording of user interactions."""

    def __init__(self, main_controller, model):
        self.main_controller = main_controller
        self.model = model
        self.is_recording = False
        self.is_paused = False
        self.steps = []
        self.tutorial_name = ""
        self.mouse_listener = None
        self.keyboard_listener = None
        self.hotkey_pressed = False
        self.recorder_mini_view = None
        
        self.tutorials_dir = os.path.join(os.getcwd(), 'tutorials')
        self.screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(self.tutorials_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        pyautogui.FAILSAFE = False
        
    def start_recording(self, tutorial_name):
        """Starts a new tutorial recording."""
        if self.is_recording:
            return False
        
        self.tutorial_name = tutorial_name.strip()
        if not self.tutorial_name:
            messagebox.showerror("Error", "Please enter a tutorial name.")
            return False

        self.steps = []
        self.is_recording = True
        self.is_paused = False
        self.hotkey_pressed = False
        
        tutorial_screenshot_dir = os.path.join(self.screenshots_dir, self.tutorial_name)
        os.makedirs(tutorial_screenshot_dir, exist_ok=True)
        
        self.recorder_mini_view = RecorderMiniView(
            parent=self.main_controller,
            toggle_pause_callback=self.toggle_pause,
            stop_recording_callback=self.stop_recording,
            undo_last_step_callback=self.undo_last_step
        )
        self.recorder_mini_view.create_window()
        
        self.start_listeners()
        print(f"Recording started for: {self.tutorial_name}")
        return True

    def stop_recording(self):
        """Stops the recording and saves the tutorial."""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        self.is_paused = False
        self.stop_listeners()
        
        if self.recorder_mini_view:
            self.recorder_mini_view.destroy_window()

        if not self.steps:
            messagebox.showinfo("Recording Stopped", "No steps were recorded.")
            return None
        
        tutorial_data = {
            "name": self.tutorial_name,
            "created": datetime.now().isoformat(),
            "steps": self.steps,
            "version": "1.0"
        }
        
        tutorial_filename = f"{self.tutorial_name.replace(' ', '_')}.json"
        tutorial_path = os.path.join(self.tutorials_dir, tutorial_filename)
        
        with open(tutorial_path, 'w') as f:
            json.dump(tutorial_data, f, indent=2)
            
        print(f"Tutorial saved: {tutorial_path}")
        messagebox.showinfo("Success", f"Tutorial '{self.tutorial_name}' saved successfully!")
        return tutorial_path

    def toggle_pause(self):
        """Toggles the recording pause state."""
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"
        print(f"Recording {status}")
        self.main_controller.views['record'].update_status(status)
        if self.recorder_mini_view:
            self.recorder_mini_view.update_pause_button(self.is_paused)

    def undo_last_step(self):
        """Removes the last recorded step and its screenshot."""
        if self.steps:
            removed_step = self.steps.pop()
            try:
                # Also remove the full screenshot and the thumbnail
                screenshot_path = os.path.join(self.screenshots_dir, removed_step["screenshot"])
                thumb_path = os.path.join(self.screenshots_dir, removed_step["thumb_path"])
                os.remove(screenshot_path)
                os.remove(thumb_path)
                print(f"Undone step {removed_step['step_number']}")
            except FileNotFoundError:
                print("Screenshot or thumbnail file not found, but step removed from list.")
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
            self.capture_step(x, y)

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
    
    def capture_step(self, x, y):
        """Captures a screenshot and saves the step data."""
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[0])
                full_image = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            step_num = len(self.steps) + 1
            
            tutorial_screenshot_dir = os.path.join(self.screenshots_dir, self.tutorial_name)
            
            screenshot_filename = f"{self.tutorial_name.replace(' ', '_')}_step_{step_num}_{int(time.time())}.png"
            thumb_filename = f"{self.tutorial_name.replace(' ', '_')}_thumb_{step_num}_{int(time.time())}.png"
            
            screenshot_path = os.path.join(tutorial_screenshot_dir, screenshot_filename)
            thumb_path = os.path.join(tutorial_screenshot_dir, thumb_filename)
            
            full_image.save(screenshot_path)

            thumb_size = 50
            left = max(0, x - thumb_size // 2)
            top = max(0, y - thumb_size // 2)
            right = min(full_image.width, x + thumb_size // 2)
            bottom = min(full_image.height, y + thumb_size // 2)
            
            cropped_image = full_image.crop((left, top, right, bottom))
            cropped_image.save(thumb_path)
            
            # Store the path relative to the screenshots directory
            relative_screenshot_path = os.path.join(self.tutorial_name, screenshot_filename)
            relative_thumb_path = os.path.join(self.tutorial_name, thumb_filename)
            
            step = {
                "step_number": step_num,
                "screenshot": relative_screenshot_path,
                "thumb_path": relative_thumb_path,
                "coordinates": [x, y],
                "timestamp": datetime.now().isoformat(),
                "notes": ""
            }
            
            self.steps.append(step)
            print(f"Captured step {step_num} at ({x}, {y})")
            self.main_controller.views['record'].update_step_count(step_num)

        except Exception as e:
            print(f"Error capturing step: {e}")
            messagebox.showerror("Capture Error", f"An error occurred while capturing a step: {e}")
            