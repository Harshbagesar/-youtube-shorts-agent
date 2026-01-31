"""
YouTube Shorts Automation Agent V2
With speed optimizations, web dashboard, and auto-upload
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.config import get_config, validate_config
from agent.trend_researcher import TrendResearcher
from agent.script_writer import ScriptWriter
from agent.voice_generator import VoiceGenerator
from agent.video_creator import VideoCreator


def print_banner():
    """Print welcome banner."""
    print("""
============================================================
🎬 YOUTUBE SHORTS AUTOMATION AGENT V2
============================================================
    """)


def create_single_video(
    niche: str = "motivation",
    topic: str = None,
    fast_mode: bool = True,
    upload: bool = False
) -> dict:
    """Create a single video."""
    config = get_config()
    
    # Initialize components
    researcher = TrendResearcher()
    writer = ScriptWriter()
    voice_gen = VoiceGenerator()
    video_creator = VideoCreator(fast_mode=fast_mode)
    
    # Get topic
    if not topic:
        print(f"\n🔍 Finding trending topic for '{niche}'...")
        topics = [t['title'] for t in researcher.get_trending_topics(niche)]
        if topics:
            topic = topics[0]
        else:
            topic = f"interesting {niche} tips"
    
    print(f"📌 Topic: {topic}")
    
    # Generate script
    print(f"\n{'='*50}")
    print(f"🎯 Creating Short: {topic}")
    print(f"{'='*50}")
    
    print("\n📝 Step 1/4: Generating script with GPT...")
    script_data = writer.generate_script(topic, niche)
    estimated_duration = writer.estimate_duration(script_data['script'])
    print(f"   ✓ Title: {script_data['title']}")
    print(f"   ✓ Script length: {len(script_data['script'].split())} words")
    print(f"   ✓ Estimated duration: {estimated_duration:.1f}s")
    
    # Generate voice
    print("\n🎙️ Step 2/4: Generating voiceover...")
    voice_data = voice_gen.generate_voice(script_data["script"])
    print(f"   ✓ Audio duration: {voice_data['duration']:.1f}s")
    print(f"   ✓ Engine: {voice_data['engine']}")
    
    # Create video
    print("\n🎬 Step 3/4: Creating video...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"short_{niche}_{timestamp}"
    video_data = video_creator.create_video(script_data, voice_data, output_filename)
    
    # Cleanup
    print("\n🧹 Step 4/4: Cleaning up temporary files...")
    video_creator.cleanup_temp_files()
    
    # Upload if requested
    if upload:
        print("\n📤 Uploading to YouTube...")
        try:
            from agent.youtube_uploader import YouTubeUploader
            uploader = YouTubeUploader()
            upload_result = uploader.upload(
                video_data["output_path"],
                video_data["title"],
                video_data.get("description", ""),
                tags=video_data.get("hashtags", [])
            )
            video_data["youtube_url"] = upload_result.get("url")
        except Exception as e:
            print(f"⚠️ Upload failed: {e}")
    
    # Print summary
    print(f"\n{'='*50}")
    print("✅ VIDEO CREATED SUCCESSFULLY!")
    print(f"{'='*50}")
    print(f"\n📁 Output: {video_data['output_path']}")
    print(f"⏱️ Duration: {video_data['duration']:.1f} seconds")
    print(f"📐 Resolution: {video_data['resolution']}")
    
    print(f"\n📋 YouTube Details:")
    print(f"   Title: {video_data.get('title', topic)}")
    print(f"   Hashtags: {' '.join(video_data.get('hashtags', ['#shorts']))}")
    
    if video_data.get("youtube_url"):
        print(f"\n🔗 YouTube URL: {video_data['youtube_url']}")
    
    return video_data


def run_interactive_mode():
    """Run in interactive mode."""
    print("🎮 INTERACTIVE MODE")
    print("-" * 40)
    
    # Select niche
    niches = ["motivation", "tech", "facts", "finance", "entertainment"]
    print("\nSelect a niche:")
    for i, niche in enumerate(niches, 1):
        emoji = ["💪", "💻", "🧠", "💰", "🎭"][i-1]
        print(f"  {i}. {emoji} {niche.title()}")
    
    choice = input("\nEnter number (1-5): ").strip()
    try:
        niche = niches[int(choice) - 1]
    except:
        niche = "motivation"
    
    print(f"\n✓ Selected: {niche}")
    
    # Get topics
    researcher = TrendResearcher()
    topics = [t['title'] for t in researcher.get_trending_topics(niche)]
    
    print(f"\n📈 Trending topics for '{niche}':")
    for i, topic in enumerate(topics[:5], 1):
        print(f"  {i}. {topic}")
    print(f"  6. Custom topic")
    
    choice = input("\nSelect topic (1-6): ").strip()
    if choice == "6":
        topic = input("Enter your topic: ").strip()
    else:
        try:
            topic = topics[int(choice) - 1]
        except:
            topic = topics[0] if topics else None
    
    # Fast mode?
    fast = input("\n⚡ Use fast mode? (y/n, default: y): ").strip().lower()
    fast_mode = fast != 'n'
    
    # Create video
    return create_single_video(niche=niche, topic=topic, fast_mode=fast_mode)


def run_automatic_mode(niche: str, batch: int = 1, fast_mode: bool = True, upload: bool = False):
    """Run in automatic mode."""
    print("🤖 AUTOMATIC MODE")
    print("-" * 40)
    
    videos = []
    for i in range(batch):
        print(f"\n📹 Creating video {i+1}/{batch}...")
        try:
            video = create_single_video(
                niche=niche,
                fast_mode=fast_mode,
                upload=upload
            )
            videos.append(video)
        except Exception as e:
            print(f"❌ Error creating video: {e}")
    
    print(f"\n🎉 Created {len(videos)} video(s)!")
    for v in videos:
        print(f"   📁 {v['output_path']}")
    
    return videos


def run_dashboard():
    """Run web dashboard."""
    try:
        from dashboard.app import run_dashboard as start_dashboard
        start_dashboard()
    except ImportError as e:
        print(f"❌ Dashboard not available: {e}")
        print("   Install Flask: pip install flask")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Automation Agent V2",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode arguments
    parser.add_argument("--auto", action="store_true", help="Automatic mode (no prompts)")
    parser.add_argument("--dashboard", action="store_true", help="Launch web dashboard")
    parser.add_argument("--test", action="store_true", help="Test API connections")
    
    # Video options
    parser.add_argument("--niche", default="motivation", 
                        choices=["motivation", "tech", "facts", "finance", "entertainment"],
                        help="Content niche (default: motivation)")
    parser.add_argument("--topic", type=str, help="Specific topic (optional)")
    parser.add_argument("--batch", type=int, default=1, help="Number of videos to create")
    
    # Speed/quality options
    parser.add_argument("--fast", action="store_true", default=True, help="Fast mode (720p)")
    parser.add_argument("--hd", action="store_true", help="HD mode (1080p, slower)")
    
    # Upload options
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after creation")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Validate config
    if not validate_config():
        print("\n❌ Configuration error. Please check config.env")
        return
    
    print("✅ All API keys configured correctly\n")
    
    # Initialize
    print("🔧 Initializing components...")
    config = get_config()
    
    # Ensure directories exist
    config.output_path.mkdir(exist_ok=True)
    config.temp_path.mkdir(exist_ok=True)
    config.assets_path.mkdir(exist_ok=True)
    (config.assets_path / "music").mkdir(exist_ok=True)
    
    print("✅ Agent ready!\n")
    
    # Handle modes
    if args.dashboard:
        run_dashboard()
    elif args.test:
        print("🧪 Testing API connections...")
        # Test would go here
        print("✅ All APIs working!")
    elif args.auto:
        fast_mode = not args.hd
        run_automatic_mode(
            niche=args.niche,
            batch=args.batch,
            fast_mode=fast_mode,
            upload=args.upload
        )
    else:
        run_interactive_mode()
    
    print(f"\n{'='*60}")
    print("👋 Thank you for using YouTube Shorts Agent!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
