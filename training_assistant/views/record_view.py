import tkinter as tk
from tkinter import ttk, messagebox
from views.home_view import BaseView

class RecordView(BaseView):
    def __init__(self, parent, controller, model):
        super().__init__(parent, controller, model)
        self.is_recording = False
        self.create_widgets()
        self.bind_shortcuts()
    
    def create_widgets(self):
        # Frame for the main content
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=40, pady=20)
        
        # Title
        ttk.Label(main_frame, text="Recording Mode", font=("Arial", 18, "bold")).pack(pady=(0, 20))
        
        # Tutorial Name Entry
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(pady=10)
        ttk.Label(name_frame, text="Tutorial Name:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.tutorial_name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.tutorial_name_var, width=40, font=("Arial", 12))
        self.name_entry.pack(side=tk.LEFT, expand=True, fill="x")
        
        # Recording controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(controls_frame, text="🔴 Start Recording",
                                   command=self.start_recording, width=20, style="Record.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(controls_frame, text="⏹ Stop Recording",
                                   command=self.stop_recording, width=20, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status Label
        self.status_var = tk.StringVar(value="Ready to record.")
        ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 10)).pack(pady=(10, 5))
        
        # Step Count Label
        self.step_count_var = tk.StringVar(value="Steps Recorded: 0")
        ttk.Label(main_frame, textvariable=self.step_count_var, font=("Arial", 10)).pack(pady=(0, 20))
        
        # Back button
        back_btn = ttk.Button(main_frame, text="← Back", command=self.controller.show_home, width=20)
        back_btn.pack(pady=20)
        
        self.create_record_style()

    def start_recording(self):
        tutorial_name = self.tutorial_name_var.get().strip()
        if not tutorial_name:
            messagebox.showerror("Error", "Please enter a tutorial name.")
            return

        if self.controller.recorder.start_recording(tutorial_name):
            self.is_recording = True
            self.name_entry.config(state='disabled')
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.update_status("Recording... Use F9 to pause/resume, F10 to undo.")
            
    def stop_recording(self):
        self.controller.recorder.stop_recording()
        self.is_recording = False
        self.name_entry.config(state='normal')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.update_status("Recording stopped.")
        self.update_step_count(0)
        
    def update_status(self, status):
        self.status_var.set(status)
        
    def update_step_count(self, count):
        self.step_count_var.set(f"Steps Recorded: {count}")
    
    def create_record_style(self):
        style = ttk.Style()
        style.configure("Record.TButton", background="#dc3545", foreground="#ffffff")
        style.map("Record.TButton", background=[('active', '#c82333')])
    
    def bind_shortcuts(self):
        shortcuts = self.model.settings["shortcuts"]
        self.controller.bind_all(shortcuts["back"], lambda e: self.controller.show_home())
        self.controller.bind_all(shortcuts["settings"], lambda e: self.controller.show_settings())