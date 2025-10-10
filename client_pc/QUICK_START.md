# Quick Start Guide - Fixed Recording Issues

## ✅ What Was Fixed

1. **Enhanced error logging** - Now captures detailed FFmpeg errors
2. **Network diagnostics tool** - Test RTMP connectivity
3. **Clear logs** - Old log backed up, fresh start
4. **New CLI entry point** - Easy to run commands

---

## 🚀 Run These Commands Now

### Step 1: Test Network Connection
```powershell
cd C:\Users\moham\Downloads\Aqua\client_pc
python test_network.py
```

This will test:
- Ping to RTMP server
- Port 1935 accessibility
- RTMP stream connection

---

### Step 2: Increase Timeout (CRITICAL!)

**The Issue:** Your stream has a 10-second delay, but timeout is set to 10 seconds. This causes FFmpeg to disconnect exactly when it hits the delay.

**The Fix:**
```powershell
# Run this to increase timeout to 30 seconds
python client_cli.py set stream.read_timeout_seconds 30 --persist
```

---

### Step 3: Run Diagnostics
```powershell
# Full diagnostic test
python client_cli.py diagnose

# Or with detailed JSON output
python client_cli.py diagnose --json
```

---

### Step 4: Start Recording with New Logging
```powershell
python client_cli.py start
```

---

### Step 5: Monitor Logs (in another terminal)

**PowerShell:**
```powershell
Get-Content logs\client.log -Wait -Tail 50
```

**Command Prompt:**
```cmd
powershell Get-Content logs\client.log -Wait -Tail 50
```

---

## 📋 All Available Commands

```powershell
# Show help
python client_cli.py --help

# Start recording
python client_cli.py start

# Stop recording
python client_cli.py stop

# Check status
python client_cli.py status

# Take snapshot
python client_cli.py snapshot

# Force reconnect
python client_cli.py reconnect

# Run diagnostics
python client_cli.py diagnose

# Change settings
python client_cli.py set <key> <value> --persist
```

---

## 🔍 What to Look For

### In Network Test Results:
- ✓ **All green checks** = Network is good
- ✗ **Ping fails** = Network/IP issue
- ✗ **Port fails** = RTMP server not running
- ✗ **RTMP fails** = Stream/camera issue

### In New Logs:
Look for these detailed error entries:

**Stream Receiver Errors:**
```json
{
  "lvl": "error",
  "comp": "stream_receiver",
  "evt": "process_died",
  "ctx": {
    "stderr": "...detailed FFmpeg error..."
  }
}
```

**Recorder Errors:**
```json
{
  "lvl": "error",
  "comp": "recorder",
  "evt": "process_died",
  "ctx": {
    "error_lines": ["specific error messages"]
  }
}
```

---

## 🎯 Expected Results After Fix

Once you increase the timeout to 30 seconds:

✅ Recording should run for full 3-hour segments
✅ No more reconnections every 5-30 seconds
✅ Stream handles the 10-second delay properly
✅ Clean logs with no process_died errors

---

## 📊 Configuration File Location

The config is automatically loaded from:
```
C:\Users\moham\Downloads\Aqua\client_pc\config.yaml
```

You can also specify a different config:
```powershell
python client_cli.py --config path\to\config.yaml start
```

---

## 🆘 If Problems Persist

After running with new logging, share:

1. **Network test results:**
   ```powershell
   python test_network.py > network_test.txt
   ```

2. **Diagnostic results:**
   ```powershell
   python client_cli.py diagnose > diagnostics.txt
   ```

3. **Log entries with process_died:**
   ```powershell
   Select-String -Path logs\client.log -Pattern "process_died" | Select-Object -Last 5
   ```

The detailed error messages will show exactly why FFmpeg is disconnecting.

---

## 💡 Pro Tips

### Monitor in Real-Time
```powershell
# Open two terminals side by side:

# Terminal 1 - Run client
python client_cli.py start

# Terminal 2 - Watch logs
Get-Content logs\client.log -Wait -Tail 50
```

### Quick Network Check
```powershell
# Just ping test
ping 192.168.100.23

# Test port (PowerShell)
Test-NetConnection -ComputerName 192.168.100.23 -Port 1935
```

### Check FFmpeg is Installed
```powershell
ffmpeg -version
```

If FFmpeg is not found, install it and add to PATH.

---

## 📁 New Files Created

- `client_cli.py` - Main entry point (use this instead of `python -m modules.cli`)
- `test_network.py` - Quick network test script
- `modules/network_diagnostics.py` - Network testing library
- `TROUBLESHOOTING.md` - Detailed troubleshooting guide
- `QUICK_START.md` - This file

---

## ⚡ TL;DR - Just Do This

```powershell
# 1. Test network
python test_network.py

# 2. Fix timeout (IMPORTANT!)
python client_cli.py set stream.read_timeout_seconds 30 --persist

# 3. Start recording
python client_cli.py start

# 4. Watch logs in another window
Get-Content logs\client.log -Wait -Tail 50
```

That's it! The recording should now be stable.
