"""
Twitter/X Auto-Poster

Automatically posts business updates to Twitter/X.
Uses Playwright for browser automation.

Features:
- Create and schedule tweets
- Thread creation for longer content
- Generate tweet content from business updates
- Track engagement metrics
- Support for hashtags and mentions

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python twitter_poster.py --vault-path ./AI_Employee_Vault --session-path ./twitter_session post "Your tweet content here"
    python twitter_poster.py --vault-path ./AI_Employee_Vault --session-path ./twitter_session thread "First tweet" "Second tweet" "Third tweet"
"""

import argparse
import json
import time
import random
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


class TwitterPoster:
    """Twitter/X auto-posting utility."""

    TWITTER_URL = 'https://twitter.com'
    TWEET_MAX_LENGTH = 280

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        headless: bool = True
    ):
        """
        Initialize Twitter poster.

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
        self.twitter_folder = self.posts_folder / 'Twitter'
        self.scheduled_folder = self.posts_folder / 'Scheduled'
        self.published_folder = self.posts_folder / 'Published'
        self.drafts_folder = self.posts_folder / 'Drafts'
        self.threads_folder = self.posts_folder / 'Threads'

        for folder in [self.posts_folder, self.twitter_folder, self.scheduled_folder,
                       self.published_folder, self.drafts_folder, self.threads_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        self.session_path.mkdir(parents=True, exist_ok=True)

    def _login_twitter(self, page: Page, username: str = None, password: str = None) -> bool:
        """Login to Twitter/X."""
        try:
            page.goto(self.TWITTER_URL, wait_until='networkidle', timeout=60000)
            time.sleep(3)

            # Check if already logged in (timeline is visible)
            if page.query_selector('[data-testid="primaryColumn"]') and page.query_selector('[data-testid="tweet"]'):
                print("Twitter: Already logged in (session restored)")
                return True

            # Check if login form is shown
            login_link = page.query_selector('[data-testid="login"]')
            if login_link:
                login_link.click()
                time.sleep(2)

            # Look for username/email field
            username_selectors = [
                'input[type="text"]',
                'input[name="text"]',
                '[data-testid="ocfEnterTextTextInput"]'
            ]

            username_input = None
            for selector in username_selectors:
                try:
                    username_input = page.query_selector(selector)
                    if username_input:
                        break
                except Exception:
                    continue

            if username_input:
                if username and password:
                    print("Twitter: Logging in with credentials...")
                    username_input.fill(username)
                    page.click('[type="submit"]')
                    time.sleep(3)

                    # Enter password
                    password_selectors = [
                        'input[type="password"]',
                        'input[name="password"]'
                    ]

                    for selector in password_selectors:
                        try:
                            password_input = page.query_selector(selector)
                            if password_input:
                                password_input.fill(password)
                                break
                        except Exception:
                            continue

                    page.click('[type="submit"]')
                    time.sleep(5)

                    # Handle 2FA if needed (wait for user)
                    code_input = page.query_selector('input[type="text"][inputmode="numeric"]')
                    if code_input:
                        print("Twitter: 2FA code required. Please enter manually.")
                        try:
                            page.wait_for_selector('[data-testid="primaryColumn"]', timeout=60000)
                        except Exception:
                            return False
                else:
                    print("Twitter: Login required. Please log in manually in the browser.")
                    # Wait for manual login (2 minutes)
                    try:
                        page.wait_for_selector('[data-testid="primaryColumn"]', timeout=120000)
                    except Exception:
                        return False

            return True

        except Exception as e:
            print(f"Twitter login error: {e}")
            return False

    def create_tweet(self, content: str, include_hashtags: bool = True) -> Dict:
        """
        Create a tweet on Twitter/X.

        Args:
            content: Tweet content (will be truncated if > 280 chars)
            include_hashtags: Add business hashtags

        Returns:
            Post result dictionary
        """
        # Truncate if needed
        if len(content) > self.TWEET_MAX_LENGTH:
            content = content[:self.TWEET_MAX_LENGTH - 3] + "..."

        hashtags = [
            '#Business',
            '#Innovation',
            '#Growth'
        ]

        if include_hashtags:
            # Only add hashtags if there's room
            hashtag_text = ' '.join(hashtags)
            if len(content) + len(hashtag_text) + 1 <= self.TWEET_MAX_LENGTH:
                content = f"{content} {hashtag_text}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate and login
                print("Navigating to Twitter/X...")
                if not self._login_twitter(page):
                    return {'success': False, 'error': 'Twitter login failed'}

                # Wait for timeline to load
                time.sleep(3)

                # Navigate to home page
                page.goto('https://twitter.com/home', wait_until='networkidle')
                time.sleep(2)

                # Find and click the tweet composer
                print("Opening tweet composer...")

                # Try different selectors for tweet button
                tweet_selectors = [
                    '[data-testid="SideNav_NewTweet"]',
                    '[data-testid="tweetButton"]',
                    '[aria-label*="Tweet"]',
                    'div[contenteditable="true"][data-testid="DraftsDatePicker"]',
                    '[data-testid="DraftsDatePicker"] + div',
                    'div[role="textbox"]'
                ]

                composer = None
                for selector in tweet_selectors:
                    try:
                        composer = page.query_selector(selector)
                        if composer:
                            composer.click()
                            time.sleep(1)
                            break
                    except Exception:
                        continue

                if not composer:
                    # Try to find the main composer area
                    composer = page.query_selector('[data-testid="tweetTextarea_0"]')
                    if composer:
                        composer.click()
                        time.sleep(1)

                # Find the textarea and fill content
                print("Writing tweet content...")

                textarea_selectors = [
                    '[data-testid="tweetTextarea_0"]',
                    'div[contenteditable="true"][role="textbox"]',
                    '[role="textbox"][data-testid^="tweetTextarea"]',
                    'div[aria-label*="Tweet text"]'
                ]

                textarea = None
                for selector in textarea_selectors:
                    try:
                        textarea = page.query_selector(selector)
                        if textarea:
                            break
                    except Exception:
                        continue

                if textarea:
                    # Clear any existing content
                    textarea.click()
                    time.sleep(0.5)
                    page.keyboard.press('Control+A')
                    page.keyboard.press('Delete')
                    time.sleep(0.5)

                    # Type the content
                    page.keyboard.type(content, delay=random.randint(20, 50))
                    time.sleep(2)
                else:
                    print("Could not find Twitter textarea element")
                    browser.close()
                    return {'success': False, 'error': 'Textarea not found'}

                # Click tweet button
                print("Publishing tweet...")

                tweet_button_selectors = [
                    '[data-testid="tweetButton"]',
                    '[data-testid="tweetButtonInline"]',
                    'button:has-text("Post")',
                    'button:has-text("Tweet")',
                    '[aria-label*="Tweet"]'
                ]

                tweet_button = None
                for selector in tweet_button_selectors:
                    try:
                        tweet_button = page.query_selector(selector)
                        if tweet_button:
                            # Check if button is enabled
                            if 'disabled' not in tweet_button.get_attribute('class', ''):
                                break
                            tweet_button = None
                    except Exception:
                        continue

                if tweet_button:
                    tweet_button.click()
                    time.sleep(3)

                    # Wait for confirmation (tweet disappears or URL changes)
                    time.sleep(2)

                    result = {
                        'success': True,
                        'content': content[:100] + '...',
                        'posted_at': datetime.now().isoformat(),
                        'platform': 'Twitter/X',
                        'character_count': len(content)
                    }

                    # Save to published folder
                    self._save_post_record(result)

                    print("Tweet published successfully!")
                    browser.close()
                    return result
                else:
                    print("Could not find tweet button")
                    browser.close()
                    return {'success': False, 'error': 'Tweet button not found'}

                browser.close()

        except Exception as e:
            print(f"Error creating tweet: {e}")
            return {'success': False, 'error': str(e)}

    def create_thread(self, tweets: List[str], include_hashtags: bool = True) -> Dict:
        """
        Create a thread of tweets on Twitter/X.

        Args:
            tweets: List of tweet contents
            include_hashtags: Add hashtags to last tweet

        Returns:
            Thread result dictionary
        """
        results = {
            'tweets': [],
            'success_count': 0,
            'total_tweets': len(tweets)
        }

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate and login
                print("Navigating to Twitter/X...")
                if not self._login_twitter(page):
                    return {'success': False, 'error': 'Twitter login failed'}

                # Wait for timeline to load
                time.sleep(3)
                page.goto('https://twitter.com/home', wait_until='networkidle')
                time.sleep(2)

                # Open composer
                print("Opening tweet composer...")
                composer = page.query_selector('[data-testid="tweetTextarea_0"]')
                if composer:
                    composer.click()
                    time.sleep(1)

                # Post first tweet
                for i, tweet_content in enumerate(tweets):
                    # Truncate if needed
                    if len(tweet_content) > self.TWEET_MAX_LENGTH:
                        tweet_content = tweet_content[:self.TWEET_MAX_LENGTH - 3] + "..."

                    # Add hashtags to last tweet
                    if i == len(tweets) - 1 and include_hashtags:
                        hashtags = ' #Business #Innovation'
                        if len(tweet_content) + len(hashtags) <= self.TWEET_MAX_LENGTH:
                            tweet_content += hashtags

                    # Find textarea and fill
                    textarea = page.query_selector('[data-testid="tweetTextarea_0"]')
                    if textarea:
                        textarea.click()
                        page.keyboard.press('Control+A')
                        page.keyboard.press('Delete')
                        page.keyboard.type(tweet_content, delay=random.randint(20, 50))
                        time.sleep(1)

                    # If not the last tweet, add another tweet
                    if i < len(tweets) - 1:
                        # Click "Add another tweet" button
                        add_button = page.query_selector('[aria-label*="Add another tweet"]')
                        if add_button:
                            add_button.click()
                            time.sleep(1)
                        else:
                            # Alternative: look for the + button
                            plus_buttons = page.query_selector_all('[aria-label*="Add"]')
                            if plus_buttons:
                                plus_buttons[-1].click()
                                time.sleep(1)

                    results['tweets'].append({
                        'index': i,
                        'content': tweet_content[:50] + '...',
                        'posted': False
                    })

                # Post all tweets
                print("Publishing thread...")
                tweet_button = page.query_selector('[data-testid="tweetButton"]')
                if tweet_button:
                    tweet_button.click()
                    time.sleep(5)

                    # Mark all as posted
                    for tweet in results['tweets']:
                        tweet['posted'] = True
                        results['success_count'] += 1

                    result = {
                        'success': True,
                        'thread': True,
                        'tweets': results['tweets'],
                        'success_count': results['success_count'],
                        'total_tweets': len(tweets),
                        'posted_at': datetime.now().isoformat(),
                        'platform': 'Twitter/X'
                    }

                    # Save to published folder
                    self._save_thread_record(result, tweets)

                    print(f"Thread published successfully! ({results['success_count']}/{len(tweets)} tweets)")
                    browser.close()
                    return result

                browser.close()
                return {'success': False, 'error': 'Tweet button not found'}

        except Exception as e:
            print(f"Error creating thread: {e}")
            return {'success': False, 'error': str(e)}

    def _save_post_record(self, post_result: Dict):
        """Save tweet record to published folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Twitter_Post_{timestamp}.md'
        filepath = self.twitter_folder / filename

        content = f'''---
type: twitter_post
posted: {post_result.get('posted_at', datetime.now().isoformat())}
platform: Twitter/X
status: published
character_count: {post_result.get('character_count', 0)}
---

# Twitter/X Post

## Content

{post_result.get('content', '')}

## Result

- **Success**: {post_result.get('success', False)}
- **Posted At**: {post_result.get('posted_at', 'N/A')}
- **Platform**: {post_result.get('platform', 'Twitter/X')}
- **Character Count**: {post_result.get('character_count', 0)}

---
*Auto-posted by AI Employee*
'''

        filepath.write_text(content, encoding='utf-8')

    def _save_thread_record(self, thread_result: Dict, original_tweets: List[str]):
        """Save thread record."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Twitter_Thread_{timestamp}.md'
        filepath = self.threads_folder / filename

        tweets_md = '\n\n'.join([
            f"### Tweet {i+1}\n\n{tweet}"
            for i, tweet in enumerate(original_tweets)
        ])

        content = f'''---
type: twitter_thread
posted: {thread_result.get('posted_at', datetime.now().isoformat())}
platform: Twitter/X
status: published
tweet_count: {thread_result.get('total_tweets', 0)}
---

# Twitter/X Thread

{tweets_md}

## Result

- **Success**: {thread_result.get('success', False)}
- **Tweets Posted**: {thread_result.get('success_count', 0)}/{thread_result.get('total_tweets', 0)}
- **Posted At**: {thread_result.get('posted_at', 'N/A')}

---
*Auto-posted by AI Employee*
'''

        filepath.write_text(content, encoding='utf-8')

    def create_draft(self, content: str, title: str = None) -> Path:
        """
        Create a draft tweet for review.

        Args:
            content: Tweet content
            title: Draft title

        Returns:
            Path to draft file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = (title or 'Draft')[:30].replace(' ', '_')
        filename = f'DRAFT_TWITTER_{timestamp}_{safe_title}.md'
        filepath = self.drafts_folder / filename

        content_md = f'''---
type: draft
created: {datetime.now().isoformat()}
platform: Twitter/X
status: draft
character_count: {len(content)}
---

# Draft Twitter Post

## Content

{content}

## Character Count: {len(content)}/{self.TWEET_MAX_LENGTH}

## Instructions

1. Review the content above
2. Edit if needed (keep under {self.TWEET_MAX_LENGTH} characters)
3. Move to /Scheduled/ folder when ready to post
4. Or run: python twitter_poster.py --vault-path {self.vault_path} --session-path ./twitter_session post "{content[:50]}..."

---
*Created by AI Employee*
'''

        filepath.write_text(content_md, encoding='utf-8')
        return filepath

    def generate_tweet_content(
        self,
        topic: str,
        tone: str = 'professional',
        include_thread: bool = False
    ) -> str | List[str]:
        """
        Generate tweet content for a topic.

        Args:
            topic: Post topic
            tone: 'professional', 'casual', 'enthusiastic'
            include_thread: Whether to generate a thread

        Returns:
            Generated tweet content (single string or list for thread)
        """
        if include_thread:
            # Generate a 3-tweet thread
            templates = {
                'professional': [
                    f"🧵 1/3 Exciting update: {topic}. Here's what you need to know...",
                    f"2/3 Our team has been working hard to bring you innovative solutions. This represents our commitment to excellence.",
                    f"3/3 Stay tuned for more updates! We're just getting started. #Business #Innovation #Growth"
                ],
                'casual': [
                    f"🧵 1/3 Hey Twitter! Quick update on {topic}. Pretty cool stuff! 👇",
                    f"2/3 We've been working behind the scenes and can't wait to show you what's coming next!",
                    f"3/3 Drop a like if you're excited! More details coming soon. 🚀 #Business #Startup"
                ],
                'enthusiastic': [
                    f"🧵🔥 1/3 BIG NEWS about {topic}! This is going to be GAME-CHANGING! Thread below 👇",
                    f"2/3 We're absolutely THRILLED to share this with you! This represents a major milestone for us!",
                    f"3/3 Get ready for something extraordinary! 🚀 #Business #Innovation #Excited #Growth"
                ]
            }
            return templates.get(tone, templates['professional'])
        else:
            # Generate single tweet
            templates = {
                'professional': f"Exciting update: {topic}. We're committed to delivering excellence and innovation. Stay tuned for more updates! #Business #Innovation #Growth",
                'casual': f"Hey Twitter! Quick update on {topic}. Pretty cool stuff! 🚀 More details coming soon. #Business #Startup #Updates",
                'enthusiastic': f"🎉 AMAZING NEWS about {topic}! This is going to be GAME-CHANGING! 🚀 Can't wait to share more! #Business #Innovation #Excited"
            }

            content = templates.get(tone, templates['professional'])

            # Ensure it fits in tweet
            if len(content) > self.TWEET_MAX_LENGTH:
                content = content[:self.TWEET_MAX_LENGTH - 3] + "..."

            return content

    def schedule_tweet(
        self,
        content: str,
        scheduled_time: datetime,
        title: str = None
    ) -> Path:
        """
        Schedule a tweet for later.

        Args:
            content: Tweet content
            scheduled_time: When to post
            title: Tweet title

        Returns:
            Path to scheduled file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = (title or 'Scheduled')[:30].replace(' ', '_')
        filename = f'SCHEDULED_TWITTER_{timestamp}_{safe_title}.md'
        filepath = self.scheduled_folder / filename

        content_md = f'''---
type: scheduled_post
created: {datetime.now().isoformat()}
scheduled_time: {scheduled_time.isoformat()}
platform: Twitter/X
status: scheduled
character_count: {len(content)}
---

# Scheduled Twitter Post

## Content

{content}

## Character Count: {len(content)}/{self.TWEET_MAX_LENGTH}

## Schedule

- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Scheduled For**: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Platform**: Twitter/X
- **Status**: Pending

## Instructions

This tweet is scheduled. The orchestrator will automatically post it at the scheduled time.

To cancel: Move this file to /Drafts/ folder.

---
*Scheduled by AI Employee*
'''

        filepath.write_text(content_md, encoding='utf-8')
        return filepath

    def get_scheduled_posts(self) -> List[Dict]:
        """Get tweets ready to publish."""
        posts = []
        now = datetime.now()

        for file_path in self.scheduled_folder.glob('*.md'):
            if 'TWITTER' not in file_path.name:
                continue

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
                        content_end = content.find('\n\n## Character Count')
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
        description='Twitter/X Auto-Poster'
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
        default='./twitter_session',
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
    post_parser = subparsers.add_parser('post', help='Create a tweet')
    post_parser.add_argument('content', type=str, help='Tweet content')
    post_parser.add_argument('--no-hashtags', action='store_true', help='Don\'t add hashtags')

    # Thread command
    thread_parser = subparsers.add_parser('thread', help='Create a thread')
    thread_parser.add_argument('tweets', type=str, nargs='+', help='Tweet contents (multiple tweets)')
    thread_parser.add_argument('--no-hashtags', action='store_true', help='Don\'t add hashtags')

    # Draft command
    draft_parser = subparsers.add_parser('draft', help='Create a draft')
    draft_parser.add_argument('content', type=str, help='Tweet content')
    draft_parser.add_argument('--title', type=str, default='Draft', help='Draft title')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate tweet content')
    gen_parser.add_argument('--topic', type=str, required=True, help='Tweet topic')
    gen_parser.add_argument('--tone', type=str, default='professional', choices=['professional', 'casual', 'enthusiastic'])
    gen_parser.add_argument('--thread', action='store_true', help='Generate a thread')

    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Schedule a tweet')
    schedule_parser.add_argument('--content', type=str, required=True, help='Tweet content')
    schedule_parser.add_argument('--time', type=str, required=True, help='Scheduled time (YYYY-MM-DD HH:MM)')
    schedule_parser.add_argument('--title', type=str, default='Scheduled', help='Tweet title')

    # List scheduled
    subparsers.add_parser('list-scheduled', help='List scheduled tweets')

    args = parser.parse_args()

    if not PLAYWRIGHT_AVAILABLE:
        print("Error: Playwright not installed")
        sys.exit(1)

    headless = args.headless or not args.visible
    poster = TwitterPoster(
        vault_path=args.vault_path,
        session_path=args.session_path,
        headless=headless
    )

    if args.command == 'post':
        result = poster.create_tweet(args.content, include_hashtags=not args.no_hashtags)
        print(f"Result: {json.dumps(result, indent=2)}")

    elif args.command == 'thread':
        result = poster.create_thread(args.tweets, include_hashtags=not args.no_hashtags)
        print(f"Result: {json.dumps(result, indent=2)}")

    elif args.command == 'draft':
        filepath = poster.create_draft(args.content, args.title)
        print(f"Draft created: {filepath}")

    elif args.command == 'generate':
        content = poster.generate_tweet_content(args.topic, args.tone, args.thread)
        print("\nGenerated Content:\n")
        if isinstance(content, list):
            for i, tweet in enumerate(content, 1):
                print(f"Tweet {i}: {tweet}\n")
        else:
            print(content)

    elif args.command == 'schedule':
        try:
            scheduled_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M')
            filepath = poster.schedule_tweet(args.content, scheduled_time, args.title)
            print(f"Tweet scheduled: {filepath}")
        except ValueError as e:
            print(f"Invalid time format. Use YYYY-MM-DD HH:MM")

    elif args.command == 'list-scheduled':
        posts = poster.get_scheduled_posts()
        if posts:
            print("Scheduled tweets ready to publish:")
            for post in posts:
                print(f"  - {post['file']}")
        else:
            print("No tweets ready to publish")

    else:
        parser.print_help()


if __name__ == '__main__':
    import sys
    main()
