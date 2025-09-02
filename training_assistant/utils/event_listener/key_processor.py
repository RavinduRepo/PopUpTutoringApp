# key_processor.py
from pynput import keyboard
import logging

logger = logging.getLogger(__name__)

class KeyProcessor:
    """Handles key processing, hotkey detection, and typing analysis"""
    
    def __init__(self):
        self.pressed_keys = set()
        self.last_hotkey_time = 0
        self.hotkey_timeout = 0.1  # 100ms timeout for hotkey detection
        self.typing_timeout = 0.5  # 500ms timeout for typing detection
        self.last_key_time = 0
        self.is_typing_mode = False
        self.sent_hotkeys = set()  # Track sent hotkey combinations to avoid duplicates
        self.key_press_times = {}  # Track when each key was first pressed
        self.typed_characters = ""
        
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
    
    def get_key_string(self, key):
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
                clean_names = {
                    'ctrl_l': 'ctrl',
                    'ctrl_r': 'ctrl',
                    'alt_l': 'alt',
                    'alt_r': 'alt',
                    'shift_l': 'shift',
                    'shift_r': 'shift',
                    'cmd_l': 'cmd',
                    'cmd_r': 'cmd'
                }
                return clean_names.get(key_name, key_name)
        except:
            return str(key)

    def format_hotkey_combination(self, keys):
        """Format the key combination into a readable string"""
        modifiers = []
        regular_keys = []
        
        for key in keys:
            key_str = self.get_key_string(key)
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

    def is_hotkey_combination(self):
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
    
    def should_send_hotkey(self, pressed_key):
        """Determine if we should send the hotkey immediately"""
        # Always process Enter immediately
        if pressed_key == keyboard.Key.enter:
            return True
        
        # For modifier keys alone, don't send
        if len(self.pressed_keys) == 1 and pressed_key in self.modifier_keys:
            return False
        
        # For single non-modifier keys that are hotkeys (F1, arrows, etc.)
        if len(self.pressed_keys) == 1 and pressed_key not in self.modifier_keys:
            return True
        
        # For combinations: send when we have modifier + non-modifier and the non-modifier was just pressed
        has_modifier = any(k in self.modifier_keys for k in self.pressed_keys)
        has_non_modifier = any(k not in self.modifier_keys for k in self.pressed_keys)
        
        if has_modifier and has_non_modifier:
            # Check if a non-modifier key was just pressed (completing the combination)
            if pressed_key not in self.modifier_keys:
                return True
            # Or if this is the first modifier being added to an existing non-modifier
            elif pressed_key in self.modifier_keys and len([k for k in self.pressed_keys if k not in self.modifier_keys]) > 0:
                return True
        
        return False
    
    def add_typed_character(self, key):
        """Add character to typed buffer"""
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
    
    def flush_typing(self):
        """Return and clear typed characters"""
        if self.typed_characters:
            text = self.typed_characters
            self.typed_characters = ""
            return text
        return None
    
    def reset_state(self):
        """Reset all state variables"""
        self.pressed_keys.clear()
        self.sent_hotkeys.clear()
        self.key_press_times.clear()
        self.typed_characters = ""
        self.is_typing_mode = False