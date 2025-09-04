# keyboard_listener.py
import time
from pynput import keyboard
import logging
from .base_listener import BaseEventListener
from .key_processor import KeyProcessor

logger = logging.getLogger(__name__)

class KeyboardEventListener(BaseEventListener):
    """Handles keyboard events with intelligent hotkey and typing detection"""
    
    def __init__(self):
        super().__init__()
        self.key_processor = KeyProcessor()
    
    def _handle_control_character(self, key):
        """Handle control characters from Ctrl combinations"""
        if not (hasattr(key, 'char') and key.char is not None and ord(key.char) < 32):
            return False
        
        char = key.char
        actual_char = self.key_processor.get_key_string(key)
        
        # Check if this is a Ctrl combination
        ctrl_chars = ['\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', 
                     '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f', '\x10', 
                     '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', 
                     '\x19', '\x1a']
        
        if char in ctrl_chars:
            combination_str = f'ctrl+{actual_char}'
            
            if combination_str not in self.key_processor.sent_hotkeys:
                # Flush any accumulated typing
                typed_text = self.key_processor.flush_typing()
                if typed_text:
                    self._notify('typing', {'message': typed_text})
                
                # Send hotkey notification
                self._notify('hotkey', {
                    'key': combination_str,
                    'combination': combination_str,
                    'keys': ['ctrl', actual_char]
                })
                
                self.key_processor.sent_hotkeys.add(combination_str)
                self.key_processor.is_typing_mode = False
            return True
        return False
    
    def _on_press(self, key):
        # treat it as a hotkey
        if key == keyboard.Key.esc:
            if 'esc' not in self.key_processor.sent_hotkeys:
                self._notify('hotkey', {
                    'key': 'esc',  # Backward compatibility
                    'combination': 'esc',
                    'keys': [self.key_processor.get_key_string(key)]
                })
                self.key_processor.sent_hotkeys.add('esc')

        # Handle control characters first
        if self._handle_control_character(key):
            return

        current_time = time.time()
        
        # Only process if this is the first press of this key (ignore key repeats)
        if key not in self.key_processor.pressed_keys:
            self.key_processor.key_press_times[key] = current_time
            self.key_processor.pressed_keys.add(key)
            self.key_processor.last_key_time = current_time
            
            # Check if this creates a valid hotkey combination
            if self.key_processor.is_hotkey_combination():
                combination_str = self.key_processor.format_hotkey_combination(self.key_processor.pressed_keys)
                
                if (self.key_processor.should_send_hotkey(key) and 
                    combination_str not in self.key_processor.sent_hotkeys):
                    
                    # Flush any accumulated typing before processing hotkey
                    typed_text = self.key_processor.flush_typing()
                    if typed_text:
                        self._notify('typing', {'message': typed_text})
                    
                    # Send hotkey notification
                    key_list = [self.key_processor.get_key_string(k) for k in self.key_processor.pressed_keys]
                    
                    self._notify('hotkey', {
                        'key': combination_str,  # Backward compatibility
                        'combination': combination_str,
                        'keys': key_list
                    })
                    
                    # Mark this combination as sent
                    self.key_processor.sent_hotkeys.add(combination_str)
                    self.key_processor.last_hotkey_time = current_time
                    self.key_processor.is_typing_mode = False
                    
            elif not self.key_processor.is_hotkey_combination():
                # Handle as typing
                self.key_processor.is_typing_mode = True
                self.key_processor.add_typed_character(key)

    def _on_release(self, key):
        # Remove key from pressed keys
        self.key_processor.pressed_keys.discard(key)
        self.key_processor.key_press_times.pop(key, None)
        
        current_time = time.time()
        
        # Clear sent hotkeys when all keys are released
        if len(self.key_processor.pressed_keys) == 0:
            self.key_processor.sent_hotkeys.clear()
        
        # If we're in typing mode and enough time has passed, flush the typing
        if (self.key_processor.is_typing_mode and 
            self.key_processor.typed_characters and 
            len(self.key_processor.pressed_keys) == 0 and 
            (current_time - self.key_processor.last_key_time) > self.key_processor.typing_timeout):
            
            typed_text = self.key_processor.flush_typing()
            if typed_text:
                self._notify('typing', {'message': typed_text})

    def start_listening(self):
        if self.is_running:
            logger.info("Keyboard listener is already running.")
            return

        logger.info("Starting keyboard listener...")
        
        self.listener_thread = keyboard.Listener(
            on_press=self._on_press, 
            on_release=self._on_release
        )
        
        self.listener_thread.start()
        self.is_running = True

        try:
            self.listener_thread.join()
        except Exception as e:
            logger.error(f"An error occurred in keyboard listener: {e}")
        finally:
            self.stop_listening()

    def stop_listening(self):
        if self.is_running:
            logger.info("Stopping keyboard listener...")
            
            # Flush any remaining typed characters
            typed_text = self.key_processor.flush_typing()
            if typed_text:
                self._notify('typing', {'message': typed_text})
            
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.stop()
                self.listener_thread.join()
            
            self.listeners.clear()
            self.key_processor.reset_state()
            self.is_running = False
            logger.info("Keyboard listener stopped.")