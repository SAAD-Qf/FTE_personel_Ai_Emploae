"""
Approval Workflow Manager

Human-in-the-Loop (HITL) approval workflow system for sensitive actions.
Manages approval requests, tracks approvals/rejections, and executes approved actions.

Features:
- Create approval requests for sensitive actions
- Track approval status and expiration
- Execute approved actions automatically
- Notify on rejections
- Audit logging

Usage:
    python approval_manager.py --vault-path ./AI_Employee_Vault list
    python approval_manager.py --vault-path ./AI_Employee_Vault process
    python approval_manager.py --vault-path ./AI_Employee_Vault cleanup
"""

import argparse
import json
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from plan_manager import PlanManager


class ApprovalStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    EXPIRED = 'expired'
    EXECUTED = 'executed'


class ActionType(Enum):
    EMAIL_SEND = 'email_send'
    PAYMENT = 'payment'
    SOCIAL_POST = 'social_post'
    FILE_DELETE = 'file_delete'
    API_CALL = 'api_call'
    CUSTOM = 'custom'


@dataclass
class ApprovalRequest:
    """Represents an approval request."""
    file_path: Path
    action_type: str
    description: str
    details: Dict[str, Any]
    created: datetime
    expires: datetime
    status: ApprovalStatus
    related_plan: Optional[str] = None
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'ApprovalRequest':
        """Load approval request from file."""
        content = file_path.read_text(encoding='utf-8')
        
        # Parse frontmatter
        action_match = re.search(r'action:\s*(\w+)', content)
        created_match = re.search(r'created:\s*([\d\-T:]+)', content)
        expires_match = re.search(r'expires:\s*([\d\-T:]+)', content)
        status_match = re.search(r'status:\s*(\w+)', content)
        plan_match = re.search(r'related_plan:\s*"([^"]*)"', content)
        desc_match = re.search(r'# Approval Request: (.+?)(?:\n|$)', content)
        
        # Parse details section
        details = {}
        details_section = re.search(r'## Details\n\n(.*?)(?:\n##|\Z)', content, re.DOTALL)
        if details_section:
            for line in details_section.group(1).strip().split('\n'):
                if line.startswith('- **'):
                    match = re.search(r'\*\*([^*]+)\*\*:\s*(.+)', line)
                    if match:
                        key = match.group(1).lower().replace(' ', '_')
                        details[key] = match.group(2).strip()
        
        # Parse comments
        comments = []
        comments_section = re.search(r'## Comments\n\n(.*?)(?:\n---|\Z)', content, re.DOTALL)
        if comments_section:
            comments_text = comments_section.group(1).strip()
            if comments_text and comments_text != '*Add comments here*':
                comments = [c.strip() for c in comments_text.split('\n') if c.strip()]
        
        return cls(
            file_path=file_path,
            action_type=action_match.group(1) if action_match else 'custom',
            description=desc_match.group(1).strip() if desc_match else 'Unknown',
            details=details,
            created=datetime.fromisoformat(created_match.group(1)) if created_match else datetime.now(),
            expires=datetime.fromisoformat(expires_match.group(1)) if expires_match else datetime.now() + timedelta(days=1),
            status=ApprovalStatus(status_match.group(1)) if status_match else ApprovalStatus.PENDING,
            related_plan=plan_match.group(1) if plan_match else None,
            comments=comments
        )
    
    def is_expired(self) -> bool:
        """Check if request is expired."""
        return datetime.now() > self.expires and self.status != ApprovalStatus.EXECUTED
    
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        details_md = '\n'.join(f'- **{k.replace("_", " ").title()}**: {v}' for k, v in self.details.items())
        comments_md = '\n'.join(f'- {c}' for c in self.comments) if self.comments else '*Add comments here*'
        
        return f'''---
type: approval_request
action: {self.action_type}
created: {self.created.isoformat()}
expires: {self.expires.isoformat()}
status: {self.status.value}
related_plan: "{self.related_plan or ''}"
---

# Approval Request: {self.description}

## Action Details

| Property | Value |
|----------|-------|
| **Action Type** | {self.action_type} |
| **Created** | {self.created.strftime('%Y-%m-%d %H:%M:%S')} |
| **Expires** | {self.expires.strftime('%Y-%m-%d %H:%M:%S')} |
| **Status** | {self.status.value} |

## Details

{details_md if details_md else 'No additional details.'}

## Instructions

### To Approve
Move this file to the `/Approved/` folder.

### To Reject
Move this file to the `/Rejected/` folder with a comment explaining why.

### To Request Changes
Add a comment below and keep in `/Pending_Approval/`.

## Comments

{comments_md}

---
*This action requires human approval before proceeding.*
'''


class ApprovalWorkflowManager:
    """Manages the approval workflow."""
    
    # Action handlers registry
    HANDLERS: Dict[str, Callable] = {}
    
    def __init__(self, vault_path: str):
        """
        Initialize approval workflow manager.
        
        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.plans = self.vault_path / 'Plans'
        
        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.rejected, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.plan_manager = PlanManager(str(vault_path))
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default action handlers."""
        
        @self.register_handler(ActionType.EMAIL_SEND.value)
        def handle_email_send(request: ApprovalRequest) -> bool:
            """Handle email send action."""
            details = request.details
            to = details.get('to', details.get('to_email', ''))
            subject = details.get('subject', '')
            body = details.get('body', details.get('email_body', ''))
            
            # Try to send via MCP if available
            try:
                result = subprocess.run(
                    ['claude', '--prompt', f'Send email to {to} with subject "{subject}"'],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(self.vault_path)
                )
                return result.returncode == 0
            except Exception:
                # Fallback: just log
                self._log_action('email_send', {'to': to, 'subject': subject, 'status': 'logged_only'})
                return True
        
        @self.register_handler(ActionType.PAYMENT.value)
        def handle_payment(request: ApprovalRequest) -> bool:
            """Handle payment action."""
            details = request.details
            amount = details.get('amount', '0')
            recipient = details.get('recipient', details.get('to', ''))
            reference = details.get('reference', details.get('invoice', ''))
            
            # Log payment for manual processing
            self._log_action('payment', {
                'amount': amount,
                'recipient': recipient,
                'reference': reference,
                'status': 'approved_manual_processing'
            })
            return True
        
        @self.register_handler(ActionType.SOCIAL_POST.value)
        def handle_social_post(request: ApprovalRequest) -> bool:
            """Handle social media post action."""
            details = request.details
            platform = details.get('platform', 'unknown')
            content = details.get('content', details.get('message', ''))
            
            self._log_action('social_post', {
                'platform': platform,
                'content_preview': content[:100],
                'status': 'approved'
            })
            return True
        
        @self.register_handler(ActionType.FILE_DELETE.value)
        def handle_file_delete(request: ApprovalRequest) -> bool:
            """Handle file delete action."""
            details = request.details
            file_path = details.get('file_path', '')
            
            if file_path:
                target = self.vault_path / file_path
                if target.exists():
                    target.unlink()
                    self._log_action('file_delete', {'file': file_path, 'status': 'deleted'})
                    return True
            
            self._log_action('file_delete', {'file': file_path, 'status': 'not_found'})
            return True
    
    def register_handler(self, action_type: str):
        """Decorator to register an action handler."""
        def decorator(func: Callable):
            self.HANDLERS[action_type] = func
            return func
        return decorator
    
    def create_approval_request(
        self,
        action_type: str,
        description: str,
        details: Dict[str, Any],
        expires_hours: int = 24,
        related_plan: Optional[str] = None
    ) -> Path:
        """
        Create a new approval request.
        
        Args:
            action_type: Type of action
            description: Human-readable description
            details: Action details
            expires_hours: Hours until expiration
            related_plan: Related plan filename
            
        Returns:
            Path to created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_desc = description[:30].replace(' ', '_').replace('/', '_')
        filename = f'APPROVAL_{timestamp}_{safe_desc}.md'
        filepath = self.pending_approval / filename
        
        request = ApprovalRequest(
            file_path=filepath,
            action_type=action_type,
            description=description,
            details=details,
            created=datetime.now(),
            expires=datetime.now() + timedelta(hours=expires_hours),
            status=ApprovalStatus.PENDING,
            related_plan=related_plan
        )
        
        filepath.write_text(request.to_markdown(), encoding='utf-8')
        self._log_action('approval_created', {
            'file': filename,
            'action_type': action_type,
            'description': description
        })
        
        return filepath
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        requests = []
        
        if not self.pending_approval.exists():
            return requests
        
        for file_path in self.pending_approval.glob('*.md'):
            try:
                request = ApprovalRequest.from_file(file_path)
                if request.is_expired():
                    request.status = ApprovalStatus.EXPIRED
                    self._move_file(file_path, self.rejected)
                    self._log_action('approval_expired', {'file': file_path.name})
                else:
                    requests.append(request)
            except Exception as e:
                print(f'Error loading {file_path}: {e}')
        
        return requests
    
    def get_approved_requests(self) -> List[Path]:
        """Get all approved files ready for execution."""
        if not self.approved.exists():
            return []
        return sorted(
            [f for f in self.approved.iterdir() if f.suffix == '.md'],
            key=lambda f: f.stat().st_mtime
        )
    
    def process_approved(self) -> List[Dict]:
        """
        Process all approved actions.
        
        Returns:
            List of processing results
        """
        results = []
        approved_files = self.get_approved_requests()
        
        for file_path in approved_files:
            try:
                request = ApprovalRequest.from_file(file_path)
                request.status = ApprovalStatus.APPROVED
                
                # Find and execute handler
                handler = self.HANDLERS.get(request.action_type)
                
                if handler:
                    success = handler(request)
                    request.executed_at = datetime.now()
                    request.executed_by = 'approval_manager'
                    request.status = ApprovalStatus.EXECUTED if success else ApprovalStatus.REJECTED
                    
                    # Move to Done
                    self._move_file(file_path, self.done)
                    
                    results.append({
                        'file': file_path.name,
                        'action_type': request.action_type,
                        'success': success
                    })
                    
                    self._log_action('approval_executed', {
                        'file': file_path.name,
                        'action_type': request.action_type,
                        'success': success
                    })
                else:
                    # No handler, just log and move to Done
                    self._log_action('approval_no_handler', {
                        'file': file_path.name,
                        'action_type': request.action_type
                    })
                    self._move_file(file_path, self.done)
                    results.append({
                        'file': file_path.name,
                        'action_type': request.action_type,
                        'success': True,
                        'note': 'No handler registered, logged only'
                    })
                    
            except Exception as e:
                results.append({
                    'file': file_path.name,
                    'success': False,
                    'error': str(e)
                })
                self._log_action('approval_error', {
                    'file': file_path.name,
                    'error': str(e)
                })
        
        return results
    
    def reject_request(self, file_path: Path, reason: str) -> bool:
        """Reject an approval request."""
        try:
            request = ApprovalRequest.from_file(file_path)
            request.status = ApprovalStatus.REJECTED
            request.comments.append(f'Rejected: {reason}')
            
            # Update file with comment
            file_path.write_text(request.to_markdown(), encoding='utf-8')
            
            # Move to Rejected folder
            self._move_file(file_path, self.rejected)
            
            self._log_action('approval_rejected', {
                'file': file_path.name,
                'reason': reason
            })
            
            return True
        except Exception as e:
            print(f'Error rejecting request: {e}')
            return False
    
    def _move_file(self, source: Path, dest_folder: Path):
        """Move file to destination folder."""
        dest_folder.mkdir(parents=True, exist_ok=True)
        dest = dest_folder / source.name
        shutil.move(str(source), str(dest))
    
    def _log_action(self, action_type: str, details: Dict):
        """Log an action to audit log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'approval_manager',
            **details
        }
        
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def list_requests(self, status: Optional[str] = None) -> List[Dict]:
        """List approval requests."""
        requests = []
        
        # Pending
        if status is None or status == 'pending':
            for req in self.get_pending_requests():
                requests.append({
                    'file': req.file_path.name,
                    'status': 'pending',
                    'action_type': req.action_type,
                    'description': req.description,
                    'expires': req.expires.strftime('%Y-%m-%d %H:%M'),
                    'related_plan': req.related_plan or '-'
                })
        
        # Approved (waiting execution)
        if status is None or status == 'approved':
            for file_path in self.get_approved_requests():
                try:
                    req = ApprovalRequest.from_file(file_path)
                    requests.append({
                        'file': file_path.name,
                        'status': 'approved',
                        'action_type': req.action_type,
                        'description': req.description,
                        'expires': req.expires.strftime('%Y-%m-%d %H:%M'),
                        'related_plan': req.related_plan or '-'
                    })
                except Exception:
                    pass
        
        return requests
    
    def cleanup_expired(self) -> int:
        """Clean up expired approval requests."""
        count = 0
        
        for req in self.get_pending_requests():
            if req.is_expired():
                req.status = ApprovalStatus.EXPIRED
                self._move_file(req.file_path, self.rejected)
                self._log_action('approval_cleanup_expired', {'file': req.file_path.name})
                count += 1
        
        return count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Approval Workflow Manager'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List approval requests')
    list_parser.add_argument('--status', type=str, choices=['pending', 'approved', 'all'])
    
    # Process command
    subparsers.add_parser('process', help='Process approved actions')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create approval request')
    create_parser.add_argument('--type', type=str, required=True, help='Action type')
    create_parser.add_argument('--description', type=str, required=True, help='Description')
    create_parser.add_argument('--details', type=str, help='JSON details')
    create_parser.add_argument('--expires', type=int, default=24, help='Expires in hours')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up expired requests')
    
    args = parser.parse_args()
    
    manager = ApprovalWorkflowManager(vault_path=args.vault_path)
    
    if args.command == 'list':
        requests = manager.list_requests(args.status)
        if requests:
            print(f"{'File':<40} {'Status':<10} {'Type':<15} {'Description':<30} {'Expires':<20}")
            print('-' * 120)
            for req in requests:
                print(f"{req['file']:<40} {req['status']:<10} {req['action_type']:<15} {req['description'][:30]:<30} {req['expires']:<20}")
        else:
            print('No approval requests found')
    
    elif args.command == 'process':
        results = manager.process_approved()
        if results:
            print(f"Processed {len(results)} approval(s):")
            for result in results:
                status = '✓' if result.get('success') else '✗'
                note = result.get('note', '')
                print(f"  {status} {result['file']} ({result['action_type']}) {note}")
        else:
            print('No approved actions to process')
    
    elif args.command == 'create':
        details = json.loads(args.details) if args.details else {}
        filepath = manager.create_approval_request(
            action_type=args.type,
            description=args.description,
            details=details,
            expires_hours=args.expires
        )
        print(f'Created approval request: {filepath}')
    
    elif args.command == 'cleanup':
        count = manager.cleanup_expired()
        print(f'Cleaned up {count} expired request(s)')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
