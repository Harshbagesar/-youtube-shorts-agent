"""
Trend Researcher
Finds trending topics using Google Trends and web research.
"""

import random
from datetime import datetime
from pytrends.request import TrendReq


class TrendResearcher:
    """Researches trending topics for content creation."""
    
    # Predefined topic databases by niche
    NICHE_TOPICS = {
        "motivation": [
            "morning routine habits successful people",
            "how to build self discipline",
            "overcoming procrastination tips",
            "growth mindset vs fixed mindset",
            "habits of millionaires",
            "how to stay focused",
            "productivity hacks that work",
            "building confidence quickly",
            "stop overthinking techniques",
            "morning motivation routine",
            "success habits daily",
            "mental toughness tips",
            "goal setting strategies",
            "time management secrets",
            "how to wake up early",
        ],
        "tech": [
            "AI tools everyone should use",
            "future of artificial intelligence",
            "smartphone hidden features",
            "best productivity apps 2024",
            "cybersecurity tips for beginners",
            "how AI is changing jobs",
            "tech gadgets worth buying",
            "programming tips for beginners",
            "future technology predictions",
            "ChatGPT tips and tricks",
            "viral tech hacks",
            "robots replacing humans",
            "quantum computing explained simply",
            "metaverse future",
            "electric vehicles future",
        ],
        "facts": [
            "psychology facts about human behavior",
            "amazing science facts",
            "history facts nobody knows",
            "human body amazing facts",
            "space facts mind blowing",
            "animal kingdom facts",
            "brain facts psychology",
            "money facts rich people know",
            "secrets of ancient civilizations",
            "facts about dreams",
            "ocean mysteries unsolved",
            "conspiracy theories that were true",
            "creepy facts about the world",
            "facts about success",
            "universe facts mind blowing",
        ],
        "finance": [
            "passive income ideas",
            "investing for beginners",
            "cryptocurrency explained",
            "how to save money fast",
            "financial freedom tips",
            "money mistakes to avoid",
            "building wealth in your 20s",
            "side hustle ideas 2024",
            "stock market for beginners",
            "real estate investing tips",
            "budgeting tips that work",
            "debt payoff strategies",
            "rich vs poor mindset",
            "money habits of millionaires",
            "retirement planning tips",
        ],
        "entertainment": [
            "celebrity secrets revealed",
            "movie facts you didnt know",
            "viral trends explained",
            "behind the scenes secrets",
            "famous people before fame",
            "plot twists in movies",
            "TV show hidden details",
            "gaming tips and tricks",
            "social media drama explained",
            "internet mysteries",
            "trending memes explained",
            "celebrity transformations",
            "movie mistakes you missed",
            "viral videos explained",
            "pop culture moments",
        ],
    }
    
    def __init__(self):
        """Initialize the trend researcher."""
        self.pytrends = None
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360)
        except Exception:
            print("⚠️ Google Trends not available, using curated topics")
    
    def get_trending_topics(self, niche: str = "motivation", count: int = 5) -> list[dict]:
        """
        Get trending topics for the specified niche.
        
        Args:
            niche: Content niche (motivation, tech, facts, finance, entertainment)
            count: Number of topics to return
            
        Returns:
            List of topic dictionaries with title and context
        """
        topics = []
        
        # Try to get real-time trends from Google
        google_trends = self._get_google_trends(niche)
        if google_trends:
            topics.extend(google_trends)
        
        # Fill remaining with curated topics
        niche_key = niche.lower()
        if niche_key in self.NICHE_TOPICS:
            curated = self.NICHE_TOPICS[niche_key].copy()
            random.shuffle(curated)
            
            for topic in curated:
                if len(topics) >= count:
                    break
                if not any(t["title"].lower() == topic.lower() for t in topics):
                    topics.append({
                        "title": topic,
                        "source": "curated",
                        "niche": niche,
                        "timestamp": datetime.now().isoformat()
                    })
        
        return topics[:count]
    
    def _get_google_trends(self, niche: str) -> list[dict]:
        """Fetch trending searches from Google Trends."""
        if not self.pytrends:
            return []
        
        try:
            # Get trending searches for US
            trending = self.pytrends.trending_searches(pn='united_states')
            
            # Convert to our format
            topics = []
            for idx, row in trending.head(10).iterrows():
                topic_title = row[0]
                topics.append({
                    "title": f"{topic_title} {niche}",
                    "source": "google_trends",
                    "niche": niche,
                    "timestamp": datetime.now().isoformat()
                })
            
            return topics[:3]  # Return top 3 Google trends
            
        except Exception as e:
            print(f"⚠️ Google Trends error: {e}")
            return []
    
    def get_topic_context(self, topic: str) -> str:
        """Generate additional context for a topic."""
        contexts = {
            "motivation": "Focus on actionable advice, emotional hooks, and personal transformation stories.",
            "tech": "Explain in simple terms, highlight practical applications, and mention future implications.",
            "facts": "Use surprising statistics, compare to everyday things, and add 'most people don't know' angle.",
            "finance": "Emphasize practical steps, mention specific numbers, and address common mistakes.",
            "entertainment": "Focus on insider knowledge, behind-the-scenes details, and trending commentary.",
        }
        
        for niche, context in contexts.items():
            if niche in topic.lower():
                return context
        
        return "Create engaging, shareable content that provides value to viewers."
    
    def select_topic_interactive(self, niche: str = "motivation") -> dict:
        """
        Interactive topic selection - shows options and lets user choose.
        
        Args:
            niche: Content niche
            
        Returns:
            Selected topic dictionary
        """
        topics = self.get_trending_topics(niche, count=5)
        
        print(f"\n🔥 Trending topics in '{niche}':\n")
        for i, topic in enumerate(topics, 1):
            source = "📈" if topic["source"] == "google_trends" else "📚"
            print(f"  {i}. {source} {topic['title']}")
        
        print(f"\n  0. 🎲 Random selection")
        print(f"  C. ✏️  Custom topic\n")
        
        while True:
            choice = input("Select topic (1-5, 0, or C): ").strip().lower()
            
            if choice == "0":
                selected = random.choice(topics)
                print(f"\n🎲 Randomly selected: {selected['title']}")
                return selected
            
            elif choice == "c":
                custom = input("Enter your custom topic: ").strip()
                return {
                    "title": custom,
                    "source": "custom",
                    "niche": niche,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif choice.isdigit() and 1 <= int(choice) <= len(topics):
                selected = topics[int(choice) - 1]
                print(f"\n✅ Selected: {selected['title']}")
                return selected
            
            else:
                print("Invalid choice, try again.")


if __name__ == "__main__":
    # Test the researcher
    researcher = TrendResearcher()
    
    print("Testing Trend Researcher...")
    topics = researcher.get_trending_topics("motivation", 5)
    
    for topic in topics:
        print(f"- {topic['title']} ({topic['source']})")
