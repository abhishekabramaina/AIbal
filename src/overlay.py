from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QWidget, QLabel, QGraphicsBlurEffect, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QFont, QPixmap, QGuiApplication

class OverlayUI(QWidget):
    """
    Transparent widget that overlays on top of the blurred screenshot
    to render the vignette and text reminders.
    """
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.show_text = False
        
        # Make transparent for input so clicks go through
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        # 1. Draw Vignette
        if self.settings.get("enable_vignette"):
            # Center of the screen
            center = QPointF(w / 2.0, h / 2.0)
            # Radial gradient covering the screen corners
            gradient = QRadialGradient(center, max(w, h) / 1.4)
            # Color points: center is transparent, edges are dark
            gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
            gradient.setColorAt(0.5, QColor(0, 0, 0, 60))
            gradient.setColorAt(0.9, QColor(0, 0, 0, 180))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 240))
            
            painter.fillRect(self.rect(), gradient)

        # 2. Draw Text Reminder
        if self.settings.get("enable_text_reminder") and self.show_text:
            # Set font configuration
            title_font = QFont("Segoe UI", 32, QFont.Weight.Bold)
            subtitle_font = QFont("Segoe UI", 16, QFont.Weight.Normal)
            
            # Title
            painter.setFont(title_font)
            painter.setPen(QColor(255, 255, 255, 230))
            rect = self.rect()
            # Draw title slightly offset upward
            title_rect = rect.adjusted(0, -40, 0, -40)
            painter.drawText(title_rect, Qt.AlignCenter, "Blink your eyes")
            
            # Subtitle
            painter.setFont(subtitle_font)
            painter.setPen(QColor(255, 255, 255, 160))
            subtitle_rect = rect.adjusted(0, 40, 0, 40)
            painter.drawText(subtitle_rect, Qt.AlignCenter, "to restore focus")


class BlurOverlay(QWidget):
    """
    Full-screen overlay widget that captures a screenshot, blurs it,
    and fades it in to force the user to blink.
    """
    def __init__(self, screen, settings):
        super().__init__()
        self.setScreen(screen)
        self.settings = settings
        self.screenshot_captured = False

        # Set window properties: Frameless, click-through, always-on-top, hide from taskbar
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool  # Prevents showing up in Alt-Tab list
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Ensure correct geometry covering the target screen
        self.setGeometry(screen.geometry())

        # Setup layout: Label for blur, overlaid by UI for vignette/text
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Label to display the blurred screenshot
        self.blur_label = QLabel(self)
        self.blur_label.setScaledContents(True)
        self.layout.addWidget(self.blur_label)

        # Graphics blur effect
        self.blur_effect = QGraphicsBlurEffect(self)
        self.blur_effect.setBlurRadius(self.settings.get("blur_radius"))
        self.blur_label.setGraphicsEffect(self.blur_effect)

        # UI Overlay widget (Vignette & Text)
        self.ui_overlay = OverlayUI(self.settings, self)
        self.ui_overlay.setGeometry(self.rect())
        self.ui_overlay.show()

        # Keep overlay UI covering the whole widget on resize
        self.resizeEvent = self.on_resize

    def on_resize(self, event):
        self.ui_overlay.setGeometry(self.rect())
        super().resizeEvent(event)

    def capture_screenshot(self):
        # Temporarily hide our window to avoid capturing ourselves
        was_visible = self.isVisible()
        if was_visible:
            self.setWindowOpacity(0.0)
            QGuiApplication.processEvents()

        # Capture the screen
        screen = self.screen()
        if screen:
            pixmap = screen.grabWindow(0)
            self.blur_label.setPixmap(pixmap)
            self.screenshot_captured = True

        if was_visible:
            # Let caller restore opacity
            pass

    def set_opacity(self, opacity, time_since_blur_start=0.0):
        # Live-update blur radius from settings
        self.blur_effect.setBlurRadius(self.settings.get("blur_radius"))
        
        if opacity <= 0.0:
            if self.screenshot_captured:
                self.blur_label.clear()
                self.screenshot_captured = False
                self.ui_overlay.show_text = False
                self.hide()
            return

        # Capture screenshot if not already done
        if not self.screenshot_captured:
            self.capture_screenshot()

        # Toggle text reminder based on delay
        text_delay = self.settings.get("text_reminder_delay")
        self.ui_overlay.show_text = (time_since_blur_start >= text_delay)

        self.setWindowOpacity(opacity)
        
        if not self.isVisible():
            self.show()
            # On Windows, occasionally need to raise the window to ensure it stays on top
            self.raise_()
        
        # Trigger repaint of text/vignette
        self.ui_overlay.update()
