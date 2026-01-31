"""
Voice Generator V2
With full ElevenLabs support and better voices
"""

import os
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
from .config import get_config


class VoiceGenerator:
    """Generates AI voiceover with gTTS or ElevenLabs."""
    
    # ElevenLabs voice IDs
    ELEVENLABS_VOICES = {
        "male": {
            "adam": "pNInz6obpgDQGcFmaJgB",
            "josh": "TxGEqnHWrfWFTfGW9XjX",
            "arnold": "VR6AewLTigWG4xSOukaG",
        },
        "female": {
            "bella": "EXAVITQu4vr4xnSDxMaL",
            "rachel": "21m00Tcm4TlvDq8ikWAM",
            "domi": "AZnzlk1XvdvUeBnXmlld",
        }
    }
    
    # gTTS language options
    GTTS_OPTIONS = {
        "en": {"lang": "en", "tld": "com"},
        "en_uk": {"lang": "en", "tld": "co.uk"},
        "en_au": {"lang": "en", "tld": "com.au"},
        "en_in": {"lang": "en", "tld": "co.in"},
    }
    
    def __init__(self):
        """Initialize voice generator."""
        self.config = get_config()
        self.temp_path = self.config.temp_path
        self.has_elevenlabs = bool(self.config.elevenlabs_api_key)
    
    def generate_voice(self, script: str, output_filename: str = None) -> dict:
        """Generate voiceover from script."""
        if output_filename is None:
            output_filename = f"voiceover_{os.urandom(4).hex()}"
        
        # Use ElevenLabs if available, otherwise gTTS
        if self.has_elevenlabs:
            return self._generate_elevenlabs(script, output_filename)
        else:
            return self._generate_gtts(script, output_filename)
    
    def _generate_gtts(self, script: str, output_filename: str) -> dict:
        """Generate voice using Google TTS (free)."""
        try:
            print(f"🎙️ Generating voiceover with gTTS...")
            
            tts = gTTS(
                text=script,
                lang="en",
                tld="com",
                slow=False
            )
            
            # Save initial MP3
            temp_mp3 = self.temp_path / f"{output_filename}_raw.mp3"
            tts.save(str(temp_mp3))
            
            # Process audio
            audio = AudioSegment.from_mp3(str(temp_mp3))
            
            # Speed up slightly for more energetic delivery
            if self.config.voice_speed != 1.0:
                audio = self._change_speed(audio, self.config.voice_speed)
            
            # Normalize volume
            audio = self._normalize_audio(audio)
            
            # Export
            final_path = self.temp_path / f"{output_filename}.mp3"
            audio.export(str(final_path), format="mp3", bitrate="192k")
            
            duration = len(audio) / 1000.0
            
            # Cleanup
            temp_mp3.unlink(missing_ok=True)
            
            print(f"✅ Voiceover generated: {duration:.1f} seconds")
            
            return {
                "audio_path": str(final_path),
                "duration": duration,
                "engine": "gtts",
                "voice": "default",
                "word_count": len(script.split())
            }
            
        except Exception as e:
            print(f"❌ Voice generation error: {e}")
            raise
    
    def _generate_elevenlabs(self, script: str, output_filename: str) -> dict:
        """Generate voice using ElevenLabs (premium)."""
        try:
            import requests
            
            print(f"🎙️ Generating voiceover with ElevenLabs...")
            
            # Select voice based on gender
            gender = self.config.voice_gender.lower()
            voices = self.ELEVENLABS_VOICES.get(gender, self.ELEVENLABS_VOICES["male"])
            voice_name = list(voices.keys())[0]  # First voice
            voice_id = voices[voice_name]
            
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
                    "similarity_boost": 0.8,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            if response.status_code == 401:
                print("⚠️ ElevenLabs API key invalid, falling back to gTTS")
                return self._generate_gtts(script, output_filename)
            
            if response.status_code == 429:
                print("⚠️ ElevenLabs quota exceeded, falling back to gTTS")
                return self._generate_gtts(script, output_filename)
            
            response.raise_for_status()
            
            # Save audio
            final_path = self.temp_path / f"{output_filename}.mp3"
            with open(final_path, "wb") as f:
                f.write(response.content)
            
            # Get duration
            audio = AudioSegment.from_mp3(str(final_path))
            duration = len(audio) / 1000.0
            
            print(f"✅ Voiceover generated: {duration:.1f} seconds (ElevenLabs)")
            
            return {
                "audio_path": str(final_path),
                "duration": duration,
                "engine": "elevenlabs",
                "voice": voice_name,
                "word_count": len(script.split())
            }
            
        except Exception as e:
            print(f"⚠️ ElevenLabs failed: {e}, falling back to gTTS")
            return self._generate_gtts(script, output_filename)
    
    def _change_speed(self, audio: AudioSegment, speed: float) -> AudioSegment:
        """Change playback speed."""
        if speed == 1.0:
            return audio
        
        new_frame_rate = int(audio.frame_rate * speed)
        return audio._spawn(audio.raw_data, overrides={
            "frame_rate": new_frame_rate
        }).set_frame_rate(audio.frame_rate)
    
    def _normalize_audio(self, audio: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
        """Normalize audio volume."""
        change = target_dbfs - audio.dBFS
        return audio.apply_gain(change)
    
    def list_voices(self) -> dict:
        """List available voices."""
        return {
            "gtts": list(self.GTTS_OPTIONS.keys()),
            "elevenlabs": {
                "male": list(self.ELEVENLABS_VOICES["male"].keys()),
                "female": list(self.ELEVENLABS_VOICES["female"].keys())
            },
            "elevenlabs_available": self.has_elevenlabs
        }


if __name__ == "__main__":
    gen = VoiceGenerator()
    print("Voice Generator V2 loaded.")
    print(f"ElevenLabs available: {gen.has_elevenlabs}")
    print(f"Available voices: {gen.list_voices()}")
