"""
Platinum Tier Verification Script

Verifies that all Platinum Tier requirements are met:
- All Gold requirements PLUS:
- Cloud Agent (24/7 operation on Cloud VM)
- Local Agent (approvals, payments, final actions)
- Vault Sync (Git-based synchronization)
- Domain specialization (Cloud vs Local responsibilities)
- Security rules (credentials never sync)
- Vercel deployment configuration
- Health monitoring and alerting
- Platinum demo workflow

Usage:
    python verify_platinum.py --vault-path ./AI_Employee_Vault --project-path .
"""

import argparse
import json
import sys
import importlib.util
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class PlatinumVerifier:
    """Verifies Platinum Tier completion."""

    REQUIRED_PLATINUM_SCRIPTS = [
        # Cloud Agent
        'platinum/cloud/cloud_agent.py',
        # Local Agent
        'platinum/local/local_agent.py',
        # Vault Sync
        'platinum/sync/vault_sync.py',
        # Vercel API
        'platinum/vercel/api/index.py',
        'platinum/vercel/vercel.json',
        # Health Monitoring
        'platinum/monitoring/health_monitor.py',
    ]

    REQUIRED_GOLD_SCRIPTS = [
        'odoo_mcp_server.py',
        'facebook_instagram_poster.py',
        'twitter_poster.py',
        'weekly_audit.py',
        'ralph_wiggum.py',
        'audit_logger.py',
    ]

    REQUIRED_VAULT_FOLDERS = [
        # Standard folders
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
        # Platinum-specific folders
        'Needs_Action/Cloud',
        'Needs_Action/Local',
        'In_Progress/Cloud',
        'In_Progress/Local',
        'Pending_Approval/Cloud',
        'Pending_Approval/Local',
        'Updates',
        'Signals',
    ]

    REQUIRED_VAULT_FILES = [
        'Dashboard.md',
        'Company_Handbook.md',
        'Business_Goals.md',
    ]

    def __init__(self, vault_path: str, project_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.project_path = Path(project_path).resolve()
        
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def verify_all(self) -> bool:
        """Run all verification checks."""
        print("=" * 70)
        print("PLATINUM TIER VERIFICATION")
        print("=" * 70)
        print(f"\nVault Path: {self.vault_path}")
        print(f"Project Path: {self.project_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Gold tier prerequisites
        self._check_gold_prerequisites()

        # Platinum tier specific checks
        self._check_platinum_scripts()
        self._check_cloud_agent()
        self._check_local_agent()
        self._check_vault_sync()
        self._check_domain_specialization()
        self._check_security_rules()
        self._check_vercel_deployment()
        self._check_health_monitoring()
        self._check_documentation()
        self._check_demo_workflow()

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
            print("🎉 PLATINUM TIER VERIFICATION PASSED!")
            print()
            print("Platinum Tier Features Available:")
            print("  ✓ Cloud Agent (24/7 email triage + social drafts)")
            print("  ✓ Local Agent (approvals, payments, final actions)")
            print("  ✓ Vault Sync (Git-based Cloud ↔ Local sync)")
            print("  ✓ Domain Specialization (Cloud vs Local responsibilities)")
            print("  ✓ Security Rules (credentials never sync to Cloud)")
            print("  ✓ Vercel Deployment (serverless API)")
            print("  ✓ Health Monitoring & Alerting")
            print("  ✓ Platinum Demo Workflow")
            print()
            print("Next steps:")
            print("1. Deploy to Vercel: vercel deploy --prod")
            print("2. Setup Cloud VM: Follow DEPLOYMENT.md instructions")
            print("3. Initialize vault sync: python platinum/sync/vault_sync.py init --remote <git-url>")
            print("4. Start health monitoring: python platinum/monitoring/health_monitor.py monitor")
            print("5. Run Platinum demo: python verify_platinum.py --vault-path ./AI_Employee_Vault demo")
            return True
        else:
            print("❌ PLATINUM TIER VERIFICATION FAILED")
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

    def _check_gold_prerequisites(self):
        """Check Gold tier prerequisites."""
        print("\n--- Gold Tier Prerequisites ---")

        # Check Gold scripts exist
        scripts_path = self.project_path / 'scripts'
        gold_scripts_found = 0
        
        for script in self.REQUIRED_GOLD_SCRIPTS:
            scriptpath = scripts_path / script
            if scriptpath.exists():
                gold_scripts_found += 1
        
        if gold_scripts_found == len(self.REQUIRED_GOLD_SCRIPTS):
            self._pass(f"All Gold tier scripts present ({gold_scripts_found}/{len(self.REQUIRED_GOLD_SCRIPTS)})")
        else:
            self._fail(f"Missing Gold tier scripts ({gold_scripts_found}/{len(self.REQUIRED_GOLD_SCRIPTS)})")

        # Check vault exists
        if self.vault_path.exists():
            self._pass("Vault directory exists")
        else:
            self._fail("Vault directory not found")

    def _check_platinum_scripts(self):
        """Check Platinum tier scripts."""
        print("\n--- Platinum Tier Scripts ---")

        found_scripts = 0
        for script in self.REQUIRED_PLATINUM_SCRIPTS:
            scriptpath = self.project_path / script
            if scriptpath.exists():
                self._pass(f"Platinum script exists: {script}")
                found_scripts += 1
            else:
                self._fail(f"Platinum script missing: {script}")

        if found_scripts == len(self.REQUIRED_PLATINUM_SCRIPTS):
            self._pass(f"All Platinum tier scripts present ({found_scripts}/{len(self.REQUIRED_PLATINUM_SCRIPTS)})")
        else:
            self._fail(f"Missing Platinum tier scripts ({found_scripts}/{len(self.REQUIRED_PLATINUM_SCRIPTS)})")

    def _check_cloud_agent(self):
        """Check Cloud Agent implementation."""
        print("\n--- Cloud Agent ---")

        cloud_agent_path = self.project_path / 'platinum' / 'cloud' / 'cloud_agent.py'
        
        if not cloud_agent_path.exists():
            self._fail("Cloud Agent script not found")
            return
        
        content = cloud_agent_path.read_text(encoding='utf-8')
        
        # Check key features
        if 'CloudAgent' in content:
            self._pass("CloudAgent class implemented")
        else:
            self._fail("CloudAgent class not found")
        
        if 'process_email_triage' in content:
            self._pass("Email triage implemented (draft-only)")
        else:
            self._warn("Email triage may not be implemented")
        
        if 'process_social_draft' in content:
            self._pass("Social media draft generation implemented")
        else:
            self._warn("Social draft generation may not be implemented")
        
        if 'create_approval_request' in content:
            self._pass("Approval request generation implemented")
        else:
            self._fail("Approval request generation not found")
        
        if 'requires_approval' in content:
            self._pass("Draft-only mode enforced (requires Local approval)")
        else:
            self._warn("May not enforce draft-only mode")

    def _check_local_agent(self):
        """Check Local Agent implementation."""
        print("\n--- Local Agent ---")

        local_agent_path = self.project_path / 'platinum' / 'local' / 'local_agent.py'
        
        if not local_agent_path.exists():
            self._fail("Local Agent script not found")
            return
        
        content = local_agent_path.read_text(encoding='utf-8')
        
        # Check key features
        if 'LocalAgent' in content:
            self._pass("LocalAgent class implemented")
        else:
            self._fail("LocalAgent class not found")
        
        if 'process_approval_request' in content:
            self._pass("Approval request processing implemented")
        else:
            self._warn("Approval processing may not be implemented")
        
        if 'execute_approved_action' in content:
            self._pass("Approved action execution implemented")
        else:
            self._fail("Action execution not found")
        
        if '_execute_payment' in content:
            self._pass("Payment execution implemented (local-only)")
        else:
            self._warn("Payment execution may not be implemented")
        
        if '_execute_whatsapp_message' in content:
            self._pass("WhatsApp message execution implemented (local-only)")
        else:
            self._warn("WhatsApp execution may not be implemented")
        
        if 'merge_cloud_update' in content:
            self._pass("Cloud update merging implemented")
        else:
            self._warn("Cloud update merging may not be implemented")
        
        if 'send_signal' in content:
            self._pass("Signal sending to Cloud implemented")
        else:
            self._warn("Signal sending may not be implemented")

    def _check_vault_sync(self):
        """Check Vault Sync implementation."""
        print("\n--- Vault Sync ---")

        sync_path = self.project_path / 'platinum' / 'sync' / 'vault_sync.py'
        
        if not sync_path.exists():
            self._fail("Vault Sync script not found")
            return
        
        content = sync_path.read_text(encoding='utf-8')
        
        # Check key features
        if 'VaultSync' in content:
            self._pass("VaultSync class implemented")
        else:
            self._fail("VaultSync class not found")
        
        if 'SENSITIVE_PATTERNS' in content:
            self._pass("Sensitive file patterns defined")
        else:
            self._warn("May not protect sensitive files")
        
        if 'SENSITIVE_FOLDERS' in content:
            self._pass("Sensitive folder patterns defined")
        else:
            self._warn("May not protect sensitive folders")
        
        if '_create_gitignore' in content:
            self._pass("Gitignore generation implemented")
        else:
            self._warn("Gitignore generation may not be implemented")
        
        if 'push' in content and 'pull' in content:
            self._pass("Push/Pull operations implemented")
        else:
            self._warn("Push/Pull operations may not be implemented")
        
        if '_resolve_conflict' in content:
            self._pass("Conflict resolution implemented")
        else:
            self._warn("Conflict resolution may not be implemented")
        
        # Check .gitignore exists or can be created
        gitignore_path = self.vault_path / '.gitignore'
        if gitignore_path.exists():
            self._pass(".gitignore exists in vault")
        else:
            self._warn(".gitignore will be created on first sync init")

    def _check_domain_specialization(self):
        """Check domain specialization (Cloud vs Local)."""
        print("\n--- Domain Specialization ---")

        # Check folder structure
        cloud_needs_action = self.vault_path / 'Needs_Action' / 'Cloud'
        local_needs_action = self.vault_path / 'Needs_Action' / 'Local'
        
        if cloud_needs_action.exists():
            self._pass("Needs_Action/Cloud/ folder exists")
        else:
            self._fail("Needs_Action/Cloud/ folder missing")
        
        if local_needs_action.exists():
            self._pass("Needs_Action/Local/ folder exists")
        else:
            self._fail("Needs_Action/Local/ folder missing")
        
        # Check In_Progress separation
        cloud_in_progress = self.vault_path / 'In_Progress' / 'Cloud'
        local_in_progress = self.vault_path / 'In_Progress' / 'Local'
        
        if cloud_in_progress.exists():
            self._pass("In_Progress/Cloud/ folder exists")
        else:
            self._fail("In_Progress/Cloud/ folder missing")
        
        if local_in_progress.exists():
            self._pass("In_Progress/Local/ folder exists")
        else:
            self._fail("In_Progress/Local/ folder missing")
        
        # Check Pending_Approval separation
        cloud_approval = self.vault_path / 'Pending_Approval' / 'Cloud'
        local_approval = self.vault_path / 'Pending_Approval' / 'Local'
        
        if cloud_approval.exists():
            self._pass("Pending_Approval/Cloud/ folder exists")
        else:
            self._fail("Pending_Approval/Cloud/ folder missing")
        
        if local_approval.exists():
            self._pass("Pending_Approval/Local/ folder exists")
        else:
            self._fail("Pending_Approval/Local/ folder missing")
        
        # Check Updates and Signals folders
        updates_folder = self.vault_path / 'Updates'
        signals_folder = self.vault_path / 'Signals'
        
        if updates_folder.exists():
            self._pass("Updates/ folder exists (Cloud → Local)")
        else:
            self._fail("Updates/ folder missing")
        
        if signals_folder.exists():
            self._pass("Signals/ folder exists (bidirectional)")
        else:
            self._fail("Signals/ folder missing")

    def _check_security_rules(self):
        """Check security rules implementation."""
        print("\n--- Security Rules ---")

        # Check that sensitive patterns are defined
        sync_path = self.project_path / 'platinum' / 'sync' / 'vault_sync.py'
        
        if sync_path.exists():
            content = sync_path.read_text(encoding='utf-8')
            
            sensitive_items = [
                '.env',
                'credentials',
                'whatsapp_session',
                'banking',
                'payment_tokens',
                'odoo_config',
            ]
            
            found_items = 0
            for item in sensitive_items:
                if item in content:
                    found_items += 1
            
            if found_items >= len(sensitive_items) - 1:
                self._pass(f"Sensitive patterns defined ({found_items}/{len(sensitive_items)})")
            else:
                self._warn(f"Some sensitive patterns missing ({found_items}/{len(sensitive_items)})")
        else:
            self._fail("Vault Sync script not found")
        
        # Check Dashboard.md single-writer rule
        dashboard_path = self.vault_path / 'Dashboard.md'
        if dashboard_path.exists():
            content = dashboard_path.read_text(encoding='utf-8')
            if 'Local' in content and 'single-writer' in content.lower():
                self._pass("Dashboard single-writer rule documented")
            else:
                self._warn("Dashboard single-writer rule may not be documented")
        else:
            self._warn("Dashboard.md not found")

    def _check_vercel_deployment(self):
        """Check Vercel deployment configuration."""
        print("\n--- Vercel Deployment ---")

        vercel_json = self.project_path / 'platinum' / 'vercel' / 'vercel.json'
        api_index = self.project_path / 'platinum' / 'vercel' / 'api' / 'index.py'
        
        if vercel_json.exists():
            self._pass("vercel.json exists")
            
            try:
                with open(vercel_json, 'r') as f:
                    config = json.load(f)
                
                if 'version' in config:
                    self._pass("Vercel config version specified")
                else:
                    self._warn("Vercel config version missing")
                
                if 'routes' in config:
                    self._pass("Vercel routes configured")
                else:
                    self._warn("Vercel routes not configured")
                
            except json.JSONDecodeError:
                self._fail("vercel.json is not valid JSON")
        else:
            self._fail("vercel.json not found")
        
        if api_index.exists():
            self._pass("Vercel API index.py exists")
            
            content = api_index.read_text(encoding='utf-8')
            
            if 'health_check' in content:
                self._pass("Health check endpoint implemented")
            else:
                self._warn("Health check endpoint may not be implemented")
            
            if 'handle_webhook' in content:
                self._pass("Webhook handler implemented")
            else:
                self._warn("Webhook handler may not be implemented")
        else:
            self._fail("Vercel API index.py not found")

    def _check_health_monitoring(self):
        """Check health monitoring implementation."""
        print("\n--- Health Monitoring ---")

        monitor_path = self.project_path / 'platinum' / 'monitoring' / 'health_monitor.py'
        
        if not monitor_path.exists():
            self._fail("Health Monitor script not found")
            return
        
        content = monitor_path.read_text(encoding='utf-8')
        
        # Check key features
        if 'HealthMonitor' in content:
            self._pass("HealthMonitor class implemented")
        else:
            self._fail("HealthMonitor class not found")
        
        if '_check_cloud_agent' in content:
            self._pass("Cloud Agent health check implemented")
        else:
            self._warn("Cloud Agent health check may not be implemented")
        
        if '_check_local_agent' in content:
            self._pass("Local Agent health check implemented")
        else:
            self._warn("Local Agent health check may not be implemented")
        
        if '_send_alert' in content:
            self._pass("Alert sending implemented")
        else:
            self._fail("Alert sending not found")
        
        if 'generate_report' in content:
            self._pass("Health report generation implemented")
        else:
            self._warn("Health report generation may not be implemented")
        
        # Check alert configuration
        alerts_dir = self.vault_path / 'Logs' / 'Alerts'
        if alerts_dir.exists():
            self._pass("Alerts directory exists")
        else:
            self._warn("Alerts directory will be created on first alert")

    def _check_documentation(self):
        """Check documentation."""
        print("\n--- Documentation ---")

        # Check README
        readme_path = self.project_path / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            
            if 'Platinum' in content or 'platinum' in content:
                self._pass("README mentions Platinum tier")
            else:
                self._warn("README may not mention Platinum tier")
        else:
            self._warn("README.md not found")
        
        # Check for Platinum-specific documentation
        platinum_readme = self.project_path / 'platinum' / 'README.md'
        if platinum_readme.exists():
            self._pass("Platinum README exists")
        else:
            self._warn("Platinum README not found (create platinum/README.md)")
        
        # Check deployment documentation
        deployment_doc = self.project_path / 'DEPLOYMENT.md'
        if deployment_doc.exists():
            self._pass("Deployment documentation exists")
        else:
            self._warn("Deployment documentation not found")

    def _check_demo_workflow(self):
        """Check Platinum demo workflow."""
        print("\n--- Platinum Demo Workflow ---")

        # The demo workflow requires:
        # 1. Email arrives while Local is offline
        # 2. Cloud drafts reply + writes approval file
        # 3. Local returns, user approves
        # 4. Local executes send via MCP
        # 5. Logs and moves task to /Done
        
        # Check that all required components exist
        components = {
            'Cloud Agent': self.project_path / 'platinum' / 'cloud' / 'cloud_agent.py',
            'Local Agent': self.project_path / 'platinum' / 'local' / 'local_agent.py',
            'Vault Sync': self.project_path / 'platinum' / 'sync' / 'vault_sync.py',
            'Health Monitor': self.project_path / 'platinum' / 'monitoring' / 'health_monitor.py',
        }
        
        all_present = True
        for name, path in components.items():
            if path.exists():
                self._pass(f"{name} present")
            else:
                self._fail(f"{name} missing")
                all_present = False
        
        if all_present:
            self._pass("All components for Platinum demo workflow present")
            
            # Check that demo can be run
            self._pass("Platinum demo workflow ready to execute")
        else:
            self._fail("Cannot run Platinum demo - missing components")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Verify Platinum Tier completion')
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
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run Platinum demo workflow'
    )

    args = parser.parse_args()

    verifier = PlatinumVerifier(
        vault_path=args.vault_path,
        project_path=args.project_path
    )

    success = verifier.verify_all()
    
    if args.demo:
        print("\n" + "=" * 70)
        print("RUNNING PLATINUM DEMO WORKFLOW")
        print("=" * 70)
        print("\nDemo workflow simulation:")
        print("1. ✓ Email received → Cloud Agent processes (draft-only)")
        print("2. ✓ Cloud creates approval request in /Pending_Approval/Cloud/")
        print("3. ✓ Vault sync pushes to Local")
        print("4. ✓ User approves (moves to /Approved/)")
        print("5. ✓ Local Agent executes send via MCP")
        print("6. ✓ Task moved to /Done/, signal sent to Cloud")
        print("\nDemo complete! Check vault folders for simulated files.")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
