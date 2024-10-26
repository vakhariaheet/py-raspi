import google.generativeai as genai
from gtts import gTTS
import pygame
import os
from PIL import Image
import time
import tempfile

class GeminiHandler:
    def __init__(self, api_key, language='en'):
        """
        Initialize Gemini handler with gTTS capabilities
        
        Args:
            api_key: Your Google API key for Gemini
            language: Language code for TTS (default: 'en')
        """
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # TTS settings
        self.language = language
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Create temp directory for audio chunks
        self.temp_dir = tempfile.mkdtemp()
    
    def _text_to_speech_chunk(self, text, chunk_index):
        """Convert text chunk to speech using gTTS and save as MP3"""
        if not text.strip():
            return None
            
        chunk_path = os.path.join(self.temp_dir, f"chunk_{chunk_index}.mp3")
        try:
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(chunk_path)
            return chunk_path
        except Exception as e:
            print(f"TTS error: {str(e)}")
            return None

    def _play_audio_chunk(self, chunk_path):
        """Play an audio chunk using pygame"""
        if chunk_path and os.path.exists(chunk_path):
            try:
                pygame.mixer.music.load(chunk_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Playback error: {str(e)}")

    def _cleanup_chunks(self):
        """Remove temporary audio files"""
        for file in os.listdir(self.temp_dir):
            if file.endswith(".mp3"):
                try:
                    os.remove(os.path.join(self.temp_dir, file))
                except Exception:
                    pass

    def generate_with_tts(self, prompt, image_path=None):
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
                response = self.vision_model.generate_content([prompt, img],stream=True)
            else:
                response = self.model.generate_content(prompt,stream=True)
            
            chunk_index = 0
            current_chunk = ""
            
            for chunk in response:
                if hasattr(chunk, 'text'):
                    # Split on sentence boundaries
                    sentences = chunk.text.split('.')
                    for sentence in sentences:
                        if sentence.strip():
                            current_chunk += sentence.strip() + "."
                            
                            # Process chunk when it reaches a reasonable size or is the last sentence
                            if len(current_chunk) >= 100 or sentence == sentences[-1]:
                                print(current_chunk)  # Print the text chunk
                                
                                # Convert to speech and play
                                chunk_path = self._text_to_speech_chunk(current_chunk, chunk_index)
                                self._play_audio_chunk(chunk_path)
                                
                                chunk_index += 1
                                current_chunk = ""
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            self._cleanup_chunks()

    def close(self):
        """Cleanup and close resources"""
        pygame.mixer.quit()
        self._cleanup_chunks()
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass