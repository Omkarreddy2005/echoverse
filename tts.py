import pyttsx3
import os
import threading
import time
from pathlib import Path

class TTSEngine:
    def __init__(self):
        """Initialize TTS engine with optimal settings"""
        self.engine = None
        self.lock = threading.Lock()
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the TTS engine with error handling"""
        try:
            self.engine = pyttsx3.init()
            self._configure_engine()
        except Exception as e:
            print(f"[TTS Init Error] Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _configure_engine(self):
        """Configure engine with optimal settings"""
        if not self.engine:
            return
            
        try:
            # Get available voices
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voice if available, otherwise use first voice
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set optimal properties
            self.engine.setProperty('rate', 180)  # Slightly faster for better flow
            self.engine.setProperty('volume', 0.9)  # Slightly lower to avoid distortion
            
        except Exception as e:
            print(f"[TTS Config Warning] Could not configure engine: {e}")
    
    def get_available_voices(self):
        """Get list of available voices"""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [(voice.id, voice.name) for voice in voices] if voices else []
        except Exception as e:
            print(f"[TTS Error] Could not get voices: {e}")
            return []
    
    def set_voice(self, voice_id):
        """Set specific voice by ID"""
        if not self.engine:
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            return True
        except Exception as e:
            print(f"[TTS Error] Could not set voice: {e}")
            return False
    
    def set_speech_rate(self, rate):
        """Set speech rate (words per minute)"""
        if not self.engine:
            return False
        
        try:
            # Clamp rate between reasonable bounds
            rate = max(50, min(300, rate))
            self.engine.setProperty('rate', rate)
            return True
        except Exception as e:
            print(f"[TTS Error] Could not set speech rate: {e}")
            return False

# Global TTS engine instance
_tts_engine = TTSEngine()

def generate_audio(text, output_path="output.wav", speech_rate=180, voice_id=None):
    """
    Generate audio from text with improved error handling and features
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Output file path
        speech_rate (int): Speech rate in words per minute (50-300)
        voice_id (str): Specific voice ID to use
    
    Returns:
        str or None: Path to generated audio file or None if failed
    """
    if not text or not text.strip():
        print("[TTS Error] Empty text provided")
        return None
    
    if not _tts_engine.engine:
        print("[TTS Error] TTS engine not initialized")
        return None
    
    # Use thread lock to prevent concurrent access issues
    with _tts_engine.lock:
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set custom voice if provided
            original_voice = None
            if voice_id:
                try:
                    original_voice = _tts_engine.engine.getProperty('voice')
                    _tts_engine.set_voice(voice_id)
                except Exception as e:
                    print(f"[TTS Warning] Could not set custom voice: {e}")
            
            # Set custom speech rate if provided
            original_rate = None
            if speech_rate != 180:
                try:
                    original_rate = _tts_engine.engine.getProperty('rate')
                    _tts_engine.set_speech_rate(speech_rate)
                except Exception as e:
                    print(f"[TTS Warning] Could not set custom speech rate: {e}")
            
            # Clean text for better pronunciation
            cleaned_text = _clean_text(text)
            
            # Generate audio
            _tts_engine.engine.save_to_file(cleaned_text, output_path)
            _tts_engine.engine.runAndWait()
            
            # Restore original settings
            if original_voice:
                _tts_engine.engine.setProperty('voice', original_voice)
            if original_rate:
                _tts_engine.engine.setProperty('rate', original_rate)
            
            # Verify file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[TTS Success] Audio generated: {output_path}")
                return output_path
            else:
                print("[TTS Error] Audio file was not created or is empty")
                return None
                
        except Exception as e:
            print(f"[TTS Error] Failed to generate audio: {e}")
            return None

def _clean_text(text):
    """Clean text for better TTS pronunciation"""
    # Remove or replace problematic characters
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = text.replace('\t', ' ')
    
    # Replace multiple spaces with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text

def speak_text(text, speech_rate=180, voice_id=None):
    """
    Speak text immediately without saving to file
    
    Args:
        text (str): Text to speak
        speech_rate (int): Speech rate in words per minute
        voice_id (str): Specific voice ID to use
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not text or not text.strip():
        print("[TTS Error] Empty text provided")
        return False
    
    if not _tts_engine.engine:
        print("[TTS Error] TTS engine not initialized")
        return False
    
    with _tts_engine.lock:
        try:
            # Set custom voice if provided
            original_voice = None
            if voice_id:
                original_voice = _tts_engine.engine.getProperty('voice')
                _tts_engine.set_voice(voice_id)
            
            # Set custom speech rate if provided
            original_rate = None
            if speech_rate != 180:
                original_rate = _tts_engine.engine.getProperty('rate')
                _tts_engine.set_speech_rate(speech_rate)
            
            # Clean and speak text
            cleaned_text = _clean_text(text)
            _tts_engine.engine.say(cleaned_text)
            _tts_engine.engine.runAndWait()
            
            # Restore original settings
            if original_voice:
                _tts_engine.engine.setProperty('voice', original_voice)
            if original_rate:
                _tts_engine.engine.setProperty('rate', original_rate)
            
            return True
            
        except Exception as e:
            print(f"[TTS Error] Failed to speak text: {e}")
            return False

def get_available_voices():
    """Get list of available TTS voices"""
    return _tts_engine.get_available_voices()

def test_tts():
    """Test TTS functionality"""
    print("Testing TTS functionality...")
    
    # Test available voices
    voices = get_available_voices()
    print(f"Available voices: {len(voices)}")
    for voice_id, voice_name in voices[:3]:  # Show first 3
        print(f"  - {voice_name} ({voice_id})")
    
    # Test speech
    test_text = "Hello! This is a test of the improved text to speech system."
    success = speak_text(test_text)
    print(f"Speech test: {'Success' if success else 'Failed'}")
    
    # Test file generation
    test_file = "test_audio.wav"
    result = generate_audio(test_text, test_file)
    print(f"File generation test: {'Success' if result else 'Failed'}")
    
    if result and os.path.exists(test_file):
        print(f"Test file created: {test_file}")

if __name__ == "__main__":
    test_tts()
