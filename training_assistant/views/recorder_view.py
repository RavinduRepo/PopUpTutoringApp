# views/recorder_view.py
import tkinter as tk
from tkinter import ttk
from views.home_view import BaseView


class RecordView(BaseView):
    def __init__(self, parent, controller, model):
        super().__init__(parent, controller, model)
        self.create_widgets()

    def create_widgets(self):
        # Frame for the main content
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=40, pady=20)

        # Title
        ttk.Label(main_frame, text="Recording Mode", font=("Arial", 18, "bold")).pack(
            pady=(0, 20)
        )

        # Tutorial Name Entry
        name_frame = ttk.Frame(main_frame)

        self.tutorial_name_var = tk.StringVar()
        self.name_entry = ttk.Entry(
            name_frame,
            textvariable=self.tutorial_name_var,
            width=40,
            font=("Arial", 12),
        )
        self.name_entry.pack(side=tk.LEFT, expand=True, fill="x")

        # Audio options frame
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Options", padding=10)
        audio_frame.pack(pady=10, fill="x")

        self.audio_option_var = tk.StringVar(value="No Audio")
        self.audio_duration_var = tk.StringVar(value="Until next step")

        def toggle_duration_menu():
            if self.audio_option_var.get() == "Include Audio":
                self.duration_menu.config(state="readonly")
            else:
                self.duration_menu.config(state="disabled")

        ttk.Radiobutton(
            audio_frame,
            text="No Audio",
            variable=self.audio_option_var,
            value="No Audio",
            command=toggle_duration_menu,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            audio_frame,
            text="Include Audio",
            variable=self.audio_option_var,
            value="Include Audio",
            command=toggle_duration_menu,
        ).pack(side=tk.LEFT, padx=5)

        self.duration_menu = ttk.Combobox(
            audio_frame,
            textvariable=self.audio_duration_var,
            values=["Until next step", "5 seconds", "10 seconds"],
            state="disabled",
            width=15,
        )
        self.duration_menu.pack(side=tk.LEFT, padx=10)

        # Recording controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(pady=20)

        self.start_btn = ttk.Button(
            controls_frame,
            text="🔴 Start Recording",
            command=lambda: self.controller.recorder.start_recording(
                self.audio_option_var.get(), self.audio_duration_var.get()
            ),
            width=20,
            style="Record.TButton",
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            controls_frame,
            text="⏹ Stop Recording",
            command=lambda: self.controller.recorder.stop_recording(),  # CALL CONTROLLER
            width=20,
            state="disabled",
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Status Label
        self.status_var = tk.StringVar(value="Ready to record.")
        ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 10)).pack(
            pady=(10, 5)
        )

        # Step Count Label
        self.step_count_var = tk.StringVar(value="Steps Recorded: 0")
        ttk.Label(
            main_frame, textvariable=self.step_count_var, font=("Arial", 10)
        ).pack(pady=(0, 20))

        # Back button
        back_btn = ttk.Button(
            main_frame, text="← Back", command=self.controller.show_home, width=20
        )
        back_btn.pack(pady=20)

        self.create_record_style()

    def update_status(self, status):
        """Updates the status label."""
        self.status_var.set(status)

    def update_step_count(self, count):
        """Updates the step count label."""
        self.step_count_var.set(f"Steps Recorded: {count}")

    def create_record_style(self):
        """Creates the custom button style."""
        style = ttk.Style()
        style.configure("Record.TButton", background="#dc3545", foreground="#ffffff")
        style.map("Record.TButton", background=[("active", "#c82333")])

    def update_ui_state(self, is_recording):
        """Updates the state of UI elements based on recording status."""
        state = "disabled" if is_recording else "normal"
        self.name_entry.config(state=state)
        self.start_btn.config(state="disabled" if is_recording else "normal")
        self.stop_btn.config(state="normal" if is_recording else "disabled")

