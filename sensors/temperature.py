import time
import RPi.GPIO as GPIO
import adafruit_dht


class DHT11Sensor:
    """
    A class to handle DHT11 temperature and humidity sensor readings using Adafruit library
    """
    
    def __init__(self, pin=27):  # Default to GPIO 27
        """
        Initialize the DHT11 sensor
        
        Args:
            pin: GPIO pin number where the sensor is connected (default: 4)
        """
        self.pin = pin
        self.sensor = Adafruit_DHT.DHT11
        self.temperature = None
        self.humidity = None
        self.last_reading_time = 0
        self.min_interval = 2  # Minimum time (seconds) between readings
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers
        GPIO.setup(self.pin, GPIO.IN)
        
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
            self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            self.last_reading_time = current_time
            
            if self.humidity is not None and self.temperature is not None:
                return self.temperature, self.humidity
            else:
                print("Failed to get reading. Try again!")
                return None, None
                
        except Exception as error:
            print(f"Error reading sensor: {str(error)}")
            return None, None
    
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
    
    def cleanup(self):
        """
        Clean up GPIO resources
        """
        GPIO.cleanup()
    
    def __del__(self):
        """
        Clean up resources when object is deleted
        """
        self.cleanup()