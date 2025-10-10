"""
Network diagnostics and troubleshooting utilities.

Provides tools to test RTMP server connectivity, measure latency, and diagnose network issues.
"""

import subprocess
import socket
import time
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse


class NetworkDiagnostics:
    """
    Network diagnostics for troubleshooting RTMP connectivity.

    Provides ping tests, port checks, and RTMP server availability tests.
    """

    def __init__(self, logger=None):
        """
        Initialize network diagnostics.

        Args:
            logger: Optional JSON logger instance.
        """
        self.logger = logger

    def _log(self, level: str, event: str, context: dict, message: str) -> None:
        """Helper to log if logger is available."""
        if self.logger:
            self.logger.log(level, "network_diagnostics", event, context, message)
        else:
            print(f"[{level}] {message}")

    def parse_rtmp_url(self, rtmp_url: str) -> Dict[str, Any]:
        """
        Parse RTMP URL to extract host and port.

        Args:
            rtmp_url: RTMP URL (e.g., rtmp://192.168.100.23/live/cam)

        Returns:
            Dictionary with host, port, and path.
        """
        parsed = urlparse(rtmp_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 1935,  # Default RTMP port
            "path": parsed.path,
            "scheme": parsed.scheme
        }

    def ping_test(self, host: str, count: int = 4, timeout: int = 5) -> Dict[str, Any]:
        """
        Perform ping test to check if host is reachable.

        Args:
            host: Hostname or IP address
            count: Number of ping packets to send
            timeout: Timeout in seconds

        Returns:
            Dictionary with ping results.
        """
        self._log("info", "ping_test_start", {"host": host, "count": count}, f"Starting ping test to {host}")

        try:
            # Windows ping command
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * count + 5)

            output = result.stdout

            # Parse ping results
            packet_loss = 100
            avg_latency = None

            # Extract packet loss (example: "Lost = 0 (0% loss)")
            loss_match = re.search(r'Lost = \d+ \((\d+)% loss\)', output)
            if loss_match:
                packet_loss = int(loss_match.group(1))

            # Extract average latency (example: "Average = 10ms")
            avg_match = re.search(r'Average = (\d+)ms', output)
            if avg_match:
                avg_latency = int(avg_match.group(1))

            success = result.returncode == 0 and packet_loss < 100

            result_data = {
                "success": success,
                "host": host,
                "packet_loss_percent": packet_loss,
                "avg_latency_ms": avg_latency,
                "raw_output": output
            }

            self._log(
                "service" if success else "error",
                "ping_test_complete",
                result_data,
                f"Ping test to {host}: {'Success' if success else 'Failed'} - {packet_loss}% loss, {avg_latency}ms avg"
            )

            return result_data

        except subprocess.TimeoutExpired:
            result_data = {
                "success": False,
                "host": host,
                "error": "Timeout",
                "packet_loss_percent": 100
            }
            self._log("error", "ping_test_timeout", result_data, f"Ping test to {host} timed out")
            return result_data

        except Exception as e:
            result_data = {
                "success": False,
                "host": host,
                "error": str(e)
            }
            self._log("error", "ping_test_failed", result_data, f"Ping test to {host} failed: {e}")
            return result_data

    def test_tcp_port(self, host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
        """
        Test if TCP port is open and accepting connections.

        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Connection timeout in seconds

        Returns:
            Dictionary with port test results.
        """
        self._log("info", "port_test_start", {"host": host, "port": port}, f"Testing TCP port {host}:{port}")

        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            result_code = sock.connect_ex((host, port))
            connect_time = (time.time() - start_time) * 1000  # Convert to ms

            sock.close()

            success = result_code == 0

            result_data = {
                "success": success,
                "host": host,
                "port": port,
                "connect_time_ms": round(connect_time, 2),
                "result_code": result_code
            }

            self._log(
                "service" if success else "error",
                "port_test_complete",
                result_data,
                f"Port test {host}:{port}: {'Open' if success else 'Closed/Unreachable'} ({connect_time:.1f}ms)"
            )

            return result_data

        except socket.timeout:
            result_data = {
                "success": False,
                "host": host,
                "port": port,
                "error": "Connection timeout"
            }
            self._log("error", "port_test_timeout", result_data, f"Port test {host}:{port} timed out")
            return result_data

        except Exception as e:
            result_data = {
                "success": False,
                "host": host,
                "port": port,
                "error": str(e)
            }
            self._log("error", "port_test_failed", result_data, f"Port test {host}:{port} failed: {e}")
            return result_data

    def test_rtmp_server(self, rtmp_url: str, timeout: int = 20) -> Dict[str, Any]:
        """
        Test RTMP server connectivity using FFmpeg.

        Args:
            rtmp_url: RTMP URL to test
            timeout: Timeout in seconds

        Returns:
            Dictionary with test results.
        """
        self._log("info", "rtmp_test_start", {"url": rtmp_url}, f"Testing RTMP server: {rtmp_url}")

        try:
            # Use ffprobe to test the RTMP stream (more reliable than ffmpeg for testing)
            cmd = [
                "ffprobe",
                "-rtmp_live", "live",
                "-i", rtmp_url,
                "-show_streams"
            ]

            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            test_duration = time.time() - start_time

            # Check if ffprobe could connect
            stderr = result.stderr
            stdout = result.stdout

            # Look for success indicators (ffprobe outputs to both stdout and stderr)
            output = stdout + stderr
            connected = (
                "[STREAM]" in output or
                "codec_name=" in output or
                "Stream #0" in output or
                "Video:" in output or
                "Audio:" in output
            )

            # Look for common errors
            errors = []
            if "Connection refused" in stderr:
                errors.append("Connection refused - RTMP server not running")
            if "No route to host" in stderr:
                errors.append("No route to host - Network unreachable")
            if "Connection timed out" in stderr:
                errors.append("Connection timed out")
            if "Invalid data found" in stderr:
                errors.append("Invalid stream data")

            result_data = {
                "success": connected,
                "url": rtmp_url,
                "test_duration_s": round(test_duration, 2),
                "errors": errors,
                "ffmpeg_output": stderr[-1000:]  # Last 1000 chars
            }

            self._log(
                "service" if connected else "error",
                "rtmp_test_complete",
                result_data,
                f"RTMP test {rtmp_url}: {'Connected' if connected else 'Failed'} - {errors[0] if errors else 'Success'}"
            )

            return result_data

        except subprocess.TimeoutExpired:
            result_data = {
                "success": False,
                "url": rtmp_url,
                "error": "Test timeout - server may be slow or unresponsive"
            }
            self._log("error", "rtmp_test_timeout", result_data, f"RTMP test {rtmp_url} timed out")
            return result_data

        except FileNotFoundError:
            result_data = {
                "success": False,
                "url": rtmp_url,
                "error": "ffprobe not found - please install FFmpeg"
            }
            self._log("error", "rtmp_test_failed", result_data, "ffprobe not found")
            return result_data

        except Exception as e:
            result_data = {
                "success": False,
                "url": rtmp_url,
                "error": str(e)
            }
            self._log("error", "rtmp_test_failed", result_data, f"RTMP test {rtmp_url} failed: {e}")
            return result_data

    def run_full_diagnostics(self, rtmp_url: str) -> Dict[str, Any]:
        """
        Run complete diagnostic suite on RTMP server.

        Args:
            rtmp_url: RTMP URL to diagnose

        Returns:
            Dictionary with all test results.
        """
        self._log("service", "diagnostics_start", {"url": rtmp_url}, f"Starting full diagnostics for {rtmp_url}")

        parsed = self.parse_rtmp_url(rtmp_url)
        host = parsed["host"]
        port = parsed["port"]

        results = {
            "rtmp_url": rtmp_url,
            "timestamp": time.time(),
            "tests": {}
        }

        # Test 1: Ping
        print(f"\n[1/3] Testing network connectivity to {host}...")
        results["tests"]["ping"] = self.ping_test(host)

        # Test 2: TCP Port
        print(f"[2/3] Testing RTMP port {port}...")
        results["tests"]["port"] = self.test_tcp_port(host, port)

        # Test 3: RTMP Connection
        print(f"[3/3] Testing RTMP server connection...")
        results["tests"]["rtmp"] = self.test_rtmp_server(rtmp_url)

        # Overall assessment
        all_passed = (
            results["tests"]["ping"].get("success", False) and
            results["tests"]["port"].get("success", False) and
            results["tests"]["rtmp"].get("success", False)
        )

        results["overall_success"] = all_passed

        # Generate summary
        summary = self._generate_summary(results)
        results["summary"] = summary

        self._log(
            "service" if all_passed else "error",
            "diagnostics_complete",
            {"success": all_passed},
            f"Diagnostics complete: {'All tests passed' if all_passed else 'Some tests failed'}"
        )

        return results

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary of diagnostics."""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("NETWORK DIAGNOSTICS SUMMARY")
        lines.append("=" * 60)

        # Ping test
        ping = results["tests"].get("ping", {})
        if ping.get("success"):
            lines.append(f"[PASS] Ping: Success ({ping.get('packet_loss_percent', 0)}% loss, {ping.get('avg_latency_ms', 'N/A')}ms avg)")
        else:
            lines.append(f"[FAIL] Ping: Failed - {ping.get('error', 'Unknown error')}")

        # Port test
        port = results["tests"].get("port", {})
        if port.get("success"):
            lines.append(f"[PASS] Port: Open ({port.get('connect_time_ms', 'N/A')}ms)")
        else:
            lines.append(f"[FAIL] Port: Closed/Unreachable - {port.get('error', 'Cannot connect')}")

        # RTMP test
        rtmp = results["tests"].get("rtmp", {})
        if rtmp.get("success"):
            lines.append(f"[PASS] RTMP: Connected ({rtmp.get('test_duration_s', 'N/A')}s)")
        else:
            errors = rtmp.get('errors', [])
            error_msg = errors[0] if errors else rtmp.get('error', 'Connection failed')
            lines.append(f"[FAIL] RTMP: Failed - {error_msg}")

        lines.append("=" * 60)

        if results["overall_success"]:
            lines.append("RESULT: All tests passed")
            lines.append("The RTMP server is reachable and streaming.")
        else:
            lines.append("RESULT: Some tests failed")
            lines.append("Please check network connection and RTMP server status.")

        lines.append("=" * 60 + "\n")

        return "\n".join(lines)


def main():
    """CLI entry point for network diagnostics."""
    import argparse

    parser = argparse.ArgumentParser(description="Network diagnostics for RTMP streaming")
    parser.add_argument("rtmp_url", help="RTMP URL to test (e.g., rtmp://192.168.100.23/live/cam)")
    parser.add_argument("--ping-only", action="store_true", help="Only run ping test")
    parser.add_argument("--port-only", action="store_true", help="Only run port test")

    args = parser.parse_args()

    diag = NetworkDiagnostics()

    if args.ping_only:
        parsed = diag.parse_rtmp_url(args.rtmp_url)
        result = diag.ping_test(parsed["host"])
        print(f"\nPing result: {'Success' if result['success'] else 'Failed'}")
    elif args.port_only:
        parsed = diag.parse_rtmp_url(args.rtmp_url)
        result = diag.test_tcp_port(parsed["host"], parsed["port"])
        print(f"\nPort result: {'Open' if result['success'] else 'Closed'}")
    else:
        results = diag.run_full_diagnostics(args.rtmp_url)
        print(results["summary"])


if __name__ == "__main__":
    main()
