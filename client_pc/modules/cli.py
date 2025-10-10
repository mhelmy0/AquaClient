"""
Command-line interface for the RTMP client.

Provides commands to start, stop, check status, take snapshots, and more.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from .config import load_config, update_config, save_config
from .logging_json import JsonLogger
from .stream_receiver import StreamReceiver
from .recorder import Recorder
from .snapshotter import Snapshotter
from .health import HealthMonitor
from .utils import backoff_iterator
from .network_diagnostics import NetworkDiagnostics


class ClientApp:
    """Main client application."""

    def __init__(self, config_path: str) -> None:
        """
        Initialize client application.

        Args:
            config_path: Path to YAML configuration file.
        """
        self.config_path = config_path
        self.config = load_config(config_path)
        self.logger = JsonLogger(self.config)

        # Initialize components
        self.stream_receiver = StreamReceiver(self.config, self.logger)
        self.recorder = Recorder(self.config, self.logger)
        self.snapshotter = Snapshotter(self.config, self.logger)
        self.health = HealthMonitor(self.config, self.stream_receiver, self.recorder, self.logger)

        # Reconnection state
        self.backoff = backoff_iterator(self.config["stream"]["reconnect"]["backoff_seconds"])
        self.running = False

    def cmd_start(self, args) -> int:
        """Start streaming and recording."""
        self.logger.log("service", "cli", "command_start", {}, "Starting client")

        try:
            # Start health monitor
            self.health.start()

            # Start stream receiver
            self.stream_receiver.start()

            # Start recorder if enabled
            if self.config["recording"].get("enabled", True):
                self.recorder.start()

            self.logger.log("service", "cli", "started", {}, "Client started successfully")
            print("Client started. Stream receiving and recording active.")

            # Keep running and monitor
            self.running = True
            self._monitor_loop()

            return 0

        except Exception as e:
            self.logger.log("error", "cli", "start_failed", {
                "error": str(e)
            }, f"Failed to start: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _monitor_loop(self) -> None:
        """Monitor streams and handle reconnection."""
        while self.running:
            try:
                # Check stream health (this will log if it died)
                self.stream_receiver.check_health()

                # Check if stream is still running
                if not self.stream_receiver.is_running():
                    delay = next(self.backoff)
                    self.logger.log("info", "cli", "reconnecting", {
                        "delay_s": delay
                    }, f"Reconnecting in {delay:.1f}s")

                    time.sleep(delay)

                    # Restart stream
                    self.stream_receiver.start()

                    # Restart recorder if needed
                    if self.config["recording"].get("enabled", True) and not self.recorder.is_running():
                        self.recorder.start()

                # Check for periodic snapshots
                if self.snapshotter.should_capture_interval():
                    try:
                        self.snapshotter.capture()
                    except Exception as e:
                        self.logger.log("error", "cli", "snapshot_failed", {
                            "error": str(e)
                        }, f"Snapshot failed: {e}")

                time.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                print("\nShutting down...")
                self.running = False
                break
            except Exception as e:
                self.logger.log("error", "cli", "monitor_error", {
                    "error": str(e)
                }, f"Monitor error: {e}")
                time.sleep(5)

        self.cmd_stop(None)

    def cmd_stop(self, args) -> int:
        """Stop streaming and recording."""
        self.logger.log("service", "cli", "command_stop", {}, "Stopping client")

        self.running = False

        # Stop recorder
        self.recorder.stop()

        # Stop stream receiver
        self.stream_receiver.stop()

        # Stop health monitor
        self.health.stop()

        self.logger.log("service", "cli", "stopped", {}, "Client stopped")
        print("Client stopped.")

        return 0

    def cmd_status(self, args) -> int:
        """Display current status."""
        self.logger.log("info", "cli", "command_status", {
            "json": args.json if args else False
        }, "Status requested")

        status = self.health.get_status()

        if args and args.json:
            # Output JSON format
            print(json.dumps(status, indent=2))
        else:
            # Output human-readable format
            summary = self.health.get_summary()
            print(summary)

        return 0

    def cmd_snapshot(self, args) -> int:
        """Capture a snapshot."""
        self.logger.log("info", "cli", "command_snapshot", {}, "Snapshot requested")

        try:
            snapshot_path = self.snapshotter.capture()
            print(f"Snapshot saved: {snapshot_path}")
            return 0

        except Exception as e:
            self.logger.log("error", "cli", "snapshot_command_failed", {
                "error": str(e)
            }, f"Snapshot command failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def cmd_reconnect(self, args) -> int:
        """Force immediate reconnection."""
        self.logger.log("info", "cli", "command_reconnect", {}, "Reconnect requested")

        try:
            # Stop and restart stream
            self.stream_receiver.stop()
            time.sleep(1)
            self.stream_receiver.start()

            # Restart recorder if needed
            if self.config["recording"].get("enabled", True):
                self.recorder.stop()
                time.sleep(1)
                self.recorder.start()

            print("Reconnected successfully.")
            return 0

        except Exception as e:
            self.logger.log("error", "cli", "reconnect_failed", {
                "error": str(e)
            }, f"Reconnect failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def cmd_set(self, args) -> int:
        """Set a configuration value."""
        self.logger.log("info", "cli", "command_set", {
            "key": args.key,
            "value": args.value
        }, f"Setting {args.key} = {args.value}")

        try:
            # Parse value as JSON to handle types
            try:
                value = json.loads(args.value)
            except json.JSONDecodeError:
                # If not valid JSON, treat as string
                value = args.value

            # Update config
            update_config(self.config, args.key, value)

            # Optionally persist
            if args.persist:
                save_config(self.config, self.config_path)
                print(f"Set {args.key} = {value} (persisted)")
            else:
                print(f"Set {args.key} = {value} (in-memory only)")

            return 0

        except Exception as e:
            self.logger.log("error", "cli", "set_failed", {
                "error": str(e)
            }, f"Set command failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def cmd_diagnose(self, args) -> int:
        """Run network diagnostics on RTMP server."""
        self.logger.log("info", "cli", "command_diagnose", {}, "Running network diagnostics")

        try:
            rtmp_url = self.config["stream"]["url"]
            print(f"Running diagnostics on: {rtmp_url}\n")

            diag = NetworkDiagnostics(self.logger)
            results = diag.run_full_diagnostics(rtmp_url)

            print(results["summary"])

            if args and hasattr(args, 'json') and args.json:
                print("\nDetailed JSON results:")
                print(json.dumps(results, indent=2))

            return 0 if results["overall_success"] else 1

        except Exception as e:
            self.logger.log("error", "cli", "diagnose_failed", {
                "error": str(e)
            }, f"Diagnostics failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RTMP Client for Windows PC",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start command
    subparsers.add_parser("start", help="Start streaming and recording")

    # Stop command
    subparsers.add_parser("stop", help="Stop streaming and recording")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # Snapshot command
    subparsers.add_parser("snapshot", help="Capture a snapshot")

    # Reconnect command
    subparsers.add_parser("reconnect", help="Force reconnection")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Configuration key (dot notation)")
    set_parser.add_argument("value", help="Value to set")
    set_parser.add_argument("--persist", action="store_true", help="Save to config file")

    # Diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Run network diagnostics on RTMP server")
    diagnose_parser.add_argument("--json", action="store_true", help="Output detailed JSON results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create application
    app = ClientApp(args.config)

    # Dispatch command
    command_map = {
        "start": app.cmd_start,
        "stop": app.cmd_stop,
        "status": app.cmd_status,
        "snapshot": app.cmd_snapshot,
        "reconnect": app.cmd_reconnect,
        "set": app.cmd_set,
        "diagnose": app.cmd_diagnose
    }

    cmd_func = command_map.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
