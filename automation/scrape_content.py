#!/usr/bin/env python3

import sys
import argparse
from content_scraper import ContentScraper

def main():
    parser = argparse.ArgumentParser(description='Content scraping script')
    args = parser.parse_args()
    
    try:
        scraper = ContentScraper()
        content = scraper.scrape_trending_content()
        
        print(f"SUCCESS: Found {len(content)} trending items")
        
        # Print top 3 items for demo
        for i, item in enumerate(content[:3]):
            print(f"{i+1}. {item['title']} (Score: {item['trendingScore']})")
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()