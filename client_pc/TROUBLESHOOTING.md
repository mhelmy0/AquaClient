# Troubleshooting Guide - Recording Stops Unexpectedly

## What Changed

### 1. **Enhanced Error Logging**
- **stream_receiver.py**: Now captures detailed FFmpeg stderr/stdout when process dies
- **recorder.py**: Extracts and logs specific error messages from FFmpeg output
- **cli.py**: Monitors stream health and logs when stream receiver dies

### 2. **Network Diagnostics Tool**
New tool to test RTMP server connectivity and diagnose network issues.

### 3. **Log Management**
- Old log backed up to `logs/client.log.backup`
- Fresh log file started for cleaner debugging

---

## Quick Tests to Run

### Test 1: Network Diagnostics (Run First!)
```bash
# Using the test script
cd c:\Users\moham\Downloads\Aqua\client_pc
python test_network.py

# OR using the CLI
python -m modules.cli diagnose
```

This will test:
- ✓ Ping to server (network connectivity)
- ✓ RTMP port 1935 (server is listening)
- ✓ RTMP connection (FFmpeg can connect)

### Test 2: Manual Connection Test
```bash
# Test if you can connect to RTMP server
ping 192.168.100.23

# Check if port 1935 is open (Windows)
Test-NetConnection -ComputerName 192.168.100.23 -Port 1935
```

### Test 3: Run with Improved Logging
```bash
cd c:\Users\moham\Downloads\Aqua\client_pc
python -m modules.cli start
```

Watch for new detailed error messages in the logs:
- Stream receiver process death details
- FFmpeg error output
- Connection failure reasons

---

## Understanding the Issue

Based on the logs, the stream keeps dying every 5-30 seconds. Here's why:

### Pattern Observed:
```
1. Stream opens successfully
2. Recording starts
3. ~5 seconds later: stream_receiver process dies
4. System reconnects with backoff delay
5. Repeat cycle
```

### Possible Root Causes:

#### 1. **Network Instability** (Most Likely)
- Packet loss between PC and camera/Pi
- WiFi interference if using wireless
- Network congestion

**Solution:**
- Use wired Ethernet connection
- Check network cables
- Reduce traffic on network during recording

#### 2. **RTMP Server Issues**
- Pi RTMP server may be unstable
- Server may be disconnecting clients
- Buffer/memory issues on Pi

**Solution:**
- Check Pi logs for RTMP server errors
- Restart RTMP server on Pi
- Increase server timeout settings

#### 3. **Timeout Too Aggressive**
Current setting: `read_timeout_seconds: 10`

If stream has >10 second delays, it will disconnect.

**Solution:**
```bash
# Increase timeout to 30 seconds
python -m modules.cli set stream.read_timeout_seconds 30 --persist
```

#### 4. **Camera/Stream Issues**
- Camera may be rebooting
- Video feed interrupted
- Encoding issues

**Solution:**
- Check camera directly
- Verify camera is stable
- Test with VLC player: `vlc rtmp://192.168.100.23/live/cam`

---

## Step-by-Step Troubleshooting

### Step 1: Run Diagnostics
```bash
python test_network.py
```

Check results:
- ✗ If ping fails → Network/IP address issue
- ✗ If port fails → RTMP server not running
- ✗ If RTMP fails → Stream/camera issue

### Step 2: Check New Logs
```bash
# Start recording with new logging
python -m modules.cli start

# In another terminal, watch logs
tail -f logs/client.log
# OR on Windows
Get-Content logs/client.log -Wait -Tail 50
```

Look for:
- `"evt": "process_died"` events
- `"stderr"` field with FFmpeg errors
- Specific error messages

### Step 3: Increase Timeouts
```bash
# If seeing timeout errors
python -m modules.cli set stream.read_timeout_seconds 30 --persist
```

### Step 4: Test Stability
Let it run for 5-10 minutes and observe:
- How often it reconnects
- Time between disconnections
- Pattern of failures

---

## Key Information You Provided

> "during recording stop, streaming is live with 10 seconds delay from the server .23"

This is **CRITICAL** - it tells us:

1. **The stream is still active** when recording stops
   - Means: RTMP server is fine
   - Means: Camera is fine
   - **Problem: Client-side connection handling**

2. **10 second delay exists**
   - Current timeout: 10 seconds
   - **This is likely the issue!**
   - FFmpeg may be timing out due to delay

### Solution:
```bash
# Increase timeout to handle the 10 second delay
python -m modules.cli set stream.read_timeout_seconds 30 --persist

# Restart recording
python -m modules.cli start
```

---

## Configuration Recommendations

Edit `config.yaml`:

```yaml
stream:
  url: "rtmp://192.168.100.23/live/cam"
  read_timeout_seconds: 30  # Increase from 10 to 30
  reconnect:
    enabled: true
    backoff_seconds: [1, 2, 5, 10, 20, 30]  # Current settings
```

---

## New Commands Available

### CLI Commands
```bash
# Run diagnostics
python -m modules.cli diagnose

# Get detailed JSON output
python -m modules.cli diagnose --json

# Check status
python -m modules.cli status

# Force reconnect
python -m modules.cli reconnect
```

### Direct Network Test
```bash
# Test specific RTMP URL
cd modules
python network_diagnostics.py rtmp://192.168.100.23/live/cam
```

---

## What to Look For in New Logs

After running with improved logging, check for these entries:

### Stream Receiver Died
```json
{
  "lvl": "error",
  "comp": "stream_receiver",
  "evt": "process_died",
  "ctx": {
    "returncode": 1,
    "stderr": "...FFmpeg error details...",
    "uptime_s": 5.2
  }
}
```

### Recorder Process Died
```json
{
  "lvl": "error",
  "comp": "recorder",
  "evt": "process_died",
  "ctx": {
    "returncode": 1,
    "ffmpeg_output": "...FFmpeg error...",
    "error_lines": ["error line 1", "error line 2"]
  }
}
```

---

## Expected Results After Fix

Once timeout is increased and network is stable:

✓ Stream should run for 3-hour segments without interruption
✓ No reconnection messages
✓ Smooth recording with proper segment rotation
✓ Logs show only normal operation events

---

## Need More Help?

Share the new log output containing:
- `"evt": "process_died"` entries
- Full `"stderr"` or `"ffmpeg_output"` fields
- Results from `python test_network.py`

This will show the exact FFmpeg error causing the disconnections.
