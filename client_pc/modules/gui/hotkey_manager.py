"""
Global hotkey manager for Aqua Stream Monitor.

Handles system-wide keyboard shortcuts using pynput library.
"""

import logging
from typing import Dict, Callable, Optional
from pynput import keyboard


class HotkeyManager:
    """
    Manages global keyboard shortcuts for the application.

    Provides registration and handling of system-wide hotkeys that work
    even when the application window is not in focus.
    """

    def __init__(self, config: Dict) -> None:
        """
        Initialize hotkey manager.

        Args:
            config: GUI configuration dictionary with hotkey settings
        """
        self.config = config
        self.enabled = config.get("hotkeys", {}).get("enabled", False)
        self.hotkey_config = config.get("hotkeys", {})
        self.callbacks: Dict[str, Callable] = {}
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self.logger = logging.getLogger(__name__)

    def register_callback(self, action: str, callback: Callable) -> None:
        """
        Register a callback for a hotkey action.

        Args:
            action: Action name (e.g., "snapshot", "start_recording")
            callback: Function to call when hotkey is pressed
        """
        self.callbacks[action] = callback
        self.logger.info(f"Registered callback for action: {action}")

    def _parse_hotkey(self, hotkey_str: str) -> str:
        """
        Parse hotkey string to pynput format.

        Args:
            hotkey_str: Hotkey string like "ctrl+shift+s"

        Returns:
            Parsed hotkey string for pynput
        """
        # Convert to pynput format
        parts = hotkey_str.lower().split('+')
        parsed_parts = []

        for part in parts:
            part = part.strip()
            if part == "ctrl":
                parsed_parts.append("<ctrl>")
            elif part == "shift":
                parsed_parts.append("<shift>")
            elif part == "alt":
                parsed_parts.append("<alt>")
            elif part == "cmd" or part == "win":
                parsed_parts.append("<cmd>")
            else:
                # Regular key
                parsed_parts.append(part)

        return '+'.join(parsed_parts)

    def start(self) -> None:
        """Start listening for global hotkeys."""
        if not self.enabled:
            self.logger.info("Hotkeys disabled in configuration")
            return

        if self.listener is not None:
            self.logger.warning("Hotkey listener already running")
            return

        # Build hotkey mappings
        hotkey_mappings = {}

        # Snapshot
        if "snapshot" in self.hotkey_config and "snapshot" in self.callbacks:
            hotkey_str = self._parse_hotkey(self.hotkey_config["snapshot"])
            hotkey_mappings[hotkey_str] = self.callbacks["snapshot"]

        # Start recording
        if "start_recording" in self.hotkey_config and "start_recording" in self.callbacks:
            hotkey_str = self._parse_hotkey(self.hotkey_config["start_recording"])
            hotkey_mappings[hotkey_str] = self.callbacks["start_recording"]

        # Stop recording
        if "stop_recording" in self.hotkey_config and "stop_recording" in self.callbacks:
            hotkey_str = self._parse_hotkey(self.hotkey_config["stop_recording"])
            hotkey_mappings[hotkey_str] = self.callbacks["stop_recording"]

        # Pause recording
        if "pause_recording" in self.hotkey_config and "pause_recording" in self.callbacks:
            hotkey_str = self._parse_hotkey(self.hotkey_config["pause_recording"])
            hotkey_mappings[hotkey_str] = self.callbacks["pause_recording"]

        # Show/hide window
        if "show_hide_window" in self.hotkey_config and "show_hide_window" in self.callbacks:
            hotkey_str = self._parse_hotkey(self.hotkey_config["show_hide_window"])
            hotkey_mappings[hotkey_str] = self.callbacks["show_hide_window"]

        if not hotkey_mappings:
            self.logger.warning("No valid hotkey mappings configured")
            return

        try:
            self.listener = keyboard.GlobalHotKeys(hotkey_mappings)
            self.listener.start()
            self.logger.info(f"Started hotkey listener with {len(hotkey_mappings)} hotkeys")
        except Exception as e:
            self.logger.error(f"Failed to start hotkey listener: {e}")

    def stop(self) -> None:
        """Stop listening for global hotkeys."""
        if self.listener is not None:
            try:
                self.listener.stop()
                self.listener = None
                self.logger.info("Stopped hotkey listener")
            except Exception as e:
                self.logger.error(f"Error stopping hotkey listener: {e}")

    def is_running(self) -> bool:
        """
        Check if hotkey listener is active.

        Returns:
            True if listener is running, False otherwise
        """
        return self.listener is not None and self.listener.is_alive()
