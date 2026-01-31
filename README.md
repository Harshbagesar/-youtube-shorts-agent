# YouTube Shorts Automation Agent

🎬 **Fully autonomous agent that creates complete YouTube Shorts from trending topics.**

## Features

- 📈 **Auto Trend Research** - Finds trending topics in your niche
- ✍️ **GPT Script Writing** - Creates viral, engaging scripts
- 🎙️ **AI Voiceover** - Natural text-to-speech conversion
- 🎬 **Video Assembly** - Stock footage + captions + music
- 💾 **Export Ready** - 1080x1920 vertical MP4 files

## Quick Start

### 1. Install Dependencies

```bash
cd youtube-shorts-agent
pip install -r requirements.txt
```

**Also install FFmpeg** (required for video processing):
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows - download from ffmpeg.org
```

### 2. Configure API Keys

Your API keys are already configured in `config.env`:
- ✅ OpenAI API Key
- ✅ Pexels API Key

### 3. Run the Agent

**Interactive Mode (recommended for first use):**
```bash
python main.py
```

**Automatic Mode:**
```bash
python main.py --auto
```

**Create Multiple Videos:**
```bash
python main.py --auto --batch 5
```

**Custom Topic:**
```bash
python main.py --topic "morning routine habits" --niche motivation
```

## Usage Examples

```bash
# Test API connections
python main.py --test

# Create a tech video
python main.py --niche tech --auto

# Create 3 motivation videos
python main.py --niche motivation --auto --batch 3

# Create video about specific topic
python main.py --topic "AI tools everyone needs"
```

## Output

Videos are saved to the `output/` folder:
- Format: MP4
- Resolution: 1080x1920 (9:16 vertical)
- Ready for YouTube Shorts upload

## Content Niches

| Niche | Description |
|-------|-------------|
| `motivation` | Success habits, productivity, mindset |
| `tech` | AI tools, gadgets, tech tips |
| `facts` | Science, psychology, history facts |
| `finance` | Money tips, investing, side hustles |
| `entertainment` | Celebrity, movies, trending topics |

## Configuration

Edit `config.env` to customize:

```env
# Default niche
DEFAULT_NICHE=motivation

# Voice settings
VOICE_GENDER=male
VOICE_SPEED=1.0

# Video duration range (seconds)
VIDEO_DURATION_MIN=30
VIDEO_DURATION_MAX=60

# Background music volume
MUSIC_VOLUME=0.15
```

## Upgrading Voice Quality

For premium AI voices, add ElevenLabs API key:
1. Get API key from [elevenlabs.io](https://elevenlabs.io)
2. Add to `config.env`:
   ```
   ELEVENLABS_API_KEY=your_key_here
   ```

## Troubleshooting

**"No module named 'moviepy'"**
```bash
pip install moviepy
```

**"FFmpeg not found"**
```bash
sudo apt install ffmpeg
```

**"OpenAI API error"**
- Check your API key in `config.env`
- Ensure you have credits in your OpenAI account

---

Built with ❤️ for content creators
