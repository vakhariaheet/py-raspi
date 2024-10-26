import RPi.GPIO as GPIO;
from sensors.touch import TouchSensor,TouchType;
from sensors.temperature import DHT11;
import time;
dht11 = DHT11(pin=27);
def main():
    def on_touch(props):
        if TouchType.SINGLE:
            result = dht11.read();
            print(str(result));
        print(f'Touch Detected {props}');
    touch_sensor = TouchSensor(17,on_touch);
    print("Touch sensor is ready! Press Ctrl+C to exit")
    print("Waiting for touches...")

    touch_sensor.wait_listener();



if __name__ == '__main__':
    main();