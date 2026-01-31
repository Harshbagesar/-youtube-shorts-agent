#!/usr/bin/env python3
"""
YouTube Shorts Automation Agent
================================
Autonomous agent that creates complete YouTube Shorts from trending topics.

Usage:
    python main.py                    # Interactive mode
    python main.py --auto             # Fully automatic mode
    python main.py --niche tech       # Specify niche
    python main.py --topic "AI tools" # Specify topic directly
    python main.py --batch 5          # Create 5 videos automatically
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.config import get_config
from agent.trend_researcher import TrendResearcher
from agent.script_writer import ScriptWriter
from agent.voice_generator import VoiceGenerator
from agent.video_creator import VideoCreator


class YouTubeShortsAgent:
    """Main agent orchestrator for creating YouTube Shorts."""
    
    NICHES = ["motivation", "tech", "facts", "finance", "entertainment"]
    
    def __init__(self):
        """Initialize all agent components."""
        print("\n" + "="*60)
        print("🎬 YOUTUBE SHORTS AUTOMATION AGENT")
        print("="*60 + "\n")
        
        self.config = get_config()
        
        # Validate configuration
        valid, messages = self.config.validate()
        for msg in messages:
            print(msg)
        
        if not valid:
            print("\n❌ Please fix the configuration errors above.")
            print("   Edit config.env with your API keys.")
            sys.exit(1)
        
        print("\n🔧 Initializing components...")
        self.researcher = TrendResearcher()
        self.writer = ScriptWriter()
        self.voice_gen = VoiceGenerator()
        self.video_creator = VideoCreator()
        
        print("✅ Agent ready!\n")
    
    def run_interactive(self):
        """Run the agent in interactive mode."""
        print("📌 INTERACTIVE MODE")
        print("-" * 40)
        
        # Step 1: Select niche
        niche = self._select_niche()
        
        # Step 2: Select topic
        topic = self.researcher.select_topic_interactive(niche)
        
        # Step 3: Generate video
        result = self.create_short(topic["title"], niche)
        
        return result
    
    def run_automatic(self, niche: str = None, count: int = 1):
        """Run the agent in fully automatic mode."""
        print("🤖 AUTOMATIC MODE")
        print("-" * 40)
        
        if niche is None:
            niche = self.config.default_niche
        
        results = []
        
        for i in range(count):
            print(f"\n📹 Creating video {i+1}/{count}...")
            
            # Get trending topic
            topics = self.researcher.get_trending_topics(niche, count=5)
            topic = topics[i % len(topics)]
            
            print(f"📌 Topic: {topic['title']}")
            
            # Create the video
            try:
                result = self.create_short(topic["title"], niche)
                results.append(result)
            except Exception as e:
                print(f"❌ Error creating video: {e}")
                continue
        
        return results
    
    def create_short(self, topic: str, niche: str) -> dict:
        """
        Create a single YouTube Short from topic to final video.
        
        Args:
            topic: The topic to create content about
            niche: Content niche for style guidance
            
        Returns:
            Dictionary with video path and metadata
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'='*50}")
        print(f"🎯 Creating Short: {topic}")
        print(f"{'='*50}\n")
        
        # Step 1: Generate Script
        print("📝 Step 1/4: Generating script with GPT...")
        script_data = self.writer.generate_script(topic, niche)
        
        print(f"   ✓ Title: {script_data['title']}")
        print(f"   ✓ Script length: {len(script_data['script'].split())} words")
        duration_estimate = self.writer.estimate_duration(script_data['script'])
        print(f"   ✓ Estimated duration: {duration_estimate}s")
        
        # Step 2: Generate Voiceover
        print("\n🎙️ Step 2/4: Generating voiceover...")
        voice_data = self.voice_gen.generate_voice(
            script_data["script"],
            f"voice_{timestamp}"
        )
        print(f"   ✓ Audio duration: {voice_data['duration']:.1f}s")
        print(f"   ✓ Engine: {voice_data['engine']}")
        
        # Step 3: Create Video
        print("\n🎬 Step 3/4: Creating video...")
        video_result = self.video_creator.create_video(
            script_data,
            voice_data,
            f"short_{niche}_{timestamp}"
        )
        
        # Step 4: Cleanup
        print("\n🧹 Step 4/4: Cleaning up temporary files...")
        self.video_creator.cleanup_temp_files()
        
        # Summary
        print(f"\n{'='*50}")
        print("✅ VIDEO CREATED SUCCESSFULLY!")
        print(f"{'='*50}")
        print(f"\n📁 Output: {video_result['output_path']}")
        print(f"⏱️ Duration: {video_result['duration']:.1f} seconds")
        print(f"📐 Resolution: {video_result['resolution']}")
        print(f"\n📋 YouTube Details:")
        print(f"   Title: {video_result['title']}")
        print(f"   Hashtags: {' '.join(video_result['hashtags'])}")
        
        return video_result
    
    def _select_niche(self) -> str:
        """Interactive niche selection."""
        print("\n🎯 Select content niche:\n")
        
        for i, niche in enumerate(self.NICHES, 1):
            emoji = {
                "motivation": "💪",
                "tech": "🔧",
                "facts": "🧠",
                "finance": "💰",
                "entertainment": "🎭"
            }.get(niche, "📌")
            print(f"   {i}. {emoji} {niche.capitalize()}")
        
        print()
        
        while True:
            choice = input("Enter choice (1-5): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(self.NICHES):
                selected = self.NICHES[int(choice) - 1]
                print(f"\n✅ Selected: {selected.capitalize()}")
                return selected
            else:
                print("Invalid choice, please try again.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                      # Interactive mode
  python main.py --auto               # Automatic mode (1 video)
  python main.py --auto --batch 5     # Create 5 videos
  python main.py --niche tech         # Specify niche
  python main.py --topic "AI tools"   # Custom topic
  python main.py --test               # Test API connections
        """
    )
    
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run in fully automatic mode"
    )
    
    parser.add_argument(
        "--niche",
        type=str,
        choices=["motivation", "tech", "facts", "finance", "entertainment"],
        help="Content niche"
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        help="Specific topic to create content about"
    )
    
    parser.add_argument(
        "--batch",
        type=int,
        default=1,
        help="Number of videos to create (with --auto)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test API connections without creating video"
    )
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        print("\n🔍 Testing API connections...\n")
        config = get_config()
        valid, messages = config.validate()
        for msg in messages:
            print(msg)
        
        if valid:
            print("\n✅ All tests passed! Ready to create videos.")
        else:
            print("\n❌ Some tests failed. Check your config.env file.")
        
        return
    
    # Initialize agent
    agent = YouTubeShortsAgent()
    
    # Custom topic mode
    if args.topic:
        niche = args.niche or agent.config.default_niche
        result = agent.create_short(args.topic, niche)
        print(f"\n🎉 Video saved to: {result['output_path']}")
    
    # Automatic mode
    elif args.auto:
        niche = args.niche or agent.config.default_niche
        results = agent.run_automatic(niche, args.batch)
        print(f"\n🎉 Created {len(results)} video(s)!")
        for r in results:
            print(f"   📁 {r['output_path']}")
    
    # Interactive mode (default)
    else:
        result = agent.run_interactive()
        print(f"\n🎉 Video saved to: {result['output_path']}")
    
    print("\n" + "="*60)
    print("👋 Thank you for using YouTube Shorts Agent!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
