"""
Gmail Watcher

Monitors Gmail for new important/unread emails and creates action files
in the Needs_Action folder for Claude Code to process.

Requires Gmail API credentials setup:
1. Go to https://console.cloud.google.com/
2. Create a project and enable Gmail API
3. Create OAuth 2.0 credentials
4. Download credentials.json to scripts/ folder
5. First run will open browser for authentication

Usage:
    python gmail_watcher.py --vault-path ./AI_Employee_Vault --credentials-path ./scripts/credentials.json
"""

import argparse
import os
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email import message_from_bytes
from email.header import decode_header

from base_watcher import BaseWatcher

# Gmail API imports (install: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib)
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


class GmailMessage:
    """Represents a Gmail message."""
    
    def __init__(self, message_id: str, thread_id: str, snippet: str, headers: Dict, body: str = ''):
        self.message_id = message_id
        self.thread_id = thread_id
        self.snippet = snippet
        self.headers = headers
        self.body = body
        
    @property
    def from_email(self) -> str:
        return self.headers.get('From', 'Unknown')
    
    @property
    def to_email(self) -> str:
        return self.headers.get('To', '')
    
    @property
    def subject(self) -> str:
        return self.headers.get('Subject', 'No Subject')
    
    @property
    def date(self) -> str:
        return self.headers.get('Date', '')
    
    @property
    def is_important(self) -> bool:
        labels = self.headers.get('Labels', [])
        return 'IMPORTANT' in labels or 'INBOX' in labels


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new important/unread emails.
    
    Creates action files in Needs_Action folder for Claude to process.
    """
    
    # OAuth scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
              'https://www.googleapis.com/auth/gmail.send',
              'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        token_path: Optional[str] = None,
        check_interval: int = 120,
        max_results: int = 10
    ):
        """
        Initialize the Gmail watcher.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            credentials_path: Path to OAuth credentials JSON file
            token_path: Path to store token pickle (default: .gmail_token.pickle)
            check_interval: Seconds between checks (default: 120)
            max_results: Maximum emails to fetch per check (default: 10)
        """
        if not GMAIL_AVAILABLE:
            raise ImportError(
                "Gmail API libraries not installed. "
                "Install with: pip install --upgrade google-api-python-client "
                "google-auth-httplib2 google-auth-oauthlib"
            )
        
        super().__init__(vault_path, check_interval)
        
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path) if token_path else self.vault_path / '.gmail_token.pickle'
        self.max_results = max_results
        self.service = None
        
        # Load or create credentials
        self._authenticate()
        
        self.logger.info(f'Credentials: {self.credentials_path}')
        self.logger.info(f'Max results per check: {self.max_results}')
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        try:
            creds = None
            
            # Load token if exists
            if self.token_path.exists():
                with open(self.token_path, 'rb') as f:
                    creds = pickle.load(f)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info('Refreshing expired token')
                    creds.refresh(self._get_request())
                else:
                    self.logger.info('Starting OAuth flow')
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0, open_browser=False)
                    self.logger.info('OAuth completed. Please run again to use saved token.')
                    # Save for next run
                    with open(self.token_path, 'wb') as f:
                        pickle.dump(creds, f)
                    exit(0)
                
                # Save token
                with open(self.token_path, 'wb') as f:
                    pickle.dump(creds, f)
            
            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Gmail API authenticated successfully')
            
        except FileNotFoundError:
            self.logger.error(f'Credentials file not found: {self.credentials_path}')
            self.logger.error('Download credentials.json from Google Cloud Console')
            raise
        except Exception as e:
            self.logger.error(f'Authentication failed: {e}')
            raise
    
    def _get_request(self):
        """Get request builder for token refresh."""
        from google.auth.transport.requests import Request
        return Request()
    
    def _decode_header(self, header_value: str) -> str:
        """Decode MIME header."""
        if not header_value:
            return ''
        
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except LookupError:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        
        return ' '.join(decoded_parts)
    
    def _get_email_body(self, message_data: Dict) -> str:
        """Extract email body from message data."""
        body = ''
        
        try:
            payload = message_data.get('payload', {})
            parts = payload.get('parts', [])
            
            if parts:
                # Multipart message
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        body_data = part.get('body', {}).get('data', '')
                        if body_data:
                            import base64
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
                            break
            else:
                # Simple message
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    import base64
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
        except Exception as e:
            self.logger.warning(f'Could not extract body: {e}')
            body = message_data.get('snippet', '')
        
        return body
    
    def _detect_priority(self, subject: str, from_email: str, snippet: str) -> str:
        """Detect email priority based on content."""
        text = f"{subject} {from_email} {snippet}".lower()
        
        high_keywords = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'important', 'action required']
        medium_keywords = ['meeting', 'schedule', 'review', 'update', 'reminder', 'follow-up']
        
        for keyword in high_keywords:
            if keyword in text:
                return 'high'
        
        for keyword in medium_keywords:
            if keyword in text:
                return 'medium'
        
        return 'normal'
    
    def _detect_type(self, subject: str, snippet: str) -> str:
        """Detect email type based on content."""
        text = f"{subject} {snippet}".lower()
        
        type_mapping = {
            'invoice': 'invoice',
            'receipt': 'receipt',
            'payment': 'payment',
            'meeting': 'meeting',
            'interview': 'interview',
            'proposal': 'proposal',
            'contract': 'contract',
            'question': 'question',
            'inquiry': 'inquiry',
        }
        
        for keyword, email_type in type_mapping.items():
            if keyword in text:
                return email_type
        
        return 'general'
    
    def check_for_updates(self) -> List[GmailMessage]:
        """
        Check Gmail for new important/unread emails.
        
        Returns:
            List of new GmailMessage objects
        """
        new_messages = []
        
        try:
            # Search for unread important messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important',
                maxResults=self.max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            for msg in messages:
                # Skip if already processed
                if msg['id'] in self.processed_ids:
                    continue
                
                # Get full message details
                message_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = {}
                for header in message_data['payload'].get('headers', []):
                    name = header['name']
                    value = self._decode_header(header['value'])
                    headers[name] = value
                
                # Add labels
                headers['Labels'] = message_data.get('labelIds', [])
                
                # Get body
                body = self._get_email_body(message_data)
                
                # Create message object
                gmail_msg = GmailMessage(
                    message_id=msg['id'],
                    thread_id=message_data.get('threadId', ''),
                    snippet=message_data.get('snippet', ''),
                    headers=headers,
                    body=body
                )
                
                new_messages.append(gmail_msg)
                self.processed_ids.add(msg['id'])
                
        except HttpError as error:
            self.logger.error(f'Gmail API error: {error}')
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}', exc_info=True)
        
        return new_messages
    
    def create_action_file(self, message: GmailMessage) -> Optional[Path]:
        """
        Create an action file for a Gmail message.
        
        Args:
            message: The GmailMessage to process
            
        Returns:
            Path to the created action file
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_subject = message.subject[:50].replace(' ', '_').replace('/', '_')
            safe_from = message.from_email.split('@')[0].replace('.', '_')
            action_filename = f'GMAIL_{timestamp}_{safe_from}_{safe_subject}.md'
            action_filepath = self.needs_action / action_filename
            
            # Detect priority and type
            priority = self._detect_priority(message.subject, message.from_email, message.snippet)
            email_type = self._detect_type(message.subject, message.snippet)
            
            # Parse date
            try:
                received_date = datetime.strptime(message.date.split(',')[0].strip(), '%d %b %Y').strftime('%Y-%m-%d %H:%M')
            except Exception:
                received_date = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Generate frontmatter
            frontmatter = self.generate_frontmatter(
                item_type='email',
                priority=priority,
                email_type=email_type,
                from_email=f'"{message.from_email}"',
                to_email=f'"{message.to_email}"',
                subject=f'"{message.subject}"',
                received=received_date,
                message_id=f'"{message.message_id}"',
                thread_id=f'"{message.thread_id}"'
            )
            
            # Generate content
            content = f'''{frontmatter}

# Email: {message.subject}

## Email Information

| Property | Value |
|----------|-------|
| **From** | {message.from_email} |
| **To** | {message.to_email} |
| **Subject** | {message.subject} |
| **Received** | {received_date} |
| **Priority** | {priority} |
| **Type** | {email_type} |

## Email Content

{message.body if message.body else message.snippet}

## Suggested Actions

- [ ] Read and understand the email
- [ ] Draft a response if needed
- [ ] Take any required action
- [ ] Mark as read in Gmail after processing
- [ ] Move to /Done when complete

## Draft Response

*Write your draft response here for Claude to review and send.*

---
*Created by GmailWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Message ID: {message.message_id}*
'''
            
            # Write action file
            action_filepath.write_text(content, encoding='utf-8')
            
            # Log the action
            self.log_action('email_received', {
                'message_id': message.message_id,
                'from': message.from_email,
                'subject': message.subject,
                'priority': priority,
                'action_file': str(action_filepath)
            })
            
            self.logger.info(f'Created action file for email from {message.from_email}')
            return action_filepath
            
        except Exception as e:
            self.logger.error(f'Failed to create action file: {e}', exc_info=True)
            return None
    
    def mark_as_read(self, message_id: str):
        """Mark a Gmail message as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.info(f'Marked message {message_id} as read')
        except Exception as e:
            self.logger.error(f'Failed to mark as read: {e}')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Gmail Watcher for AI Employee'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--credentials-path',
        type=str,
        required=True,
        help='Path to Gmail OAuth credentials JSON file'
    )
    parser.add_argument(
        '--token-path',
        type=str,
        default=None,
        help='Path to store token pickle (default: .gmail_token.pickle in vault)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=120,
        help='Check interval in seconds (default: 120)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum emails to fetch per check (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Create and run watcher
    watcher = GmailWatcher(
        vault_path=args.vault_path,
        credentials_path=args.credentials_path,
        token_path=args.token_path,
        check_interval=args.interval,
        max_results=args.max_results
    )
    watcher.run()


if __name__ == '__main__':
    main()
