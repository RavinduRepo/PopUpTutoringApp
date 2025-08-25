# mouse_listener.py
import time
from pynput import mouse
import logging
from .base_listener import BaseEventListener

logger = logging.getLogger(__name__)

class MouseEventListener(BaseEventListener):
    """Handles mouse events including clicks and double-clicks"""
    
    def __init__(self):
        super().__init__()
        self.last_click_time = 0
        self.click_count = 0
        self.double_click_threshold = 0.3  # 300ms for double-click detection
    
    def _on_click(self, x, y, button, pressed):
        if pressed:
            current_time = time.time()
            self.click_count += 1

            if current_time - self.last_click_time < self.double_click_threshold:
                if self.click_count == 2:
                    self._notify('double_click', {
                        'x': x, 
                        'y': y, 
                        'button': 'double_click'
                    })
                    self.click_count = 0
            else:
                self.click_count = 1
                self._notify('single_click', {
                    'x': x, 
                    'y': y, 
                    'button': f"{button.name}_click"
                })
            
            self.last_click_time = current_time

    def start_listening(self):
        if self.is_running:
            logger.info("Mouse listener is already running.")
            return

        logger.info("Starting mouse listener...")
        
        self.listener_thread = mouse.Listener(on_click=self._on_click)
        self.listener_thread.start()
        self.is_running = True

    def stop_listening(self):
        if self.is_running:
            logger.info("Stopping mouse listener...")
            
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.stop()
                self.listener_thread.join()
            
            self.listeners.clear()
            self.is_running = False
            logger.info("Mouse listener stopped.")