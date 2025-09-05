#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

try:
    from bs4 import BeautifulSoup
    import praw  # Reddit API wrapper
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

class ContentScraper:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load scraping configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "reddit": {
                    "subreddits": ["techfails", "softwaregore", "ProgrammerHumor", "pcmasterrace"],
                    "min_score": 100,
                    "time_filter": "day"
                },
                "keywords": [
                    "fail", "error", "crash", "glitch", "bug", "404", "500",
                    "blue screen", "bsod", "server down", "network error",
                    "compilation error", "syntax error", "database crash"
                ],
                "scoring": {
                    "upvote_weight": 0.4,
                    "comment_weight": 0.3,
                    "keyword_weight": 0.3
                }
            }

    def scrape_reddit(self, subreddit_name: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Scrape Reddit for tech fail content"""
        content = []
        
        try:
            # Note: In production, you would use proper Reddit API credentials
            # For now, we'll simulate the scraping with example data structure
            
            url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit={limit}"
            
            # Simulate API response structure
            posts = self.get_reddit_posts(subreddit_name, limit)
            
            for post in posts:
                # Calculate trending score
                score = self.calculate_trending_score(
                    post.get('ups', 0),
                    post.get('num_comments', 0),
                    post.get('title', '')
                )
                
                # Extract video URLs if present
                video_url = self.extract_video_url(post)
                
                if score > 50:  # Minimum threshold
                    content.append({
                        'title': post.get('title', ''),
                        'url': video_url or post.get('url', ''),
                        'description': post.get('selftext', '')[:500],
                        'source': f"r/{subreddit_name}",
                        'upvotes': post.get('ups', 0),
                        'views': post.get('view_count', 0),
                        'likes': post.get('ups', 0),
                        'trendingScore': min(score, 100),
                        'tags': self.extract_tags(post.get('title', '')),
                        'thumbnailUrl': post.get('thumbnail', ''),
                        'sourceData': post
                    })
            
            logging.info(f"Scraped {len(content)} items from r/{subreddit_name}")
            
        except Exception as e:
            logging.error(f"Failed to scrape r/{subreddit_name}: {e}")
        
        return content

    def get_reddit_posts(self, subreddit: str, limit: int) -> List[Dict[str, Any]]:
        """Get Reddit posts (simulated for demo)"""
        # In production, use proper Reddit API
        example_posts = [
            {
                'title': 'Epic Server Meltdown - Entire Data Center Goes Down',
                'url': 'https://v.redd.it/example1',
                'selftext': 'Our production server just crashed and took everything with it...',
                'ups': 1500,
                'num_comments': 89,
                'thumbnail': 'https://via.placeholder.com/150',
                'created_utc': time.time()
            },
            {
                'title': 'Windows Blue Screen Collection - The Greatest Hits',
                'url': 'https://v.redd.it/example2', 
                'selftext': 'Compilation of the most epic BSOD moments',
                'ups': 2300,
                'num_comments': 156,
                'thumbnail': 'https://via.placeholder.com/150',
                'created_utc': time.time()
            },
            {
                'title': 'Database Query Gone Wrong - 10 Hour Execution Time',
                'url': 'https://v.redd.it/example3',
                'selftext': 'When you forget to add WHERE clause...',
                'ups': 890,
                'num_comments': 43,
                'thumbnail': 'https://via.placeholder.com/150',
                'created_utc': time.time()
            }
        ]
        
        return example_posts[:limit]

    def extract_video_url(self, post: Dict[str, Any]) -> str:
        """Extract video URL from Reddit post"""
        url = post.get('url', '')
        
        # Check for Reddit video
        if 'v.redd.it' in url:
            return url
        
        # Check for other video platforms
        video_platforms = ['youtube.com', 'youtu.be', 'vimeo.com', 'streamable.com']
        for platform in video_platforms:
            if platform in url:
                return url
        
        return ''

    def calculate_trending_score(self, upvotes: int, comments: int, title: str) -> int:
        """Calculate trending score for content"""
        config = self.config.get('scoring', {})
        
        # Normalize scores
        upvote_score = min(upvotes / 100, 10) * config.get('upvote_weight', 0.4)
        comment_score = min(comments / 50, 10) * config.get('comment_weight', 0.3)
        
        # Keyword matching
        keyword_score = 0
        keywords = self.config.get('keywords', [])
        title_lower = title.lower()
        
        for keyword in keywords:
            if keyword in title_lower:
                keyword_score += 1
        
        keyword_score = min(keyword_score, 10) * config.get('keyword_weight', 0.3)
        
        # Calculate final score (0-100)
        total_score = (upvote_score + comment_score + keyword_score) * 10
        return min(int(total_score), 100)

    def extract_tags(self, title: str) -> List[str]:
        """Extract relevant tags from title"""
        tags = []
        keywords = self.config.get('keywords', [])
        title_lower = title.lower()
        
        # Add keyword matches as tags
        for keyword in keywords:
            if keyword in title_lower:
                tags.append(keyword)
        
        # Add tech-specific tags
        tech_terms = ['python', 'javascript', 'java', 'server', 'database', 'api', 'frontend', 'backend']
        for term in tech_terms:
            if term in title_lower:
                tags.append(term)
        
        # Add category tags
        if any(word in title_lower for word in ['error', 'crash', 'fail']):
            tags.append('error')
        if any(word in title_lower for word in ['funny', 'lol', 'epic']):
            tags.append('humor')
        
        return list(set(tags))  # Remove duplicates

    def scrape_trending_content(self) -> List[Dict[str, Any]]:
        """Scrape trending content from all configured sources"""
        all_content = []
        
        # Scrape Reddit
        subreddits = self.config.get('reddit', {}).get('subreddits', [])
        for subreddit in subreddits:
            content = self.scrape_reddit(subreddit)
            all_content.extend(content)
            time.sleep(1)  # Rate limiting
        
        # Sort by trending score
        all_content.sort(key=lambda x: x['trendingScore'], reverse=True)
        
        logging.info(f"Total content scraped: {len(all_content)}")
        return all_content

    def save_content(self, content: List[Dict[str, Any]], filename: str = None):
        """Save scraped content to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_content_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Content saved to {filename}")

def main():
    """Main scraping function"""
    scraper = ContentScraper()
    
    try:
        logging.info("Starting content scraping...")
        content = scraper.scrape_trending_content()
        
        if content:
            # Save to file
            scraper.save_content(content)
            
            # Print top results
            print(f"\nTop {min(5, len(content))} trending items:")
            for i, item in enumerate(content[:5]):
                print(f"{i+1}. {item['title']} (Score: {item['trendingScore']})")
            
            print(f"\nSUCCESS: Found {len(content)} items")
        else:
            print("No content found")
            
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
