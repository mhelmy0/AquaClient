"""
Quality and recording settings dialog.

Allows users to configure video quality, bitrate, and recording parameters.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QSpinBox, QSlider, QPushButton,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, Any


class QualitySettingsDialog(QDialog):
    """
    Dialog for configuring recording quality and bitrate settings.

    Signals:
        settings_changed: Emitted when settings are applied
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings: Dict[str, Any], parent=None):
        """
        Initialize quality settings dialog.

        Args:
            current_settings: Current quality settings
            parent: Parent widget
        """
        super().__init__(parent)

        self.current_settings = current_settings.copy()

        self.setWindowTitle("Recording Quality Settings")
        self.setMinimumWidth(500)
        self.setModal(True)

        # Create UI
        self._create_ui()
        self._load_current_settings()

    def _create_ui(self) -> None:
        """Create dialog UI components."""
        main_layout = QVBoxLayout()

        # Quality preset group
        preset_group = QGroupBox("Quality Preset")
        preset_layout = QVBoxLayout()

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Low (1 Mbps) - Save disk space", "low")
        self.preset_combo.addItem("Medium (2.5 Mbps) - Balanced", "medium")
        self.preset_combo.addItem("High (5 Mbps) - Recommended", "high")
        self.preset_combo.addItem("Ultra (8 Mbps) - Best quality", "ultra")
        self.preset_combo.addItem("Lossless (Copy) - No re-encoding", "lossless")
        self.preset_combo.addItem("Custom - Manual bitrate", "custom")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        preset_layout.addWidget(QLabel("Select quality preset:"))
        preset_layout.addWidget(self.preset_combo)

        preset_group.setLayout(preset_layout)
        main_layout.addWidget(preset_group)

        # Custom bitrate group
        self.custom_group = QGroupBox("Custom Bitrate Settings")
        custom_layout = QVBoxLayout()

        # Video bitrate slider
        bitrate_label_layout = QHBoxLayout()
        bitrate_label_layout.addWidget(QLabel("Video Bitrate:"))
        self.bitrate_value_label = QLabel("5000 kbps")
        bitrate_label_layout.addWidget(self.bitrate_value_label)
        bitrate_label_layout.addStretch()
        custom_layout.addLayout(bitrate_label_layout)

        self.bitrate_slider = QSlider(Qt.Horizontal)
        self.bitrate_slider.setMinimum(500)   # 500 kbps
        self.bitrate_slider.setMaximum(15000)  # 15 Mbps
        self.bitrate_slider.setValue(5000)
        self.bitrate_slider.setTickPosition(QSlider.TicksBelow)
        self.bitrate_slider.setTickInterval(1000)
        self.bitrate_slider.valueChanged.connect(self._on_bitrate_changed)
        custom_layout.addWidget(self.bitrate_slider)

        # Preset markers
        marker_layout = QHBoxLayout()
        marker_layout.addWidget(QLabel("500k"))
        marker_layout.addStretch()
        marker_layout.addWidget(QLabel("5M"))
        marker_layout.addStretch()
        marker_layout.addWidget(QLabel("15M"))
        custom_layout.addLayout(marker_layout)

        self.custom_group.setLayout(custom_layout)
        self.custom_group.setEnabled(False)
        main_layout.addWidget(self.custom_group)

        # Video codec group
        codec_group = QGroupBox("Video Codec")
        codec_layout = QVBoxLayout()

        self.codec_button_group = QButtonGroup()

        self.h264_radio = QRadioButton("H.264 (libx264) - Universal compatibility")
        self.h264_radio.setChecked(True)
        self.codec_button_group.addButton(self.h264_radio, 0)
        codec_layout.addWidget(self.h264_radio)

        self.h265_radio = QRadioButton("H.265 (libx265) - Better compression")
        self.codec_button_group.addButton(self.h265_radio, 1)
        codec_layout.addWidget(self.h265_radio)

        self.copy_radio = QRadioButton("Copy - No re-encoding (fastest)")
        self.codec_button_group.addButton(self.copy_radio, 2)
        codec_layout.addWidget(self.copy_radio)

        codec_group.setLayout(codec_layout)
        main_layout.addWidget(codec_group)

        # Encoding settings group
        encoding_group = QGroupBox("Encoding Settings")
        encoding_layout = QVBoxLayout()

        # Preset (speed vs quality)
        preset_enc_layout = QHBoxLayout()
        preset_enc_layout.addWidget(QLabel("Encoding Speed:"))
        self.encoding_preset_combo = QComboBox()
        self.encoding_preset_combo.addItem("Ultrafast - Fastest, lower quality", "ultrafast")
        self.encoding_preset_combo.addItem("Superfast", "superfast")
        self.encoding_preset_combo.addItem("Veryfast", "veryfast")
        self.encoding_preset_combo.addItem("Faster", "faster")
        self.encoding_preset_combo.addItem("Fast", "fast")
        self.encoding_preset_combo.addItem("Medium - Balanced (Recommended)", "medium")
        self.encoding_preset_combo.addItem("Slow - Better quality", "slow")
        self.encoding_preset_combo.addItem("Slower", "slower")
        self.encoding_preset_combo.addItem("Veryslow - Best quality", "veryslow")
        self.encoding_preset_combo.setCurrentIndex(5)  # Medium
        preset_enc_layout.addWidget(self.encoding_preset_combo)
        encoding_layout.addLayout(preset_enc_layout)

        # CRF (Constant Rate Factor) for quality-based encoding
        crf_layout = QHBoxLayout()
        crf_layout.addWidget(QLabel("Quality (CRF):"))
        self.crf_spinbox = QSpinBox()
        self.crf_spinbox.setMinimum(0)
        self.crf_spinbox.setMaximum(51)
        self.crf_spinbox.setValue(23)
        self.crf_spinbox.setToolTip("Lower = better quality, larger files (0-51, default: 23)")
        crf_layout.addWidget(self.crf_spinbox)
        crf_layout.addStretch()
        encoding_layout.addLayout(crf_layout)

        encoding_group.setLayout(encoding_layout)
        main_layout.addWidget(encoding_group)

        # File format group
        format_group = QGroupBox("Output Format")
        format_layout = QHBoxLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItem("MP4 - Universal (Recommended)", "mp4")
        self.format_combo.addItem("MKV - Matroska (Advanced)", "mkv")
        self.format_combo.addItem("AVI - Legacy", "avi")

        format_layout.addWidget(QLabel("Container:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()

        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)

        # Estimated file size info
        self.estimate_label = QLabel("Estimated file size: ~9 GB/hour")
        self.estimate_label.setStyleSheet("color: #888; font-style: italic;")
        main_layout.addWidget(self.estimate_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        apply_button = QPushButton("Apply")
        apply_button.setDefault(True)
        apply_button.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _on_preset_changed(self, index: int) -> None:
        """Handle preset selection change."""
        preset = self.preset_combo.currentData()

        if preset == "custom":
            self.custom_group.setEnabled(True)
        else:
            self.custom_group.setEnabled(False)

            # Update slider to match preset
            preset_bitrates = {
                'low': 1000,
                'medium': 2500,
                'high': 5000,
                'ultra': 8000,
                'lossless': 5000  # Placeholder
            }
            if preset in preset_bitrates:
                self.bitrate_slider.setValue(preset_bitrates[preset])

            # For lossless, select copy codec
            if preset == "lossless":
                self.copy_radio.setChecked(True)
            else:
                self.h264_radio.setChecked(True)

        self._update_file_size_estimate()

    def _on_bitrate_changed(self, value: int) -> None:
        """Handle bitrate slider change."""
        self.bitrate_value_label.setText(f"{value} kbps ({value / 1000:.1f} Mbps)")
        self._update_file_size_estimate()

    def _update_file_size_estimate(self) -> None:
        """Update estimated file size label."""
        preset = self.preset_combo.currentData()

        if preset == "lossless" or self.copy_radio.isChecked():
            self.estimate_label.setText("Estimated file size: Variable (no re-encoding)")
        else:
            # Get current bitrate
            if preset == "custom":
                bitrate_kbps = self.bitrate_slider.value()
            else:
                preset_bitrates = {
                    'low': 1000,
                    'medium': 2500,
                    'high': 5000,
                    'ultra': 8000
                }
                bitrate_kbps = preset_bitrates.get(preset, 5000)

            # Calculate approximate file size per hour
            # (bitrate in kbps * 3600 seconds) / (8 bits/byte * 1024 MB/GB)
            gb_per_hour = (bitrate_kbps * 3600) / (8 * 1024)

            self.estimate_label.setText(f"Estimated file size: ~{gb_per_hour:.1f} GB/hour")

    def _load_current_settings(self) -> None:
        """Load current settings into dialog."""
        # Load preset
        preset = self.current_settings.get('quality_preset', 'high')
        index = self.preset_combo.findData(preset)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

        # Load custom bitrate
        custom_bitrate = self.current_settings.get('custom_bitrate', 5000)
        self.bitrate_slider.setValue(custom_bitrate)

        # Load codec
        codec = self.current_settings.get('codec', 'h264')
        if codec == 'h265':
            self.h265_radio.setChecked(True)
        elif codec == 'copy':
            self.copy_radio.setChecked(True)
        else:
            self.h264_radio.setChecked(True)

        # Load encoding preset
        encoding_preset = self.current_settings.get('encoding_preset', 'medium')
        index = self.encoding_preset_combo.findData(encoding_preset)
        if index >= 0:
            self.encoding_preset_combo.setCurrentIndex(index)

        # Load CRF
        crf = self.current_settings.get('crf', 23)
        self.crf_spinbox.setValue(crf)

        # Load format
        output_format = self.current_settings.get('output_format', 'mp4')
        index = self.format_combo.findData(output_format)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)

    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.preset_combo.setCurrentIndex(2)  # High
        self.bitrate_slider.setValue(5000)
        self.h264_radio.setChecked(True)
        self.encoding_preset_combo.setCurrentIndex(5)  # Medium
        self.crf_spinbox.setValue(23)
        self.format_combo.setCurrentIndex(0)  # MP4

    def _apply_settings(self) -> None:
        """Apply settings and close dialog."""
        settings = {
            'quality_preset': self.preset_combo.currentData(),
            'custom_bitrate': self.bitrate_slider.value(),
            'codec': self._get_selected_codec(),
            'encoding_preset': self.encoding_preset_combo.currentData(),
            'crf': self.crf_spinbox.value(),
            'output_format': self.format_combo.currentData()
        }

        self.settings_changed.emit(settings)
        self.accept()

    def _get_selected_codec(self) -> str:
        """Get selected codec."""
        if self.h265_radio.isChecked():
            return 'h265'
        elif self.copy_radio.isChecked():
            return 'copy'
        else:
            return 'h264'

    def get_settings(self) -> Dict[str, Any]:
        """
        Get current settings.

        Returns:
            Dictionary with all settings
        """
        return {
            'quality_preset': self.preset_combo.currentData(),
            'custom_bitrate': self.bitrate_slider.value(),
            'codec': self._get_selected_codec(),
            'encoding_preset': self.encoding_preset_combo.currentData(),
            'crf': self.crf_spinbox.value(),
            'output_format': self.format_combo.currentData()
        }
