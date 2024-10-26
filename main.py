import RPi.GPIO as GPIO;
from sensors.touch import TouchSensor,TouchType;
from sensors.temperature import DHT11;
from sensors.camera import CameraSensor;
from services.gemini import GeminiHandler
import pygame;
import os;
import time;
dht11 = DHT11(pin=27);
pygame.init()
def main():
    def on_touch(props):
        if TouchType.SINGLE:
            result = dht11.read();
            print(str(result));
            CameraSensor().capture("image.jpg");
            print("Image captured");
            gemini = GeminiHandler(api_key=os.getenv('API_KEY'));
            gemini.generate_with_tts("Describe this scene as if narrating to someone who can't see it. Be detailed but natural, avoiding any mention of an image. Use only elements present in the scene. Keep your description concise, under 100 words, while capturing the essence of what's visible.",image_path="image.jpg");
            print("Text to speech completed");
        print(f'Touch Detected {props}');
    
    touch_sensor = TouchSensor(17,on_touch);
    print("Touch sensor is ready! Press Ctrl+C to exit")
    print("Waiting for touches...")
    
    touch_sensor.wait_listener();



if __name__ == '__main__':
    main();