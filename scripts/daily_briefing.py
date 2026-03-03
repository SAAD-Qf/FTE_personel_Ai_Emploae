"""
Daily Briefing Generator

Generates a daily CEO briefing summarizing yesterday's activities,
pending items, and business metrics.

Usage:
    python daily_briefing.py --vault-path ./AI_Employee_Vault
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any


class DailyBriefingGenerator:
    """Generates daily CEO briefings."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.done_folder = self.vault_path / 'Done'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.briefings_folder = self.vault_path / 'Briefings'
        self.logs_folder = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        self.business_goals = self.vault_path / 'Business_Goals.md'
        
        self.briefings_folder.mkdir(parents=True, exist_ok=True)
    
    def generate_briefing(self, date: str = None) -> Path:
        """
        Generate a daily briefing.
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to yesterday
            
        Returns:
            Path to generated briefing file
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Gather data
        completed_items = self._get_completed_items(date)
        pending_items = self._get_pending_items()
        approval_items = self._get_pending_approvals()
        metrics = self._calculate_metrics(date)
        logs = self._get_logs(date)
        
        # Generate briefing
        filename = f'Briefing_{date}.md'
        filepath = self.briefings_folder / filename
        
        content = self._format_briefing(
            date=date,
            completed=completed_items,
            pending=pending_items,
            approvals=approval_items,
            metrics=metrics,
            logs=logs
        )
        
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    def _get_completed_items(self, date: str) -> List[Dict]:
        """Get items completed on date."""
        items = []
        
        if not self.done_folder.exists():
            return items
        
        for file_path in self.done_folder.glob('*.md'):
            try:
                # Check if file was modified on the date
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime.strftime('%Y-%m-%d') == date:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Extract type and description
                    type_match = re.search(r'type:\s*(\w+)', content)
                    subject_match = re.search(r'(?:subject|original_name):\s*"([^"]+)"', content)
                    
                    items.append({
                        'file': file_path.name,
                        'type': type_match.group(1) if type_match else 'unknown',
                        'description': subject_match.group(1) if subject_match else file_path.stem,
                        'completed_at': mtime.strftime('%H:%M')
                    })
            except Exception:
                continue
        
        return items
    
    def _get_pending_items(self) -> List[Dict]:
        """Get currently pending items."""
        items = []
        
        if not self.needs_action.exists():
            return items
        
        for file_path in self.needs_action.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                type_match = re.search(r'type:\s*(\w+)', content)
                priority_match = re.search(r'priority:\s*(\w+)', content)
                subject_match = re.search(r'(?:subject|original_name):\s*"([^"]+)"', content)
                
                items.append({
                    'file': file_path.name,
                    'type': type_match.group(1) if type_match else 'unknown',
                    'priority': priority_match.group(1) if priority_match else 'normal',
                    'description': subject_match.group(1) if subject_match else file_path.stem
                })
            except Exception:
                continue
        
        return items
    
    def _get_pending_approvals(self) -> List[Dict]:
        """Get pending approval items."""
        items = []
        
        if not self.pending_approval.exists():
            return items
        
        for file_path in self.pending_approval.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                action_match = re.search(r'action:\s*(\w+)', content)
                desc_match = re.search(r'# Approval Request: (.+?)(?:\n|$)', content)
                
                items.append({
                    'file': file_path.name,
                    'action': action_match.group(1) if action_match else 'unknown',
                    'description': desc_match.group(1).strip() if desc_match else file_path.stem
                })
            except Exception:
                continue
        
        return items
    
    def _calculate_metrics(self, date: str) -> Dict:
        """Calculate metrics for date."""
        metrics = {
            'items_completed': 0,
            'items_pending': 0,
            'approvals_pending': 0,
            'emails_processed': 0,
            'files_processed': 0,
            'whatsapp_messages': 0
        }
        
        # Count by type
        if self.done_folder.exists():
            for f in self.done_folder.glob('*.md'):
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime.strftime('%Y-%m-%d') == date:
                    metrics['items_completed'] += 1
                    
                    content = f.read_text(encoding='utf-8')
                    if 'type: email' in content:
                        metrics['emails_processed'] += 1
                    elif 'type: file_drop' in content:
                        metrics['files_processed'] += 1
                    elif 'type: whatsapp' in content:
                        metrics['whatsapp_messages'] += 1
        
        # Count pending
        metrics['items_pending'] = len(self._get_pending_items())
        metrics['approvals_pending'] = len(self._get_pending_approvals())
        
        return metrics
    
    def _get_logs(self, date: str) -> List[Dict]:
        """Get logs for date."""
        logs = []
        log_file = self.logs_folder / f'{date}.json'
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            logs.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
            except Exception:
                pass
        
        return logs[-20:]  # Last 20 entries
    
    def _format_briefing(
        self,
        date: str,
        completed: List[Dict],
        pending: List[Dict],
        approvals: List[Dict],
        metrics: Dict,
        logs: List[Dict]
    ) -> str:
        """Format briefing as markdown."""
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        
        # Completed items section
        completed_md = ''
        if completed:
            completed_md = '\n'.join(
                f"- [x] {item['description']} ({item['type']}) - {item['completed_at']}"
                for item in completed
            )
        else:
            completed_md = '*No items completed*'
        
        # Pending items section
        pending_md = ''
        if pending:
            pending_md = '\n'.join(
                f"- [ ] **{item['priority'].upper()}** {item['description']} ({item['type']})"
                for item in pending
            )
        else:
            pending_md = '*No pending items*'
        
        # Approvals section
        approvals_md = ''
        if approvals:
            approvals_md = '\n'.join(
                f"- ⏳ {item['description']} ({item['action']})"
                for item in approvals
            )
        else:
            approvals_md = '*No pending approvals*'
        
        return f'''---
type: daily_briefing
date: {date}
generated: {datetime.now().isoformat()}
items_completed: {metrics['items_completed']}
items_pending: {metrics['items_pending']}
approvals_pending: {metrics['approvals_pending']}
---

# Daily Briefing - {day_name}, {date_obj.strftime('%B %d, %Y')}

> Generated by AI Employee v0.2 (Silver Tier)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Items Completed** | {metrics['items_completed']} |
| **Items Pending** | {metrics['items_pending']} |
| **Approvals Pending** | {metrics['approvals_pending']} |
| **Emails Processed** | {metrics['emails_processed']} |
| **Files Processed** | {metrics['files_processed']} |

---

## Completed Items

{completed_md}

---

## Pending Items

{pending_md}

---

## Awaiting Your Approval

{approvals_md}

---

## Activity Log (Last 20 entries)

| Time | Action | Details |
|------|--------|---------|
''' + '\n'.join(
            f"| {log.get('timestamp', 'N/A')[-8:-1] if log.get('timestamp') else 'N/A'} | {log.get('action_type', 'N/A')} | {str(log.get('details', {}))[:50]} |"
            for log in logs[-10:]
        ) + f'''

---

## Action Items for Today

1. Review and approve pending items in `/Pending_Approval/`
2. Process high-priority items in `/Needs_Action/`
3. Check completed items in `/Done/`

---

*This briefing was automatically generated by the AI Employee system.*
'''


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Daily Briefing Generator'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date for briefing (YYYY-MM-DD), defaults to yesterday'
    )
    
    args = parser.parse_args()
    
    generator = DailyBriefingGenerator(vault_path=args.vault_path)
    filepath = generator.generate_briefing(args.date)
    
    print(f'Daily briefing generated: {filepath}')


if __name__ == '__main__':
    main()
