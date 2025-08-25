# __init__.py
"""
Event Listener Package

A modular event listening system for mouse and keyboard events with
intelligent hotkey detection and typing analysis.
"""

from .event_listener import EventListener
from .base_listener import BaseEventListener
from .mouse_listener import MouseEventListener
from .keyboard_listener import KeyboardEventListener
from .key_processor import KeyProcessor

__version__ = "1.0.0"
__author__ = "Ravindu Pathirage"

# For backward compatibility, export the main class
__all__ = [
    'EventListener',
    'BaseEventListener', 
    'MouseEventListener',
    'KeyboardEventListener',
    'KeyProcessor'
]