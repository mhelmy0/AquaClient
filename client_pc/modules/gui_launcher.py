"""
GUI launcher for Aqua Stream Monitor.

Entry point for launching the PyQt5 GUI application.
"""

import sys
import yaml
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from .gui.main_window import MainWindow
from .gui.app_controller import AppController
from .config import load_config
from .logging_json import JsonLogger


def main():
    """Launch the GUI application."""
    # Load configuration
    try:
        # Default config path is config.yaml in the client_pc directory
        config_path = Path(__file__).parent.parent / "config.yaml"
        config = load_config(str(config_path))
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Check if GUI is enabled
    if not config.get("ui", {}).get("enabled", False):
        print("GUI is disabled in configuration. Set ui.enabled to true in config.yaml")
        sys.exit(1)

    # Initialize logger
    logger = JsonLogger(config)

    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Aqua Stream Monitor")
    app.setOrganizationName("Aqua")

    # Create main window
    window = MainWindow(config)

    # Create controller to bridge GUI and backend
    controller = AppController(window, config, logger)

    # Show window (unless start minimized is enabled)
    if config.get("ui", {}).get("window", {}).get("start_minimized", False):
        window.hide()
    else:
        window.show()

    # Cleanup on exit
    def cleanup():
        controller.cleanup()
        logger.close()

    app.aboutToQuit.connect(cleanup)

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
