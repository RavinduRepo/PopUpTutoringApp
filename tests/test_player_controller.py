
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
# Add project root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from training_assistant.controllers.player_controller import PlayerController

class TestPlayerController(unittest.TestCase):
    def setUp(self):
        self.mock_main_controller = MagicMock()
        self.mock_event_listener = MagicMock()
        self.controller = PlayerController(self.mock_main_controller, self.mock_event_listener)

    def test_initial_state(self):
        self.assertIsNone(self.controller.current_tutorial)
        self.assertEqual(self.controller.current_step_index, 0)
        self.assertFalse(self.controller.is_playing)
        self.assertFalse(self.controller.is_paused)

    @patch('tkinter.filedialog.askopenfilename', return_value='dummy.json')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"steps": []}')
    def test_load_tutorial_from_dialog(self, mock_open, mock_dialog):
        self.controller.main_controller.views = {'play': MagicMock()}
        self.controller.load_tutorial_from_dialog()
        self.assertIsNotNone(self.controller.current_tutorial)

    def test_toggle_pause(self):
        self.controller.is_playing = True
        self.controller.is_paused = False
        self.controller.player_mini_view.update_play_pause_button = MagicMock()
        self.controller.player_mini_view.destroy_overlay = MagicMock()
        self.controller.main_controller.views = {'play': MagicMock()}
        self.controller.toggle_pause()
        self.assertTrue(self.controller.is_paused)

    def test_end_playback(self):
        self.controller.is_playing = True
        self.controller.player_mini_view.destroy_overlay = MagicMock()
        self.controller.player_mini_view.destroy_control_window = MagicMock()
        self.controller.main_controller.views = {'play': MagicMock()}
        self.controller.main_controller.deiconify = MagicMock()
        with patch('tkinter.messagebox.showinfo'):
            self.controller.end_playback()
        self.assertFalse(self.controller.is_playing)

if __name__ == '__main__':
    unittest.main()
