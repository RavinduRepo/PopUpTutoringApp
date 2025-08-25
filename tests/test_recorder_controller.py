import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from training_assistant.controllers.recorder_controller import RecorderController

class TestRecorderController(unittest.TestCase):
    def setUp(self):
        self.mock_main_controller = MagicMock()
        self.mock_event_listener = MagicMock()
        self.controller = RecorderController(self.mock_main_controller, self.mock_event_listener)

    def test_initial_state(self):
        self.assertFalse(self.controller.is_recording)
        self.assertFalse(self.controller.is_paused)

    def test_start_and_stop_recording(self):
        self.controller.start_recording()
        self.assertTrue(self.controller.is_recording)
        self.controller.stop_recording()
        self.assertFalse(self.controller.is_recording)

if __name__ == '__main__':
    unittest.main()
