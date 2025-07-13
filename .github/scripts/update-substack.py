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
    
    # Try multiple user agents if one fails
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'curl/7.68.0',
        'python-requests/2.31.0'
    ]
    
    for i, user_agent in enumerate(user_agents):
        try:
            print(f"Attempt {i+1}: Trying with user agent: {user_agent[:50]}...")
            
            headers = {
                'User-Agent': user_agent,
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Add session for cookie persistence
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
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
                return articles
            else:
                print(f"Failed with status {response.status_code}: {response.text[:200]}")
        
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            continue
    
    print("All attempts failed")
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