"""
Orchestrator

Master process for the AI Employee system. Monitors folders,
triggers Claude Code for processing, and manages task completion.

Usage:
    python orchestrator.py --vault-path ./AI_Employee_Vault
    python orchestrator.py --vault-path ./AI_Employee_Vault --auto-process
"""

import argparse
import subprocess
import shutil
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging


class Orchestrator:
    """
    Main orchestrator for the AI Employee system.
    
    Responsibilities:
    - Monitor Needs_Action folder for pending items
    - Trigger Claude Code to process items
    - Move completed items to Done folder
    - Update Dashboard.md with current status
    - Manage approval workflow
    """
    
    def __init__(self, vault_path: str, auto_process: bool = False):
        """
        Initialize the orchestrator.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            auto_process: Whether to automatically trigger Claude processing
        """
        self.vault_path = Path(vault_path)
        self.auto_process = auto_process
        
        # Folder paths
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.done = self.vault_path / 'Done'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.plans = self.vault_path / 'Plans'
        self.briefings = self.vault_path / 'Briefings'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        # Ensure all folders exist
        self._ensure_folders()
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Orchestrator initialized')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Auto-process: {auto_process}')
    
    def _ensure_folders(self):
        """Ensure all required folders exist."""
        folders = [
            self.needs_action, self.in_progress, self.done,
            self.pending_approval, self.approved, self.rejected,
            self.plans, self.briefings, self.logs
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Configure logging."""
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
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
        
        self.logger = logging.getLogger('Orchestrator')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def count_items(self, folder: Path) -> int:
        """Count .md files in a folder."""
        if not folder.exists():
            return 0
        return len([f for f in folder.iterdir() if f.suffix == '.md'])
    
    def get_pending_items(self) -> List[Path]:
        """Get list of pending action files."""
        if not self.needs_action.exists():
            return []
        return sorted(
            [f for f in self.needs_action.iterdir() if f.suffix == '.md'],
            key=lambda f: f.stat().st_mtime
        )
    
    def get_approved_items(self) -> List[Path]:
        """Get list of approved action files."""
        if not self.approved.exists():
            return []
        return sorted(
            [f for f in self.approved.iterdir() if f.suffix == '.md'],
            key=lambda f: f.stat().st_mtime
        )
    
    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        try:
            # Count items in each folder
            pending_count = self.count_items(self.needs_action)
            in_progress_count = self.count_items(self.in_progress)
            approval_count = self.count_items(self.pending_approval)
            done_today = self._count_done_today()
            
            # Get recent activity
            recent_activity = self._get_recent_activity()
            
            # Read current dashboard
            if self.dashboard.exists():
                content = self.dashboard.read_text(encoding='utf-8')
            else:
                content = self._create_default_dashboard()
            
            # Update status section
            content = self._update_dashboard_status(
                content,
                pending_count,
                in_progress_count,
                approval_count,
                done_today
            )
            
            # Update recent activity
            content = self._update_dashboard_activity(content, recent_activity)
            
            # Update system health
            content = self._update_dashboard_health(content)
            
            # Write updated dashboard
            self.dashboard.write_text(content, encoding='utf-8')
            
            self.logger.debug('Dashboard updated')
            
        except Exception as e:
            self.logger.error(f'Failed to update dashboard: {e}', exc_info=True)
    
    def _count_done_today(self) -> int:
        """Count items moved to Done today."""
        if not self.done.exists():
            return 0
        
        today = datetime.now().date()
        count = 0
        
        for f in self.done.iterdir():
            if f.suffix == '.md':
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime).date()
                    if mtime == today:
                        count += 1
                except Exception:
                    pass
        
        return count
    
    def _get_recent_activity(self) -> List[Dict]:
        """Get recent activity from logs."""
        activity = []
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-10:]  # Last 10 entries
                    
                for line in lines:
                    if 'INFO' in line and 'Created action file' in line:
                        # Extract filename
                        match = re.search(r'Created action file for?: (\S+)', line)
                        if match:
                            activity.append({
                                'timestamp': line.split(' - ')[0],
                                'action': f'File received: {match.group(1)}',
                                'status': 'pending'
                            })
            except Exception as e:
                self.logger.error(f'Error reading logs: {e}')
        
        return activity
    
    def _create_default_dashboard(self) -> str:
        """Create a default dashboard if none exists."""
        return f'''---
last_updated: {datetime.now().isoformat()}
status: active
---

# AI Employee Dashboard

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

## Quick Status

| Metric | Value |
|--------|-------|
| **Pending Items** | 0 |
| **In Progress** | 0 |
| **Awaiting Approval** | 0 |
| **Completed Today** | 0 |

---

*Generated by AI Employee v0.1 (Bronze Tier)*
'''
    
    def _update_dashboard_status(
        self,
        content: str,
        pending: int,
        in_progress: int,
        approval: int,
        done: int
    ) -> str:
        """Update the status table in dashboard."""
        # Find and replace status table
        pattern = r'(\|\s*\*\*Pending Items\*\*\s*\|)[^\n]+\n[^|]+\|[^|]+\|[^|]+\|[^|]+\|'
        replacement = f'''| **Pending Items** | {pending} |
| **In Progress** | {in_progress} |
| **Awaiting Approval** | {approval} |
| **Completed Today** | {done} |'''
        
        return re.sub(pattern, replacement, content)
    
    def _update_dashboard_activity(self, content: str, activity: List[Dict]) -> str:
        """Update recent activity section."""
        if not activity:
            content = re.sub(
                r'(\#\# Recent Activity\n\n\| Timestamp \| Action \| Status \|)\n(\|-+\|[^|]+\|[^|]+\|)\n(\| — \| — \| — \|)',
                r'\1\n\2\n| — | — | — |',
                content
            )
        else:
            rows = '\n'.join([
                f"| {a['timestamp']} | {a['action']} | {a['status']} |"
                for a in activity[-5:]  # Last 5 items
            ])
            content = re.sub(
                r'(\#\# Recent Activity\n\n\| Timestamp \| Action \| Status \|)\n(\|-+\|[^|]+\|[^|]+\|)\n([^|]+)',
                f'\\1\n\\2\n{rows}',
                content
            )
        
        return content
    
    def _update_dashboard_health(self, content: str) -> str:
        """Update system health section."""
        # Check if watchers are running (simplified check)
        watcher_status = '⏳ Not running'
        orchestrator_status = '✅ Running'
        
        health_section = f'''## System Health

| Component | Status |
|-----------|--------|
| Watchers | {watcher_status} |
| Orchestrator | {orchestrator_status} |
| Last Sync | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |'''
        
        # Replace health section
        pattern = r'## System Health\n\n.*?(?=\n\n|\Z)'
        return re.sub(pattern, health_section, content, flags=re.DOTALL)
    
    def trigger_claude_processing(self) -> bool:
        """
        Trigger Claude Code to process pending items.
        
        Returns:
            True if processing was triggered, False otherwise
        """
        pending = self.get_pending_items()
        
        if not pending:
            self.logger.debug('No pending items to process')
            return False
        
        self.logger.info(f'Found {len(pending)} pending item(s)')
        
        # Create a processing prompt
        prompt = self._create_processing_prompt(pending)
        
        # Option 1: Create a prompt file for manual Claude processing
        prompt_file = self.vault_path / '_CLAUDE_PROMPT.md'
        prompt_file.write_text(prompt, encoding='utf-8')
        
        self.logger.info(f'Created prompt file: {prompt_file}')
        self.logger.info('Run: claude --prompt "_CLAUDE_PROMPT.md"')
        
        # Option 2: If Claude Code is available, trigger directly
        if self._claude_available():
            try:
                result = subprocess.run(
                    ['claude', '--prompt', prompt],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=str(self.vault_path)
                )
                
                if result.returncode == 0:
                    self.logger.info('Claude processing completed successfully')
                    return True
                else:
                    self.logger.error(f'Claude error: {result.stderr}')
                    
            except subprocess.TimeoutExpired:
                self.logger.error('Claude processing timed out')
            except FileNotFoundError:
                self.logger.warning('Claude Code not found in PATH')
            except Exception as e:
                self.logger.error(f'Error triggering Claude: {e}')
        
        return False
    
    def _claude_available(self) -> bool:
        """Check if Claude Code is available."""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _create_processing_prompt(self, pending_items: List[Path]) -> str:
        """Create a prompt for Claude Code."""
        item_list = '\n'.join([f'- `{item.name}`' for item in pending_items])
        
        return f'''# AI Employee Task Processing

You are the AI Employee assistant. Process the pending items in the Needs_Action folder.

## Pending Items

{item_list}

## Your Tasks

1. **Read** each pending action file in `/Needs_Action/`
2. **Understand** what action is required
3. **Create a plan** in `/Plans/` for complex tasks
4. **Execute** simple tasks directly (reading, categorizing, summarizing)
5. **Request approval** for sensitive actions by creating files in `/Pending_Approval/`
6. **Move completed items** to `/Done/` after processing

## Rules

- Always be helpful and thorough
- Follow the Company_Handbook.md for decision-making
- When in doubt, request human approval
- Log all actions taken
- Update the Dashboard.md after processing

## Start Processing

Begin by reading the first pending item and determining what action is needed.
'''
    
    def process_approved_items(self) -> bool:
        """
        Process approved items (actions that have human approval).
        
        Returns:
            True if any items were processed
        """
        approved = self.get_approved_items()
        
        if not approved:
            return False
        
        self.logger.info(f'Processing {len(approved)} approved item(s)')
        
        for item in approved:
            try:
                # Read the approved action
                content = item.read_text(encoding='utf-8')
                
                # Extract action type from frontmatter
                action_type = self._extract_frontmatter_value(content, 'action')
                
                # Log the approval
                self.log_action('approved', {
                    'file': item.name,
                    'action_type': action_type or 'unknown'
                })
                
                # Move to Done
                dest = self.done / item.name
                shutil.move(str(item), str(dest))
                
                self.logger.info(f'Processed approved item: {item.name}')
                
            except Exception as e:
                self.logger.error(f'Error processing approved item: {e}', exc_info=True)
        
        return True
    
    def _extract_frontmatter_value(self, content: str, key: str) -> Optional[str]:
        """Extract a value from YAML frontmatter."""
        match = re.search(rf'^---\n.*?^{key}:\s*(.+)$', content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip().strip('"\'')
        return None
    
    def log_action(self, action_type: str, details: Dict):
        """Log an action to the audit log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'orchestrator',
            **details
        }
        
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def run_once(self):
        """Run a single orchestration cycle."""
        self.logger.debug('Running orchestration cycle')
        
        # Update dashboard
        self.update_dashboard()
        
        # Process approved items first
        if self.process_approved_items():
            self.update_dashboard()
        
        # Trigger Claude processing if auto-process is enabled
        if self.auto_process:
            if self.trigger_claude_processing():
                self.update_dashboard()
    
    def run_continuous(self, interval: int = 60):
        """
        Run continuous orchestration loop.
        
        Args:
            interval: Seconds between cycles
        """
        import time
        
        self.logger.info(f'Starting continuous orchestration (interval: {interval}s)')
        
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Employee Orchestrator'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--auto-process',
        action='store_true',
        help='Automatically trigger Claude processing'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (daemon mode)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = Orchestrator(
        vault_path=args.vault_path,
        auto_process=args.auto_process
    )
    
    # Run
    if args.continuous:
        orchestrator.run_continuous(interval=args.interval)
    else:
        orchestrator.run_once()


if __name__ == '__main__':
    main()
