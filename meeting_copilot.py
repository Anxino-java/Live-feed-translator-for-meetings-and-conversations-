import io
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk
from google import genai
from google.genai import types
import numpy as np
import scipy.io.wavfile as wav
import soundcard as sc

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

SAMPLE_RATE = 16000
CHUNK_DURATION = 6
ENERGY_THRESHOLD = 0.015

MODELS_TO_TRY = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite"
]

ui_queue = queue.Queue()


def get_default_loopback():
    speaker = sc.default_speaker()
    return sc.get_microphone(id=str(speaker.name), include_loopback=True)


def audio_worker(stop_event):
    mic = get_default_loopback()
    chunk_frames = int(SAMPLE_RATE * CHUNK_DURATION)

    with mic.recorder(samplerate=SAMPLE_RATE, channels=1) as recorder:
        while not stop_event.is_set():
            data = recorder.record(numframes=chunk_frames)
            audio_mono = data[:, 0]

            energy = np.sqrt(np.mean(audio_mono**2))
            if energy < ENERGY_THRESHOLD:
                continue

            audio_int16 = np.int16(audio_mono * 32767)
            wav_io = io.BytesIO()
            wav.write(wav_io, SAMPLE_RATE, audio_int16)
            wav_bytes = wav_io.getvalue()

            prompt = (
                "You are an active meeting co-pilot. Listen carefully to this meeting audio segment.\n"
                "1. Provide a clean, accurate transcription of what was said.\n"
                "2. If the speaker is not using English, provide a one-line English translation.\n"
                "3. Provide two distinct, concise, professional suggestions for what the user should say next.\n"
                "4. CRITICAL: The suggestions must be written in the exact same language used by the speaker so the user can speak them aloud directly.\n"
                "If the audio contains only ambient noise or no recognizable speech, respond strictly with: NO_SPEECH\n\n"
                "Output strictly in this format:\n"
                "TRANSCRIPT:\n"
                "<transcribed text>\n\n"
                "RESPONSE:\n"
                "Translation: <translation or 'Same as input'>\n"
                "Suggestion 1: <first direct response>\n"
                "Suggestion 2: <second direct response>"
            )

            response = None
            last_err = None

            for model_name in MODELS_TO_TRY:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(
                                data=wav_bytes,
                                mime_type="audio/wav"
                            ),
                            prompt
                        ]
                    )
                    if response and response.text:
                        break
                except Exception as err:
                    last_err = err
                    continue

            if response is None or not response.text:
                if last_err:
                    ui_queue.put(("error", f"Failover exhausted: {str(last_err)}"))
                continue

            raw_text = response.text.strip()
            if not raw_text or "NO_SPEECH" in raw_text:
                continue

            if "RESPONSE:" in raw_text:
                parts = raw_text.split("RESPONSE:", 1)
                transcript = parts[0].replace("TRANSCRIPT:", "").strip()
                advice = parts[1].strip()
            else:
                transcript = "Audio processed"
                advice = raw_text

            ui_queue.put(("transcript", transcript))
            ui_queue.put(("suggestion", advice))


class MeetingCopilotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Meeting Co-Pilot - Gemini Edition")
        self.root.geometry("480x540")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1e2e")

        self.stop_event = threading.Event()
        self.worker_thread = None

        self._build_ui()
        self.root.after(100, self._process_queue)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        title_label = tk.Label(
            self.root,
            text="Meeting Co-Pilot",
            font=("Segoe UI", 12, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2e"
        )
        title_label.pack(pady=(12, 4))

        self.status_label = tk.Label(
            self.root,
            text="Status: Idle",
            font=("Segoe UI", 9),
            fg="#a6adc8",
            bg="#1e1e2e"
        )
        self.status_label.pack(pady=(0, 8))

        tk.Label(
            self.root,
            text="Live Meeting Audio Transcription:",
            font=("Segoe UI", 10, "bold"),
            fg="#89b4fa",
            bg="#1e1e2e",
            anchor="w"
        ).pack(fill="x", padx=16)

        self.txt_transcript = tk.Text(
            self.root,
            height=4,
            wrap="word",
            bg="#181825",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat",
            padx=8,
            pady=8,
            font=("Segoe UI", 10)
        )
        self.txt_transcript.pack(fill="x", padx=16, pady=(4, 12))

        tk.Label(
            self.root,
            text="Translation & What to Say Next:",
            font=("Segoe UI", 10, "bold"),
            fg="#a6e3a1",
            bg="#1e1e2e",
            anchor="w"
        ).pack(fill="x", padx=16)

        self.txt_suggestion = tk.Text(
            self.root,
            height=11,
            wrap="word",
            bg="#181825",
            fg="#a6e3a1",
            insertbackground="#a6e3a1",
            relief="flat",
            padx=8,
            pady=8,
            font=("Segoe UI", 10)
        )
        self.txt_suggestion.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        self.btn_toggle = tk.Button(
            self.root,
            text="Start Listening",
            command=self.toggle_listening,
            bg="#89b4fa",
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2"
        )
        self.btn_toggle.pack(pady=(0, 14))

    def toggle_listening(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_event.set()
            self.status_label.config(text="Status: Stopping...", fg="#f38ba8")
            self.btn_toggle.config(text="Start Listening", bg="#89b4fa")
            self.root.after(600, self._check_thread_stopped)
        else:
            self.stop_event.clear()
            self.worker_thread = threading.Thread(
                target=audio_worker,
                args=(self.stop_event,),
                daemon=True
            )
            self.worker_thread.start()
            self.status_label.config(text="Status: Active - Listening to Meeting", fg="#a6e3a1")
            self.btn_toggle.config(text="Stop Listening", bg="#f38ba8")

    def _check_thread_stopped(self):
        self.status_label.config(text="Status: Idle", fg="#a6adc8")

    def _process_queue(self):
        while not ui_queue.empty():
            msg_type, payload = ui_queue.get_nowait()
            if msg_type == "transcript":
                self.txt_transcript.delete("1.0", tk.END)
                self.txt_transcript.insert(tk.END, payload)
            elif msg_type == "suggestion":
                self.txt_suggestion.delete("1.0", tk.END)
                self.txt_suggestion.insert(tk.END, payload)
            elif msg_type == "error":
                self.status_label.config(text=payload, fg="#f38ba8")

        self.root.after(100, self._process_queue)


if __name__ == "__main__":
    app_root = tk.Tk()
    app = MeetingCopilotApp(app_root)
    app_root.mainloop()