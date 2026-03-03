"""
Comprehensive Audit Logging System

Provides detailed audit logging for all AI Employee actions.
Features:
- Structured JSON logging
- Daily log rotation
- Action categorization
- Search and filter capabilities
- Compliance reporting
- Activity summaries

Usage:
    python audit_logger.py --vault-path ./AI_Employee_Vault log action_type --details '{"key": "value"}'
    python audit_logger.py --vault-path ./AI_Employee_Vault search --type email_send
    python audit_logger.py --vault-path ./AI_Employee_Vault summary --days 7
    python audit_logger.py --vault-path ./AI_Employee_Vault export --format csv
"""

import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import csv
import io


class ActionType(Enum):
    """Categories of auditable actions."""
    # Communication
    EMAIL_RECEIVED = 'email_received'
    EMAIL_SENT = 'email_send'
    EMAIL_DRAFTED = 'email_draft'
    WHATSAPP_RECEIVED = 'whatsapp_message'
    WHATSAPP_SENT = 'whatsapp_send'
    SOCIAL_POST = 'social_post'
    
    # File Operations
    FILE_RECEIVED = 'file_drop'
    FILE_CREATED = 'file_created'
    FILE_MODIFIED = 'file_modified'
    FILE_DELETED = 'file_delete'
    FILE_MOVED = 'file_moved'
    
    # Task Management
    TASK_CREATED = 'task_created'
    TASK_STARTED = 'task_started'
    TASK_COMPLETED = 'task_completed'
    TASK_MOVED_TO_DONE = 'moved_to_done'
    PLAN_CREATED = 'plan_created'
    PLAN_UPDATED = 'plan_updated'
    
    # Approval Workflow
    APPROVAL_REQUESTED = 'approval_requested'
    APPROVAL_GRANTED = 'approval_granted'
    APPROVAL_REJECTED = 'approval_rejected'
    APPROVAL_EXECUTED = 'approval_executed'
    APPROVAL_EXPIRED = 'approval_expired'
    
    # Financial
    INVOICE_CREATED = 'invoice_created'
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_SENT = 'payment_sent'
    EXPENSE_RECORDED = 'expense_recorded'
    
    # System
    WATCHER_STARTED = 'watcher_started'
    WATCHER_STOPPED = 'watcher_stopped'
    ORCHESTRATOR_CYCLE = 'orchestrator_cycle'
    ERROR_OCCURRED = 'error_occurred'
    CONFIG_CHANGED = 'config_changed'
    
    # Audit
    BRIEFING_GENERATED = 'briefing_generated'
    AUDIT_EXPORT = 'audit_export'
    REPORT_GENERATED = 'report_generated'
    
    # Custom
    CUSTOM = 'custom'


class Severity(Enum):
    """Action severity levels."""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    timestamp: str
    action_type: str
    actor: str
    severity: str = 'info'
    description: str = ''
    details: Dict[str, Any] = field(default_factory=dict)
    vault_path: str = ''
    related_files: List[str] = field(default_factory=list)
    session_id: str = ''
    entry_id: str = ''
    
    def __post_init__(self):
        if not self.entry_id:
            # Generate unique entry ID
            content = f"{self.timestamp}{self.action_type}{self.actor}{json.dumps(self.details)}"
            self.entry_id = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEntry':
        """Create from dictionary."""
        return cls(**data)


class AuditLogger:
    """
    Comprehensive audit logging system.
    
    Features:
    - Structured JSON logging
    - Daily log rotation
    - Search and filter
    - Activity summaries
    - Export capabilities
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize audit logger.
        
        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs'
        self.audit_folder = self.logs_folder / 'Audit'
        
        # Ensure folders exist
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        self.audit_folder.mkdir(parents=True, exist_ok=True)
        
        # Current session ID
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Default actor
        self.default_actor = 'ai_employee'
    
    def log(
        self,
        action_type: Union[ActionType, str],
        actor: Optional[str] = None,
        description: str = '',
        details: Optional[Dict] = None,
        severity: Severity = Severity.INFO,
        related_files: Optional[List[str]] = None
    ) -> AuditEntry:
        """
        Log an action.
        
        Args:
            action_type: Type of action
            actor: Who performed the action
            description: Human-readable description
            details: Additional details dictionary
            severity: Severity level
            related_files: Related file paths
            
        Returns:
            Created audit entry
        """
        # Convert action type to string
        if isinstance(action_type, ActionType):
            action_type_str = action_type.value
        else:
            action_type_str = str(action_type)
        
        # Create entry
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action_type=action_type_str,
            actor=actor or self.default_actor,
            severity=severity.value,
            description=description,
            details=details or {},
            vault_path=str(self.vault_path),
            related_files=related_files or [],
            session_id=self.session_id
        )
        
        # Write to log file
        self._write_entry(entry)
        
        return entry
    
    def _write_entry(self, entry: AuditEntry):
        """Write entry to daily log file."""
        # Get daily log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.audit_folder / f'{date_str}.jsonl'
        
        # Append entry
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry.to_json() + '\n')
    
    def search(
        self,
        action_type: Optional[str] = None,
        actor: Optional[str] = None,
        severity: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        keyword: Optional[str] = None
    ) -> List[AuditEntry]:
        """
        Search audit logs.
        
        Args:
            action_type: Filter by action type
            actor: Filter by actor
            severity: Filter by severity
            date_from: Start date
            date_to: End date
            keyword: Search in description and details
            
        Returns:
            List of matching entries
        """
        results = []
        
        # Determine date range
        if date_from is None:
            date_from = datetime.now() - timedelta(days=30)
        if date_to is None:
            date_to = datetime.now()
        
        # Search log files
        for log_file in self.audit_folder.glob('*.jsonl'):
            # Check if file is in date range
            try:
                file_date = datetime.strptime(log_file.stem, '%Y-%m-%d')
                if not (date_from <= file_date <= date_to):
                    continue
            except ValueError:
                pass
            
            # Read entries
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = AuditEntry.from_dict(json.loads(line.strip()))
                        
                        # Apply filters
                        if action_type and entry.action_type != action_type:
                            continue
                        if actor and entry.actor != actor:
                            continue
                        if severity and entry.severity != severity:
                            continue
                        
                        # Keyword search
                        if keyword:
                            keyword_lower = keyword.lower()
                            if (keyword_lower not in entry.description.lower() and
                                keyword_lower not in json.dumps(entry.details).lower()):
                                continue
                        
                        results.append(entry)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error reading log entry: {e}")
        
        # Sort by timestamp
        results.sort(key=lambda e: e.timestamp, reverse=True)
        
        return results
    
    def get_summary(
        self,
        days: int = 7,
        group_by: str = 'action_type'
    ) -> Dict:
        """
        Get audit summary.
        
        Args:
            days: Number of days to summarize
            group_by: Group results by (action_type, actor, severity)
            
        Returns:
            Summary dictionary
        """
        entries = self.search(
            date_from=datetime.now() - timedelta(days=days)
        )
        
        # Group entries
        groups: Dict[str, List[AuditEntry]] = {}
        for entry in entries:
            if group_by == 'action_type':
                key = entry.action_type
            elif group_by == 'actor':
                key = entry.actor
            elif group_by == 'severity':
                key = entry.severity
            else:
                key = 'all'
            
            if key not in groups:
                groups[key] = []
            groups[key].append(entry)
        
        # Build summary
        summary = {
            'period': {
                'days': days,
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            },
            'total_entries': len(entries),
            'by_type': {k: len(v) for k, v in groups.items()},
            'severity_breakdown': {
                'debug': sum(1 for e in entries if e.severity == 'debug'),
                'info': sum(1 for e in entries if e.severity == 'info'),
                'warning': sum(1 for e in entries if e.severity == 'warning'),
                'error': sum(1 for e in entries if e.severity == 'error'),
                'critical': sum(1 for e in entries if e.severity == 'critical')
            },
            'most_active_actor': max(
                groups.keys(),
                key=lambda k: len(groups[k])
            ) if groups else None,
            'top_actions': sorted(
                [(k, len(v)) for k, v in groups.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        return summary
    
    def export(
        self,
        format: str = 'json',
        output_path: Optional[str] = None,
        **search_kwargs
    ) -> Path:
        """
        Export audit logs.
        
        Args:
            format: Export format (json, csv)
            output_path: Output file path
            search_kwargs: Search filters
            
        Returns:
            Path to exported file
        """
        entries = self.search(**search_kwargs)
        
        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.logs_folder / f'audit_export_{timestamp}.{format}'
        else:
            output_path = Path(output_path)
        
        if format == 'json':
            self._export_json(entries, output_path)
        elif format == 'csv':
            self._export_csv(entries, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Log the export
        self.log(
            action_type=ActionType.AUDIT_EXPORT,
            description=f'Exported {len(entries)} audit entries to {format}',
            details={'format': format, 'output': str(output_path), 'count': len(entries)}
        )
        
        return output_path
    
    def _export_json(self, entries: List[AuditEntry], output_path: Path):
        """Export to JSON."""
        data = {
            'exported_at': datetime.now().isoformat(),
            'count': len(entries),
            'entries': [e.to_dict() for e in entries]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _export_csv(self, entries: List[AuditEntry], output_path: Path):
        """Export to CSV."""
        output = io.StringIO()
        
        # Define columns
        fieldnames = [
            'timestamp', 'action_type', 'actor', 'severity',
            'description', 'details', 'related_files', 'entry_id'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in entries:
            row = entry.to_dict()
            row['details'] = json.dumps(row['details'])
            row['related_files'] = ', '.join(row['related_files'])
            writer.writerow(row)
        
        output_path.write_text(output.getvalue(), encoding='utf-8')
    
    def generate_report(
        self,
        period_days: int = 7,
        include_details: bool = False
    ) -> Path:
        """
        Generate audit report.
        
        Args:
            period_days: Report period in days
            include_details: Include detailed entries
            
        Returns:
            Path to report file
        """
        summary = self.get_summary(days=period_days)
        entries = self.search(date_from=datetime.now() - timedelta(days=period_days))
        
        # Generate report
        report_path = self.audit_folder / f'Audit_Report_{datetime.now().strftime("%Y%m%d")}.md'
        
        content = f'''---
type: audit_report
generated: {datetime.now().isoformat()}
period_days: {period_days}
---

# Audit Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Period:** Last {period_days} days

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Entries** | {summary['total_entries']} |
| **Unique Action Types** | {len(summary['by_type'])} |
| **Most Active Actor** | {summary['most_active_actor'] or 'N/A'} |

---

## Severity Breakdown

| Severity | Count |
|----------|-------|
| Critical | {summary['severity_breakdown']['critical']} |
| Error | {summary['severity_breakdown']['error']} |
| Warning | {summary['severity_breakdown']['warning']} |
| Info | {summary['severity_breakdown']['info']} |
| Debug | {summary['severity_breakdown']['debug']} |

---

## Top Actions

| Action Type | Count |
|-------------|-------|
'''
        
        for action, count in summary['top_actions'][:10]:
            content += f"| {action} | {count} |\n"
        
        if include_details:
            content += '''
---

## Detailed Entries

'''
            for entry in entries[:100]:  # Limit to 100 entries
                content += f'''
### {entry.entry_id}

- **Timestamp:** {entry.timestamp}
- **Action:** {entry.action_type}
- **Actor:** {entry.actor}
- **Severity:** {entry.severity}
- **Description:** {entry.description}
- **Details:** {json.dumps(entry.details, indent=2)}

---
'''
        
        content += f'''
---

*Generated by AI Employee Audit Logger*
'''
        
        report_path.write_text(content, encoding='utf-8')
        return report_path
    
    def cleanup_old_logs(self, keep_days: int = 90) -> int:
        """
        Clean up old log files.
        
        Args:
            keep_days: Number of days to keep
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        for log_file in self.audit_folder.glob('*.jsonl'):
            try:
                file_date = datetime.strptime(log_file.stem, '%Y-%m-%d')
                if file_date < cutoff:
                    log_file.unlink()
                    deleted += 1
            except ValueError:
                pass
        
        return deleted


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Audit Logger'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Log an action')
    log_parser.add_argument('action_type', type=str, help='Action type')
    log_parser.add_argument('--actor', type=str, default='cli', help='Actor name')
    log_parser.add_argument('--description', type=str, help='Description')
    log_parser.add_argument('--details', type=str, help='JSON details')
    log_parser.add_argument('--severity', type=str, default='info',
                          choices=['debug', 'info', 'warning', 'error', 'critical'])
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search logs')
    search_parser.add_argument('--type', type=str, help='Action type filter')
    search_parser.add_argument('--actor', type=str, help='Actor filter')
    search_parser.add_argument('--severity', type=str, help='Severity filter')
    search_parser.add_argument('--from', type=str, dest='date_from', help='Start date (YYYY-MM-DD)')
    search_parser.add_argument('--to', type=str, dest='date_to', help='End date (YYYY-MM-DD)')
    search_parser.add_argument('--keyword', type=str, help='Keyword search')
    search_parser.add_argument('--limit', type=int, default=20, help='Max results')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Get summary')
    summary_parser.add_argument('--days', type=int, default=7, help='Number of days')
    summary_parser.add_argument('--group-by', type=str, default='action_type',
                               choices=['action_type', 'actor', 'severity'])
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export logs')
    export_parser.add_argument('--format', type=str, default='json',
                              choices=['json', 'csv'])
    export_parser.add_argument('--output', type=str, help='Output file path')
    export_parser.add_argument('--days', type=int, default=30, help='Days to export')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate report')
    report_parser.add_argument('--days', type=int, default=7, help='Report period')
    report_parser.add_argument('--details', action='store_true', help='Include details')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old logs')
    cleanup_parser.add_argument('--keep-days', type=int, default=90, help='Days to keep')
    
    args = parser.parse_args()
    
    logger = AuditLogger(vault_path=args.vault_path)
    
    if args.command == 'log':
        details = json.loads(args.details) if args.details else {}
        entry = logger.log(
            action_type=args.action_type,
            actor=args.actor,
            description=args.description,
            details=details,
            severity=Severity(args.severity)
        )
        print(f"Logged: {entry.entry_id}")
    
    elif args.command == 'search':
        date_from = datetime.strptime(args.date_from, '%Y-%m-%d') if args.date_from else None
        date_to = datetime.strptime(args.date_to, '%Y-%m-%d') if args.date_to else None
        
        results = logger.search(
            action_type=args.type,
            actor=args.actor,
            severity=args.severity,
            date_from=date_from,
            date_to=date_to,
            keyword=args.keyword
        )
        
        print(f"Found {len(results)} entries:\n")
        for entry in results[:args.limit]:
            print(f"[{entry.timestamp}] {entry.action_type} - {entry.actor}")
            if entry.description:
                print(f"  {entry.description}")
            print()
    
    elif args.command == 'summary':
        summary = logger.get_summary(days=args.days, group_by=args.group_by)
        print(f"Audit Summary (Last {args.days} days)")
        print("=" * 50)
        print(f"Total Entries: {summary['total_entries']}")
        print(f"Most Active Actor: {summary['most_active_actor']}")
        print(f"\nSeverity Breakdown:")
        for sev, count in summary['severity_breakdown'].items():
            print(f"  {sev.title()}: {count}")
        print(f"\nTop Actions:")
        for action, count in summary['top_actions'][:5]:
            print(f"  {action}: {count}")
    
    elif args.command == 'export':
        output = logger.export(
            format=args.format,
            output_path=args.output,
            date_from=datetime.now() - timedelta(days=args.days)
        )
        print(f"Exported to: {output}")
    
    elif args.command == 'report':
        report = logger.generate_report(period_days=args.days, include_details=args.details)
        print(f"Report generated: {report}")
    
    elif args.command == 'cleanup':
        deleted = logger.cleanup_old_logs(keep_days=args.keep_days)
        print(f"Deleted {deleted} old log file(s)")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
