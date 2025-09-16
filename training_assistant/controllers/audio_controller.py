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

    def stop_recording(self):
        if not self.is_recording:
            return False

        self.is_recording = False
        self.is_paused = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()

        # Combine chunks into single array
        recording = np.concatenate(self.audio_chunks, axis=0)

        # Convert NumPy array to AudioSegment
        audio_segment = AudioSegment(
            data=recording.tobytes(),
            sample_width=recording.dtype.itemsize,
            frame_rate=self.fs,
            channels=self.channels,
        )

        # Export as MP3 to an in-memory buffer
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="mp3", bitrate="128k")
        mp3_bytes = buffer.getvalue()

        # Encode Base64
        encoded = base64.b64encode(mp3_bytes).decode("utf-8")
        data = {"sample_rate": self.fs, "audio_data": encoded, "format": "mp3"}

        # Save JSON
        with open(self.json_file, "w") as f:
            json.dump(data, f)

        return True

    def play_audio(self):
        try:
            # If not already loaded, load the audio file
            if self.audio_to_play is None:
                with open(self.json_file, "r") as f:
                    data = json.load(f)
                audio_bytes = base64.b64decode(data["audio_data"])
                audio_format = data.get("format", "wav")

                if audio_format == "mp3":
                    audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                    fs = audio.frame_rate
                    raw_audio = np.array(audio.get_array_of_samples(), dtype=np.int16)
                    if audio.channels == 2:
                        raw_audio = raw_audio.reshape((-1, 2))
                    self.audio_to_play = raw_audio
                else:
                    fs, audio = read(io.BytesIO(audio_bytes))
                    self.audio_to_play = audio

            # Play from the current playback position
            sd.play(self.audio_to_play[self.playback_position :], self.fs)

            print("Playback started/resumed.")
            sd.wait()
            self.playback_position = 0  # Reset when playback finishes
            self.audio_to_play = None  # Clear audio for next time
            return True
        except Exception as e:
            print("Playback error:", e)
            return False

    def pause_playing(self):
        if self.audio_to_play is not None and sd.get_stream().active:
            # Get the current position and stop the stream
            status = sd.get_stream()._read_and_write()
            self.playback_position += status.read_bytes / (
                self.fs * self.channels * self.audio_to_play.dtype.itemsize
            )
            sd.stop()
            print("Playback paused.")
            return True
        return False

    def stop_playing(self):
        sd.stop()
        self.playback_position = 0
        self.audio_to_play = None
        print("Playback stopped.")
