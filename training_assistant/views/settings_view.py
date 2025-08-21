import tkinter as tk
from tkinter import ttk, messagebox
from views.home_view import BaseView

class SettingsView(BaseView):
    def __init__(self, parent, controller, model):
        super().__init__(parent, controller, model)
        self.shortcut_entries = {}
        self.create_widgets()
        self.bind_shortcuts()
    
    def create_widgets(self):
        ttk.Label(self, text="Settings",
                 font=("Arial", 18, "bold")).pack(pady=20)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=40, pady=20)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        appearance_frame = ttk.Frame(notebook)
        shortcuts_frame = ttk.Frame(notebook)
        
        notebook.add(appearance_frame, text="Appearance")
        notebook.add(shortcuts_frame, text="Shortcuts")
        
        self.create_appearance_tab(appearance_frame)
        self.create_shortcuts_tab(shortcuts_frame)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="← Back",
                  command=self.controller.show_home).pack(side="left")
        
        ttk.Button(button_frame, text="Apply",
                  command=self.apply_settings).pack(side="right", padx=(10, 0))
    
    def create_appearance_tab(self, parent):
        theme_frame = ttk.LabelFrame(parent, text="Theme", padding=20)
        theme_frame.pack(fill="x", pady=10)
        
        self.theme_var = tk.StringVar(value=self.model.settings["theme"])
        
        ttk.Radiobutton(theme_frame, text="Light Mode", variable=self.theme_var,
                       value="light").pack(anchor="w", pady=5)
        ttk.Radiobutton(theme_frame, text="Dark Mode", variable=self.theme_var,
                       value="dark").pack(anchor="w", pady=5)
    
    def create_shortcuts_tab(self, parent):
        shortcuts_frame = ttk.LabelFrame(parent, text="Keyboard Shortcuts", padding=20)
        shortcuts_frame.pack(fill="both", expand=True, pady=10)
        
        shortcuts = self.model.settings["shortcuts"]
        labels = {
            "record": "Record Tutorial:",
            "play": "Play Tutorial:",
            "settings": "Open Settings:",
            "back": "Go Back:"
        }
        
        for i, (key, label) in enumerate(labels.items()):
            row_frame = ttk.Frame(shortcuts_frame)
            row_frame.pack(fill="x", pady=5)
            
            ttk.Label(row_frame, text=label, width=20).pack(side="left")
            
            entry = ttk.Entry(row_frame, width=20)
            entry.pack(side="left", padx=(10, 0))
            entry.insert(0, shortcuts[key])
            
            self.shortcut_entries[key] = entry
    
    def apply_settings(self):
        self.model.update_setting("theme", self.theme_var.get())
        
        new_shortcuts = {}
        for key, entry in self.shortcut_entries.items():
            new_shortcuts[key] = entry.get()
        
        self.model.update_setting("shortcuts", new_shortcuts)
        self.controller.update_theme()
        self.controller.rebind_shortcuts()
        
        messagebox.showinfo("Settings", "Settings applied successfully!")
    
    def bind_shortcuts(self):
        shortcuts = self.model.settings["shortcuts"]
        self.controller.bind_all(shortcuts["back"], lambda e: self.controller.show_home())
