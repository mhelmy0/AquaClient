"""
Configuration loader for Windows client.

Loads YAML configuration and validates against schema.
"""

import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Basic validation
    required_keys = ["stream", "recording", "snapshots", "logging", "health"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")

    # Validate stream config
    if "url" not in config["stream"]:
        raise ValueError("stream.url is required")

    # Validate recording config
    if "output_dir" not in config["recording"]:
        raise ValueError("recording.output_dir is required")

    return config


def update_config(config: Dict[str, Any], key: str, value: Any) -> None:
    """
    Update a configuration value using dot notation.

    Args:
        config: Configuration dictionary to update.
        key: Dot-separated key path (e.g., "stream.url").
        value: New value to set.
    """
    keys = key.split(".")
    current = config

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: Configuration dictionary.
        config_path: Path to save the YAML file.
    """
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
