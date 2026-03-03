"""
Vault Sync - Platinum Tier

Handles synchronization between Cloud and Local vaults using Git.
Ensures secure sync without exposing sensitive credentials.

Key Features:
- Git-based sync (recommended for Platinum tier)
- Security rules: Never sync .env, tokens, sessions, banking creds
- Claim-by-move rule enforcement
- Single-writer rule for Dashboard.md (Local only)
- Conflict resolution

Architecture:
- Cloud vault: Pushes updates, drafts, summaries
- Local vault: Pulls updates, pushes approvals, final actions
- Shared remote: Central Git remote for sync

Usage:
    # Initialize sync (first time)
    python vault_sync.py --vault-path ./AI_Employee_Vault init --remote <git-url>
    
    # Push changes
    python vault_sync.py --vault-path ./AI_Employee_Vault push
    
    # Pull changes
    python vault_sync.py --vault-path ./AI_Employee_Vault pull
    
    # Sync status
    python vault_sync.py --vault-path ./AI_Employee_Vault status
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set


# Files and patterns that should NEVER sync to Cloud
SENSITIVE_PATTERNS = [
    '.env',
    '*.key',
    '*.pem',
    '*.crt',
    '*_credentials*',
    '*_token*',
    '*_secret*',
    'credentials.json',
    'service_account*.json',
    '.whatsapp_session',
    'whatsapp_session',
    '*_session',
    'banking*',
    'payment_tokens*',
    'odoo_config.json',
    'mcp.json',
    '.gitignore',  # Local git config
]

# Folders that should NEVER sync to Cloud
SENSITIVE_FOLDERS = [
    '.qwen',  # Qwen Code config
    '.claude',  # Claude Code config (may contain local secrets)
    'Logs/Local',  # Local-only logs
    'Logs/Cloud',  # Cloud-only logs (if running locally)
    '__pycache__',
    '*.pyc',
    '.git',  # Git metadata (handled separately)
]


class VaultSync:
    """
    Vault synchronization manager.
    
    Handles Git-based sync between Cloud and Local vaults.
    """

    def __init__(self, vault_path: str, mode: str = 'local'):
        """
        Initialize vault sync.
        
        Args:
            vault_path: Path to the Obsidian vault
            mode: 'local' or 'cloud' - determines sync behavior
        """
        self.vault_path = Path(vault_path).resolve()
        self.mode = mode  # 'local' or 'cloud'
        self.git_dir = self.vault_path / '.git'
        
        # Setup logging
        self._setup_logging()
        
        # Git configuration
        self.remote_url: Optional[str] = None
        self.branch_name = 'main'
        
        self.logger.info(f"VaultSync initialized (mode: {mode})")
        self.logger.info(f"Vault path: {self.vault_path}")

    def _setup_logging(self):
        """Configure logging."""
        log_dir = self.vault_path / 'Logs' / 'Sync'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('VaultSync')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        cmd = ['git'] + args
        self.logger.debug(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                check=check,
                env=self._get_git_env()
            )
            
            if result.stdout:
                self.logger.debug(f"Git stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"Git stderr: {result.stderr.strip()}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git command failed: {e}")
            self.logger.error(f"Stderr: {e.stderr}")
            raise

    def _get_git_env(self) -> dict:
        """Get environment variables for git commands."""
        env = os.environ.copy()
        
        # Set git user info if not already set
        if 'GIT_AUTHOR_NAME' not in env:
            env['GIT_AUTHOR_NAME'] = f'AI-Employee-{self.mode}'
            env['GIT_AUTHOR_EMAIL'] = f'ai-employee-{self.mode}@local'
            env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
            env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']
        
        return env

    def is_git_repo(self) -> bool:
        """Check if vault is a git repository."""
        return self.git_dir.exists()

    def init_repo(self, remote_url: Optional[str] = None) -> bool:
        """
        Initialize git repository for vault sync.
        
        Args:
            remote_url: Optional Git remote URL
            
        Returns:
            True if successful
        """
        self.logger.info("Initializing Git repository for vault sync")
        
        try:
            # Initialize git repo
            if not self.is_git_repo():
                self._run_git(['init'])
                self.logger.info("Git repository initialized")
            
            # Create .gitignore for sensitive files
            self._create_gitignore()
            
            # Create sync rules documentation
            self._create_sync_rules()
            
            # Set remote if provided
            if remote_url:
                self.set_remote(remote_url)
            
            # Initial commit
            self._run_git(['add', '.'])
            self._run_git(['commit', '-m', 'Initial commit: Vault structure for Platinum tier sync'])
            
            # Push to remote if configured
            if remote_url:
                self._run_git(['push', '-u', 'origin', 'main'], check=False)
            
            self.logger.info("Git repository setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize git repo: {e}", exc_info=True)
            return False

    def _create_gitignore(self):
        """Create .gitignore for sensitive files."""
        gitignore_path = self.vault_path / '.gitignore'
        
        content = """# AI Employee Vault - Git Ignore Rules
# Generated by VaultSync for Platinum Tier

# Sensitive credentials (NEVER sync to Cloud)
.env
*.key
*.pem
*.crt
*_credentials*
*_token*
*_secret*
credentials.json
service_account*.json

# Session files
.whatsapp_session/
whatsapp_session/
*_session/

# Banking and payment
banking*
payment_tokens*
odoo_config.json

# Local configs
.qwen/
.claude/
mcp.json

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Logs (local only)
Logs/Local/
Logs/Cloud/

# OS files
.DS_Store
Thumbs.db
*.swp
*.swo
*~

# IDE
.vscode/
.idea/
*.iml

# Temporary files
*.tmp
*.temp
"""
        
        gitignore_path.write_text(content, encoding='utf-8')
        self.logger.info(f"Created .gitignore: {gitignore_path}")

    def _create_sync_rules(self):
        """Create sync rules documentation."""
        rules_path = self.vault_path / 'SYNC_RULES.md'
        
        content = f"""---
created: {datetime.now().isoformat()}
mode: {self.mode}
version: 1.0
---

# Vault Sync Rules (Platinum Tier)

## Overview

This document defines the synchronization rules between Cloud and Local vaults.

## Security Rules

### NEVER Sync to Cloud

The following files and folders MUST NEVER be synced to the Cloud vault:

1. **Credentials**: `.env`, `*_credentials*`, `*_token*`, `*_secret*`
2. **Sessions**: `.whatsapp_session/`, `*_session/`
3. **Banking**: `banking*`, `payment_tokens*`, `odoo_config.json`
4. **Local Config**: `.qwen/`, `.claude/`, `mcp.json`
5. **Local Logs**: `Logs/Local/`, `Logs/Cloud/`

### Single-Writer Rules

1. **Dashboard.md**: Only Local agent writes to Dashboard.md
2. **Cloud writes to**: `/Updates/`, `/Signals/`, `/Pending_Approval/Cloud/`
3. **Local writes to**: `/Approved/`, `/Rejected/`, `/Done/`, `/Signals/`

## Claim-by-Move Rule

When an agent wants to process a file:

1. Move file from `/Needs_Action/<domain>/` to `/In_Progress/<agent>/`
2. First agent to move owns the file
3. Other agents MUST ignore files in `/In_Progress/<other_agent>/`

## Folder Structure

```
AI_Employee_Vault/
├── Needs_Action/
│   ├── Cloud/          # Cloud agent processes these
│   └── Local/          # Local agent processes these
├── In_Progress/
│   ├── Cloud/          # Files claimed by Cloud
│   └── Local/          # Files claimed by Local
├── Pending_Approval/
│   ├── Cloud/          # Cloud-generated approvals
│   └── Local/          # Local-generated approvals
├── Updates/            # Cloud → Local updates
├── Signals/            # Bidirectional signals
└── Done/              # Completed tasks
```

## Sync Commands

```bash
# Initialize sync
python vault_sync.py --vault-path ./AI_Employee_Vault init --remote <git-url>

# Push changes
python vault_sync.py --vault-path ./AI_Employee_Vault push

# Pull changes
python vault_sync.py --vault-path ./AI_Employee_Vault pull

# Check status
python vault_sync.py --vault-path ./AI_Employee_Vault status
```

## Conflict Resolution

If sync conflicts occur:

1. **Dashboard.md**: Local version always wins (single-writer rule)
2. **Approval files**: Most recent version wins
3. **Log files**: Keep both, merge if possible

## Mode: {self.mode.upper()}

This vault is configured as: **{self.mode.upper()}**

- Cloud mode: Pushes drafts, summaries, email triage
- Local mode: Pushes approvals, final actions, dashboard updates

---
*Generated by VaultSync v1.0*
"""
        
        rules_path.write_text(content, encoding='utf-8')
        self.logger.info(f"Created sync rules: {rules_path}")

    def set_remote(self, remote_url: str, name: str = 'origin') -> bool:
        """Set the Git remote URL."""
        try:
            # Remove existing remote if present
            self._run_git(['remote', 'remove', name], check=False)
            
            # Add new remote
            self._run_git(['remote', 'add', name, remote_url])
            
            self.remote_url = remote_url
            self.logger.info(f"Set remote '{name}' to: {remote_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set remote: {e}", exc_info=True)
            return False

    def push(self, branch: Optional[str] = None) -> bool:
        """
        Push local changes to remote.
        
        Args:
            branch: Branch name (default: main)
        """
        branch = branch or self.branch_name
        
        self.logger.info(f"Pushing changes to remote (branch: {branch})")
        
        try:
            # Stage all changes
            self._run_git(['add', '.'])
            
            # Check if there are changes to commit
            status = self._run_git(['status', '--porcelain'])
            
            if status.stdout.strip():
                # Commit changes
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._run_git([
                    'commit',
                    '-m', f'Auto-commit: {self.mode} update at {timestamp}'
                ])
                self.logger.info("Changes committed")
            
            # Push to remote
            result = self._run_git(['push', 'origin', branch], check=False)
            
            if result.returncode == 0:
                self.logger.info("Push successful")
                return True
            else:
                self.logger.warning(f"Push failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Push failed: {e}", exc_info=True)
            return False

    def pull(self, branch: Optional[str] = None) -> bool:
        """
        Pull changes from remote.
        
        Args:
            branch: Branch name (default: main)
        """
        branch = branch or self.branch_name
        
        self.logger.info(f"Pulling changes from remote (branch: {branch})")
        
        try:
            # Fetch from remote
            self._run_git(['fetch', 'origin'])
            
            # Pull changes
            result = self._run_git(['pull', 'origin', branch], check=False)
            
            if result.returncode == 0:
                self.logger.info("Pull successful")
                
                # Handle any conflicts
                self._handle_pull_conflicts()
                
                return True
            else:
                self.logger.warning(f"Pull failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Pull failed: {e}", exc_info=True)
            return False

    def _handle_pull_conflicts(self):
        """Handle conflicts after pull."""
        # Get list of conflicted files
        try:
            status = self._run_git(['status', '--porcelain'], check=False)
            
            for line in status.stdout.split('\n'):
                if 'U' in line:  # Unmerged (conflicted)
                    filepath = line.split()[-1]
                    self.logger.warning(f"Conflict detected: {filepath}")
                    self._resolve_conflict(Path(filepath))
                    
        except Exception as e:
            self.logger.error(f"Conflict handling failed: {e}", exc_info=True)

    def _resolve_conflict(self, filepath: Path):
        """
        Resolve a sync conflict.
        
        Rules:
        - Dashboard.md: Local version always wins
        - Other files: Keep remote version with local backup
        """
        filename = filepath.name
        
        if filename == 'Dashboard.md':
            # Local version wins
            self.logger.info(f"Resolving Dashboard.md conflict: keeping local version")
            self._run_git(['checkout', '--ours', str(filepath)])
        else:
            # Keep remote, backup local
            backup_path = filepath.with_suffix(filepath.suffix + '.local_backup')
            if filepath.exists():
                shutil.copy2(str(filepath), str(backup_path))
                self.logger.info(f"Backed up local version: {backup_path}")
            
            self._run_git(['checkout', '--theirs', str(filepath)])
            self.logger.info(f"Resolving conflict: kept remote version, backed up local")

    def status(self) -> dict:
        """Get sync status."""
        status_info = {
            'is_git_repo': self.is_git_repo(),
            'mode': self.mode,
            'vault_path': str(self.vault_path),
            'remote_url': None,
            'branch': None,
            'changes': [],
            'errors': [],
        }
        
        if not self.is_git_repo():
            status_info['errors'].append('Not a git repository')
            return status_info
        
        try:
            # Get current branch
            branch_result = self._run_git(['branch', '--show-current'])
            status_info['branch'] = branch_result.stdout.strip()
            
            # Get remote URL
            remote_result = self._run_git(['remote', 'get-url', 'origin'], check=False)
            if remote_result.returncode == 0:
                status_info['remote_url'] = remote_result.stdout.strip()
            
            # Get changes
            status_result = self._run_git(['status', '--porcelain'])
            if status_result.stdout.strip():
                for line in status_result.stdout.split('\n'):
                    if line.strip():
                        status_info['changes'].append(line.strip())
            
            # Get ahead/behind status
            if status_info['remote_url']:
                self._run_git(['fetch', 'origin'], check=False)
                ahead_behind = self._run_git(
                    ['rev-list', '--left-right', '--count', 'HEAD...origin/HEAD'],
                    check=False
                )
                if ahead_behind.returncode == 0:
                    parts = ahead_behind.stdout.strip().split('\t')
                    if len(parts) == 2:
                        status_info['ahead'] = int(parts[0])
                        status_info['behind'] = int(parts[1])
            
        except Exception as e:
            status_info['errors'].append(str(e))
        
        return status_info

    def log(self, limit: int = 10) -> List[dict]:
        """Get recent sync log."""
        try:
            log_result = self._run_git([
                'log',
                f'-{limit}',
                '--format=%H|%ai|%an|%s'
            ])
            
            entries = []
            for line in log_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        entries.append({
                            'hash': parts[0],
                            'timestamp': parts[1],
                            'author': parts[2],
                            'message': '|'.join(parts[3:]),
                        })
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Failed to get log: {e}", exc_info=True)
            return []


# Import shutil for conflict backup
import shutil


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Vault Sync - Platinum Tier')
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['local', 'cloud'],
        default='local',
        help='Sync mode: local or cloud (default: local)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize git repo for sync')
    init_parser.add_argument(
        '--remote',
        type=str,
        required=True,
        help='Git remote URL'
    )
    
    # Push command
    subparsers.add_parser('push', help='Push changes to remote')
    
    # Pull command
    subparsers.add_parser('pull', help='Pull changes from remote')
    
    # Status command
    subparsers.add_parser('status', help='Show sync status')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Show sync log')
    log_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of entries to show (default: 10)'
    )
    
    args = parser.parse_args()
    
    sync = VaultSync(
        vault_path=args.vault_path,
        mode=args.mode
    )
    
    if args.command == 'init':
        success = sync.init_repo(remote_url=args.remote)
        sys.exit(0 if success else 1)
        
    elif args.command == 'push':
        success = sync.push()
        sys.exit(0 if success else 1)
        
    elif args.command == 'pull':
        success = sync.pull()
        sys.exit(0 if success else 1)
        
    elif args.command == 'status':
        status = sync.status()
        print(json.dumps(status, indent=2))
        
    elif args.command == 'log':
        entries = sync.log(limit=args.limit)
        for entry in entries:
            print(f"{entry['timestamp']} - {entry['author']}: {entry['message']}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
