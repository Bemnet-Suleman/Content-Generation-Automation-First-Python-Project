#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import json
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    import pickle
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

class YouTubeUploader:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.youtube = None
        self.setup_api()

    def load_config(self, config_path: str) -> dict:
        """Load YouTube API configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "youtube": {
                    "default_tags": ["fail", "glitch", "404Circus", "compilation", "tech fails", "viral"],
                    "default_category": "28",  # Science & Technology
                    "privacy_status": "public",
                    "made_for_kids": False
                }
            }

    def setup_api(self):
        """Setup YouTube Data API v3"""
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        creds = None
        token_path = 'token.pickle'
        credentials_path = 'credentials.json'
        
        # Load existing credentials
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logging.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(credentials_path):
                    logging.error(f"Credentials file not found: {credentials_path}")
                    logging.info("Please download OAuth2 credentials from Google Cloud Console")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            logging.info("YouTube API initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize YouTube API: {e}")

    def upload_video(self, video_path: str, title: str, description: str = "", 
                    tags: list = None, thumbnail_path: str = None,
                    category_id: str = None, privacy_status: str = None) -> str:
        """Upload video to YouTube"""
        
        if not self.youtube:
            logging.error("YouTube API not initialized")
            return None

        if not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            return None

        # Use config defaults if not provided
        youtube_config = self.config.get("youtube", {})
        
        if tags is None:
            tags = youtube_config.get("default_tags", [])
        if category_id is None:
            category_id = youtube_config.get("default_category", "28")
        if privacy_status is None:
            privacy_status = youtube_config.get("privacy_status", "public")

        # Prepare request body
        request_body = {
            'snippet': {
                'title': title[:100],  # YouTube title limit
                'description': description[:5000],  # YouTube description limit
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': youtube_config.get("made_for_kids", False)
            }
        }

        try:
            logging.info(f"Uploading video: {title}")
            
            # Create upload request
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in single chunk
                resumable=True
            )
            
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media
            )

            # Execute upload
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logging.info(f"Upload progress: {int(status.progress() * 100)}%")

            video_id = response['id']
            logging.info(f"Video uploaded successfully: https://youtube.com/watch?v={video_id}")

            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.upload_thumbnail(video_id, thumbnail_path)

            return video_id

        except HttpError as e:
            logging.error(f"HTTP error during upload: {e}")
            return None
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            return None

    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Upload custom thumbnail for video"""
        try:
            logging.info(f"Uploading thumbnail for video {video_id}")
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            
            logging.info(f"Thumbnail uploaded successfully for {video_id}")
            return True
            
        except Exception as e:
            logging.error(f"Thumbnail upload failed: {e}")
            return False

    def update_video(self, video_id: str, title: str = None, description: str = None,
                    tags: list = None) -> bool:
        """Update video metadata"""
        try:
            # Get current video details
            response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not response['items']:
                logging.error(f"Video not found: {video_id}")
                return False
            
            snippet = response['items'][0]['snippet']
            
            # Update only provided fields
            if title:
                snippet['title'] = title
            if description:
                snippet['description'] = description
            if tags:
                snippet['tags'] = tags
            
            # Update video
            self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': snippet
                }
            ).execute()
            
            logging.info(f"Video updated successfully: {video_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update video {video_id}: {e}")
            return False

    def get_video_stats(self, video_id: str) -> dict:
        """Get video statistics"""
        try:
            response = self.youtube.videos().list(
                part='statistics,snippet',
                id=video_id
            ).execute()
            
            if response['items']:
                item = response['items'][0]
                stats = item.get('statistics', {})
                snippet = item.get('snippet', {})
                
                return {
                    'title': snippet.get('title', ''),
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'dislikes': int(stats.get('dislikeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'published': snippet.get('publishedAt', '')
                }
            
            return {}
            
        except Exception as e:
            logging.error(f"Failed to get stats for {video_id}: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='404 Circus YouTube Uploader')
    parser.add_argument('--projectId', help='Project ID')
    parser.add_argument('--videoPath', required=True, help='Path to video file')
    parser.add_argument('--title', required=True, help='Video title')
    parser.add_argument('--description', help='Video description')
    parser.add_argument('--thumbnailPath', help='Path to thumbnail image')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--category', help='YouTube category ID')
    parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'], 
                       default='public', help='Privacy status')
    
    args = parser.parse_args()
    
    uploader = YouTubeUploader()
    
    # Parse tags
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(',')]
    
    try:
        video_id = uploader.upload_video(
            video_path=args.videoPath,
            title=args.title,
            description=args.description or f"{args.title}\n\nBrought to you by 404 Circus — Viral tech chaos compilations.",
            tags=tags,
            thumbnail_path=args.thumbnailPath,
            category_id=args.category,
            privacy_status=args.privacy
        )
        
        if video_id:
            print(f"SUCCESS: {video_id}")
            logging.info(f"Upload completed successfully for project {args.projectId}")
        else:
            logging.error("Upload failed")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Upload process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
