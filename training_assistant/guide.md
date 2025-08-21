
# Interactive Software Training Assistant – Development Guide

## Project Overview

A desktop application for **recording, editing, and playing back interactive tutorials** on Windows using **Python + Tkinter**.

### Features

* Record mouse clicks and screenshots
* Add notes per step
* Playback with overlays and guided execution
* Undo/pause recording
* Save/load tutorials (JSON + screenshots)
* Tutorial library with edit and playback options
* Secure handling (pause before typing sensitive input)

---

## Project Structure

```
training_assistant/
│
├── main.py          # Tkinter UI and navigation
├── recorder.py      # Mouse/keyboard recording + screenshot engine
├── player.py        # Playback engine with overlays
├── storage.py       # Save/load tutorial JSON + screenshot paths
├── models.py        # Step and Tutorial data classes
├── assets/          # Icons and UI images
└── tutorials/       # Saved tutorials and screenshots
```

---

## Phase 1 – Setup

1. Install Python 3.10+
2. Install dependencies:

```bash
pip install pillow mss pynput
```

3. Create project folders (`assets/`, `tutorials/`)

---

## Phase 2 – Core Data Model (0.5 day)

* Create `models.py` with `Step` class:

```python
class Step:
    def __init__(self, screenshot, coords, note=""):
        self.screenshot = screenshot
        self.coords = coords
        self.note = note
```

* JSON format example:

```json
{
  "tutorial": "Excel Basics",
  "steps": [
    {
      "screenshot": "step1.png",
      "coords": [450, 120],
      "note": "Click File menu"
    }
  ]
}
```

---

## Phase 3 – UI Skeleton (1–2 days)

* Use **Tkinter + ttk**
* Screens:

  1. HomeScreen: "Record", "Play", "Exit"
  2. RecordScreen: "Start Recording", "Stop Recording", "Back"
  3. PlayScreen: "Load Tutorial", "Back"
* Placeholders for button actions
* Implement **screen switching**
* File: `main.py` (full skeleton code provided earlier)

---

## Phase 4 – Recording Engine (2–3 days)

* File: `recorder.py`
* Features:

  * Start / Stop / Pause recording
  * Mouse click capture (pynput)
  * Screenshot capture (mss)
  * Store Step objects in memory
  * Undo last step
* Example functions:

```python
from pynput import mouse
import mss
from models import Step

class Recorder:
    def __init__(self):
        self.steps = []
        self.is_recording = False

    def start(self):
        self.is_recording = True

    def stop(self):
        self.is_recording = False

    def add_step(self, screenshot_path, coords, note=""):
        self.steps.append(Step(screenshot_path, coords, note))

    def undo_last_step(self):
        if self.steps:
            self.steps.pop()
```

* Integrate with `RecordScreen.start_recording()` in `main.py`

---

## Phase 5 – Tutorial Storage (1 day)

* File: `storage.py`
* Functions:

  * `save_tutorial(name, steps)` → saves JSON + screenshots
  * `load_tutorial(file)` → loads JSON into Step objects
* Handle **unfinished tutorials**

---

## Phase 6 – Playback Engine (3–4 days)

* File: `player.py`
* Features:

  * Load tutorial JSON + screenshots
  * Display current step: highlight area + show notes
  * Auto-advance if learner clicks correct spot
  * Manual Next / Back / Replay
  * Skip step if needed
* Example:

```python
class Player:
    def __init__(self, tutorial_file):
        self.steps = self.load_tutorial(tutorial_file)
        self.current_step = 0
```

---

## Phase 7 – Tutorial Editing (2–3 days)

* Open tutorial → List steps in Tkinter `Listbox`
* Edit notes
* Delete step
* Reorder steps (Up/Down buttons)
* Save updated JSON

---

## Phase 8 – File Management (1–2 days)

* List all tutorials in `tutorials/` folder
* Buttons: Play / Edit / Delete
* Export: single folder with JSON + screenshots
* Import: unzip folder into `tutorials/`

---

## Phase 9 – Security & Reliability (1–2 days)

* Pause recording before typing sensitive data
* Save temp JSON after every click for crash recovery
* Playback handles missing screenshots gracefully

---

## Phase 10 – UI Polish (2–3 days)

* Use `ttk` widgets for clean look
* Add progress bar: "Step X of Y"
* Add icons for buttons
* Simple onboarding screen (Home → Record / Play)

---

## Phase 11 – Packaging & Distribution (1–2 days)

* Use **PyInstaller**:

```bash
pyinstaller --onefile --noconsole main.py
```

* Test on clean Windows machine
* Optional installer: Inno Setup or NSIS

---

## Suggested Timeline

| Phase                  | Duration            |
| ---------------------- | ------------------- |
| Setup                  | 1–2 days            |
| Core Data Model        | 0.5 day             |
| UI Skeleton            | 1–2 days            |
| Recording Engine       | 2–3 days            |
| Storage                | 1 day               |
| Playback Engine        | 3–4 days            |
| Editing                | 2–3 days            |
| File Management        | 1–2 days            |
| Security & Reliability | 1–2 days            |
| UI Polish              | 2–3 days            |
| Packaging              | 1–2 days            |
| **Total**              | \~15 days full-time |

---

### ✅ Notes

* All **Tkinter UI logic** goes in `main.py`
* `recorder.py` and `player.py` handle backend logic
* `storage.py` handles JSON & screenshot files
* Modular design → easy to extend (e.g., library, cloud sync)
* Start simple: recording + saving steps first, then playback, then editing

---

I can also **write the first working `recorder.py` with mouse clicks + screenshot capture** next, fully ready to plug into this skeleton.

Do you want me to do that?
