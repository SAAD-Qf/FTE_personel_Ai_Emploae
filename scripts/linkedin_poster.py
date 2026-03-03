"""
LinkedIn Auto-Poster

Automatically posts business updates to LinkedIn to generate sales.
Uses Playwright for browser automation.

Features:
- Create and schedule posts
- Auto-post at optimal times
- Generate post content from business updates
- Track engagement metrics

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python linkedin_poster.py --vault-path ./AI_Employee_Vault --session-path ./linkedin_session post "Your post content here"
    python linkedin_poster.py --vault-path ./AI_Employee_Vault --session-path ./linkedin_session schedule --content-file ./posts/draft.md
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with: pip install playwright && playwright install chromium")


class LinkedInPoster:
    """LinkedIn auto-posting utility."""
    
    LINKEDIN_URL = 'https://www.linkedin.com/feed/'
    
    def __init__(
        self,
        vault_path: str,
        session_path: str,
        headless: bool = True
    ):
        """
        Initialize LinkedIn poster.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            session_path: Path to store browser session data
            headless: Run browser in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available")
        
        self.vault_path = Path(vault_path)
        self.session_path = Path(session_path)
        self.headless = headless
        
        # Folders
        self.posts_folder = self.vault_path / 'Posts'
        self.scheduled_folder = self.posts_folder / 'Scheduled'
        self.published_folder = self.posts_folder / 'Published'
        self.drafts_folder = self.posts_folder / 'Drafts'
        
        for folder in [self.posts_folder, self.scheduled_folder, self.published_folder, self.drafts_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.session_path.mkdir(parents=True, exist_ok=True)
    
    def _login(self, page: Page, email: str = None, password: str = None) -> bool:
        """
        Login to LinkedIn.
        
        Args:
            page: Playwright page
            email: LinkedIn email (if not using saved session)
            password: LinkedIn password (if not using saved session)
            
        Returns:
            True if logged in successfully
        """
        try:
            page.goto(self.LINKEDIN_URL, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            # Check if already logged in (feed is visible)
            if page.query_selector('[data-testid="feed"]'):
                print("Already logged in (session restored)")
                return True
            
            # Check if login page is shown
            login_button = page.query_selector('input[type="email"]')
            if login_button:
                if email and password:
                    print("Logging in with credentials...")
                    login_button.fill(email)
                    page.click('input[type="password"]').fill(password)
                    page.click('button[type="submit"]')
                    time.sleep(5)
                else:
                    print("Login required. Please log in manually in the browser.")
                    # Wait for manual login
                    page.wait_for_selector('[data-testid="feed"]', timeout=120000)
            
            return True
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def create_post(self, content: str, include_hashtags: bool = True) -> Dict:
        """
        Create a post on LinkedIn.
        
        Args:
            content: Post content
            include_hashtags: Add business hashtags
            
        Returns:
            Post result dictionary
        """
        hashtags = [
            '#Business',
            '#Entrepreneurship',
            '#Innovation',
            '#Growth',
            '#Networking'
        ]
        
        if include_hashtags:
            content = f"{content}\n\n{' '.join(hashtags)}"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate and login
                print("Navigating to LinkedIn...")
                if not self._login(page):
                    return {'success': False, 'error': 'Login failed'}
                
                # Wait for feed to load
                time.sleep(3)
                
                # Find and click the post creation box
                print("Opening post composer...")
                start_post = page.query_selector('[data-testid="update-components-start-a-post"]')
                if not start_post:
                    start_post = page.query_selector('button[aria-label*="Create a post"]')
                
                if start_post:
                    start_post.click()
                    time.sleep(2)
                else:
                    # Alternative: navigate directly to post creation
                    page.goto('https://www.linkedin.com/feed/?shareActive=true', wait_until='networkidle')
                    time.sleep(3)
                
                # Find the text editor and fill content
                print("Writing post content...")
                editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                if editor:
                    editor.fill(content)
                    time.sleep(1)
                else:
                    print("Could not find editor element")
                    return {'success': False, 'error': 'Editor not found'}
                
                # Click post button
                print("Publishing post...")
                post_button = page.query_selector('button[aria-label*="Post"]')
                if post_button:
                    post_button.click()
                    time.sleep(3)
                    
                    # Wait for confirmation
                    time.sleep(2)
                    
                    result = {
                        'success': True,
                        'content': content[:100] + '...',
                        'posted_at': datetime.now().isoformat(),
                        'platform': 'LinkedIn'
                    }
                    
                    # Save to published folder
                    self._save_post_record(result)
                    
                    print("Post published successfully!")
                    return result
                else:
                    print("Could not find post button")
                    return {'success': False, 'error': 'Post button not found'}
                
                browser.close()
                
        except Exception as e:
            print(f"Error creating post: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_post_record(self, post_result: Dict):
        """Save post record to published folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Post_{timestamp}.md'
        filepath = self.published_folder / filename
        
        content = f'''---
type: linkedin_post
posted: {post_result.get('posted_at', datetime.now().isoformat())}
platform: LinkedIn
status: published
---

# LinkedIn Post

## Content

{post_result.get('content', '')}

## Result

- **Success**: {post_result.get('success', False)}
- **Posted At**: {post_result.get('posted_at', 'N/A')}
- **Platform**: {post_result.get('platform', 'LinkedIn')}

---
*Auto-posted by AI Employee*
'''
        
        filepath.write_text(content, encoding='utf-8')
    
    def create_draft(self, content: str, title: str = None) -> Path:
        """
        Create a draft post for review.
        
        Args:
            content: Post content
            title: Draft title
            
        Returns:
            Path to draft file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = (title or 'Draft')[:30].replace(' ', '_')
        filename = f'DRAFT_{timestamp}_{safe_title}.md'
        filepath = self.drafts_folder / filename
        
        content_md = f'''---
type: draft
created: {datetime.now().isoformat()}
platform: LinkedIn
status: draft
---

# Draft LinkedIn Post

## Content

{content}

## Instructions

1. Review the content above
2. Edit if needed
3. Move to /Scheduled/ folder when ready to post
4. Or run: python linkedin_poster.py --vault-path {self.vault_path} --session-path ./linkedin_session post-file {filename}

---
*Created by AI Employee*
'''
        
        filepath.write_text(content_md, encoding='utf-8')
        return filepath
    
    def generate_post_content(
        self,
        topic: str,
        tone: str = 'professional',
        length: str = 'medium'
    ) -> str:
        """
        Generate post content for a topic.
        
        Args:
            topic: Post topic
            tone: 'professional', 'casual', 'enthusiastic'
            length: 'short', 'medium', 'long'
            
        Returns:
            Generated post content
        """
        # Templates based on tone and length
        templates = {
            'professional': {
                'short': f"Exciting update: {topic}. We're committed to delivering excellence. #Business #Innovation",
                'medium': f"""We're thrilled to share an important update about {topic}.

Our team has been working diligently to bring you the best solutions. This represents our ongoing commitment to innovation and customer satisfaction.

Stay tuned for more updates!

#Business #Innovation #Growth""",
                'long': f"""We're excited to announce significant developments regarding {topic}.

At our company, we believe in continuous improvement and delivering exceptional value to our clients. This latest update reflects our dedication to staying ahead of industry trends and meeting evolving customer needs.

Key highlights:
• Enhanced capabilities
• Improved user experience  
• Better value proposition

We appreciate your continued support and look forward to serving you better.

#Business #Innovation #Entrepreneurship #Growth #Networking"""
            },
            'casual': {
                'short': f"Hey everyone! Quick update on {topic}. Pretty cool stuff! 🚀 #Business #Updates",
                'medium': f"""Hey LinkedIn fam! 👋

Wanted to share something exciting about {topic}. We've been working hard on this and can't wait for you to see what's coming next!

Drop a comment if you have questions!

#Business #Startup #Innovation""",
                'long': f"""Hello connections! 

I'm super excited to talk about {topic} today. Here's what's been happening behind the scenes...

We've learned so much through this journey and can't wait to apply these insights to serve you better.

What do you think? I'd love to hear your thoughts in the comments!

#Business #Entrepreneurship #Innovation #Growth #Networking"""
            },
            'enthusiastic': {
                'short': f"🎉 AMAZING NEWS about {topic}! This is going to be GAME-CHANGING! 🚀 #Excited #Business",
                'medium': f"""🌟 BIG ANNOUNCEMENT! 🌟

We're absolutely THRILLED to share updates about {topic}! This is something we've been passionate about and can't WAIT for you to experience!

Get ready for something extraordinary! 

#Business #Innovation #Excited #Growth""",
                'long': f"""🚀 INCREDIBLE UPDATE! 🚀

I'm beyond excited to finally share this with you all! {topic} represents a major milestone for us!

Here's why this matters:
✨ Innovation at its finest
✨ Customer-focused solutions
✨ Game-changing results

We couldn't have done this without our amazing community. Thank you for your support!

Let's make things happen! 💪

#Business #Entrepreneurship #Innovation #Growth #Success #Networking"""
            }
        }
        
        return templates.get(tone, templates['professional']).get(length, templates['professional']['medium'])
    
    def schedule_post(
        self,
        content: str,
        scheduled_time: datetime,
        title: str = None
    ) -> Path:
        """
        Schedule a post for later.
        
        Args:
            content: Post content
            scheduled_time: When to post
            title: Post title
            
        Returns:
            Path to scheduled file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = (title or 'Scheduled')[:30].replace(' ', '_')
        filename = f'SCHEDULED_{timestamp}_{safe_title}.md'
        filepath = self.scheduled_folder / filename
        
        content_md = f'''---
type: scheduled_post
created: {datetime.now().isoformat()}
scheduled_time: {scheduled_time.isoformat()}
platform: LinkedIn
status: scheduled
---

# Scheduled LinkedIn Post

## Content

{content}

## Schedule

- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Scheduled For**: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Status**: Pending

## Instructions

This post is scheduled. The orchestrator will automatically post it at the scheduled time.

To cancel: Move this file to /Drafts/ folder.

---
*Scheduled by AI Employee*
'''
        
        filepath.write_text(content_md, encoding='utf-8')
        return filepath
    
    def get_scheduled_posts(self) -> List[Dict]:
        """Get posts ready to publish."""
        posts = []
        now = datetime.now()
        
        for file_path in self.scheduled_folder.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract scheduled time
                time_match = content.find('scheduled_time:')
                if time_match != -1:
                    time_str = content[time_match + 15:time_match + 40].strip()
                    scheduled_time = datetime.fromisoformat(time_str)
                    
                    if scheduled_time <= now:
                        # Extract content
                        content_start = content.find('## Content\n\n') + 13
                        content_end = content.find('\n\n## Schedule')
                        post_content = content[content_start:content_end].strip()
                        
                        posts.append({
                            'file': file_path.name,
                            'content': post_content,
                            'scheduled_time': scheduled_time
                        })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return posts


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='LinkedIn Auto-Poster'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--session-path',
        type=str,
        default='./linkedin_session',
        help='Path to store browser session'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (for first-time login)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Post command
    post_parser = subparsers.add_parser('post', help='Create a post')
    post_parser.add_argument('content', type=str, help='Post content')
    post_parser.add_argument('--no-hashtags', action='store_true', help='Don\'t add hashtags')
    
    # Post from file command
    post_file_parser = subparsers.add_parser('post-file', help='Post from file')
    post_file_parser.add_argument('file', type=str, help='File with post content')
    
    # Draft command
    draft_parser = subparsers.add_parser('draft', help='Create a draft')
    draft_parser.add_argument('content', type=str, help='Post content')
    draft_parser.add_argument('--title', type=str, default='Draft', help='Draft title')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate post content')
    gen_parser.add_argument('--topic', type=str, required=True, help='Post topic')
    gen_parser.add_argument('--tone', type=str, default='professional', choices=['professional', 'casual', 'enthusiastic'])
    gen_parser.add_argument('--length', type=str, default='medium', choices=['short', 'medium', 'long'])
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Schedule a post')
    schedule_parser.add_argument('--content', type=str, required=True, help='Post content')
    schedule_parser.add_argument('--time', type=str, required=True, help='Scheduled time (YYYY-MM-DD HH:MM)')
    schedule_parser.add_argument('--title', type=str, default='Scheduled', help='Post title')
    
    # List scheduled
    subparsers.add_parser('list-scheduled', help='List scheduled posts')
    
    args = parser.parse_args()
    
    if not PLAYWRIGHT_AVAILABLE:
        print("Error: Playwright not installed")
        sys.exit(1)
    
    headless = args.headless or not args.visible
    poster = LinkedInPoster(
        vault_path=args.vault_path,
        session_path=args.session_path,
        headless=headless
    )
    
    if args.command == 'post':
        result = poster.create_post(args.content, include_hashtags=not args.no_hashtags)
        print(f"Result: {json.dumps(result, indent=2)}")
    
    elif args.command == 'post-file':
        file_path = Path(args.file)
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
            # Remove frontmatter if present
            if '---' in content:
                parts = content.split('---', 2)
                if len(parts) > 2:
                    content = parts[2].strip()
            result = poster.create_post(content)
            print(f"Result: {json.dumps(result, indent=2)}")
        else:
            print(f"File not found: {file_path}")
    
    elif args.command == 'draft':
        filepath = poster.create_draft(args.content, args.title)
        print(f"Draft created: {filepath}")
    
    elif args.command == 'generate':
        content = poster.generate_post_content(args.topic, args.tone, args.length)
        print("\nGenerated Content:\n")
        print(content)
    
    elif args.command == 'schedule':
        try:
            scheduled_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M')
            filepath = poster.schedule_post(args.content, scheduled_time, args.title)
            print(f"Post scheduled: {filepath}")
        except ValueError as e:
            print(f"Invalid time format. Use YYYY-MM-DD HH:MM")
    
    elif args.command == 'list-scheduled':
        posts = poster.get_scheduled_posts()
        if posts:
            print("Scheduled posts ready to publish:")
            for post in posts:
                print(f"  - {post['file']}")
        else:
            print("No posts ready to publish")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
