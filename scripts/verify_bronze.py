"""
Bronze Tier Verification Script

Verifies that all Bronze Tier requirements are met:
- Obsidian vault with Dashboard.md and Company_Handbook.md
- One working Watcher script (File System)
- Basic folder structure: /Inbox, /Needs_Action, /Done
- Claude Code can read from and write to the vault

Usage:
    python verify_bronze.py --vault-path ./AI_Employee_Vault
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class BronzeVerifier:
    """Verifies Bronze Tier completion."""
    
    REQUIRED_FILES = [
        'Dashboard.md',
        'Company_Handbook.md',
        'Business_Goals.md',
    ]
    
    REQUIRED_FOLDERS = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Plans',
        'Pending_Approval',
        'Approved',
        'Rejected',
        'Briefings',
        'Logs',
    ]
    
    REQUIRED_SCRIPTS = [
        'base_watcher.py',
        'filesystem_watcher.py',
        'orchestrator.py',
    ]
    
    def __init__(self, vault_path: str, project_path: str):
        """
        Initialize verifier.
        
        Args:
            vault_path: Path to the Obsidian vault
            project_path: Path to the project root (contains scripts/)
        """
        self.vault_path = Path(vault_path).resolve()
        self.project_path = Path(project_path).resolve()
        self.scripts_path = self.project_path / 'scripts'
        
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def verify_all(self) -> bool:
        """
        Run all verification checks.
        
        Returns:
            True if all required checks pass
        """
        print("=" * 60)
        print("BRONZE TIER VERIFICATION")
        print("=" * 60)
        print(f"\nVault Path: {self.vault_path}")
        print(f"Project Path: {self.project_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run checks
        self._check_vault_exists()
        self._check_required_files()
        self._check_required_folders()
        self._check_watcher_scripts()
        self._check_dashboard_content()
        self._check_company_handbook_content()
        self._check_claude_available()
        self._test_watcher_import()
        
        # Summary
        print()
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"✓ Passed:   {self.passed}")
        print(f"✗ Failed:   {self.failed}")
        print(f"⚠ Warnings: {self.warnings}")
        print()
        
        if self.failed == 0:
            print("🎉 BRONZE TIER VERIFICATION PASSED!")
            print()
            print("Next steps:")
            print("1. Drop a test file into AI_Employee_Vault/Inbox/")
            print("2. Run: python scripts/filesystem_watcher.py --vault-path ./AI_Employee_Vault")
            print("3. Check AI_Employee_Vault/Needs_Action/ for the created action file")
            print("4. Run: claude --prompt \"Process the pending item in Needs_Action\"")
            return True
        else:
            print("❌ BRONZE TIER VERIFICATION FAILED")
            print()
            print("Please fix the failed checks above.")
            return False
    
    def _pass(self, message: str):
        """Mark a check as passed."""
        print(f"✓ {message}")
        self.passed += 1
    
    def _fail(self, message: str):
        """Mark a check as failed."""
        print(f"✗ {message}")
        self.failed += 1
    
    def _warn(self, message: str):
        """Mark a check as warning."""
        print(f"⚠ {message}")
        self.warnings += 1
    
    def _check_vault_exists(self):
        """Check if vault directory exists."""
        if self.vault_path.exists() and self.vault_path.is_dir():
            self._pass(f"Vault directory exists: {self.vault_path}")
        else:
            self._fail(f"Vault directory not found: {self.vault_path}")
    
    def _check_required_files(self):
        """Check if required files exist in vault."""
        print("\n--- Required Vault Files ---")
        
        for filename in self.REQUIRED_FILES:
            filepath = self.vault_path / filename
            if filepath.exists():
                self._pass(f"File exists: {filename}")
            else:
                self._fail(f"File missing: {filename}")
    
    def _check_required_folders(self):
        """Check if required folders exist."""
        print("\n--- Required Vault Folders ---")
        
        for foldername in self.REQUIRED_FOLDERS:
            folderpath = self.vault_path / foldername
            if folderpath.exists() and folderpath.is_dir():
                self._pass(f"Folder exists: {foldername}/")
            else:
                self._fail(f"Folder missing: {foldername}/")
    
    def _check_watcher_scripts(self):
        """Check if watcher scripts exist."""
        print("\n--- Watcher Scripts ---")
        
        for scriptname in self.REQUIRED_SCRIPTS:
            scriptpath = self.scripts_path / scriptname
            if scriptpath.exists():
                self._pass(f"Script exists: {scriptname}")
            else:
                self._fail(f"Script missing: {scriptname}")
    
    def _check_dashboard_content(self):
        """Check if Dashboard.md has required content."""
        print("\n--- Dashboard Content ---")
        
        dashboard_path = self.vault_path / 'Dashboard.md'
        if not dashboard_path.exists():
            return  # Already failed in required files
        
        try:
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Check for key sections
            checks = [
                ('AI Employee Dashboard', 'Title'),
                ('Quick Status', 'Status section'),
                ('Needs Action', 'Needs Action section'),
                ('Recent Activity', 'Activity section'),
            ]
            
            for search_term, description in checks:
                if search_term in content:
                    self._pass(f"Contains {description}")
                else:
                    self._warn(f"Missing {description}")
            
        except Exception as e:
            self._fail(f"Error reading Dashboard.md: {e}")
    
    def _check_company_handbook_content(self):
        """Check if Company_Handbook.md has required content."""
        print("\n--- Company Handbook Content ---")
        
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if not handbook_path.exists():
            return  # Already failed in required files
        
        try:
            content = handbook_path.read_text(encoding='utf-8')
            
            # Check for key sections
            checks = [
                ('Core Principles', 'Core Principles'),
                ('Communication Rules', 'Communication Rules'),
                ('Financial Rules', 'Financial Rules'),
                ('Approval Workflow', 'Approval Workflow'),
            ]
            
            for search_term, description in checks:
                if search_term in content:
                    self._pass(f"Contains {description}")
                else:
                    self._warn(f"Missing {description}")
            
        except Exception as e:
            self._fail(f"Error reading Company_Handbook.md: {e}")
    
    def _check_claude_available(self):
        """Check if Claude Code is available."""
        print("\n--- Claude Code Availability ---")
        
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                self._pass(f"Claude Code available: {version}")
            else:
                self._warn(f"Claude Code returned error: {result.stderr.strip()}")
                
        except FileNotFoundError:
            self._warn("Claude Code not found in PATH")
            print("  Install: npm install -g @anthropic/claude-code")
        except subprocess.TimeoutExpired:
            self._warn("Claude Code version check timed out")
        except Exception as e:
            self._warn(f"Error checking Claude Code: {e}")
    
    def _test_watcher_import(self):
        """Test if watcher scripts can be imported."""
        print("\n--- Watcher Import Test ---")
        
        import sys
        sys.path.insert(0, str(self.scripts_path))
        
        try:
            import base_watcher
            self._pass("base_watcher.py imports successfully")
        except ImportError as e:
            self._fail(f"base_watcher.py import failed: {e}")
        
        try:
            import filesystem_watcher
            self._pass("filesystem_watcher.py imports successfully")
        except ImportError as e:
            self._fail(f"filesystem_watcher.py import failed: {e}")
        
        try:
            import orchestrator
            self._pass("orchestrator.py imports successfully")
        except ImportError as e:
            self._fail(f"orchestrator.py import failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify Bronze Tier completion'
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
        help='Path to the project root (default: current directory)'
    )
    
    args = parser.parse_args()
    
    verifier = BronzeVerifier(
        vault_path=args.vault_path,
        project_path=args.project_path
    )
    
    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
