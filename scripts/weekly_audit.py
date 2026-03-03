"""
Weekly Business Audit & CEO Briefing Generator

Generates comprehensive weekly business reports including:
- Revenue analysis
- Expense tracking
- Subscription audit
- Task completion summary
- Bottleneck identification
- Proactive suggestions

This is a key Gold Tier feature that transforms the AI from reactive to proactive.

Usage:
    python weekly_audit.py --vault-path ./AI_Employee_Vault generate
    python weekly_audit.py --vault-path ./AI_Employee_Vault generate --with-odoo
    python weekly_audit.py --vault-path ./AI_Employee_Vault schedule
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import Odoo client
try:
    from odoo_mcp_server import OdooClient
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False


class BriefingType(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


@dataclass
class BusinessMetric:
    """Represents a business metric."""
    name: str
    value: float
    target: Optional[float] = None
    trend: str = 'stable'  # improving, declining, stable
    alert: bool = False


@dataclass
class Subscription:
    """Represents a subscription service."""
    name: str
    cost: float
    frequency: str  # monthly, yearly
    last_used: Optional[datetime] = None
    status: str = 'active'  # active, unused, increased


class WeeklyAuditGenerator:
    """Generates weekly business audits and CEO briefings."""

    def __init__(self, vault_path: str, odoo_config: Optional[str] = None):
        """
        Initialize audit generator.

        Args:
            vault_path: Path to the Obsidian vault directory
            odoo_config: Path to Odoo config file (optional)
        """
        self.vault_path = Path(vault_path)
        self.odoo_client = None

        # Folders
        self.briefings_folder = self.vault_path / 'Briefings'
        self.done_folder = self.vault_path / 'Done'
        self.needs_action_folder = self.vault_path / 'Needs_Action'
        self.pending_approval_folder = self.vault_path / 'Pending_Approval'
        self.logs_folder = self.vault_path / 'Logs'
        self.posts_folder = self.vault_path / 'Posts'
        self.invoices_folder = self.vault_path / 'Invoices'

        # Ensure folders exist
        self.briefings_folder.mkdir(parents=True, exist_ok=True)

        # Initialize Odoo if configured
        if odoo_config and ODOO_AVAILABLE:
            try:
                config_path = Path(odoo_config)
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    self.odoo_client = OdooClient(
                        url=config['url'],
                        db=config['db'],
                        username=config['username'],
                        password=config['password']
                    )
            except Exception as e:
                print(f"Warning: Could not initialize Odoo: {e}")

    def generate_weekly_briefing(
        self,
        week_start: Optional[datetime] = None,
        include_odoo: bool = False
    ) -> Path:
        """
        Generate a comprehensive weekly CEO briefing.

        Args:
            week_start: Start of the week (default: last Monday)
            include_odoo: Include Odoo accounting data

        Returns:
            Path to generated briefing file
        """
        # Calculate week dates
        if week_start is None:
            # Get last Monday
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday, weeks=1)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # Gather data
        revenue_data = self._analyze_revenue(week_start, week_end, include_odoo)
        expense_data = self._analyze_expenses(week_start, week_end, include_odoo)
        task_data = self._analyze_tasks(week_start, week_end)
        social_data = self._analyze_social_media(week_start, week_end)
        subscription_data = self._audit_subscriptions()
        bottlenecks = self._identify_bottlenecks(task_data)
        suggestions = self._generate_suggestions(revenue_data, expense_data, subscription_data, bottlenecks)

        # Generate briefing
        briefing_path = self._create_briefing_file(
            week_start=week_start,
            week_end=week_end,
            revenue=revenue_data,
            expenses=expense_data,
            tasks=task_data,
            social=social_data,
            subscriptions=subscription_data,
            bottlenecks=bottlenecks,
            suggestions=suggestions
        )

        return briefing_path

    def _analyze_revenue(
        self,
        week_start: datetime,
        week_end: datetime,
        include_odoo: bool = False
    ) -> Dict:
        """Analyze revenue for the period."""
        revenue = {
            'total': 0.0,
            'invoices_sent': 0,
            'invoices_paid': 0,
            'outstanding': 0.0,
            'by_client': {},
            'trend': 'stable'
        }

        # Try Odoo first if available
        if include_odoo and self.odoo_client:
            try:
                metrics = self.odoo_client.get_business_metrics()
                revenue['total'] = metrics.get('monthly_revenue', 0)
                revenue['outstanding'] = metrics.get('outstanding_amount', 0)
                revenue['invoices_sent'] = metrics.get('outstanding_invoices', 0)
            except Exception as e:
                print(f"Could not get Odoo metrics: {e}")

        # Also check local invoice files
        if self.invoices_folder.exists():
            for invoice_file in self.invoices_folder.glob('*.md'):
                try:
                    content = invoice_file.read_text(encoding='utf-8')

                    # Check if invoice was created/paid in this period
                    created_match = re.search(r'created:\s*([\d\-T:]+)', content)
                    if created_match:
                        created_date = datetime.fromisoformat(created_match.group(1))
                        if week_start <= created_date <= week_end:
                            # Extract amount
                            amount_match = re.search(r'amount:\s*([\d.]+)', content)
                            if amount_match:
                                amount = float(amount_match.group(1))
                                revenue['total'] += amount
                                revenue['invoices_sent'] += 1

                            # Extract client
                            client_match = re.search(r'client:\s*["\']?([^"\'\n]+)', content)
                            if client_match:
                                client = client_match.group(1).strip()
                                revenue['by_client'][client] = revenue['by_client'].get(client, 0) + amount

                except Exception as e:
                    print(f"Error reading invoice {invoice_file}: {e}")

        # Check logs for payment confirmations
        if self.logs_folder.exists():
            for log_file in self.logs_folder.glob('*.json'):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            entry = json.loads(line.strip())
                            if entry.get('action_type') == 'payment_received':
                                log_date = datetime.fromisoformat(entry.get('timestamp', ''))
                                if week_start <= log_date <= week_end:
                                    revenue['invoices_paid'] += 1
                except Exception:
                    pass

        # Calculate trend (simplified)
        if revenue['total'] > 0:
            revenue['trend'] = 'improving'
        elif revenue['total'] == 0:
            revenue['trend'] = 'declining'

        return revenue

    def _analyze_expenses(
        self,
        week_start: datetime,
        week_end: datetime,
        include_odoo: bool = False
    ) -> Dict:
        """Analyze expenses for the period."""
        expenses = {
            'total': 0.0,
            'by_category': {},
            'subscriptions': 0.0,
            'one_time': 0.0,
            'flagged': []
        }

        # Try Odoo if available
        if include_odoo and self.odoo_client:
            try:
                pl = self.odoo_client.get_profit_loss()
                expenses['total'] = pl.get('total_expense', 0)
                expenses['by_category'] = {
                    acc['name']: acc['balance']
                    for acc in pl.get('expenses', [])
                }
            except Exception as e:
                print(f"Could not get Odoo P&L: {e}")

        # Check for expense files
        expense_patterns = ['expense', 'receipt', 'bill', 'invoice_in']

        if self.needs_action_folder.exists():
            for file in self.needs_action_folder.glob('*.md'):
                content_lower = file.name.lower()
                if any(p in content_lower for p in expense_patterns):
                    try:
                        content = file.read_text(encoding='utf-8')
                        amount_match = re.search(r'amount:\s*([\d.]+)', content)
                        if amount_match:
                            amount = float(amount_match.group(1))
                            expenses['total'] += amount
                            expenses['one_time'] += amount
                    except Exception:
                        pass

        # Flag large expenses
        if expenses['total'] > 500:
            expenses['flagged'].append({
                'reason': 'High weekly expenses',
                'amount': expenses['total'],
                'threshold': 500
            })

        return expenses

    def _analyze_tasks(
        self,
        week_start: datetime,
        week_end: datetime
    ) -> Dict:
        """Analyze task completion for the period."""
        tasks = {
            'completed': 0,
            'pending': 0,
            'in_progress': 0,
            'overdue': 0,
            'by_type': {},
            'avg_completion_time': 0
        }

        # Count completed tasks
        if self.done_folder.exists():
            for file in self.done_folder.glob('*.md'):
                try:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if week_start <= mtime <= week_end:
                        tasks['completed'] += 1

                        # Extract type from frontmatter
                        content = file.read_text(encoding='utf-8')
                        type_match = re.search(r'type:\s*(\w+)', content)
                        if type_match:
                            task_type = type_match.group(1)
                            tasks['by_type'][task_type] = tasks['by_type'].get(task_type, 0) + 1
                except Exception:
                    pass

        # Count pending tasks
        if self.needs_action_folder.exists():
            tasks['pending'] = len(list(self.needs_action_folder.glob('*.md')))

        # Count in-progress tasks
        if self.vault_path.exists():
            in_progress = self.vault_path / 'In_Progress'
            if in_progress.exists():
                tasks['in_progress'] = len(list(in_progress.glob('*.md')))

        # Check for overdue (simplified - items older than 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        if self.needs_action_folder.exists():
            for file in self.needs_action_folder.glob('*.md'):
                try:
                    created_match = re.search(
                        r'created:\s*([\d\-T:]+)',
                        file.read_text(encoding='utf-8')
                    )
                    if created_match:
                        created = datetime.fromisoformat(created_match.group(1))
                        if created < week_ago:
                            tasks['overdue'] += 1
                except Exception:
                    pass

        return tasks

    def _analyze_social_media(
        self,
        week_start: datetime,
        week_end: datetime
    ) -> Dict:
        """Analyze social media activity."""
        social = {
            'posts_published': 0,
            'by_platform': {},
            'scheduled': 0,
            'drafts': 0
        }

        # Check published posts
        if self.posts_folder.exists():
            published = self.posts_folder / 'Published'
            if published.exists():
                for file in published.glob('*.md'):
                    try:
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if week_start <= mtime <= week_end:
                            content = file.read_text(encoding='utf-8')

                            # Extract platform
                            platform_match = re.search(r'platform:\s*(\w+)', content)
                            if platform_match:
                                platform = platform_match.group(1)
                                social['by_platform'][platform] = social['by_platform'].get(platform, 0) + 1
                                social['posts_published'] += 1
                    except Exception:
                        pass

            # Check scheduled
            scheduled = self.posts_folder / 'Scheduled'
            if scheduled.exists():
                social['scheduled'] = len(list(scheduled.glob('*.md')))

            # Check drafts
            drafts = self.posts_folder / 'Drafts'
            if drafts.exists():
                social['drafts'] = len(list(drafts.glob('*.md')))

        return social

    def _audit_subscriptions(self) -> List[Subscription]:
        """Audit active subscriptions."""
        subscriptions = []

        # Check Business_Goals.md for subscription list
        business_goals = self.vault_path / 'Business_Goals.md'
        if business_goals.exists():
            try:
                content = business_goals.read_text(encoding='utf-8')

                # Look for subscription table
                in_subscription_table = False
                for line in content.split('\n'):
                    if '| Service |' in line and 'Monthly Cost' in line:
                        in_subscription_table = True
                        continue
                    if in_subscription_table and line.startswith('|'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            name = parts[1].strip()
                            if name and name != '---':
                                try:
                                    cost_str = parts[2].strip().replace('$', '')
                                    cost = float(cost_str) if cost_str else 0
                                except ValueError:
                                    cost = 0

                                subscriptions.append(Subscription(
                                    name=name,
                                    cost=cost,
                                    frequency='monthly',
                                    status='active'
                                ))
                    elif in_subscription_table and not line.startswith('|'):
                        in_subscription_table = False

            except Exception as e:
                print(f"Error reading subscriptions: {e}")

        # Flag unused subscriptions (simplified - would need actual usage data)
        for sub in subscriptions:
            # In production, check actual usage
            if sub.cost > 100:  # Flag expensive subscriptions
                sub.status = 'review_recommended'

        return subscriptions

    def _identify_bottlenecks(self, task_data: Dict) -> List[Dict]:
        """Identify business bottlenecks."""
        bottlenecks = []

        # Check for overdue tasks
        if task_data['overdue'] > 0:
            bottlenecks.append({
                'type': 'overdue_tasks',
                'severity': 'high' if task_data['overdue'] > 5 else 'medium',
                'description': f"{task_data['overdue']} task(s) are overdue",
                'recommendation': 'Review and prioritize overdue items'
            })

        # Check for pending tasks buildup
        if task_data['pending'] > 10:
            bottlenecks.append({
                'type': 'task_backlog',
                'severity': 'medium',
                'description': f"{task_data['pending']} tasks pending",
                'recommendation': 'Consider batching similar tasks or delegating'
            })

        # Check for in-progress without completion
        if task_data['in_progress'] > 5:
            bottlenecks.append({
                'type': 'wip_limit',
                'severity': 'low',
                'description': f"{task_data['in_progress']} tasks in progress",
                'recommendation': 'Focus on completing existing tasks before starting new ones'
            })

        return bottlenecks

    def _generate_suggestions(
        self,
        revenue: Dict,
        expenses: Dict,
        subscriptions: List[Subscription],
        bottlenecks: List[Dict]
    ) -> List[Dict]:
        """Generate proactive business suggestions."""
        suggestions = []

        # Revenue suggestions
        if revenue['trend'] == 'declining':
            suggestions.append({
                'category': 'Revenue',
                'priority': 'high',
                'suggestion': 'Revenue is declining. Consider reaching out to pending clients or launching a promotion.',
                'action': 'Review outstanding invoices and follow up with clients'
            })

        if revenue['outstanding'] > 1000:
            suggestions.append({
                'category': 'Cash Flow',
                'priority': 'high',
                'suggestion': f"${revenue['outstanding']:.2f} in outstanding invoices",
                'action': 'Send payment reminders to clients with overdue invoices'
            })

        # Expense suggestions
        if expenses['total'] > revenue['total'] and revenue['total'] > 0:
            suggestions.append({
                'category': 'Expenses',
                'priority': 'high',
                'suggestion': 'Expenses exceed revenue this period',
                'action': 'Review and reduce non-essential expenses'
            })

        # Subscription suggestions
        unused_subs = [s for s in subscriptions if s.status == 'review_recommended']
        if unused_subs:
            total_unused = sum(s.cost for s in unused_subs)
            suggestions.append({
                'category': 'Subscriptions',
                'priority': 'medium',
                'suggestion': f"Review {len(unused_subs)} subscription(s) totaling ${total_unused:.2f}/month",
                'action': f"Consider canceling: {', '.join(s.name for s in unused_subs)}"
            })

        # Bottleneck suggestions
        for bottleneck in bottlenecks:
            suggestions.append({
                'category': 'Operations',
                'priority': bottleneck['severity'],
                'suggestion': bottleneck['description'],
                'action': bottleneck['recommendation']
            })

        return suggestions

    def _create_briefing_file(
        self,
        week_start: datetime,
        week_end: datetime,
        revenue: Dict,
        expenses: Dict,
        tasks: Dict,
        social: Dict,
        subscriptions: List[Subscription],
        bottlenecks: List[Dict],
        suggestions: List[Dict]
    ) -> Path:
        """Create the CEO briefing markdown file."""
        # Generate filename
        filename = f"{week_start.strftime('%Y-%m-%d')}_Monday_Briefing.md"
        filepath = self.briefings_folder / filename

        # Generate content
        revenue_trend_emoji = '📈' if revenue['trend'] == 'improving' else '📉' if revenue['trend'] == 'declining' else '➡️'

        content = f'''---
type: weekly_briefing
generated: {datetime.now().isoformat()}
period_start: {week_start.strftime('%Y-%m-%d')}
period_end: {week_end.strftime('%Y-%m-%d')}
---

# Monday Morning CEO Briefing

**Period:** {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

{self._generate_executive_summary(revenue, expenses, tasks, bottlenecks)}

---

## Revenue {revenue_trend_emoji}

| Metric | Value |
|--------|-------|
| **Total Revenue** | ${revenue['total']:.2f} |
| **Invoices Sent** | {revenue['invoices_sent']} |
| **Invoices Paid** | {revenue['invoices_paid']} |
| **Outstanding** | ${revenue['outstanding']:.2f} |
| **Trend** | {revenue['trend'].title()} |

### By Client
{self._format_client_breakdown(revenue['by_client'])}

---

## Expenses

| Metric | Value |
|--------|-------|
| **Total Expenses** | ${expenses['total']:.2f} |
| **Subscriptions** | ${expenses['subscriptions']:.2f} |
| **One-Time** | ${expenses['one_time']:.2f} |

{self._format_flagged_expenses(expenses['flagged'])}

---

## Task Completion

| Metric | Count |
|--------|-------|
| **Completed This Week** | {tasks['completed']} |
| **Pending** | {tasks['pending']} |
| **In Progress** | {tasks['in_progress']} |
| **Overdue** | {tasks['overdue']} |

### By Type
{self._format_task_breakdown(tasks['by_type'])}

---

## Social Media Activity

| Metric | Count |
|--------|-------|
| **Posts Published** | {social['posts_published']} |
| **Scheduled** | {social['scheduled']} |
| **Drafts** | {social['drafts']} |

### By Platform
{self._format_platform_breakdown(social['by_platform'])}

---

## Subscription Audit

| Service | Monthly Cost | Status |
|---------|-------------|--------|
{self._format_subscription_table(subscriptions)}

---

## Bottlenecks Identified

{self._format_bottlenecks(bottlenecks)}

---

## Proactive Suggestions

{self._format_suggestions(suggestions)}

---

## Action Items for This Week

Based on the analysis above, here are the recommended actions:

1. {self._generate_action_items(suggestions, bottlenecks)}

---

*Generated by AI Employee - Gold Tier Weekly Audit System*
'''

        filepath.write_text(content, encoding='utf-8')
        return filepath

    def _generate_executive_summary(
        self,
        revenue: Dict,
        expenses: Dict,
        tasks: Dict,
        bottlenecks: List[Dict]
    ) -> str:
        """Generate executive summary paragraph."""
        summary_parts = []

        # Revenue summary
        if revenue['trend'] == 'improving':
            summary_parts.append(f"Strong week with revenue trending upward (${revenue['total']:.2f}).")
        elif revenue['trend'] == 'declining':
            summary_parts.append(f"Challenging week with revenue at ${revenue['total']:.2f}.")
        else:
            summary_parts.append(f"Steady week with revenue at ${revenue['total']:.2f}.")

        # Task summary
        summary_parts.append(f"{tasks['completed']} tasks completed.")

        # Bottleneck summary
        if bottlenecks:
            high_severity = [b for b in bottlenecks if b.get('severity') == 'high']
            if high_severity:
                summary_parts.append(f"{len(high_severity)} critical issue(s) need attention.")

        return " ".join(summary_parts)

    def _format_client_breakdown(self, by_client: Dict) -> str:
        """Format client revenue breakdown."""
        if not by_client:
            return "*No client-specific revenue recorded*"

        lines = ["| Client | Revenue |", "|--------|---------|"]
        for client, amount in sorted(by_client.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {client} | ${amount:.2f} |")

        return '\n'.join(lines)

    def _format_flagged_expenses(self, flagged: List[Dict]) -> str:
        """Format flagged expenses section."""
        if not flagged:
            return ""

        lines = ["### ⚠️ Flagged Expenses", ""]
        for item in flagged:
            lines.append(f"- **{item['reason']}**: ${item['amount']:.2f} (threshold: ${item['threshold']:.2f})")

        return '\n'.join(lines)

    def _format_task_breakdown(self, by_type: Dict) -> str:
        """Format task type breakdown."""
        if not by_type:
            return "*No task types recorded*"

        lines = ["| Type | Count |", "|------|-------|"]
        for task_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {task_type.replace('_', ' ').title()} | {count} |")

        return '\n'.join(lines)

    def _format_platform_breakdown(self, by_platform: Dict) -> str:
        """Format social media platform breakdown."""
        if not by_platform:
            return "*No social media activity recorded*"

        lines = ["| Platform | Posts |", "|----------|-------|"]
        for platform, count in sorted(by_platform.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {platform} | {count} |")

        return '\n'.join(lines)

    def _format_subscription_table(self, subscriptions: List[Subscription]) -> str:
        """Format subscription audit table."""
        if not subscriptions:
            return "*No subscriptions tracked*"

        lines = []
        for sub in subscriptions:
            status_emoji = "⚠️" if sub.status == 'review_recommended' else "✅"
            lines.append(f"| {sub.name} | ${sub.cost:.2f} | {status_emoji} {sub.status.replace('_', ' ').title()} |")

        return '\n'.join(lines)

    def _format_bottlenecks(self, bottlenecks: List[Dict]) -> str:
        """Format bottlenecks section."""
        if not bottlenecks:
            return "✅ No significant bottlenecks identified."

        lines = []
        for b in bottlenecks:
            severity_emoji = "🔴" if b['severity'] == 'high' else "🟡" if b['severity'] == 'medium' else "🟢"
            lines.append(f"- {severity_emoji} **{b['type'].replace('_', ' ').title()}**: {b['description']}")
            lines.append(f"  - *Recommendation: {b['recommendation']}*")

        return '\n'.join(lines)

    def _format_suggestions(self, suggestions: List[Dict]) -> str:
        """Format suggestions section."""
        if not suggestions:
            return "✅ No specific suggestions at this time. Business is running smoothly!"

        lines = []
        for s in suggestions:
            priority_emoji = "🔴" if s['priority'] == 'high' else "🟡" if s['priority'] == 'medium' else "🟢"
            lines.append(f"- {priority_emoji} **{s['category']}**: {s['suggestion']}")
            lines.append(f"  - *Action: {s['action']}*")

        return '\n'.join(lines)

    def _generate_action_items(
        self,
        suggestions: List[Dict],
        bottlenecks: List[Dict]
    ) -> str:
        """Generate prioritized action items."""
        action_items = []

        # Get high priority items first
        high_priority = [s for s in suggestions if s.get('priority') == 'high']
        for item in high_priority[:3]:  # Top 3
            action_items.append(item['action'])

        # Add bottleneck actions
        for b in bottlenecks[:2]:  # Top 2
            if b['action'] not in action_items:
                action_items.append(b['recommendation'])

        if not action_items:
            return "Continue monitoring business metrics. No urgent actions required."

        return " | ".join(action_items[:5])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Weekly Business Audit & CEO Briefing Generator'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--odoo-config',
        type=str,
        default=None,
        help='Path to Odoo configuration file'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate weekly briefing')
    gen_parser.add_argument('--week-start', type=str, help='Week start date (YYYY-MM-DD)')
    gen_parser.add_argument('--with-odoo', action='store_true', help='Include Odoo data')

    # Schedule command
    subparsers.add_parser('schedule', help='Show schedule command')

    args = parser.parse_args()

    generator = WeeklyAuditGenerator(
        vault_path=args.vault_path,
        odoo_config=args.odoo_config
    )

    if args.command == 'generate':
        week_start = None
        if args.week_start:
            try:
                week_start = datetime.strptime(args.week_start, '%Y-%m-%d')
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return

        print("Generating weekly CEO briefing...")
        briefing_path = generator.generate_weekly_briefing(
            week_start=week_start,
            include_odoo=args.with_odoo
        )
        print(f"\n✅ Briefing generated: {briefing_path}")
        print("\nOpen this file in Obsidian to review the weekly business audit.")

    elif args.command == 'schedule':
        print("\nTo schedule weekly briefings, use Windows Task Scheduler:")
        print(f"""
# Run every Monday at 7:00 AM
schtasks /create /tn "Weekly CEO Briefing" /tr "python {Path(__file__).resolve()} --vault-path {args.vault_path} generate" /sc weekly /d MON /st 07:00
""")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
