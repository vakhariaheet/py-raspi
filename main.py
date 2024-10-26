import RPi.GPIO as GPIO
from sensors.touch import TouchSensor, TouchType
from sensors.temperature import DHT11Sensor
from sensors.camera import CameraSensor
from services.gemini import GeminiHandler
from gtts import gTTS
from services.wit import WitAiClient,IntentType
import pygame
import os
import re
import time
from dotenv import load_dotenv


class ApplicationState:
    def __init__(self):
        self.is_recording = False


def explore_scene(gemini_key):
    try:
        CameraSensor().capture("image.jpg")
        print("Image captured")
        print(f"Gemini Key: {gemini_key}")
        gemini = GeminiHandler(api_key=gemini_key)
        gemini.generate_with_tts(
            "Describe this scene as if narrating to someone who can't see it. "
            "Be detailed but natural, avoiding any mention of an image. "
            "Use only elements present in the scene. Keep your description "
            "concise, under 100 words, while capturing the essence of what's visible.",
            image_path="image.jpg",
        )
        print("Text to speech completed")
    except Exception as e:
        print(f"Error in explore_scene: {str(e)}")

def handle_currency_intent():
    try:
        CameraSensor().capture("image.jpg")
        print("Image captured")
        gemini = GeminiHandler(api_key=os.environ.get("API_KEY"))
        gemini.generate_with_tts(
            "Analyze the image and identify the currency. Provide the name of the currency and its denomination."
            "If there are multiple currencies, provide details for each one.",
            image_path="image.jpg",
        );
        print("Text to speech completed")

    except Exception as e:
        print(f"Error handling currency intent: {str(e)}")

def handle_gpt_intent(transcript: str):
    try:
        prompt = transcript.replace(r"Hey Visio", "").strip();
        print(f"Prompt: {prompt}")
        gemini = GeminiHandler(api_key=os.environ.get("API_KEY"))
        gemini.generate_with_tts(f"Generate text based on the provided prompt. Remove any phrases like 'ask visio' or 'hey visio.' Ensure the text is concise (under 100 words unless otherwise specified). Avoid introductory phrases such as 'here is the generated text.' prompt: {prompt}")
        print("Text to speech completed");
    except Exception as e:
        print(f"Error handling GPT intent: {str(e)}")


def create_touch_handler(state, wit_client):
    def on_touch(props):
        try:
            print("Is recording: ", state.is_recording)

            if props == TouchType.SINGLE:
                print("Single touch detected")
                if state.is_recording:
                    audio_file = wit_client.stop()
                    play_sound("assets/sfx/start.mp3")
                    intent, data, transcript, result = wit_client.process_audio(
                        audio_file
                    )
                    print(f"Intent: {intent}")
                    print(f"Data: {data}")
                    print(f"Transcript: {transcript}")
                    print(f"Result: {result}")
                    state.is_recording = False
                    print("Recording stopped")
                    if intent == IntentType.GPT:
                        handle_gpt_intent(transcript)
                    elif intent == IntentType.CURRENCY:
                        handle_currency_intent();
                    elif intent == IntentType.TEMPERATURE:
                        temperature, humidity = DHT11Sensor().read_sensor()
                        gTTS(f"The temperature is {temperature} degrees Celsius and humidity is {humidity} percent", lang="en").save("output.mp3")
                        play_sound("output.mp3")
                        
                else:
                    explore_scene(os.environ.get("API_KEY"))

            elif props == TouchType.DOUBLE:
                print("Double touch detected")
                wit_client.record(timeout=10)
                state.is_recording = True
                play_sound("assets/sfx/end.mp3")

            print(f"Touch Detected {props}")

        except Exception as e:
            print(f"Error in touch handler: {str(e)}")

    return on_touch


def play_sound(sound_file):
    try:
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {str(e)}")


def initialize_system():
    try:
        load_dotenv()
        pygame.init()
        return DHT11Sensor(pin=27)
    except Exception as e:
        print(f"Error initializing system: {str(e)}")
        return None


def main():
    try:
        dht11 = initialize_system()
        if not dht11:
            print("Failed to initialize system. Exiting...")
            return

        state = ApplicationState()
        wit_client = WitAiClient(wit_api_key=os.environ.get("WIT_API_KEY"))

        touch_handler = create_touch_handler(state, wit_client)
        touch_sensor = TouchSensor(17, touch_handler)

        print("Touch sensor is ready! Press Ctrl+C to exit")
        print("Waiting for touches...")

        touch_sensor.wait_listener()

    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        GPIO.cleanup()
        pygame.quit()


if __name__ == "__main__":
    main()
