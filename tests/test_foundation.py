"""
Tests for SnapSight Sprint 1 Foundation.
"""
import pytest
from PySide6.QtWidgets import QApplication
from app.config import APP_NAME, APP_VERSION
from app.ui.main_window import MainWindow

# Provide a QApplication instance for the tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_configuration_loads_successfully():
    """Test 1: Configuration loads successfully and application metadata is correct (Test 2)."""
    assert APP_NAME == "SnapSight"
    assert APP_VERSION == "0.1.0"
    
def test_main_window_instantiation(qapp):
    """Test 3: Main window can be instantiated."""
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "SnapSight"

def test_ui_controls_exist(qapp):
    """Test 4: Required UI controls exist."""
    window = MainWindow()
    assert window.btn_capture_window is not None
    assert window.btn_select_region is not None
    assert window.btn_ask_ai is not None

def test_ask_ai_starts_enabled(qapp):
    """Test 5: Ask AI starts enabled for general queries."""
    window = MainWindow()
    assert window.btn_ask_ai.isEnabled() is True

def test_capture_buttons_exist(qapp):
    """Test 6: Capture buttons exist (and are enabled)."""
    window = MainWindow()
    assert window.btn_capture_window.isEnabled() is True
    assert window.btn_select_region.isEnabled() is True

def test_no_secrets_in_config():
    """Test 7: Application configuration does not require secrets."""
    import app.config as config
    config_vars = dir(config)
    for var in config_vars:
        if not var.startswith("__"):
            assert "key" not in var.lower(), f"Secret found in config: {var}"
            assert "secret" not in var.lower(), f"Secret found in config: {var}"
            assert "token" not in var.lower(), f"Secret found in config: {var}"
            assert "password" not in var.lower(), f"Secret found in config: {var}"
