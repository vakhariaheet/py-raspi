import RPi.GPIO as GPIO;
from sensors.touch import TouchSensor,TouchType;
from sensors.temperature import DHT11;
from sensors.camera import CameraSensor;
from services.gemini import GeminiHandler
from services.wit import WitAiClient;
import pygame;
import os;
import time;
from dotenv import load_dotenv;
load_dotenv();
dht11 = DHT11(pin=27);
pygame.init()
gemini_key = os.environ.get('API_KEY')

def explore_scene():
    CameraSensor().capture("image.jpg");
    print("Image captured");
    print(f"Gemini Key: {gemini_key}");
    gemini = GeminiHandler(api_key=gemini_key);
    gemini.generate_with_tts("Describe this scene as if narrating to someone who can't see it. Be detailed but natural, avoiding any mention of an image. Use only elements present in the scene. Keep your description concise, under 100 words, while capturing the essence of what's visible.",image_path="image.jpg");
    print("Text to speech completed");

def main():
    witClient = WitAiClient(wit_api_key=os.environ.get('WIT_API_KEY'));
    def on_touch(props):
        is_recording = False;
        if TouchType.SINGLE:
            if is_recording:
                audio_file = witClient.stop();
                pygame.mixer.music.load("assets/sfx/start.mp3");
                intent, data, transcript = witClient.process_audio(audio_file)
                print(f"Intent: {intent}");
                print(f"Data: {data}");
                print(f"Transcript: {transcript}");
                is_recording = False;
                print("Recording stopped");
            else:
                explore_scene();
            
            
        elif TouchType.DOUBLE:
            print("Double touch detected");
            witClient.record(timeout=10);
            pygame.mixer.music.load("assets/sfx/start.mp3");
        
        print(f'Touch Detected {props}');
    
    touch_sensor = TouchSensor(17,on_touch);
    print("Touch sensor is ready! Press Ctrl+C to exit")
    print("Waiting for touches...")
    
    touch_sensor.wait_listener();



if __name__ == '__main__':
    main();