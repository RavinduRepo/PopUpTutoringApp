# views/home_view.py
import tkinter as tk
from tkinter import ttk

class BaseView(tk.Frame):
    def __init__(self, parent, controller, model):
        super().__init__(parent)
        self.controller = controller
        self.model = model
        self.configure_style()
    
    def configure_style(self):
        self.update_theme()
    
    def update_theme(self):
        theme = self.model.settings["theme"]
        if theme == "dark":
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            btn_bg = "#404040"
        else:
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            btn_bg = "#e1e1e1"
        
        self.configure(bg=bg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        if theme == "dark":
            style.configure('TFrame', background='#2b2b2b')
            style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
            style.configure('TButton', background='#404040', foreground='#ffffff')
            style.map('TButton', background=[('active', '#555555')])
        else:
            style.configure('TFrame', background='#f0f0f0')
            style.configure('TLabel', background='#f0f0f0', foreground='#000000')
            style.configure('TButton', background='#e1e1e1', foreground='#000000')
            style.map('TButton', background=[('active', '#d5d5d5')])


class HomeView(BaseView):
    def __init__(self, parent, controller, model):
        super().__init__(parent, controller, model)
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="Interactive Training Assistant",
                 font=("Arial", 20, "bold")).pack(pady=30)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(anchor="center")
        
        ttk.Label(content_frame, text="Choose an option:",
                 font=("Arial", 14)).pack(pady=(0, 30))
        
        self.record_btn = ttk.Button(content_frame, text="📹 Record Tutorial",
                                    command=self.controller.show_record,
                                    width=20, style="Accent.TButton")
        self.record_btn.pack(pady=10)
        
        self.play_btn = ttk.Button(content_frame, text="▶ Play Tutorial",
                                  command=self.controller.show_play,
                                  width=20, style="Accent.TButton")
        self.play_btn.pack(pady=10)
        
        self.exit_btn = ttk.Button(content_frame, text="✕ Exit",
                                  command=self.controller.quit_app,
                                  width=20)
        self.exit_btn.pack(pady=20)
        
        self.create_accent_style()
    
    def create_accent_style(self):
        style = ttk.Style()
        if self.model.settings["theme"] == "dark":
            style.configure("Accent.TButton", background="#0d7377", foreground="#ffffff")
            style.map("Accent.TButton", background=[('active', '#14a085')])
        else:
            style.configure("Accent.TButton", background="#007acc", foreground="#ffffff")
            style.map("Accent.TButton", background=[('active', '#005a9e')])
    
    def update_theme(self):
        super().update_theme()
        self.create_accent_style()
