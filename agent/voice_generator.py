"""
Voice Generator
Converts script text to natural-sounding AI voiceover.
"""

import os
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
from .config import get_config


class VoiceGenerator:
    """Generates AI voiceover from script text."""
    
    # Language/accent options for gTTS
    VOICE_OPTIONS = {
        "male_us": {"lang": "en", "tld": "com"},
        "male_uk": {"lang": "en", "tld": "co.uk"},
        "male_au": {"lang": "en", "tld": "com.au"},
        "female_us": {"lang": "en", "tld": "com"},
        "female_uk": {"lang": "en", "tld": "co.uk"},
    }
    
    def __init__(self):
        """Initialize the voice generator."""
        self.config = get_config()
        self.temp_path = self.config.temp_path
    
    def generate_voice(self, script: str, output_filename: str = None) -> dict:
        """
        Generate voiceover audio from script text.
        
        Args:
            script: The text to convert to speech
            output_filename: Optional custom filename (without extension)
            
        Returns:
            Dictionary with audio path, duration, and metadata
        """
        if output_filename is None:
            output_filename = f"voiceover_{os.urandom(4).hex()}"
        
        # Use ElevenLabs if API key is available, otherwise gTTS
        if self.config.elevenlabs_api_key:
            return self._generate_elevenlabs(script, output_filename)
        else:
            return self._generate_gtts(script, output_filename)
    
    def _generate_gtts(self, script: str, output_filename: str) -> dict:
        """Generate voice using Google Text-to-Speech (free)."""
        try:
            # Get voice settings
            voice_key = f"{self.config.voice_gender}_us"
            voice_config = self.VOICE_OPTIONS.get(voice_key, self.VOICE_OPTIONS["male_us"])
            
            # Generate speech
            print(f"🎙️ Generating voiceover with gTTS...")
            tts = gTTS(
                text=script,
                lang=voice_config["lang"],
                tld=voice_config["tld"],
                slow=False
            )
            
            # Save initial MP3
            temp_mp3 = self.temp_path / f"{output_filename}_raw.mp3"
            tts.save(str(temp_mp3))
            
            # Process audio (adjust speed, normalize)
            audio = AudioSegment.from_mp3(str(temp_mp3))
            
            # Adjust speed if needed
            if self.config.voice_speed != 1.0:
                audio = self._change_speed(audio, self.config.voice_speed)
            
            # Normalize audio levels
            audio = self._normalize_audio(audio)
            
            # Export final audio
            final_path = self.temp_path / f"{output_filename}.mp3"
            audio.export(str(final_path), format="mp3", bitrate="192k")
            
            # Get duration
            duration = len(audio) / 1000.0  # Convert ms to seconds
            
            # Clean up temp file
            temp_mp3.unlink(missing_ok=True)
            
            print(f"✅ Voiceover generated: {duration:.1f} seconds")
            
            return {
                "audio_path": str(final_path),
                "duration": duration,
                "engine": "gtts",
                "voice": voice_key,
                "word_count": len(script.split())
            }
            
        except Exception as e:
            print(f"❌ Voice generation error: {e}")
            raise
    
    def _generate_elevenlabs(self, script: str, output_filename: str) -> dict:
        """Generate voice using ElevenLabs (premium quality)."""
        try:
            import requests
            
            print(f"🎙️ Generating voiceover with ElevenLabs...")
            
            # ElevenLabs voice IDs
            voice_ids = {
                "male": "pNInz6obpgDQGcFmaJgB",  # Adam
                "female": "EXAVITQu4vr4xnSDxMaL"  # Bella
            }
            
            voice_id = voice_ids.get(self.config.voice_gender, voice_ids["male"])
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.config.elevenlabs_api_key
            }
            
            data = {
                "text": script,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Save audio
            final_path = self.temp_path / f"{output_filename}.mp3"
            with open(final_path, "wb") as f:
                f.write(response.content)
            
            # Get duration
            audio = AudioSegment.from_mp3(str(final_path))
            duration = len(audio) / 1000.0
            
            print(f"✅ Voiceover generated: {duration:.1f} seconds")
            
            return {
                "audio_path": str(final_path),
                "duration": duration,
                "engine": "elevenlabs",
                "voice": self.config.voice_gender,
                "word_count": len(script.split())
            }
            
        except Exception as e:
            print(f"⚠️ ElevenLabs failed, falling back to gTTS: {e}")
            return self._generate_gtts(script, output_filename)
    
    def _change_speed(self, audio: AudioSegment, speed: float) -> AudioSegment:
        """Change the playback speed of audio."""
        if speed == 1.0:
            return audio
        
        # Change speed by altering the frame rate
        new_frame_rate = int(audio.frame_rate * speed)
        return audio._spawn(audio.raw_data, overrides={
            "frame_rate": new_frame_rate
        }).set_frame_rate(audio.frame_rate)
    
    def _normalize_audio(self, audio: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
        """Normalize audio to a target volume level."""
        change_in_dbfs = target_dbfs - audio.dBFS
        return audio.apply_gain(change_in_dbfs)
    
    def get_word_timings(self, script: str, duration: float) -> list[dict]:
        """
        Estimate word timings for caption synchronization.
        
        Args:
            script: The script text
            duration: Total audio duration in seconds
            
        Returns:
            List of dictionaries with word, start_time, end_time
        """
        words = script.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        # Calculate time per word (with some variance)
        avg_time_per_word = duration / total_words
        
        timings = []
        current_time = 0.0
        
        for word in words:
            # Longer words take slightly more time
            word_duration = avg_time_per_word * (0.8 + 0.4 * (len(word) / 6))
            word_duration = min(word_duration, avg_time_per_word * 1.5)
            
            timings.append({
                "word": word,
                "start": round(current_time, 2),
                "end": round(current_time + word_duration, 2)
            })
            
            current_time += word_duration
        
        return timings


if __name__ == "__main__":
    # Test the voice generator
    generator = VoiceGenerator()
    
    test_script = """Here's something most people don't realize about success.
    The difference between winners and losers isn't talent.
    It's consistency. Showing up every single day.
    Start today. Not tomorrow."""
    
    print("Testing Voice Generator...")
    result = generator.generate_voice(test_script, "test_voice")
    print(f"\nAudio saved to: {result['audio_path']}")
    print(f"Duration: {result['duration']} seconds")
