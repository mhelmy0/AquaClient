#!/usr/bin/env python3
"""
Quick network test script for RTMP server.

Usage:
    python test_network.py
"""

import sys
from pathlib import Path

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from network_diagnostics import NetworkDiagnostics

# RTMP server URL - change this to match your server
RTMP_URL = "rtmp://192.168.100.23/live/cam"


def main():
    print("=" * 70)
    print("RTMP SERVER NETWORK TEST")
    print("=" * 70)
    print(f"\nTesting: {RTMP_URL}\n")

    diag = NetworkDiagnostics()
    results = diag.run_full_diagnostics(RTMP_URL)

    # Print summary
    print(results["summary"])

    # Additional recommendations based on results
    print("\n" + "=" * 70)
    print("TROUBLESHOOTING RECOMMENDATIONS")
    print("=" * 70)

    ping_result = results["tests"].get("ping", {})
    port_result = results["tests"].get("port", {})
    rtmp_result = results["tests"].get("rtmp", {})

    if not ping_result.get("success"):
        print("\n⚠ PING FAILED:")
        print("  - Check if the camera/server is powered on")
        print("  - Verify the IP address is correct")
        print("  - Check network cables and switches")
        print("  - Try pinging from command line: ping 192.168.100.23")

    elif ping_result.get("packet_loss_percent", 0) > 0:
        print("\n⚠ PACKET LOSS DETECTED:")
        print(f"  - {ping_result['packet_loss_percent']}% packet loss indicates unstable network")
        print("  - Check for network congestion")
        print("  - Try using a wired connection instead of WiFi")
        print("  - Check for faulty network cables")

    if ping_result.get("avg_latency_ms", 0) > 50:
        print("\n⚠ HIGH LATENCY:")
        print(f"  - Average latency: {ping_result['avg_latency_ms']}ms")
        print("  - This may cause stream interruptions")
        print("  - Reduce network hops between client and server")

    if not port_result.get("success"):
        print("\n⚠ RTMP PORT NOT ACCESSIBLE:")
        print("  - RTMP server may not be running on the Pi")
        print("  - Check if the streaming service is active")
        print("  - Firewall may be blocking port 1935")
        print("  - Verify server configuration")

    if not rtmp_result.get("success"):
        print("\n⚠ RTMP CONNECTION FAILED:")
        errors = rtmp_result.get("errors", [])
        if errors:
            for error in errors:
                print(f"  - {error}")
        print("\n  Possible causes:")
        print("  - RTMP server crashed or stopped")
        print("  - Stream path is incorrect (check /live/cam)")
        print("  - Camera is not providing video feed")
        print("  - FFmpeg timeout setting too low (increase read_timeout_seconds in config)")

    if results["overall_success"]:
        print("\n✓ All tests passed! The connection looks good.")
        print("\nIf you're still experiencing issues:")
        print("  - Check the new logs for detailed FFmpeg error messages")
        print("  - Monitor the stream for 1-2 minutes to check stability")
        print("  - Consider increasing read_timeout_seconds to 30 in config.yaml")

    print("\n" + "=" * 70)

    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
