"""
Email MCP Server

Model Context Protocol (MCP) server for sending emails via Gmail API.
This server exposes email capabilities that Claude Code can invoke.

Features:
- Send emails
- Draft emails (for review before sending)
- Search emails
- Mark emails as read

Setup:
1. Install dependencies: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
2. Create OAuth credentials in Google Cloud Console
3. Download credentials.json to this folder
4. Run once to authenticate

Usage:
    python email_mcp_server.py --credentials-path ./credentials.json

Claude Code Configuration (~/.config/claude-code/mcp.json):
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": ["D:/Hackathon_0/FTE_personel_Ai_Emploae/scripts/email_mcp_server.py"],
      "env": {
        "CREDENTIALS_PATH": "D:/Hackathon_0/FTE_personel_Ai_Emploae/scripts/credentials.json"
      }
    }
  }
}
"""

import argparse
import json
import pickle
import sys
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional, Dict, Any, List

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not available. Install with: pip install mcp")

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Gmail API not available. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")


class GmailClient:
    """Gmail API client."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self, credentials_path: str, token_path: Optional[str] = None):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path) if token_path else Path.home() / '.gmail_token.pickle'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        if self.token_path.exists():
            with open(self.token_path, 'rb') as f:
                creds = pickle.load(f)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(self._get_request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(f'Credentials not found: {self.credentials_path}')
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=False)
            
            with open(self.token_path, 'wb') as f:
                pickle.dump(creds, f)
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def _get_request(self):
        from google.auth.transport.requests import Request
        return Request()
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email."""
        message = self._create_message(to, subject, body, cc, bcc, in_reply_to)
        sent_message = self.service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        return {
            'success': True,
            'message_id': sent_message['id'],
            'thread_id': sent_message['threadId']
        }
    
    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a draft email."""
        message = self._create_message(to, subject, body, cc)
        draft = self.service.users().drafts().create(
            userId='me',
            body={'message': message}
        ).execute()
        
        return {
            'success': True,
            'draft_id': draft['id'],
            'message_id': draft['message']['id']
        }
    
    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a MIME message."""
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
            message['References'] = in_reply_to
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def search_emails(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for emails."""
        results = self.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        email_list = []
        
        for msg in messages:
            email_data = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in email_data['payload']['headers']}
            email_list.append({
                'id': msg['id'],
                'thread_id': email_data['threadId'],
                'snippet': email_data.get('snippet', ''),
                **headers
            })
        
        return email_list
    
    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark an email as read."""
        result = self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return {
            'success': True,
            'message_id': result['id']
        }


class EmailMCPServer:
    """MCP Server for email operations."""
    
    def __init__(self, credentials_path: str):
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP library not available")
        if not GMAIL_AVAILABLE:
            raise RuntimeError("Gmail API not available")
        
        self.server = Server("email-mcp")
        self.gmail_client = GmailClient(credentials_path)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP tool handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="email_send",
                    description="Send an email via Gmail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body text"
                            },
                            "cc": {
                                "type": "string",
                                "description": "CC recipients (optional)"
                            },
                            "in_reply_to": {
                                "type": "string",
                                "description": "Message ID to reply to (optional)"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                ),
                Tool(
                    name="email_create_draft",
                    description="Create a draft email for review before sending",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body text"
                            },
                            "cc": {
                                "type": "string",
                                "description": "CC recipients (optional)"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                ),
                Tool(
                    name="email_search",
                    description="Search for emails in Gmail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Gmail search query (e.g., 'is:unread from:boss@company.com')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="email_mark_read",
                    description="Mark an email as read",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "string",
                                "description": "Gmail message ID to mark as read"
                            }
                        },
                        "required": ["message_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            try:
                if name == "email_send":
                    result = self.gmail_client.send_email(
                        to=arguments["to"],
                        subject=arguments["subject"],
                        body=arguments["body"],
                        cc=arguments.get("cc"),
                        in_reply_to=arguments.get("in_reply_to")
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
                
                elif name == "email_create_draft":
                    result = self.gmail_client.create_draft(
                        to=arguments["to"],
                        subject=arguments["subject"],
                        body=arguments["body"],
                        cc=arguments.get("cc")
                    )
                    return [TextContent(
                        type="text",
                        text=f"Draft created successfully!\n\nDraft ID: {result['draft_id']}\nMessage ID: {result['message_id']}\n\nThe draft is saved in your Gmail drafts folder for review before sending."
                    )]
                
                elif name == "email_search":
                    results = self.gmail_client.search_emails(
                        query=arguments["query"],
                        max_results=arguments.get("max_results", 10)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "email_mark_read":
                    result = self.gmail_client.mark_as_read(arguments["message_id"])
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Email MCP Server for AI Employee'
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
        help='Path to store token pickle'
    )
    
    args = parser.parse_args()
    
    if not MCP_AVAILABLE:
        print("Error: MCP library not installed")
        print("Install with: pip install mcp")
        sys.exit(1)
    
    if not GMAIL_AVAILABLE:
        print("Error: Gmail API not installed")
        print("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        sys.exit(1)
    
    server = EmailMCPServer(
        credentials_path=args.credentials_path,
        token_path=args.token_path
    )
    
    print("Email MCP Server starting...", file=sys.stderr)
    import asyncio
    asyncio.run(server.run())


if __name__ == '__main__':
    main()
