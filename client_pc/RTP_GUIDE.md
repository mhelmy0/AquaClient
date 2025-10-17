# RTP Stream Receiver & Recorder - Quick Start Guide

## Overview

This application receives RTP video streams from your Raspberry Pi, displays them in real-time, and records them with configurable quality settings. It also monitors the Raspberry Pi's health (temperature, CPU usage).

---

## Features

✅ **RTP Stream Reception** - Receive H.264 video over RTP/UDP
✅ **Auto SDP Discovery** - Automatically fetch stream parameters from Pi
✅ **Live Video Preview** - Real-time video display with adjustable FPS
✅ **High-Quality Recording** - Record to MP4 with configurable bitrate
✅ **Snapshot Capture** - Take JPEG snapshots from live stream
✅ **Pi Health Monitoring** - Monitor CPU temp, usage, uptime
✅ **Quality Presets** - Low, Medium, High, Ultra, Lossless options
✅ **Segmented Recording** - Auto-split recordings (3-hour segments)
✅ **PyQt5 GUI** - Clean, modern interface

---

## Prerequisites

### 1. FFmpeg Installation (Required)

FFmpeg is required for receiving RTP streams and recording.

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH
4. Verify installation:
   ```powershell
   ffmpeg -version
   ```

### 2. Python Dependencies

Install required packages:
```powershell
pip install -r requirements.txt
```

---

## Configuration

The application is configured via [config.yaml](config.yaml).

### Key Settings:

```yaml
stream:
  type: "rtp"
  rtp:
    server_ip: "192.168.100.23"  # Your Raspberry Pi IP
    port: 5000                    # RTP port from SDP
    auto_discover_sdp: true       # Auto-fetch SDP
```

### Recording Quality Presets:

```yaml
recording:
  quality:
    preset: "high"  # Options: low, medium, high, ultra, lossless, custom
```

| Preset | Bitrate | File Size (per hour) | Use Case |
|--------|---------|----------------------|----------|
| Low | 1 Mbps | ~450 MB | Save disk space |
| Medium | 2.5 Mbps | ~1.1 GB | Balanced |
| **High** | 5 Mbps | ~2.2 GB | **Recommended** |
| Ultra | 8 Mbps | ~3.5 GB | Best quality |
| Lossless | N/A | Variable | No re-encoding |

---

## Running the Application

### Quick Start:

```powershell
# Navigate to client_pc directory
cd C:\Users\moham\Downloads\Aqua\client_pc

# Run RTP GUI
python rtp_gui.py
```

### With Custom Config:

```powershell
python rtp_gui.py --config path\to\config.yaml
```

---

## Using the GUI

### Main Window Layout:

```
┌─────────────────────────────────────────────────┐
│  Menu Bar (File, Stream, Recording, View)      │
├─────────────────────┬───────────────────────────┤
│                     │  🎬 Recording Controls    │
│                     │   [▶ Start] [⏸ Pause]    │
│   📹 Video Preview  │   [⏹ Stop]                │
│                     │                           │
│                     │  📷 Quick Actions         │
│                     │   [📷 Snapshot]           │
│                     │   [🔌 Reconnect]          │
│                     │                           │
├─────────────────────┤  🍓 Raspberry Pi Health   │
│   📋 Log Viewer     │   Status: ✅ Healthy      │
│                     │   Temp: 45.2°C [████░░░░] │
│                     │   CPU: 12.3%   [██░░░░░░] │
│                     │   Uptime: 2d 5h 23m       │
│                     │                           │
│                     │  💻 Local System          │
│                     │   Stream: udp://@:5000    │
│                     │   Quality: 1920x1080 @5M  │
│                     │   Disk: 125.4 GB free     │
└─────────────────────┴───────────────────────────┘
```

### Step-by-Step Usage:

1. **Start the application**
   ```powershell
   python rtp_gui.py
   ```

2. **Verify SDP Auto-Discovery**
   - Check log viewer for "SDP auto-discovery successful"
   - If failed, manually configure SDP in `config.yaml`

3. **Connect to Stream**
   - Menu: `Stream → Connect`
   - Or press the reconnect button
   - Video should appear in the preview window

4. **Start Recording**
   - Click `▶ Start Recording`
   - Files saved to `records/videos/`
   - Format: `recording_YYYYMMDD_HHMMSS.mp4`

5. **Take Snapshots**
   - Click `📷 Take Snapshot`
   - Or press `Ctrl+Shift+S` (configurable hotkey)
   - Files saved to `records/snapshots/`

6. **Monitor Pi Health**
   - Temperature and CPU usage update every 5 seconds
   - Color coding:
     - 🟢 Green: Normal
     - 🟡 Yellow: Warning (>70°C or >90% CPU)
     - 🔴 Red: Critical (>80°C or >95% CPU)

7. **Adjust Recording Quality**
   - Menu: `File → Settings`
   - Recording Quality tab
   - Select preset or custom bitrate
   - Apply and restart recording

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+S` | Take snapshot |
| `Ctrl+Shift+R` | Start recording |
| `Ctrl+Shift+X` | Stop recording |
| `Ctrl+Shift+P` | Pause/Resume recording |
| `F11` | Toggle fullscreen video |
| `Ctrl+,` | Open settings |
| `Ctrl+Q` | Quit application |

---

## SDP Configuration

The application uses SDP (Session Description Protocol) to discover stream parameters.

### Auto-Discovery (Recommended):

```yaml
rtp:
  auto_discover_sdp: true
  sdp_url: "http://192.168.100.23/stream.sdp"
```

The app will fetch SDP from your Pi's `/stream.sdp` endpoint.

### Manual SDP (Fallback):

If auto-discovery fails, configure manual SDP:

```yaml
rtp:
  manual_sdp: |
    v=0
    o=- 0 0 IN IP4 127.0.0.1
    s=Raspberry Pi Camera Stream
    c=IN IP4 0.0.0.0
    t=0 0
    m=video 5000 RTP/AVP 96
    a=rtpmap:96 H264/90000
    a=fmtp:96 packetization-mode=1
```

**Key Parameters:**
- `m=video 5000` - Port 5000 for video
- `RTP/AVP 96` - RTP payload type 96
- `H264/90000` - H.264 codec, 90kHz clock rate

---

## Raspberry Pi Health Endpoint

The app expects a health endpoint on your Pi at:
```
http://192.168.100.23/health
```

### Expected JSON Format:

```json
{
  "temperature": 45.2,
  "cpu_usage": 12.3,
  "uptime": 186180,
  "memory": {
    "used": 512,
    "total": 1024,
    "percent": 50.0
  },
  "disk": {
    "used": 10240,
    "total": 32768,
    "percent": 31.2
  }
}
```

If you don't have this endpoint, disable health monitoring:
```yaml
health:
  pi_health:
    enabled: false
```

---

## Troubleshooting

### Issue: Video not displaying

**Solutions:**
1. Check FFmpeg is installed and in PATH
2. Verify Pi is streaming to port 5000
3. Check firewall allows UDP port 5000
4. Test UDP reception:
   ```powershell
   ffplay -protocol_whitelist udp,rtp -i udp://@:5000
   ```

### Issue: SDP auto-discovery failed

**Solutions:**
1. Check Pi health endpoint is accessible:
   ```powershell
   curl http://192.168.100.23/stream.sdp
   ```
2. Use manual SDP in `config.yaml`
3. Check Pi IP address is correct

### Issue: Recording not starting

**Solutions:**
1. Check FFmpeg is installed
2. Verify `records/videos/` directory exists
3. Check disk space (needs >500 MB)
4. Review logs in `logs/client.log`

### Issue: Pi health shows "Disconnected"

**Solutions:**
1. Check Pi health endpoint:
   ```powershell
   curl http://192.168.100.23/health
   ```
2. Verify Pi IP is correct
3. Check Pi web server is running
4. Disable health monitoring if not needed

### Issue: High CPU usage

**Solutions:**
1. Lower FPS limit in config:
   ```yaml
   ui:
     preview:
       fps_limit: 15  # Lower from 30
   ```
2. Use lossless recording (no re-encoding)
3. Reduce video preview size

---

## File Output Structure

```
client_pc/
├── records/
│   ├── videos/
│   │   ├── recording_20241017_143022.mp4
│   │   ├── recording_20241017_173022.mp4  # 3-hour segments
│   │   └── recording_20241017_203022.mp4
│   └── snapshots/
│       ├── snapshot_20241017_143523.jpg
│       └── snapshot_20241017_145812.jpg
└── logs/
    └── client.log
```

---

## Advanced: Custom Quality Settings

For fine-grained control, use custom quality mode:

```yaml
recording:
  quality:
    preset: "custom"
    custom_bitrate: 6000  # 6 Mbps
    codec: "h264"
    encoding_preset: "medium"
    crf: 23
    output_format: "mp4"
```

**Encoding Presets (speed vs quality):**
- `ultrafast` - Fastest, lowest quality
- `medium` - Balanced (recommended)
- `veryslow` - Slowest, best quality

**CRF (Constant Rate Factor):**
- Lower = better quality, larger files
- Range: 0-51
- Recommended: 18-28
- Default: 23

---

## Performance Tips

### For Best Quality:
```yaml
recording:
  quality:
    preset: "ultra"
    encoding_preset: "slow"
    crf: 18
```

### For Low Disk Usage:
```yaml
recording:
  quality:
    preset: "low"
    encoding_preset: "fast"
```

### For Fastest (no re-encoding):
```yaml
recording:
  quality:
    preset: "lossless"
    codec: "copy"
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 10/11 |
| CPU | Dual-core 2.0 GHz | Quad-core 3.0 GHz |
| RAM | 4 GB | 8 GB+ |
| Disk | 10 GB free | 100 GB+ SSD |
| Network | 10 Mbps | 100 Mbps+ |

---

## Next Steps

1. ✅ Configure `config.yaml` with your Pi's IP
2. ✅ Ensure FFmpeg is installed
3. ✅ Run `python rtp_gui.py`
4. ✅ Connect to RTP stream
5. ✅ Start recording
6. ✅ Adjust quality settings as needed

---

## Support

For issues or questions:
1. Check logs in `logs/client.log`
2. Review `TROUBLESHOOTING.md`
3. Ensure Pi is streaming correctly
4. Test with FFmpeg directly first

---

**Enjoy your RTP streaming! 🎬**
