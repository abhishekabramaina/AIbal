import os
import sys
import subprocess

def run_command(command):
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error details:")
        print(result.stdout)
        print(result.stderr)
        return False
    print("Success!")
    return True

def main():
    print("AIbal Executable Packaging Script")
    print("--------------------------------")
    
    # 1. Check if pyinstaller is installed
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        pip_ext = ".exe" if sys.platform == "win32" else ""
        pip_path = os.path.join(".venv", "Scripts", f"pip{pip_ext}") if os.path.exists(os.path.join(".venv", "Scripts", f"pip{pip_ext}")) else f"pip{pip_ext}"
        if not run_command([pip_path, "install", "pyinstaller"]):
            print("Failed to install PyInstaller. Exiting.")
            sys.exit(1)

    # 2. Build the PyInstaller command
    # We use --onedir (folder mode) for faster startups and better antivirus compatibility,
    # and --noconsole to hide the command prompt window.
    pyinstaller_ext = ".exe" if sys.platform == "win32" else ""
    pyinstaller_bin = os.path.join(".venv", "Scripts", f"pyinstaller{pyinstaller_ext}") if os.path.exists(os.path.join(".venv", "Scripts", f"pyinstaller{pyinstaller_ext}")) else f"pyinstaller{pyinstaller_ext}"
    
    cmd = [
        pyinstaller_bin,
        "--noconsole",
        "--clean",
        "--onedir",
        "--name=AIbal",
        "main.py"
    ]
    
    print("\nStarting compilation process...")
    if run_command(cmd):
        print("\n=======================================================")
        print("BUILD SUCCESSFUL!")
        print("The standalone folder is located at:")
        print(os.path.abspath(os.path.join("dist", "AIbal")))
        print("\nYou can run the app directly by double-clicking:")
        print(os.path.abspath(os.path.join("dist", "AIbal", "AIbal.exe")))
        print("=======================================================")
    else:
        print("\nBuild failed. Please check the logs above.")

if __name__ == "__main__":
    main()
