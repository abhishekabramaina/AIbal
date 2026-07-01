import os
import cv2
import time
import urllib.request
import mediapipe as mp
from PySide6.QtCore import QThread, Signal

# Download URL for the face landmarker model
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "face_landmarker.task")

class BlinkDetector(QThread):
    status_changed = Signal(str)
    blink_detected = Signal()
    blink_values = Signal(float, float)  # (left_score, right_score)
    face_detected = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_running = False
        self.is_interrupted = False
        
        # Thread-safe control flags
        self.camera_index = self.settings.get("camera_index")
        self.blink_threshold = self.settings.get("blink_threshold")
        self.eyes_closed = False
        self.last_blink_time = time.time()

    def run(self):
        self.is_running = True
        self.is_interrupted = False
        
        # Step 1: Ensure model exists
        if not self._ensure_model_exists():
            self.error_occurred.emit("Failed to download or verify the face detection model.")
            self.is_running = False
            return

        # Step 2: Initialize MediaPipe Face Landmarker
        self.status_changed.emit("Initializing Face Landmarker...")
        try:
            BaseOptions = mp.tasks.BaseOptions
            FaceLandmarker = mp.tasks.vision.FaceLandmarker
            FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode

            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=VisionRunningMode.IMAGE,
                output_face_blendshapes=True
            )
            landmarker = FaceLandmarker.create_from_options(options)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load model: {str(e)}")
            self.is_running = False
            return

        # Step 3: Open Camera
        self.status_changed.emit("Opening camera...")
        # On Windows, cv2.CAP_DSHOW is much faster to initialize
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Fallback to default backend
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                self.error_occurred.emit(f"Could not open camera index {self.camera_index}.")
                landmarker.close()
                self.is_running = False
                return

        self.status_changed.emit("Blink detector active")
        self.last_blink_time = time.time()

        try:
            while not self.is_interrupted:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                # Convert to RGB (MediaPipe expects RGB)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Create MediaPipe Image object
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                # Run landmarker detection
                result = landmarker.detect(mp_image)
                
                face_found = bool(result.face_blendshapes)
                self.face_detected.emit(face_found)
                
                if face_found:
                    blendshapes = result.face_blendshapes[0]
                    blink_l = 0.0
                    blink_r = 0.0
                    
                    for category in blendshapes:
                        if category.category_name == "eyeBlinkLeft":
                            blink_l = category.score
                        elif category.category_name == "eyeBlinkRight":
                            blink_r = category.score
                            
                    self.blink_values.emit(blink_l, blink_r)
                    
                    # Compute average blink score
                    avg_blink = (blink_l + blink_r) / 2.0
                    
                    # Update threshold in real-time from settings
                    self.blink_threshold = self.settings.get("blink_threshold")
                    
                    if avg_blink >= self.blink_threshold:
                        # Reset blink timer while eyes are closed
                        self.last_blink_time = time.time()
                        if not self.eyes_closed:
                            self.eyes_closed = True
                            self.blink_detected.emit()
                    else:
                        self.eyes_closed = False
                
                # Check for camera index updates at runtime
                current_cam = self.settings.get("camera_index")
                if current_cam != self.camera_index:
                    self.status_changed.emit(f"Switching camera to index {current_cam}...")
                    cap.release()
                    cap = cv2.VideoCapture(current_cam, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        cap = cv2.VideoCapture(current_cam)
                    if cap.isOpened():
                        self.camera_index = current_cam
                        self.status_changed.emit("Blink detector active")
                    else:
                        self.error_occurred.emit(f"Failed to open camera index {current_cam}.")
                
                # Control loop speed (15 FPS is plenty and saves CPU)
                time.sleep(1.0 / 15.0)
                
        except Exception as e:
            self.error_occurred.emit(f"Runtime error in detector: {str(e)}")
        finally:
            cap.release()
            landmarker.close()
            self.is_running = False
            self.status_changed.emit("Blink detector stopped")

    def stop(self):
        self.is_interrupted = True
        self.wait()

    def _ensure_model_exists(self):
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)

        if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10 * 1024 * 1024:
            return True

        self.status_changed.emit("Downloading face detection model (approx. 33MB)...")
        try:
            # Simple chunked downloader to prevent blocking too long and write progress
            # but urlretrieve is simple and works.
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            return True
        except Exception as e:
            print(f"Error downloading model: {e}")
            return False
