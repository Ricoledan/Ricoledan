#!/usr/bin/env python3

import os
import sys
import json
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import time

def load_cached_articles():
    """Load articles from cache file if available"""
    cache_file = '.github/scripts/articles_cache.json'
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Check if cache is less than 24 hours old
                if 'timestamp' in data:
                    cache_age = time.time() - data['timestamp']
                    if cache_age < 86400:  # 24 hours
                        print(f"Using cached articles (age: {cache_age/3600:.1f} hours)")
                        return data.get('articles', [])
    except Exception as e:
        print(f"Could not load cache: {e}")
    return None

def save_articles_cache(articles):
    """Save articles to cache file"""
    cache_file = '.github/scripts/articles_cache.json'
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'articles': articles
            }, f, indent=2)
        print(f"Saved {len(articles)} articles to cache")
    except Exception as e:
        print(f"Could not save cache: {e}")

def get_fallback_articles():
    """Return empty list when RSS feed is unavailable"""
    return []

def fetch_substack_articles():
    """Fetch articles from Substack RSS feed"""
    
    # First try to use cached articles if available
    cached = load_cached_articles()
    if cached:
        return cached
    
    url = "https://ricardoledan.substack.com/feed"
    
    # Simple request attempt
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GitHub Actions Bot)',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    
    try:
        print(f"Attempting to fetch RSS feed from {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            articles = []
            for item in root.findall('.//item')[:5]:  # Get latest 5 articles
                title = item.find('title').text if item.find('title') is not None else "No Title"
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                # Parse date
                if pub_date:
                    try:
                        date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                        formatted_date = date_obj.strftime("%b %d, %Y")
                    except:
                        formatted_date = pub_date.split()[1:4]  # Fallback
                        formatted_date = " ".join(formatted_date)
                else:
                    formatted_date = "Recent"
                
                articles.append({
                    'title': title,
                    'link': link,
                    'date': formatted_date
                })
            
            print(f"Successfully fetched {len(articles)} articles")
            save_articles_cache(articles)  # Save to cache for future use
            return articles
            
        elif response.status_code == 403:
            print(f"Access blocked (403). This is expected with Cloudflare protection.")
            print("No articles fetched - will use cache if available")
            return []
        else:
            print(f"Failed with status {response.status_code}")
            return []
    
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        print("No articles fetched - will use cache if available")
        return []

def update_readme(articles):
    """Update README.md with latest articles"""
    try:
        readme_path = 'README.md'
        if not os.path.exists(readme_path):
            print(f"ERROR: {readme_path} not found")
            return False
            
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Generate articles section
        articles_md = []
        for article in articles:
            articles_md.append(f"- [{article['title']}]({article['link']}) - {article['date']}")
        
        articles_section = "\n".join(articles_md)
        
        # Replace content between markers
        pattern = r'(<!-- SUBSTACK:START -->).*?(<!-- SUBSTACK:END -->)'
        replacement = f'\\1\n{articles_section}\n\\2'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open(readme_path, 'w') as f:
            f.write(new_content)
        
        print(f"Updated README.md with {len(articles)} articles")
        return True
        
    except Exception as e:
        print(f"Error updating README: {e}")
        return False

if __name__ == "__main__":
    print(f"Working directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    
    # Try to fetch articles (from cache or fresh)
    articles = fetch_substack_articles()
    
    if articles:
        # Only update if we have real articles
        success = update_readme(articles)
        if success:
            print("✅ Successfully updated README with Substack articles")
            sys.exit(0)
        else:
            print("⚠️ Failed to update README")
            # Exit with success to not block the workflow
            sys.exit(0)
    else:
        print("⚠️ No articles available (RSS blocked and no cache), skipping update")
        # Exit with success to not block the workflow
        sys.exit(0)