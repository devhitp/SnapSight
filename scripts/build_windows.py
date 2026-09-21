import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("Starting SnapSight Windows Build...")
    
    # Ensure we are in the root directory
    root_dir = Path(__file__).resolve().parent.parent
    os.chdir(root_dir)
    print(f"Working directory: {root_dir}")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"Found PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Error: PyInstaller is not installed in this environment.")
        print("Please install it with: pip install pyinstaller")
        sys.exit(1)
        
    # Define build parameters
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    app_name = "SnapSight"
    entry_point = "app/main.py"
    
    # Clean previous builds
    print("Cleaning previous build artifacts...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
        
    # PyInstaller arguments
    # --onedir creates a folder containing the executable and libraries
    # --noconfirm overwrites output directory without asking
    # --clean cleans PyInstaller cache
    # --windowed hides the console window for a GUI app
    args = [
        entry_point,
        f"--name={app_name}",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--hidden-import=pyside6",
        "--hidden-import=llama_cpp",
        "--hidden-import=easyocr",
        "--hidden-import=app.ui.main_window",
    ]
    
    print(f"Running PyInstaller with args: {' '.join(args)}")
    
    try:
        import PyInstaller.__main__
        PyInstaller.__main__.run(args)
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)
        
    print("\nVerifying build...")
    exe_path = dist_dir / app_name / f"{app_name}.exe"
    if not exe_path.exists():
        print(f"Error: Expected executable not found at {exe_path}")
        sys.exit(1)
        
    print(f"Success! Executable generated at: {exe_path}")
    print("\nNOTE: Large AI models are NOT bundled. To use the packaged application:")
    print(f"Place a 'models' directory next to {exe_path.name} before running.")

if __name__ == "__main__":
    main()
