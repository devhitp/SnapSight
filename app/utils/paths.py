"""
Path resolution for SnapSight.

Handles both standard Python execution (source mode) and PyInstaller packaged execution (frozen mode).
Ensures that models and external resources are always located relative to the application,
regardless of how it was launched.
"""
import sys
import os

def is_frozen() -> bool:
    """Returns True if the application is running as a PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_app_root() -> str:
    """
    Returns the root directory of the application.
    In frozen mode, this is the directory containing the executable.
    In source mode, this is the project root (where scripts/ and app/ live).
    """
    if is_frozen():
        # sys.executable is the path to the .exe when frozen
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # We are in app/utils/paths.py
        # root is 2 levels up
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_models_dir() -> str:
    """
    Returns the path to the external models directory.
    This directory must ALWAYS remain external, even when packaged.
    """
    return os.path.join(get_app_root(), "models")

def get_bundled_res_dir() -> str:
    """
    Returns the path to bundled internal resources (e.g. assets, if any).
    In frozen mode, this is inside sys._MEIPASS (the extracted temp directory).
    In source mode, this is just the project root.
    """
    if is_frozen():
        return sys._MEIPASS
    else:
        return get_app_root()
