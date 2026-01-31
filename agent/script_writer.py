"""
Script Writer
Uses OpenAI GPT to generate engaging YouTube Shorts scripts.
"""

from openai import OpenAI
from .config import get_config


class ScriptWriter:
    """Generates viral YouTube Shorts scripts using GPT."""
    
    def __init__(self):
        """Initialize the script writer with OpenAI client."""
        self.config = get_config()
        self.client = OpenAI(api_key=self.config.openai_api_key)
        
        # Script templates by niche
        self.system_prompts = {
            "motivation": """You are a viral YouTube Shorts scriptwriter specializing in motivational content.
Your scripts are:
- Hook viewers in the first 2 seconds with a bold statement or question
- Conversational and personal (use "you" frequently)
- Action-oriented with specific, practical advice
- Emotionally compelling with power words
- 30-60 seconds when read aloud (150-200 words max)

Structure:
1. HOOK (2 sec): Shocking statement or provocative question
2. PROBLEM (5 sec): Relatable struggle the viewer faces  
3. INSIGHT (15 sec): The key revelation or framework
4. ACTION (10 sec): Specific steps they can take today
5. CTA (3 sec): Follow for more / Save this / Share with someone who needs this""",

            "tech": """You are a viral YouTube Shorts scriptwriter specializing in tech content.
Your scripts are:
- Start with "This AI tool..." or "Your phone can..." hooks
- Explain complex tech in simple, everyday language
- Focus on practical benefits and "life hacks"
- Create urgency ("before everyone else knows")
- 30-60 seconds when read aloud (150-200 words max)

Structure:
1. HOOK (2 sec): Surprising capability or hidden feature
2. WHAT (10 sec): What the tech/tool does
3. HOW (20 sec): Step-by-step explanation
4. WHY (10 sec): Why this matters / benefits
5. CTA (3 sec): Try it now / Follow for more tech tips""",

            "facts": """You are a viral YouTube Shorts scriptwriter specializing in fascinating facts.
Your scripts are:
- Open with "Did you know..." or "Scientists discovered..."
- Build curiosity with each sentence
- Use comparisons to make facts relatable
- End with mind-blowing conclusion
- 30-60 seconds when read aloud (150-200 words max)

Structure:
1. HOOK (2 sec): Most surprising fact as opener
2. CONTEXT (10 sec): Why this matters / background
3. DETAILS (20 sec): Additional fascinating details
4. TWIST (10 sec): Unexpected connection or implication
5. CTA (3 sec): Follow for more facts / Comment if you knew this""",

            "finance": """You are a viral YouTube Shorts scriptwriter specializing in finance/money content.
Your scripts are:
- Start with specific numbers or money amounts
- Address common financial mistakes or myths
- Provide actionable wealth-building tips
- Create FOMO about missing opportunities
- 30-60 seconds when read aloud (150-200 words max)

Structure:
1. HOOK (2 sec): Specific money amount or shocking statistic
2. PROBLEM (10 sec): Common mistake people make
3. SOLUTION (20 sec): The smarter approach with specifics
4. PROOF (10 sec): Example or result
5. CTA (3 sec): Start today / Follow for money tips""",

            "entertainment": """You are a viral YouTube Shorts scriptwriter specializing in entertainment content.
Your scripts are:
- Start with "Nobody knows this about..." or insider secrets
- Create gossip-worthy, shareable moments
- Build suspense and curiosity
- End with satisfying reveal or cliffhanger
- 30-60 seconds when read aloud (150-200 words max)

Structure:
1. HOOK (2 sec): Teaser of the secret/reveal
2. SETUP (10 sec): Context about the celebrity/show/trend
3. STORY (20 sec): The juicy details
4. REVEAL (10 sec): The surprising conclusion
5. CTA (3 sec): Follow for more / Comment your reaction"""
        }
    
    def generate_script(self, topic: str, niche: str = "motivation") -> dict:
        """
        Generate a YouTube Shorts script for the given topic.
        
        Args:
            topic: The topic/title to write about
            niche: Content niche for style guidance
            
        Returns:
            Dictionary with script, title, hashtags, and metadata
        """
        system_prompt = self.system_prompts.get(
            niche.lower(), 
            self.system_prompts["motivation"]
        )
        
        user_prompt = f"""Create a viral YouTube Shorts script about: "{topic}"

Requirements:
1. Make it EXACTLY suitable for a {self.config.video_duration_min}-{self.config.video_duration_max} second video
2. Write in a conversational, energetic tone
3. Include natural pauses (indicated by "...")
4. Every sentence should add value or build tension

Output format:
TITLE: [Catchy title for the Short, max 50 chars]
DESCRIPTION: [2-3 sentences for YouTube description]
HASHTAGS: [5-7 relevant hashtags]

---SCRIPT START---
[Your complete script here, ready to be read as voiceover]
---SCRIPT END---

SCENE_SUGGESTIONS: [Brief notes on what visuals would work well, comma-separated]"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            return self._parse_script_response(content, topic, niche)
            
        except Exception as e:
            print(f"❌ Script generation error: {e}")
            return self._get_fallback_script(topic, niche)
    
    def _parse_script_response(self, content: str, topic: str, niche: str) -> dict:
        """Parse the GPT response into structured data."""
        result = {
            "topic": topic,
            "niche": niche,
            "title": "",
            "description": "",
            "hashtags": [],
            "script": "",
            "scene_suggestions": [],
            "raw_response": content
        }
        
        lines = content.split("\n")
        in_script = False
        script_lines = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("TITLE:"):
                result["title"] = line.replace("TITLE:", "").strip()
            
            elif line.startswith("DESCRIPTION:"):
                result["description"] = line.replace("DESCRIPTION:", "").strip()
            
            elif line.startswith("HASHTAGS:"):
                hashtags = line.replace("HASHTAGS:", "").strip()
                result["hashtags"] = [h.strip() for h in hashtags.split() if h.startswith("#")]
            
            elif "---SCRIPT START---" in line:
                in_script = True
            
            elif "---SCRIPT END---" in line:
                in_script = False
            
            elif in_script and line:
                script_lines.append(line)
            
            elif line.startswith("SCENE_SUGGESTIONS:"):
                suggestions = line.replace("SCENE_SUGGESTIONS:", "").strip()
                result["scene_suggestions"] = [s.strip() for s in suggestions.split(",")]
        
        result["script"] = " ".join(script_lines)
        
        # Ensure we have valid data
        if not result["title"]:
            result["title"] = topic[:50]
        
        if not result["script"]:
            result["script"] = content  # Use raw content as fallback
        
        if not result["hashtags"]:
            result["hashtags"] = ["#shorts", "#viral", f"#{niche}"]
        
        return result
    
    def _get_fallback_script(self, topic: str, niche: str) -> dict:
        """Return a fallback script if GPT fails."""
        fallback_scripts = {
            "motivation": f"""Here's something most people don't realize about {topic}...
            
The difference between those who succeed and those who don't isn't talent.
It's not luck either.

It's consistency. Showing up every single day, even when you don't feel like it.

The person who practices for 15 minutes daily will always beat the person who practices for 3 hours once a week.

Small actions compound into massive results.

Start today. Not tomorrow. Not next week. Today.

Follow for more daily motivation.""",

            "tech": f"""Stop scrolling, this will change how you use technology...

Most people don't know about {topic}.

Here's why it matters: This can save you hours every single week.

Step one: Open your settings.
Step two: Look for this hidden feature.
Step three: Enable it and watch the magic happen.

You're welcome. Follow for more tech tips you actually need.""",
        }
        
        script = fallback_scripts.get(niche, fallback_scripts["motivation"])
        
        return {
            "topic": topic,
            "niche": niche,
            "title": topic[:50],
            "description": f"Learn about {topic} in this short video!",
            "hashtags": ["#shorts", "#viral", f"#{niche}", "#fyp"],
            "script": script,
            "scene_suggestions": ["motivational imagery", "success visuals", "nature shots"],
            "raw_response": script
        }
    
    def estimate_duration(self, script: str) -> float:
        """Estimate the duration of a script when read aloud."""
        # Average reading speed for voiceover: ~150 words per minute
        # Slightly slower for emphasis: ~140 wpm
        words = len(script.split())
        duration_minutes = words / 140
        duration_seconds = duration_minutes * 60
        return round(duration_seconds, 1)


if __name__ == "__main__":
    # Test the script writer
    writer = ScriptWriter()
    
    print("Testing Script Writer...")
    result = writer.generate_script("morning routine habits", "motivation")
    
    print(f"\nTitle: {result['title']}")
    print(f"Hashtags: {' '.join(result['hashtags'])}")
    print(f"\nScript:\n{result['script']}")
    print(f"\nEstimated duration: {writer.estimate_duration(result['script'])} seconds")
