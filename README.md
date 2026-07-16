# Aibal 👁️

**AIbal** is a smart desktop application designed to prevent eye strain and dry eyes for software engineers. It monitors your blink rate in the background using your webcam and gently blurs the screen if you go too long without blinking, triggering your natural blink reflex.

---

## ✨ Features

- **Webcam-Based Eye Tracking:** Uses Google's **MediaPipe Face Landmarker** to track precise blink scores (`eyeBlinkLeft`, `eyeBlinkRight`) rather than crude movement.
- **Hardware-Accelerated Blur:** Captures a snapshot of all active displays and overlays a hardware-accelerated blur, vignetted shadow, and gentle text reminder when a blink is overdue.
- **Instant Reset:** The screen returns to normal the exact millisecond you blink.
- **Tray-First Layout:** Minimizes to the Windows System Tray with a custom vector eyeball icon that changes dynamically (glowing blue when active, sleeping eyelashes when paused).
- **Privacy-focused Pausing:** Instantly releases your camera handle when paused, turning off your camera light indicator and freeing it up for video calls (Zoom, Teams, Meet).
- **Dynamic Multi-Monitor Support:** Automatically adapts to monitor additions/removals without restarting the application.
- **Auto Calibration:** Counts down 5 seconds to calibrate your natural open/closed eye threshold.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **PySide6** (Qt for Python)
- **OpenCV** (Camera Capture)
- **MediaPipe** (Face Mesh / Blendshape Inference)

---

## 🚀 Setup & Installation

### 1. Clone and Navigate
```bash
git clone https://github.com/abhishekabramaina/AIbal.git
cd AIbal
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
```

### 3. Activate the Environment
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Note: On the first application run, the app will automatically download the 33MB `face_landmarker.task` model file to the local `models/` directory).*

---

## 🎮 How to Run

### Standard Run (runs in system tray):
```bash
python main.py
```

### Run and Open Settings Dashboard Directly:
```bash
python main.py --settings
```

---

## ⚙️ Calibration

1. Right-click the eyeball icon in the system tray and select **Settings...** (or double-click the icon).
2. Ensure your face is tracked (the status label will show **"Tracking Active"**).
3. Click **Auto Calibrate** and blink normally for 5 seconds.
4. The dashboard will automatically set your custom sensitivity threshold based on your eye shape.
5. Click **Save Settings** to complete.

---

## 📜 License
Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
