# event_listener.py
import time
from pynput import mouse, keyboard
import threading
import logging
logger = logging.getLogger(__name__)

class EventListener:
    def __init__(self):
        logger.info("initialized event listener")
        self.mouse_listeners = {}
        self.keyboard_listeners = {}
        self.typed_characters = ""
        self.last_click_time = 0
        self.click_count = 0
        self.mouse_listener_thread = None
        self.keyboard_listener_thread = None
        self.is_running = False
        
        # State variables for intelligent hotkey detection
        self.pressed_keys = set()
        self.last_hotkey_time = 0
        self.hotkey_timeout = 0.1  # 100ms timeout for hotkey detection
        self.typing_timeout = 0.5  # 500ms timeout for typing detection
        self.last_key_time = 0
        self.is_typing_mode = False
        self.sent_hotkeys = set()  # Track sent hotkey combinations to avoid duplicates
        self.key_press_times = {}  # Track when each key was first pressed
        
        # Modifier keys that typically indicate hotkeys
        self.modifier_keys = {
            keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt_l, keyboard.Key.alt_r, 
            keyboard.Key.shift_l, keyboard.Key.shift_r,
            keyboard.Key.cmd_l, keyboard.Key.cmd_r,  # For Mac
            keyboard.Key.tab, keyboard.Key.esc,
            keyboard.Key.f1, keyboard.Key.f2, keyboard.Key.f3, keyboard.Key.f4,
            keyboard.Key.f5, keyboard.Key.f6, keyboard.Key.f7, keyboard.Key.f8,
            keyboard.Key.f9, keyboard.Key.f10, keyboard.Key.f11, keyboard.Key.f12
        }
        
        # Keys that typically indicate navigation/control rather than typing
        self.control_keys = {
            keyboard.Key.enter, keyboard.Key.backspace, keyboard.Key.delete,
            keyboard.Key.home, keyboard.Key.end, keyboard.Key.page_up, 
            keyboard.Key.page_down, keyboard.Key.up, keyboard.Key.down,
            keyboard.Key.left, keyboard.Key.right, keyboard.Key.insert
        }

    def subscribe_mouse(self, event_type, listener):
        if event_type not in self.mouse_listeners:
            self.mouse_listeners[event_type] = []
        self.mouse_listeners[event_type].append(listener)

    def subscribe_keyboard(self, event_type, listener):
        if event_type not in self.keyboard_listeners:
            self.keyboard_listeners[event_type] = []
        self.keyboard_listeners[event_type].append(listener)

    def _notify_mouse(self, event_type, data):
        if event_type in self.mouse_listeners:
            for listener in self.mouse_listeners[event_type]:
                listener(data)

    def _notify_keyboard(self, event_type, data):
        if event_type in self.keyboard_listeners:
            for listener in self.keyboard_listeners[event_type]:
                listener(data)

    def _on_click(self, x, y, button, pressed):
        if pressed:
            current_time = time.time()
            self.click_count += 1
            
            # Reset typing mode on mouse click
            self.is_typing_mode = False

            # Flush any accumulated typing
            if self.typed_characters:
                self._notify_keyboard('typing', {'message': self.typed_characters})
                self.typed_characters = ""

            if current_time - self.last_click_time < 0.3:
                if self.click_count == 2:
                    self._notify_mouse('double_click', {'x': x, 'y': y, 'button': 'double_click'})
                    self.click_count = 0
            else:
                self.click_count = 1
                self._notify_mouse('single_click', {'x': x, 'y': y, 'button': f"{button.name}_click"})
            
            self.last_click_time = current_time

    def _get_key_string(self, key):
        """Convert key object to string representation"""
        try:
            if hasattr(key, 'char') and key.char is not None:
                # Filter out control characters and hex values caused by Ctrl combinations
                char = key.char
                # If it's a control character (ASCII < 32), it's likely from Ctrl combination
                if ord(char) < 32:
                    # Common Ctrl combinations mapping
                    ctrl_map = {
                        '\x01': 'a',  # Ctrl+A
                        '\x02': 'b',  # Ctrl+B  
                        '\x03': 'c',  # Ctrl+C
                        '\x04': 'd',  # Ctrl+D
                        '\x05': 'e',  # Ctrl+E
                        '\x06': 'f',  # Ctrl+F
                        '\x07': 'g',  # Ctrl+G
                        '\x08': 'h',  # Ctrl+H (also backspace)
                        '\x09': 'i',  # Ctrl+I (also tab)
                        '\x0a': 'j',  # Ctrl+J (also enter/newline)
                        '\x0b': 'k',  # Ctrl+K
                        '\x0c': 'l',  # Ctrl+L
                        '\x0d': 'm',  # Ctrl+M (also enter)
                        '\x0e': 'n',  # Ctrl+N
                        '\x0f': 'o',  # Ctrl+O
                        '\x10': 'p',  # Ctrl+P
                        '\x11': 'q',  # Ctrl+Q
                        '\x12': 'r',  # Ctrl+R
                        '\x13': 's',  # Ctrl+S
                        '\x14': 't',  # Ctrl+T
                        '\x15': 'u',  # Ctrl+U
                        '\x16': 'v',  # Ctrl+V
                        '\x17': 'w',  # Ctrl+W
                        '\x18': 'x',  # Ctrl+X
                        '\x19': 'y',  # Ctrl+Y
                        '\x1a': 'z',  # Ctrl+Z
                        '\x1b': 'esc', # ESC
                    }
                    return ctrl_map.get(char, char)
                return char
            else:
                # Handle special keys with cleaner names
                key_name = str(key).replace('Key.', '')
                # Clean up common key names
                if key_name == 'ctrl_l':
                    return 'ctrl'
                elif key_name == 'ctrl_r':
                    return 'ctrl'
                elif key_name == 'alt_l':
                    return 'alt'
                elif key_name == 'alt_r':
                    return 'alt'
                elif key_name == 'shift_l':
                    return 'shift'
                elif key_name == 'shift_r':
                    return 'shift'
                elif key_name == 'cmd_l':
                    return 'cmd'
                elif key_name == 'cmd_r':
                    return 'cmd'
                return key_name
        except:
            return str(key)

    def _format_hotkey_combination(self, keys):
        """Format the key combination into a readable string"""
        key_strings = []
        modifiers = []
        regular_keys = []
        
        for key in keys:
            key_str = self._get_key_string(key)
            if key in self.modifier_keys or key in self.control_keys:
                modifiers.append(key_str)
            else:
                regular_keys.append(key_str)
        
        # Sort modifiers for consistent output (remove duplicates for left/right variants)
        unique_modifiers = []
        seen_modifiers = set()
        
        modifier_order = ['ctrl', 'alt', 'shift', 'cmd']
        for mod in modifier_order:
            if mod in modifiers and mod not in seen_modifiers:
                unique_modifiers.append(mod)
                seen_modifiers.add(mod)
        
        # Add any other modifiers not in the order
        for mod in modifiers:
            if mod not in seen_modifiers:
                unique_modifiers.append(mod)
                seen_modifiers.add(mod)
        
        # Combine modifiers and regular keys
        key_strings = unique_modifiers + sorted(regular_keys)
        return '+'.join(key_strings)

    def _is_hotkey_combination(self):
        """Determine if current key combination should be treated as a hotkey"""
        if len(self.pressed_keys) == 0:
            return False
            
        # Single key check
        if len(self.pressed_keys) == 1:
            key = next(iter(self.pressed_keys))
            
            # Enter is always a hotkey
            if key == keyboard.Key.enter:
                return True
                
            # Backspace is NOT a hotkey (used for typing correction)
            if key == keyboard.Key.backspace:
                return False
            
            # Modifier keys alone are NOT hotkeys (wait for combination)
            if key in self.modifier_keys:
                return False
            
            # Other control keys (except backspace) are hotkeys
            if key in self.control_keys and key != keyboard.Key.backspace:
                return True
        
        # Any combination with modifiers + other keys is a hotkey
        has_modifier = any(key in self.modifier_keys for key in self.pressed_keys)
        has_non_modifier = any(key not in self.modifier_keys for key in self.pressed_keys)
        
        if has_modifier and has_non_modifier and len(self.pressed_keys) > 1:
            return True
        
        # Multiple non-modifier keys pressed simultaneously are likely hotkeys
        if len(self.pressed_keys) > 1 and not has_modifier:
            return True
        
        return False

    def _on_press(self, key):
        # Stop listening on 'Esc' press (but also treat it as a hotkey)
        if key == keyboard.Key.esc:
            if 'esc' not in self.sent_hotkeys:
                self._notify_keyboard('hotkey', {
                    'key': 'esc',  # Backward compatibility
                    'combination': 'esc',
                    'keys': [self._get_key_string(key)]
                })
                self.sent_hotkeys.add('esc')
            return False

        current_time = time.time()
        
        # Handle control characters from Ctrl combinations first
        if hasattr(key, 'char') and key.char is not None and ord(key.char) < 32:
            # This is a control character, likely from a Ctrl combination
            char = key.char
            actual_char = self._get_key_string(key)  # This will map control chars to letters
            
            if char in ['\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a']:
                # This is definitely a Ctrl combination
                combination_str = f'ctrl+{actual_char}'
                
                if combination_str not in self.sent_hotkeys:
                    # Flush any accumulated typing
                    if self.typed_characters:
                        self._notify_keyboard('typing', {'message': self.typed_characters})
                        self.typed_characters = ""
                    
                    # Send hotkey notification
                    self._notify_keyboard('hotkey', {
                        'key': combination_str,
                        'combination': combination_str,
                        'keys': ['ctrl', actual_char]
                    })
                    
                    self.sent_hotkeys.add(combination_str)
                    self.is_typing_mode = False
                return
        
        # Only process if this is the first press of this key (ignore key repeats)
        if key not in self.pressed_keys:
            self.key_press_times[key] = current_time
            self.pressed_keys.add(key)
            self.last_key_time = current_time
            
            # Check if this creates a valid hotkey combination
            if self._is_hotkey_combination():
                combination_str = self._format_hotkey_combination(self.pressed_keys)
                
                # Determine if we should send this hotkey now
                should_send = False
                
                # Always process Enter immediately
                if key == keyboard.Key.enter:
                    should_send = True
                # For modifier keys alone, don't send
                elif len(self.pressed_keys) == 1 and key in self.modifier_keys:
                    should_send = False
                # For single non-modifier keys that are hotkeys (F1, arrows, etc.)
                elif len(self.pressed_keys) == 1 and key not in self.modifier_keys:
                    should_send = True
                # For combinations: send when we have modifier + non-modifier and the non-modifier was just pressed
                else:
                    has_modifier = any(k in self.modifier_keys for k in self.pressed_keys)
                    has_non_modifier = any(k not in self.modifier_keys for k in self.pressed_keys)
                    
                    if has_modifier and has_non_modifier:
                        # Check if a non-modifier key was just pressed (completing the combination)
                        if key not in self.modifier_keys:
                            should_send = True
                        # Or if this is the first modifier being added to an existing non-modifier
                        elif key in self.modifier_keys and len([k for k in self.pressed_keys if k not in self.modifier_keys]) > 0:
                            should_send = True
                
                if should_send and combination_str not in self.sent_hotkeys:
                    # Flush any accumulated typing before processing hotkey
                    if self.typed_characters:
                        self._notify_keyboard('typing', {'message': self.typed_characters})
                        self.typed_characters = ""
                    
                    # Send hotkey notification
                    key_list = [self._get_key_string(k) for k in self.pressed_keys]
                    
                    self._notify_keyboard('hotkey', {
                        'key': combination_str,  # Backward compatibility
                        'combination': combination_str,
                        'keys': key_list
                    })
                    
                    # Mark this combination as sent
                    self.sent_hotkeys.add(combination_str)
                    self.last_hotkey_time = current_time
                    self.is_typing_mode = False
                    
            elif not self._is_hotkey_combination():
                # Handle as typing
                self.is_typing_mode = True
                
                if key == keyboard.Key.backspace:
                    self.typed_characters = self.typed_characters[:-1]
                elif key == keyboard.Key.space:
                    self.typed_characters += ' '
                else:
                    try:
                        if hasattr(key, 'char') and key.char is not None:
                            # Don't add control characters to typed text
                            if ord(key.char) >= 32:
                                self.typed_characters += key.char
                    except AttributeError:
                        pass

    def _on_release(self, key):
        # Remove key from pressed keys
        self.pressed_keys.discard(key)
        
        # Remove from key press times
        self.key_press_times.pop(key, None)
        
        current_time = time.time()
        
        # Clear sent hotkeys when all keys are released
        if len(self.pressed_keys) == 0:
            self.sent_hotkeys.clear()
        
        # If we're in typing mode and enough time has passed, flush the typing
        if (self.is_typing_mode and 
            self.typed_characters and 
            len(self.pressed_keys) == 0 and 
            (current_time - self.last_key_time) > self.typing_timeout):
            
            self._notify_keyboard('typing', {'message': self.typed_characters})
            self.typed_characters = ""

    def start_listening(self):
        if self.is_running:
            logger.info("Listener is already running.")
            return

        logger.info("Listening for events... Press 'Esc' to quit.")
        
        self.mouse_listener_thread = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener_thread = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        
        self.mouse_listener_thread.start()
        self.keyboard_listener_thread.start()
        self.is_running = True

        try:
            self.keyboard_listener_thread.join()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            self.stop_listening()

    def stop_listening(self):
        if self.is_running:
            logger.info("\nStopping listeners...")
            
            # Flush any remaining typed characters
            if self.typed_characters:
                self._notify_keyboard('typing', {'message': self.typed_characters})
                self.typed_characters = ""
            
            if self.mouse_listener_thread and self.mouse_listener_thread.is_alive():
                self.mouse_listener_thread.stop()
                self.mouse_listener_thread.join()
            if self.keyboard_listener_thread and self.keyboard_listener_thread.is_alive():
                self.keyboard_listener_thread.stop()
                self.keyboard_listener_thread.join()
            
            # Unsubscribe all listeners
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
    listener.subscribe_mouse('right_click', on_click)
    
    try:
        listener.start_listening()
    except KeyboardInterrupt:
        listener.stop_listening()
