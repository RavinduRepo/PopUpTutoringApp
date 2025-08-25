import os
import sys
import unittest
from unittest.mock import MagicMock
# Add project root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from training_assistant.controllers.base_controller import BaseController


class TestBaseController(unittest.TestCase):
    def setUp(self):
        self.mock_main_controller = MagicMock()
        self.mock_event_listener = MagicMock()
        self.controller = BaseController(self.mock_main_controller, self.mock_event_listener)

    def test_init(self):
        self.assertEqual(self.controller.main_controller, self.mock_main_controller)
        self.assertEqual(self.controller.event_listener, self.mock_event_listener)

    def test_is_click_on_app_window(self):
        # Should be implemented in subclass, but test default returns False
        self.assertFalse(self.controller.is_click_on_app_window(0, 0))

if __name__ == '__main__':
    unittest.main()
