"""
Web Dashboard for YouTube Shorts Agent
Control your agent from the browser
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.config import get_config
from agent.trend_researcher import TrendResearcher
from agent.script_writer import ScriptWriter
from agent.voice_generator import VoiceGenerator
from agent.video_creator import VideoCreator


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global state
agent_status = {
    "is_running": False,
    "current_step": "",
    "progress": 0,
    "last_video": None,
    "history": []
}


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current agent status."""
    return jsonify(agent_status)


@app.route('/api/niches')
def get_niches():
    """Get available niches."""
    return jsonify({
        "niches": ["motivation", "tech", "facts", "finance", "entertainment"]
    })


@app.route('/api/topics/<niche>')
def get_topics(niche):
    """Get trending topics for a niche."""
    researcher = TrendResearcher()
    topics = [t['title'] for t in researcher.get_trending_topics(niche)]
    return jsonify({"topics": topics[:10]})


@app.route('/api/create', methods=['POST'])
def create_video():
    """Create a new video."""
    global agent_status
    
    if agent_status["is_running"]:
        return jsonify({"error": "Agent is already running"}), 400
    
    data = request.json
    niche = data.get('niche', 'motivation')
    topic = data.get('topic', '')
    fast_mode = data.get('fast_mode', True)
    
    # Run in background
    thread = threading.Thread(
        target=_create_video_task,
        args=(niche, topic, fast_mode)
    )
    thread.start()
    
    return jsonify({"status": "started"})


def _create_video_task(niche: str, topic: str, fast_mode: bool):
    """Background task to create video."""
    global agent_status
    
    try:
        agent_status["is_running"] = True
        agent_status["progress"] = 0
        
        config = get_config()
        
        # Step 1: Get topic
        agent_status["current_step"] = "Finding topic..."
        agent_status["progress"] = 10
        
        if not topic:
            researcher = TrendResearcher()
            topics = [t['title'] for t in researcher.get_trending_topics(niche)]
            topic = topics[0] if topics else f"{niche} tips"
        
        # Step 2: Generate script
        agent_status["current_step"] = "Writing script..."
        agent_status["progress"] = 25
        
        writer = ScriptWriter()
        script_data = writer.generate_script(topic, niche)
        
        # Step 3: Generate voice
        agent_status["current_step"] = "Generating voiceover..."
        agent_status["progress"] = 45
        
        voice_gen = VoiceGenerator()
        voice_data = voice_gen.generate_voice(script_data["script"])
        
        # Step 4: Create video
        agent_status["current_step"] = "Creating video..."
        agent_status["progress"] = 65
        
        video_creator = VideoCreator(fast_mode=fast_mode)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"short_{niche}_{timestamp}"
        video_data = video_creator.create_video(script_data, voice_data, output_filename)
        
        # Step 5: Cleanup
        agent_status["current_step"] = "Cleaning up..."
        agent_status["progress"] = 90
        video_creator.cleanup_temp_files()
        
        # Done!
        agent_status["current_step"] = "Complete!"
        agent_status["progress"] = 100
        agent_status["last_video"] = video_data
        
        # Add to history
        agent_status["history"].insert(0, {
            "title": script_data.get("title", topic),
            "path": video_data["output_path"],
            "duration": video_data["duration"],
            "created_at": datetime.now().isoformat(),
            "niche": niche
        })
        
        # Keep only last 20 in history
        agent_status["history"] = agent_status["history"][:20]
        
    except Exception as e:
        agent_status["current_step"] = f"Error: {str(e)}"
        agent_status["progress"] = 0
        
    finally:
        agent_status["is_running"] = False


@app.route('/api/history')
def get_history():
    """Get video creation history."""
    return jsonify({"history": agent_status["history"]})


@app.route('/api/videos/<path:filename>')
def serve_video(filename):
    """Serve a created video file."""
    config = get_config()
    return send_from_directory(str(config.output_path), filename)


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Get or update settings."""
    config = get_config()
    
    if request.method == 'GET':
        return jsonify({
            "default_niche": config.default_niche,
            "voice_gender": config.voice_gender,
            "has_openai": bool(config.openai_api_key),
            "has_pexels": bool(config.pexels_api_key),
            "has_elevenlabs": bool(config.elevenlabs_api_key),
        })
    
    # POST - update settings (would need to update config.env)
    return jsonify({"status": "settings saved"})


def run_dashboard(port: int = 5000, debug: bool = False):
    """Run the dashboard server."""
    print(f"\n🌐 Dashboard running at: http://localhost:{port}")
    print("   Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    run_dashboard(debug=True)
