import time
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QGuiApplication

from src.detector import BlinkDetector
from src.overlay import BlurOverlay
from src.settings_gui import SettingsWindow

def create_tray_icon(active=True):
    """
    Draws a custom vector icon dynamically for the system tray
    so no external files are required.
    """
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    if active:
        # Draw a beautiful open eye (Indigo/Cyan theme)
        painter.setPen(QPen(QColor(99, 102, 241), 2))  # Indigo-500
        painter.setBrush(QBrush(QColor(15, 23, 42)))   # Slate-900
        painter.drawEllipse(2, 6, 28, 20)              # Eye shape
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(6, 182, 212)))  # Cyan-500 iris
        painter.drawEllipse(11, 11, 10, 10)
        
        painter.setBrush(QBrush(QColor(255, 255, 255))) # Pupil highlight
        painter.drawEllipse(14, 12, 3, 3)
    else:
        # Draw a sleeping eye (closed) with eyelashes (Slate gray)
        painter.setPen(QPen(QColor(148, 163, 184), 2)) # Slate-400
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Arc representing the closed lid curved downwards
        # In Qt, angles are in 1/16th of a degree. 180 * 16 to 360 * 16 is bottom half
        painter.drawArc(4, 6, 24, 16, 180 * 16, 180 * 16)
        
        # Eyelashes
        painter.drawLine(16, 17, 16, 23)
        painter.drawLine(10, 15, 8, 20)
        painter.drawLine(22, 15, 24, 20)
        
    painter.end()
    return QIcon(pixmap)


class SysTrayApp(QObject):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.overlays = []
        self.settings_window = None
        self.is_paused = False
        
        # Initialize detector
        self.detector = BlinkDetector(self.settings)
        self.detector.status_changed.connect(self.on_status_changed)
        self.detector.error_occurred.connect(self.on_detector_error)
        
        # Create overlays for all active monitors
        self.rebuild_overlays()
        
        # Connect screen changes (plug/unplug monitors)
        QGuiApplication.instance().screenAdded.connect(self.rebuild_overlays)
        QGuiApplication.instance().screenRemoved.connect(self.rebuild_overlays)
        
        # Setup system tray icon
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(create_tray_icon(active=True))
        self.tray.setToolTip("AIbal - Blink Assistant")
        
        # Setup context menu
        self.setup_menu()
        self.tray.show()
        
        # Connect double-click to settings
        self.tray.activated.connect(self.on_tray_activated)
        
        # Main timer to poll blink status and control overlays (20 FPS)
        self.overlay_timer = QTimer(self)
        self.overlay_timer.setInterval(50)
        self.overlay_timer.timeout.connect(self.update_overlays)
        self.overlay_timer.start()

        # Start detection immediately
        self.start_monitoring()

    def setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 1px solid #1e293b;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
            }
            QMenu::item:selected {
                background-color: #312e81;
            }
        """)
        
        self.pause_action = menu.addAction("Pause Eye Monitor")
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(self.is_paused)
        self.pause_action.triggered.connect(self.toggle_pause)
        
        menu.addSeparator()
        
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.open_settings)
        
        menu.addSeparator()
        
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(QGuiApplication.quit)
        
        self.tray.setContextMenu(menu)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings()

    def toggle_pause(self):
        self.is_paused = self.pause_action.isChecked()
        if self.is_paused:
            self.stop_monitoring()
            self.tray.setIcon(create_tray_icon(active=False))
            self.tray.setToolTip("AIbal - Eye Monitor Paused")
        else:
            self.start_monitoring()
            self.tray.setIcon(create_tray_icon(active=True))
            self.tray.setToolTip("AIbal - Blink Assistant")

    def start_monitoring(self):
        if not self.detector.isRunning():
            self.detector.start()
        self.clear_all_blurs()

    def stop_monitoring(self):
        if self.detector.isRunning():
            self.detector.stop()
        self.clear_all_blurs()

    def rebuild_overlays(self):
        # Clean up old overlays safely
        self.clear_all_blurs()
        for overlay in self.overlays:
            overlay.close()
        self.overlays.clear()
        
        # Create a new overlay window for each monitor screen
        for screen in QGuiApplication.screens():
            overlay = BlurOverlay(screen, self.settings)
            self.overlays.append(overlay)

    def clear_all_blurs(self):
        for overlay in self.overlays:
            overlay.set_opacity(0.0)

    def update_overlays(self):
        if self.is_paused or not self.detector.is_running:
            self.clear_all_blurs()
            return
            
        elapsed = time.time() - self.detector.last_blink_time
        target_interval = self.settings.get("blink_target_interval")
        fade_duration = self.settings.get("fade_duration")
        max_opacity = self.settings.get("max_opacity")
        
        if elapsed <= target_interval:
            self.clear_all_blurs()
        else:
            time_since_blur_start = elapsed - target_interval
            pct = time_since_blur_start / fade_duration
            opacity = min(max_opacity, pct)
            
            for overlay in self.overlays:
                overlay.set_opacity(opacity, time_since_blur_start)

    def open_settings(self):
        # Bring settings window to front if already open
        if self.settings_window is not None:
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return

        self.settings_window = SettingsWindow(self.settings)
        
        # Route live tracker updates to settings monitor GUI if settings is open
        self.detector.blink_values.connect(self.settings_window.update_live_data)
        self.detector.face_detected.connect(self.settings_window.update_face_status)
        self.settings_window.settings_saved.connect(self.on_settings_saved)
        
        # Reset window reference when closed
        self.settings_window.finished.connect(self.cleanup_settings_window)
        self.settings_window.show()

    def cleanup_settings_window(self):
        if self.settings_window:
            # Disconnect signals to avoid crashes
            try:
                self.detector.blink_values.disconnect(self.settings_window.update_live_data)
                self.detector.face_detected.disconnect(self.settings_window.update_face_status)
            except Exception:
                pass
            self.settings_window = None

    def on_settings_saved(self):
        # If camera index changed, the detector will automatically reset itself in its loop
        self.clear_all_blurs()

    def on_status_changed(self, message):
        self.tray.setToolTip(f"AIbal: {message}")
        if self.settings_window:
            self.settings_window.face_status_label.setText(message)

    def on_detector_error(self, error_message):
        self.stop_monitoring()
        self.tray.setIcon(create_tray_icon(active=False))
        self.tray.setToolTip("AIbal - Error")
        
        # Show alert to user
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("AIbal Monitor Error")
        msg.setInformativeText(error_message)
        msg.setWindowTitle("AIbal Error")
        msg.exec()
        
        # Auto-check the pause item in the menu
        self.is_paused = True
        self.pause_action.setChecked(True)
