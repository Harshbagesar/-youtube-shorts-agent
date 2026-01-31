"""
Video Creator V2
With speed optimizations: parallel downloads, 720p mode, faster encoding
"""

import os
import random
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip, CompositeAudioClip
)
from .config import get_config


class VideoCreator:
    """Creates YouTube Shorts videos with optimized speed."""
    
    # System fonts to try
    FONTS_TO_TRY = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
        None
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
    
    def __init__(self, fast_mode: bool = True):
        """Initialize the video creator."""
        self.config = get_config()
        self.fast_mode = fast_mode
        
        # Resolution based on mode
        if fast_mode:
            self.width, self.height = 720, 1280  # 720p for speed
        else:
            self.width, self.height = self.config.get_resolution()
        
        self.pexels_headers = {
            "Authorization": self.config.pexels_api_key
        }
        self.caption_font = self._find_available_font()
        
        # Clip cache directory
        self.cache_path = self.config.base_path / "cache"
        self.cache_path.mkdir(exist_ok=True)
    
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
        """Create a YouTube Short video with optimized speed."""
        if output_filename is None:
            output_filename = f"short_{os.urandom(4).hex()}"
        
        niche = script_data.get("niche", "motivation")
        duration = voice_data["duration"]
        
        mode_label = "FAST" if self.fast_mode else "HD"
        print(f"\n🎬 Creating video ({duration:.1f}s) [{mode_label} MODE]...")
        
        try:
            # Step 1: Download stock footage (PARALLEL)
            print("📥 Downloading stock footage (parallel)...")
            video_clips = self._get_stock_footage_parallel(niche, duration)
            
            # Step 2: Create base video
            print("🎞️ Assembling video clips...")
            base_video = self._create_base_video(video_clips, duration)
            
            # Step 3: Load voiceover
            print("🎙️ Adding voiceover...")
            voiceover = AudioFileClip(voice_data["audio_path"])
            
            # Step 4: Add captions
            print("📝 Generating captions...")
            if self.caption_font:
                captioned_video = self._add_captions(
                    base_video, 
                    script_data["script"],
                    duration
                )
            else:
                print("⚠️ No font found, skipping captions")
                captioned_video = CompositeVideoClip([base_video])
            
            # Step 5: Add audio (voiceover + music)
            print("🎵 Mixing audio...")
            final_video = self._add_audio(captioned_video, voiceover, niche)
            
            # Step 6: Export with optimized settings
            print("💾 Exporting video...")
            output_path = self.config.output_path / f"{output_filename}.mp4"
            
            # Optimized encoding settings
            if self.fast_mode:
                fps = 24
                bitrate = "3M"
                preset = "ultrafast"
            else:
                fps = 30
                bitrate = "6M"
                preset = "fast"
            
            final_video.write_videofile(
                str(output_path),
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                bitrate=bitrate,
                preset=preset,
                threads=os.cpu_count() or 4,
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
    
    def _download_single_clip(self, args: tuple) -> tuple:
        """Download a single clip (for parallel execution)."""
        search_term, clip_index = args
        
        try:
            url = "https://api.pexels.com/videos/search"
            params = {
                "query": search_term,
                "per_page": 2,
                "orientation": "portrait",
                "size": "small" if self.fast_mode else "medium"
            }
            
            response = requests.get(url, headers=self.pexels_headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            videos = data.get("videos", [])
            if not videos:
                return None, 0
            
            video = videos[0]
            video_files = video.get("video_files", [])
            
            # Get appropriate quality file
            best_file = None
            target_height = 480 if self.fast_mode else 720
            
            for vf in sorted(video_files, key=lambda x: abs(x.get("height", 0) - target_height)):
                if vf.get("height", 0) >= 360:
                    best_file = vf
                    break
            
            if not best_file and video_files:
                best_file = video_files[0]
            
            if best_file:
                video_url = best_file["link"]
                
                # Check cache first
                cache_key = f"{search_term.replace(' ', '_')}_{clip_index}.mp4"
                clip_path = self.cache_path / cache_key
                
                if not clip_path.exists():
                    video_response = requests.get(video_url, stream=True, timeout=30)
                    with open(clip_path, "wb") as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                return str(clip_path), video.get("duration", 10)
            
            return None, 0
            
        except Exception as e:
            return None, 0
    
    def _get_stock_footage_parallel(self, niche: str, duration: float) -> list:
        """Download stock footage in parallel for speed."""
        search_terms = self.NICHE_SEARCH_TERMS.get(niche, self.NICHE_SEARCH_TERMS["motivation"])
        selected_terms = random.sample(search_terms, min(4, len(search_terms)))
        
        clips = []
        total_duration = 0
        target_duration = duration + 5
        
        # Prepare download tasks
        download_tasks = [(term, i) for i, term in enumerate(selected_terms)]
        
        # Download in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self._download_single_clip, task): task for task in download_tasks}
            
            for future in as_completed(futures):
                clip_path, clip_duration = future.result()
                if clip_path:
                    clips.append(clip_path)
                    total_duration += clip_duration
                    print(f"   ✓ Downloaded clip {len(clips)}")
                
                if total_duration >= target_duration:
                    break
        
        if not clips:
            print("⚠️ Using fallback background")
            clips = self._create_fallback_backgrounds(duration)
        
        return clips
    
    def _create_fallback_backgrounds(self, duration: float) -> list:
        """Create color background as fallback."""
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
        """Create base video from clips."""
        clips = []
        total_duration = 0
        
        for clip_path in clip_paths:
            if total_duration >= target_duration:
                break
            
            try:
                clip = VideoFileClip(clip_path)
                clip = self._resize_and_crop(clip)
                
                remaining = target_duration - total_duration
                if clip.duration > remaining:
                    clip = clip.subclipped(0, remaining)
                
                clips.append(clip)
                total_duration += clip.duration
                
            except Exception as e:
                continue
        
        if not clips:
            return ColorClip(
                size=(self.width, self.height),
                color=(30, 30, 50),
                duration=target_duration
            )
        
        if len(clips) == 1:
            return clips[0]
        
        return concatenate_videoclips(clips, method="compose")
    
    def _resize_and_crop(self, clip):
        """Resize and crop video to target dimensions."""
        clip_w, clip_h = clip.size
        target_ratio = self.width / self.height
        clip_ratio = clip_w / clip_h
        
        if clip_ratio > target_ratio:
            new_height = self.height
            new_width = int(clip_w * (self.height / clip_h))
        else:
            new_width = self.width
            new_height = int(clip_h * (self.width / clip_w))
        
        clip = clip.resized((new_width, new_height))
        
        x1 = max(0, (new_width - self.width) // 2)
        y1 = max(0, (new_height - self.height) // 2)
        x2 = x1 + self.width
        y2 = y1 + self.height
        
        return clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
    
    def _add_captions(self, video, script: str, duration: float) -> CompositeVideoClip:
        """Add captions to video."""
        words = script.split()
        if not words:
            return CompositeVideoClip([video])
        
        # Group into segments
        segments = []
        current = []
        for word in words:
            current.append(word)
            if len(current) >= 5 or word.endswith(('.', '!', '?')):
                segments.append(' '.join(current))
                current = []
        if current:
            segments.append(' '.join(current))
        
        if not segments:
            return CompositeVideoClip([video])
        
        segment_duration = duration / len(segments)
        caption_clips = []
        
        # Smaller font for fast mode
        font_size = 40 if self.fast_mode else 50
        
        for i, segment in enumerate(segments):
            try:
                txt_clip = TextClip(
                    text=segment.upper(),
                    font_size=font_size,
                    color='white',
                    font=self.caption_font,
                    stroke_color='black',
                    stroke_width=2,
                    size=(self.width - 60, None),
                    method='caption',
                    text_align='center'
                )
                
                txt_clip = txt_clip.with_position(('center', int(self.height * 0.75)))
                txt_clip = txt_clip.with_start(i * segment_duration)
                txt_clip = txt_clip.with_duration(segment_duration)
                
                caption_clips.append(txt_clip)
            except:
                continue
        
        if caption_clips:
            return CompositeVideoClip([video] + caption_clips)
        return CompositeVideoClip([video])
    
    def _add_audio(self, video, voiceover, niche: str):
        """Add voiceover and background music."""
        # Check for background music
        music_path = self._get_background_music(niche)
        
        if music_path:
            try:
                music = AudioFileClip(music_path)
                # Loop music if needed
                if music.duration < voiceover.duration:
                    loops_needed = int(voiceover.duration / music.duration) + 1
                    music = concatenate_audioclips([music] * loops_needed)
                music = music.subclipped(0, voiceover.duration)
                
                # Lower music volume
                music = music.with_volume_scaled(0.15)
                
                # Mix audio
                mixed = CompositeAudioClip([voiceover, music])
                return video.with_audio(mixed)
            except:
                pass
        
        return video.with_audio(voiceover)
    
    def _get_background_music(self, niche: str) -> str:
        """Get a background music file for the niche."""
        music_dir = self.config.assets_path / "music"
        
        if not music_dir.exists():
            return None
        
        # Look for niche-specific music first
        niche_music = list(music_dir.glob(f"{niche}*.mp3"))
        if niche_music:
            return str(random.choice(niche_music))
        
        # Fall back to any music
        all_music = list(music_dir.glob("*.mp3"))
        if all_music:
            return str(random.choice(all_music))
        
        return None
    
    def cleanup_temp_files(self):
        """Remove temporary files."""
        for temp_file in self.config.temp_path.glob("*"):
            try:
                temp_file.unlink()
            except:
                pass


# Helper for audio concatenation
def concatenate_audioclips(clips):
    """Concatenate audio clips."""
    from moviepy import concatenate_audioclips as concat
    return concat(clips)


if __name__ == "__main__":
    print("Video Creator V2 loaded.")
    creator = VideoCreator(fast_mode=True)
    print(f"Resolution: {creator.width}x{creator.height}")
    print(f"Font: {creator.caption_font}")
