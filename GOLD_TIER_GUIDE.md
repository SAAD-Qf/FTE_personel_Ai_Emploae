# Gold Tier Implementation Guide

## Overview

This document provides comprehensive documentation for the **Gold Tier** implementation of the Personal AI Employee (Digital FTE) hackathon project.

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

**Tier Status:** 🏆 Gold Tier - Autonomous Employee

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Gold Tier Features](#gold-tier-features)
3. [Installation & Setup](#installation--setup)
4. [Configuration Guide](#configuration-guide)
5. [Usage Guide](#usage-guide)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     GOLD TIER ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Watchers   │    │   Ralph      │    │   MCP        │      │
│  │  (Senses)    │───▶│   Wiggum     │───▶│   Servers    │      │
│  │              │    │   (Brain)    │    │   (Hands)    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Obsidian Vault (Memory/GUI)                 │   │
│  │  /Inbox /Needs_Action /In_Progress /Done /Briefings     │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Social     │    │   Weekly     │    │   Audit      │      │
│  │   Media      │    │   Audit      │    │   Logger     │      │
│  │   Posters    │    │   Generator  │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Perception:** Watchers monitor Gmail, WhatsApp, filesystem for triggers
2. **Reasoning:** Ralph Wiggum loop keeps Claude working until task completion
3. **Action:** MCP servers handle external systems (Odoo, Email, Social Media)
4. **Memory:** All state stored in Obsidian vault (Markdown files)
5. **Audit:** Comprehensive logging of all actions

---

## Gold Tier Features

### 1. Odoo MCP Integration

**Purpose:** Full accounting and ERP integration for business management.

**Capabilities:**
- Create and manage invoices
- Track payments and transactions
- Generate accounting reports (P&L, Balance Sheet)
- Manage customers and vendors
- Monitor business metrics

**Files:**
- `scripts/odoo_mcp_server.py` - MCP server implementation
- `scripts/odoo_mcp_server.py::OdooClient` - Odoo XML-RPC client

**Setup:**
```bash
# 1. Install Odoo Community Edition (local or cloud)
# 2. Create configuration file
mkdir -p ~/.config
cat > ~/.config/odoo_config.json << EOF
{
  "url": "http://localhost:8069",
  "db": "odoo_db",
  "username": "admin",
  "password": "your_password"
}
EOF

# 3. Test connection
python scripts/odoo_mcp_server.py --config-path ~/.config/odoo_config.json --test-connection
```

### 2. Facebook/Instagram Integration

**Purpose:** Cross-platform social media auto-posting for business promotion.

**Capabilities:**
- Create Facebook posts
- Create Instagram stories
- Cross-post to both platforms
- Schedule posts
- Generate post content

**Files:**
- `scripts/facebook_instagram_poster.py`

**Usage:**
```bash
# Post to both platforms
python scripts/facebook_instagram_poster.py \
  --vault-path ./AI_Employee_Vault \
  --session-path ./fb_ig_session \
  post both "Exciting business update!"

# Generate content
python scripts/facebook_instagram_poster.py \
  --vault-path ./AI_Employee_Vault \
  generate --topic "New product launch" --tone professional
```

### 3. Twitter/X Integration

**Purpose:** Twitter/X auto-posting for real-time business updates.

**Capabilities:**
- Create tweets (280 characters)
- Create tweet threads
- Schedule tweets
- Generate tweet content

**Files:**
- `scripts/twitter_poster.py`

**Usage:**
```bash
# Post a tweet
python scripts/twitter_poster.py \
  --vault-path ./AI_Employee_Vault \
  --session-path ./twitter_session \
  post "Business update here! #Innovation"

# Create a thread
python scripts/twitter_poster.py \
  --vault-path ./AI_Employee_Vault \
  thread "1/3 Thread start" "2/3 Middle" "3/3 End"
```

### 4. Weekly Business Audit & CEO Briefing

**Purpose:** Autonomous weekly business analysis with proactive suggestions.

**Capabilities:**
- Revenue analysis
- Expense tracking
- Subscription audit
- Task completion summary
- Bottleneck identification
- Proactive suggestions

**Files:**
- `scripts/weekly_audit.py`
- `scripts/weekly_audit.py::WeeklyAuditGenerator`

**Usage:**
```bash
# Generate weekly briefing
python scripts/weekly_audit.py \
  --vault-path ./AI_Employee_Vault \
  generate

# Generate with Odoo data
python scripts/weekly_audit.py \
  --vault-path ./AI_Employee_Vault \
  generate --with-odoo

# Schedule weekly (Mondays at 7 AM)
schtasks /create /tn "Weekly CEO Briefing" \
  /tr "python scripts/weekly_audit.py --vault-path ./AI_Employee_Vault generate" \
  /sc weekly /d MON /st 07:00
```

**Output:** `AI_Employee_Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`

### 5. Ralph Wiggum Autonomous Loop

**Purpose:** Keep Claude Code working autonomously until task completion.

**Pattern:**
1. Orchestrator creates state file with prompt
2. Claude works on task
3. Claude tries to exit
4. Stop hook checks: Is task complete?
5. YES → Allow exit | NO → Re-inject prompt (loop continues)

**Files:**
- `scripts/ralph_wiggum.py`
- `scripts/ralph_wiggum.py::RalphWiggumLoop`
- `scripts/ralph_wiggum.py::RalphWiggumOrchestrator`

**Usage:**
```bash
# Start autonomous loop
python scripts/ralph_wiggum.py \
  --vault-path ./AI_Employee_Vault \
  start "Process all pending items in Needs_Action" \
  --auto --max-iterations 10

# Check status
python scripts/ralph_wiggum.py \
  --vault-path ./AI_Employee_Vault \
  status

# Stop loop
python scripts/ralph_wiggum.py \
  --vault-path ./AI_Employee_Vault \
  stop
```

### 6. Comprehensive Audit Logging

**Purpose:** Detailed audit trail for compliance and debugging.

**Capabilities:**
- Structured JSON logging
- Daily log rotation
- Search and filter
- Export (JSON, CSV)
- Report generation

**Files:**
- `scripts/audit_logger.py`
- `scripts/audit_logger.py::AuditLogger`
- `scripts/audit_logger.py::AuditEntry`

**Usage:**
```bash
# Log an action
python scripts/audit_logger.py \
  --vault-path ./AI_Employee_Vault \
  log email_send --actor "ai_employee" \
  --description "Sent invoice to Client A"

# Search logs
python scripts/audit_logger.py \
  --vault-path ./AI_Employee_Vault \
  search --type email_send --days 7

# Get summary
python scripts/audit_logger.py \
  --vault-path ./AI_Employee_Vault \
  summary --days 7

# Export logs
python scripts/audit_logger.py \
  --vault-path ./AI_Employee_Vault \
  export --format csv --days 30

# Generate report
python scripts/audit_logger.py \
  --vault-path ./AI_Employee_Vault \
  report --days 7
```

---

## Installation & Setup

### Prerequisites

```bash
# Python packages
pip install playwright google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install xmlrpc-client mcp

# Playwright browsers
playwright install chromium

# System requirements
# - Python 3.13+
# - Node.js v24+
# - 16GB RAM recommended
# - SSD storage
```

### Step-by-Step Setup

1. **Verify Bronze/Silver tiers complete**
   ```bash
   python scripts/verify_bronze.py --vault-path ./AI_Employee_Vault
   python scripts/verify_silver.py --vault-path ./AI_Employee_Vault
   ```

2. **Install Gold tier dependencies**
   ```bash
   pip install xmlrpc-client mcp
   ```

3. **Configure Odoo (optional)**
   ```bash
   mkdir -p ~/.config
   # Create ~/.config/odoo_config.json
   ```

4. **Verify Gold tier**
   ```bash
   python scripts/verify_gold.py --vault-path ./AI_Employee_Vault
   ```

---

## Configuration Guide

### Odoo Configuration

```json
{
  "url": "http://localhost:8069",
  "db": "odoo_db",
  "username": "admin",
  "password": "secure_password"
}
```

### MCP Server Configuration

```json
{
  "servers": [
    {
      "name": "odoo",
      "command": "python",
      "args": ["D:/Hackathon_0/FTE_personel_Ai_Emploae/scripts/odoo_mcp_server.py"],
      "env": {
        "CONFIG_PATH": "C:/Users/YourName/.config/odoo_config.json"
      }
    },
    {
      "name": "email",
      "command": "python",
      "args": ["D:/Hackathon_0/FTE_personel_Ai_Emploae/scripts/email_mcp_server.py"],
      "env": {
        "CREDENTIALS_PATH": "D:/Hackathon_0/FTE_personel_Ai_Emploae/scripts/credentials.json"
      }
    }
  ]
}
```

---

## Usage Guide

### Daily Operations

```bash
# 1. Start watchers
python scripts/filesystem_watcher.py --vault-path ./AI_Employee_Vault &
python scripts/gmail_watcher.py --vault-path ./AI_Employee_Vault --credentials-path ./credentials.json &

# 2. Start orchestrator
python scripts/orchestrator.py --vault-path ./AI_Employee_Vault --auto-process --continuous &

# 3. Start Ralph loop for autonomous processing
python scripts/ralph_wiggum.py --vault-path ./AI_Employee_Vault \
  start "Process all pending items and move to Done" --auto
```

### Weekly Operations

```bash
# Monday morning: Generate CEO briefing
python scripts/weekly_audit.py --vault-path ./AI_Employee_Vault generate

# Review briefing in Obsidian
# Open: AI_Employee_Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md
```

### Social Media Posting

```bash
# Daily business update
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault \
  post "Daily business update content"

# Cross-platform post
python scripts/facebook_instagram_poster.py --vault-path ./AI_Employee_Vault \
  post both "Cross-platform content"

# Twitter update
python scripts/twitter_poster.py --vault-path ./AI_Employee_Vault \
  post "Quick update #business"
```

---

## API Reference

### OdooClient

```python
from odoo_mcp_server import OdooClient

client = OdooClient(url, db, username, password)

# Create invoice
invoice_id = client.create_invoice(partner_id, lines=[...])

# Get invoices
invoices = client.get_invoices(partner_id=None, state='posted')

# Register payment
result = client.register_payment(invoice_id, amount)

# Get business metrics
metrics = client.get_business_metrics()

# Get P&L statement
pl = client.get_profit_loss()
```

### WeeklyAuditGenerator

```python
from weekly_audit import WeeklyAuditGenerator

generator = WeeklyAuditGenerator(vault_path, odoo_config=None)

# Generate weekly briefing
briefing_path = generator.generate_weekly_briefing(
    week_start=None,  # Auto-detect last Monday
    include_odoo=False
)
```

### RalphWiggumLoop

```python
from ralph_wiggum import RalphWiggumLoop

loop = RalphWiggumLoop(
    vault_path='./AI_Employee_Vault',
    max_iterations=10,
    completion_promise='TASK_COMPLETE'
)

# Start loop
loop.start(prompt="Process pending items")

# Check completion
is_complete = loop.check_completion(claude_output)

# Run iteration
output = loop.run_claude_iteration()
```

### AuditLogger

```python
from audit_logger import AuditLogger

logger = AuditLogger(vault_path='./AI_Employee_Vault')

# Log action
entry = logger.log(
    action_type='email_send',
    actor='ai_employee',
    description='Sent invoice',
    details={'invoice_id': 123}
)

# Search logs
results = logger.search(
    action_type='email_send',
    date_from=datetime.now() - timedelta(days=7)
)

# Get summary
summary = logger.get_summary(days=7)

# Export
export_path = logger.export(format='csv', days=30)
```

---

## Troubleshooting

### Common Issues

**Odoo Connection Failed**
```
Error: Odoo connection failed: Authentication failed
```
**Solution:** Verify credentials in `~/.config/odoo_config.json`

**Playwright Browser Not Found**
```
Error: Executable doesn't exist
```
**Solution:** Run `playwright install chromium`

**Ralph Loop Not Exiting**
```
Loop continues beyond expected completion
```
**Solution:** Check completion_promise string matches Claude's output

**Audit Logs Not Writing**
```
Permission denied: Logs/Audit
```
**Solution:** Check folder permissions, create folder manually

### Debug Mode

Enable verbose logging:
```bash
# Set environment variable
set DEBUG=1

# Run with verbose flag
python scripts/audit_logger.py --vault-path ./AI_Employee_Vault search --verbose
```

---

## Best Practices

### Security

1. **Never commit credentials** - Use environment variables
2. **Restrict vault access** - File permissions 600
3. **Rotate API keys monthly** - Set calendar reminder
4. **Review audit logs weekly** - Check for anomalies

### Performance

1. **Run watchers in background** - Use `&` or task scheduler
2. **Limit Ralph loop iterations** - Start with max_iterations=5
3. **Clean old audit logs** - Run cleanup monthly
4. **Use headless browsers** - Save resources

### Reliability

1. **Enable error logging** - All actions logged
2. **Set up monitoring** - Check dashboard daily
3. **Backup vault regularly** - Use Git or cloud sync
4. **Test recovery procedures** - Practice restores

### Compliance

1. **Retain audit logs 90 days minimum**
2. **Export monthly reports** - For review
3. **Document all configuration changes**
4. **Review approval workflow weekly**

---

## Gold Tier Verification Checklist

- [ ] Odoo MCP server configured and tested
- [ ] Facebook/Instagram posting working
- [ ] Twitter/X posting working
- [ ] Weekly audit generates CEO briefing
- [ ] Ralph Wiggum loop completes tasks autonomously
- [ ] Audit logging captures all actions
- [ ] All verification tests pass

```bash
python scripts/verify_gold.py --vault-path ./AI_Employee_Vault
```

---

*Generated for Personal AI Employee Hackathon - Gold Tier*
*Version 1.0 - March 2026*
