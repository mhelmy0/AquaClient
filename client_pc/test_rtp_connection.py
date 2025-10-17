"""
Quick RTP connection diagnostic tool.

Tests UDP port 5000 reception and network connectivity.
"""

import socket
import sys
import requests
from datetime import datetime

def test_ping(host):
    """Test if host is reachable."""
    print(f"\n[1/4] Testing network connectivity to {host}...")
    import subprocess
    try:
        result = subprocess.run(['ping', '-n', '2', host],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print(f"✅ Host {host} is reachable")
            return True
        else:
            print(f"❌ Host {host} is not reachable")
            return False
    except Exception as e:
        print(f"❌ Ping failed: {e}")
        return False

def test_http_endpoint(url):
    """Test if HTTP endpoint is accessible."""
    print(f"\n[2/4] Testing HTTP endpoint {url}...")
    try:
        response = requests.get(url, timeout=3)
        print(f"✅ HTTP endpoint accessible")
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} bytes")
        return True
    except Exception as e:
        print(f"❌ HTTP endpoint failed: {e}")
        return False

def test_udp_port(port, timeout=10):
    """Test UDP port reception."""
    print(f"\n[3/4] Testing UDP port {port} reception...")
    print(f"   Listening for {timeout} seconds...")
    print(f"   Make sure your Raspberry Pi is streaming NOW!")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    try:
        # Bind to port 5000
        sock.bind(('', port))
        print(f"✅ Successfully bound to UDP port {port}")
        print(f"   Waiting for RTP packets...")

        # Try to receive data
        start_time = datetime.now()
        data, addr = sock.recvfrom(2048)
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"✅ Received UDP packet!")
        print(f"   From: {addr[0]}:{addr[1]}")
        print(f"   Size: {len(data)} bytes")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   First 16 bytes: {data[:16].hex()}")

        # Check if it looks like RTP
        if len(data) >= 12:
            version = (data[0] >> 6) & 0x3
            payload_type = data[1] & 0x7F
            if version == 2 and payload_type == 96:
                print(f"✅ Looks like RTP packet! (Version: {version}, PT: {payload_type})")
            else:
                print(f"⚠️  Packet received but might not be RTP (V: {version}, PT: {payload_type})")

        return True

    except socket.timeout:
        print(f"❌ Timeout - no UDP packets received on port {port}")
        print(f"   Possible causes:")
        print(f"   • Raspberry Pi is not streaming")
        print(f"   • Firewall is blocking port {port}")
        print(f"   • Pi is streaming to wrong IP address")
        print(f"   • Network issue")
        return False
    except OSError as e:
        print(f"❌ Port binding failed: {e}")
        print(f"   Port {port} might already be in use")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        sock.close()

def test_firewall():
    """Check Windows Firewall status."""
    print(f"\n[4/4] Checking Windows Firewall...")
    import subprocess
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if 'RTP' in result.stdout or '5000' in result.stdout:
            print(f"✅ Found firewall rules related to RTP/port 5000")
        else:
            print(f"⚠️  No firewall rules found for port 5000")
            print(f"   You may need to add a firewall rule:")
            print(f"   netsh advfirewall firewall add rule name=\"RTP Port 5000\" dir=in action=allow protocol=UDP localport=5000")

    except Exception as e:
        print(f"⚠️  Could not check firewall: {e}")

def get_local_ip():
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def main():
    print("=" * 60)
    print("RTP Connection Diagnostic Tool")
    print("=" * 60)

    pi_ip = "192.168.100.23"
    sdp_url = f"http://{pi_ip}/stream.sdp"
    port = 5000

    local_ip = get_local_ip()
    print(f"\nYour PC IP: {local_ip}")
    print(f"Raspberry Pi IP: {pi_ip}")
    print(f"RTP Port: {port}")

    # Run tests
    results = []
    results.append(("Network Ping", test_ping(pi_ip)))
    results.append(("HTTP/SDP Endpoint", test_http_endpoint(sdp_url)))
    results.append(("UDP Port Reception", test_udp_port(port, timeout=10)))
    test_firewall()

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! RTP streaming should work.")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Add firewall rule for UDP port 5000")
        print("2. Ensure Raspberry Pi is streaming")
        print("3. Verify Pi is streaming to your PC IP:", local_ip)

    print("=" * 60)

if __name__ == "__main__":
    main()
