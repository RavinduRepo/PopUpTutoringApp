import tkinter as tk
from tkinter import ttk, messagebox
from views.home_view import BaseView

class SettingsView(BaseView):
    def __init__(self, parent, controller, model, settings_controller):
        super().__init__(parent, controller, model)
        self.settings_controller = settings_controller
        self.shortcut_buttons = {}
        self.shortcut_values = {}
        self.status_var = tk.StringVar(value="Click a shortcut button to capture a new hotkey.")
        self.create_widgets()
   
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
        # Create a container frame for the canvas and scrollbar
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Bind the frame to the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
       
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
       
        shortcuts_frame = ttk.LabelFrame(scrollable_frame, text="Keyboard Shortcuts", padding=20)
        shortcuts_frame.pack(fill="both", expand=True, pady=10)
       
        shortcuts_data = self.model.settings["shortcuts"]
       
        # Create main container with two columns
        columns_frame = ttk.Frame(shortcuts_frame)
        columns_frame.pack(fill="both", expand=True, pady=10)
        
        # Create left and right columns
        left_column = ttk.Frame(columns_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_column = ttk.Frame(columns_frame)
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Helper function to create sections for player and recorder
        def create_section(parent_frame, title, data_dict):
            section_frame = ttk.LabelFrame(parent_frame, text=title, padding=10)
            section_frame.pack(fill="x", pady=10)
           
            for key, value in data_dict.items():
                row_frame = ttk.Frame(section_frame)
                row_frame.pack(fill="x", pady=5)
               
                label_text = key.replace("_", " ").title() + ":"
                ttk.Label(row_frame, text=label_text, width=20).pack(side="left")
               
                # Create a button that shows the current shortcut value
                button = ttk.Button(row_frame, width=20, 
                                  command=lambda k=key, t=title: self.capture_shortcut(k, t))
                button.pack(side="left", padx=(10, 0))
               
                # Use a unique key for each button
                full_key = f"{title.lower()}_{key}"
                self.shortcut_buttons[full_key] = button
                self.shortcut_values[full_key] = value
                
                # Set initial button text to show current shortcut
                button.config(text=value if value else "Click to set")

        # Create the recorder shortcuts section (left side)
        create_section(left_column, "Recorder", shortcuts_data.get("recorder", {}))
       
        # Create the player shortcuts section (right side)
        create_section(right_column, "Player", shortcuts_data.get("player", {}))

        # Status Label to provide feedback to the user
        ttk.Label(shortcuts_frame, textvariable=self.status_var, font=("Arial", 10)).pack(pady=10)
       
    def capture_shortcut(self, key, section):
        """Initiates shortcut capture for the specified key."""
        full_key = f"{section.lower()}_{key}"
        button = self.shortcut_buttons[full_key]
        
        # Change button appearance to indicate capture mode
        button.config(text="Listening...", state="disabled")
        self.status_var.set(f"Press a hotkey for {key.replace('_', ' ').title()}...")
        
        # Notify the controller to start capturing
        self.settings_controller.start_hotkey_capture(full_key)

    def update_shortcut_button(self, full_key, hotkey_combo):
        """Updates the button text with the captured shortcut."""
        if full_key in self.shortcut_buttons:
            button = self.shortcut_buttons[full_key]
            button.config(text=hotkey_combo, state="normal")
            self.shortcut_values[full_key] = hotkey_combo

    def reset_capture_state(self):
        """Resets all buttons to normal state."""
        for button in self.shortcut_buttons.values():
            button.config(state="normal")

    def update_status(self, message):
        """Updates the status label."""
        self.status_var.set(message)
   
    def apply_settings(self):
        new_shortcuts = {
            "player": {},
            "recorder": {}
        }
       
        for full_key, value in self.shortcut_values.items():
            section, shortcut_name = full_key.split('_', 1)
            new_shortcuts[section][shortcut_name] = value
       
        self.settings_controller.apply_settings(self.theme_var.get(), new_shortcuts)
   
    def on_show(self):
        """Method to call when this view is raised."""
        self.settings_controller.on_show()
   
    def on_hide(self):
        """Method to call when this view is hidden."""
        self.settings_controller.on_hide()