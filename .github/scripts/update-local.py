#!/usr/bin/env python3
"""
Local script to fetch Substack articles and update cache.
Run this locally where Cloudflare doesn't block requests.
"""

import json
import subprocess
import sys
from datetime import datetime

def main():
    print("Fetching your latest Substack articles...")
    
    # Use curl to fetch from the archive API
    cmd = [
        'curl', '-s',
        'https://ricardoledan.substack.com/api/v1/archive?sort=new&limit=5',
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        '-H', 'Accept: application/json'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error fetching articles: {result.stderr}")
            return 1
        
        data = json.loads(result.stdout)
        
        articles = []
        for post in data[:5]:
            post_date = post.get('post_date', '')
            if post_date:
                try:
                    date_obj = datetime.strptime(post_date.split('T')[0], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%b %d, %Y")
                except:
                    formatted_date = "Recent"
            else:
                formatted_date = "Recent"
            
            articles.append({
                'title': post.get('title', 'Untitled'),
                'link': f"https://ricardoledan.substack.com/p/{post.get('slug', '')}",
                'date': formatted_date
            })
        
        # Save to cache file
        cache_data = {
            'timestamp': datetime.now().timestamp(),
            'articles': articles
        }
        
        with open('.github/scripts/articles_cache.json', 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"✅ Successfully cached {len(articles)} articles:")
        for article in articles:
            print(f"  - {article['title']} ({article['date']})")
        
        print("\nNow commit and push the cache:")
        print("  git add .github/scripts/articles_cache.json")
        print("  git commit -m 'Update Substack articles cache'")
        print("  git push")
        print("\nThen trigger the workflow:")
        print("  gh workflow run update-substack.yml")
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response: {result.stdout[:500]}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())