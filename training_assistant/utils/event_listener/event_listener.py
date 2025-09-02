# event_listener.py
"""
Main EventListener class that maintains the same API as the original
while using the modular components internally.
"""
import logging
from .mouse_listener import MouseEventListener
from .keyboard_listener import KeyboardEventListener

logger = logging.getLogger(__name__)

class EventListener:
    """
    Main event listener that combines mouse and keyboard functionality.
    Maintains the same API as the original for backward compatibility.
    """
    
    def __init__(self):
        logger.info("Initialized event listener")
        self.mouse_listener = MouseEventListener()
        self.keyboard_listener = KeyboardEventListener()
        self.is_running = False
        
        # For backward compatibility, store references to the old attribute names
        self.mouse_listeners = {}
        self.keyboard_listeners = {}
        self.typed_characters = ""
        self.last_click_time = 0
        self.click_count = 0
        self.mouse_listener_thread = None
        self.keyboard_listener_thread = None
        
        # State variables for intelligent hotkey detection (for compatibility)
        self.pressed_keys = set()
        self.last_hotkey_time = 0
        self.hotkey_timeout = 0.1
        self.typing_timeout = 0.5
        self.last_key_time = 0
        self.is_typing_mode = False
        self.sent_hotkeys = set()
        self.key_press_times = {}
        
        # Key sets for compatibility
        self.modifier_keys = self.keyboard_listener.key_processor.modifier_keys
        self.control_keys = self.keyboard_listener.key_processor.control_keys

    def subscribe_mouse(self, event_type, listener):
        """Subscribe to mouse events - maintains original API"""
        # Store in old format for compatibility
        if event_type not in self.mouse_listeners:
            self.mouse_listeners[event_type] = []
        self.mouse_listeners[event_type].append(listener)
        
        # Subscribe to the new mouse listener
        self.mouse_listener.subscribe(event_type, listener)

    def subscribe_keyboard(self, event_type, listener):
        """Subscribe to keyboard events - maintains original API"""
        # Store in old format for compatibility
        if event_type not in self.keyboard_listeners:
            self.keyboard_listeners[event_type] = []
        self.keyboard_listeners[event_type].append(listener)
        
        # Subscribe to the new keyboard listener
        self.keyboard_listener.subscribe(event_type, listener)

    def _notify_mouse(self, event_type, data):
        """Notify mouse listeners - kept for backward compatibility"""
        if event_type in self.mouse_listeners:
            for listener in self.mouse_listeners[event_type]:
                try:
                    listener(data)
                except Exception as e:
                    logger.error(f"Error in mouse listener callback: {e}")

    def _notify_keyboard(self, event_type, data):
        """Notify keyboard listeners - kept for backward compatibility"""
        if event_type in self.keyboard_listeners:
            for listener in self.keyboard_listeners[event_type]:
                try:
                    listener(data)
                except Exception as e:
                    logger.error(f"Error in keyboard listener callback: {e}")

    # Legacy methods for backward compatibility
    def _get_key_string(self, key):
        """Legacy method - delegates to key processor"""
        return self.keyboard_listener.key_processor.get_key_string(key)

    def _format_hotkey_combination(self, keys):
        """Legacy method - delegates to key processor"""
        return self.keyboard_listener.key_processor.format_hotkey_combination(keys)

    def _is_hotkey_combination(self):
        """Legacy method - delegates to key processor"""
        return self.keyboard_listener.key_processor.is_hotkey_combination()

    def start_listening(self):
        """Start listening for both mouse and keyboard events"""
        if self.is_running:
            logger.info("Listener is already running.")
            return

        logger.info("Listening for events... Press 'Esc' to quit.")
        
        # Set up cross-listener communication for typing mode reset
        def on_mouse_click(data):
            # Reset typing mode on mouse click
            self.keyboard_listener.key_processor.is_typing_mode = False
            
            # Flush any accumulated typing
            typed_text = self.keyboard_listener.key_processor.flush_typing()
            if typed_text:
                self.keyboard_listener._notify('typing', {'message': typed_text})
        
        # Subscribe to mouse events to handle typing mode reset
        self.mouse_listener.subscribe('single_click', on_mouse_click)
        self.mouse_listener.subscribe('double_click', on_mouse_click)
        
        # Start both listeners
        self.mouse_listener.start_listening()
        
        # Store references for compatibility
        self.mouse_listener_thread = self.mouse_listener.listener_thread
        
        self.is_running = True
        
        # Start keyboard listener (this will block)
        try:
            self.keyboard_listener.start_listening()
            self.keyboard_listener_thread = self.keyboard_listener.listener_thread
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            self.stop_listening()

    def stop_listening(self):
        """Stop listening for events"""
        if self.is_running:
            logger.info("\nStopping listeners...")
            
            # Stop both listeners
            self.mouse_listener.stop_listening()
            self.keyboard_listener.stop_listening()
            
            # Clear old format listeners for compatibility
            self.mouse_listeners.clear()
            self.keyboard_listeners.clear()
            
            self.is_running = False
            logger.info("Listeners stopped and all subscribers cleared.")


# Example usage and testing
if __name__ == "__main__":
    def on_hotkey(data):
        logger.info(f"Hotkey detected: {data['combination']} (keys: {data['keys']})")
    
    def on_typing(data):
        logger.info(f"Typing detected: '{data['message']}'")
    
    def on_click(data):
        logger.info(f"Click at ({data['x']}, {data['y']}) with {data['button']}")
    
    listener = EventListener()
    listener.subscribe_keyboard('hotkey', on_hotkey)
    listener.subscribe_keyboard('typing', on_typing)
    listener.subscribe_mouse('single_click', on_click)
    listener.subscribe_mouse('double_click', on_click)
    
    try:
        listener.start_listening()
    except KeyboardInterrupt:
        listener.stop_listening()