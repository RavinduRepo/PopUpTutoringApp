# player.py
import tkinter as tk
from tkinter import scrolledtext
import threading
from event_listener import EventListener

class Player:
    def __init__(self, event_listener: EventListener):
        self.listener = event_listener
        self.listener_thread = None
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Event Player GUI")
        
        self.frame = tk.Frame(self.root, padx=10, pady=10)
        self.frame.pack()
        
        # Action Buttons
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(pady=(0, 10))

        self.start_button = tk.Button(self.button_frame, text="Start Listening", command=self.start_listening, state=tk.NORMAL)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.button_frame, text="Stop Listening", command=self.stop_listening, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.log_label = tk.Label(self.frame, text="Event Log:", font=("Arial", 12, "bold"))
        self.log_label.pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(self.frame, width=70, height=20, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def run(self):
        """Starts the Tkinter main loop."""
        print("Player GUI initialized. Use the buttons to control the event listener.")
        self.root.mainloop()

    def start_listening(self):
        """Starts the event listener in a new thread and subscribes methods."""
        if self.listener_thread is None or not self.listener_thread.is_alive():
            self.log_message("[GUI] Starting listener...")
            
            # Subscribing is now done here, right before the listener starts
            self.setup_subscriptions()
            
            self.listener_thread = threading.Thread(target=self.listener.start_listening, daemon=True)
            self.listener_thread.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

    def stop_listening(self):
        """Stops the event listener thread."""
        if self.listener_thread and self.listener_thread.is_alive():
            self.log_message("[GUI] Stopping listener...")
            self.listener.stop_listening()
            self.listener_thread.join()
            self.listener_thread = None
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log_message("[GUI] Listener stopped.")

    def on_closing(self):
        """Handles the window closing event to stop listeners and exit."""
        self.stop_listening()
        self.root.destroy()
    
    def setup_subscriptions(self):
        """Subscribes the player's methods to events from the listener."""
        self.listener.subscribe_mouse('single_click', self.play_single_click)
        self.listener.subscribe_mouse('right_click', self.play_right_click)
        self.listener.subscribe_mouse('double_click', self.play_double_click)
        self.listener.subscribe_keyboard('typing', self.play_typing)
        self.listener.subscribe_keyboard('hotkey', self.play_hotkey)

    def log_message(self, message):
        """Thread-safe method to update the GUI text box."""
        self.root.after(0, self._insert_message, message)

    def _insert_message(self, message):
        """Inserts a message into the text box and scrolls to the end."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def play_single_click(self, data):
        self.log_message(f"[PLAYER] Simulating single click at ({data['x']}, {data['y']}) with button: {data['button']}")

    def play_right_click(self, data):
        self.log_message(f"[PLAYER] Simulating right click at ({data['x']}, {data['y']}) with button: {data['button']}")

    def play_double_click(self, data):
        self.log_message(f"[PLAYER] Simulating double click at ({data['x']}, {data['y']}) with button: {data['button']}")

    def play_typing(self, data):
        self.log_message(f"[PLAYER] Simulating typing of message: '{data['message']}'")

    def play_hotkey(self, data):
        self.log_message(f"[PLAYER] Simulating hotkey: '{data['combination']}'")