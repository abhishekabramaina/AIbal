import json
import os

from src.utils import get_app_data_dir

SETTINGS_FILE = os.path.join(get_app_data_dir(), "config.json")

DEFAULT_SETTINGS = {
    "blink_target_interval": 6.0,  # seconds before screen starts to blur
    "fade_duration": 4.0,          # seconds to reach maximum blur
    "max_opacity": 0.85,           # maximum opacity of the blur overlay (0.0 to 1.0)
    "blur_radius": 25,             # how blurry the screen gets (px)
    "blink_threshold": 0.55,       # mediapipe blink threshold (0.0 to 1.0)
    "camera_index": 0,             # default webcam index
    "enable_vignette": True,       # show a smooth dark vignette
    "enable_text_reminder": True,  # show a gentle reminder text
    "text_reminder_delay": 2.0,    # seconds after blur starts before showing text
}

class AppSettings:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    loaded = json.load(f)
                    # Merge loaded settings into default to ensure new keys exist
                    for k, v in loaded.items():
                        if k in self.settings:
                            self.settings[k] = v
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        if key in self.settings:
            # Type casting to maintain data types
            orig_type = type(DEFAULT_SETTINGS[key])
            try:
                self.settings[key] = orig_type(value)
                self.save()
            except Exception as e:
                print(f"Error setting {key}: {e}")
