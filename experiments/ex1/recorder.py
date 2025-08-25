# recorder.py
import sys
from event_listener import EventListener

class Recorder:
    def __init__(self, event_listener: EventListener):
        self.listener = event_listener
        self.setup_subscriptions()

    def run(self):
        """Starts the event listener and handles the program's lifecycle."""
        print("Recorder initialized. Waiting for events...")
        try:
            self.listener.start_listening()
        except KeyboardInterrupt:
            print("\nProgram interrupted by user (Ctrl+C).")
        finally:
            self.listener.stop_listening() # Ensures listeners are stopped on exit
            sys.exit(0)

    def setup_subscriptions(self):
        """Subscribes the recorder's methods to events from the listener."""
        self.listener.subscribe_mouse('single_click', self.record_single_click)
        self.listener.subscribe_mouse('right_click', self.record_right_click)
        self.listener.subscribe_mouse('double_click', self.record_double_click)
        self.listener.subscribe_keyboard('typing', self.record_typing)
        self.listener.subscribe_keyboard('hotkey', self.record_hotkey)
    
    def record_single_click(self, data):
        print(f"[RECORDER] Single click at coordinates: ({data['x']}, {data['y']}) with button: {data['button']}")

    def record_right_click(self, data):
        print(f"[RECORDER] Right click at coordinates: ({data['x']}, {data['y']}) with button: {data['button']}")

    def record_double_click(self, data):
        print(f"[RECORDER] Double click at coordinates: ({data['x']}, {data['y']}) with button: {data['button']}")

    def record_typing(self, data):
        print(f"[RECORDER] Typed message: '{data['message']}'")

    def record_hotkey(self, data):
        print(f"[RECORDER] Hotkey pressed: '{data['combination']}'")