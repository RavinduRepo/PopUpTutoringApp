import sounddevice as sd
import numpy as np
import json
import base64
import io
from scipy.io.wavfile import read
from pydub import AudioSegment


class AudioController:
    def __init__(self, json_file="recording.json", fs=44100, channels=2):
        self.json_file = json_file
        self.fs = fs
        self.channels = channels
        self.is_recording = False
        self.is_paused = False
        self.audio_chunks = []
        self.stream = None
        self.playback_position = 0
        self.audio_to_play = None
        self.is_muted = False

    def _audio_callback(self, indata, frames, time, status):
        if self.is_recording and not self.is_paused:
            self.audio_chunks.append(indata.copy())

    def start_recording(self):
        if self.is_recording:
            return

        # Reset chunks for new recording
        self.audio_chunks = []
        self.is_recording = True
        self.is_paused = False
        self.stream = sd.InputStream(
            samplerate=self.fs,
            channels=self.channels,
            callback=self._audio_callback,
            dtype="int16",
        )
        self.stream.start()

    def pause_recording(self):
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            print("Recording paused.")
            return True
        return False

    def resume_recording(self):
        if self.is_recording and self.is_paused:
            self.is_paused = False
            print("Recording resumed.")
            return True
        return False

    def stop_recording(self, max_duration_ms=None):
        if not self.is_recording:
            return None

        self.is_recording = False
        self.is_paused = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.audio_chunks:
            return None

        # Combine chunks into single array
        recording = np.concatenate(self.audio_chunks, axis=0)
        self.audio_chunks = []

        # Convert NumPy array to AudioSegment
        audio_segment = AudioSegment(
            data=recording.tobytes(),
            sample_width=recording.dtype.itemsize,
            frame_rate=self.fs,
            channels=self.channels,
        )

        # Trim if necessary
        if max_duration_ms and len(audio_segment) > max_duration_ms:
            audio_segment = audio_segment[:max_duration_ms]

        # Export as MP3 to an in-memory buffer
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="mp3", bitrate="128k")
        mp3_bytes = buffer.getvalue()

        # Encode Base64
        encoded = base64.b64encode(mp3_bytes).decode("utf-8")
        data = {"sample_rate": self.fs, "audio_data": encoded, "format": "mp3"}

        return data

    def play_audio(self, audio_data):
        if self.is_muted or not audio_data or not audio_data.get("audio_data"):
            return False

        try:
            # Stop any currently playing audio first.
            self.stop_playing()

            audio_bytes = base64.b64decode(audio_data["audio_data"])
            audio_format = audio_data.get("format", "mp3")

            if audio_format == "mp3":
                audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                fs = audio.frame_rate
                raw_audio = np.array(audio.get_array_of_samples(), dtype=np.int16)
                if audio.channels == 2:
                    raw_audio = raw_audio.reshape((-1, 2))
                self.audio_to_play = raw_audio
                self.fs = fs
            else:  # Fallback for wav
                fs, audio = read(io.BytesIO(audio_bytes))
                self.audio_to_play = audio
                self.fs = fs

            # Play in non-blocking mode
            sd.play(self.audio_to_play, self.fs)
            print("Audio playback started for step.")
            return True
        except Exception as e:
            print(f"Playback error: {e}")
            self.audio_to_play = None
            return False

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop_playing()
        return self.is_muted

    def stop_playing(self):
        sd.stop()
        self.playback_position = 0
        self.audio_to_play = None
