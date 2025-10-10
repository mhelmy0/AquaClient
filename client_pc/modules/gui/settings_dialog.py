"""
Settings dialog for configuring application preferences.

Allows users to modify stream URL, hotkeys, theme, and other settings.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QCheckBox, QTabWidget, QWidget, QGroupBox,
    QSpinBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict, Any


class SettingsDialog(QDialog):
    """
    Settings dialog for application configuration.

    Signals:
        settings_changed: Emitted when settings are saved with new config dict
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, config: Dict[str, Any], parent=None):
        """
        Initialize settings dialog.

        Args:
            config: Current configuration dictionary
            parent: Parent widget
        """
        super().__init__(parent)

        self.config = config.copy()
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Create layout
        layout = QVBoxLayout()

        # Create tab widget
        tabs = QTabWidget()

        # Stream settings tab
        stream_tab = self._create_stream_tab()
        tabs.addTab(stream_tab, "Stream")

        # Recording settings tab
        recording_tab = self._create_recording_tab()
        tabs.addTab(recording_tab, "Recording")

        # Hotkeys settings tab
        hotkeys_tab = self._create_hotkeys_tab()
        tabs.addTab(hotkeys_tab, "Hotkeys")

        # UI settings tab
        ui_tab = self._create_ui_tab()
        tabs.addTab(ui_tab, "UI")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_stream_tab(self) -> QWidget:
        """Create stream settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Stream URL
        group = QGroupBox("Stream Configuration")
        form = QFormLayout()

        self.stream_url_input = QLineEdit()
        self.stream_url_input.setText(self.config["stream"]["url"])
        form.addRow("RTMP URL:", self.stream_url_input)

        self.read_timeout_input = QSpinBox()
        self.read_timeout_input.setRange(1, 60)
        self.read_timeout_input.setValue(self.config["stream"].get("read_timeout_seconds", 10))
        self.read_timeout_input.setSuffix(" seconds")
        form.addRow("Read Timeout:", self.read_timeout_input)

        group.setLayout(form)
        layout.addWidget(group)

        # Test connection button
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self._test_connection)
        layout.addWidget(test_button)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_recording_tab(self) -> QWidget:
        """Create recording settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Recording settings
        group = QGroupBox("Recording Configuration")
        form = QFormLayout()

        self.segment_duration_input = QSpinBox()
        self.segment_duration_input.setRange(300, 21600)  # 5 min to 6 hours
        self.segment_duration_input.setValue(self.config["recording"]["segment_seconds"])
        self.segment_duration_input.setSuffix(" seconds")
        form.addRow("Segment Duration:", self.segment_duration_input)

        self.disk_floor_input = QSpinBox()
        self.disk_floor_input.setRange(100, 10000)
        self.disk_floor_input.setValue(self.config["recording"]["disk_free_floor_mib"])
        self.disk_floor_input.setSuffix(" MiB")
        form.addRow("Disk Space Floor:", self.disk_floor_input)

        self.disk_resume_input = QSpinBox()
        self.disk_resume_input.setRange(100, 10000)
        self.disk_resume_input.setValue(self.config["recording"]["disk_free_resume_mib"])
        self.disk_resume_input.setSuffix(" MiB")
        form.addRow("Disk Space Resume:", self.disk_resume_input)

        group.setLayout(form)
        layout.addWidget(group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_hotkeys_tab(self) -> QWidget:
        """Create hotkeys settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Hotkeys enable
        self.hotkeys_enabled = QCheckBox("Enable Global Hotkeys")
        self.hotkeys_enabled.setChecked(self.config["ui"]["hotkeys"].get("enabled", True))
        layout.addWidget(self.hotkeys_enabled)

        # Hotkey inputs
        group = QGroupBox("Hotkey Configuration")
        form = QFormLayout()

        hotkeys_config = self.config["ui"]["hotkeys"]

        self.snapshot_hotkey = QLineEdit()
        self.snapshot_hotkey.setText(hotkeys_config.get("snapshot", "ctrl+shift+s"))
        form.addRow("Snapshot:", self.snapshot_hotkey)

        self.start_rec_hotkey = QLineEdit()
        self.start_rec_hotkey.setText(hotkeys_config.get("start_recording", "ctrl+shift+r"))
        form.addRow("Start Recording:", self.start_rec_hotkey)

        self.stop_rec_hotkey = QLineEdit()
        self.stop_rec_hotkey.setText(hotkeys_config.get("stop_recording", "ctrl+shift+x"))
        form.addRow("Stop Recording:", self.stop_rec_hotkey)

        self.pause_rec_hotkey = QLineEdit()
        self.pause_rec_hotkey.setText(hotkeys_config.get("pause_recording", "ctrl+shift+p"))
        form.addRow("Pause Recording:", self.pause_rec_hotkey)

        self.show_hide_hotkey = QLineEdit()
        self.show_hide_hotkey.setText(hotkeys_config.get("show_hide_window", "ctrl+shift+m"))
        form.addRow("Show/Hide Window:", self.show_hide_hotkey)

        group.setLayout(form)
        layout.addWidget(group)

        # Help text
        help_text = QLabel("Format: ctrl+shift+key or alt+key\nExample: ctrl+shift+s")
        help_text.setStyleSheet("color: #888; font-size: 8pt;")
        layout.addWidget(help_text)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_ui_tab(self) -> QWidget:
        """Create UI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Theme settings
        group = QGroupBox("Appearance")
        form = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        current_theme = self.config["ui"]["window"].get("theme", "dark")
        self.theme_combo.setCurrentText(current_theme)
        form.addRow("Theme:", self.theme_combo)

        group.setLayout(form)
        layout.addWidget(group)

        # Window settings
        window_group = QGroupBox("Window")
        window_layout = QVBoxLayout()

        self.always_on_top = QCheckBox("Always on Top")
        self.always_on_top.setChecked(self.config["ui"]["window"].get("always_on_top", False))
        window_layout.addWidget(self.always_on_top)

        self.remember_position = QCheckBox("Remember Window Position")
        self.remember_position.setChecked(self.config["ui"]["window"].get("remember_position", True))
        window_layout.addWidget(self.remember_position)

        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        # System tray settings
        tray_group = QGroupBox("System Tray")
        tray_layout = QVBoxLayout()

        self.tray_enabled = QCheckBox("Enable System Tray Icon")
        self.tray_enabled.setChecked(self.config["ui"]["system_tray"].get("enabled", True))
        tray_layout.addWidget(self.tray_enabled)

        self.minimize_to_tray = QCheckBox("Minimize to Tray")
        self.minimize_to_tray.setChecked(self.config["ui"]["system_tray"].get("minimize_to_tray", True))
        tray_layout.addWidget(self.minimize_to_tray)

        self.close_to_tray = QCheckBox("Close to Tray")
        self.close_to_tray.setChecked(self.config["ui"]["system_tray"].get("close_to_tray", True))
        tray_layout.addWidget(self.close_to_tray)

        tray_group.setLayout(tray_layout)
        layout.addWidget(tray_group)

        # Notifications
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout()

        self.notif_enabled = QCheckBox("Enable Notifications")
        self.notif_enabled.setChecked(self.config["ui"]["notifications"].get("enabled", True))
        notif_layout.addWidget(self.notif_enabled)

        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _test_connection(self) -> None:
        """Test RTMP stream connection."""
        url = self.stream_url_input.text()
        # TODO: Implement actual connection test
        QMessageBox.information(
            self,
            "Connection Test",
            f"Testing connection to:\n{url}\n\nThis feature will be implemented in the stream handler."
        )

    def _save_settings(self) -> None:
        """Save settings and emit changes."""
        # Update config dictionary
        self.config["stream"]["url"] = self.stream_url_input.text()
        self.config["stream"]["read_timeout_seconds"] = self.read_timeout_input.value()

        self.config["recording"]["segment_seconds"] = self.segment_duration_input.value()
        self.config["recording"]["disk_free_floor_mib"] = self.disk_floor_input.value()
        self.config["recording"]["disk_free_resume_mib"] = self.disk_resume_input.value()

        self.config["ui"]["hotkeys"]["enabled"] = self.hotkeys_enabled.isChecked()
        self.config["ui"]["hotkeys"]["snapshot"] = self.snapshot_hotkey.text()
        self.config["ui"]["hotkeys"]["start_recording"] = self.start_rec_hotkey.text()
        self.config["ui"]["hotkeys"]["stop_recording"] = self.stop_rec_hotkey.text()
        self.config["ui"]["hotkeys"]["pause_recording"] = self.pause_rec_hotkey.text()
        self.config["ui"]["hotkeys"]["show_hide_window"] = self.show_hide_hotkey.text()

        self.config["ui"]["window"]["theme"] = self.theme_combo.currentText()
        self.config["ui"]["window"]["always_on_top"] = self.always_on_top.isChecked()
        self.config["ui"]["window"]["remember_position"] = self.remember_position.isChecked()

        self.config["ui"]["system_tray"]["enabled"] = self.tray_enabled.isChecked()
        self.config["ui"]["system_tray"]["minimize_to_tray"] = self.minimize_to_tray.isChecked()
        self.config["ui"]["system_tray"]["close_to_tray"] = self.close_to_tray.isChecked()

        self.config["ui"]["notifications"]["enabled"] = self.notif_enabled.isChecked()

        # Emit signal with updated config
        self.settings_changed.emit(self.config)

        # Close dialog
        self.accept()
