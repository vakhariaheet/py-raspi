import RPi.GPIO as GPIO
import time

class DHT11:
    """
    DHT11 Temperature and Humidity Sensor class for Raspberry Pi
    """
    
    def __init__(self, pin):
        """
        Initialize the DHT11 sensor
        
        Args:
            pin (int): GPIO pin number (BCM numbering)
        """
        self.pin = pin
        self._last_read = 0
        self._last_temp = 0
        self._last_humidity = 0
        self._MIN_READ_INTERVAL = 2  # DHT11 needs 2 seconds between reads
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
    
    def _read_raw_data(self):
        """
        Read raw data from DHT11 sensor
        
        Returns:
            list: 40 bits of data if successful, None if failed
        """
        # Send initial signal
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(self.pin, GPIO.HIGH)
        
        # Switch to input mode
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Collect data
        raw_data = []
        data_counter = 0
        last_state = GPIO.HIGH
        counter = 0
        
        for i in range(10000):  # Timeout after 100ms
            current_state = GPIO.input(self.pin)
            
            if counter > 100:
                break
                
            if last_state != current_state:
                last_state = current_state
                counter = 0
            else:
                counter += 1
                
            if counter == 4:  # State held long enough to be valid
                raw_data.append(counter)
                data_counter += 1
                counter = 0
                
            if data_counter >= 40:  # We have all the bits we need
                break
        
        if len(raw_data) < 40:
            return None
            
        return raw_data
    
    def _calculate_values(self, raw_data):
        """
        Calculate temperature and humidity from raw data
        
        Args:
            raw_data (list): 40 bits of raw data from sensor
            
        Returns:
            tuple: (humidity, temperature) or None if checksum fails
        """
        # Convert raw timing data to bits
        bits = []
        for timing in raw_data:
            if timing > 7:  # Long pulse = 1, short pulse = 0
                bits.append(1)
            else:
                bits.append(0)
        
        # Convert bits to bytes
        bytes_data = []
        for i in range(0, 40, 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            bytes_data.append(byte)
        
        # Verify checksum
        checksum = bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]
        checksum = checksum & 0xFF
        
        if checksum != bytes_data[4]:
            return None
            
        humidity = bytes_data[0]
        temperature = bytes_data[2]
        
        return humidity, temperature
    
    def read(self, retries=3):
        """
        Read temperature and humidity from the sensor
        
        Args:
            retries (int): Number of times to retry if reading fails
            
        Returns:
            tuple: (humidity, temperature) or None if all retries fail
            
        Raises:
            TimeoutError: If called too soon after last reading
        """
        current_time = time.time()
        
        # Check if enough time has passed since last reading
        if current_time - self._last_read < self._MIN_READ_INTERVAL:
            remaining = self._MIN_READ_INTERVAL - (current_time - self._last_read)
            raise TimeoutError(
                f"Sensor needs {remaining:.1f} more seconds before next reading"
            )
        
        # Try to read the sensor
        for _ in range(retries):
            raw_data = self._read_raw_data()
            if raw_data:
                result = self._calculate_values(raw_data)
                if result:
                    self._last_read = current_time
                    self._last_humidity, self._last_temp = result
                    return result
            time.sleep(0.1)
        
        # Return last valid reading if all retries fail
        if self._last_temp:
            return self._last_humidity, self._last_temp
            
        return None
    
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup(self.pin)