#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

def fetch_substack_articles():
    """Fetch articles from Substack RSS feed"""
    url = "https://ricardoledan.substack.com/feed"
    
    # Use browser-like headers to avoid 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
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
        
        return articles
    
    except Exception as e:
        print(f"Error fetching articles: {e}")
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
    
    articles = fetch_substack_articles()
    if articles:
        success = update_readme(articles)
        if success:
            print("✅ Successfully updated Substack articles")
            sys.exit(0)
        else:
            print("❌ Failed to update README")
            sys.exit(1)
    else:
        print("❌ No articles found or failed to fetch")
        sys.exit(1)