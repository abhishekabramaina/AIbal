import os
import sys

def get_app_data_dir():
    """
    Returns the path to the directory where user-specific application data
    (like settings and models) should be stored.
    Creates the directory if it does not exist.
    """
    if sys.platform == "win32":
        # Windows: C:\\Users\\<Username>\\AppData\\Local\\AIbal
        base_dir = os.environ.get("LOCALAPPDATA")
        if not base_dir:
            base_dir = os.path.expanduser("~")
    else:
        # macOS/Linux fallback
        base_dir = os.path.expanduser("~")
        
    app_dir = os.path.join(base_dir, "AIbal")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir
