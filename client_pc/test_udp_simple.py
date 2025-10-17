"""Simple UDP port 5000 receiver test."""

import socket
import sys

port = 5000
timeout = 15

print(f"Testing UDP port {port} reception...")
print(f"Your PC IP: 192.168.100.41")
print(f"Listening on 0.0.0.0:{port} for {timeout} seconds...")
print(f"\nMake sure your Raspberry Pi is streaming NOW!\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(timeout)

try:
    sock.bind(('', port))
    print(f"[OK] Bound to UDP port {port}")
    print(f"[WAITING] Listening for packets...\n")

    data, addr = sock.recvfrom(2048)

    print(f"\n[SUCCESS] Received UDP packet!")
    print(f"From: {addr[0]}:{addr[1]}")
    print(f"Size: {len(data)} bytes")
    print(f"First 16 bytes (hex): {data[:16].hex()}")

    # Check RTP header
    if len(data) >= 12:
        version = (data[0] >> 6) & 0x3
        payload_type = data[1] & 0x7F
        print(f"\nRTP Header Info:")
        print(f"  Version: {version} (should be 2)")
        print(f"  Payload Type: {payload_type} (should be 96 for H264)")

        if version == 2 and payload_type == 96:
            print(f"\n[SUCCESS] Valid RTP/H264 packet detected!")
        else:
            print(f"\n[WARNING] Packet might not be RTP/H264")

    sys.exit(0)

except socket.timeout:
    print(f"\n[TIMEOUT] No packets received in {timeout} seconds")
    print(f"\nPossible causes:")
    print(f"1. Raspberry Pi is not streaming to 192.168.100.41")
    print(f"2. Windows Firewall is blocking UDP port {port}")
    print(f"3. Pi is streaming but to a different IP/port")
    print(f"\nTo fix firewall (run as Administrator):")
    print(f'netsh advfirewall firewall add rule name="RTP Port 5000" dir=in action=allow protocol=UDP localport=5000')
    sys.exit(1)

except OSError as e:
    print(f"\n[ERROR] {e}")
    print(f"Port {port} might already be in use")
    print(f"Close the rtp_gui.py if it's running")
    sys.exit(1)

finally:
    sock.close()
