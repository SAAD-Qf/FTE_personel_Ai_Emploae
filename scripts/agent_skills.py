"""
Agent Skills Module

Reusable AI functionality that can be called by Claude Code or other agents.
Each skill is a self-contained function with clear inputs and outputs.

These skills implement the "Agent Skills" pattern from Claude Code documentation:
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

Usage:
    from agent_skills import AgentSkills
    
    skills = AgentSkills(vault_path="./AI_Employee_Vault")
    skills.create_plan("Process invoice", source_file="invoice.pdf")
    skills.request_approval("email_send", {"to": "client@example.com"})
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable


class AgentSkills:
    """Collection of reusable AI agent skills."""
    
    def __init__(self, vault_path: str):
        """
        Initialize agent skills.
        
        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        
        # Folder paths
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.done = self.vault_path / 'Done'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.plans = self.vault_path / 'Plans'
        self.briefings = self.vault_path / 'Briefings'
        self.logs = self.vault_path / 'Logs'
        
        # Ensure folders exist
        for folder in [
            self.inbox, self.needs_action, self.in_progress,
            self.done, self.pending_approval, self.approved,
            self.rejected, self.plans, self.briefings, self.logs
        ]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Skill registry
        self._skills: Dict[str, Callable] = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """Register default skills."""
        
        @self.skill
        def create_plan(objective: str, source_file: Optional[str] = None, priority: str = 'normal') -> Dict:
            """
            Create a plan for a complex task.
            
            Args:
                objective: What needs to be accomplished
                source_file: Source action file that triggered this plan
                priority: Task priority (high, normal, low)
                
            Returns:
                Plan file path and status
            """
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_objective = objective[:40].replace(' ', '_').replace('/', '_')
            filename = f'PLAN_{timestamp}_{safe_objective}.md'
            filepath = self.plans / filename
            
            content = f'''---
type: plan
objective: "{objective}"
created: {datetime.now().isoformat()}
status: pending
priority: {priority}
source_file: "{source_file or ''}"
completed_steps: 0
total_steps: 5
---

# Plan: {objective}

## Objective

{objective}

## Progress

0/5 steps completed (0%)

## Steps

- [ ] Review source material and understand requirements
- [ ] Identify required actions and dependencies
- [ ] Execute required actions
- [ ] Verify completion and update status
- [ ] Move source file to /Done when complete

## Notes

*Add notes here*

---
*Created by AgentSkills at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
            
            filepath.write_text(content, encoding='utf-8')
            self._log_action('plan_created', {'objective': objective, 'file': filename})
            
            return {'success': True, 'file': str(filepath), 'status': 'created'}
        
        @self.skill
        def request_approval(
            action_type: str,
            description: str,
            details: Dict[str, Any],
            expires_hours: int = 24
        ) -> Dict:
            """
            Request human approval for a sensitive action.
            
            Args:
                action_type: Type of action (email_send, payment, etc.)
                description: Human-readable description
                details: Action details
                expires_hours: Hours until expiration
                
            Returns:
                Approval file path and status
            """
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_desc = description[:30].replace(' ', '_').replace('/', '_')
            filename = f'APPROVAL_{timestamp}_{safe_desc}.md'
            filepath = self.pending_approval / filename
            
            details_md = '\n'.join(f'- **{k.replace("_", " ").title()}**: {v}' for k, v in details.items())
            
            content = f'''---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
expires: {(datetime.now() + timedelta(hours=expires_hours)).isoformat()}
status: pending
---

# Approval Request: {description}

## Action Details

| Property | Value |
|----------|-------|
| **Action Type** | {action_type} |
| **Created** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **Expires** | {(datetime.now() + timedelta(hours=expires_hours)).strftime('%Y-%m-%d %H:%M:%S')} |

## Details

{details_md if details_md else 'No additional details.'}

## Instructions

### To Approve
Move this file to the `/Approved/` folder.

### To Reject
Move this file to the `/Rejected/` folder with a comment explaining why.

## Comments

*Add comments here*

---
*This action requires human approval before proceeding.*
'''
            
            filepath.write_text(content, encoding='utf-8')
            self._log_action('approval_requested', {'type': action_type, 'file': filename})
            
            return {'success': True, 'file': str(filepath), 'status': 'pending'}
        
        @self.skill
        def move_to_done(source_file: str, reason: str = '') -> Dict:
            """
            Move a completed item to the Done folder.
            
            Args:
                source_file: Path to the source file (relative to vault or filename)
                reason: Reason for completion
                
            Returns:
                Status of the move operation
            """
            # Find source file
            source_path = self.vault_path / source_file
            if not source_path.exists():
                for folder in [self.needs_action, self.in_progress, self.pending_approval]:
                    test_path = folder / source_file
                    if test_path.exists():
                        source_path = test_path
                        break
            
            if not source_path.exists():
                return {'success': False, 'error': f'File not found: {source_file}'}
            
            # Move to Done
            dest_path = self.done / source_path.name
            shutil.move(str(source_path), str(dest_path))
            
            self._log_action('moved_to_done', {'file': source_file, 'reason': reason})
            
            return {'success': True, 'file': str(dest_path), 'status': 'completed'}
        
        @self.skill
        def update_dashboard() -> Dict:
            """
            Update the Dashboard.md with current status.
            
            Returns:
                Dashboard update status
            """
            dashboard = self.vault_path / 'Dashboard.md'
            
            # Count items
            pending_count = len(list(self.needs_action.glob('*.md')))
            in_progress_count = len(list(self.in_progress.glob('*.md')))
            approval_count = len(list(self.pending_approval.glob('*.md')))
            done_today = self._count_done_today()
            
            if dashboard.exists():
                content = dashboard.read_text(encoding='utf-8')
                
                # Update status table
                content = re.sub(
                    r'\|\s*\*\*Pending Items\*\*\s*\|[^|]+\|',
                    f'| **Pending Items** | {pending_count} |',
                    content
                )
                content = re.sub(
                    r'\|\s*\*\*In Progress\*\*\s*\|[^|]+\|',
                    f'| **In Progress** | {in_progress_count} |',
                    content
                )
                content = re.sub(
                    r'\|\s*\*\*Awaiting Approval\*\*\s*\|[^|]+\|',
                    f'| **Awaiting Approval** | {approval_count} |',
                    content
                )
                content = re.sub(
                    r'\|\s*\*\*Completed Today\*\*\s*\|[^|]+\|',
                    f'| **Completed Today** | {done_today} |',
                    content
                )
                
                # Update timestamp
                content = re.sub(
                    r'last_updated: [^\n]+',
                    f'last_updated: {datetime.now().isoformat()}',
                    content
                )
                
                dashboard.write_text(content, encoding='utf-8')
            
            return {
                'success': True,
                'pending': pending_count,
                'in_progress': in_progress_count,
                'approvals': approval_count,
                'done_today': done_today
            }
        
        @self.skill
        def categorize_item(file_path: str, category: str, tags: List[str] = None) -> Dict:
            """
            Categorize an item by adding metadata.
            
            Args:
                file_path: Path to the file to categorize
                category: Category name
                tags: List of tags to add
                
            Returns:
                Categorization status
            """
            target = self.vault_path / file_path
            if not target.exists():
                return {'success': False, 'error': 'File not found'}
            
            content = target.read_text(encoding='utf-8')
            
            # Add category and tags to frontmatter
            if 'category:' not in content:
                content = re.sub(
                    r'(^---\n)',
                    f'\\1category: {category}\n',
                    content
                )
            
            if tags and 'tags:' not in content:
                tags_str = ', '.join(tags)
                content = re.sub(
                    r'(^---\n)',
                    f'\\1tags: [{tags_str}]\n',
                    content
                )
            
            target.write_text(content, encoding='utf-8')
            self._log_action('item_categorized', {'file': file_path, 'category': category})
            
            return {'success': True, 'category': category, 'tags': tags or []}
        
        @self.skill
        def extract_info(file_path: str, info_type: str = 'all') -> Dict:
            """
            Extract information from an action file.
            
            Args:
                file_path: Path to the file
                info_type: Type of info to extract (frontmatter, content, all)
                
            Returns:
                Extracted information
            """
            target = self.vault_path / file_path
            if not target.exists():
                return {'success': False, 'error': 'File not found'}
            
            content = target.read_text(encoding='utf-8')
            result = {'success': True, 'file': file_path}
            
            if info_type in ['frontmatter', 'all']:
                # Extract frontmatter
                fm_match = re.search(r'---\n(.*?)\n---', content, re.DOTALL)
                if fm_match:
                    frontmatter = fm_match.group(1)
                    result['frontmatter'] = {}
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            result['frontmatter'][key.strip()] = value.strip()
            
            if info_type in ['content', 'all']:
                # Extract main content (after frontmatter)
                content_match = re.search(r'---\n.*?\n---\n(.*)', content, re.DOTALL)
                if content_match:
                    result['content'] = content_match.group(1).strip()
            
            return result
        
        @self.skill
        def create_briefing(
            period: str = 'daily',
            date: Optional[str] = None
        ) -> Dict:
            """
            Create a periodic briefing.
            
            Args:
                period: 'daily' or 'weekly'
                date: Date for briefing (YYYY-MM-DD), defaults to yesterday
                
            Returns:
                Briefing file path
            """
            if date is None:
                date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            filename = f'Briefing_{date}.md'
            filepath = self.briefings / filename
            
            # Count completed items
            done_count = 0
            for f in self.done.glob('*.md'):
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime.strftime('%Y-%m-%d') == date:
                    done_count += 1
            
            content = f'''---
type: {period}_briefing
date: {date}
generated: {datetime.now().isoformat()}
period: {period}
---

# {period.title()} Briefing - {date_obj.strftime('%A, %B %d, %Y')}

## Summary

| Metric | Value |
|--------|-------|
| **Items Completed** | {done_count} |
| **Generated** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

## Completed Items

*Review /Done folder for completed items*

## Pending Items

*Review /Needs_Action folder for pending items*

## Notes

*Add your notes here*

---
*Generated by AgentSkills*
'''
            
            filepath.write_text(content, encoding='utf-8')
            self._log_action('briefing_created', {'period': period, 'date': date})
            
            return {'success': True, 'file': str(filepath)}
    
    def skill(self, func: Callable) -> Callable:
        """Decorator to register a skill."""
        self._skills[func.__name__] = func
        return func
    
    def get_skill(self, name: str) -> Optional[Callable]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def list_skills(self) -> List[str]:
        """List all registered skills."""
        return list(self._skills.keys())
    
    def execute_skill(self, name: str, **kwargs) -> Any:
        """Execute a skill by name."""
        skill = self.get_skill(name)
        if not skill:
            return {'success': False, 'error': f'Skill not found: {name}'}
        
        try:
            return skill(**kwargs)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _count_done_today(self) -> int:
        """Count items moved to Done today."""
        if not self.done.exists():
            return 0
        
        today = datetime.now().date()
        count = 0
        
        for f in self.done.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime).date()
                if mtime == today:
                    count += 1
            except Exception:
                pass
        
        return count
    
    def _log_action(self, action_type: str, details: Dict):
        """Log an action to the audit log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'agent_skills',
            **details
        }
        
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


# Convenience functions for direct use
def create_plan(vault_path: str, objective: str, source_file: str = None) -> Dict:
    """Create a plan."""
    skills = AgentSkills(vault_path)
    return skills.create_plan(objective, source_file)


def request_approval(vault_path: str, action_type: str, description: str, details: Dict) -> Dict:
    """Request approval."""
    skills = AgentSkills(vault_path)
    return skills.request_approval(action_type, description, details)


def move_to_done(vault_path: str, source_file: str) -> Dict:
    """Move to done."""
    skills = AgentSkills(vault_path)
    return skills.move_to_done(source_file)


if __name__ == '__main__':
    # Demo usage
    import sys
    
    if len(sys.argv) > 1:
        vault = sys.argv[1]
    else:
        vault = './AI_Employee_Vault'
    
    skills = AgentSkills(vault)
    
    print("Available Skills:")
    print("-" * 30)
    for skill_name in skills.list_skills():
        print(f"  - {skill_name}")
