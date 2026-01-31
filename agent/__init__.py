# YouTube Shorts Agent
# ====================
# Autonomous agent for creating YouTube Shorts from trending topics

from .config import Config
from .trend_researcher import TrendResearcher
from .script_writer import ScriptWriter
from .voice_generator import VoiceGenerator
from .video_creator import VideoCreator

__version__ = "1.0.0"
__all__ = ["Config", "TrendResearcher", "ScriptWriter", "VoiceGenerator", "VideoCreator"]
