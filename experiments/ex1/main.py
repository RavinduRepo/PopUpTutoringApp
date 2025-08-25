# main.py
import sys
from event_listener import EventListener
from recorder import Recorder
from player import Player

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py [recorder | player]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    event_listener = EventListener()

    if mode == 'recorder':
        recorder = Recorder(event_listener)
        recorder.run()
    elif mode == 'player':
        player = Player(event_listener)
        player.run()
    else:
        print(f"Invalid mode: '{mode}'. Choose 'recorder' or 'player'.")
        sys.exit(1)