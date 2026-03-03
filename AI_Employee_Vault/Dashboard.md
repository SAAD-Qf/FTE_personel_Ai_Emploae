---
last_updated: 2026-03-04T00:00:00Z
status: active
tier: gold
version: 1.0
---

# AI Employee Dashboard

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

> **Tier:** 🏆 Gold Tier - Autonomous Employee

---

## Quick Status

| Metric | Value |
|--------|-------|
| **Pending Items** | 0 |
| **In Progress** | 0 |
| **Awaiting Approval** | 0 |
| **Completed Today** | 0 |
| **Active Ralph Loop** | No |

---

## Inbox Summary

### Needs Action
*No items pending*

### In Progress
*No items currently being processed*

### Pending Approval
*No items awaiting your approval*

---

## Recent Activity

| Timestamp | Action | Status |
|-----------|--------|--------|
| — | — | — |

---

## Business Metrics

### Revenue (MTD)
- **Target:** $10,000
- **Current:** $0
- **Progress:** 0%

### Revenue (This Week)
- **Total:** $0
- **Invoices Sent:** 0
- **Invoices Paid:** 0
- **Outstanding:** $0

### Expenses (This Week)
- **Total:** $0
- **Subscriptions:** $0

### Active Projects
*No active projects*

---

## Social Media Summary

| Platform | Published | Scheduled | Drafts |
|----------|-----------|-----------|--------|
| LinkedIn | 0 | 0 | 0 |
| Facebook | 0 | 0 | 0 |
| Instagram | 0 | 0 | 0 |
| Twitter/X | 0 | 0 | 0 |

---

## System Health

| Component | Status |
|-----------|--------|
| File Watcher | ⏳ Not running |
| Gmail Watcher | ⏳ Not running |
| WhatsApp Watcher | ⏳ Not running |
| Orchestrator | ⏳ Not running |
| Ralph Wiggum Loop | ⏳ Not running |
| Odoo MCP | ⏳ Not configured |
| Last Sync | — |

---

## Gold Tier Features

### ✅ Accounting Integration (Odoo)
- **Status:** Ready to configure
- **Config:** `~/.config/odoo_config.json`
- **Capabilities:** Invoices, Payments, Business Metrics, P&L Reports

### ✅ Social Media Auto-Posting
- **Facebook/Instagram:** Configured
- **Twitter/X:** Configured
- **LinkedIn:** Configured
- **Cross-Platform Posting:** Available

### ✅ Weekly CEO Briefing
- **Last Briefing:** None yet
- **Schedule:** Every Monday at 7:00 AM
- **Includes:** Revenue, Expenses, Bottlenecks, Suggestions

### ✅ Ralph Wiggum Autonomous Loop
- **Status:** Ready
- **Max Iterations:** 10 (configurable)
- **Completion Detection:** Promise-based & File-based

### ✅ Comprehensive Audit Logging
- **Log Location:** `AI_Employee_Vault/Logs/Audit/`
- **Retention:** 90 days
- **Export Formats:** JSON, CSV

---

## Quick Commands

### Core Operations
```bash
# Start filesystem watcher
python scripts/filesystem_watcher.py --vault-path ./AI_Employee_Vault

# Process pending items with Claude
claude --prompt "Check /Needs_Action folder and process all items"

# Start orchestrator (continuous mode)
python scripts/orchestrator.py --vault-path ./AI_Employee_Vault --continuous
```

### Gold Tier Commands
```bash
# Generate weekly CEO briefing
python scripts/weekly_audit.py --vault-path ./AI_Employee_Vault generate

# Start Ralph Wiggum autonomous loop
python scripts/ralph_wiggum.py --vault-path ./AI_Employee_Vault start "Process all pending items" --auto

# View audit summary (last 7 days)
python scripts/audit_logger.py --vault-path ./AI_Employee_Vault summary --days 7

# Export audit logs
python scripts/audit_logger.py --vault-path ./AI_Employee_Vault export --format csv --days 30

# Post to social media
python scripts/facebook_instagram_poster.py --vault-path ./AI_Employee_Vault post both "Your message"
python scripts/twitter_poster.py --vault-path ./AI_Employee_Vault post "Your tweet"
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault post "Your post"
```

### MCP Server Setup
```bash
# Start Odoo MCP server (configure first)
python scripts/odoo_mcp_server.py --config-path ~/.config/odoo_config.json

# Start Email MCP server
python scripts/email_mcp_server.py --credentials-path ./scripts/credentials.json
```

---

## Folder Structure Reference

```
AI_Employee_Vault/
├── Inbox/                  # Raw incoming items
│   └── Files/              # Dropped files storage
├── Needs_Action/           # Items requiring processing
├── In_Progress/            # Currently being worked on
├── Done/                   # Completed tasks
├── Pending_Approval/       # Awaiting human approval
├── Approved/               # Approved actions ready to execute
├── Rejected/               # Rejected actions
├── Plans/                  # Generated plans (Plan.md)
├── Briefings/              # CEO briefings (Monday Morning Briefing)
├── Logs/                   # Audit logs
│   └── Audit/              # Structured audit entries
├── Posts/                  # Social media posts
│   ├── Facebook/           # Facebook posts
│   ├── Instagram/          # Instagram posts
│   ├── Twitter/            # Twitter/X posts
│   ├── Published/          # All published posts
│   ├── Scheduled/          # Scheduled posts
│   └── Drafts/             # Draft posts
├── Invoices/               # Generated invoices
└── .ralph_state/           # Ralph Wiggum loop state
```

---

## Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| Odoo Config | Odoo ERP connection | `~/.config/odoo_config.json` |
| Gmail Credentials | Gmail API OAuth | `./scripts/credentials.json` |
| MCP Config | Claude Code MCP servers | `~/.config/claude-code/mcp.json` |

---

## Tier Progression

| Tier | Status | Features |
|------|--------|----------|
| 🥉 Bronze | ✅ Complete | Vault, File Watcher, Basic Orchestrator |
| 🥈 Silver | ✅ Complete | Gmail/WhatsApp Watchers, LinkedIn, Email MCP, Approval Workflow |
| 🏆 Gold | ✅ Complete | Odoo, Facebook/Instagram, Twitter, Weekly Audit, Ralph Loop, Audit Logging |
| 💎 Platinum | ⏳ Pending | Cloud Deployment, Domain Specialization, A2A Upgrade |

---

*Generated by AI Employee v1.0 (Gold Tier)*
