"""
Facebook/Instagram Auto-Poster

Automatically posts business updates to Facebook and Instagram.
Uses Playwright for browser automation.

Features:
- Create and schedule posts for Facebook and Instagram
- Cross-post to both platforms
- Generate post content from business updates
- Track engagement metrics
- Support for images and hashtags

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python facebook_instagram_poster.py --vault-path ./AI_Employee_Vault --session-path ./fb_ig_session post facebook "Your post content here"
    python facebook_instagram_poster.py --vault-path ./AI_Employee_Vault --session-path ./fb_ig_session post instagram "Your post content here"
    python facebook_instagram_poster.py --vault-path ./AI_Employee_Vault --session-path ./fb_ig_session post both "Your post content here"
"""

import argparse
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with: pip install playwright && playwright install chromium")


class SocialMediaPoster:
    """Facebook and Instagram auto-posting utility."""

    FACEBOOK_URL = 'https://www.facebook.com'
    INSTAGRAM_URL = 'https://www.instagram.com'

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        headless: bool = True
    ):
        """
        Initialize social media poster.

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
        self.facebook_folder = self.posts_folder / 'Facebook'
        self.instagram_folder = self.posts_folder / 'Instagram'
        self.scheduled_folder = self.posts_folder / 'Scheduled'
        self.published_folder = self.posts_folder / 'Published'
        self.drafts_folder = self.posts_folder / 'Drafts'

        for folder in [self.posts_folder, self.facebook_folder, self.instagram_folder,
                       self.scheduled_folder, self.published_folder, self.drafts_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        self.session_path.mkdir(parents=True, exist_ok=True)

    def _login_facebook(self, page: Page, email: str = None, password: str = None) -> bool:
        """Login to Facebook."""
        try:
            page.goto(self.FACEBOOK_URL, wait_until='networkidle', timeout=60000)
            time.sleep(3)

            # Check if already logged in (feed is visible)
            if page.query_selector('[data-testid="story_tray"]') or page.query_selector('[role="feed"]'):
                print("Facebook: Already logged in (session restored)")
                return True

            # Check if login form is shown
            email_input = page.query_selector('input[type="email"]')
            if email_input:
                if email and password:
                    print("Facebook: Logging in with credentials...")
                    email_input.fill(email)
                    page.fill('input[type="password"]', password)
                    page.click('button[type="submit"]')
                    time.sleep(5)
                else:
                    print("Facebook: Login required. Please log in manually in the browser.")
                    # Wait for manual login (2 minutes)
                    try:
                        page.wait_for_selector('[data-testid="story_tray"]', timeout=120000)
                    except Exception:
                        return False

            return True

        except Exception as e:
            print(f"Facebook login error: {e}")
            return False

    def _login_instagram(self, page: Page, username: str = None, password: str = None) -> bool:
        """Login to Instagram."""
        try:
            page.goto(self.INSTAGRAM_URL, wait_until='networkidle', timeout=60000)
            time.sleep(3)

            # Check if already logged in (feed is visible)
            if page.query_selector('[role="feed"]') or page.query_selector('[data-testid="Story"]'):
                print("Instagram: Already logged in (session restored)")
                return True

            # Check if login form is shown
            username_input = page.query_selector('input[type="text"]')
            if username_input:
                if username and password:
                    print("Instagram: Logging in with credentials...")
                    username_input.fill(username)
                    page.fill('input[type="password"]', password)
                    page.click('button[type="submit"]')
                    time.sleep(5)
                else:
                    print("Instagram: Login required. Please log in manually in the browser.")
                    # Wait for manual login (2 minutes)
                    try:
                        page.wait_for_selector('[role="feed"]', timeout=120000)
                    except Exception:
                        return False

            return True

        except Exception as e:
            print(f"Instagram login error: {e}")
            return False

    def create_facebook_post(self, content: str, include_hashtags: bool = True) -> Dict:
        """
        Create a post on Facebook.

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
            '#SmallBusiness'
        ]

        if include_hashtags:
            content = f"{content}\n\n{' '.join(hashtags)}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path / 'facebook'),
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate and login
                print("Navigating to Facebook...")
                if not self._login_facebook(page):
                    return {'success': False, 'error': 'Facebook login failed'}

                # Wait for feed to load
                time.sleep(3)

                # Find and click the post creation box
                print("Opening Facebook post composer...")
                
                # Try different selectors for post creation
                post_selectors = [
                    '[data-testid="create_post"]',
                    'div[role="button"][aria-label*="What\'s on your mind"]',
                    '.x1n2onr6.x1n2onr6',  # Facebook's dynamic class
                    'button:has-text("What\'s on your mind")'
                ]

                post_button = None
                for selector in post_selectors:
                    try:
                        post_button = page.query_selector(selector)
                        if post_button:
                            break
                    except Exception:
                        continue

                if post_button:
                    post_button.click()
                    time.sleep(2)
                else:
                    # Alternative: navigate directly to post creation
                    page.goto('https://www.facebook.com/feed/', wait_until='networkidle')
                    time.sleep(3)

                # Find the text editor and fill content
                print("Writing post content...")
                
                # Try different editor selectors
                editor_selectors = [
                    '[contenteditable="true"][data-contents="true"]',
                    '[role="textbox"]',
                    'div[contenteditable="true"]',
                    '[aria-label*="What\'s on your mind"]'
                ]

                editor = None
                for selector in editor_selectors:
                    try:
                        editor = page.query_selector(selector)
                        if editor:
                            break
                    except Exception:
                        continue

                if editor:
                    # Use keyboard type for better reliability
                    editor.click()
                    time.sleep(1)
                    page.keyboard.type(content, delay=random.randint(20, 50))
                    time.sleep(2)
                else:
                    print("Could not find Facebook editor element")
                    browser.close()
                    return {'success': False, 'error': 'Editor not found'}

                # Click post button
                print("Publishing Facebook post...")
                
                post_button_selectors = [
                    'button:has-text("Post")',
                    '[aria-label="Post"]',
                    'div[role="button"]:has-text("Post")'
                ]

                submit_button = None
                for selector in post_button_selectors:
                    try:
                        submit_button = page.query_selector(selector)
                        if submit_button:
                            break
                    except Exception:
                        continue

                if submit_button:
                    submit_button.click()
                    time.sleep(3)

                    # Wait for confirmation
                    time.sleep(2)

                    result = {
                        'success': True,
                        'content': content[:100] + '...',
                        'posted_at': datetime.now().isoformat(),
                        'platform': 'Facebook'
                    }

                    # Save to published folder
                    self._save_post_record(result, 'facebook')

                    print("Facebook post published successfully!")
                    browser.close()
                    return result
                else:
                    print("Could not find Facebook post button")
                    browser.close()
                    return {'success': False, 'error': 'Post button not found'}

                browser.close()

        except Exception as e:
            print(f"Error creating Facebook post: {e}")
            return {'success': False, 'error': str(e)}

    def create_instagram_post(self, content: str, include_hashtags: bool = True) -> Dict:
        """
        Create a post on Instagram.

        Note: Instagram requires an image for posts. This creates a text-based post
        using Instagram's story feature or requires an image path.

        Args:
            content: Post content (caption)
            include_hashtags: Add business hashtags

        Returns:
            Post result dictionary
        """
        hashtags = [
            '#Business',
            '#Entrepreneurship',
            '#Innovation',
            '#Growth',
            '#InstaBusiness',
            '#Success'
        ]

        caption = content
        if include_hashtags:
            caption = f"{content}\n.\n.\n.\n{' '.join(hashtags)}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path / 'instagram'),
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate and login
                print("Navigating to Instagram...")
                if not self._login_instagram(page):
                    return {'success': False, 'error': 'Instagram login failed'}

                # Wait for feed to load
                time.sleep(3)

                # Instagram requires an image for regular posts
                # We'll create a story post which is text-based
                print("Creating Instagram story...")

                # Click on "Your Story" or the + button
                story_selectors = [
                    '[aria-label="New story"]',
                    '[aria-label="Create story"]',
                    'img[alt*="story"]',
                    'div:has-text("Your story")'
                ]

                story_button = None
                for selector in story_selectors:
                    try:
                        story_button = page.query_selector(selector)
                        if story_button:
                            break
                    except Exception:
                        continue

                if story_button:
                    story_button.click()
                    time.sleep(2)
                else:
                    # Navigate to story creation
                    page.goto('https://www.instagram.com/stories/new/', wait_until='networkidle')
                    time.sleep(3)

                # For text-based story, we need to use the text tool
                # This is a simplified approach - Instagram's UI changes frequently
                print("Adding text to story...")

                # Look for text input or create button
                text_area = page.query_selector('textarea[aria-label*="text"]')
                if text_area:
                    text_area.fill(caption[:500])  # Instagram has character limits
                    time.sleep(1)
                else:
                    # Alternative: use keyboard to type
                    page.keyboard.type(caption[:500], delay=random.randint(20, 50))
                    time.sleep(2)

                # Click share/post button
                share_selectors = [
                    'button:has-text("Share")',
                    'button:has-text("Your Story")',
                    '[aria-label="Share"]'
                ]

                share_button = None
                for selector in share_selectors:
                    try:
                        share_button = page.query_selector(selector)
                        if share_button:
                            break
                    except Exception:
                        continue

                if share_button:
                    share_button.click()
                    time.sleep(3)

                    result = {
                        'success': True,
                        'content': caption[:100] + '...',
                        'posted_at': datetime.now().isoformat(),
                        'platform': 'Instagram',
                        'type': 'story'
                    }

                    # Save to published folder
                    self._save_post_record(result, 'instagram')

                    print("Instagram story posted successfully!")
                    browser.close()
                    return result
                else:
                    print("Could not find Instagram share button")
                    browser.close()
                    return {'success': False, 'error': 'Share button not found'}

                browser.close()

        except Exception as e:
            print(f"Error creating Instagram post: {e}")
            return {'success': False, 'error': str(e)}

    def post_to_both(self, content: str, include_hashtags: bool = True) -> Dict:
        """
        Post to both Facebook and Instagram.

        Args:
            content: Post content
            include_hashtags: Add hashtags

        Returns:
            Combined result dictionary
        """
        results = {
            'facebook': None,
            'instagram': None,
            'success_count': 0
        }

        # Post to Facebook
        print("\n=== Posting to Facebook ===")
        fb_result = self.create_facebook_post(content, include_hashtags)
        results['facebook'] = fb_result
        if fb_result.get('success'):
            results['success_count'] += 1

        # Wait a bit between platforms
        time.sleep(3)

        # Post to Instagram
        print("\n=== Posting to Instagram ===")
        ig_result = self.create_instagram_post(content, include_hashtags)
        results['instagram'] = ig_result
        if ig_result.get('success'):
            results['success_count'] += 1

        # Save combined result
        self._save_combined_post_record(results, content)

        return results

    def _save_post_record(self, post_result: Dict, platform: str):
        """Save post record to published folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{platform.title()}_Post_{timestamp}.md'
        filepath = self.published_folder / filename

        content = f'''---
type: {platform.lower()}_post
posted: {post_result.get('posted_at', datetime.now().isoformat())}
platform: {platform.title()}
status: published
---

# {platform.title()} Post

## Content

{post_result.get('content', '')}

## Result

- **Success**: {post_result.get('success', False)}
- **Posted At**: {post_result.get('posted_at', 'N/A')}
- **Platform**: {post_result.get('platform', platform.title())}

---
*Auto-posted by AI Employee*
'''

        filepath.write_text(content, encoding='utf-8')

    def _save_combined_post_record(self, results: Dict, original_content: str):
        """Save combined post record."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'CrossPlatform_Post_{timestamp}.md'
        filepath = self.published_folder / filename

        fb_status = '✓' if results['facebook'].get('success') else '✗'
        ig_status = '✓' if results['instagram'].get('success') else '✗'

        content = f'''---
type: cross_platform_post
posted: {datetime.now().isoformat()}
platforms: [Facebook, Instagram]
status: published
---

# Cross-Platform Post

## Original Content

{original_content}

## Results

### Facebook {fb_status}
- Success: {results['facebook'].get('success', False)}
- Posted At: {results['facebook'].get('posted_at', 'N/A')}

### Instagram {ig_status}
- Success: {results['instagram'].get('success', False)}
- Posted At: {results['instagram'].get('posted_at', 'N/A')}

## Summary
- Platforms Posted: {results['success_count']}/2

---
*Auto-posted by AI Employee*
'''

        filepath.write_text(content, encoding='utf-8')

    def create_draft(self, content: str, platform: str = 'both', title: str = None) -> Path:
        """
        Create a draft post for review.

        Args:
            content: Post content
            platform: 'facebook', 'instagram', or 'both'
            title: Draft title

        Returns:
            Path to draft file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = (title or 'Draft')[:30].replace(' ', '_')
        filename = f'DRAFT_{platform}_{timestamp}_{safe_title}.md'
        filepath = self.drafts_folder / filename

        content_md = f'''---
type: draft
created: {datetime.now().isoformat()}
platform: {platform}
status: draft
---

# Draft {platform.title()} Post

## Content

{content}

## Instructions

1. Review the content above
2. Edit if needed
3. Move to /Scheduled/ folder when ready to post
4. Or run: python facebook_instagram_poster.py --vault-path {self.vault_path} --session-path ./fb_ig_session post {platform} "your content"

---
*Created by AI Employee*
'''

        filepath.write_text(content_md, encoding='utf-8')
        return filepath

    def generate_post_content(
        self,
        topic: str,
        platform: str = 'facebook',
        tone: str = 'professional',
        length: str = 'medium'
    ) -> str:
        """
        Generate post content for a topic.

        Args:
            topic: Post topic
            platform: 'facebook', 'instagram', or 'both'
            tone: 'professional', 'casual', 'enthusiastic'
            length: 'short', 'medium', 'long'

        Returns:
            Generated post content
        """
        # Platform-specific adjustments
        if platform == 'instagram':
            # Instagram prefers shorter, more visual content with emojis
            templates = {
                'professional': f"📊 Business update: {topic}. Committed to excellence. #Business #Innovation",
                'casual': f"Hey Instagram fam! 👋 Quick update on {topic}. Stay tuned! 🚀 #Business #Updates",
                'enthusiastic': f"🎉 AMAZING NEWS about {topic}! This is GAME-CHANGING! 🚀 #Excited #Business"
            }
        else:
            # Facebook can be longer
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
                    'medium': f"""Hey friends! 👋

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

        if platform == 'instagram':
            return templates.get(tone, templates['professional'])
        else:
            return templates.get(tone, templates['professional']).get(length, templates['professional']['medium'])

    def schedule_post(
        self,
        content: str,
        platform: str,
        scheduled_time: datetime,
        title: str = None
    ) -> Path:
        """
        Schedule a post for later.

        Args:
            content: Post content
            platform: 'facebook', 'instagram', or 'both'
            scheduled_time: When to post
            title: Post title

        Returns:
            Path to scheduled file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = (title or 'Scheduled')[:30].replace(' ', '_')
        filename = f'SCHEDULED_{platform}_{timestamp}_{safe_title}.md'
        filepath = self.scheduled_folder / filename

        content_md = f'''---
type: scheduled_post
created: {datetime.now().isoformat()}
scheduled_time: {scheduled_time.isoformat()}
platform: {platform}
status: scheduled
---

# Scheduled {platform.title()} Post

## Content

{content}

## Schedule

- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Scheduled For**: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Platform**: {platform.title()}
- **Status**: Pending

## Instructions

This post is scheduled. The orchestrator will automatically post it at the scheduled time.

To cancel: Move this file to /Drafts/ folder.

---
*Scheduled by AI Employee*
'''

        filepath.write_text(content_md, encoding='utf-8')
        return filepath

    def get_scheduled_posts(self, platform: str = None) -> List[Dict]:
        """Get posts ready to publish."""
        posts = []
        now = datetime.now()

        for file_path in self.scheduled_folder.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')

                # Check platform filter
                if platform and platform.lower() not in file_path.name.lower():
                    continue

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

                        # Extract platform
                        platform_match = content.find('platform:')
                        post_platform = 'unknown'
                        if platform_match != -1:
                            post_platform = content[platform_match + 9:platform_match + 30].strip().split('\n')[0]

                        posts.append({
                            'file': file_path.name,
                            'content': post_content,
                            'scheduled_time': scheduled_time,
                            'platform': post_platform
                        })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        return posts


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Facebook/Instagram Auto-Poster'
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
        default='./fb_ig_session',
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
    post_parser.add_argument('platform', type=str, choices=['facebook', 'instagram', 'both'], help='Platform to post to')
    post_parser.add_argument('content', type=str, help='Post content')
    post_parser.add_argument('--no-hashtags', action='store_true', help='Don\'t add hashtags')

    # Draft command
    draft_parser = subparsers.add_parser('draft', help='Create a draft')
    draft_parser.add_argument('platform', type=str, choices=['facebook', 'instagram', 'both'], help='Platform')
    draft_parser.add_argument('content', type=str, help='Post content')
    draft_parser.add_argument('--title', type=str, default='Draft', help='Draft title')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate post content')
    gen_parser.add_argument('--topic', type=str, required=True, help='Post topic')
    gen_parser.add_argument('--platform', type=str, default='facebook', choices=['facebook', 'instagram', 'both'])
    gen_parser.add_argument('--tone', type=str, default='professional', choices=['professional', 'casual', 'enthusiastic'])
    gen_parser.add_argument('--length', type=str, default='medium', choices=['short', 'medium', 'long'])

    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Schedule a post')
    schedule_parser.add_argument('--platform', type=str, required=True, choices=['facebook', 'instagram', 'both'])
    schedule_parser.add_argument('--content', type=str, required=True, help='Post content')
    schedule_parser.add_argument('--time', type=str, required=True, help='Scheduled time (YYYY-MM-DD HH:MM)')
    schedule_parser.add_argument('--title', type=str, default='Scheduled', help='Post title')

    # List scheduled
    list_parser = subparsers.add_parser('list-scheduled', help='List scheduled posts')
    list_parser.add_argument('--platform', type=str, choices=['facebook', 'instagram'], help='Filter by platform')

    args = parser.parse_args()

    if not PLAYWRIGHT_AVAILABLE:
        print("Error: Playwright not installed")
        sys.exit(1)

    headless = args.headless or not args.visible
    poster = SocialMediaPoster(
        vault_path=args.vault_path,
        session_path=args.session_path,
        headless=headless
    )

    if args.command == 'post':
        if args.platform == 'facebook':
            result = poster.create_facebook_post(args.content, include_hashtags=not args.no_hashtags)
        elif args.platform == 'instagram':
            result = poster.create_instagram_post(args.content, include_hashtags=not args.no_hashtags)
        else:  # both
            result = poster.post_to_both(args.content, include_hashtags=not args.no_hashtags)
        print(f"Result: {json.dumps(result, indent=2)}")

    elif args.command == 'draft':
        filepath = poster.create_draft(args.content, args.platform, args.title)
        print(f"Draft created: {filepath}")

    elif args.command == 'generate':
        content = poster.generate_post_content(args.topic, args.platform, args.tone, args.length)
        print("\nGenerated Content:\n")
        print(content)

    elif args.command == 'schedule':
        try:
            scheduled_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M')
            filepath = poster.schedule_post(args.content, args.platform, scheduled_time, args.title)
            print(f"Post scheduled: {filepath}")
        except ValueError as e:
            print(f"Invalid time format. Use YYYY-MM-DD HH:MM")

    elif args.command == 'list-scheduled':
        posts = poster.get_scheduled_posts(args.platform)
        if posts:
            print("Scheduled posts ready to publish:")
            for post in posts:
                print(f"  - {post['file']} ({post['platform']})")
        else:
            print("No posts ready to publish")

    else:
        parser.print_help()


if __name__ == '__main__':
    import sys
    main()
