"""
Raspberry Pi health monitoring module.

Fetches and tracks health metrics from the Raspberry Pi server.
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime


class PiHealthMonitor:
    """
    Monitor Raspberry Pi health metrics.

    Fetches temperature, CPU usage, and other system metrics from the Pi's health endpoint.
    """

    def __init__(self, pi_ip: str = "192.168.100.23", logger: Optional[logging.Logger] = None):
        """
        Initialize Pi health monitor.

        Args:
            pi_ip: IP address of Raspberry Pi
            logger: Optional logger instance
        """
        self.pi_ip = pi_ip
        self.health_url = f"http://{pi_ip}/health"
        self.logger = logger or logging.getLogger(__name__)

        self.last_health_data: Optional[Dict[str, Any]] = None
        self.last_update_time: Optional[datetime] = None
        self.is_connected = False

    def fetch_health(self, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        """
        Fetch current health metrics from Raspberry Pi.

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing health metrics, or None if request failed
        """
        try:
            response = requests.get(self.health_url, timeout=timeout)
            response.raise_for_status()

            health_data = response.json()
            self.last_health_data = health_data
            self.last_update_time = datetime.now()
            self.is_connected = True

            self.logger.debug(f"Health data received: {health_data}")
            return health_data

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch health data: {e}")
            self.is_connected = False
            return None

        except ValueError as e:
            self.logger.error(f"Failed to parse health data JSON: {e}")
            self.is_connected = False
            return None

    def get_temperature(self) -> Optional[float]:
        """
        Get CPU temperature in Celsius.

        Returns:
            Temperature in Celsius, or None if not available
        """
        if not self.last_health_data:
            return None

        # Try common field names
        temp_fields = ['temperature', 'cpu_temp', 'temp_c', 'cpu_temperature']
        for field in temp_fields:
            if field in self.last_health_data:
                try:
                    return float(self.last_health_data[field])
                except (ValueError, TypeError):
                    continue

        # Check nested structure
        if 'system' in self.last_health_data:
            system = self.last_health_data['system']
            for field in temp_fields:
                if field in system:
                    try:
                        return float(system[field])
                    except (ValueError, TypeError):
                        continue

        return None

    def get_cpu_usage(self) -> Optional[float]:
        """
        Get CPU usage percentage.

        Returns:
            CPU usage as percentage (0-100), or None if not available
        """
        if not self.last_health_data:
            return None

        # Try common field names
        cpu_fields = ['cpu_usage', 'cpu_percent', 'cpu', 'cpu_usage_percent']
        for field in cpu_fields:
            if field in self.last_health_data:
                try:
                    return float(self.last_health_data[field])
                except (ValueError, TypeError):
                    continue

        # Check nested structure
        if 'system' in self.last_health_data:
            system = self.last_health_data['system']
            for field in cpu_fields:
                if field in system:
                    try:
                        return float(system[field])
                    except (ValueError, TypeError):
                        continue

        return None

    def get_memory_usage(self) -> Optional[Dict[str, float]]:
        """
        Get memory usage information.

        Returns:
            Dictionary with 'used', 'total', 'percent' keys, or None if not available
        """
        if not self.last_health_data:
            return None

        memory_data = {}

        # Check for memory field
        if 'memory' in self.last_health_data:
            mem = self.last_health_data['memory']
            if isinstance(mem, dict):
                try:
                    memory_data['used'] = float(mem.get('used', 0))
                    memory_data['total'] = float(mem.get('total', 0))
                    memory_data['percent'] = float(mem.get('percent', 0))
                    return memory_data
                except (ValueError, TypeError):
                    pass

        # Try alternative field names
        if 'mem_percent' in self.last_health_data:
            try:
                memory_data['percent'] = float(self.last_health_data['mem_percent'])
                return memory_data
            except (ValueError, TypeError):
                pass

        return None

    def get_uptime(self) -> Optional[int]:
        """
        Get system uptime in seconds.

        Returns:
            Uptime in seconds, or None if not available
        """
        if not self.last_health_data:
            return None

        uptime_fields = ['uptime', 'uptime_seconds', 'uptime_s']
        for field in uptime_fields:
            if field in self.last_health_data:
                try:
                    return int(self.last_health_data[field])
                except (ValueError, TypeError):
                    continue

        if 'system' in self.last_health_data:
            system = self.last_health_data['system']
            for field in uptime_fields:
                if field in system:
                    try:
                        return int(system[field])
                    except (ValueError, TypeError):
                        continue

        return None

    def get_disk_usage(self) -> Optional[Dict[str, float]]:
        """
        Get disk usage information.

        Returns:
            Dictionary with 'used', 'total', 'percent' keys, or None if not available
        """
        if not self.last_health_data:
            return None

        disk_data = {}

        # Check for disk field
        if 'disk' in self.last_health_data:
            disk = self.last_health_data['disk']
            if isinstance(disk, dict):
                try:
                    disk_data['used'] = float(disk.get('used', 0))
                    disk_data['total'] = float(disk.get('total', 0))
                    disk_data['percent'] = float(disk.get('percent', 0))
                    return disk_data
                except (ValueError, TypeError):
                    pass

        return None

    def get_network_info(self) -> Optional[Dict[str, Any]]:
        """
        Get network information.

        Returns:
            Dictionary with network stats, or None if not available
        """
        if not self.last_health_data:
            return None

        if 'network' in self.last_health_data:
            return self.last_health_data['network']

        return None

    def is_healthy(self) -> bool:
        """
        Check if Pi is healthy based on thresholds.

        Returns:
            True if all metrics are within healthy ranges
        """
        if not self.is_connected or not self.last_health_data:
            return False

        # Check temperature (warning if > 70°C, critical if > 80°C)
        temp = self.get_temperature()
        if temp and temp > 80:
            return False

        # Check CPU usage (warning if > 90%)
        cpu = self.get_cpu_usage()
        if cpu and cpu > 95:
            return False

        return True

    def get_health_status(self) -> str:
        """
        Get overall health status.

        Returns:
            Status string: 'healthy', 'warning', 'critical', or 'disconnected'
        """
        if not self.is_connected:
            return 'disconnected'

        temp = self.get_temperature()
        cpu = self.get_cpu_usage()

        # Critical conditions
        if temp and temp > 80:
            return 'critical'
        if cpu and cpu > 95:
            return 'critical'

        # Warning conditions
        if temp and temp > 70:
            return 'warning'
        if cpu and cpu > 90:
            return 'warning'

        return 'healthy'

    def format_uptime(self) -> str:
        """
        Format uptime as human-readable string.

        Returns:
            Formatted uptime string (e.g., "2d 3h 45m")
        """
        uptime = self.get_uptime()
        if uptime is None:
            return "N/A"

        days = uptime // 86400
        hours = (uptime % 86400) // 3600
        minutes = (uptime % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}m")

        return " ".join(parts)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all health metrics.

        Returns:
            Dictionary with all available health information
        """
        return {
            'connected': self.is_connected,
            'status': self.get_health_status(),
            'temperature': self.get_temperature(),
            'cpu_usage': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'uptime': self.get_uptime(),
            'uptime_formatted': self.format_uptime(),
            'last_update': self.last_update_time,
            'raw_data': self.last_health_data
        }
