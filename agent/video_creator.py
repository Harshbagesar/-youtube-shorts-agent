"""
Video Creator
Assembles the final YouTube Short video with stock footage, captions, and music.
Compatible with MoviePy 2.x
"""

import os
import random
import requests
from pathlib import Path
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip, CompositeAudioClip
)
from .config import get_config


class VideoCreator:
    """Creates YouTube Shorts videos by assembling all components."""
    
    # System fonts to try (in order of preference)
    FONTS_TO_TRY = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arial.ttf",  # Windows
        None  # Will use default
    ]
    
    # Pexels video search queries by niche
    NICHE_SEARCH_TERMS = {
        "motivation": [
            "success business", "morning sunrise", "workout fitness",
            "city aerial", "nature mountains", "running athlete",
            "typing laptop", "meditation peaceful", "ocean waves"
        ],
        "tech": [
            "technology", "coding programming", "smartphone mobile",
            "futuristic", "computer screen", "robot ai",
            "circuit board", "data center", "digital abstract"
        ],
        "facts": [
            "space universe", "nature wildlife", "ocean underwater",
            "science laboratory", "ancient history", "brain mind",
            "earth planet", "microscope", "abstract patterns"
        ],
        "finance": [
            "money cash", "stock market", "business office",
            "cryptocurrency", "luxury lifestyle", "city skyline",
            "calculator finance", "gold coins", "real estate"
        ],
        "entertainment": [
            "party celebration", "movie cinema", "gaming",
            "concert crowd", "red carpet", "social media",
            "trending viral", "colorful abstract", "neon lights"
        ]
    }
    
    def __init__(self):
        """Initialize the video creator."""
        self.config = get_config()
        self.width, self.height = self.config.get_resolution()
        self.pexels_headers = {
            "Authorization": self.config.pexels_api_key
        }
        self.caption_font = self._find_available_font()
    
    def _find_available_font(self) -> str:
        """Find an available font on the system."""
        for font_path in self.FONTS_TO_TRY:
            if font_path is None:
                return None
            if os.path.exists(font_path):
                return font_path
        return None
    
    def create_video(
        self,
        script_data: dict,
        voice_data: dict,
        output_filename: str = None
    ) -> dict:
        """
        Create a complete YouTube Short video.
        
        Args:
            script_data: Dictionary from ScriptWriter with script and metadata
            voice_data: Dictionary from VoiceGenerator with audio path and duration
            output_filename: Optional custom output filename
            
        Returns:
            Dictionary with output path and video metadata
        """
        if output_filename is None:
            output_filename = f"short_{os.urandom(4).hex()}"
        
        niche = script_data.get("niche", "motivation")
        duration = voice_data["duration"]
        
        print(f"\n🎬 Creating video ({duration:.1f}s)...")
        
        try:
            # Step 1: Download stock footage
            print("📥 Downloading stock footage...")
            video_clips = self._get_stock_footage(niche, duration)
            
            # Step 2: Create base video from clips
            print("🎞️ Assembling video clips...")
            base_video = self._create_base_video(video_clips, duration)
            
            # Step 3: Add voiceover audio
            print("🎙️ Adding voiceover...")
            voiceover = AudioFileClip(voice_data["audio_path"])
            
            # Step 4: Add captions (if font available)
            print("📝 Generating captions...")
            if self.caption_font:
                captioned_video = self._add_captions(
                    base_video, 
                    script_data["script"],
                    duration
                )
            else:
                print("⚠️ No suitable font found, skipping captions")
                captioned_video = CompositeVideoClip([base_video])
            
            # Step 5: Add audio
            print("🎵 Adding audio...")
            final_video = captioned_video.with_audio(voiceover)
            
            # Step 6: Export final video
            print("💾 Exporting video (this may take a few minutes)...")
            output_path = self.config.output_path / f"{output_filename}.mp4"
            
            final_video.write_videofile(
                str(output_path),
                fps=24,  # Lower fps for faster encoding
                codec="libx264",
                audio_codec="aac",
                bitrate="4M",  # Lower bitrate for faster encoding
                preset="ultrafast",  # Fastest encoding
                threads=4,
                logger=None
            )
            
            # Cleanup
            final_video.close()
            base_video.close()
            voiceover.close()
            
            print(f"\n✅ Video created successfully!")
            print(f"📁 Saved to: {output_path}")
            
            return {
                "output_path": str(output_path),
                "duration": duration,
                "resolution": f"{self.width}x{self.height}",
                "title": script_data.get("title", ""),
                "description": script_data.get("description", ""),
                "hashtags": script_data.get("hashtags", [])
            }
            
        except Exception as e:
            print(f"❌ Video creation error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_stock_footage(self, niche: str, duration: float) -> list:
        """Download stock footage from Pexels."""
        clips = []
        search_terms = self.NICHE_SEARCH_TERMS.get(niche, self.NICHE_SEARCH_TERMS["motivation"])
        
        # We need enough clips to cover the duration
        target_duration = duration + 5  # Extra buffer
        current_duration = 0
        
        for search_term in random.sample(search_terms, min(5, len(search_terms))):
            if current_duration >= target_duration:
                break
            
            try:
                # Search Pexels for videos
                url = "https://api.pexels.com/videos/search"
                params = {
                    "query": search_term,
                    "per_page": 3,
                    "orientation": "portrait",
                    "size": "medium"
                }
                
                response = requests.get(url, headers=self.pexels_headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for video in data.get("videos", [])[:2]:
                    if current_duration >= target_duration:
                        break
                    
                    # Get a smaller file for faster download
                    video_files = video.get("video_files", [])
                    best_file = None
                    
                    # Prefer smaller files for speed
                    for vf in sorted(video_files, key=lambda x: x.get("height", 0)):
                        if 360 <= vf.get("height", 0) <= 720:
                            best_file = vf
                            break
                    
                    if not best_file and video_files:
                        best_file = video_files[0]
                    
                    if best_file:
                        video_url = best_file["link"]
                        clip_path = self.config.temp_path / f"clip_{len(clips)}.mp4"
                        
                        print(f"   ↓ Downloading clip {len(clips)+1}...")
                        video_response = requests.get(video_url, stream=True, timeout=60)
                        with open(clip_path, "wb") as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        clips.append(str(clip_path))
                        current_duration += video.get("duration", 10)
                        
            except Exception as e:
                print(f"⚠️ Error fetching video for '{search_term}': {e}")
                continue
        
        # If we couldn't get enough clips, use color backgrounds
        if not clips:
            print("⚠️ Using fallback color backgrounds")
            clips = self._create_fallback_backgrounds(duration)
        
        return clips
    
    def _create_fallback_backgrounds(self, duration: float) -> list:
        """Create simple color background as fallback."""
        # Just return a single color clip path
        clip_path = self.config.temp_path / "bg_fallback.mp4"
        
        color_clip = ColorClip(
            size=(self.width, self.height),
            color=(30, 30, 50),
            duration=duration
        )
        
        color_clip.write_videofile(
            str(clip_path),
            fps=24,
            codec="libx264",
            preset="ultrafast",
            logger=None
        )
        color_clip.close()
        
        return [str(clip_path)]
    
    def _create_base_video(self, clip_paths: list, target_duration: float):
        """Create base video from multiple clips."""
        clips = []
        total_duration = 0
        
        for clip_path in clip_paths:
            if total_duration >= target_duration:
                break
            
            try:
                clip = VideoFileClip(clip_path)
                
                # Resize to fit our dimensions
                clip = self._resize_and_crop(clip)
                
                # Calculate how much of this clip we need
                remaining = target_duration - total_duration
                if clip.duration > remaining:
                    clip = clip.subclipped(0, remaining)
                
                clips.append(clip)
                total_duration += clip.duration
                
            except Exception as e:
                print(f"⚠️ Error loading clip {clip_path}: {e}")
                continue
        
        if not clips:
            # Create a simple color background
            return ColorClip(
                size=(self.width, self.height),
                color=(30, 30, 50),
                duration=target_duration
            )
        
        # If only one clip, return it directly
        if len(clips) == 1:
            return clips[0]
        
        # Concatenate all clips
        final_clip = concatenate_videoclips(clips, method="compose")
        
        return final_clip
    
    def _resize_and_crop(self, clip):
        """Resize and center-crop video to target dimensions."""
        # Get clip dimensions
        clip_w, clip_h = clip.size
        
        target_ratio = self.width / self.height
        clip_ratio = clip_w / clip_h
        
        if clip_ratio > target_ratio:
            # Clip is wider, fit by height
            new_height = self.height
            new_width = int(clip_w * (self.height / clip_h))
        else:
            # Clip is taller, fit by width
            new_width = self.width
            new_height = int(clip_h * (self.width / clip_w))
        
        # Resize using MoviePy 2.x method
        clip = clip.resized((new_width, new_height))
        
        # Center crop - calculate crop coordinates
        x1 = max(0, (new_width - self.width) // 2)
        y1 = max(0, (new_height - self.height) // 2)
        x2 = x1 + self.width
        y2 = y1 + self.height
        
        clip = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
        
        return clip
    
    def _add_captions(
        self, 
        video, 
        script: str, 
        duration: float
    ) -> CompositeVideoClip:
        """Add TikTok-style captions to the video."""
        words = script.split()
        total_words = len(words)
        
        if total_words == 0:
            return CompositeVideoClip([video])
        
        # Group words into caption segments (4-6 words each)
        segments = []
        current_segment = []
        
        for word in words:
            current_segment.append(word)
            if len(current_segment) >= 5 or word.endswith(('.', '!', '?')):
                segments.append(' '.join(current_segment))
                current_segment = []
        
        if current_segment:
            segments.append(' '.join(current_segment))
        
        if not segments:
            return CompositeVideoClip([video])
        
        # Calculate timing for each segment
        segment_duration = duration / len(segments)
        
        caption_clips = []
        
        for i, segment in enumerate(segments):
            start_time = i * segment_duration
            
            try:
                # Create text clip with available font
                txt_clip = TextClip(
                    text=segment.upper(),
                    font_size=50,
                    color='white',
                    font=self.caption_font,
                    stroke_color='black',
                    stroke_width=2,
                    size=(self.width - 80, None),
                    method='caption',
                    text_align='center'
                )
                
                txt_clip = txt_clip.with_position(('center', int(self.height * 0.75)))
                txt_clip = txt_clip.with_start(start_time)
                txt_clip = txt_clip.with_duration(segment_duration)
                
                caption_clips.append(txt_clip)
                
            except Exception as e:
                # Skip this caption if it fails
                continue
        
        # Composite video with captions
        if caption_clips:
            final = CompositeVideoClip([video] + caption_clips)
        else:
            final = CompositeVideoClip([video])
        
        return final
    
    def cleanup_temp_files(self):
        """Remove temporary files created during video generation."""
        for temp_file in self.config.temp_path.glob("*"):
            try:
                temp_file.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    # Test the video creator
    print("Video Creator module loaded successfully.")
    creator = VideoCreator()
    print(f"Output resolution: {creator.width}x{creator.height}")
    print(f"Caption font: {creator.caption_font}")
