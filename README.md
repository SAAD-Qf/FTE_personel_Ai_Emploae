# AI Employee - Silver Tier

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

This is a **Silver Tier** implementation of the Personal AI Employee from the [Hackathon 0](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md). It builds upon the Bronze Tier foundation with advanced features including multiple watchers, MCP servers, approval workflows, and automated social media posting.

## Silver Tier Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Multiple Watchers** | ✅ | File System, Gmail, and WhatsApp monitoring |
| **LinkedIn Auto-Poster** | ✅ | Automated business posts to generate sales |
| **Plan.md Reasoning** | ✅ | Claude creates multi-step plans for complex tasks |
| **Email MCP Server** | ✅ | Send emails via Model Context Protocol |
| **HITL Approval Workflow** | ✅ | Human-in-the-Loop for sensitive actions |
| **Task Scheduler** | ✅ | Windows Task Scheduler integration |
| **Agent Skills Module** | ✅ | Reusable AI functionality |
| **Daily Briefings** | ✅ | Automated CEO briefings |

## Quick Start

### 1. Verify Silver Tier Setup

```bash
python scripts/verify_silver.py --vault-path ./AI_Employee_Vault --project-path .
```

Expected: 55+ checks passed.

### 2. Install Scheduled Tasks (Windows)

```bash
# Install all scheduled tasks
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . --all install

# Or install individual tasks
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . --filesystem install
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . --orchestrator install
python scripts/setup_scheduler.py --vault-path ./AI_Employee_Vault --project-path . --briefing install
```

### 3. Configure Gmail Watcher (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` to `scripts/` folder
5. First run will require OAuth authentication

```bash
python scripts/gmail_watcher.py --vault-path ./AI_Employee_Vault --credentials-path ./scripts/credentials.json
```

### 4. Test LinkedIn Posting

```bash
# Create a draft post
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault --session-path ./linkedin_session draft "Exciting business update coming soon! #Innovation"

# Post directly (visible browser for first-time login)
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault --session-path ./linkedin_session --visible post "Test post from AI Employee"

# Generate post content
python scripts/linkedin_poster.py --vault-path ./AI_Employee_Vault generate --topic "New product launch" --tone professional --length medium
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│     Gmail       │    WhatsApp     │     File System    │  LinkedIn  │
└────────┬────────┴────────┬────────┴─────────┬────────┴────┬─────────┘
         │                 │                  │             │
         ▼                 ▼                  ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER (Watchers)                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Gmail Watcher│ │WhatsApp Watch│ │File Watcher  │            │
│  │  (API)       │ │ (Playwright) │ │  (watchdog)  │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Local)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /Needs_Action/  │ /Plans/  │ /Done/  │ /Posts/  │ /Logs/ │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Dashboard.md    │ Company_Handbook.md │ Business_Goals.md│  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ /Pending_Approval/  │  /Approved/  │  /Briefings/       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REASONING LAYER                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   CLAUDE CODE + Plan Manager              │ │
│  │   Read → Think → Plan → Request Approval → Write → Done   │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │
              ┌──────────────────┴───────────────────┐
              ▼                                      ▼
┌────────────────────────────┐    ┌────────────────────────────────┐
│    HUMAN-IN-THE-LOOP       │    │         ACTION LAYER           │
│  ┌──────────────────────┐  │    │  ┌─────────────────────────┐   │
│  │ Approval Manager     │──┼───▶│  │    MCP SERVERS          │   │
│  │ /Pending_Approval/   │  │    │  │  ┌──────┐ ┌──────────┐  │   │
│  │ Move to /Approved    │  │    │  │  │Email │ │ LinkedIn │  │   │
│  └──────────────────────┘  │    │  │  │ MCP  │ │  Poster  │  │   │
│                            │    │  │  └──┬───┘ └────┬─────┘  │   │
└────────────────────────────┘    │  └─────┼──────────┼────────┘   │
                                  └────────┼──────────┼────────────┘
                                           │          │
                                           ▼          ▼
                                  ┌────────────────────────────────┐
                                  │     EXTERNAL ACTIONS           │
                                  │  Send Email │ Post to LinkedIn │
                                  └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Windows Task Scheduler (via setup_scheduler.py)   │ │
│  │   On Login: Start watchers                                │ │
│  │   Daily 8AM: Generate briefing                            │ │
│  │   Weekly: Cleanup old logs                                │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Drop folder for new files
│   └── Files/                # Stored copies of dropped files
├── Needs_Action/             # Items pending processing
├── In_Progress/              # Items currently being worked on
├── Done/                     # Completed items
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Approved actions ready to execute
├── Rejected/                 # Rejected actions
├── Plans/                    # Generated plans (Plan.md)
├── Briefings/                # Daily/weekly briefings
├── Logs/                     # Audit logs
└── Posts/                    # LinkedIn posts
    ├── Drafts/               # Draft posts
    ├── Scheduled/            # Scheduled posts
    └── Published/            # Published posts
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

## Silver Tier vs Bronze Tier

| Feature | Bronze | Silver |
|---------|--------|--------|
| Watchers | 1 (File System) | 3 (File + Gmail + WhatsApp) |
| MCP Servers | None | Email MCP |
| Approval Workflow | Basic | Full HITL system |
| Planning | Manual | Plan.md with steps |
| Social Media | None | LinkedIn Auto-Poster |
| Scheduling | Manual | Task Scheduler integration |
| Agent Skills | None | Full module |
| Briefings | Manual | Automated daily |

## Next Steps (Gold Tier)

After mastering Silver Tier, consider adding:

1. **Odoo Integration** - Self-hosted ERP via MCP
2. **Facebook/Instagram** - Social media integration
3. **Twitter (X) Integration** - Post and monitor
4. **Multiple MCP Servers** - Browser, calendar, Slack
5. **Weekly CEO Audit** - Comprehensive business review
6. **Ralph Wiggum Loop** - Autonomous multi-step completion

## Resources

- [Hackathon Documentation](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Claude Code Documentation](https://platform.claude.com/docs)
- [Obsidian Documentation](https://help.obsidian.md)
- [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Documentation](https://modelcontextprotocol.io/introduction)
- [Playwright Documentation](https://playwright.dev/python/)

---

*Built with ❤️ for the AI Employee Hackathon - Silver Tier*
