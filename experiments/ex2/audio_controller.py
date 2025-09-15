import sounddevice as sd
import numpy as np
import json
import base64
import io
from scipy.io.wavfile import write, read


class AudioController:
    def __init__(self, json_file="recording.json", fs=44100, channels=2):
        self.json_file = json_file
        self.fs = fs
        self.channels = channels
        self.is_recording = False
        self.audio_chunks = []
        self.stream = None

    def _audio_callback(self, indata, frames, time, status):
        if self.is_recording:
            self.audio_chunks.append(indata.copy())

    def start_recording(self):
        if self.is_recording:
            return
        self.audio_chunks = []
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.fs,
            channels=self.channels,
            callback=self._audio_callback,
            dtype="int16",
        )
        self.stream.start()

    def stop_recording(self):
        if not self.is_recording:
            return False
        self.is_recording = False
        self.stream.stop()
        self.stream.close()

        # Combine chunks into single array
        recording = np.concatenate(self.audio_chunks, axis=0)

        # Save as WAV in memory
        buffer = io.BytesIO()
        write(buffer, self.fs, recording)
        wav_bytes = buffer.getvalue()

        # Encode Base64
        encoded = base64.b64encode(wav_bytes).decode("utf-8")
        data = {"sample_rate": self.fs, "audio_data": encoded}

        # Save JSON
        with open(self.json_file, "w") as f:
            json.dump(data, f)

        return True

    def play_audio(self):
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)

            wav_bytes = base64.b64decode(data["audio_data"])
            buffer = io.BytesIO(wav_bytes)
            fs, audio = read(buffer)

            sd.play(audio, fs)
            sd.wait()
            return True
        except Exception as e:
            print("Playback error:", e)
            return False
