#!/usr/bin/env python3
"""
Command-line entry point for RTMP client.

This script adds the modules directory to the path and runs the CLI.
"""

import sys
from pathlib import Path

# Add modules directory to Python path
modules_path = Path(__file__).parent / "modules"
sys.path.insert(0, str(modules_path))

# Now import and run the CLI
from cli import main

if __name__ == "__main__":
    sys.exit(main())
