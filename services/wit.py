from enum import Enum
import pyaudio
import wave
import requests
import json
import threading
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

class IntentType(Enum):
    TEMPERATURE = "wit$get_temperature"
    VOLUME = "volume"
    READ_TEXT = "read_text"
    CURRENCY = "currency"
    MAPS = "maps"
    GPT = "gpt"

class WitAiClient:
    def __init__(self, wit_api_key: str, temp_dir: str = "/tmp"):
        """Initialize WitAi client with API key and temporary directory for audio files.
        
        Args:
            wit_api_key (str): Your Wit.ai API key
            temp_dir (str): Directory to store temporary audio files
        """
        self.wit_api_key = wit_api_key
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio recording settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.recording = False
        self.audio = pyaudio.PyAudio()
        
        # Recording state
        self.frames = []
        self.audio_thread = None

    def _record_audio(self, timeout: Optional[float] = None):
        """Internal method to record audio from microphone."""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        start_time = time.time()
        self.frames = []
        
        while self.recording:
            if timeout and (time.time() - start_time) > timeout:
                self.stop()
                break
                
            data = stream.read(self.chunk, exception_on_overflow=False)
            self.frames.append(data)
            
        stream.stop_stream()
        stream.close()

    def record(self, timeout: Optional[float] = None):
        """Start recording audio from microphone.
        
        Args:
            timeout (float, optional): Recording timeout in seconds
        """
        if self.recording:
            return
            
        self.recording = True
        self.audio_thread = threading.Thread(
            target=self._record_audio,
            args=(timeout,)
        )
        self.audio_thread.start()

    def stop(self) -> str:
        """Stop recording and save audio to temporary WAV file.
        
        Returns:
            str: Path to saved WAV file
        """
        if not self.recording:
            return ""
            
        self.recording = False
        if self.audio_thread:
            self.audio_thread.join()
        
        # Save recorded audio to WAV file
        temp_file = self.temp_dir / f"recording_{int(time.time())}.wav"
        with wave.open(str(temp_file), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            
        return str(temp_file)

    def process_audio(self, audio_file: str) -> Tuple[IntentType, Dict[str, Any], str]:
        """Send audio file to Wit.ai API and process the response.
        
        Args:
            audio_file (str): Path to audio file
            
        Returns:
            Tuple containing:
            - IntentType: Detected intent
            - Dict: Extracted entities and data
            - str: Transcript of the audio
        """
        headers = {
            'Authorization': f'Bearer {self.wit_api_key}',
        }
        
        with open(audio_file, 'rb') as f:
            resp = requests.post(
                'https://api.wit.ai/speech',
                headers=headers,
                data=f,
                params={'v': '20240101'}
            )
        
        if resp.status_code != 200:
            raise Exception(f"Wit.ai API error: {resp.status_code} - {resp.text}")
            
        result = resp.json()
        
        # Extract intent
        intent = None
        if 'intents' in result and result['intents']:
            intent_name = result['intents'][0]['name']
            try:
                intent = IntentType(intent_name)
            except ValueError:
                intent = None
        
        # Extract entities and other data
        data = {
            'entities': result.get('entities', {}),
            'traits': result.get('traits', {}),
        }
        
        # Get transcript
        transcript = result.get('text', '')
        
        return intent, data, transcript

    def listen_and_process(self, timeout: Optional[float] = None) -> Tuple[IntentType, Dict[str, Any], str]:
        """Record audio and process it through Wit.ai in one step.
        
        Args:
            timeout (float, optional): Recording timeout in seconds
            
        Returns:
            Tuple containing:
            - IntentType: Detected intent
            - Dict: Extracted entities and data
            - str: Transcript of the audio
        """
        self.record(timeout)
        time.sleep(0.5)  # Small delay to ensure recording starts
        
        while self.recording:
            time.sleep(0.1)  # Wait for recording to finish
            
        audio_file = self.stop()
        return self.process_audio(audio_file)

    def __del__(self):
        """Cleanup audio resources."""
        self.audio.terminate()