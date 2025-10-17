"""Create SDP file for RTP streaming."""

from modules.config import load_config
from modules.rtp_receiver import RTPReceiver

# Load config
config = load_config("config.yaml")

# Create receiver
rtp_config = config.get("stream", {}).get("rtp", {})
receiver = RTPReceiver(server_ip=rtp_config.get("server_ip", "192.168.100.23"))

# Load manual SDP
manual_sdp = rtp_config.get("manual_sdp", "")
if manual_sdp:
    receiver.use_manual_sdp(manual_sdp)
    print("[OK] Manual SDP loaded")

    # Save to file
    if receiver.save_sdp_file("stream.sdp"):
        print("[OK] SDP file created: stream.sdp")
        print("\nNow run:")
        print("  ffplay -protocol_whitelist file,udp,rtp -i stream.sdp")
    else:
        print("[ERROR] Failed to create SDP file")
else:
    print("[ERROR] No manual SDP in config.yaml")
