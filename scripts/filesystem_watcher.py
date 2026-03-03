"""
File System Watcher

Monitors a drop folder for new files and creates action files
in the Needs_Action folder for Claude Code to process.

This is the Bronze Tier watcher - simple, reliable, and doesn't
require any API credentials.

Usage:
    python filesystem_watcher.py --vault-path ./AI_Employee_Vault
    python filesystem_watcher.py --vault-path ./AI_Employee_Vault --watch-folder ./DropFolder
"""

import argparse
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher


class FileDropItem:
    """Represents a file dropped for processing."""
    
    def __init__(self, source_path: Path, file_hash: str):
        self.source_path = source_path
        self.file_hash = file_hash
        self.name = source_path.name
        self.size = source_path.stat().st_size
        self.created = datetime.fromtimestamp(source_path.stat().st_ctime)
        self.modified = datetime.fromtimestamp(source_path.stat().st_mtime)


class FileSystemWatcher(BaseWatcher):
    """
    Watches a folder for new files and creates action files.
    
    Files dropped into the watch folder are copied to the vault
    and an action file is created in Needs_Action.
    """
    
    def __init__(
        self,
        vault_path: str,
        watch_folder: Optional[str] = None,
        check_interval: int = 30
    ):
        """
        Initialize the file system watcher.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            watch_folder: Path to folder to watch (default: vault/Inbox)
            check_interval: Seconds between checks (default: 30)
        """
        super().__init__(vault_path, check_interval)
        
        # Set up watch folder
        if watch_folder:
            self.watch_folder = Path(watch_folder)
        else:
            self.watch_folder = self.inbox
        
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed files by hash
        self.processed_hashes: set = set()
        
        # Load existing processed hashes from log
        self._load_processed_hashes()
        
        self.logger.info(f'Watch folder: {self.watch_folder}')
    
    def _load_processed_hashes(self):
        """Load hashes of already processed files."""
        hash_file = self.vault_path / '.processed_files'
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                self.processed_hashes = set(line.strip() for line in f)
            self.logger.info(f'Loaded {len(self.processed_hashes)} processed file hashes')
    
    def _save_hash(self, file_hash: str):
        """Save a file hash to the processed list."""
        hash_file = self.vault_path / '.processed_files'
        with open(hash_file, 'a') as f:
            f.write(file_hash + '\n')
        self.processed_hashes.add(file_hash)
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _detect_priority(self, filename: str) -> str:
        """Detect priority based on filename keywords."""
        filename_lower = filename.lower()
        
        high_priority_keywords = ['urgent', 'asap', 'emergency', 'invoice', 'payment']
        medium_priority_keywords = ['important', 'review', 'action', 'todo']
        
        for keyword in high_priority_keywords:
            if keyword in filename_lower:
                return 'high'
        
        for keyword in medium_priority_keywords:
            if keyword in filename_lower:
                return 'medium'
        
        return 'normal'
    
    def _detect_type(self, filename: str) -> str:
        """Detect document type based on filename."""
        filename_lower = filename.lower()
        
        type_mapping = {
            'invoice': 'invoice',
            'receipt': 'receipt',
            'contract': 'contract',
            'agreement': 'contract',
            'proposal': 'proposal',
            'quote': 'quote',
            'report': 'report',
            'brief': 'brief',
            'memo': 'memo',
        }
        
        for keyword, doc_type in type_mapping.items():
            if keyword in filename_lower:
                return doc_type
        
        return 'general'
    
    def check_for_updates(self) -> List[FileDropItem]:
        """
        Check the watch folder for new files.
        
        Returns:
            List of new FileDropItem objects
        """
        new_items = []
        
        try:
            # Get all files in watch folder (not directories)
            files = [f for f in self.watch_folder.iterdir() if f.is_file()]
            
            for file_path in files:
                # Skip hidden files and our own tracking file
                if file_path.name.startswith('.'):
                    continue
                
                # Calculate hash
                file_hash = self._calculate_hash(file_path)
                
                # Skip if already processed
                if file_hash in self.processed_hashes:
                    self.logger.debug(f'Skipping already processed: {file_path.name}')
                    continue
                
                # Create item
                item = FileDropItem(file_path, file_hash)
                new_items.append(item)
                
        except FileNotFoundError:
            self.logger.error(f'Watch folder not found: {self.watch_folder}')
        except PermissionError as e:
            self.logger.error(f'Permission denied: {e}')
        except Exception as e:
            self.logger.error(f'Error checking watch folder: {e}', exc_info=True)
        
        return new_items
    
    def create_action_file(self, item: FileDropItem) -> Optional[Path]:
        """
        Create an action file for a dropped file.
        
        Copies the file to the vault and creates a markdown action file.
        
        Args:
            item: The FileDropItem to process
            
        Returns:
            Path to the created action file
        """
        try:
            # Create a safe filename for the action file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = item.name.replace(' ', '_').replace('-', '_')
            action_filename = f'FILE_DROP_{timestamp}_{safe_name}.md'
            action_filepath = self.needs_action / action_filename
            
            # Copy file to vault storage
            storage_folder = self.vault_path / 'Inbox' / 'Files'
            storage_folder.mkdir(parents=True, exist_ok=True)
            dest_path = storage_folder / f'{timestamp}_{item.name}'
            shutil.copy2(item.source_path, dest_path)
            
            # Detect priority and type
            priority = self._detect_priority(item.name)
            doc_type = self._detect_type(item.name)
            
            # Generate frontmatter
            frontmatter = self.generate_frontmatter(
                item_type='file_drop',
                priority=priority,
                document_type=doc_type,
                original_name=f'"{item.name}"',
                size=item.size,
                stored_path=f'"{dest_path.relative_to(self.vault_path)}"'
            )
            
            # Generate content
            content = f'''{frontmatter}

# File Drop: {item.name}

## File Information

| Property | Value |
|----------|-------|
| **Original Name** | {item.name} |
| **Size** | {self._format_size(item.size)} |
| **Detected Type** | {doc_type} |
| **Priority** | {priority} |
| **Created** | {item.created.strftime('%Y-%m-%d %H:%M')} |
| **Modified** | {item.modified.strftime('%Y-%m-%d %H:%M')} |

## File Location

- **Storage:** `{dest_path.relative_to(self.vault_path)}`
- **Original:** `{item.source_path}`

## Suggested Actions

- [ ] Review file contents
- [ ] Categorize appropriately
- [ ] Take necessary action
- [ ] Move to /Done when complete

## Notes

*Add notes here after reviewing the file.*

---
*Created by FileSystemWatcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
            
            # Write action file
            action_filepath.write_text(content, encoding='utf-8')
            
            # Save hash to prevent reprocessing
            self._save_hash(item.file_hash)
            
            # Log the action
            self.log_action('file_drop', {
                'filename': item.name,
                'size': item.size,
                'priority': priority,
                'action_file': str(action_filepath)
            })
            
            self.logger.info(f'Created action file for: {item.name}')
            return action_filepath
            
        except Exception as e:
            self.logger.error(f'Failed to create action file: {e}', exc_info=True)
            return None
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='File System Watcher for AI Employee'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--watch-folder',
        type=str,
        default=None,
        help='Folder to watch (default: vault/Inbox)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Create and run watcher
    watcher = FileSystemWatcher(
        vault_path=args.vault_path,
        watch_folder=args.watch_folder,
        check_interval=args.interval
    )
    watcher.run()


if __name__ == '__main__':
    main()
