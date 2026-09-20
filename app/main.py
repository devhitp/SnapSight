"""
Main Entry Point for SnapSight.
"""
import sys
import logging
from PySide6.QtWidgets import QApplication
from app.config import APP_NAME
from app.utils.logging import configure_logging
from app.ui.main_window import MainWindow

def main():
    # 1. Configure logging
    logger = configure_logging()
    logger.info(f"{APP_NAME} starting")

    # 2. Create QApplication
    app = QApplication(sys.argv)

    # 3. Load configuration (already loaded in config.py)

    # 4. Create main window
    logger.info("UI initialized")
    window = MainWindow()

    # 5. Show main window
    window.show()
    logger.info("Application ready")

    # 6. Start Qt event loop
    exit_code = app.exec()
    
    # 7. Exit cleanly
    logger.info("Application shutting down")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
