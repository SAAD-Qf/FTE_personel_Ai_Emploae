"""
Local Agent - Platinum Tier

Runs on local machine, handling:
- Human-in-the-loop approvals
- WhatsApp session (requires local browser)
- Payments and banking (sensitive credentials stay local)
- Final send/post actions (Email, Social Media)
- Merging Cloud updates into Dashboard

Architecture:
- Reads from: /Needs_Action/Local/, /Pending_Approval/, /Updates/, /Signals/
- Writes to: /Plans/Local/, /Approved/, /Done/, Dashboard.md
- Claims files by moving to: /In_Progress/Local/
- NEVER syncs: .env, tokens, WhatsApp sessions, banking credentials

Usage:
    python local_agent.py --vault-path ./AI_Employee_Vault --continuous
"""

import argparse
import json
import logging
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LocalTask:
    """Represents a local-side task."""
    task_id: str
    task_type: str  # approval, payment, whatsapp, send_email, post_social
    source_file: str
    status: str  # pending, in_progress, completed, failed, rejected
    created: str
    updated: str
    result: Optional[Dict] = None
    error: Optional[str] = None


class LocalAgent:
    """
    Local-side AI Employee agent.
    
    Responsibilities:
    - Process human approvals (move files between folders)
    - Execute sensitive actions (payments, banking)
    - Send emails via MCP (after approval)
    - Post to social media via MCP (after approval)
    - Manage WhatsApp session (local browser automation)
    - Merge Cloud updates into Dashboard.md
    - Send signals to Cloud agent
    """

    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path).resolve()
        self.check_interval = check_interval
        self.agent_id = "local"
        
        # Domain-specific folders
        self.needs_action_local = self.vault_path / 'Needs_Action' / 'Local'
        self.in_progress_local = self.vault_path / 'In_Progress' / 'Local'
        self.pending_approval_local = self.vault_path / 'Pending_Approval' / 'Local'
        self.pending_approval_cloud = self.vault_path / 'Pending_Approval' / 'Cloud'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.plans_local = self.vault_path / 'Plans' / 'Local'
        self.updates = self.vault_path / 'Updates'
        self.signals = self.vault_path / 'Signals'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        # Ensure folders exist
        self._ensure_folders()
        
        # Setup logging
        self._setup_logging()
        
        # State tracking
        self.processed_files: set = set()
        self.task_counter = 0
        
        # MCP server connections (lazy initialization)
        self.email_mcp_available = False
        self.social_mcp_available = False
        self.payment_mcp_available = False
        
        self.logger.info("Local Agent initialized")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {check_interval}s")

    def _ensure_folders(self):
        """Ensure all required folders exist."""
        folders = [
            self.needs_action_local,
            self.in_progress_local,
            self.pending_approval_local,
            self.approved,
            self.rejected,
            self.plans_local,
            self.updates,
            self.signals,
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Configure logging."""
        log_dir = self.vault_path / 'Logs' / 'Local'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('LocalAgent')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def claim_file(self, source: Path) -> Optional[Path]:
        """
        Claim a file by moving it to In_Progress/Local/.
        Returns the new path or None if claim failed.
        """
        if not source.exists():
            return None
            
        dest = self.in_progress_local / source.name
        
        try:
            shutil.move(str(source), str(dest))
            self.logger.info(f"Claimed file: {source.name}")
            return dest
        except Exception as e:
            self.logger.warning(f"Failed to claim file {source.name}: {e}")
            return None

    def process_approval_request(self, approval_file: Path) -> Dict:
        """
        Process an approval request file.
        This is a HUMAN-in-the-loop action - waits for user decision.
        
        In production, this would present a UI notification.
        For now, it logs the approval request and waits for file movement.
        """
        try:
            content = approval_file.read_text(encoding='utf-8')
            approval_data = self._parse_approval_request(content)
            
            action_type = approval_data.get('action', 'unknown')
            
            self.logger.info(f"Approval request received: {action_type}")
            self.logger.info(f"File: {approval_file.name}")
            
            # Log the pending approval
            self._log_pending_approval(approval_data, approval_file.name)
            
            # Update dashboard with pending approval count
            self._update_dashboard_approvals()
            
            return {
                'action': 'approval_pending',
                'approval_file': approval_file.name,
                'action_type': action_type,
                'status': 'waiting_human',
                'message': f'Approval required: {approval_file.name}. Move to /Approved/ or /Rejected/',
            }
            
        except Exception as e:
            self.logger.error(f"Approval processing failed: {e}", exc_info=True)
            return {'error': str(e)}

    def _parse_approval_request(self, content: str) -> Dict:
        """Parse approval request markdown."""
        approval_data = {
            'action': 'unknown',
            'type': 'approval_request',
        }
        
        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key in ['action', 'type', 'category', 'priority']:
                            approval_data[key] = value
        
        return approval_data

    def _log_pending_approval(self, approval_data: Dict, filename: str):
        """Log pending approval for audit."""
        audit_log = self.vault_path / 'Logs' / 'Audit' / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        audit_log.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'approval_pending',
            'actor': 'local_agent',
            'file': filename,
            'action_type': approval_data.get('action', 'unknown'),
            'category': approval_data.get('category', 'unknown'),
            'priority': approval_data.get('priority', 'medium'),
        }
        
        with open(audit_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def check_approvals(self) -> List[Path]:
        """
        Check for approved/rejected files.
        Returns list of files ready for execution.
        """
        approved_files = []
        
        # Check Approved folder
        if self.approved.exists():
            for f in sorted(self.approved.glob('*.md')):
                if f.name not in self.processed_files:
                    approved_files.append(f)
        
        # Check Cloud Pending_Approval -> Approved
        cloud_approved = self.vault_path / 'Approved' / 'Cloud'
        if cloud_approved.exists():
            for f in sorted(cloud_approved.glob('*.md')):
                if f.name not in self.processed_files:
                    approved_files.append(f)
        
        return approved_files

    def execute_approved_action(self, approved_file: Path) -> Dict:
        """
        Execute an approved action.
        This is where sensitive actions happen (payments, sending, posting).
        """
        try:
            content = approved_file.read_text(encoding='utf-8')
            approval_data = self._parse_approval_request(content)
            
            action_type = approval_data.get('action', 'unknown')
            
            self.logger.info(f"Executing approved action: {action_type}")
            
            result = {
                'action': action_type,
                'source_file': approved_file.name,
                'status': 'completed',
                'executed_at': datetime.now().isoformat(),
            }
            
            if action_type == 'send_email_reply':
                result = self._execute_email_send(content, approved_file.name)
            elif action_type == 'post_social_media':
                result = self._execute_social_post(content, approved_file.name)
            elif action_type == 'payment':
                result = self._execute_payment(content, approved_file.name)
            elif action_type == 'whatsapp_message':
                result = self._execute_whatsapp_message(content, approved_file.name)
            else:
                result['status'] = 'unknown_action'
                result['message'] = f'Unknown action type: {action_type}'
            
            # Log execution
            self._log_action_execution(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Action execution failed: {e}", exc_info=True)
            return {
                'error': str(e),
                'source_file': approved_file.name,
                'status': 'failed',
            }

    def _execute_email_send(self, content: str, filename: str) -> Dict:
        """Execute email sending via MCP."""
        self.logger.info(f"Sending email (approved): {filename}")
        
        # Check if email MCP is available
        if not self._check_email_mcp():
            return {
                'action': 'send_email_reply',
                'status': 'mcp_unavailable',
                'message': 'Email MCP server not available',
                'filename': filename,
            }
        
        # Extract email details from approval file
        email_data = self._extract_email_details(content)
        
        # In production, this would call the actual MCP server
        # For now, simulate the send
        self.logger.info(f"Email sent successfully (simulated): {email_data.get('to', 'Unknown')}")
        
        return {
            'action': 'send_email_reply',
            'status': 'sent',
            'to': email_data.get('to', 'Unknown'),
            'subject': email_data.get('subject', 'Unknown'),
            'filename': filename,
            'executed_at': datetime.now().isoformat(),
        }

    def _execute_social_post(self, content: str, filename: str) -> Dict:
        """Execute social media posting via MCP."""
        self.logger.info(f"Posting to social media (approved): {filename}")
        
        # Check if social MCP is available
        if not self._check_social_mcp():
            return {
                'action': 'post_social_media',
                'status': 'mcp_unavailable',
                'message': 'Social media MCP server not available',
                'filename': filename,
            }
        
        # Extract post details
        post_data = self._extract_post_details(content)
        
        # Post to each platform
        results = {}
        for platform in post_data.get('platforms', []):
            # In production, call actual MCP server for each platform
            self.logger.info(f"Posted to {platform} (simulated)")
            results[platform] = 'posted'
        
        return {
            'action': 'post_social_media',
            'status': 'posted',
            'platforms': post_data.get('platforms', []),
            'results': results,
            'filename': filename,
            'executed_at': datetime.now().isoformat(),
        }

    def _execute_payment(self, content: str, filename: str) -> Dict:
        """Execute payment via MCP (banking integration)."""
        self.logger.info(f"Processing payment (approved): {filename}")
        
        # Check if payment MCP is available
        if not self._check_payment_mcp():
            return {
                'action': 'payment',
                'status': 'mcp_unavailable',
                'message': 'Payment MCP server not available',
                'filename': filename,
            }
        
        # Extract payment details
        payment_data = self._extract_payment_details(content)
        
        # SECURITY: All banking credentials stay local, never sync to Cloud
        self.logger.info(f"Payment processed (simulated): ${payment_data.get('amount', 0)} to {payment_data.get('recipient', 'Unknown')}")
        
        return {
            'action': 'payment',
            'status': 'processed',
            'amount': payment_data.get('amount', 0),
            'recipient': payment_data.get('recipient', 'Unknown'),
            'reference': payment_data.get('reference', 'Unknown'),
            'filename': filename,
            'executed_at': datetime.now().isoformat(),
        }

    def _execute_whatsapp_message(self, content: str, filename: str) -> Dict:
        """Execute WhatsApp message via local browser automation."""
        self.logger.info(f"Sending WhatsApp message (approved): {filename}")
        
        # WhatsApp requires local browser session - NEVER runs on Cloud
        # This uses Playwright for browser automation
        
        try:
            # Extract WhatsApp details
            wa_data = self._extract_whatsapp_details(content)
            
            # In production, this would use Playwright to send via WhatsApp Web
            self.logger.info(f"WhatsApp message sent (simulated): {wa_data.get('contact', 'Unknown')}")
            
            return {
                'action': 'whatsapp_message',
                'status': 'sent',
                'contact': wa_data.get('contact', 'Unknown'),
                'filename': filename,
                'executed_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                'action': 'whatsapp_message',
                'status': 'failed',
                'error': str(e),
                'filename': filename,
            }

    def _extract_email_details(self, content: str) -> Dict:
        """Extract email details from approval file."""
        # Simplified extraction - in production, parse full frontmatter
        return {
            'to': 'recipient@example.com',
            'subject': 'Re: Your Message',
            'body': 'Email body extracted from approval file',
        }

    def _extract_post_details(self, content: str) -> Dict:
        """Extract social media post details from approval file."""
        # Simplified extraction
        return {
            'platforms': ['facebook', 'instagram', 'twitter', 'linkedin'],
            'content': 'Post content extracted from approval file',
        }

    def _extract_payment_details(self, content: str) -> Dict:
        """Extract payment details from approval file."""
        # Simplified extraction
        return {
            'amount': 100.00,
            'recipient': 'Vendor Name',
            'reference': 'Invoice #12345',
        }

    def _extract_whatsapp_details(self, content: str) -> Dict:
        """Extract WhatsApp message details from approval file."""
        # Simplified extraction
        return {
            'contact': '+1234567890',
            'message': 'Message content extracted from approval file',
        }

    def _check_email_mcp(self) -> bool:
        """Check if email MCP server is available."""
        # In production, check actual MCP server connection
        # For now, return True if credentials exist
        creds_path = Path.home() / '.config' / 'claude-code' / 'mcp.json'
        self.email_mcp_available = creds_path.exists()
        return self.email_mcp_available

    def _check_social_mcp(self) -> bool:
        """Check if social media MCP server is available."""
        # In production, check actual MCP server connections
        self.social_mcp_available = True  # Assume available
        return self.social_mcp_available

    def _check_payment_mcp(self) -> bool:
        """Check if payment MCP server is available."""
        # In production, check Odoo MCP or payment gateway
        self.payment_mcp_available = True  # Assume available
        return self.payment_mcp_available

    def _log_action_execution(self, result: Dict):
        """Log action execution for audit."""
        audit_log = self.vault_path / 'Logs' / 'Audit' / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        audit_log.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'action_executed',
            'actor': 'local_agent',
            'action_type': result.get('action', 'unknown'),
            'status': result.get('status', 'unknown'),
            'details': result,
        }
        
        with open(audit_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def merge_cloud_update(self, update_file: Path):
        """Merge Cloud update into Dashboard.md."""
        try:
            content = update_file.read_text(encoding='utf-8')
            update_data = self._parse_cloud_update(content)
            
            update_type = update_data.get('update_type', 'unknown')
            
            self.logger.debug(f"Merging Cloud update: {update_type}")
            
            # Update dashboard with cloud activity
            self._update_dashboard_cloud_activity(update_type, update_data)
            
            # Move processed update to Done
            done_file = self.vault_path / 'Done' / f"Cloud_Update_{update_file.name}"
            shutil.move(str(update_file), str(done_file))
            
        except Exception as e:
            self.logger.error(f"Failed to merge Cloud update: {e}", exc_info=True)

    def _parse_cloud_update(self, content: str) -> Dict:
        """Parse Cloud update markdown."""
        update_data = {'update_type': 'unknown'}
        
        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key == 'update_type':
                            update_data['update_type'] = value
        
        return update_data

    def _update_dashboard_cloud_activity(self, update_type: str, update_data: Dict):
        """Update Dashboard.md with Cloud activity."""
        if not self.dashboard.exists():
            return
        
        try:
            content = self.dashboard.read_text(encoding='utf-8')
            
            # Update Cloud status section
            cloud_status = f"""## Cloud Agent Activity

| Update Type | Last Update | Status |
|-------------|-------------|--------|
| {update_type} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ✅ Active |"""

            # Replace or add cloud activity section
            if '## Cloud Agent Activity' in content:
                # Replace existing section
                import re
                pattern = r'## Cloud Agent Activity\n\n.*?(?=\n\n##|\Z)'
                content = re.sub(pattern, cloud_status, content, flags=re.DOTALL)
            else:
                # Add new section before the last footer
                content = content.rstrip() + '\n\n' + cloud_status + '\n'
            
            self.dashboard.write_text(content, encoding='utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}", exc_info=True)

    def _update_dashboard_approvals(self):
        """Update Dashboard.md with pending approval count."""
        if not self.dashboard.exists():
            return
        
        try:
            content = self.dashboard.read_text(encoding='utf-8')
            
            # Count pending approvals
            pending_count = 0
            if self.pending_approval_local.exists():
                pending_count += len(list(self.pending_approval_local.glob('*.md')))
            if self.pending_approval_cloud.exists():
                pending_count += len(list(self.pending_approval_cloud.glob('*.md')))
            
            # Update status table
            import re
            pattern = r'(\|\s*\*\*Awaiting Approval\*\*\s*\|)\s*\d+\s*\|'
            replacement = f'| **Awaiting Approval** | {pending_count} |'
            content = re.sub(pattern, replacement, content)
            
            self.dashboard.write_text(content, encoding='utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard approvals: {e}", exc_info=True)

    def send_signal(self, signal_type: str, data: Dict):
        """Send signal to Cloud agent."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"SIGNAL_{signal_type}_{timestamp}.md"
        filepath = self.signals / filename
        
        content = f"""---
type: signal
signal_type: {signal_type}
created: {datetime.now().isoformat()}
---

# Signal to Cloud Agent: {signal_type.replace('_', ' ').title()}

## Data
```json
{json.dumps(data, indent=2)}
```

---
*Sent by Local Agent*
"""
        filepath.write_text(content, encoding='utf-8')
        self.logger.debug(f"Sent signal: {filename}")

    def run_cycle(self):
        """Run one processing cycle."""
        self.logger.debug("Starting processing cycle")
        
        # Process Cloud updates
        if self.updates.exists():
            for update_file in sorted(self.updates.glob('*.md')):
                if update_file.name not in self.processed_files:
                    self.merge_cloud_update(update_file)
                    self.processed_files.add(update_file.name)
        
        # Check for approved actions
        approved_files = self.check_approvals()
        for approved_file in approved_files:
            if approved_file.name in self.processed_files:
                continue
            
            self.processed_files.add(approved_file.name)
            self.task_counter += 1
            
            # Execute the approved action
            result = self.execute_approved_action(approved_file)
            
            # Move to Done
            if result.get('status') in ['completed', 'sent', 'posted', 'processed']:
                done_file = self.vault_path / 'Done' / f"Local_{approved_file.name}"
                try:
                    shutil.move(str(approved_file), str(done_file))
                    self.logger.info(f"Completed action: {approved_file.name}")
                    
                    # Send success signal to Cloud
                    self.send_signal('approval_granted', {
                        'file': approved_file.name,
                        'action': result.get('action'),
                        'status': result.get('status'),
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to move to Done: {e}")
            else:
                self.logger.warning(f"Action failed: {result.get('status', 'unknown')}")
        
        # Process Local pending approvals (wait for human)
        if self.pending_approval_local.exists():
            for approval_file in sorted(self.pending_approval_local.glob('*.md')):
                if approval_file.name not in self.processed_files:
                    self.process_approval_request(approval_file)
                    self.processed_files.add(approval_file.name)
        
        # Process Cloud pending approvals (synced to Local)
        if self.pending_approval_cloud.exists():
            for approval_file in sorted(self.pending_approval_cloud.glob('*.md')):
                if approval_file.name not in self.processed_files:
                    self.process_approval_request(approval_file)
                    self.processed_files.add(approval_file.name)
        
        return True

    def run_continuous(self):
        """Run continuous processing loop."""
        self.logger.info("Starting continuous Local Agent loop")
        
        # Send sync_complete signal to Cloud
        self.send_signal('sync_complete', {'agent': 'local'})
        
        try:
            while True:
                should_continue = self.run_cycle()
                if not should_continue:
                    self.logger.info("Shutdown signal received")
                    break
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Local Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Local Agent error: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Local Agent - Platinum Tier')
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (daemon mode)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    agent = LocalAgent(
        vault_path=args.vault_path,
        check_interval=args.interval
    )
    
    if args.continuous:
        agent.run_continuous()
    else:
        agent.run_cycle()


if __name__ == '__main__':
    main()
