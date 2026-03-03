"""
Plan Manager

Creates and manages Plan.md files for Claude's reasoning loop.
Plans break down complex tasks into actionable steps with checkboxes.

Usage:
    python plan_manager.py --vault-path ./AI_Employee_Vault create "Process invoice from Client A"
    python plan_manager.py --vault-path ./AI_Employee_Vault update --plan-file Plans/PLAN_invoice.md
    python plan_manager.py --vault-path ./AI_Employee_Vault list
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


class PlanStep:
    """Represents a single step in a plan."""
    
    def __init__(
        self,
        description: str,
        completed: bool = False,
        requires_approval: bool = False,
        action_type: str = 'general'
    ):
        self.description = description
        self.completed = completed
        self.requires_approval = requires_approval
        self.action_type = action_type
    
    def to_markdown(self) -> str:
        """Convert step to markdown checkbox."""
        checkbox = '[x]' if self.completed else '[ ]'
        approval_tag = ' 🔒' if self.requires_approval else ''
        return f'- {checkbox} {description}{approval_tag}'


class Plan:
    """Represents a task plan with multiple steps."""
    
    def __init__(
        self,
        objective: str,
        source_file: Optional[str] = None,
        priority: str = 'normal'
    ):
        self.objective = objective
        self.source_file = source_file
        self.priority = priority
        self.steps: List[PlanStep] = []
        self.created = datetime.now()
        self.status = 'pending'  # pending, in_progress, completed, blocked
        self.notes = ''
    
    def add_step(
        self,
        description: str,
        completed: bool = False,
        requires_approval: bool = False,
        action_type: str = 'general'
    ):
        """Add a step to the plan."""
        self.steps.append(PlanStep(
            description=description,
            completed=completed,
            requires_approval=requires_approval,
            action_type=action_type
        ))
    
    @property
    def completed_count(self) -> int:
        """Count of completed steps."""
        return sum(1 for s in self.steps if s.completed)
    
    @property
    def total_count(self) -> int:
        """Total number of steps."""
        return len(self.steps)
    
    @property
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return self.total_count > 0 and self.completed_count == self.total_count
    
    @property
    def pending_approvals(self) -> List[PlanStep]:
        """Get steps that require approval."""
        return [s for s in self.steps if s.requires_approval and not s.completed]
    
    def to_markdown(self) -> str:
        """Convert plan to markdown format."""
        # Generate frontmatter
        frontmatter = f'''---
type: plan
objective: "{self.objective}"
created: {self.created.isoformat()}
status: {self.status}
priority: {self.priority}
source_file: "{self.source_file or ''}"
completed_steps: {self.completed_count}
total_steps: {self.total_count}
---
'''
        # Generate content
        steps_markdown = '\n'.join(f'  {step.to_markdown()}' for step in self.steps)
        
        approval_section = ''
        if self.pending_approvals:
            approval_list = '\n'.join(f'- {s.description}' for s in self.pending_approvals)
            approval_section = f'''
## Requires Approval

The following steps require human approval:

{approval_list}

Move approval files from `/Pending_Approval/` to `/Approved/` to proceed.
'''
        
        notes_section = f'''
## Notes

{self.notes if self.notes else '*Add notes here*'}
'''
        
        return f'''{frontmatter}

# Plan: {self.objective}

## Objective

{self.objective}

## Progress

{self.completed_count}/{self.total_count} steps completed ({self._progress_percentage}%)

## Steps

{steps_markdown}
{approval_section}
{notes_section}
---
*Created by PlanManager at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
    
    @property
    def _progress_percentage(self) -> int:
        """Calculate progress percentage."""
        if self.total_count == 0:
            return 0
        return int((self.completed_count / self.total_count) * 100)


class PlanManager:
    """Manages plans in the vault."""
    
    def __init__(self, vault_path: str):
        """
        Initialize plan manager.
        
        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        self.plans_folder = self.vault_path / 'Plans'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        
        # Ensure folders exist
        self.plans_folder.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.pending_approval.mkdir(parents=True, exist_ok=True)
    
    def create_plan(
        self,
        objective: str,
        source_file: Optional[str] = None,
        priority: str = 'normal',
        steps: Optional[List[Dict]] = None
    ) -> Path:
        """
        Create a new plan.
        
        Args:
            objective: The plan objective
            source_file: Source action file that triggered this plan
            priority: Plan priority (high, normal, low)
            steps: List of step dictionaries
            
        Returns:
            Path to the created plan file
        """
        # Create plan
        plan = Plan(objective=objective, source_file=source_file, priority=priority)
        
        # Add default steps if none provided
        if not steps:
            steps = [
                {'description': 'Review source material and understand requirements', 'action_type': 'review'},
                {'description': 'Identify required actions and dependencies', 'action_type': 'analysis'},
                {'description': 'Execute required actions', 'action_type': 'execution'},
                {'description': 'Verify completion and update status', 'action_type': 'verification'},
                {'description': 'Move source file to /Done', 'action_type': 'cleanup'},
            ]
        
        # Add steps to plan
        for step_data in steps:
            plan.add_step(
                description=step_data.get('description', 'Unknown step'),
                completed=step_data.get('completed', False),
                requires_approval=step_data.get('requires_approval', False),
                action_type=step_data.get('action_type', 'general')
            )
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_objective = objective[:40].replace(' ', '_').replace('/', '_')
        filename = f'PLAN_{timestamp}_{safe_objective}.md'
        filepath = self.plans_folder / filename
        
        # Write plan file
        filepath.write_text(plan.to_markdown(), encoding='utf-8')
        
        return filepath
    
    def create_approval_request(
        self,
        action_type: str,
        description: str,
        details: Dict,
        related_plan: Optional[str] = None
    ) -> Path:
        """
        Create an approval request file.
        
        Args:
            action_type: Type of action (email_send, payment, etc.)
            description: Human-readable description
            details: Action details dictionary
            related_plan: Related plan filename
            
        Returns:
            Path to the created approval file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_desc = description[:30].replace(' ', '_').replace('/', '_')
        filename = f'APPROVAL_{timestamp}_{safe_desc}.md'
        filepath = self.pending_approval / filename
        
        content = f'''---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
expires: {(datetime.now().replace(hour=23, minute=59)).isoformat()}
status: pending
related_plan: "{related_plan or ''}"
---

# Approval Request: {description}

## Action Details

| Property | Value |
|----------|-------|
| **Action Type** | {action_type} |
| **Created** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **Description** | {description} |

## Details

{self._format_details(details)}

## Instructions

### To Approve
Move this file to the `/Approved/` folder.

### To Reject
Move this file to the `/Rejected/` folder with a comment explaining why.

### To Request Changes
Add a comment below and move back to `/Pending_Approval/`.

## Comments

*Add comments here*

---
*This action requires human approval before proceeding.*
'''
        
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    def _format_details(self, details: Dict) -> str:
        """Format details dictionary as markdown."""
        if not details:
            return 'No additional details.'
        
        lines = []
        for key, value in details.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f'- **{formatted_key}**: {value}')
        
        return '\n'.join(lines)
    
    def update_plan_status(self, plan_file: Path, completed_steps: List[int]) -> bool:
        """
        Update a plan's completed steps.
        
        Args:
            plan_file: Path to the plan file
            completed_steps: List of step indices (0-based) that are completed
            
        Returns:
            True if update was successful
        """
        try:
            content = plan_file.read_text(encoding='utf-8')
            
            # Parse current plan
            plan = self._parse_plan(content)
            
            # Update completed steps
            for idx in completed_steps:
                if 0 <= idx < len(plan.steps):
                    plan.steps[idx].completed = True
            
            # Update status
            if plan.is_complete:
                plan.status = 'completed'
            elif any(s.completed for s in plan.steps):
                plan.status = 'in_progress'
            
            # Write updated plan
            plan_file.write_text(plan.to_markdown(), encoding='utf-8')
            return True
            
        except Exception as e:
            print(f'Error updating plan: {e}')
            return False
    
    def _parse_plan(self, content: str) -> Plan:
        """Parse a plan from markdown content."""
        # Extract objective from frontmatter
        obj_match = re.search(r'objective:\s*"([^"]+)"', content)
        objective = obj_match.group(1) if obj_match else 'Unknown'
        
        # Extract source file
        source_match = re.search(r'source_file:\s*"([^"]*)"', content)
        source_file = source_match.group(1) if source_match else None
        
        # Extract priority
        priority_match = re.search(r'priority:\s*(\w+)', content)
        priority = priority_match.group(1) if priority_match else 'normal'
        
        plan = Plan(objective=objective, source_file=source_file, priority=priority)
        
        # Parse steps (look for checkbox pattern)
        step_pattern = r'- \[([ x])\] (.+?)(?: 🔒)?(?:$|\n)'
        for match in re.finditer(step_pattern, content, re.MULTILINE):
            completed = match.group(1) == 'x'
            description = match.group(2).strip()
            requires_approval = '🔒' in match.group(0)
            plan.add_step(description=description, completed=completed, requires_approval=requires_approval)
        
        return plan
    
    def list_plans(self) -> List[Dict]:
        """List all plans with their status."""
        plans = []
        
        for plan_file in self.plans_folder.glob('*.md'):
            content = plan_file.read_text(encoding='utf-8')
            
            # Extract key info
            obj_match = re.search(r'objective:\s*"([^"]+)"', content)
            status_match = re.search(r'status:\s*(\w+)', content)
            completed_match = re.search(r'completed_steps:\s*(\d+)', content)
            total_match = re.search(r'total_steps:\s*(\d+)', content)
            
            plans.append({
                'file': plan_file.name,
                'objective': obj_match.group(1) if obj_match else 'Unknown',
                'status': status_match.group(1) if status_match else 'unknown',
                'completed': int(completed_match.group(1)) if completed_match else 0,
                'total': int(total_match.group(1)) if total_match else 0,
            })
        
        return plans
    
    def get_pending_approvals(self) -> List[Path]:
        """Get list of pending approval files."""
        if not self.pending_approval.exists():
            return []
        return sorted(
            [f for f in self.pending_approval.iterdir() if f.suffix == '.md'],
            key=lambda f: f.stat().st_mtime
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Plan Manager for AI Employee'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new plan')
    create_parser.add_argument('objective', type=str, help='Plan objective')
    create_parser.add_argument('--source', type=str, help='Source action file')
    create_parser.add_argument('--priority', type=str, default='normal', choices=['high', 'normal', 'low'])
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a plan')
    update_parser.add_argument('--plan-file', type=str, required=True, help='Plan file to update')
    update_parser.add_argument('--completed', type=int, nargs='+', help='Step indices to mark complete')
    
    # List command
    subparsers.add_parser('list', help='List all plans')
    
    # Approval command
    approval_parser = subparsers.add_parser('approval', help='Create approval request')
    approval_parser.add_argument('--type', type=str, required=True, help='Action type')
    approval_parser.add_argument('--description', type=str, required=True, help='Description')
    approval_parser.add_argument('--details', type=str, help='JSON details')
    
    args = parser.parse_args()
    
    manager = PlanManager(vault_path=args.vault_path)
    
    if args.command == 'create':
        filepath = manager.create_plan(
            objective=args.objective,
            source_file=args.source,
            priority=args.priority
        )
        print(f'Created plan: {filepath}')
    
    elif args.command == 'update':
        plan_file = Path(args.plan_file)
        if not plan_file.exists():
            plan_file = manager.plans_folder / args.plan_file
        
        completed = args.completed or []
        success = manager.update_plan_status(plan_file, completed)
        print(f'Update {"successful" if success else "failed"}')
    
    elif args.command == 'list':
        plans = manager.list_plans()
        if plans:
            print(f"{'File':<40} {'Status':<12} {'Progress':<15} {'Objective'}")
            print('-' * 100)
            for plan in plans:
                progress = f"{plan['completed']}/{plan['total']}"
                print(f"{plan['file']:<40} {plan['status']:<12} {progress:<15} {plan['objective'][:40]}")
        else:
            print('No plans found')
    
    elif args.command == 'approval':
        details = json.loads(args.details) if args.details else {}
        filepath = manager.create_approval_request(
            action_type=args.type,
            description=args.description,
            details=details
        )
        print(f'Created approval request: {filepath}')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
