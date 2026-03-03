"""
Cleanup Utility

Weekly cleanup utility for AI Employee system.
Removes old logs, archives completed items, and cleans up temp files.

Usage:
    python cleanup.py --vault-path ./AI_Employee_Vault
"""

import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict


class CleanupUtility:
    """System cleanup utility."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs'
        self.done_folder = self.vault_path / 'Done'
        self.rejected_folder = self.vault_path / 'Rejected'
        self.inbox_files = self.vault_path / 'Inbox' / 'Files'
        
        # Retention periods (days)
        self.log_retention = 90
        self.done_retention = 365
        self.rejected_retention = 30
    
    def cleanup_old_logs(self, dry_run: bool = False) -> int:
        """Remove logs older than retention period."""
        count = 0
        cutoff = datetime.now() - timedelta(days=self.log_retention)
        
        if not self.logs_folder.exists():
            return count
        
        for log_file in self.logs_folder.glob('*.log'):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    if dry_run:
                        print(f'Would delete: {log_file.name}')
                    else:
                        log_file.unlink()
                    count += 1
            except Exception as e:
                print(f'Error processing {log_file}: {e}')
        
        # Also cleanup JSON logs
        for json_file in self.logs_folder.glob('*.json'):
            try:
                mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
                if mtime < cutoff:
                    if dry_run:
                        print(f'Would delete: {json_file.name}')
                    else:
                        json_file.unlink()
                    count += 1
            except Exception as e:
                print(f'Error processing {json_file}: {e}')
        
        return count
    
    def archive_old_done_items(self, dry_run: bool = False) -> int:
        """Archive completed items older than retention period."""
        count = 0
        cutoff = datetime.now() - timedelta(days=self.done_retention)
        
        archive_folder = self.done_folder / 'Archive'
        
        if not self.done_folder.exists():
            return count
        
        for item_file in self.done_folder.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(item_file.stat().st_mtime)
                if mtime < cutoff:
                    if dry_run:
                        print(f'Would archive: {item_file.name}')
                    else:
                        archive_folder.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(item_file), str(archive_folder / item_file.name))
                    count += 1
            except Exception as e:
                print(f'Error processing {item_file}: {e}')
        
        return count
    
    def cleanup_rejected(self, dry_run: bool = False) -> int:
        """Remove rejected items older than retention period."""
        count = 0
        cutoff = datetime.now() - timedelta(days=self.rejected_retention)
        
        if not self.rejected_folder.exists():
            return count
        
        for item_file in self.rejected_folder.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(item_file.stat().st_mtime)
                if mtime < cutoff:
                    if dry_run:
                        print(f'Would delete: {item_file.name}')
                    else:
                        item_file.unlink()
                    count += 1
            except Exception as e:
                print(f'Error processing {item_file}: {e}')
        
        return count
    
    def cleanup_temp_files(self, dry_run: bool = False) -> int:
        """Remove temporary files."""
        count = 0
        
        # Clean up .processed_files hash file if too large
        hash_file = self.vault_path / '.processed_files'
        if hash_file.exists():
            try:
                size = hash_file.stat().st_size
                if size > 1024 * 1024:  # > 1MB
                    if dry_run:
                        print(f'Would truncate: .processed_files ({size} bytes)')
                    else:
                        # Keep only last 1000 hashes
                        with open(hash_file, 'r') as f:
                            lines = f.readlines()
                        with open(hash_file, 'w') as f:
                            f.writelines(lines[-1000:])
                    count += 1
            except Exception as e:
                print(f'Error processing hash file: {e}')
        
        return count
    
    def generate_report(self) -> Dict:
        """Generate cleanup report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'vault_path': str(self.vault_path),
            'folders': {}
        }
        
        # Count items in each folder
        folders = {
            'Inbox': self.vault_path / 'Inbox',
            'Needs_Action': self.vault_path / 'Needs_Action',
            'Done': self.vault_folder / 'Done',
            'Pending_Approval': self.vault_path / 'Pending_Approval',
            'Logs': self.logs_folder,
        }
        
        for name, folder in folders.items():
            if folder.exists():
                count = len(list(folder.glob('*.md')))
                report['folders'][name] = count
        
        return report
    
    def run_all(self, dry_run: bool = False) -> Dict:
        """Run all cleanup tasks."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'logs_deleted': self.cleanup_old_logs(dry_run),
            'done_archived': self.archive_old_done_items(dry_run),
            'rejected_deleted': self.cleanup_rejected(dry_run),
            'temp_cleaned': self.cleanup_temp_files(dry_run)
        }
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Cleanup Utility'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate storage report only'
    )
    
    args = parser.parse_args()
    
    utility = CleanupUtility(vault_path=args.vault_path)
    
    if args.report:
        report = utility.generate_report()
        print(json.dumps(report, indent=2))
    else:
        results = utility.run_all(dry_run=args.dry_run)
        
        print("\n" + "=" * 50)
        print("CLEANUP RESULTS")
        print("=" * 50)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Dry Run: {results['dry_run']}")
        print(f"  Logs deleted: {results['logs_deleted']}")
        print(f"  Done items archived: {results['done_archived']}")
        print(f"  Rejected items deleted: {results['rejected_deleted']}")
        print(f"  Temp files cleaned: {results['temp_cleaned']}")


if __name__ == '__main__':
    main()
