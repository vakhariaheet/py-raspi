import time
import board
import adafruit_dht

class DHT11Sensor:
    """
    A class to handle DHT11 temperature and humidity sensor readings using Adafruit library
    """
    
    def __init__(self, pin=board.D27):
        """
        Initialize the DHT11 sensor
        
        Args:
            pin: Digital pin where the sensor is connected (default: board.D4)
        """
        self.dht_device = adafruit_dht.DHT11(pin)
        self.temperature = None
        self.humidity = None
        self.last_reading_time = 0
        self.min_interval = 2  # Minimum time (seconds) between readings
        
    def read_sensor(self):
        """
        Read temperature and humidity from the sensor
        
        Returns:
            tuple: (temperature, humidity) if successful, (None, None) if failed
        """
        # Check if enough time has passed since last reading
        current_time = time.time()
        if current_time - self.last_reading_time < self.min_interval:
            return self.temperature, self.humidity
            
        try:
            # Read temperature and humidity
            self.temperature = self.dht_device.temperature
            self.humidity = self.dht_device.humidity
            self.last_reading_time = current_time
            return self.temperature, self.humidity
            
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(f"Error reading sensor: {error.args[0]}")
            return None, None
            
        except Exception as error:
            # Other errors are handled here
            self.dht_device.exit()
            raise error
    
    def get_temperature(self):
        """
        Get the temperature in Celsius
        
        Returns:
            float: Temperature in Celsius or None if reading failed
        """
        temp, _ = self.read_sensor()
        return temp
    
    def get_humidity(self):
        """
        Get the relative humidity percentage
        
        Returns:
            float: Relative humidity percentage or None if reading failed
        """
        _, humidity = self.read_sensor()
        return humidity
    
    def get_fahrenheit(self):
        """
        Get the temperature in Fahrenheit
        
        Returns:
            float: Temperature in Fahrenheit or None if reading failed
        """
        temp = self.get_temperature()
        if temp is not None:
            return (temp * 9/5) + 32
        return None
    
    def __del__(self):
        """
        Clean up resources when object is deleted
        """
        self.dht_device.exit()