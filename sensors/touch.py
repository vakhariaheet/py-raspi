import RPi.GPIO as GPIO
import time
from enum import Enum
from threading import Timer

class TouchType(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    LONG = "long"

class TouchSensor:
    def __init__(self, pin, callback=None, bounce_time=200):
        """
        Initialize the touch sensor
        
        Args:
            pin (int): GPIO pin number (BCM numbering)
            callback (function, optional): Function to call when touch is detected
            bounce_time (int, optional): Debounce time in milliseconds
        """
        self.pin = pin
        self.callback = callback
        self.bounce_time = bounce_time
        
        # Touch detection configuration
        self.long_press_time = 1.0  # seconds
        self.double_click_time = 0.5  # seconds
        
        # State variables
        self.last_touch_time = 0
        self.touch_count = 0
        self.is_touching = False
        self.long_press_timer = None
        self.double_click_timer = None
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
    def on_touch(self, callback):
        """
        Register callback for different touch types
        
        Args:
            callback (callable): Function to call when touch is detected.
                               Should accept TouchType as parameter
        """
        self.callback = callback
    
    def _handle_touch(self, channel):
        """Internal callback handler"""
        current_time = time.time()
        
        if not self.is_touching:  # Touch started
            self.is_touching = True
            
            # Start long press timer
            self.long_press_timer = Timer(self.long_press_time, self._handle_long_press)
            self.long_press_timer.start()
            
            # Handle potential double click
            if current_time - self.last_touch_time < self.double_click_time:
                self.touch_count += 1
                if self.touch_count == 2:
                    self._handle_double_click()
            else:
                self.touch_count = 1
                
            self.last_touch_time = current_time
            
        else:  # Touch ended
            self.is_touching = False
            
            # Cancel long press timer if it's running
            if self.long_press_timer:
                self.long_press_timer.cancel()
                
            # Start timer for potential double click
            if self.touch_count == 1:
                if self.double_click_timer:
                    self.double_click_timer.cancel()
                self.double_click_timer = Timer(self.double_click_time, self._handle_single_click)
                self.double_click_timer.start()
    
    def _handle_single_click(self):
        """Handle single click event"""
        if self.callback and self.touch_count == 1:
            self.callback(TouchType.SINGLE)
        self.touch_count = 0
        
    def _handle_double_click(self):
        """Handle double click event"""
        if self.callback:
            self.callback(TouchType.DOUBLE)
        self.touch_count = 0
        if self.double_click_timer:
            self.double_click_timer.cancel()
            
    def _handle_long_press(self):
        """Handle long press event"""
        if self.callback and self.is_touching:
            self.callback(TouchType.LONG)
        self.touch_count = 0
        
    def is_touched(self):
        """
        Check if sensor is currently being touched
        
        Returns:
            bool: True if touched, False otherwise
        """
        return GPIO.input(self.pin) == GPIO.HIGH
    
    def wait_listener(self):
        """Main loop to monitor touch events"""
        while True:
            current_state = self.is_touched()
            if current_state != self.is_touching:
                self._handle_touch(self.pin)
            time.sleep(0.01)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if self.long_press_timer:
            self.long_press_timer.cancel()
        if self.double_click_timer:
            self.double_click_timer.cancel()
        GPIO.cleanup(self.pin)