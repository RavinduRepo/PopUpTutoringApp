# views/mini_view_base.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import base64
import io
import logging

logger = logging.getLogger(__name__)

class MiniViewBase:
    """A base class for all mini-view windows to handle common UI and logic."""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.drag_x = 0
        self.drag_y = 0
        self.full_screenshot_window = None
        self.full_screenshot_photo = None
        self.current_step_data = None
        
        # Logging configuration is typically done in the main file
        # But we'll keep the logger here for each module

    def create_base_window(self, title):
        """Creates the base window with common properties."""
        self.window = tk.Toplevel(self.parent)
        self.window.title(title)
        self.window.attributes('-topmost', True)
        self.window.overrideredirect(True)
        self.window.resizable(False, False)

        main_frame = ttk.Frame(self.window, padding=5)
        main_frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_frame, width=30)
        header_frame.pack(side="left", fill="y", padx=(0, 5))
        header_frame.bind("<ButtonPress-1>", self.on_drag_start)
        header_frame.bind("<B1-Motion>", self.on_drag_motion)
        
        return main_frame, header_frame

    def on_drag_start(self, event):
        """Records the initial position of the mouse for dragging."""
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag_motion(self, event):
        """Moves the window as the mouse is dragged."""
        x = self.window.winfo_x() + event.x - self.drag_x
        y = self.window.winfo_y() + event.y - self.drag_y
        self.window.geometry(f"+{x}+{y}")

    def set_current_step_data(self, step_data):
        """Sets the data for the current step."""
        self.current_step_data = step_data

    def on_info_press(self, event):
        """Shows the full screenshot when the info button is pressed."""
        if self.current_step_data:
            full_screenshot_base64 = self.current_step_data.get("screenshot_base64") or self.current_step_data.get("screenshot")
            coordinates = self.current_step_data.get("recorded_coordinates") or self.current_step_data.get("coordinates")
            
            if full_screenshot_base64 and coordinates:
                full_data = base64.b64decode(full_screenshot_base64)
                full_screenshot = Image.open(io.BytesIO(full_data))
                self.show_full_screenshot(full_screenshot, coordinates)
            else:
                logger.info("Full screenshot data is not available.")

    def on_info_release(self, event):
        """Hides the full screenshot when the info button is released."""
        self.hide_full_screenshot()

    def show_full_screenshot(self, screenshot_image, coordinates):
        """Creates and displays a top-level window with the full screenshot."""
        if self.full_screenshot_window:
            return
            
        self.full_screenshot_window = tk.Toplevel(self.parent)
        self.full_screenshot_window.attributes('-topmost', True)
        self.full_screenshot_window.overrideredirect(True)

        draw = ImageDraw.Draw(screenshot_image)
        radius = 50
        x, y = coordinates
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="red", width=10)
        
        self.full_screenshot_photo = ImageTk.PhotoImage(screenshot_image)
        label = tk.Label(self.full_screenshot_window, image=self.full_screenshot_photo)
        label.pack()
        
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        win_width = screenshot_image.width
        win_height = screenshot_image.height
        x_pos = (screen_width - win_width) // 2
        y_pos = (screen_height - win_height) // 2
        self.full_screenshot_window.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")

    def hide_full_screenshot(self):
        """Destroys the full screenshot window if it exists."""
        if self.full_screenshot_window:
            self.full_screenshot_window.destroy()
            self.full_screenshot_window = None
            self.full_screenshot_photo = None
            
    def destroy_window(self):
        """Destroys the main view window and any associated windows."""
        if self.window:
            self.window.destroy()
            self.window = None
            self.hide_full_screenshot()