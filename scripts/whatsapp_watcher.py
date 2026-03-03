"""
WhatsApp Watcher

Monitors WhatsApp Web for new messages containing keywords and creates
action files in the Needs_Action folder for Claude Code to process.

Uses Playwright for browser automation. The browser session is persisted
so you only need to scan the QR code once.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python whatsapp_watcher.py --vault-path ./AI_Employee_Vault --session-path ./whatsapp_session
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WhatsAppMessage:
    """Represents a WhatsApp message."""
    
    def __init__(
        self,
        chat_name: str,
        message_text: str,
        timestamp: datetime,
        is_from_me: bool = False,
        is_unread: bool = True
    ):
        self.chat_name = chat_name
        self.message_text = message_text
        self.timestamp = timestamp
        self.is_from_me = is_from_me
        self.is_unread = is_unread
    
    @property
    def is_urgent(self) -> bool:
        """Check if message contains urgent keywords."""
        urgent_keywords = ['urgent', 'asap', 'emergency', 'help', 'invoice', 'payment']
        text_lower = self.message_text.lower()
        return any(kw in text_lower for kw in urgent_keywords)


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages with keywords.
    
    Uses persistent browser context to maintain login session.
    """
    
    # Keywords to watch for
    DEFAULT_KEYWORDS = ['urgent', 'asap', 'invoice', 'payment', 'help', 'meeting', 'call']
    
    # WhatsApp Web URL
    WHATSAPP_URL = 'https://web.whatsapp.com'
    
    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval: int = 60,
        keywords: Optional[List[str]] = None,
        headless: bool = True
    ):
        """
        Initialize the WhatsApp watcher.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 60)
            keywords: List of keywords to watch for (default: DEFAULT_KEYWORDS)
            headless: Run browser in headless mode (default: True)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )
        
        super().__init__(vault_path, check_interval)
        
        self.session_path = Path(session_path)
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.headless = headless
        
        # Track processed messages
        self.processed_messages: set = set()
        
        self.logger.info(f'Session path: {self.session_path}')
        self.logger.info(f'Keywords: {self.keywords}')
        self.logger.info(f'Headless: {headless}')
    
    def _wait_for_whatsapp_load(self, page: Page, timeout: int = 60000):
        """Wait for WhatsApp Web to load."""
        try:
            # Wait for chat list to appear (indicates logged in)
            page.wait_for_selector('[data-testid="chat-list"]', timeout=timeout)
            self.logger.info('WhatsApp Web loaded successfully')
            return True
        except Exception as e:
            self.logger.warning(f'Chat list not found: {e}')
            return False
    
    def _check_logged_in(self, page: Page) -> bool:
        """Check if WhatsApp Web is logged in."""
        try:
            # Look for chat list (present when logged in)
            chat_list = page.query_selector('[data-testid="chat-list"]')
            return chat_list is not None
        except Exception:
            return False
    
    def _get_unread_chats(self, page: Page) -> List[Dict]:
        """Get list of chats with unread messages."""
        unread_chats = []
        
        try:
            # Find all chat elements with unread indicator
            # WhatsApp Web structure may change, these selectors are current as of 2026
            chat_selectors = [
                '[aria-label*="unread"]',
                '[data-testid="chat-list"] [role="listitem"]',
                'div[role="listitem"]'
            ]
            
            for selector in chat_selectors:
                chats = page.query_selector_all(selector)
                if chats:
                    for chat in chats:
                        try:
                            # Extract chat info
                            name_elem = chat.query_selector('[data-testid="chat-info-name"]')
                            msg_elem = chat.query_selector('[data-testid="message-preview"]')
                            
                            if name_elem:
                                chat_name = name_elem.inner_text()
                                chat_msg = msg_elem.inner_text() if msg_elem else ''
                                
                                # Check for unread indicator
                                is_unread = 'unread' in chat.get_attribute('aria-label', '').lower()
                                
                                if chat_name and (is_unread or any(kw in chat_msg.lower() for kw in self.keywords)):
                                    unread_chats.append({
                                        'name': chat_name,
                                        'message': chat_msg,
                                        'is_unread': is_unread,
                                        'element': chat
                                    })
                        except Exception:
                            continue
                    
                    if unread_chats:
                        break
                        
        except Exception as e:
            self.logger.error(f'Error getting unread chats: {e}')
        
        return unread_chats
    
    def _detect_priority(self, message_text: str) -> str:
        """Detect message priority based on content."""
        text_lower = message_text.lower()
        
        high_keywords = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'help']
        medium_keywords = ['meeting', 'call', 'schedule', 'review', 'update']
        
        for keyword in high_keywords:
            if keyword in text_lower:
                return 'high'
        
        for keyword in medium_keywords:
            if keyword in text_lower:
                return 'medium'
        
        return 'normal'
    
    def _detect_type(self, message_text: str) -> str:
        """Detect message type based on content."""
        text_lower = message_text.lower()
        
        type_mapping = {
            'invoice': 'invoice',
            'payment': 'payment',
            'meeting': 'meeting',
            'call': 'call',
            'question': 'question',
            'urgent': 'urgent',
        }
        
        for keyword, msg_type in type_mapping.items():
            if keyword in text_lower:
                return msg_type
        
        return 'general'
    
    def check_for_updates(self) -> List[WhatsAppMessage]:
        """
        Check WhatsApp Web for new messages.
        
        Returns:
            List of new WhatsAppMessage objects
        """
        new_messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to WhatsApp
                self.logger.info('Navigating to WhatsApp Web...')
                page.goto(self.WHATSAPP_URL, wait_until='networkidle', timeout=60000)
                
                # Wait for load
                if not self._wait_for_whatsapp_load(page):
                    self.logger.warning('WhatsApp Web not fully loaded, checking anyway')
                
                # Give it a moment to render
                time.sleep(2)
                
                # Get unread chats
                unread_chats = self._get_unread_chats(page)
                
                for chat in unread_chats:
                    # Create unique message ID
                    msg_id = f"{chat['name']}:{chat['message'][:20]}"
                    
                    # Skip if already processed
                    if msg_id in self.processed_messages:
                        continue
                    
                    # Check if message contains our keywords
                    if any(kw in chat['message'].lower() for kw in self.keywords):
                        msg = WhatsAppMessage(
                            chat_name=chat['name'],
                            message_text=chat['message'],
                            timestamp=datetime.now(),
                            is_unread=chat['is_unread']
                        )
                        new_messages.append(msg)
                        self.processed_messages.add(msg_id)
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f'Error checking WhatsApp: {e}', exc_info=True)
        
        return new_messages
    
    def create_action_file(self, message: WhatsAppMessage) -> Optional[Path]:
        """
        Create an action file for a WhatsApp message.
        
        Args:
            message: The WhatsAppMessage to process
            
        Returns:
            Path to the created action file
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = message.chat_name.replace(' ', '_').replace('+', '_')[:30]
            action_filename = f'WHATSAPP_{timestamp}_{safe_name}.md'
            action_filepath = self.needs_action / action_filename
            
            # Detect priority and type
            priority = self._detect_priority(message.message_text)
            msg_type = self._detect_type(message.message_text)
            
            # Generate frontmatter
            frontmatter = self.generate_frontmatter(
                item_type='whatsapp',
                priority=priority,
                message_type=msg_type,
                chat_name=f'"{message.chat_name}"',
                received=message.timestamp.isoformat(),
                is_urgent=str(message.is_urgent).lower()
            )
            
            # Generate content
            content = f'''{frontmatter}

# WhatsApp Message: {message.chat_name}

## Message Information

| Property | Value |
|----------|-------|
| **From** | {message.chat_name} |
| **Received** | {message.timestamp.strftime('%Y-%m-%d %H:%M')} |
| **Priority** | {priority} |
| **Type** | {msg_type} |
| **Urgent** | {'Yes' if message.is_urgent else 'No'} |

## Message Content

{message.message_text}

## Suggested Actions

- [ ] Read and understand the message
- [ ] Draft a response if needed
- [ ] Take any required action
- [ ] Mark as read in WhatsApp after processing
- [ ] Move to /Done when complete

## Draft Response

*Write your draft response here for Claude to review.*

---
*Created by WhatsAppWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
            
            # Write action file
            action_filepath.write_text(content, encoding='utf-8')
            
            # Log the action
            self.log_action('whatsapp_message', {
                'chat_name': message.chat_name,
                'message_preview': message.message_text[:100],
                'priority': priority,
                'is_urgent': message.is_urgent,
                'action_file': str(action_filepath)
            })
            
            self.logger.info(f'Created action file for WhatsApp from {message.chat_name}')
            return action_filepath
            
        except Exception as e:
            self.logger.error(f'Failed to create action file: {e}', exc_info=True)
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='WhatsApp Watcher for AI Employee'
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
        required=True,
        help='Path to store browser session data'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        default=None,
        help='Keywords to watch for (default: urgent asap invoice payment help meeting call)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (default: True)'
    )
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (for QR code scan on first run)'
    )
    
    args = parser.parse_args()
    
    # First run should be visible for QR code scan
    headless = args.headless and not args.visible
    
    # Create and run watcher
    watcher = WhatsAppWatcher(
        vault_path=args.vault_path,
        session_path=args.session_path,
        check_interval=args.interval,
        keywords=args.keywords,
        headless=headless
    )
    watcher.run()


if __name__ == '__main__':
    main()
