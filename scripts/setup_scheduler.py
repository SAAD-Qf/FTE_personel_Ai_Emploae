"""
Task Scheduler Setup

Creates scheduled tasks for Windows Task Scheduler to run AI Employee
components automatically.

Features:
- Start watchers on login
- Run orchestrator periodically
- Generate daily briefings at scheduled time
- Cleanup old logs weekly

Usage:
    python setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . install
    python setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . list
    python setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . remove
"""

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional


class TaskScheduler:
    """Windows Task Scheduler manager."""
    
    def __init__(self, vault_path: str, project_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.project_path = Path(project_path).resolve()
        self.scripts_path = self.project_path / 'scripts'
        self.python_exe = sys.executable
        
        # Task names
        self.task_prefix = 'AI_Employee'
        self.tasks = {
            'watcher_filesystem': f'{self.task_prefix}_FileSystemWatcher',
            'watcher_gmail': f'{self.task_prefix}_GmailWatcher',
            'watcher_whatsapp': f'{self.task_prefix}_WhatsAppWatcher',
            'orchestrator': f'{self.task_prefix}_Orchestrator',
            'daily_briefing': f'{self.task_prefix}_DailyBriefing',
            'cleanup': f'{self.task_prefix}_WeeklyCleanup',
        }
    
    def create_task(
        self,
        task_name: str,
        action: str,
        trigger_type: str,
        trigger_config: dict,
        run_as_user: Optional[str] = None,
        run_with_highest_privileges: bool = False
    ) -> bool:
        """
        Create a scheduled task.
        
        Args:
            task_name: Name of the task
            action: Command to run
            trigger_type: 'login', 'daily', 'weekly', 'idle'
            trigger_config: Trigger-specific configuration
            run_as_user: User account to run as
            run_with_highest_privileges: Run as administrator
        """
        # Build schtasks command
        cmd = ['schtasks', '/Create', '/TN', task_name, '/TR', action]
        
        # Add trigger
        if trigger_type == 'login':
            cmd.extend(['/TRIGGER', 'ONLOGON'])
        elif trigger_type == 'daily':
            time = trigger_config.get('time', '09:00')
            cmd.extend(['/TRIGGER', 'DAILY', '/ST', time])
        elif trigger_type == 'weekly':
            day = trigger_config.get('day', 'SUN')
            time = trigger_config.get('time', '03:00')
            cmd.extend(['/TRIGGER', 'WEEKLY', '/D', day, '/ST', time])
        elif trigger_type == 'idle':
            cmd.extend(['/TRIGGER', 'IDLE'])
        
        # Add action type
        cmd.extend(['/SC', trigger_type.upper()])
        
        # Add user if specified
        if run_as_user:
            cmd.extend(['/RU', run_as_user])
        
        # Add privileges
        if run_with_highest_privileges:
            cmd.append('/RL', 'HIGHEST')
        
        # Add description
        cmd.extend(['/F', '/SD', datetime.now().strftime('%m/%d/%Y')])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f'✓ Created task: {task_name}')
                return True
            else:
                print(f'✗ Failed to create task {task_name}: {result.stderr}')
                return False
        except Exception as e:
            print(f'✗ Error creating task {task_name}: {e}')
            return False
    
    def install_filesystem_watcher(self, interval: int = 30) -> bool:
        """Install filesystem watcher task."""
        action = f'"{self.python_exe}" "{self.scripts_path}\\filesystem_watcher.py" --vault-path "{self.vault_path}" --interval {interval}'
        return self.create_task(
            task_name=self.tasks['watcher_filesystem'],
            action=action,
            trigger_type='login',
            trigger_config={}
        )
    
    def install_gmail_watcher(
        self,
        credentials_path: str,
        interval: int = 120
    ) -> bool:
        """Install Gmail watcher task."""
        action = f'"{self.python_exe}" "{self.scripts_path}\\gmail_watcher.py" --vault-path "{self.vault_path}" --credentials-path "{credentials_path}" --interval {interval}'
        return self.create_task(
            task_name=self.tasks['watcher_gmail'],
            action=action,
            trigger_type='login',
            trigger_config={}
        )
    
    def install_whatsapp_watcher(
        self,
        session_path: str,
        interval: int = 60
    ) -> bool:
        """Install WhatsApp watcher task."""
        action = f'"{self.python_exe}" "{self.scripts_path}\\whatsapp_watcher.py" --vault-path "{self.vault_path}" --session-path "{session_path}" --interval {interval}'
        return self.create_task(
            task_name=self.tasks['watcher_whatsapp'],
            action=action,
            trigger_type='login',
            trigger_config={}
        )
    
    def install_orchestrator(self, interval: int = 60) -> bool:
        """Install orchestrator task."""
        action = f'"{self.python_exe}" "{self.scripts_path}\\orchestrator.py" --vault-path "{self.vault_path}" --continuous --interval {interval}'
        return self.create_task(
            task_name=self.tasks['orchestrator'],
            action=action,
            trigger_type='login',
            trigger_config={}
        )
    
    def install_daily_briefing(self, time: str = '08:00') -> bool:
        """Install daily briefing task."""
        action = f'"{self.python_exe}" "{self.scripts_path}\\daily_briefing.py" --vault-path "{self.vault_path}"'
        return self.create_task(
            task_name=self.tasks['daily_briefing'],
            action=action,
            trigger_type='daily',
            trigger_config={'time': time}
        )
    
    def install_weekly_cleanup(self, day: str = 'SUN', time: str = '03:00') -> bool:
        """Install weekly cleanup task."""
        action = f'"{self.python_exe}" "{self.scripts_path}\\cleanup.py" --vault-path "{self.vault_path}"'
        return self.create_task(
            task_name=self.tasks['cleanup'],
            action=action,
            trigger_type='weekly',
            trigger_config={'day': day, 'time': time}
        )
    
    def install_all(self, email: str = '', credentials_path: str = '') -> bool:
        """Install all scheduled tasks."""
        print("Installing all AI Employee scheduled tasks...\n")
        
        results = []
        
        # Filesystem watcher (always)
        results.append(('Filesystem Watcher', self.install_filesystem_watcher()))
        
        # Gmail watcher (if credentials provided)
        if credentials_path:
            results.append(('Gmail Watcher', self.install_gmail_watcher(credentials_path)))
        else:
            print("⊘ Skipping Gmail Watcher (no credentials path provided)")
        
        # WhatsApp watcher (optional)
        session_path = str(self.vault_path / 'whatsapp_session')
        results.append(('WhatsApp Watcher', self.install_whatsapp_watcher(session_path)))
        
        # Orchestrator
        results.append(('Orchestrator', self.install_orchestrator()))
        
        # Daily briefing
        results.append(('Daily Briefing', self.install_daily_briefing()))
        
        # Weekly cleanup
        results.append(('Weekly Cleanup', self.install_weekly_cleanup()))
        
        # Summary
        print("\n" + "=" * 50)
        print("INSTALLATION SUMMARY")
        print("=" * 50)
        for name, success in results:
            status = '✓' if success else '✗'
            print(f"  {status} {name}")
        
        return all(r[1] for r in results)
    
    def list_tasks(self) -> list:
        """List all AI Employee tasks."""
        try:
            result = subprocess.run(
                ['schtasks', '/Query', '/FO', 'TABLE'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                ai_tasks = [line for line in lines if self.task_prefix in line]
                return ai_tasks
            return []
        except Exception as e:
            print(f'Error listing tasks: {e}')
            return []
    
    def remove_task(self, task_name: str) -> bool:
        """Remove a scheduled task."""
        try:
            result = subprocess.run(
                ['schtasks', '/Delete', '/TN', task_name, '/F'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f'✓ Removed task: {task_name}')
                return True
            else:
                print(f'✗ Failed to remove task {task_name}: {result.stderr}')
                return False
        except Exception as e:
            print(f'✗ Error removing task {task_name}: {e}')
            return False
    
    def remove_all(self) -> bool:
        """Remove all AI Employee tasks."""
        tasks = self.list_tasks()
        
        if not tasks:
            print("No AI Employee tasks found.")
            return True
        
        print(f"Removing {len(tasks)} AI Employee task(s)...\n")
        
        results = []
        for task_line in tasks:
            task_name = task_line.split()[0]
            results.append(self.remove_task(task_name))
        
        return all(results)
    
    def run_task(self, task_name: str) -> bool:
        """Run a task immediately."""
        try:
            result = subprocess.run(
                ['schtasks', '/Run', '/TN', task_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f'✓ Started task: {task_name}')
                return True
            else:
                print(f'✗ Failed to start task {task_name}: {result.stderr}')
                return False
        except Exception as e:
            print(f'✗ Error starting task {task_name}: {e}')
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Task Scheduler Setup for AI Employee'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--project-path',
        type=str,
        default='.',
        help='Path to the project root'
    )
    parser.add_argument(
        '--credentials-path',
        type=str,
        default='',
        help='Path to Gmail credentials file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install scheduled tasks')
    install_parser.add_argument('--all', action='store_true', help='Install all tasks')
    install_parser.add_argument('--filesystem', action='store_true', help='Install filesystem watcher')
    install_parser.add_argument('--gmail', action='store_true', help='Install Gmail watcher')
    install_parser.add_argument('--whatsapp', action='store_true', help='Install WhatsApp watcher')
    install_parser.add_argument('--orchestrator', action='store_true', help='Install orchestrator')
    install_parser.add_argument('--briefing', action='store_true', help='Install daily briefing')
    install_parser.add_argument('--cleanup', action='store_true', help='Install weekly cleanup')
    
    # List command
    subparsers.add_parser('list', help='List installed tasks')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove scheduled tasks')
    remove_parser.add_argument('--all', action='store_true', help='Remove all tasks')
    remove_parser.add_argument('--task', type=str, help='Remove specific task')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a task immediately')
    run_parser.add_argument('--task', type=str, required=True, help='Task to run')
    
    args = parser.parse_args()
    
    scheduler = TaskScheduler(
        vault_path=args.vault_path,
        project_path=args.project_path
    )
    
    if args.command == 'install':
        if args.all:
            scheduler.install_all(credentials_path=args.credentials_path)
        else:
            if args.filesystem:
                scheduler.install_filesystem_watcher()
            if args.gmail and args.credentials_path:
                scheduler.install_gmail_watcher(args.credentials_path)
            if args.whatsapp:
                scheduler.install_whatsapp_watcher(str(scheduler.vault_path / 'whatsapp_session'))
            if args.orchestrator:
                scheduler.install_orchestrator()
            if args.briefing:
                scheduler.install_daily_briefing()
            if args.cleanup:
                scheduler.install_weekly_cleanup()
            
            if not any([args.filesystem, args.gmail, args.whatsapp, args.orchestrator, args.briefing, args.cleanup]):
                install_parser.print_help()
    
    elif args.command == 'list':
        tasks = scheduler.list_tasks()
        if tasks:
            print("AI Employee Scheduled Tasks:")
            print("-" * 50)
            for task in tasks:
                print(f"  {task}")
        else:
            print("No AI Employee tasks found.")
    
    elif args.command == 'remove':
        if args.all:
            scheduler.remove_all()
        elif args.task:
            scheduler.remove_task(args.task)
        else:
            remove_parser.print_help()
    
    elif args.command == 'run':
        scheduler.run_task(args.task)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
