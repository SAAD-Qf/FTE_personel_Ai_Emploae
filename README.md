# AI Employee - Platinum Tier

> **Tagline:** Your life and business on autopilot. Cloud-scale, local-control, human-in-the-loop.

> **Tier:** 💎 Platinum Tier - Always-On Cloud + Local Executive

This is a **Platinum Tier** implementation of the Personal AI Employee from the [Hackathon 0](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md). It builds upon Gold Tier with Cloud + Local architecture, secure vault sync, health monitoring, and Vercel deployment.

## Platinum Tier Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Cloud Agent** | ✅ | 24/7 email triage + social drafts (draft-only) |
| **Local Agent** | ✅ | Approvals, payments, WhatsApp, final actions |
| **Vault Sync** | ✅ | Git-based Cloud ↔ Local synchronization |
| **Domain Specialization** | ✅ | Cloud vs Local responsibilities |
| **Security Rules** | ✅ | Credentials never sync to Cloud |
| **Vercel Deployment** | ✅ | Serverless API for Cloud Agent |
| **Health Monitoring** | ✅ | System health + alerts |
| **Odoo Cloud** | ✅ | 24/7 accounting on Cloud VM with HTTPS |

## Quick Start

### 1. Verify Platinum Tier Setup

```bash
python scripts/verify_platinum.py --vault-path ./AI_Employee_Vault --project-path .
```

Expected: 55+ checks passed, 0 failed.

### 2. Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod

# Test health endpoint
curl https://your-project.vercel.app/health
```

### 3. Setup Cloud VM (Oracle Cloud Free Tier)

```bash
# SSH into VM
ssh ubuntu@<VM_PUBLIC_IP>

# Clone repository
git clone <YOUR_GIT_REPO_URL>

# Start Cloud Agent
python3 platinum/cloud/cloud_agent.py --vault-path ~/vault --continuous
```

### 4. Initialize Vault Sync

```bash
# Initialize Git sync
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local init --remote <GIT_REMOTE_URL>

# Push changes
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local push
```

### 5. Start Health Monitoring

```bash
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault monitor --interval 60
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLOUD (24/7)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Vercel    │  │  Cloud VM   │  │      Odoo (HTTPS)       │ │
│  │   Serverless│  │   Agent     │  │      Accounting         │ │
│  │   API       │  │  (Docker)   │  │      Invoicing          │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
│                   Git Remote (Sync)                              │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                    (Secure Sync)
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                    LOCAL (Your Machine)                          │
│                          │                                       │
│  ┌───────────────────────┴──────────────────────────────────┐   │
│  │              Local Agent (Python)                         │   │
│  │  - Human approvals                                        │   │
│  │  - Payment execution                                      │   │
│  │  - WhatsApp (browser session)                             │   │
│  │  - Final send/post actions                                │   │
│  └───────────────────────────────────────────────────────────┘   │
│                          │                                       │
│  ┌───────────────────────┴──────────────────────────────────┐   │
│  │           Obsidian Vault (Local Copy)                     │   │
│  │  - Dashboard.md (Local writes)                            │   │
│  │  - /Approved/ (Local executes)                            │   │
│  │  - /Pending_Approval/ (Human reviews)                     │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard (Local writes only)
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Objectives and metrics
├── Needs_Action/             # Items pending processing
│   ├── Cloud/                # Cloud agent processes these
│   └── Local/                # Local agent processes these
├── In_Progress/              # Items currently being worked on
│   ├── Cloud/                # Files claimed by Cloud agent
│   └── Local/                # Files claimed by Local agent
├── Done/                     # Completed items
├── Pending_Approval/         # Awaiting human approval
│   ├── Cloud/                # Cloud-generated approvals
│   └── Local/                # Local-generated approvals
├── Approved/                 # Approved actions ready to execute
├── Rejected/                 # Rejected actions
├── Plans/                    # Generated plans (Plan.md)
│   ├── Cloud/                # Cloud agent plans
│   └── Local/                # Local agent plans
├── Briefings/                # Daily/weekly briefings, health reports
├── Logs/                     # Audit logs
│   ├── Cloud/                # Cloud agent logs
│   ├── Local/                # Local agent logs (never sync)
│   ├── Monitoring/           # Health monitor logs
│   ├── Sync/                 # Vault sync logs
│   └── Audit/                # Structured audit entries
├── Updates/                  # Cloud → Local updates (Platinum)
├── Signals/                  # Bidirectional signals (Platinum)
├── Posts/                    # Social media posts
│   ├── Facebook/             # Facebook posts
│   ├── Instagram/            # Instagram posts
│   ├── Twitter/              # Twitter/X posts
│   ├── Published/            # All published posts
│   ├── Scheduled/            # Scheduled posts
│   └── Drafts/               # Draft posts
└── Invoices/                 # Generated invoices
```

## Scripts Reference

### Watchers

| Script | Purpose | Command |
|--------|---------|---------|
| `filesystem_watcher.py` | Monitor file drops | `python scripts/filesystem_watcher.py --vault-path ./AI_Employee_Vault` |
| `gmail_watcher.py` | Monitor Gmail | `python scripts/gmail_watcher.py --vault-path ./AI_Employee_Vault --credentials-path ./credentials.json` |
| `whatsapp_watcher.py` | Monitor WhatsApp | `python scripts/whatsapp_watcher.py --vault-path ./AI_Employee_Vault --session-path ./whatsapp_session` |

### Processing

| Script | Purpose | Command |
|--------|---------|---------|
| `orchestrator.py` | Manage task processing | `python scripts/orchestrator.py --vault-path ./AI_Employee_Vault --continuous` |
| `plan_manager.py` | Create/manage plans | `python scripts/plan_manager.py --vault-path ./AI_Employee_Vault create "Process invoice"` |
| `approval_manager.py` | Handle approvals | `python scripts/approval_manager.py --vault-path ./AI_Employee_Vault list` |

### Actions

| Script | Purpose | Command |
|--------|---------|---------|
| `email_mcp_server.py` | Send emails via MCP | Configure in Claude Code MCP settings |
| `linkedin_poster.py` | Post to LinkedIn | `python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault post "Content"` |
| `agent_skills.py` | Reusable AI skills | Import as module: `from agent_skills import AgentSkills` |

### Scheduling & Maintenance

| Script | Purpose | Command |
|--------|---------|---------|
| `setup_scheduler.py` | Windows Task Scheduler | `python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault --all install` |
| `daily_briefing.py` | Generate daily briefings | `python scripts/daily_briefing.py --vault-path ./AI_Employee_Vault` |
| `cleanup.py` | Weekly cleanup | `python scripts/cleanup.py --vault-path ./AI_Employee_Vault --dry-run` |

## Usage Examples

### Example 1: Email Processing with Approval

1. Gmail Watcher detects important email → Creates action file in `Needs_Action/`
2. Orchestrator triggers Claude → Reads email, creates plan in `Plans/`
3. Claude determines reply needed → Creates approval request in `Pending_Approval/`
4. Human reviews and moves file to `Approved/`
5. Email MCP sends reply → File moved to `Done/`

### Example 2: LinkedIn Auto-Posting

```bash
# Generate post content
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault generate \
  --topic "Q1 business growth" --tone enthusiastic --length medium

# Create draft for review
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault draft \
  "Generated content here" --title "Q1_Update"

# After review, post directly
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault post-file \
  ./AI_Employee_Vault/Posts/Drafts/DRAFT_*.md
```

### Example 3: Daily Briefing

```bash
# Generate briefing for yesterday
python scripts/daily_briefing.py --vault-path ./AI_Employee_Vault

# Generate for specific date
python scripts/daily_briefing.py --vault-path ./AI_Employee_Vault --date 2026-03-03
```

### Example 4: Using Agent Skills

```python
from agent_skills import AgentSkills

skills = AgentSkills(vault_path="./AI_Employee_Vault")

# Create a plan
result = skills.create_plan(
    objective="Process client invoice and send receipt",
    source_file="invoice_123.pdf",
    priority="high"
)

# Request approval for sensitive action
approval = skills.request_approval(
    action_type="email_send",
    description="Send invoice to client",
    details={"to": "client@example.com", "amount": "$1,500"}
)

# Update dashboard
skills.update_dashboard()
```

## Human-in-the-Loop Workflow

### Approval Process

1. **AI Creates Request**: When Claude detects a sensitive action (payment, email to new contact), it creates a file in `/Pending_Approval/`

2. **Human Reviews**: File contains action details and instructions

3. **Approve**: Move file to `/Approved/` folder

4. **Reject**: Move file to `/Rejected/` with comment

5. **Execute**: Orchestrator processes approved files automatically

### Approval File Format

```markdown
---
type: approval_request
action: email_send
created: 2026-03-04T10:00:00
expires: 2026-03-05T10:00:00
status: pending
---

# Approval Request: Send invoice to Client A

## Details

| Property | Value |
|----------|-------|
| **Action Type** | email_send |
| **To** | client@example.com |
| **Subject** | Invoice #123 |
| **Amount** | $1,500 |

## Instructions

### To Approve
Move this file to the `/Approved/` folder.

### To Reject
Move this file to the `/Rejected/` folder with a comment.
```

## Configuration

### Gmail API Setup

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download `credentials.json`
6. Place in `scripts/` folder
7. First run will open browser for OAuth authorization

### LinkedIn Session

First run should be visible to complete login:

```bash
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault --session-path ./linkedin_session --visible draft "Test"
```

Session will be saved for subsequent headless runs.

### Task Scheduler

```bash
# View installed tasks
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault list

# Remove all tasks
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault remove --all

# Run task immediately
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault run --task AI_Employee_DailyBriefing
```

## Troubleshooting

### Gmail Watcher Not Working

- Verify `credentials.json` is in correct location
- Check OAuth token: delete `.gmail_token.pickle` and re-authenticate
- Ensure Gmail API is enabled in Google Cloud Console

### LinkedIn Posting Fails

- First run must be visible for login: use `--visible` flag
- Check session folder exists and is writable
- LinkedIn Web structure may change - update selectors if needed

### Approval Not Processing

- Ensure file is in `/Approved/` folder (not `/Pending_Approval/`)
- Check orchestrator is running: `python scripts/orchestrator.py --vault-path ./AI_Employee_Vault --continuous`
- Review logs in `Logs/` folder

### Task Scheduler Issues

- Run as Administrator to install tasks
- Check Task Scheduler library for error details
- Verify Python path in task configuration

## Platinum Demo Workflow

The Platinum demo demonstrates the full Cloud + Local workflow:

```bash
# Run demo simulation
python scripts/verify_platinum.py --vault-path ./AI_Employee_Vault --demo
```

### Workflow Steps

1. **Email arrives** (while Local is offline)
   - Cloud Agent detects email in `Needs_Action/Cloud/`
   - Cloud drafts reply (draft-only mode)

2. **Cloud creates approval**
   - Creates `Pending_Approval/Cloud/APPROVAL_EmailReply_*.md`
   - Contains draft reply for human review

3. **Vault sync to Local**
   - Git sync pushes approval file to remote
   - Local pulls changes

4. **Human reviews and approves**
   - User reads approval request
   - Moves file to `Approved/` folder

5. **Local executes action**
   - Local Agent detects approved file
   - Sends email via MCP (after approval only)
   - Logs action to audit log

6. **Task complete**
   - File moved to `Done/`
   - Signal sent to Cloud
   - Dashboard updated
```

## Security Rules

### NEVER Sync to Cloud

The following files and folders MUST stay local:

```
.env
*.key
*.pem
*.crt
*_credentials*
*_token*
*_secret*
credentials.json
.whatsapp_session/
banking*
payment_tokens*
odoo_config.json
mcp.json
Logs/Local/
```

These are blocked by `.gitignore` (auto-generated by vault sync).

### Single-Writer Rules

| File | Writer | Reason |
|------|--------|--------|
| Dashboard.md | Local only | Prevents sync conflicts |
| Pending_Approval/Cloud/ | Cloud | Cloud-generated approvals |
| Approved/ | Local | Local executes approved actions |
| Updates/ | Cloud | Cloud → Local communication |
| Signals/ | Both | Bidirectional signals |

### Claim-by-Move Rule

1. Agent wants to process a file
2. Moves from `Needs_Action/<domain>/` to `In_Progress/<agent>/`
3. First agent to move owns the file
4. Other agents MUST ignore files in `In_Progress/<other_agent>/`

---

## Tier Progression

| Tier | Status | Features |
|------|--------|----------|
| 🥉 Bronze | ✅ Complete | Vault, File Watcher, Basic Orchestrator |
| 🥈 Silver | ✅ Complete | Gmail/WhatsApp Watchers, LinkedIn, Email MCP, Approval Workflow |
| 🏆 Gold | ✅ Complete | Odoo, Facebook/Instagram, Twitter, Weekly Audit, Ralph Loop, Audit Logging |
| 💎 Platinum | ✅ Complete | Cloud Deployment, Domain Specialization, Vault Sync, Health Monitoring |

---

*Built with ❤️ for the AI Employee Hackathon - Platinum Tier*

## Resources

- [Hackathon Documentation](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Claude Code Documentation](https://platform.claude.com/docs)
- [Obsidian Documentation](https://help.obsidian.md)
- [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Documentation](https://modelcontextprotocol.io/introduction)
- [Playwright Documentation](https://playwright.dev/python/)

---

*Built with ❤️ for the AI Employee Hackathon - Silver Tier*
