import tkinter as tk
from tkinter import messagebox
import threading
from audio_controller import AudioController


class AudioRecorderApp:
    def __init__(self, root):
        self.controller = AudioController()
        self.root = root
        self.root.title("Voice Recorder (MVC)")
        self.root.geometry("320x250")

        # UI Components
        self.record_btn = tk.Button(
            root,
            text="🎙 Start Recording",
            command=lambda: threading.Thread(target=self.start_recording).start(),
            width=20,
            height=2,
        )
        self.record_btn.pack(pady=10)

        self.stop_btn = tk.Button(
            root,
            text="⏹ Stop Recording",
            command=self.stop_recording,
            width=20,
            height=2,
        )
        self.stop_btn.pack(pady=10)

        self.play_btn = tk.Button(
            root,
            text="▶ Play",
            command=lambda: threading.Thread(target=self.play_audio).start(),
            width=20,
            height=2,
        )
        self.play_btn.pack(pady=10)

        self.status_label = tk.Label(root, text="Idle", fg="blue")
        self.status_label.pack(pady=10)

    def start_recording(self):
        self.controller.start_recording()
        self.status_label.config(text="Recording...")

    def stop_recording(self):
        success = self.controller.stop_recording()
        if success:
            self.status_label.config(text="Recording saved to JSON")
        else:
            messagebox.showwarning("Warning", "No active recording.")

    def play_audio(self):
        success = self.controller.play_audio()
        if success:
            self.status_label.config(text="Finished Playing")
        else:
            messagebox.showerror("Error", "No recording found.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()
