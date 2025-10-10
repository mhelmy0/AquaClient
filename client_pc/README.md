# Windows PC RTMP Client

This directory contains the client-side code for receiving and recording RTMP video streams from the Raspberry Pi.

## Features

- **RTMP stream reception** - Receives H.264 video from Nginx-RTMP server
- **Automatic recording** - Records to 3-hour MP4 segments with no re-encoding
- **Snapshot capture** - Extract single frames on demand or at intervals
- **Disk space guard** - Automatically pauses recording when disk is low
- **Auto-reconnection** - Handles stream drops with exponential backoff
- **Health monitoring** - Tracks FPS, disk space, and stream status
- **GUI interface** - PyQt5-based graphical interface with live preview and controls
- **CLI interface** - Full command-line control
- **Global hotkeys** - System-wide keyboard shortcuts for quick actions
- **System tray** - Background operation with tray icon and quick menu

## Prerequisites

### Software
- Windows 10/11
- Python 3.11 or later
- FFmpeg (must be in PATH)
- Docker Desktop (for Nginx-RTMP server)

## Installation

1. **Install Python dependencies**:
   ```cmd
   cd client_pc
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install FFmpeg**:
   - Download from https://ffmpeg.org/download.html
   - Add to system PATH
   - Verify: `ffmpeg -version`

3. **Configure RTMP URL**:
   Edit `config.yaml` and set `stream.url` to point to your RTMP server:
   ```yaml
   stream:
     url: "rtmp://127.0.0.1/live/cam"
   ```

4. **Create output directories**:
   ```cmd
   mkdir records\videos
   mkdir records\snapshots
   mkdir logs
   ```

## Configuration

Edit `config.yaml` to customize settings:

- **stream.url**: RTMP stream endpoint (local Nginx server)
- **stream.read_timeout_seconds**: Timeout before triggering reconnect
- **recording.enabled**: Enable/disable recording
- **recording.segment_seconds**: Segment duration (10800 = 3 hours)
- **recording.disk_free_floor_mib**: Pause recording below this free space
- **snapshots.interval_seconds**: Automatic snapshot interval (0 = disabled)
- **ui.enabled**: Enable/disable GUI (must be true for GUI mode)
- **ui.hotkeys**: Configure global keyboard shortcuts
- **ui.window**: Window size, theme, and behavior settings
- **ui.system_tray**: Tray icon settings and close behavior
- **logging**: Log level, file path, and rotation settings

## Usage

### GUI Mode (Recommended)

**Start the GUI application**:
```cmd
venv\Scripts\activate
python -m modules.gui_launcher
```

**GUI Features**:
- **Live Video Preview**: Real-time stream display with auto-reconnection
- **Recording Controls**: Start, Stop, Pause, Resume buttons
- **Quick Actions**: Snapshot and Reconnect buttons
- **Health Monitor**: Stream URL, quality, disk space, current file, segment progress
- **Statistics Panel**: Today's recording time, segments, snapshots, total disk usage
- **Log Viewer**: Real-time activity logs
- **System Tray**: Minimize to tray, quick actions menu
- **Global Hotkeys**: Control recording without focusing window

**GUI Shortcuts**:
- `F11` or double-click video: Toggle fullscreen
- `Ctrl+,`: Open settings
- `Ctrl+Q`: Exit application
- `Ctrl+Shift+S`: Take snapshot (global)
- `Ctrl+Shift+R`: Start recording (global)
- `Ctrl+Shift+E`: Stop recording (global)
- `Ctrl+Shift+H`: Show/hide window (global)

**Menu Options**:
- **File**: Settings, Exit
- **Stream**: Connect, Disconnect
- **Recording**: Start Recording, Stop Recording
- **View**: Fullscreen, Always on Top
- **Help**: About

**Configuration for GUI** (config.yaml):
```yaml
ui:
  enabled: true  # Must be true for GUI mode
  window:
    width: 1024
    height: 768
    theme: "dark"  # or "light"
    start_minimized: false
    always_on_top: false

  preview:
    fps_limit: 30  # GUI preview framerate

  hotkeys:
    enabled: true
    snapshot: "ctrl+shift+s"
    start_recording: "ctrl+shift+r"
    stop_recording: "ctrl+shift+e"
    pause_recording: "ctrl+shift+p"
    show_hide_window: "ctrl+shift+h"

  system_tray:
    enabled: true
    close_to_tray: true  # Close button minimizes to tray
```

### CLI Mode

**Start recording** using Python module:
```cmd
venv\Scripts\activate
python modules\cli.py start
```

Using batch script:
```cmd
scripts\run_record.bat
```

This will:
1. Connect to the RTMP stream
2. Start recording to MP4 files
3. Monitor health and handle reconnections
4. Continue until stopped with Ctrl+C

### CLI Commands

**Check status**:
```cmd
python modules\cli.py status
python modules\cli.py status --json
```

**Capture snapshot**:
```cmd
python modules\cli.py snapshot
```

Or use the batch script:
```cmd
scripts\snapshot.bat
```

**Force reconnection**:
```cmd
python modules\cli.py reconnect
```

**Update configuration**:
```cmd
python modules\cli.py set stream.url rtmp://192.168.1.100/live/cam
python modules\cli.py set recording.segment_seconds 7200 --persist
```

**Stop client**:
```cmd
python modules\cli.py stop
```

### Output Files

**Recordings**: Saved to `records/videos/` with pattern:
```
rec_20251003_120000.mp4
rec_20251003_150000.mp4
rec_20251003_180000.mp4
```

**Snapshots**: Saved to `records/snapshots/` with pattern:
```
snap_20251003_143022_123.jpg
```

**Logs**: Written to `logs/client.log` in JSON Lines format

## Project Structure

```
client_pc/
├── modules/
│   ├── stream_receiver.py   # RTMP stream reception
│   ├── recorder.py           # MP4 segment recording
│   ├── snapshotter.py        # Snapshot capture
│   ├── health.py             # Health monitoring
│   ├── cli.py                # Command-line interface
│   ├── gui_launcher.py       # GUI entry point
│   ├── config.py             # Configuration loader
│   ├── logging_json.py       # JSON logger
│   ├── utils.py              # Utility functions
│   └── gui/                  # GUI components (PyQt5)
│       ├── main_window.py    # Main application window
│       ├── video_widget.py   # Live video preview widget
│       ├── control_panel.py  # Recording controls panel
│       ├── status_bar.py     # Status bar widget
│       ├── stats_panel.py    # Statistics display
│       ├── log_viewer.py     # Log viewer widget
│       ├── settings_dialog.py # Settings configuration
│       ├── system_tray.py    # System tray icon
│       ├── hotkey_manager.py # Global hotkey handler
│       └── themes.py         # UI themes (dark/light)
├── tests/
│   ├── test_filenames.py     # Filename pattern tests
│   ├── test_backoff.py       # Backoff logic tests
│   ├── test_diskguard.py     # Disk guard tests
│   └── conftest.py           # Pytest fixtures
├── scripts/
│   ├── run_record.bat        # Start recording script
│   └── snapshot.bat          # Snapshot script
├── config.yaml               # Configuration file
└── requirements.txt          # Python dependencies
```

## Running Tests

```cmd
venv\Scripts\activate
pytest tests/ -v
pytest tests/ --cov=modules
```

Tests cover:
- Filename pattern generation
- Backoff sequence with jitter
- Disk guard pause/resume logic
- Configuration validation

## Troubleshooting

### GUI won't start
- Ensure `ui.enabled: true` in config.yaml
- Check PyQt5 is installed: `pip install PyQt5`
- Review error messages in console
- Try CLI mode to verify stream works: `python modules\cli.py start`

### GUI shows "No Video Stream"
- Click "Connect" in Stream menu or "🔌 Reconnect Stream" button
- Verify RTMP server is running: `curl http://127.0.0.1:8080`
- Check stream URL in config.yaml matches RTMP server
- Review logs in GUI log viewer for connection errors

### Global hotkeys not working
- Ensure `ui.hotkeys.enabled: true` in config.yaml
- Check for hotkey conflicts with other applications
- Run GUI as administrator (Windows may restrict global hotkeys)
- Verify hotkey syntax in config.yaml (e.g., "ctrl+shift+s")

### Stream not connecting
- Verify Nginx-RTMP server is running: `curl http://127.0.0.1:8080`
- Check RTMP URL in config.yaml
- Review logs: `type logs\client.log` or check GUI log viewer

### Recording files not created
- Check disk space: ensure > 500 MiB free (shown in GUI health monitor)
- Verify FFmpeg is installed: `ffmpeg -version`
- Check output directory exists and is writable
- Ensure recording is enabled in config.yaml

### Snapshots failing
- Ensure stream is active (video preview shows frames)
- Check snapshot directory permissions
- Review error logs for FFmpeg output

### High disk usage
- Monitor disk usage in GUI statistics panel
- Reduce segment duration in config.yaml
- Increase disk_free_floor_mib to pause recording earlier
- Set up automatic cleanup of old recordings

## Advanced Usage

### Disk Space Management

The client monitors free disk space and automatically pauses recording when it falls below `disk_free_floor_mib` (default 500 MiB). Recording resumes when free space exceeds `disk_free_resume_mib` (default 1024 MiB).

This hysteresis prevents rapid pause/resume cycles.

### Automatic Reconnection

On stream drops or network issues, the client automatically reconnects using exponential backoff:
- Attempts: 1s, 2s, 5s, 10s, 20s, 30s
- After exhausting the schedule, continues at 30s intervals
- Jitter (±10%) prevents thundering herd

### Custom Backoff Schedule

Edit `config.yaml`:
```yaml
stream:
  reconnect:
    backoff_seconds: [2, 5, 15, 30, 60]
```

## License

MIT
