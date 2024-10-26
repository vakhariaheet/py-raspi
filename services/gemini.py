import google.generativeai as genai
from google.cloud import texttospeech
import pygame
import os
from PIL import Image
import io
import time

class GeminiHandler:
    def __init__(self, api_key, voice_language_code='en-US', voice_name='en-US-Standard-A'):
        """
        Initialize Gemini handler with TTS capabilities
        
        Args:
            api_key: Your Google API key
            voice_language_code: Language code for TTS
            voice_name: Voice name for TTS
        """
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        
        # Initialize TTS client
        self.tts_client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=voice_language_code,
            name=voice_name
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Create temp directory for audio chunks if it doesn't exist
        self.temp_dir = "temp_audio"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def _text_to_speech_chunk(self, text, chunk_index):
        """Convert text chunk to speech and save as MP3"""
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config
        )
        
        # Save the audio chunk
        chunk_path = f"{self.temp_dir}/chunk_{chunk_index}.mp3"
        with open(chunk_path, "wb") as out:
            out.write(response.audio_content)
        return chunk_path

    def _play_audio_chunk(self, chunk_path):
        """Play an audio chunk using pygame"""
        pygame.mixer.music.load(chunk_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    
    def _cleanup_chunks(self):
        """Remove temporary audio files"""
        for file in os.listdir(self.temp_dir):
            if file.endswith(".mp3"):
                os.remove(os.path.join(self.temp_dir, file))

    async def generate_with_tts(self, prompt, image_path=None):
        """
        Generate response from Gemini and stream it with real-time TTS
        
        Args:
            prompt: Text prompt for Gemini
            image_path: Optional path to image file
        """
        try:
            # Handle image if provided
            if image_path:
                img = Image.open(image_path)
                response = await self.vision_model.generate_content_async([prompt, img],stream=True)
            else:
                response = await self.model.generate_content_async(prompt, stream=True)
            
            # Process the streaming response
            chunk_index = 0
            current_chunk = ""
            
            async for chunk in response:
                if hasattr(chunk, 'text'):
                    # Split on sentence boundaries for more natural TTS
                    sentences = chunk.text.split('.')
                    for sentence in sentences:
                        if sentence.strip():
                            current_chunk += sentence.strip() + "."
                            
                            # Process chunk when it reaches a reasonable size
                            if len(current_chunk) >= 100 or sentence == sentences[-1]:
                                print(current_chunk)  # Print the text chunk
                                
                                # Convert to speech and play
                                chunk_path = self._text_to_speech_chunk(current_chunk, chunk_index)
                                self._play_audio_chunk(chunk_path)
                                
                                chunk_index += 1
                                current_chunk = ""
            
            # Clean up temporary files
            self._cleanup_chunks()
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            self._cleanup_chunks()

    def close(self):
        """Cleanup and close resources"""
        pygame.mixer.quit()
        self._cleanup_chunks()
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)