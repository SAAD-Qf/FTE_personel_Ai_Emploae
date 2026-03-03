"""
Cloud Agent - Platinum Tier

Runs 24/7 on cloud VM, handling:
- Email triage and draft replies
- Social media post drafts and scheduling
- Writing approval files for Local agent
- NEVER handles: WhatsApp sessions, payments, banking, final send actions

Architecture:
- Reads from: /Needs_Action/Cloud/, /Signals/
- Writes to: /Plans/Cloud/, /Pending_Approval/Cloud/, /Updates/
- Claims files by moving to: /In_Progress/Cloud/

Usage:
    python cloud_agent.py --vault-path ./AI_Employee_Vault --continuous
"""

import argparse
import json
import logging
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CloudTask:
    """Represents a cloud-side task."""
    task_id: str
    task_type: str  # email_triage, social_draft, summary
    source_file: str
    status: str  # pending, in_progress, completed, failed
    created: str
    updated: str
    result: Optional[Dict] = None
    error: Optional[str] = None


class CloudAgent:
    """
    Cloud-side AI Employee agent.
    
    Responsibilities:
    - Email triage and draft replies (draft-only, no sending)
    - Social media post creation (draft-only, requires Local approval)
    - Business summaries and reports
    - Writing approval files for sensitive actions
    """

    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path).resolve()
        self.check_interval = check_interval
        self.agent_id = "cloud"
        
        # Domain-specific folders
        self.needs_action_cloud = self.vault_path / 'Needs_Action' / 'Cloud'
        self.in_progress_cloud = self.vault_path / 'In_Progress' / 'Cloud'
        self.pending_approval_cloud = self.vault_path / 'Pending_Approval' / 'Cloud'
        self.plans_cloud = self.vault_path / 'Plans' / 'Cloud'
        self.updates = self.vault_path / 'Updates'
        self.signals = self.vault_path / 'Signals'
        
        # Ensure folders exist
        self._ensure_folders()
        
        # Setup logging
        self._setup_logging()
        
        # State tracking
        self.processed_files: set = set()
        self.task_counter = 0
        
        self.logger.info("Cloud Agent initialized")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {check_interval}s")

    def _ensure_folders(self):
        """Ensure all required folders exist."""
        folders = [
            self.needs_action_cloud,
            self.in_progress_cloud,
            self.pending_approval_cloud,
            self.plans_cloud,
            self.updates,
            self.signals,
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Configure logging."""
        log_dir = self.vault_path / 'Logs' / 'Cloud'
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
        
        self.logger = logging.getLogger('CloudAgent')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def claim_file(self, source: Path) -> Optional[Path]:
        """
        Claim a file by moving it to In_Progress/Cloud/.
        Returns the new path or None if claim failed.
        """
        if not source.exists():
            return None
            
        dest = self.in_progress_cloud / source.name
        
        try:
            shutil.move(str(source), str(dest))
            self.logger.info(f"Claimed file: {source.name}")
            return dest
        except Exception as e:
            self.logger.warning(f"Failed to claim file {source.name}: {e}")
            return None

    def process_email_triage(self, email_file: Path) -> Dict:
        """
        Process email for triage.
        Returns draft reply and categorization (draft-only, no sending).
        """
        try:
            content = email_file.read_text(encoding='utf-8')
            
            # Extract email metadata (simplified parsing)
            email_data = self._parse_email_content(content)
            
            # Categorize email
            category = self._categorize_email(email_data)
            
            # Generate draft reply
            draft_reply = self._generate_draft_reply(email_data, category)
            
            result = {
                'action': 'email_triage',
                'category': category,
                'priority': self._assess_priority(email_data, category),
                'draft_reply': draft_reply,
                'requires_approval': category in ['complaint', 'payment_issue', 'legal'],
                'suggested_action': self._suggest_action(category),
            }
            
            self.logger.info(f"Email triage completed: {email_data.get('subject', 'Unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Email triage failed: {e}", exc_info=True)
            return {'error': str(e)}

    def _parse_email_content(self, content: str) -> Dict:
        """Parse email markdown content."""
        email_data = {
            'from': 'Unknown',
            'subject': 'Unknown',
            'body': '',
            'received': datetime.now().isoformat(),
        }
        
        # Extract frontmatter
        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key in email_data:
                            email_data[key] = value
        
        # Extract body
        if '## Email Content' in content:
            body_start = content.find('## Email Content') + len('## Email Content')
            email_data['body'] = content[body_start:].strip()
        else:
            email_data['body'] = content
        
        return email_data

    def _categorize_email(self, email_data: Dict) -> str:
        """Categorize email based on content."""
        body_lower = email_data.get('body', '').lower()
        subject_lower = email_data.get('subject', '').lower()
        
        # Priority keywords
        if any(kw in body_lower for kw in ['urgent', 'asap', 'emergency']):
            return 'urgent'
        
        # Complaint detection
        if any(kw in body_lower for kw in ['complaint', 'unhappy', 'dissatisfied', 'refund']):
            return 'complaint'
        
        # Payment/invoice detection
        if any(kw in body_lower for kw in ['invoice', 'payment', 'billing', 'overdue']):
            return 'payment'
        
        # Partnership/sales
        if any(kw in body_lower for kw in ['partnership', 'collaboration', 'proposal']):
            return 'business'
        
        # General inquiry
        if any(kw in body_lower for kw in ['question', 'help', 'information']):
            return 'inquiry'
        
        return 'general'

    def _assess_priority(self, email_data: Dict, category: str) -> str:
        """Assess email priority."""
        high_priority_categories = ['urgent', 'complaint', 'payment']
        
        if category in high_priority_categories:
            return 'high'
        
        # Check for VIP sender (simplified)
        from_email = email_data.get('from', '').lower()
        if any(vip in from_email for vip in ['ceo', 'director', 'manager']):
            return 'high'
        
        return 'medium'

    def _generate_draft_reply(self, email_data: Dict, category: str) -> str:
        """Generate a draft reply based on category."""
        from_name = email_data.get('from', 'Sender').split('@')[0]
        subject = email_data.get('subject', 'Your Message')
        
        templates = {
            'urgent': f"""Dear {from_name},

Thank you for your urgent message regarding "{subject}". I understand the importance of this matter and am giving it immediate attention.

I will review this thoroughly and get back to you within 2 hours with a detailed response.

Best regards,
[Your Name]""",
            
            'complaint': f"""Dear {from_name},

Thank you for bringing this matter to my attention. I sincerely apologize for any inconvenience you've experienced regarding "{subject}".

Your feedback is valuable to us, and I'm personally looking into this issue. I will contact you within 24 hours with a resolution.

Best regards,
[Your Name]""",
            
            'payment': f"""Dear {from_name},

Thank you for your message regarding "{subject}". I'm reviewing the payment details you've provided.

I will verify this with our accounting team and respond with confirmation within 4 business hours.

Best regards,
[Your Name]""",
            
            'business': f"""Dear {from_name},

Thank you for reaching out regarding "{subject}". This sounds like an interesting opportunity.

I'd like to learn more about this proposal. Could we schedule a call this week to discuss further?

Best regards,
[Your Name]""",
            
            'inquiry': f"""Dear {from_name},

Thank you for your inquiry about "{subject}". I'd be happy to help you with this.

Here's the information you requested:

[Provide relevant information based on Company Handbook]

Please let me know if you need any clarification.

Best regards,
[Your Name]""",
            
            'general': f"""Dear {from_name},

Thank you for your message regarding "{subject}". I've received it and will review it shortly.

I'll get back to you within 1-2 business days with a detailed response.

Best regards,
[Your Name]""",
        }
        
        return templates.get(category, templates['general'])

    def _suggest_action(self, category: str) -> str:
        """Suggest next action based on category."""
        suggestions = {
            'urgent': 'Respond within 2 hours. Consider phone follow-up.',
            'complaint': 'Review with team. Prepare resolution options. Consider compensation.',
            'payment': 'Verify with accounting. Process if valid. Send confirmation.',
            'business': 'Schedule call. Prepare proposal review.',
            'inquiry': 'Provide information from Company Handbook.',
            'general': 'Standard response within 24-48 hours.',
        }
        return suggestions.get(category, 'Review and respond appropriately.')

    def process_social_draft(self, post_file: Path) -> Dict:
        """
        Process social media post draft.
        Returns formatted posts for each platform (draft-only).
        """
        try:
            content = post_file.read_text(encoding='utf-8')
            post_data = self._parse_post_content(content)
            
            # Generate platform-specific drafts
            drafts = {
                'facebook': self._format_for_facebook(post_data),
                'instagram': self._format_for_instagram(post_data),
                'twitter': self._format_for_twitter(post_data),
                'linkedin': self._format_for_linkedin(post_data),
            }
            
            result = {
                'action': 'social_draft',
                'original_content': post_data,
                'platform_drafts': drafts,
                'requires_approval': True,  # Always require approval before posting
                'suggested_schedule': self._suggest_posting_schedule(post_data),
            }
            
            self.logger.info(f"Social draft processed: {post_data.get('topic', 'Unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Social draft processing failed: {e}", exc_info=True)
            return {'error': str(e)}

    def _parse_post_content(self, content: str) -> Dict:
        """Parse social media post markdown."""
        post_data = {
            'topic': 'General Update',
            'content': '',
            'hashtags': [],
            'media': [],
            'urgency': 'normal',
        }
        
        # Extract frontmatter
        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key == 'topic':
                            post_data['topic'] = value
                        elif key == 'urgency':
                            post_data['urgency'] = value
        
        # Extract content
        if '## Post Content' in content:
            content_start = content.find('## Post Content') + len('## Post Content')
            post_data['content'] = content[content_start:].strip()
        else:
            post_data['content'] = content
        
        # Extract hashtags
        import re
        post_data['hashtags'] = re.findall(r'#\w+', post_data['content'])
        
        return post_data

    def _format_for_facebook(self, post_data: Dict) -> str:
        """Format post for Facebook."""
        content = post_data['content']
        hashtags = ' '.join(post_data.get('hashtags', []))
        
        return f"""{content}

{hashtags}

#Facebook #BusinessUpdate"""

    def _format_for_instagram(self, post_data: Dict) -> str:
        """Format post for Instagram."""
        content = post_data['content']
        hashtags = '\n'.join(post_data.get('hashtags', []))
        
        return f"""{content}

.
.
.
{hashtags}

#Instagram #BusinessUpdate"""

    def _format_for_twitter(self, post_data: Dict) -> str:
        """Format post for Twitter/X (280 chars)."""
        content = post_data['content'][:260]  # Leave room for hashtags
        hashtags = ' '.join(post_data.get('hashtags', []))
        
        return f"{content} {hashtags}"

    def _format_for_linkedin(self, post_data: Dict) -> str:
        """Format post for LinkedIn."""
        content = post_data['content']
        hashtags = ' '.join(post_data.get('hashtags', []))
        
        return f"""{content}

{hashtags}

#LinkedIn #Professional #BusinessUpdate"""

    def _suggest_posting_schedule(self, post_data: Dict) -> Dict:
        """Suggest optimal posting schedule."""
        urgency = post_data.get('urgency', 'normal')
        
        now = datetime.now()
        
        if urgency == 'urgent':
            schedule_time = now + timedelta(hours=1)
        else:
            # Schedule for next business day 9 AM
            schedule_time = now + timedelta(days=1)
            schedule_time = schedule_time.replace(hour=9, minute=0, second=0)
        
        return {
            'suggested_time': schedule_time.isoformat(),
            'platforms': ['facebook', 'instagram', 'twitter', 'linkedin'],
            'timezone': 'UTC',
        }

    def create_approval_request(self, task_result: Dict, source_file: Path):
        """Create approval request file for Local agent."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if task_result.get('action') == 'email_triage':
            filename = f"APPROVAL_EmailReply_{timestamp}.md"
            filepath = self.pending_approval_cloud / filename
            
            content = f"""---
type: approval_request
action: send_email_reply
category: {task_result.get('category', 'general')}
priority: {task_result.get('priority', 'medium')}
created: {datetime.now().isoformat()}
source_file: {source_file.name}
status: pending
---

# Email Reply Approval Request

## Original Email
- **From:** {task_result.get('from', 'Unknown')}
- **Subject:** {task_result.get('subject', 'Unknown')}
- **Category:** {task_result.get('category', 'general')}
- **Priority:** {task_result.get('priority', 'medium')}

## Draft Reply
```
{task_result.get('draft_reply', 'No draft available')}
```

## Suggested Action
{task_result.get('suggested_action', 'Review and respond')}

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Move this file to `/Rejected/` folder.

---
*Generated by Cloud Agent - Draft Only. Requires Local approval before sending.*
"""
            filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"Created approval request: {filename}")
            
        elif task_result.get('action') == 'social_draft':
            filename = f"APPROVAL_SocialPost_{timestamp}.md"
            filepath = self.pending_approval_cloud / filename
            
            drafts = task_result.get('platform_drafts', {})
            
            content = f"""---
type: approval_request
action: post_social_media
platforms: {list(drafts.keys())}
created: {datetime.now().isoformat()}
source_file: {source_file.name}
status: pending
---

# Social Media Post Approval Request

## Topic
{task_result.get('topic', 'General Update')}

## Platform Drafts

### Facebook
```
{drafts.get('facebook', 'Not available')}
```

### Instagram
```
{drafts.get('instagram', 'Not available')}
```

### Twitter/X
```
{drafts.get('twitter', 'Not available')}
```

### LinkedIn
```
{drafts.get('linkedin', 'Not available')}
```

## Suggested Schedule
- **Time:** {task_result.get('suggested_schedule', {}).get('suggested_time', 'ASAP')}
- **Platforms:** All listed above

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Move this file to `/Rejected/` folder.

---
*Generated by Cloud Agent - Draft Only. Requires Local approval before posting.*
"""
            filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"Created approval request: {filename}")

    def write_update(self, update_type: str, data: Dict):
        """Write update to /Updates/ folder for Local agent."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"UPDATE_{update_type}_{timestamp}.md"
        filepath = self.updates / filename
        
        content = f"""---
type: cloud_update
update_type: {update_type}
created: {datetime.now().isoformat()}
---

# Cloud Agent Update: {update_type.replace('_', ' ').title()}

## Details
```json
{json.dumps(data, indent=2)}
```

---
*Generated by Cloud Agent*
"""
        filepath.write_text(content, encoding='utf-8')
        self.logger.debug(f"Wrote update: {filename}")

    def process_signal(self, signal_file: Path) -> bool:
        """Process signal from Local agent."""
        try:
            content = signal_file.read_text(encoding='utf-8')
            signal_data = self._parse_signal(content)
            
            signal_type = signal_data.get('type', 'unknown')
            
            if signal_type == 'sync_complete':
                self.logger.info("Received sync_complete signal")
                # Clear processed files cache to allow re-processing
                self.processed_files.clear()
                
            elif signal_type == 'approval_granted':
                self.logger.info("Received approval_granted signal")
                # Log the approval for audit
                self.write_update('approval_logged', {
                    'approval_file': signal_data.get('file'),
                    'action': signal_data.get('action'),
                })
                
            elif signal_type == 'shutdown':
                self.logger.info("Received shutdown signal")
                return False  # Signal to stop
            
            # Move processed signal to Done
            done_signal = self.vault_path / 'Done' / f"Cloud_{signal_file.name}"
            shutil.move(str(signal_file), str(done_signal))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Signal processing failed: {e}", exc_info=True)
            return True  # Continue running

    def _parse_signal(self, content: str) -> Dict:
        """Parse signal markdown file."""
        signal_data = {'type': 'unknown'}
        
        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key == 'type':
                            signal_data['type'] = value
                        elif key == 'action':
                            signal_data['action'] = value
                        elif key == 'file':
                            signal_data['file'] = value
        
        return signal_data

    def run_cycle(self):
        """Run one processing cycle."""
        self.logger.debug("Starting processing cycle")
        
        # Process signals from Local
        signals_folder = self.signals
        if signals_folder.exists():
            for signal_file in signals_folder.glob('*.md'):
                if signal_file.name not in self.processed_files:
                    should_continue = self.process_signal(signal_file)
                    if not should_continue:
                        return False
        
        # Process new items in Needs_Action/Cloud
        if self.needs_action_cloud.exists():
            for item_file in sorted(self.needs_action_cloud.glob('*.md')):
                if item_file.name in self.processed_files:
                    continue
                
                # Claim the file
                claimed = self.claim_file(item_file)
                if not claimed:
                    continue
                
                self.processed_files.add(item_file.name)
                self.task_counter += 1
                
                # Determine task type and process
                task_result = self._process_item(claimed)
                
                if task_result.get('error'):
                    self.logger.error(f"Task failed: {task_result['error']}")
                    task_result['status'] = 'failed'
                else:
                    task_result['status'] = 'completed'
                
                # Create approval request if needed
                if task_result.get('requires_approval', False):
                    self.create_approval_request(task_result, claimed)
                else:
                    # Write update for non-approval tasks
                    self.write_update(task_result.get('action', 'unknown'), task_result)
                
                # Move to Done
                done_file = self.vault_path / 'Done' / f"Cloud_{claimed.name}"
                try:
                    shutil.move(str(claimed), str(done_file))
                    self.logger.info(f"Completed task: {claimed.name}")
                except Exception as e:
                    self.logger.warning(f"Failed to move to Done: {e}")
        
        return True

    def _process_item(self, item_file: Path) -> Dict:
        """Process a single item based on its type."""
        try:
            content = item_file.read_text(encoding='utf-8')
            
            # Determine type from frontmatter
            item_type = self._extract_item_type(content)
            
            if item_type == 'email':
                return self.process_email_triage(item_file)
            elif item_type in ['social_post', 'post_draft']:
                return self.process_social_draft(item_file)
            else:
                # Default: summarize and categorize
                return self._summarize_item(content, item_file.name)
                
        except Exception as e:
            return {'error': str(e)}

    def _extract_item_type(self, content: str) -> str:
        """Extract item type from frontmatter."""
        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        if key.strip() == 'type':
                            return value.strip().strip('"\'')
        return 'unknown'

    def _summarize_item(self, content: str, filename: str) -> Dict:
        """Create a summary of unknown item type."""
        # Simple summarization
        lines = content.split('\n')
        summary_lines = []
        char_count = 0
        
        for line in lines:
            if char_count + len(line) < 500:
                summary_lines.append(line)
                char_count += len(line)
            else:
                break
        
        return {
            'action': 'summary',
            'filename': filename,
            'summary': '\n'.join(summary_lines[:20]),  # First 20 lines or 500 chars
            'full_length': len(content),
            'requires_approval': False,
        }

    def run_continuous(self):
        """Run continuous processing loop."""
        self.logger.info("Starting continuous Cloud Agent loop")
        
        try:
            while True:
                should_continue = self.run_cycle()
                if not should_continue:
                    self.logger.info("Shutdown signal received")
                    break
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Cloud Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Cloud Agent error: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Cloud Agent - Platinum Tier')
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
    
    agent = CloudAgent(
        vault_path=args.vault_path,
        check_interval=args.interval
    )
    
    if args.continuous:
        agent.run_continuous()
    else:
        agent.run_cycle()


if __name__ == '__main__':
    main()
