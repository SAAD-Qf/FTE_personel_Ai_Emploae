"""
Health Monitoring & Alerting - Platinum Tier

Monitors the health of Cloud and Local agents, vault sync, and system components.
Sends alerts when issues are detected.

Features:
- Agent health checks (Cloud, Local)
- Vault sync status monitoring
- Resource usage tracking
- Alert notifications (email, webhook)
- Health dashboard generation
- Auto-recovery suggestions

Usage:
    # Run health check
    python health_monitor.py --vault-path ./AI_Employee_Vault check
    
    # Start continuous monitoring
    python health_monitor.py --vault-path ./AI_Employee_Vault monitor --interval 60
    
    # Generate health report
    python health_monitor.py --vault-path ./AI_Employee_Vault report
    
    # Send test alert
    python health_monitor.py --vault-path ./AI_Employee_Vault test-alert
"""

import argparse
import json
import logging
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class HealthStatus:
    """Health status of a component."""
    component: str
    status: str  # healthy, degraded, unhealthy, unknown
    message: str
    timestamp: str
    details: Dict[str, Any] = None
    recovery_suggestion: str = None


@dataclass
class Alert:
    """Alert notification."""
    alert_id: str
    severity: str  # critical, warning, info
    component: str
    message: str
    timestamp: str
    details: Dict = None


class HealthMonitor:
    """
    Health monitoring and alerting system.
    """

    def __init__(self, vault_path: str, config_path: Optional[str] = None):
        self.vault_path = Path(vault_path).resolve()
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Alert history
        self.alerts: List[Alert] = []
        self.alert_cooldown: Dict[str, datetime] = {}  # Prevent alert spam
        
        self.logger.info("Health Monitor initialized")

    def _load_config(self) -> Dict:
        """Load monitoring configuration."""
        default_config = {
            'alerts': {
                'enabled': True,
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'sender': None,
                    'recipients': [],
                    'password_env': 'SMTP_PASSWORD',
                },
                'webhook': {
                    'enabled': False,
                    'url': None,
                    'method': 'POST',
                },
                'cooldown_minutes': 15,  # Minimum time between same alerts
            },
            'checks': {
                'agent_timeout_minutes': 30,  # Consider agent dead if no activity
                'disk_usage_threshold': 90,  # Alert if disk usage > 90%
                'queue_size_threshold': 100,  # Alert if queue > 100 items
            },
            'dashboard': {
                'enabled': True,
                'refresh_interval_seconds': 60,
            },
        }
        
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge configs
                    self._merge_config(default_config, user_config)
            except Exception as e:
                logging.warning(f"Failed to load config: {e}, using defaults")
        
        return default_config

    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge config dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _setup_logging(self):
        """Configure logging."""
        log_dir = self.vault_path / 'Logs' / 'Monitoring'
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
        
        self.logger = logging.getLogger('HealthMonitor')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def check_all(self) -> List[HealthStatus]:
        """Run all health checks."""
        self.logger.info("Running all health checks")
        
        checks = [
            self._check_cloud_agent,
            self._check_local_agent,
            self._check_vault_sync,
            self._check_disk_space,
            self._check_queue_sizes,
            self._check_logs,
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                self.logger.error(f"Check {check.__name__} failed: {e}", exc_info=True)
                results.append(HealthStatus(
                    component=check.__name__.replace('_check_', ''),
                    status='unknown',
                    message=f'Check failed: {str(e)}',
                    timestamp=datetime.now().isoformat(),
                ))
        
        # Process alerts based on health status
        self._process_health_results(results)
        
        return results

    def _check_cloud_agent(self) -> HealthStatus:
        """Check Cloud Agent health."""
        cloud_log_dir = self.vault_path / 'Logs' / 'Cloud'
        
        # Check if log directory exists
        if not cloud_log_dir.exists():
            return HealthStatus(
                component='cloud_agent',
                status='unknown',
                message='Cloud agent log directory not found',
                timestamp=datetime.now().isoformat(),
                recovery_suggestion='Ensure Cloud agent is deployed and running',
            )
        
        # Check for recent log activity
        today = datetime.now().strftime('%Y-%m-%d')
        today_log = cloud_log_dir / f'{today}.log'
        
        if not today_log.exists():
            # Check if there's any recent log
            logs = sorted(cloud_log_dir.glob('*.log'), key=lambda f: f.stat().st_mtime, reverse=True)
            
            if not logs:
                return HealthStatus(
                    component='cloud_agent',
                    status='unhealthy',
                    message='No Cloud agent logs found',
                    timestamp=datetime.now().isoformat(),
                    recovery_suggestion='Start Cloud agent: python platinum/cloud/cloud_agent.py --continuous',
                )
            
            latest_log = logs[0]
            age = datetime.now() - datetime.fromtimestamp(latest_log.stat().st_mtime)
            
            if age > timedelta(minutes=self.config['checks']['agent_timeout_minutes']):
                return HealthStatus(
                    component='cloud_agent',
                    status='unhealthy',
                    message=f'Cloud agent inactive for {age.seconds // 60} minutes',
                    timestamp=datetime.now().isoformat(),
                    recovery_suggestion='Restart Cloud agent or check VM status',
                )
        
        # Check for errors in recent logs
        error_count = self._count_log_errors(today_log if today_log.exists() else logs[0])
        
        if error_count > 10:
            return HealthStatus(
                component='cloud_agent',
                status='degraded',
                message=f'High error count in Cloud agent logs: {error_count}',
                timestamp=datetime.now().isoformat(),
                details={'error_count': error_count},
                recovery_suggestion='Review Cloud agent logs for errors',
            )
        
        return HealthStatus(
            component='cloud_agent',
            status='healthy',
            message='Cloud agent is running normally',
            timestamp=datetime.now().isoformat(),
            details={'error_count': error_count},
        )

    def _check_local_agent(self) -> HealthStatus:
        """Check Local Agent health."""
        local_log_dir = self.vault_path / 'Logs' / 'Local'
        
        if not local_log_dir.exists():
            return HealthStatus(
                component='local_agent',
                status='unknown',
                message='Local agent log directory not found',
                timestamp=datetime.now().isoformat(),
                recovery_suggestion='Start Local agent: python platinum/local/local_agent.py --continuous',
            )
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_log = local_log_dir / f'{today}.log'
        
        if not today_log.exists():
            logs = sorted(local_log_dir.glob('*.log'), key=lambda f: f.stat().st_mtime, reverse=True)
            
            if not logs:
                return HealthStatus(
                    component='local_agent',
                    status='unhealthy',
                    message='No Local agent logs found',
                    timestamp=datetime.now().isoformat(),
                    recovery_suggestion='Start Local agent',
                )
            
            latest_log = logs[0]
            age = datetime.now() - datetime.fromtimestamp(latest_log.stat().st_mtime)
            
            if age > timedelta(minutes=self.config['checks']['agent_timeout_minutes']):
                return HealthStatus(
                    component='local_agent',
                    status='unhealthy',
                    message=f'Local agent inactive for {age.seconds // 60} minutes',
                    timestamp=datetime.now().isoformat(),
                    recovery_suggestion='Restart Local agent',
                )
        
        error_count = self._count_log_errors(today_log if today_log.exists() else logs[0])
        
        if error_count > 10:
            return HealthStatus(
                component='local_agent',
                status='degraded',
                message=f'High error count in Local agent logs: {error_count}',
                timestamp=datetime.now().isoformat(),
                details={'error_count': error_count},
                recovery_suggestion='Review Local agent logs for errors',
            )
        
        return HealthStatus(
            component='local_agent',
            status='healthy',
            message='Local agent is running normally',
            timestamp=datetime.now().isoformat(),
            details={'error_count': error_count},
        )

    def _check_vault_sync(self) -> HealthStatus:
        """Check vault sync health."""
        git_dir = self.vault_path / '.git'
        
        if not git_dir.exists():
            return HealthStatus(
                component='vault_sync',
                status='degraded',
                message='Git repository not initialized',
                timestamp=datetime.now().isoformat(),
                recovery_suggestion='Initialize sync: python platinum/sync/vault_sync.py init --remote <url>',
            )
        
        try:
            # Check git status
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            uncommitted_changes = len([l for l in result.stdout.split('\n') if l.strip()])
            
            if uncommitted_changes > 50:
                return HealthStatus(
                    component='vault_sync',
                    status='degraded',
                    message=f'Large number of uncommitted changes: {uncommitted_changes}',
                    timestamp=datetime.now().isoformat(),
                    details={'uncommitted_changes': uncommitted_changes},
                    recovery_suggestion='Run vault sync push to commit changes',
                )
            
            # Check remote connectivity
            result = subprocess.run(
                ['git', 'ls-remote', 'origin'],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode != 0:
                return HealthStatus(
                    component='vault_sync',
                    status='degraded',
                    message='Cannot connect to Git remote',
                    timestamp=datetime.now().isoformat(),
                    recovery_suggestion='Check network connectivity and Git remote configuration',
                )
            
            return HealthStatus(
                component='vault_sync',
                status='healthy',
                message='Vault sync is configured correctly',
                timestamp=datetime.now().isoformat(),
                details={'uncommitted_changes': uncommitted_changes},
            )
            
        except subprocess.TimeoutExpired:
            return HealthStatus(
                component='vault_sync',
                status='unhealthy',
                message='Git command timed out',
                timestamp=datetime.now().isoformat(),
                recovery_suggestion='Check network connectivity',
            )
        except Exception as e:
            return HealthStatus(
                component='vault_sync',
                status='unknown',
                message=f'Sync check failed: {str(e)}',
                timestamp=datetime.now().isoformat(),
            )

    def _check_disk_space(self) -> HealthStatus:
        """Check disk space usage."""
        try:
            # Get disk usage
            if sys.platform == 'win32':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(self.vault_path)),
                    None,
                    None,
                    ctypes.pointer(free_bytes)
                )
                free_gb = free_bytes.value / (1024**3)
                total_gb = 500  # Estimate for Windows
                usage_percent = ((total_gb - free_gb) / total_gb) * 100
            else:
                stat = os.statvfs(str(self.vault_path))
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
                total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
                usage_percent = ((total_gb - free_gb) / total_gb) * 100
            
            if usage_percent > self.config['checks']['disk_usage_threshold']:
                return HealthStatus(
                    component='disk_space',
                    status='unhealthy',
                    message=f'Disk usage critical: {usage_percent:.1f}%',
                    timestamp=datetime.now().isoformat(),
                    details={
                        'usage_percent': usage_percent,
                        'free_gb': free_gb,
                        'total_gb': total_gb,
                    },
                    recovery_suggestion='Free up disk space or expand storage',
                )
            
            if usage_percent > 80:
                return HealthStatus(
                    component='disk_space',
                    status='degraded',
                    message=f'Disk usage warning: {usage_percent:.1f}%',
                    timestamp=datetime.now().isoformat(),
                    details={
                        'usage_percent': usage_percent,
                        'free_gb': free_gb,
                        'total_gb': total_gb,
                    },
                    recovery_suggestion='Consider cleaning up old logs and processed files',
                )
            
            return HealthStatus(
                component='disk_space',
                status='healthy',
                message=f'Disk usage normal: {usage_percent:.1f}%',
                timestamp=datetime.now().isoformat(),
                details={
                    'usage_percent': usage_percent,
                    'free_gb': free_gb,
                    'total_gb': total_gb,
                },
            )
            
        except Exception as e:
            return HealthStatus(
                component='disk_space',
                status='unknown',
                message=f'Disk check failed: {str(e)}',
                timestamp=datetime.now().isoformat(),
            )

    def _check_queue_sizes(self) -> HealthStatus:
        """Check queue sizes for backlogs."""
        queues = {
            'needs_action_cloud': 'Needs_Action/Cloud',
            'needs_action_local': 'Needs_Action/Local',
            'pending_approval_cloud': 'Pending_Approval/Cloud',
            'pending_approval_local': 'Pending_Approval/Local',
            'updates': 'Updates',
        }
        
        queue_status = {}
        max_queue_size = 0
        largest_queue = None
        
        for name, path in queues.items():
            folder = self.vault_path / path
            if folder.exists():
                count = len([f for f in folder.glob('*.md')])
                queue_status[name] = count
                if count > max_queue_size:
                    max_queue_size = count
                    largest_queue = name
            else:
                queue_status[name] = 0
        
        if max_queue_size > self.config['checks']['queue_size_threshold']:
            return HealthStatus(
                component='queue_sizes',
                status='degraded',
                message=f'Large queue detected: {largest_queue} has {max_queue_size} items',
                timestamp=datetime.now().isoformat(),
                details={
                    'queue_status': queue_status,
                    'largest_queue': largest_queue,
                    'max_size': max_queue_size,
                },
                recovery_suggestion=f'Process items in {largest_queue} or increase agent processing speed',
            )
        
        return HealthStatus(
            component='queue_sizes',
            status='healthy',
            message='All queues within normal limits',
            timestamp=datetime.now().isoformat(),
            details={'queue_status': queue_status},
        )

    def _check_logs(self) -> HealthStatus:
        """Check log files for critical errors."""
        logs_dir = self.vault_path / 'Logs'
        
        if not logs_dir.exists():
            return HealthStatus(
                component='logs',
                status='unknown',
                message='Logs directory not found',
                timestamp=datetime.now().isoformat(),
            )
        
        critical_errors = []
        
        # Search for critical errors in recent logs
        for log_file in logs_dir.rglob('*.log'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'CRITICAL' in line or 'FATAL' in line:
                            critical_errors.append({
                                'file': str(log_file),
                                'line': line.strip(),
                            })
            except Exception:
                pass
        
        if len(critical_errors) > 5:
            return HealthStatus(
                component='logs',
                status='degraded',
                message=f'Multiple critical errors detected: {len(critical_errors)}',
                timestamp=datetime.now().isoformat(),
                details={'critical_errors': critical_errors[:10]},  # First 10
                recovery_suggestion='Review critical errors in logs and address root causes',
            )
        
        return HealthStatus(
            component='logs',
            status='healthy',
            message='No critical errors in logs',
            timestamp=datetime.now().isoformat(),
            details={'critical_error_count': len(critical_errors)},
        )

    def _count_log_errors(self, log_file: Path) -> int:
        """Count ERROR level entries in a log file."""
        if not log_file or not log_file.exists():
            return 0
        
        try:
            error_count = 0
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'ERROR' in line or 'CRITICAL' in line:
                        error_count += 1
            return error_count
        except Exception:
            return 0

    def _process_health_results(self, results: List[HealthStatus]):
        """Process health results and send alerts if needed."""
        for result in results:
            if result.status in ['unhealthy', 'degraded']:
                severity = 'critical' if result.status == 'unhealthy' else 'warning'
                
                # Check cooldown
                alert_key = f"{result.component}:{result.message}"
                if self._is_in_cooldown(alert_key):
                    self.logger.debug(f"Alert in cooldown: {alert_key}")
                    continue
                
                # Create and send alert
                alert = Alert(
                    alert_id=hashlib.md5(alert_key.encode()).hexdigest()[:8],
                    severity=severity,
                    component=result.component,
                    message=result.message,
                    timestamp=datetime.now().isoformat(),
                    details=result.details,
                )
                
                self._send_alert(alert)
                self._set_cooldown(alert_key)

    def _is_in_cooldown(self, alert_key: str) -> bool:
        """Check if alert is in cooldown period."""
        if alert_key in self.alert_cooldown:
            cooldown_end = self.alert_cooldown[alert_key]
            if datetime.now() < cooldown_end:
                return True
        return False

    def _set_cooldown(self, alert_key: str):
        """Set cooldown for an alert."""
        cooldown_minutes = self.config['alerts']['cooldown_minutes']
        self.alert_cooldown[alert_key] = datetime.now() + timedelta(minutes=cooldown_minutes)

    def _send_alert(self, alert: Alert):
        """Send alert notification."""
        self.alerts.append(alert)
        self.logger.warning(f"Alert [{alert.severity}]: {alert.message}")
        
        if not self.config['alerts']['enabled']:
            self.logger.info("Alerts disabled, skipping notification")
            return
        
        # Send email alert
        if self.config['alerts']['email']['enabled']:
            self._send_email_alert(alert)
        
        # Send webhook alert
        if self.config['alerts']['webhook']['enabled']:
            self._send_webhook_alert(alert)
        
        # Write alert to file
        self._write_alert_file(alert)

    def _send_email_alert(self, alert: Alert):
        """Send alert via email."""
        try:
            email_config = self.config['alerts']['email']
            
            if not email_config.get('sender') or not email_config.get('recipients'):
                self.logger.warning("Email not configured, skipping")
                return
            
            msg = MIMEMultipart()
            msg['From'] = email_config['sender']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"[AI Employee Alert] {alert.severity.upper()}: {alert.component}"
            
            body = f"""
AI Employee Health Alert

Severity: {alert.severity.upper()}
Component: {alert.component}
Time: {alert.timestamp}

Message:
{alert.message}

Details:
{json.dumps(alert.details or {}, indent=2)}

Recovery Suggestion:
{alert.recovery_suggestion or 'N/A'}

---
AI Employee Platinum Tier Health Monitor
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            password = os.environ.get(email_config.get('password_env', 'SMTP_PASSWORD'))
            
            if not password:
                self.logger.warning("SMTP password not found, skipping email")
                return
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender'], password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent to {email_config['recipients']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}", exc_info=True)

    def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook."""
        try:
            import urllib.request
            
            webhook_config = self.config['alerts']['webhook']
            
            if not webhook_config.get('url'):
                self.logger.warning("Webhook URL not configured, skipping")
                return
            
            payload = json.dumps(asdict(alert)).encode('utf-8')
            
            req = urllib.request.Request(
                webhook_config['url'],
                data=payload,
                headers={'Content-Type': 'application/json'},
                method=webhook_config.get('method', 'POST')
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                self.logger.info(f"Webhook alert sent: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}", exc_info=True)

    def _write_alert_file(self, alert: Alert):
        """Write alert to file for persistence."""
        alerts_dir = self.vault_path / 'Logs' / 'Alerts'
        alerts_dir.mkdir(parents=True, exist_ok=True)
        
        alert_file = alerts_dir / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # Read existing alerts
        alerts = []
        if alert_file.exists():
            try:
                with open(alert_file, 'r') as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []
        
        # Add new alert
        alerts.append(asdict(alert))
        
        # Write back
        with open(alert_file, 'w') as f:
            json.dump(alerts, f, indent=2)
        
        self.logger.debug(f"Alert written to {alert_file}")

    def generate_report(self) -> str:
        """Generate health report in Markdown."""
        results = self.check_all()
        
        report = f"""---
generated: {datetime.now().isoformat()}
type: health_report
---

# AI Employee Health Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Component | Status | Message |
|-----------|--------|---------|
"""
        
        for result in results:
            status_icon = {'healthy': '✅', 'degraded': '⚠️', 'unhealthy': '❌', 'unknown': '❓'}.get(result.status, '❓')
            report += f"| {result.component.replace('_', ' ').title()} | {status_icon} {result.status} | {result.message} |\n"
        
        report += f"""
## Detailed Status

"""
        
        for result in results:
            report += f"""### {result.component.replace('_', ' ').title()}

- **Status:** {result.status}
- **Message:** {result.message}
- **Timestamp:** {result.timestamp}
"""
            if result.details:
                report += f"- **Details:** ```json\n{json.dumps(result.details or {}, indent=2)}\n```\n"
            if result.recovery_suggestion:
                report += f"- **Recovery:** {result.recovery_suggestion}\n"
            report += "\n"
        
        # Recent alerts
        alerts_file = self.vault_path / 'Logs' / 'Alerts' / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    alerts = json.load(f)
                
                if alerts:
                    report += "## Recent Alerts\n\n"
                    for alert in alerts[-10:]:  # Last 10 alerts
                        report += f"- **[{alert['severity'].upper()}]** {alert['component']}: {alert['message']}\n"
                    report += "\n"
            except Exception:
                pass
        
        report += f"""
---
*Generated by AI Employee Health Monitor v1.0*
"""
        
        return report

    def run_check(self):
        """Run health check and print results."""
        results = self.check_all()
        
        print("\n" + "=" * 70)
        print("HEALTH CHECK RESULTS")
        print("=" * 70)
        
        for result in results:
            status_icon = {'healthy': '✅', 'degraded': '⚠️', 'unhealthy': '❌', 'unknown': '❓'}.get(result.status, '❓')
            print(f"\n{status_icon} {result.component.replace('_', ' ').title()}")
            print(f"   Status: {result.status}")
            print(f"   Message: {result.message}")
            if result.recovery_suggestion:
                print(f"   Recovery: {result.recovery_suggestion}")
        
        print("\n" + "=" * 70)
        
        # Summary
        healthy = sum(1 for r in results if r.status == 'healthy')
        total = len(results)
        
        if healthy == total:
            print("✅ All systems healthy!")
        else:
            print(f"⚠️ {total - healthy} component(s) need attention")

    def run_monitor(self, interval: int = 60):
        """Run continuous monitoring."""
        self.logger.info(f"Starting continuous health monitoring (interval: {interval}s)")
        
        try:
            while True:
                self.check_all()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info("Health monitoring stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Health Monitor - Platinum Tier')
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Check command
    subparsers.add_parser('check', help='Run health check')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Run continuous monitoring')
    monitor_parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    
    # Report command
    subparsers.add_parser('report', help='Generate health report')
    
    # Test alert command
    subparsers.add_parser('test-alert', help='Send test alert')
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(
        vault_path=args.vault_path,
        config_path=args.config
    )
    
    if args.command == 'check':
        monitor.run_check()
        
    elif args.command == 'monitor':
        monitor.run_monitor(interval=args.interval)
        
    elif args.command == 'report':
        report = monitor.generate_report()
        
        # Save report
        report_file = monitor.vault_path / 'Briefings' / f'Health_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report, encoding='utf-8')
        
        print(f"Health report saved to: {report_file}")
        print("\n" + report)
        
    elif args.command == 'test-alert':
        test_alert = Alert(
            alert_id='test',
            severity='info',
            component='health_monitor',
            message='This is a test alert from AI Employee Health Monitor',
            timestamp=datetime.now().isoformat(),
            details={'test': True},
        )
        monitor._send_alert(test_alert)
        print("Test alert sent!")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
