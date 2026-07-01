from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QComboBox, QCheckBox, QPushButton, 
                             QGroupBox, QFormLayout, QProgressBar)
from PySide6.QtGui import QFont, QIcon, QPainter, QColor

class CustomProgressBar(QProgressBar):
    """
    Custom progress bar that draws a threshold line on top.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.threshold = 0.55
        self.setTextVisible(False)

    def set_threshold(self, threshold):
        self.threshold = threshold
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        
        # Draw threshold line
        if self.minimum() < self.maximum():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Calculate position
            val_range = self.maximum() - self.minimum()
            pct = (self.threshold - self.minimum()) / val_range
            x = int(self.width() * pct)
            
            # Draw glowing line at the threshold
            painter.setPen(QColor(239, 68, 68, 200))  # Light red (Tailwind red-500)
            painter.drawLine(x, 0, x, self.height())
            
            # Draw a small tick at the top of the threshold line
            painter.setBrush(QColor(239, 68, 68))
            painter.drawRect(x - 2, 0, 4, 4)


class SettingsWindow(QDialog):
    settings_saved = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.calibration_ticks = 0
        self.calibration_scores = []
        
        self.setWindowTitle("AIbal Settings")
        self.setMinimumSize(420, 560)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        
        # Apply CSS Stylesheet for visual excellence
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a; /* Deep Slate 900 */
                color: #f1f5f9;
            }
            QLabel {
                color: #cbd5e1;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: bold;
                color: #818cf8; /* Light Indigo */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #4f46e5; /* Indigo 600 */
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
            QPushButton#calibrateBtn {
                background-color: #0d9488; /* Teal 600 */
            }
            QPushButton#calibrateBtn:hover {
                background-color: #0f766e;
            }
            QPushButton#cancelBtn {
                background-color: #334155;
            }
            QPushButton#cancelBtn:hover {
                background-color: #1e293b;
            }
            QSlider::groove:horizontal {
                border: 1px solid #1e293b;
                height: 6px;
                background: #1e293b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #6366f1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #f1f5f9;
                border: 1px solid #6366f1;
                width: 14px;
                height: 14px;
                margin-top: -4px;
                border-radius: 7px;
            }
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 5px;
                color: white;
            }
            QProgressBar {
                border: 1px solid #1e293b;
                border-radius: 6px;
                background-color: #1e293b;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border-radius: 5px;
            }
        """)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        
        title_label = QLabel("AIbal Dashboard")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        
        subtitle_label = QLabel("Eye blink monitoring and strain relief")
        subtitle_label.setFont(QFont("Segoe UI", 10))
        subtitle_label.setStyleSheet("color: #64748b;")
        
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        header_layout.addLayout(header_text_layout)
        main_layout.addLayout(header_layout)

        # 1. Real-time feedback Widget
        fb_group = QGroupBox("Real-time Monitor")
        fb_layout = QVBoxLayout(fb_group)
        fb_layout.setSpacing(10)
        
        status_row = QHBoxLayout()
        self.face_status_label = QLabel("Initializing camera...")
        self.face_status_label.setStyleSheet("font-weight: bold; color: #f59e0b;") # Amber
        status_row.addWidget(QLabel("Face Status:"))
        status_row.addWidget(self.face_status_label, 0, Qt.AlignmentFlag.AlignRight)
        fb_layout.addLayout(status_row)
        
        # Blink score progress bar
        self.blink_bar = CustomProgressBar(self)
        self.blink_bar.setRange(0, 100)
        self.blink_bar.setValue(0)
        self.blink_bar.set_threshold(self.settings.get("blink_threshold"))
        fb_layout.addWidget(QLabel("Eye Closedness Score:"))
        fb_layout.addWidget(self.blink_bar)
        
        # Calibration button
        self.calibrate_btn = QPushButton("Auto Calibrate", self)
        self.calibrate_btn.setObjectName("calibrateBtn")
        self.calibrate_btn.clicked.connect(self.start_calibration)
        fb_layout.addWidget(self.calibrate_btn)
        
        main_layout.addWidget(fb_group)

        # 2. Settings Group
        settings_group = QGroupBox("Parameters")
        form_layout = QFormLayout(settings_group)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(12, 16, 12, 12)

        # Camera dropdown
        self.camera_combo = QComboBox(self)
        self.camera_combo.addItems(["Camera 0 (Default)", "Camera 1", "Camera 2", "Camera 3"])
        self.camera_combo.setCurrentIndex(self.settings.get("camera_index"))
        form_layout.addRow("Webcam Source:", self.camera_combo)

        # Target Interval
        self.interval_label = QLabel(f'{self.settings.get("blink_target_interval"):.1f} seconds')
        self.interval_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.interval_slider.setRange(20, 200) # 2.0s to 20.0s
        self.interval_slider.setValue(int(self.settings.get("blink_target_interval") * 10))
        self.interval_slider.valueChanged.connect(self.on_interval_changed)
        
        interval_row = QHBoxLayout()
        interval_row.addWidget(self.interval_slider)
        interval_row.addWidget(self.interval_label)
        form_layout.addRow("Blink Target:", interval_row)

        # Blink Threshold
        self.threshold_label = QLabel(f'{self.settings.get("blink_threshold"):.2f}')
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.threshold_slider.setRange(10, 95) # 0.10 to 0.95
        self.threshold_slider.setValue(int(self.settings.get("blink_threshold") * 100))
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(self.threshold_slider)
        threshold_row.addWidget(self.threshold_label)
        form_layout.addRow("Blink Sensitivity:", threshold_row)

        # Blur Intensity
        self.blur_label = QLabel(f'{self.settings.get("blur_radius")} px')
        self.blur_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.blur_slider.setRange(5, 50)
        self.blur_slider.setValue(self.settings.get("blur_radius"))
        self.blur_slider.valueChanged.connect(self.on_blur_changed)
        
        blur_row = QHBoxLayout()
        blur_row.addWidget(self.blur_slider)
        blur_row.addWidget(self.blur_label)
        form_layout.addRow("Blur Intensity:", blur_row)

        # Options Checklist
        self.vignette_check = QCheckBox("Enable dark vignette edge effect", self)
        self.vignette_check.setChecked(self.settings.get("enable_vignette"))
        
        self.text_check = QCheckBox("Enable gentle text reminder", self)
        self.text_check.setChecked(self.settings.get("enable_text_reminder"))
        
        form_layout.addRow("", self.vignette_check)
        form_layout.addRow("", self.text_check)

        main_layout.addWidget(settings_group)

        # Buttons Row
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings", self)
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

        # Calibration Timer
        self.calibration_timer = QTimer(self)
        self.calibration_timer.setInterval(100) # 10 samples per sec
        self.calibration_timer.timeout.connect(self.on_calibration_tick)

    def on_interval_changed(self, val):
        self.interval_label.setText(f"{val / 10.0:.1f} seconds")

    def on_threshold_changed(self, val):
        t = val / 100.0
        self.threshold_label.setText(f"{t:.2f}")
        self.blink_bar.set_threshold(t)
        self.settings.set("blink_threshold", t) # Instant feedback during monitor

    def on_blur_changed(self, val):
        self.blur_label.setText(f"{val} px")

    def update_live_data(self, blink_l, blink_r):
        avg = (blink_l + blink_r) / 2.0
        self.blink_bar.setValue(int(avg * 100))
        
        # If in calibration phase, record scores
        if self.calibration_timer.isActive():
            self.calibration_scores.append(avg)

    def update_face_status(self, face_detected):
        if self.calibration_timer.isActive():
            return
            
        if face_detected:
            self.face_status_label.setText("Tracking Active")
            self.face_status_label.setStyleSheet("font-weight: bold; color: #10b981;") # Green
        else:
            self.face_status_label.setText("No Face Detected")
            self.face_status_label.setStyleSheet("font-weight: bold; color: #ef4444;") # Red
            self.blink_bar.setValue(0)

    def start_calibration(self):
        self.calibrate_btn.setEnabled(False)
        self.face_status_label.setText("LOOK AT SCREEN AND BLINK NORMALLY...")
        self.face_status_label.setStyleSheet("font-weight: bold; color: #06b6d4;") # Cyan
        self.calibration_scores = []
        self.calibration_ticks = 50 # 5 seconds
        self.calibration_timer.start()

    def on_calibration_tick(self):
        self.calibration_ticks -= 1
        if self.calibration_ticks % 10 == 0:
            secs_left = self.calibration_ticks // 10
            self.face_status_label.setText(f"Calibrating... {secs_left}s remaining")
            
        if self.calibration_ticks <= 0:
            self.calibration_timer.stop()
            self.calibrate_btn.setEnabled(True)
            self.face_status_label.setText("Calibration Complete!")
            self.face_status_label.setStyleSheet("font-weight: bold; color: #10b981;")
            
            # Analyze scores to find optimal threshold
            if self.calibration_scores:
                # Typically, during 5s, the user will be looking at the screen open-eyed (low score)
                # and blinking occasionally (high spikes).
                # We want to identify the normal open eye score and set the threshold just above it.
                # Let's sort the scores and find the 75th percentile as a baseline for open eyes,
                # then place the threshold halfway between that and 1.0, or use a set multiplier.
                self.calibration_scores.sort()
                # 80% of the time, the eyes are open. Let's take the 50th percentile (median) as open eye base.
                idx_median = int(len(self.calibration_scores) * 0.50)
                median_open = self.calibration_scores[idx_median]
                
                # Let's calculate a robust threshold:
                # If median open is very low (e.g. 0.15), threshold can be 0.45 or 0.5.
                # A good general threshold is median_open + 0.35, clamped between 0.35 and 0.75.
                optimal_threshold = max(0.35, min(0.75, median_open + 0.30))
                
                # Update slider
                self.threshold_slider.setValue(int(optimal_threshold * 100))
                self.threshold_label.setText(f"{optimal_threshold:.2f}")
                self.blink_bar.set_threshold(optimal_threshold)
                self.settings.set("blink_threshold", optimal_threshold)

    def save_settings(self):
        # Save all config items
        self.settings.set("camera_index", self.camera_combo.currentIndex())
        self.settings.set("blink_target_interval", self.interval_slider.value() / 10.0)
        self.settings.set("blink_threshold", self.threshold_slider.value() / 100.0)
        self.settings.set("blur_radius", self.blur_slider.value())
        self.settings.set("enable_vignette", self.vignette_check.isChecked())
        self.settings.set("enable_text_reminder", self.text_check.isChecked())
        self.settings.save()
        
        self.settings_saved.emit()
        self.accept()
