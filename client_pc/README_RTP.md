# Aqua RTP Stream Monitor

A professional PyQt5-based GUI application for receiving, displaying, and recording RTP video streams from Raspberry Pi with real-time health monitoring.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## 🚀 Features

### Video Streaming
- ✅ **RTP/UDP Stream Reception** - Native H.264 RTP support
- ✅ **Auto SDP Discovery** - Automatic stream parameter detection
- ✅ **Live Preview** - Real-time video display with adjustable FPS
- ✅ **Reconnection Handling** - Automatic reconnect on connection loss

### Recording
- 📹 **High-Quality Recording** - MP4/MKV/AVI with configurable bitrate
- 🎚️ **Quality Presets** - Low, Medium, High, Ultra, Lossless modes
- ⏱️ **Segmented Recording** - Auto-split into 3-hour segments
- 🔧 **Custom Bitrate** - Fine-grained control (500 kbps - 15 Mbps)
- ⏯️ **Pause/Resume** - Control recording without stopping

### Monitoring
- 🍓 **Pi Health Dashboard** - Real-time Raspberry Pi metrics
  - CPU Temperature (with color-coded warnings)
  - CPU Usage percentage
  - System uptime
  - Memory and disk usage
- 💻 **Local System Info** - Disk space monitoring
- 📊 **Stream Statistics** - FPS, bitrate, resolution

### User Interface
- 🎨 **Modern Dark/Light Themes**
- ⌨️ **Global Hotkeys** - Keyboard shortcuts for all actions
- 🖱️ **System Tray Integration** - Minimize to tray
- 📷 **Snapshot Capture** - JPEG screenshots from live stream
- 📋 **Live Logging** - Real-time event logs

---

## 📋 Prerequisites

### Required Software

1. **Python 3.8+**
   ```powershell
   python --version
   ```

2. **FFmpeg** (Essential!)
   - Download: https://ffmpeg.org/download.html
   - Install to: `C:\ffmpeg`
   - Add to PATH: `C:\ffmpeg\bin`
   - Verify:
     ```powershell
     ffmpeg -version
     ```

3. **Python Packages**
   ```powershell
   pip install -r requirements.txt
   ```

### Raspberry Pi Requirements

Your Raspberry Pi should:
- Stream H.264 video over RTP to port 5000
- Provide SDP file at `http://<pi-ip>/stream.sdp`
- Expose health endpoint at `http://<pi-ip>/health` (optional)

---

## 🔧 Installation

### 1. Clone/Download Repository
```powershell
cd C:\Users\moham\Downloads\Aqua\client_pc
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Application

Edit [config.yaml](config.yaml):

```yaml
stream:
  type: "rtp"
  rtp:
    server_ip: "192.168.100.23"  # Your Raspberry Pi IP
    port: 5000
    auto_discover_sdp: true

recording:
  quality:
    preset: "high"  # low, medium, high, ultra, lossless

health:
  pi_health:
    enabled: true
    url: "http://192.168.100.23/health"
```

### 4. Run Application
```powershell
python rtp_gui.py
```

---

## 🎮 Usage Guide

### Quick Start

1. **Launch Application**
   ```powershell
   python rtp_gui.py
   ```

2. **Auto-Connect**
   - Application auto-discovers SDP on startup
   - Video stream starts automatically

3. **Start Recording**
   - Click `▶ Start Recording` button
   - Files saved to `records/videos/`

4. **Take Snapshots**
   - Click `📷 Take Snapshot`
   - Or press `Ctrl+Shift+S`

### Menu Options

#### File Menu
- **Settings** (`Ctrl+,`) - Configure all options
- **Exit** (`Ctrl+Q`) - Close application

#### Stream Menu
- **Connect** - Connect to RTP stream
- **Disconnect** - Stop stream

#### Recording Menu
- **Start Recording** (`Ctrl+Shift+R`)
- **Stop Recording** (`Ctrl+Shift+X`)

#### View Menu
- **Fullscreen** (`F11`) - Toggle fullscreen video
- **Always on Top** - Pin window on top

---

## 🎛️ Configuration Reference

### Stream Settings

```yaml
stream:
  type: "rtp"  # Stream type: rtp, rtmp, or auto

  rtp:
    server_ip: "192.168.100.23"
    port: 5000
    auto_discover_sdp: true
    sdp_url: "http://192.168.100.23/stream.sdp"

    # Fallback manual SDP
    manual_sdp: |
      v=0
      o=- 0 0 IN IP4 127.0.0.1
      s=Raspberry Pi Camera Stream
      c=IN IP4 0.0.0.0
      t=0 0
      m=video 5000 RTP/AVP 96
      a=rtpmap:96 H264/90000
      a=fmtp:96 packetization-mode=1

  url: "udp://@:5000"  # Constructed URL
  read_timeout_seconds: 30
```

### Recording Quality Presets

| Preset | Bitrate | File Size/Hour | Best For |
|--------|---------|----------------|----------|
| **low** | 1 Mbps | ~450 MB | Disk space saving |
| **medium** | 2.5 Mbps | ~1.1 GB | Balanced |
| **high** | 5 Mbps | ~2.2 GB | ⭐ Recommended |
| **ultra** | 8 Mbps | ~3.5 GB | Maximum quality |
| **lossless** | N/A | Variable | No re-encoding |

```yaml
recording:
  quality:
    preset: "high"
    custom_bitrate: 5000  # kbps (if preset = custom)
    codec: "h264"  # h264, h265, copy
    encoding_preset: "medium"  # ultrafast to veryslow
    crf: 23  # 0-51, lower = better
    output_format: "mp4"  # mp4, mkv, avi
```

### GUI Customization

```yaml
ui:
  window:
    width: 1024
    height: 768
    theme: "dark"  # dark or light
    always_on_top: false
    start_minimized: false

  hotkeys:
    snapshot: "ctrl+shift+s"
    start_recording: "ctrl+shift+r"
    stop_recording: "ctrl+shift+x"
    pause_recording: "ctrl+shift+p"

  preview:
    fps_limit: 30  # Lower for less CPU usage
```

### Pi Health Monitoring

```yaml
health:
  pi_health:
    enabled: true
    url: "http://192.168.100.23/health"
    update_interval: 5  # seconds

    # Alert thresholds
    temp_warning: 70   # °C
    temp_critical: 80  # °C
    cpu_warning: 90    # %
    cpu_critical: 95   # %
```

---

## 📊 Raspberry Pi Health Endpoint

The application expects a JSON health endpoint on your Pi:

### Endpoint URL
```
GET http://192.168.100.23/health
```

### Expected JSON Response
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

### Health Status Colors

- 🟢 **Green (Healthy)**: Temp < 70°C, CPU < 90%
- 🟡 **Yellow (Warning)**: Temp 70-80°C or CPU 90-95%
- 🔴 **Red (Critical)**: Temp > 80°C or CPU > 95%
- ⚪ **Gray (Disconnected)**: Cannot reach endpoint

---

## 🎹 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+S` | Take snapshot |
| `Ctrl+Shift+R` | Start recording |
| `Ctrl+Shift+X` | Stop recording |
| `Ctrl+Shift+P` | Pause/Resume recording |
| `Ctrl+Shift+M` | Show/Hide window |
| `F11` | Toggle fullscreen |
| `Ctrl+,` | Settings dialog |
| `Ctrl+Q` | Quit application |

---

## 📁 Output File Structure

```
client_pc/
├── records/
│   ├── videos/
│   │   ├── recording_20241017_140000.mp4  # Segment 1
│   │   ├── recording_20241017_170000.mp4  # Segment 2 (3hrs later)
│   │   └── recording_20241017_200000.mp4  # Segment 3
│   └── snapshots/
│       ├── snapshot_20241017_143022.jpg
│       └── snapshot_20241017_155812.jpg
├── logs/
│   └── client.log  # Application logs
└── config.yaml  # Configuration file
```

---

## 🐛 Troubleshooting

### Video Not Displaying

**Symptoms:** Black screen, "No Video Stream" message

**Solutions:**
1. Check FFmpeg installation:
   ```powershell
   ffmpeg -version
   ```
2. Test RTP stream directly:
   ```powershell
   ffplay -protocol_whitelist file,udp,rtp -i udp://@:5000
   ```
3. Verify Pi is streaming to port 5000:
   ```bash
   # On Raspberry Pi
   sudo netstat -tulpn | grep 5000
   ```
4. Check Windows Firewall allows UDP port 5000
5. Ensure Pi and PC are on same network

### SDP Auto-Discovery Failed

**Symptoms:** "SDP auto-discovery failed" in logs

**Solutions:**
1. Test SDP endpoint:
   ```powershell
   curl http://192.168.100.23/stream.sdp
   ```
2. If endpoint doesn't exist, use manual SDP in `config.yaml`:
   ```yaml
   rtp:
     auto_discover_sdp: false
     manual_sdp: |
       v=0
       # ... your SDP content here
   ```
3. Check Pi IP address is correct
4. Verify Pi web server is running

### Recording Won't Start

**Symptoms:** "Failed to start recording" error

**Solutions:**
1. Verify FFmpeg is in PATH
2. Check disk space (needs >500 MB):
   ```powershell
   Get-PSDrive C | Select-Object Used,Free
   ```
3. Ensure `records/videos/` directory exists
4. Check logs in `logs/client.log` for FFmpeg errors
5. Try lossless mode first (no re-encoding)

### Pi Health Shows "Disconnected"

**Symptoms:** Gray status, "N/A" for all metrics

**Solutions:**
1. Test health endpoint:
   ```powershell
   curl http://192.168.100.23/health
   ```
2. Verify Pi IP is correct
3. Check Pi web server is running
4. Temporarily disable if not needed:
   ```yaml
   health:
     pi_health:
       enabled: false
   ```

### High CPU Usage

**Symptoms:** Application using >50% CPU

**Solutions:**
1. Lower preview FPS:
   ```yaml
   ui:
     preview:
       fps_limit: 15  # Instead of 30
   ```
2. Use lossless recording (no re-encoding):
   ```yaml
   recording:
     quality:
       preset: "lossless"
   ```
3. Reduce video preview size
4. Close other applications

### Port Already in Use

**Symptoms:** "Address already in use" error

**Solutions:**
1. Check what's using port 5000:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. Kill the process or use different port
3. Change port in `config.yaml`:
   ```yaml
   rtp:
     port: 5001  # Use different port
   ```

---

## 📈 Performance Tuning

### For Best Quality
```yaml
recording:
  quality:
    preset: "ultra"
    codec: "h264"
    encoding_preset: "slow"
    crf: 18
```

### For Low CPU Usage
```yaml
recording:
  quality:
    preset: "lossless"  # No re-encoding
    codec: "copy"

ui:
  preview:
    fps_limit: 15  # Lower FPS
```

### For Minimal Disk Space
```yaml
recording:
  quality:
    preset: "low"
    codec: "h265"  # Better compression
    encoding_preset: "fast"
```

---

## 🔬 Technical Details

### Architecture

```
┌──────────────┐     RTP/UDP     ┌────────────┐
│ Raspberry Pi │ ─────────────> │ Windows PC │
│ (Camera)     │  Port 5000     │ (Receiver) │
└──────────────┘                 └────────────┘
       │                                │
       │ HTTP                           │
       │ /health                        │
       │ /stream.sdp                    │
       └───────────────────────────────>│
                                        │
                                   ┌────┴────┐
                                   │ RTP GUI │
                                   └────┬────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              ┌─────▼─────┐      ┌─────▼──────┐     ┌─────▼─────┐
              │ Video     │      │ Recorder   │     │ Health    │
              │ Display   │      │ (FFmpeg)   │     │ Monitor   │
              └───────────┘      └────────────┘     └───────────┘
```

### Modules

- **rtp_receiver.py** - RTP stream reception and SDP parsing
- **rtp_recorder.py** - Video recording with quality control
- **pi_health_monitor.py** - Raspberry Pi health metrics
- **gui/rtp_video_widget.py** - Live video display widget
- **gui/control_panel.py** - Recording controls and health display
- **gui/quality_dialog.py** - Quality settings dialog
- **rtp_gui.py** - Main application entry point

### Dependencies

| Package | Purpose |
|---------|---------|
| PyQt5 | GUI framework |
| opencv-python | Video capture and processing |
| requests | HTTP requests for SDP/health |
| PyYAML | Configuration parsing |
| psutil | System monitoring |
| pynput | Global hotkeys |

---

## 🚀 Advanced Usage

### Command Line Options

```powershell
# Custom config file
python rtp_gui.py --config custom_config.yaml

# Help
python rtp_gui.py --help
```

### Programmatic Usage

```python
from modules.rtp_receiver import RTPReceiver
from modules.rtp_recorder import RTPRecorder

# Initialize receiver
receiver = RTPReceiver(server_ip="192.168.100.23")
receiver.fetch_sdp()

# Get stream URL
stream_url = receiver.get_stream_url()  # "udp://@:5000"

# Start recording
recorder = RTPRecorder(quality="high")
recorder.start_recording(stream_url, segment_duration=10800)
```

### Custom Quality Settings

```yaml
recording:
  quality:
    preset: "custom"
    custom_bitrate: 6000  # 6 Mbps
    codec: "h265"         # Better compression than h264
    encoding_preset: "medium"
    crf: 20               # Lower = better quality
    output_format: "mkv"  # Matroska container
```

---

## 📝 Logs and Debugging

### Log Files

Logs are written to `logs/client.log` with automatic rotation.

**View Logs:**
```powershell
# Follow logs in real-time
Get-Content logs\client.log -Wait -Tail 50

# Search for errors
Select-String -Path logs\client.log -Pattern "error"
```

### Debug Mode

Enable detailed logging:

```yaml
logging:
  level: debug  # Instead of "info"
```

### Log Format

```json
{
  "lvl": "info",
  "comp": "rtp_receiver",
  "evt": "sdp_discovered",
  "ctx": {
    "port": 5000,
    "codec": "H264"
  }
}
```

---

## 🔐 Security Considerations

- RTP streams are **unencrypted** - use on trusted networks only
- Health endpoint exposes system info - secure your Pi
- No authentication on RTP - anyone on network can receive
- For production, consider SRTP (Secure RTP) or VPN

---

## 📚 Additional Resources

- [RTP_GUIDE.md](RTP_GUIDE.md) - Detailed setup guide
- [QUICK_START.md](QUICK_START.md) - Original RTMP guide
- [config.yaml](config.yaml) - Full configuration reference

---

## 🛠️ Development

### Project Structure
```
client_pc/
├── modules/
│   ├── rtp_receiver.py        # RTP stream handling
│   ├── rtp_recorder.py        # Video recording
│   ├── pi_health_monitor.py   # Health monitoring
│   └── gui/
│       ├── rtp_video_widget.py
│       ├── control_panel.py
│       └── quality_dialog.py
├── rtp_gui.py                 # Main entry point
├── config.yaml                # Configuration
├── requirements.txt           # Dependencies
└── logs/                      # Application logs
```

### Testing

```powershell
# Run tests
pytest tests/

# With coverage
pytest --cov=modules tests/
```

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- FFmpeg team for excellent video processing tools
- PyQt5 for the GUI framework
- Raspberry Pi community

---

**Happy Streaming! 🎥**

For support, check logs and review the troubleshooting section above.
