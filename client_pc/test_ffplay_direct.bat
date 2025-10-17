@echo off
echo Testing FFplay with RTP stream...
echo.
echo Make sure your Raspberry Pi is streaming!
echo.
echo Starting FFplay...
echo Press Ctrl+C to stop
echo.

ffplay -protocol_whitelist file,udp,rtp -fflags nobuffer -flags low_delay -framedrop -probesize 32 -analyzeduration 0 -i udp://@:5000 -window_title "RTP Stream Test"

pause
