import sys
import os
from unittest import mock
import pytest
from app.utils.paths import get_app_root, get_models_dir, get_bundled_res_dir, is_frozen

def test_paths_source_mode():
    """Test path resolution in standard non-frozen source execution."""
    # Ensure sys._MEIPASS is not set
    with mock.patch('sys.frozen', False, create=True):
        assert not is_frozen()
        
        app_root = get_app_root()
        models_dir = get_models_dir()
        bundled_dir = get_bundled_res_dir()
        
        assert os.path.basename(app_root) == "SnapSight"
        assert os.path.basename(models_dir) == "models"
        assert os.path.dirname(models_dir) == app_root
        assert bundled_dir == app_root

def test_paths_frozen_mode():
    """Test path resolution when running as a PyInstaller frozen binary."""
    fake_meipass = os.path.join("C:\\", "Temp", "_MEI12345")
    fake_exe = os.path.join("C:\\", "Program Files", "SnapSight", "SnapSight.exe")
    
    with mock.patch('sys.frozen', True, create=True), \
         mock.patch('sys._MEIPASS', fake_meipass, create=True), \
         mock.patch('sys.executable', fake_exe):
        
        assert is_frozen()
        
        app_root = get_app_root()
        models_dir = get_models_dir()
        bundled_dir = get_bundled_res_dir()
        
        # When frozen, app_root should be the directory of the .exe
        expected_root = os.path.dirname(fake_exe)
        assert app_root == expected_root
        
        # Models dir should be directly next to the .exe
        assert models_dir == os.path.join(expected_root, "models")
        
        # Bundled dir should be the temporary PyInstaller extraction folder
        assert bundled_dir == fake_meipass
