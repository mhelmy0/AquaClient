"""
Theme management for Aqua Stream Monitor GUI.

Provides dark and light theme stylesheets for PyQt5 application.
"""

# Dark theme stylesheet
DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 9pt;
}

QPushButton {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3d3d3d;
    border: 1px solid #4d4d4d;
}

QPushButton:pressed {
    background-color: #1d1d1d;
}

QPushButton:disabled {
    background-color: #252525;
    color: #666666;
}

QPushButton#recordButton {
    background-color: #c41e3a;
    border: 1px solid #d41e3a;
}

QPushButton#recordButton:hover {
    background-color: #d41e3a;
}

QPushButton#stopButton {
    background-color: #8b0000;
    border: 1px solid #9b0000;
}

QPushButton#snapshotButton {
    background-color: #0066cc;
    border: 1px solid #0076dd;
}

QPushButton#snapshotButton:hover {
    background-color: #0076dd;
}

QLabel {
    background-color: transparent;
    color: #e0e0e0;
}

QLabel#statusLabel {
    font-weight: bold;
    font-size: 10pt;
}

QLabel#videoLabel {
    background-color: #000000;
    border: 2px solid #3d3d3d;
}

QTextEdit {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 4px;
}

QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #4d4d4d;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5d5d5d;
}

QProgressBar {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #0066cc;
    border-radius: 3px;
}

QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #e0e0e0;
}

QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-top: 1px solid #3d3d3d;
}

QMenuBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-bottom: 1px solid #3d3d3d;
}

QMenuBar::item:selected {
    background-color: #3d3d3d;
}

QMenu {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
}

QMenu::item:selected {
    background-color: #3d3d3d;
}

QLineEdit {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 4px;
}

QLineEdit:focus {
    border: 1px solid #0066cc;
}

QCheckBox {
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    background-color: #252525;
}

QCheckBox::indicator:checked {
    background-color: #0066cc;
}

QComboBox {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 4px;
}

QComboBox:hover {
    border: 1px solid #4d4d4d;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    selection-background-color: #3d3d3d;
}
"""

# Light theme stylesheet
LIGHT_THEME = """
QMainWindow {
    background-color: #f5f5f5;
    color: #2c2c2c;
}

QWidget {
    background-color: #f5f5f5;
    color: #2c2c2c;
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 9pt;
}

QPushButton {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #e8e8e8;
    border: 1px solid #b0b0b0;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f0f0f0;
    color: #a0a0a0;
}

QPushButton#recordButton {
    background-color: #e74c3c;
    color: #ffffff;
    border: 1px solid #c0392b;
}

QPushButton#recordButton:hover {
    background-color: #c0392b;
}

QPushButton#stopButton {
    background-color: #c0392b;
    color: #ffffff;
    border: 1px solid #a02820;
}

QPushButton#snapshotButton {
    background-color: #3498db;
    color: #ffffff;
    border: 1px solid #2980b9;
}

QPushButton#snapshotButton:hover {
    background-color: #2980b9;
}

QLabel {
    background-color: transparent;
    color: #2c2c2c;
}

QLabel#statusLabel {
    font-weight: bold;
    font-size: 10pt;
}

QLabel#videoLabel {
    background-color: #000000;
    border: 2px solid #d0d0d0;
}

QTextEdit {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px;
}

QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QProgressBar {
    background-color: #e0e0e0;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    text-align: center;
    color: #2c2c2c;
}

QProgressBar::chunk {
    background-color: #3498db;
    border-radius: 3px;
}

QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #2c2c2c;
}

QStatusBar {
    background-color: #ffffff;
    color: #2c2c2c;
    border-top: 1px solid #d0d0d0;
}

QMenuBar {
    background-color: #ffffff;
    color: #2c2c2c;
    border-bottom: 1px solid #d0d0d0;
}

QMenuBar::item:selected {
    background-color: #e8e8e8;
}

QMenu {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
}

QMenu::item:selected {
    background-color: #e8e8e8;
}

QLineEdit {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px;
}

QLineEdit:focus {
    border: 1px solid #3498db;
}

QCheckBox {
    color: #2c2c2c;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d0d0d0;
    border-radius: 3px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
}

QComboBox {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px;
}

QComboBox:hover {
    border: 1px solid #b0b0b0;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
    selection-background-color: #e8e8e8;
}
"""


def get_theme(theme_name: str) -> str:
    """
    Get stylesheet for specified theme.

    Args:
        theme_name: "dark" or "light"

    Returns:
        Theme stylesheet string
    """
    if theme_name.lower() == "light":
        return LIGHT_THEME
    return DARK_THEME
