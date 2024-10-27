import serial
import time
from datetime import datetime
from typing import Optional, Tuple, Dict
import pynmea2

class GPSReader:
    """
    A class to handle reading and parsing GPS data from a GPS module
    using NMEA sentences over serial connection.
    """
    
    def __init__(self, port: str = '/dev/ttyUSB0', baud_rate: int = 9600, timeout: float = 1.0):
        """
        Initialize GPS reader with serial connection parameters.
        
        Args:
            port (str): Serial port where GPS module is connected
            baud_rate (int): Baud rate for serial communication
            timeout (float): Serial reading timeout in seconds
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn = None
        self.last_read_time = 0
        self.min_read_interval = 1.0  # Minimum time between reads in seconds

    def connect(self) -> bool:
        """
        Establish connection to the GPS module.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            return True
        except serial.SerialException as e:
            print(f"Error connecting to GPS module: {e}")
            return False

    def disconnect(self):
        """Close the serial connection to GPS module."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def _parse_gps_data(self, nmea_sentence: str) -> Optional[Dict]:
        """
        Parse NMEA sentence to extract GPS data.
        
        Args:
            nmea_sentence (str): Raw NMEA sentence from GPS module
            
        Returns:
            Optional[Dict]: Dictionary containing parsed GPS data or None if parsing fails
        """
        try:
            msg = pynmea2.parse(nmea_sentence)
            if isinstance(msg, pynmea2.GGA):
                return {
                    'timestamp': datetime.now().isoformat(),
                    'latitude': msg.latitude,
                    'longitude': msg.longitude,
                    'altitude': msg.altitude,
                    'satellites': msg.num_sats,
                    'quality': msg.gps_qual,
                }
            return None
        except pynmea2.ParseError:
            return None

    def read_gps_data(self, force: bool = False) -> Optional[Dict]:
        """
        Read and parse GPS data from the module.
        
        Args:
            force (bool): If True, ignore minimum read interval
            
        Returns:
            Optional[Dict]: Dictionary containing GPS data or None if read fails
        """
        current_time = time.time()
        
        # Check if enough time has passed since last read
        if not force and (current_time - self.last_read_time) < self.min_read_interval:
            return None

        if not self.serial_conn or not self.serial_conn.is_open:
            if not self.connect():
                return None

        try:
            # Read lines until we get a GGA sentence
            for _ in range(100):  # Limit attempts to prevent infinite loop
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('ascii', errors='replace').strip()
                    if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                        gps_data = self._parse_gps_data(line)
                        if gps_data:
                            self.last_read_time = current_time
                            return gps_data
            return None
            
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"Error reading GPS data: {e}")
            self.disconnect()
            return None

    def get_location(self) -> Optional[Tuple[float, float]]:
        """
        Get current latitude and longitude.
        
        Returns:
            Optional[Tuple[float, float]]: Tuple of (latitude, longitude) or None if unavailable
        """
        gps_data = self.read_gps_data()
        if gps_data:
            return (gps_data['latitude'], gps_data['longitude'])
        return None

    def wait_for_fix(self, timeout: float = 60.0) -> bool:
        """
        Wait for GPS to acquire fix.
        
        Args:
            timeout (float): Maximum time to wait in seconds
            
        Returns:
            bool: True if fix acquired, False if timeout occurred
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            gps_data = self.read_gps_data(force=True)
            if gps_data and gps_data['quality'] > 0:
                return True
            time.sleep(0.5)
        return False