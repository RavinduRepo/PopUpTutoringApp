# main.py
import sys
import threading
from event_listener import EventListener
from recorder import Recorder
from player import Player

if __name__ == "__main__":
    event_listener = EventListener()

    if len(sys.argv) < 2:
        print("Usage: python main.py [recorder | player]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == 'recorder':
        Recorder(event_listener)
        print("Recorder initialized. Waiting for events...")
        try:
            event_listener.start_listening()
        except KeyboardInterrupt:
            print("\nProgram interrupted by user (Ctrl+C).")
        finally:
            event_listener.stop_listening()
            sys.exit(0)
    elif mode == 'player':
        player_instance = Player(event_listener)
        print("Player initialized with GUI.")
        
        # Start the event listener in a separate thread
        listener_thread = threading.Thread(target=event_listener.start_listening, daemon=True)
        listener_thread.start()
        
        # Start the GUI in the main thread
        player_instance.run_gui()

    else:
        print(f"Invalid mode: '{mode}'. Choose 'recorder' or 'player'.")
        sys.exit(1)