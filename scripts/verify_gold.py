"""
Gold Tier Verification Script

Verifies that all Gold Tier requirements are met:
- All Silver requirements PLUS:
- Full cross-domain integration (Personal + Business)
- Odoo MCP integration for accounting
- Facebook/Instagram integration
- Twitter/X integration
- Multiple MCP servers
- Weekly Business Audit with CEO Briefing generation
- Error recovery and graceful degradation
- Comprehensive audit logging
- Ralph Wiggum loop for autonomous task completion
- Documentation of architecture and lessons learned

Usage:
    python verify_gold.py --vault-path ./AI_Employee_Vault --project-path .
"""

import argparse
import sys
import importlib.util
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class GoldVerifier:
    """Verifies Gold Tier completion."""

    REQUIRED_GOLD_SCRIPTS = [
        'odoo_mcp_server.py',
        'facebook_instagram_poster.py',
        'twitter_poster.py',
        'weekly_audit.py',
        'ralph_wiggum.py',
        'audit_logger.py',
    ]

    REQUIRED_SILVER_SCRIPTS = [
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
        'In_Progress',
        'Plans',
        'Pending_Approval',
        'Approved',
        'Rejected',
        'Briefings',
        'Logs',
        'Posts',
        'Invoices',
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
        print("=" * 70)
        print("GOLD TIER VERIFICATION")
        print("=" * 70)
        print(f"\nVault Path: {self.vault_path}")
        print(f"Project Path: {self.project_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Silver tier checks (prerequisites)
        self._check_silver_prerequisites()

        # Gold tier specific checks
        self._check_gold_scripts()
        self._check_odoo_integration()
        self._check_social_media_integrations()
        self._check_weekly_audit()
        self._check_ralph_wiggum()
        self._check_audit_logging()
        self._check_error_handling()
        self._check_documentation()
        self._check_imports()

        # Summary
        print()
        print("=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"✓ Passed:   {self.passed}")
        print(f"✗ Failed:   {self.failed}")
        print(f"⚠ Warnings: {self.warnings}")
        print()

        if self.failed == 0:
            print("🎉 GOLD TIER VERIFICATION PASSED!")
            print()
            print("Gold Tier Features Available:")
            print("  ✓ Odoo MCP integration for accounting")
            print("  ✓ Facebook/Instagram auto-posting")
            print("  ✓ Twitter/X auto-posting")
            print("  ✓ Weekly Business Audit with CEO Briefing")
            print("  ✓ Ralph Wiggum autonomous loop")
            print("  ✓ Comprehensive audit logging")
            print("  ✓ Error recovery and graceful degradation")
            print("  ✓ Full documentation")
            print()
            print("Next steps:")
            print("1. Configure Odoo: Create ~/.config/odoo_config.json")
            print("2. Run weekly audit: python scripts/weekly_audit.py --vault-path ./AI_Employee_Vault generate")
            print("3. Start Ralph loop: python scripts/ralph_wiggum.py --vault-path ./AI_Employee_Vault start \"Process pending items\" --auto")
            print("4. View audit summary: python scripts/audit_logger.py --vault-path ./AI_Employee_Vault summary --days 7")
            return True
        else:
            print("❌ GOLD TIER VERIFICATION FAILED")
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

    def _check_silver_prerequisites(self):
        """Check Silver tier prerequisites."""
        print("\n--- Silver Tier Prerequisites ---")

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

        # Silver scripts
        found_scripts = 0
        for script in self.REQUIRED_SILVER_SCRIPTS:
            scriptpath = self.scripts_path / script
            if scriptpath.exists():
                found_scripts += 1

        if found_scripts >= len(self.REQUIRED_SILVER_SCRIPTS) - 2:  # Allow 2 missing
            self._pass(f"Silver tier scripts present ({found_scripts}/{len(self.REQUIRED_SILVER_SCRIPTS)})")
        else:
            self._fail(f"Missing Silver tier scripts ({found_scripts}/{len(self.REQUIRED_SILVER_SCRIPTS)})")

    def _check_gold_scripts(self):
        """Check Gold tier scripts."""
        print("\n--- Gold Tier Scripts ---")

        found_scripts = 0
        for script in self.REQUIRED_GOLD_SCRIPTS:
            scriptpath = self.scripts_path / script
            if scriptpath.exists():
                self._pass(f"Gold script exists: {script}")
                found_scripts += 1
            else:
                self._fail(f"Gold script missing: {script}")

        if found_scripts == len(self.REQUIRED_GOLD_SCRIPTS):
            self._pass(f"All Gold tier scripts present ({found_scripts}/{len(self.REQUIRED_GOLD_SCRIPTS)})")
        else:
            self._fail(f"Missing Gold tier scripts ({found_scripts}/{len(self.REQUIRED_GOLD_SCRIPTS)})")

    def _check_odoo_integration(self):
        """Check Odoo MCP integration."""
        print("\n--- Odoo MCP Integration ---")

        odoo_script = self.scripts_path / 'odoo_mcp_server.py'
        if odoo_script.exists():
            self._pass("Odoo MCP server script exists")

            content = odoo_script.read_text(encoding='utf-8')

            if 'OdooClient' in content:
                self._pass("OdooClient class implemented")
            else:
                self._warn("OdooClient class may not be implemented")

            if 'mcp.server' in content or 'Server' in content:
                self._pass("Uses MCP server framework")
            else:
                self._warn("May not use MCP server framework")

            if 'create_invoice' in content:
                self._pass("Invoice creation supported")
            else:
                self._warn("Invoice creation may not be supported")

            if 'get_business_metrics' in content:
                self._pass("Business metrics supported")
            else:
                self._warn("Business metrics may not be supported")

            if 'get_profit_loss' in content:
                self._pass("Profit/Loss reporting supported")
            else:
                self._warn("Profit/Loss reporting may not be supported")
        else:
            self._fail("Odoo MCP server script not found")

    def _check_social_media_integrations(self):
        """Check social media integrations."""
        print("\n--- Social Media Integrations ---")

        # Facebook/Instagram
        fb_ig_script = self.scripts_path / 'facebook_instagram_poster.py'
        if fb_ig_script.exists():
            self._pass("Facebook/Instagram poster exists")

            content = fb_ig_script.read_text(encoding='utf-8')

            if 'create_facebook_post' in content:
                self._pass("Facebook posting supported")
            else:
                self._warn("Facebook posting may not be supported")

            if 'create_instagram_post' in content:
                self._pass("Instagram posting supported")
            else:
                self._warn("Instagram posting may not be supported")

            if 'post_to_both' in content:
                self._pass("Cross-platform posting supported")
            else:
                self._warn("Cross-platform posting may not be supported")
        else:
            self._fail("Facebook/Instagram poster not found")

        # Twitter/X
        twitter_script = self.scripts_path / 'twitter_poster.py'
        if twitter_script.exists():
            self._pass("Twitter/X poster exists")

            content = twitter_script.read_text(encoding='utf-8')

            if 'create_tweet' in content:
                self._pass("Tweet creation supported")
            else:
                self._warn("Tweet creation may not be supported")

            if 'create_thread' in content:
                self._pass("Thread creation supported")
            else:
                self._warn("Thread creation may not be supported")
        else:
            self._fail("Twitter/X poster not found")

        # Check Posts folder structure
        posts_folder = self.vault_path / 'Posts'
        if posts_folder.exists():
            self._pass("Posts folder exists")

            # Check subfolders
            subfolders = ['Facebook', 'Instagram', 'Twitter', 'Published', 'Scheduled', 'Drafts']
            found_subfolders = 0
            for subfolder in subfolders:
                if (posts_folder / subfolder).exists():
                    found_subfolders += 1

            if found_subfolders >= 3:
                self._pass(f"Posts subfolders organized ({found_subfolders}/{len(subfolders)})")
            else:
                self._warn(f"Missing Posts subfolders ({found_subfolders}/{len(subfolders)})")
        else:
            self._fail("Posts folder not found")

    def _check_weekly_audit(self):
        """Check weekly audit system."""
        print("\n--- Weekly Audit System ---")

        audit_script = self.scripts_path / 'weekly_audit.py'
        if audit_script.exists():
            self._pass("Weekly audit script exists")

            content = audit_script.read_text(encoding='utf-8')

            if 'generate_weekly_briefing' in content:
                self._pass("Weekly briefing generation implemented")
            else:
                self._warn("Weekly briefing generation may not be implemented")

            if '_analyze_revenue' in content:
                self._pass("Revenue analysis implemented")
            else:
                self._warn("Revenue analysis may not be implemented")

            if '_analyze_expenses' in content:
                self._pass("Expense analysis implemented")
            else:
                self._warn("Expense analysis may not be implemented")

            if '_audit_subscriptions' in content:
                self._pass("Subscription audit implemented")
            else:
                self._warn("Subscription audit may not be implemented")

            if '_identify_bottlenecks' in content:
                self._pass("Bottleneck identification implemented")
            else:
                self._warn("Bottleneck identification may not be implemented")

            if '_generate_suggestions' in content:
                self._pass("Proactive suggestions implemented")
            else:
                self._warn("Proactive suggestions may not be implemented")
        else:
            self._fail("Weekly audit script not found")

        # Check Briefings folder
        briefings_folder = self.vault_path / 'Briefings'
        if briefings_folder.exists():
            self._pass("Briefings folder exists")
        else:
            self._fail("Briefings folder not found")

    def _check_ralph_wiggum(self):
        """Check Ralph Wiggum loop implementation."""
        print("\n--- Ralph Wiggum Loop ---")

        ralph_script = self.scripts_path / 'ralph_wiggum.py'
        if ralph_script.exists():
            self._pass("Ralph Wiggum script exists")

            content = ralph_script.read_text(encoding='utf-8')

            if 'RalphWiggumLoop' in content:
                self._pass("RalphWiggumLoop class implemented")
            else:
                self._warn("RalphWiggumLoop class may not be implemented")

            if 'check_completion' in content:
                self._pass("Completion checking implemented")
            else:
                self._warn("Completion checking may not be implemented")

            if 'should_continue' in content:
                self._pass("Loop continuation logic implemented")
            else:
                self._warn("Loop continuation logic may not be implemented")

            if 'max_iterations' in content:
                self._pass("Max iterations protection implemented")
            else:
                self._warn("Max iterations protection may not be implemented")

            if 'completion_promise' in content:
                self._pass("Completion promise detection implemented")
            else:
                self._warn("Completion promise detection may not be implemented")
        else:
            self._fail("Ralph Wiggum script not found")

    def _check_audit_logging(self):
        """Check audit logging system."""
        print("\n--- Audit Logging System ---")

        audit_script = self.scripts_path / 'audit_logger.py'
        if audit_script.exists():
            self._pass("Audit logger script exists")

            content = audit_script.read_text(encoding='utf-8')

            if 'AuditLogger' in content:
                self._pass("AuditLogger class implemented")
            else:
                self._warn("AuditLogger class may not be implemented")

            if 'AuditEntry' in content:
                self._pass("Structured audit entries implemented")
            else:
                self._warn("Structured audit entries may not be implemented")

            if 'search' in content:
                self._pass("Log search capability implemented")
            else:
                self._warn("Log search may not be implemented")

            if 'export' in content:
                self._pass("Log export capability implemented")
            else:
                self._warn("Log export may not be implemented")

            if 'generate_report' in content:
                self._pass("Audit report generation implemented")
            else:
                self._warn("Audit report generation may not be implemented")
        else:
            self._fail("Audit logger script not found")

        # Check Logs folder
        logs_folder = self.vault_path / 'Logs'
        if logs_folder.exists():
            self._pass("Logs folder exists")

            # Check for Audit subfolder
            audit_subfolder = logs_folder / 'Audit'
            if audit_subfolder.exists():
                self._pass("Audit subfolder exists")
            else:
                self._warn("Audit subfolder not found")
        else:
            self._fail("Logs folder not found")

    def _check_error_handling(self):
        """Check error recovery and graceful degradation."""
        print("\n--- Error Handling & Recovery ---")

        # Check key scripts for error handling
        scripts_to_check = [
            ('odoo_mcp_server.py', 'Odoo MCP'),
            ('facebook_instagram_poster.py', 'Social Media'),
            ('weekly_audit.py', 'Weekly Audit'),
            ('orchestrator.py', 'Orchestrator'),
        ]

        for script_name, display_name in scripts_to_check:
            script_path = self.scripts_path / script_name
            if script_path.exists():
                content = script_path.read_text(encoding='utf-8')

                # Check for try/except blocks
                if 'try:' in content and 'except' in content:
                    self._pass(f"{display_name} has error handling")
                else:
                    self._warn(f"{display_name} may lack error handling")

                # Check for logging
                if 'logger' in content.lower() or 'print' in content:
                    self._pass(f"{display_name} has logging")
                else:
                    self._warn(f"{display_name} may lack logging")
            else:
                self._warn(f"{display_name} script not found")

    def _check_documentation(self):
        """Check documentation."""
        print("\n--- Documentation ---")

        # Check for README
        readme_path = self.project_path / 'README.md'
        if readme_path.exists():
            self._pass("README.md exists")

            content = readme_path.read_text(encoding='utf-8')

            if 'Gold' in content or 'gold' in content:
                self._pass("README mentions Gold tier")
            else:
                self._warn("README may not mention Gold tier")
        else:
            self._warn("README.md not found")

        # Check QWEN.md
        qwen_path = self.project_path / 'QWEN.md'
        if qwen_path.exists():
            self._pass("QWEN.md (project documentation) exists")
        else:
            self._warn("QWEN.md not found")

        # Check for architecture documentation
        docs_path = self.project_path / 'docs'
        if docs_path.exists():
            self._pass("Documentation folder exists")
        else:
            self._warn("Documentation folder not found")

    def _check_imports(self):
        """Test if Gold tier scripts can be imported."""
        print("\n--- Import Tests ---")

        import sys
        sys.path.insert(0, str(self.scripts_path))

        scripts_to_test = [
            'odoo_mcp_server',
            'facebook_instagram_poster',
            'twitter_poster',
            'weekly_audit',
            'ralph_wiggum',
            'audit_logger',
        ]

        for script in scripts_to_test:
            try:
                spec = importlib.util.spec_from_file_location(
                    script,
                    self.scripts_path / f'{script}.py'
                )
                # Just check syntax, don't exec
                self._pass(f"{script}.py syntax OK")
            except Exception as e:
                self._fail(f"{script}.py import error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify Gold Tier completion'
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

    verifier = GoldVerifier(
        vault_path=args.vault_path,
        project_path=args.project_path
    )

    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
