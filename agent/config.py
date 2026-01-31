"""
Configuration Manager
Loads and validates environment variables for the agent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Central configuration manager for the YouTube Shorts Agent."""
    
    def __init__(self):
        # Load environment variables from config.env
        config_path = Path(__file__).parent.parent / "config.env"
        load_dotenv(config_path)
        
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", "")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        
        # Settings
        self.default_niche = os.getenv("DEFAULT_NICHE", "motivation")
        self.voice_gender = os.getenv("VOICE_GENDER", "male")
        self.voice_speed = float(os.getenv("VOICE_SPEED", "1.0"))
        
        # Video settings
        self.video_duration_min = int(os.getenv("VIDEO_DURATION_MIN", "30"))
        self.video_duration_max = int(os.getenv("VIDEO_DURATION_MAX", "60"))
        self.output_resolution = os.getenv("OUTPUT_RESOLUTION", "1080x1920")
        self.music_volume = float(os.getenv("MUSIC_VOLUME", "0.15"))
        
        # Paths
        self.base_path = Path(__file__).parent.parent
        self.output_path = self.base_path / "output"
        self.assets_path = self.base_path / "assets"
        self.temp_path = self.base_path / "temp"
        
        # Create necessary directories
        self.output_path.mkdir(exist_ok=True)
        self.assets_path.mkdir(exist_ok=True)
        self.temp_path.mkdir(exist_ok=True)
        (self.assets_path / "fonts").mkdir(exist_ok=True)
        (self.assets_path / "music").mkdir(exist_ok=True)
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate that required API keys are present."""
        errors = []
        
        if not self.openai_api_key or not self.openai_api_key.startswith("sk-"):
            errors.append("❌ OpenAI API key is missing or invalid")
        
        if not self.pexels_api_key:
            errors.append("❌ Pexels API key is missing")
        
        if errors:
            return False, errors
        
        return True, ["✅ All API keys configured correctly"]
    
    def get_resolution(self) -> tuple[int, int]:
        """Parse resolution string to width, height tuple."""
        parts = self.output_resolution.split("x")
        return int(parts[0]), int(parts[1])
    
    def __repr__(self):
        return f"Config(niche={self.default_niche}, voice={self.voice_gender})"


# Global config instance
_config = None

def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def validate_config() -> bool:
    """Validate configuration and print status."""
    config = get_config()
    valid, messages = config.validate()
    for msg in messages:
        print(msg)
    return valid

