import sys
from PySide6.QtWidgets import QApplication
from src.settings import AppSettings
from src.systray import SysTrayApp

def main():
    # Initialize the Qt Application
    app = QApplication(sys.argv)
    
    # Crucial for tray-based applications: prevent quitting when Settings window is closed
    app.setQuitOnLastWindowClosed(False)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", "-s", action="store_true", help="Open settings window directly at startup")
    args = parser.parse_args()
    
    # Load application settings
    settings = AppSettings()
    
    # Initialize and start the System Tray application controller
    tray_app = SysTrayApp(settings)
    
    if args.settings:
        tray_app.open_settings()
        
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
