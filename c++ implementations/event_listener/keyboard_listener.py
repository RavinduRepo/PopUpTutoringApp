# keyboard_listener.py
import time
from pynput import keyboard
import logging
from .base_listener import BaseEventListener

# Change the import to use the C++ module
from key_processor_cpp import KeyProcessor, Key

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
        # The C++ KeyProcessor will handle the string conversion
        actual_char = self.key_processor.get_key_string(Key(character=char))
        
        # Check if this is a Ctrl combination
        ctrl_chars = ['\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', 
                     '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f', '\x10', 
                     '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', 
                     '\x19', '\x1a']
        
        if char in ctrl_chars:
            combination_str = f'ctrl+{actual_char}'
            
            if combination_str not in self.key_processor.get_sent_hotkeys():
                typed_text = self.key_processor.flush_typing()
                if typed_text:
                    self._notify('typing', {'message': typed_text})
                
                self._notify('hotkey', {
                    'key': combination_str,
                    'combination': combination_str,
                    'keys': ['ctrl', actual_char]
                })
                
                self.key_processor.sent_hotkeys.add(combination_str) # This needs to be done in C++ now
                self.key_processor.is_typing_mode = False # This too
            return True
        return False
    
    def _on_press(self, key):
        """Callback for key press events"""
        if key == keyboard.Key.esc:
            if 'esc' not in self.key_processor.get_sent_hotkeys():
                self._notify('hotkey', {
                    'key': 'esc',
                    'combination': 'esc',
                    'keys': [self.key_processor.get_key_string(Key(name='esc'))]
                })
                self.key_processor.sent_hotkeys.add('esc') # This needs to be done in C++ now
            return False

        if self._handle_control_character(key):
            return

        current_time = time.time()
        
        # Create a C++ Key object from the pynput key
        key_name = None
        key_char = '\0'
        if hasattr(key, 'char') and key.char is not None:
            key_char = key.char
            if key.char == ' ':
                key_name = 'space'
        else:
            key_name = str(key).replace('Key.', '')
        cpp_key = Key(key_name, key_char)

        if cpp_key.name not in self.key_processor.get_pressed_keys():
            self.key_processor.add_pressed_key(cpp_key)
            
            # The logic for last_key_time is now handled in the C++ add_pressed_key method
            
            if self.key_processor.is_hotkey_combination():
                combination_str = self.key_processor.format_hotkey_combination()
                
                if (self.key_processor.should_send_hotkey(cpp_key) and 
                    combination_str not in self.key_processor.get_sent_hotkeys()):
                    
                    typed_text = self.key_processor.flush_typing()
                    if typed_text:
                        self._notify('typing', {'message': typed_text})
                    
                    key_list = [self.key_processor.get_key_string(Key(name=k)) for k in self.key_processor.get_pressed_keys()]
                    
                    self._notify('hotkey', {
                        'key': combination_str,
                        'combination': combination_str,
                        'keys': key_list
                    })
                    
                    self.key_processor.get_sent_hotkeys().add(combination_str)
                    self.key_processor.last_hotkey_time = current_time # This is a setter that needs to be implemented
                    self.key_processor.is_typing_mode = False
                    
            elif not self.key_processor.is_hotkey_combination():
                self.key_processor.is_typing_mode = True
                self.key_processor.add_typed_character(cpp_key)

    def _on_release(self, key):
        """Callback for key release events"""
        key_name = None
        key_char = '\0'
        if hasattr(key, 'char') and key.char is not None:
            key_char = key.char
            if key.char == ' ':
                key_name = 'space'
        else:
            key_name = str(key).replace('Key.', '')
        cpp_key = Key(key_name, key_char)

        self.key_processor.remove_released_key(cpp_key)
        
        current_time = time.time()
        
        if len(self.key_processor.get_pressed_keys()) == 0:
            self.key_processor.get_sent_hotkeys().clear()
        
        if (self.key_processor.get_is_typing_mode() and 
            (current_time - self.key_processor.get_last_key_time()) > self.key_processor.get_typing_timeout()):
            
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