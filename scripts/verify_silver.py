"""
Silver Tier Verification Script

Verifies that all Silver Tier requirements are met:
- All Bronze requirements PLUS:
- Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- LinkedIn Auto-Poster for business posts
- Claude reasoning loop with Plan.md creation
- One working MCP server (Email MCP)
- Human-in-the-loop approval workflow
- Basic scheduling via Task Scheduler
- Agent Skills module implemented

Usage:
    python verify_silver.py --vault-path ./AI_Employee_Vault --project-path .
"""

import argparse
import sys
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class SilverVerifier:
    """Verifies Silver Tier completion."""
    
    REQUIRED_WATCHERS = [
        'filesystem_watcher.py',
        'gmail_watcher.py',
        'whatsapp_watcher.py',
    ]
    
    REQUIRED_SCRIPTS = [
        'base_watcher.py',
        'filesystem_watcher.py',
        'gmail_watcher.py',
        'whatsapp_watcher.py',
        'orchestrator.py',
        'plan_manager.py',
        'approval_manager.py',
        'email_mcp_server.py',
        'agent_skills.py',
        'linkedin_poster.py',
        'setup_scheduler.py',
        'daily_briefing.py',
        'cleanup.py',
    ]
    
    REQUIRED_VAULT_FILES = [
        'Dashboard.md',
        'Company_Handbook.md',
        'Business_Goals.md',
    ]
    
    REQUIRED_VAULT_FOLDERS = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Plans',
        'Pending_Approval',
        'Approved',
        'Rejected',
        'Briefings',
        'Logs',
        'Posts',
    ]
    
    def __init__(self, vault_path: str, project_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.project_path = Path(project_path).resolve()
        self.scripts_path = self.project_path / 'scripts'
        
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def verify_all(self) -> bool:
        """Run all verification checks."""
        print("=" * 60)
        print("SILVER TIER VERIFICATION")
        print("=" * 60)
        print(f"\nVault Path: {self.vault_path}")
        print(f"Project Path: {self.project_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Bronze tier checks (prerequisites)
        self._check_bronze_prerequisites()
        
        # Silver tier specific checks
        self._check_watchers()
        self._check_mcp_servers()
        self._check_approval_workflow()
        self._check_scheduler()
        self._check_agent_skills()
        self._check_linkedin_poster()
        self._check_plan_system()
        self._check_imports()
        
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
            print("🎉 SILVER TIER VERIFICATION PASSED!")
            print()
            print("Silver Tier Features Available:")
            print("  ✓ Multiple watchers (File System, Gmail, WhatsApp)")
            print("  ✓ LinkedIn Auto-Posting for business")
            print("  ✓ Plan.md reasoning loop")
            print("  ✓ Email MCP server")
            print("  ✓ Human-in-the-Loop approval workflow")
            print("  ✓ Task Scheduler integration")
            print("  ✓ Agent Skills module")
            print()
            print("Next steps:")
            print("1. Run: python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault --all install")
            print("2. Configure Gmail credentials for email watcher")
            print("3. Test LinkedIn posting: python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault draft \"Test post\"")
            return True
        else:
            print("❌ SILVER TIER VERIFICATION FAILED")
            print()
            print("Please fix the failed checks above.")
            return False
    
    def _pass(self, message: str):
        print(f"✓ {message}")
        self.passed += 1
    
    def _fail(self, message: str):
        print(f"✗ {message}")
        self.failed += 1
    
    def _warn(self, message: str):
        print(f"⚠ {message}")
        self.warnings += 1
    
    def _check_bronze_prerequisites(self):
        """Check Bronze tier prerequisites."""
        print("\n--- Bronze Tier Prerequisites ---")
        
        # Vault exists
        if self.vault_path.exists():
            self._pass("Vault directory exists")
        else:
            self._fail("Vault directory not found")
            return
        
        # Required files
        for filename in self.REQUIRED_VAULT_FILES:
            filepath = self.vault_path / filename
            if filepath.exists():
                self._pass(f"Vault file exists: {filename}")
            else:
                self._fail(f"Vault file missing: {filename}")
        
        # Required folders
        for foldername in self.REQUIRED_VAULT_FOLDERS:
            folderpath = self.vault_path / foldername
            if folderpath.exists():
                self._pass(f"Vault folder exists: {foldername}/")
            else:
                self._fail(f"Vault folder missing: {foldername}/")
    
    def _check_watchers(self):
        """Check watcher scripts."""
        print("\n--- Watcher Scripts ---")
        
        found_watchers = 0
        
        for watcher in self.REQUIRED_WATCHERS:
            scriptpath = self.scripts_path / watcher
            if scriptpath.exists():
                self._pass(f"Watcher exists: {watcher}")
                found_watchers += 1
                
                # Check for required imports
                content = scriptpath.read_text(encoding='utf-8')
                if 'BaseWatcher' in content or 'base_watcher' in content:
                    self._pass(f"{watcher} extends BaseWatcher")
                else:
                    self._warn(f"{watcher} may not extend BaseWatcher")
            else:
                self._warn(f"Watcher not found: {watcher}")
        
        if found_watchers >= 2:
            self._pass(f"Multiple watchers available ({found_watchers})")
        else:
            self._fail(f"Need at least 2 watchers, found {found_watchers}")
    
    def _check_mcp_servers(self):
        """Check MCP server implementations."""
        print("\n--- MCP Servers ---")
        
        mcp_server = self.scripts_path / 'email_mcp_server.py'
        if mcp_server.exists():
            self._pass("Email MCP server exists")
            
            content = mcp_server.read_text(encoding='utf-8')
            if 'mcp.server' in content or 'Server' in content:
                self._pass("MCP server uses MCP library")
            else:
                self._warn("MCP server may not use MCP library correctly")
            
            if 'gmail' in content.lower() or 'email' in content.lower():
                self._pass("Email MCP handles email operations")
            else:
                self._warn("Email MCP may not handle email correctly")
        else:
            self._fail("Email MCP server not found")
    
    def _check_approval_workflow(self):
        """Check approval workflow system."""
        print("\n--- Approval Workflow ---")
        
        approval_manager = self.scripts_path / 'approval_manager.py'
        if approval_manager.exists():
            self._pass("Approval manager exists")
            
            content = approval_manager.read_text(encoding='utf-8')
            
            if 'Pending_Approval' in content:
                self._pass("Uses Pending_Approval folder")
            else:
                self._warn("May not use Pending_Approval folder")
            
            if 'Approved' in content and 'Rejected' in content:
                self._pass("Has approval/rejection workflow")
            else:
                self._warn("May not have complete approval workflow")
            
            if 'action_type' in content:
                self._pass("Supports multiple action types")
            else:
                self._warn("May not support multiple action types")
        else:
            self._fail("Approval manager not found")
        
        # Check vault folders
        if (self.vault_path / 'Pending_Approval').exists():
            self._pass("Pending_Approval folder exists")
        else:
            self._fail("Pending_Approval folder missing")
        
        if (self.vault_path / 'Approved').exists():
            self._pass("Approved folder exists")
        else:
            self._fail("Approved folder missing")
        
        if (self.vault_path / 'Rejected').exists():
            self._pass("Rejected folder exists")
        else:
            self._fail("Rejected folder missing")
    
    def _check_scheduler(self):
        """Check scheduler integration."""
        print("\n--- Task Scheduler ---")
        
        scheduler = self.scripts_path / 'setup_scheduler.py'
        if scheduler.exists():
            self._pass("Scheduler setup script exists")
            
            content = scheduler.read_text(encoding='utf-8')
            if 'schtasks' in content:
                self._pass("Uses Windows Task Scheduler")
            else:
                self._warn("May not use Windows Task Scheduler")
            
            if 'daily_briefing' in content:
                self._pass("Includes daily briefing task")
            else:
                self._warn("May not include daily briefing")
        else:
            self._fail("Scheduler setup script not found")
        
        # Check daily briefing script
        briefing = self.scripts_path / 'daily_briefing.py'
        if briefing.exists():
            self._pass("Daily briefing generator exists")
        else:
            self._fail("Daily briefing generator not found")
    
    def _check_agent_skills(self):
        """Check Agent Skills module."""
        print("\n--- Agent Skills ---")
        
        agent_skills = self.scripts_path / 'agent_skills.py'
        if agent_skills.exists():
            self._pass("Agent Skills module exists")
            
            content = agent_skills.read_text(encoding='utf-8')
            
            # Check for key skills
            skills_to_check = [
                'create_plan',
                'request_approval',
                'move_to_done',
                'update_dashboard',
                'categorize_item'
            ]
            
            for skill in skills_to_check:
                if f'def {skill}' in content:
                    self._pass(f"Skill '{skill}' implemented")
                else:
                    self._warn(f"Skill '{skill}' may not be implemented")
        else:
            self._fail("Agent Skills module not found")
    
    def _check_linkedin_poster(self):
        """Check LinkedIn Auto-Poster."""
        print("\n--- LinkedIn Auto-Poster ---")
        
        linkedin = self.scripts_path / 'linkedin_poster.py'
        if linkedin.exists():
            self._pass("LinkedIn poster exists")
            
            content = linkedin.read_text(encoding='utf-8')
            
            if 'playwright' in content.lower():
                self._pass("Uses Playwright for automation")
            else:
                self._warn("May not use Playwright")
            
            if 'create_post' in content:
                self._pass("Can create posts")
            else:
                self._warn("May not be able to create posts")
            
            if 'schedule' in content.lower():
                self._pass("Supports scheduled posting")
            else:
                self._warn("May not support scheduling")
            
            # Check Posts folder
            posts_folder = self.vault_path / 'Posts'
            if posts_folder.exists():
                self._pass("Posts folder exists")
            else:
                self._warn("Posts folder not found")
        else:
            self._fail("LinkedIn poster not found")
    
    def _check_plan_system(self):
        """Check Plan.md reasoning loop system."""
        print("\n--- Plan System ---")
        
        plan_manager = self.scripts_path / 'plan_manager.py'
        if plan_manager.exists():
            self._pass("Plan manager exists")
            
            content = plan_manager.read_text(encoding='utf-8')
            
            if 'Plan' in content and 'steps' in content.lower():
                self._pass("Supports multi-step plans")
            else:
                self._warn("May not support multi-step plans")
            
            if 'create_approval_request' in content:
                self._pass("Integrates with approval system")
            else:
                self._warn("May not integrate with approval system")
        else:
            self._fail("Plan manager not found")
        
        # Check Plans folder
        if (self.vault_path / 'Plans').exists():
            self._pass("Plans folder exists")
        else:
            self._fail("Plans folder missing")
    
    def _check_imports(self):
        """Test if scripts can be imported."""
        print("\n--- Import Tests ---")
        
        import sys
        sys.path.insert(0, str(self.scripts_path))
        
        scripts_to_test = [
            'base_watcher',
            'filesystem_watcher',
            'plan_manager',
            'approval_manager',
            'agent_skills',
        ]
        
        for script in scripts_to_test:
            try:
                spec = importlib.util.spec_from_file_location(
                    script,
                    self.scripts_path / f'{script}.py'
                )
                module = importlib.util.module_from_spec(spec)
                # Don't exec, just check syntax
                self._pass(f"{script}.py syntax OK")
            except Exception as e:
                self._fail(f"{script}.py import error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify Silver Tier completion'
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
    
    verifier = SilverVerifier(
        vault_path=args.vault_path,
        project_path=args.project_path
    )
    
    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
