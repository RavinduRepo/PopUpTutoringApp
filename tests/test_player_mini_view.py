import os
import sys
import unittest
from unittest.mock import MagicMock
# Add project root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from training_assistant.views.player_mini_view import PlayerMiniView

class TestPlayerMiniView(unittest.TestCase):
    def setUp(self):
        self.view = PlayerMiniView(
            parent=MagicMock(),
            next_step_callback=MagicMock(),
            previous_step_callback=MagicMock(),
            toggle_pause_callback=MagicMock(),
            end_playback_callback=MagicMock()
        )

    def test_update_step_display(self):
        step_info = {
            "index": 0,
            "total": 1,
            "action_type": "click",
            "notes": "",
            "text": "",
            "keys": "",
            "highlight_coordinates": (10, 10),
            "thumb": MagicMock(),
            "highlight_color": "red",
            "highlight_radius": 10,
            "screenshot": None,
            "recorded_coordinates": (10, 10)
        }
        # Should not raise
        self.view.update_step_display(step_info)

    def test_create_and_destroy_overlay(self):
        # Should not raise
        self.view.create_overlay({'highlight_coordinates': (10, 10)})
        self.view.destroy_overlay()

if __name__ == '__main__':
    unittest.main()
