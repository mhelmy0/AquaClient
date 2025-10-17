"""
RTP stream receiver with SDP support.

Handles RTP video stream reception from Raspberry Pi using GStreamer/FFmpeg.
"""

import subprocess
import logging
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from threading import Thread, Event


class SDPParser:
    """Parse SDP session description protocol files."""

    @staticmethod
    def parse(sdp_content: str) -> Dict[str, Any]:
        """
        Parse SDP content and extract stream parameters.

        Args:
            sdp_content: SDP file content as string

        Returns:
            Dictionary containing parsed parameters
        """
        params = {
            'session_name': '',
            'connection_address': '',
            'media_type': '',
            'port': 0,
            'protocol': '',
            'payload_type': 0,
            'codec': '',
            'clock_rate': 0,
            'encoding_params': {}
        }

        lines = sdp_content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('s='):
                # Session name
                params['session_name'] = line[2:].strip()

            elif line.startswith('c='):
                # Connection information: c=IN IP4 0.0.0.0
                parts = line[2:].split()
                if len(parts) >= 3:
                    params['connection_address'] = parts[2]

            elif line.startswith('m='):
                # Media description: m=video 5000 RTP/AVP 96
                parts = line[2:].split()
                if len(parts) >= 4:
                    params['media_type'] = parts[0]
                    params['port'] = int(parts[1])
                    params['protocol'] = parts[2]
                    params['payload_type'] = int(parts[3])

            elif line.startswith('a=rtpmap:'):
                # RTP map: a=rtpmap:96 H264/90000
                parts = line[9:].split()
                if len(parts) >= 2:
                    payload_and_codec = parts[0].split()
                    codec_parts = parts[1].split('/')
                    if len(codec_parts) >= 2:
                        params['codec'] = codec_parts[0]
                        params['clock_rate'] = int(codec_parts[1])

            elif line.startswith('a=fmtp:'):
                # Format parameters: a=fmtp:96 packetization-mode=1
                parts = line[7:].split(None, 1)
                if len(parts) >= 2:
                    fmtp_params = parts[1].split(';')
                    for param in fmtp_params:
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params['encoding_params'][key.strip()] = value.strip()

        return params


class RTPReceiver:
    """
    RTP stream receiver with automatic SDP discovery.

    Connects to RTP stream and provides frames for display and recording.
    """

    def __init__(self, server_ip: str = "192.168.100.23", logger: Optional[logging.Logger] = None):
        """
        Initialize RTP receiver.

        Args:
            server_ip: IP address of Raspberry Pi streaming server
            logger: Optional logger instance
        """
        self.server_ip = server_ip
        self.logger = logger or logging.getLogger(__name__)

        self.sdp_params: Optional[Dict[str, Any]] = None
        self.is_running = False
        self.stop_event = Event()

        # Process handle
        self.process: Optional[subprocess.Popen] = None

    def fetch_sdp(self, sdp_url: Optional[str] = None) -> bool:
        """
        Fetch SDP description from server.

        Args:
            sdp_url: Optional custom SDP URL. If None, uses default server endpoint

        Returns:
            True if SDP was successfully fetched and parsed
        """
        if sdp_url is None:
            sdp_url = f"http://{self.server_ip}/stream.sdp"

        try:
            self.logger.info(f"Fetching SDP from {sdp_url}")
            response = requests.get(sdp_url, timeout=5)
            response.raise_for_status()

            sdp_content = response.text
            self.logger.debug(f"SDP content:\n{sdp_content}")

            # Parse SDP
            self.sdp_params = SDPParser.parse(sdp_content)
            self.logger.info(f"SDP parsed: {self.sdp_params}")

            return True

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch SDP: {e}")
            return False

    def use_manual_sdp(self, sdp_content: str) -> bool:
        """
        Use manually provided SDP content.

        Args:
            sdp_content: SDP file content as string

        Returns:
            True if SDP was successfully parsed
        """
        try:
            self.sdp_params = SDPParser.parse(sdp_content)
            self.logger.info(f"Manual SDP parsed: {self.sdp_params}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to parse manual SDP: {e}")
            return False

    def get_stream_url(self) -> Optional[str]:
        """
        Get FFmpeg-compatible stream URL from SDP parameters.

        Returns:
            Stream URL string or None if SDP not available
        """
        if not self.sdp_params:
            return None

        # For H264 over RTP, we can use UDP directly with FFmpeg
        port = self.sdp_params.get('port', 5000)

        # FFmpeg can accept RTP streams via UDP
        return f"udp://@:{port}"

    def save_sdp_file(self, filepath: str) -> bool:
        """
        Save current SDP parameters to file for FFmpeg.

        Args:
            filepath: Path to save SDP file

        Returns:
            True if file was saved successfully
        """
        if not self.sdp_params:
            self.logger.error("No SDP parameters available")
            return False

        try:
            # Reconstruct SDP file
            sdp_content = self._build_sdp_content()

            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(sdp_content)

            self.logger.info(f"SDP file saved to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save SDP file: {e}")
            return False

    def _build_sdp_content(self) -> str:
        """
        Build SDP file content from parsed parameters.

        Returns:
            SDP file content as string
        """
        params = self.sdp_params

        sdp_lines = [
            "v=0",
            f"o=- 0 0 IN IP4 {self.server_ip}",
            f"s={params.get('session_name', 'RTP Stream')}",
            f"c=IN IP4 {params.get('connection_address', '0.0.0.0')}",
            "t=0 0",
            f"m={params.get('media_type', 'video')} {params.get('port', 5000)} {params.get('protocol', 'RTP/AVP')} {params.get('payload_type', 96)}",
            f"a=rtpmap:{params.get('payload_type', 96)} {params.get('codec', 'H264')}/{params.get('clock_rate', 90000)}"
        ]

        # Add format parameters
        encoding_params = params.get('encoding_params', {})
        if encoding_params:
            fmtp_parts = [f"{k}={v}" for k, v in encoding_params.items()]
            fmtp_line = f"a=fmtp:{params.get('payload_type', 96)} {';'.join(fmtp_parts)}"
            sdp_lines.append(fmtp_line)

        return '\n'.join(sdp_lines) + '\n'

    def get_ffmpeg_command(self, output_url: str, sdp_file: Optional[str] = None) -> list:
        """
        Generate FFmpeg command for receiving RTP stream.

        Args:
            output_url: Output URL/file for FFmpeg
            sdp_file: Optional path to SDP file. If None, uses UDP directly

        Returns:
            FFmpeg command as list of arguments
        """
        if sdp_file:
            # Use SDP file
            cmd = [
                'ffmpeg',
                '-protocol_whitelist', 'file,udp,rtp',
                '-i', sdp_file,
                '-c:v', 'copy',
                '-f', 'mp4',
                '-movflags', 'frag_keyframe+empty_moov',
                output_url
            ]
        else:
            # Use UDP directly
            stream_url = self.get_stream_url()
            if not stream_url:
                raise ValueError("No SDP parameters available")

            cmd = [
                'ffmpeg',
                '-protocol_whitelist', 'udp,rtp',
                '-i', stream_url,
                '-c:v', 'copy',
                '-f', 'mp4',
                '-movflags', 'frag_keyframe+empty_moov',
                output_url
            ]

        return cmd

    def get_gstreamer_pipeline(self) -> Optional[str]:
        """
        Generate GStreamer pipeline for receiving RTP stream.

        Returns:
            GStreamer pipeline string or None if SDP not available
        """
        if not self.sdp_params:
            return None

        port = self.sdp_params.get('port', 5000)

        # GStreamer pipeline for H264 RTP reception
        pipeline = (
            f"udpsrc port={port} "
            f"caps=\"application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)96\" ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
        )

        return pipeline

    def start(self, auto_fetch_sdp: bool = True) -> bool:
        """
        Start RTP receiver.

        Args:
            auto_fetch_sdp: If True, automatically fetch SDP from server

        Returns:
            True if receiver started successfully
        """
        if auto_fetch_sdp and not self.sdp_params:
            if not self.fetch_sdp():
                self.logger.error("Failed to fetch SDP, cannot start receiver")
                return False

        if not self.sdp_params:
            self.logger.error("No SDP parameters available")
            return False

        self.is_running = True
        self.stop_event.clear()
        self.logger.info("RTP receiver started")
        return True

    def stop(self) -> None:
        """Stop RTP receiver."""
        self.is_running = False
        self.stop_event.set()

        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        self.logger.info("RTP receiver stopped")

    def get_info(self) -> Dict[str, Any]:
        """
        Get receiver information.

        Returns:
            Dictionary with receiver status and parameters
        """
        return {
            'running': self.is_running,
            'server_ip': self.server_ip,
            'sdp_params': self.sdp_params,
            'stream_url': self.get_stream_url()
        }
