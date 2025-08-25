import os
import sys
import unittest
from unittest.mock import MagicMock

# Assuming event_listener.py contains EventListener
# Add project root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from training_assistant.utils.event_listener import EventListener


class TestEventListener(unittest.TestCase):
    def setUp(self):
        self.listener = EventListener()

    def test_subscribe_and_emit_mouse(self):
        callback = MagicMock()
        self.listener.subscribe_mouse('single_click', callback)
        self.listener.emit_mouse('single_click', {'x': 1, 'y': 2})
        callback.assert_called_once_with({'x': 1, 'y': 2})

    def test_subscribe_and_emit_keyboard(self):
        callback = MagicMock()
        self.listener.subscribe_keyboard('hotkey', callback)
        self.listener.emit_keyboard('hotkey', {'key': 'ctrl+c'})
        callback.assert_called_once_with({'key': 'ctrl+c'})

if __name__ == '__main__':
    unittest.main()
