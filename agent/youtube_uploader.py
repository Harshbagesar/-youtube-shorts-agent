"""
YouTube Uploader
Uploads videos directly to YouTube as Shorts
"""

import os
import pickle
import time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .config import get_config


class YouTubeUploader:
    """Uploads videos to YouTube as Shorts."""
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def __init__(self):
        """Initialize YouTube uploader."""
        self.config = get_config()
        self.credentials_path = self.config.base_path / "credentials"
        self.credentials_path.mkdir(exist_ok=True)
        self.token_path = self.credentials_path / "youtube_token.pickle"
        self.client_secrets_path = self.credentials_path / "client_secrets.json"
        self.youtube = None
    
    def authenticate(self) -> bool:
        """Authenticate with YouTube API."""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
            
            if not creds:
                if not self.client_secrets_path.exists():
                    print("❌ YouTube credentials not set up.")
                    print(f"   Please add client_secrets.json to: {self.credentials_path}")
                    print("   Get it from: https://console.cloud.google.com/apis/credentials")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secrets_path), self.SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save token
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        return True
    
    def upload(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        privacy: str = "private",
        schedule_time: str = None
    ) -> dict:
        """
        Upload a video to YouTube.
        
        Args:
            video_path: Path to the video file
            title: Video title (max 100 chars)
            description: Video description
            tags: List of tags
            privacy: 'private', 'unlisted', or 'public'
            schedule_time: ISO format datetime for scheduled publish
            
        Returns:
            Dictionary with video ID and URL
        """
        if not self.youtube:
            if not self.authenticate():
                return {"error": "Authentication failed"}
        
        # Prepare metadata
        title = title[:100]  # YouTube limit
        
        if tags is None:
            tags = ["shorts", "viral"]
        
        # Add #Shorts to description if not present
        if "#shorts" not in description.lower():
            description = description + "\n\n#Shorts"
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Schedule if requested
        if schedule_time and privacy == "private":
            body['status']['publishAt'] = schedule_time
            body['status']['privacyStatus'] = "private"
        
        print(f"📤 Uploading to YouTube: {title}")
        
        try:
            # Upload video
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True
            )
            
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"   Uploading: {progress}%")
            
            video_id = response['id']
            video_url = f"https://youtube.com/shorts/{video_id}"
            
            print(f"✅ Upload complete!")
            print(f"🔗 Video URL: {video_url}")
            
            return {
                "video_id": video_id,
                "url": video_url,
                "title": title,
                "privacy": privacy
            }
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return {"error": str(e)}
    
    def check_quota(self) -> dict:
        """Check remaining YouTube API quota."""
        # YouTube API quota is 10,000 units per day
        # Video upload costs ~1600 units
        # This is a simplified check
        return {
            "daily_limit": 10000,
            "upload_cost": 1600,
            "estimated_uploads_remaining": 6
        }


if __name__ == "__main__":
    uploader = YouTubeUploader()
    print("YouTube Uploader loaded.")
    print(f"Token exists: {uploader.token_path.exists()}")
    print(f"Client secrets exist: {uploader.client_secrets_path.exists()}")
