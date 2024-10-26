import google.generativeai as genai
from gtts import gTTS
import pygame
import os
from PIL import Image
import time
import tempfile
import re

 

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
    
    def _clean_and_split_text(self, text):
        """
        Clean and split text into natural sentences, handling periods in abbreviations
        and numbers properly.
        """
        # Remove any standalone periods
        text = re.sub(r'\s*\.\s*', '. ', text)
        
        # Fix common abbreviations (add more as needed)
        common_abbrev = r'(?<!Mr)(?<!Mrs)(?<!Dr)(?<!Ph\.D)(?<!Sr)(?<!Jr)(?<!\s[A-Z])(?<!\d)'
        
        # Split on periods followed by space and capital letter or new sentence starters
        sentences = re.split(f'{common_abbrev}\\.\s+(?=[A-Z]|["\']|[0-9]|I\s)', text)
        
        # Clean up each sentence
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Add period if it's missing
                if not sentence.endswith(('.', '!', '?')):
                    sentence += '.'
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences

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
            buffer = ""
            
            for chunk in response:
                if hasattr(chunk, 'text'):
                    buffer += chunk.text
                    
                    # Once we have enough text, process it into natural sentences
                    if len(buffer) >= 150 or chunk.text.endswith(('.', '!', '?')):
                        sentences = self._clean_and_split_text(buffer)
                        
                        for sentence in sentences:
                            if sentence.strip():
                                print(sentence)  # Print the clean sentence
                                chunk_path = self._text_to_speech_chunk(sentence, chunk_index)
                                self._play_audio_chunk(chunk_path)
                                chunk_index += 1
                        
                        buffer = ""  # Clear the buffer after processing
            
            # Process any remaining text in the buffer
            if buffer.strip():
                sentences = self._clean_and_split_text(buffer)
                for sentence in sentences:
                    if sentence.strip():
                        print(sentence)
                        chunk_path = self._text_to_speech_chunk(sentence, chunk_index)
                        self._play_audio_chunk(chunk_path)
                        chunk_index += 1
            
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