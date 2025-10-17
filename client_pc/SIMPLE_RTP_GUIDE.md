# Simple RTP Stream Viewer - Quick Guide

## Overview

This is a **simplified version** of the RTP GUI that uses FFplay for video display with minimal complexity.

---

## ✅ Features

- ✅ **Manual SDP configuration** (no auto-discovery)
- ✅ **FFplay integration** (simpler than OpenCV)
- ✅ **Minimal dependencies**
- ✅ **Easy to troubleshoot**
- ✅ **One-click launch**

---

## 🚀 Quick Start

### 1. Configure SDP

The SDP is already configured in `config.yaml`:

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

### 2. Add Firewall Rule

Run as **Administrator**:

```powershell
netsh advfirewall firewall add rule name="RTP Port 5000" dir=in action=allow protocol=UDP localport=5000
```

### 3. Run the Application

**Option 1 - Double-click:**
```
run_simple_rtp.bat
```

**Option 2 - Command line:**
```powershell
python simple_rtp_gui.py
```

### 4. Play Stream

1. Make sure your Raspberry Pi is streaming to port 5000
2. Click "▶ Play Stream with FFplay"
3. Video will appear in a separate FFplay window

---

## 📋 Requirements

### Required

- ✅ Python 3.8+
- ✅ FFmpeg/FFplay (in PATH)
- ✅ PyQt5
- ✅ PyYAML

### Install Dependencies

```powershell
pip install PyQt5 PyYAML requests
```

### Install FFmpeg

1. Download from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH
4. Verify:
   ```powershell
   ffplay -version
   ```

---

## 🎯 How It Works

```
┌──────────────┐                          ┌────────────┐
│ Raspberry Pi │ ───RTP/UDP──────────> │ Windows PC │
│  (Camera)    │    Port 5000           │  (Viewer)  │
└──────────────┘                          └────────────┘
                                                │
                                          ┌─────▼─────┐
                                          │ FFplay    │
                                          │ Window    │
                                          └───────────┘
```

**Flow:**
1. Application reads SDP from `config.yaml`
2. Generates stream URL: `udp://@:5000`
3. Launches FFplay with the URL
4. FFplay displays video in separate window

---

## 🔧 Troubleshooting

### No Video Appears

**Check 1: Is FFplay installed?**
```powershell
ffplay -version
```

If not found, install FFmpeg.

**Check 2: Is firewall blocking?**
```powershell
# Add rule
netsh advfirewall firewall add rule name="RTP Port 5000" dir=in action=allow protocol=UDP localport=5000
```

**Check 3: Is Pi streaming?**
Test UDP port:
```powershell
python test_udp_simple.py
```

Should show: `[SUCCESS] Received UDP packet!`

**Check 4: Is Pi streaming to your IP?**
Your PC IP: `192.168.100.41`

Make sure Pi is sending to this IP on port 5000.

### FFplay Error Messages

Common errors shown in the log viewer:

**"Protocol not found"**
- Solution: FFmpeg not installed or too old
- Reinstall FFmpeg

**"Connection timeout"**
- Solution: No RTP packets arriving
- Check firewall and Pi configuration

**"Invalid data found"**
- Solution: Wrong codec or stream format
- Verify SDP matches Pi's output

---

## 🆚 Simple vs Full GUI

| Feature | Simple GUI | Full GUI (rtp_gui.py) |
|---------|------------|----------------------|
| Video Display | FFplay (external) | OpenCV (embedded) |
| Configuration | Manual SDP only | Auto + Manual SDP |
| Health Monitor | No | Yes |
| Recording | No | Yes |
| Snapshots | No | Yes |
| Complexity | ⭐ Low | ⭐⭐⭐ Medium |
| Use Case | Testing/Viewing | Production |

---

## 💡 Tips

### For Best Results

1. **Start Pi streaming first**, then run the GUI
2. **Check logs** if video doesn't appear
3. **Test UDP port** with `test_udp_simple.py` first
4. **Use local network** (same subnet as Pi)

### FFplay Keyboard Shortcuts

When FFplay window is active:

- `q` - Quit
- `f` - Toggle fullscreen
- `p` or `Space` - Pause
- `s` - Step to next frame
- `w` - Show audio waves

### Command Line Testing

Test stream directly with FFplay:

```powershell
ffplay -protocol_whitelist file,udp,rtp -i udp://@:5000
```

---

## 📁 Files

- `simple_rtp_gui.py` - Main application
- `run_simple_rtp.bat` - Quick launcher
- `config.yaml` - Configuration (manual SDP)
- `logs/simple_rtp.log` - Application logs

---

## 🔄 Differences from Full GUI

**Removed for Simplicity:**
- Auto SDP discovery (always uses manual)
- Embedded video display (uses external FFplay)
- Recording functionality
- Snapshot capture
- Pi health monitoring
- Quality settings dialog
- System tray integration

**Benefits:**
- ✅ Easier to troubleshoot
- ✅ Fewer dependencies
- ✅ Clearer error messages
- ✅ Faster startup
- ✅ Works with any FFplay version

---

## 🚦 Status Indicators

The log viewer shows:

- **"FFplay started successfully"** - Command executed
- **"Video should appear"** - Check for FFplay window
- **"FFplay exited"** - Process stopped (check errors below)
- **"ERROR: FFplay not found"** - Install FFmpeg
- **"ERROR: No stream URL"** - Check SDP configuration

---

## 🔐 Security Note

- RTP streams are **unencrypted**
- Use on trusted networks only
- Consider VPN for remote access

---

## 📞 Getting Help

If you encounter issues:

1. **Check logs** in the GUI log viewer
2. **Run UDP test**: `python test_udp_simple.py`
3. **Test FFplay directly**: `ffplay -i udp://@:5000`
4. **Verify firewall** allows UDP port 5000
5. **Check Pi is streaming** to your IP

---

## ✨ Summary

This simple GUI is perfect for:
- ✅ **Testing** your RTP setup
- ✅ **Viewing** live streams
- ✅ **Troubleshooting** connection issues
- ✅ **Learning** how RTP streaming works

For production use with recording, use the full `rtp_gui.py` instead.

**Happy Streaming! 🎥**
