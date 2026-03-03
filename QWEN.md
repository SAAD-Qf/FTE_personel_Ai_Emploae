# Personal AI Employee (Digital FTE) Project

## Project Overview

This is a **hackathon project** focused on building a "Digital FTE" (Full-Time Equivalent) — an autonomous AI employee that proactively manages personal and business affairs 24/7. The project leverages **Claude Code** as the reasoning engine and **Obsidian** as the knowledge management dashboard.

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

### Core Architecture

The architecture follows a **Perception → Reasoning → Action** pattern:

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Perception (Watchers)** | Python Sentinel Scripts | Monitor Gmail, WhatsApp, filesystems for triggers |
| **Reasoning (Brain)** | Claude Code | Multi-step reasoning, planning, decision-making |
| **Memory/GUI** | Obsidian (Markdown) | Long-term memory, dashboard, human-readable state |
| **Action (Hands)** | MCP Servers | External system integration (email, browser, payments) |
| **Persistence** | Ralph Wiggum Loop | Keeps agent working until task completion |

### Key Concepts

- **Watchers:** Lightweight Python scripts that run continuously, monitoring inputs and creating `.md` files in `/Needs_Action` folder
- **Human-in-the-Loop (HITL):** Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
- **Ralph Wiggum Pattern:** A Stop hook that prevents Claude from exiting until tasks are complete
- **Business Handover:** Autonomous weekly audits generating "Monday Morning CEO Briefing"

## Directory Structure

```
FTE_personel_Ai_Emploae/
├── .qwen/skills/           # Qwen Code skills (browsing-with-playwright)
├── .claude/                # Claude Code plugins (ralph-wiggum)
├── Vault/                  # Obsidian vault (to be created)
│   ├── Inbox/              # Raw incoming items
│   ├── Needs_Action/       # Items requiring processing
│   ├── In_Progress/        # Currently being worked on
│   ├── Done/               # Completed tasks
│   ├── Pending_Approval/   # Awaiting human approval
│   ├── Approved/           # Approved actions ready to execute
│   ├── Plans/              # Generated plans (Plan.md)
│   ├── Briefings/          # CEO briefings
│   ├── Business_Goals.md   # Objectives and metrics
│   └── Dashboard.md        # Real-time summary
├── scripts/                # Watcher scripts and utilities
└── QWEN.md                 # This file
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Active subscription | Primary reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts & orchestration |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers & automation |
| [GitHub Desktop](https://desktop.github.com/download/) | Latest | Version control |

**Hardware:** Minimum 8GB RAM, 4-core CPU, 20GB free disk. Recommended: 16GB RAM, 8-core CPU, SSD.

### Setup Commands

```bash
# 1. Verify Claude Code installation
claude --version

# 2. Create Obsidian vault structure
mkdir -p Vault/{Inbox,Needs_Action,In_Progress,Done,Pending_Approval,Approved,Plans,Briefings}

# 3. Start Playwright MCP server (for browser automation)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# 4. Verify Playwright server
python3 .qwen/skills/browsing-with-playwright/scripts/verify.py

# 5. Stop Playwright server (when done)
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh
```

### Running Watchers (Example)

```bash
# Gmail Watcher (requires Gmail API credentials)
python scripts/gmail_watcher.py --vault-path ./Vault

# File System Watcher
python scripts/filesystem_watcher.py --vault-path ./Vault

# WhatsApp Watcher (Playwright-based)
python scripts/whatsapp_watcher.py --vault-path ./Vault --session-path ~/.whatsapp_session
```

### Ralph Wiggum Loop (Persistence)

```bash
# Start autonomous task processing
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

## Development Conventions

### Agent Skills

All AI functionality should be implemented as **[Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)**. Use prompt engineering to convert AI functionality into reusable skills.

### File-Based Communication

- **Single-writer rule:** Only one agent writes to `Dashboard.md` at a time
- **Claim-by-move rule:** First agent to move a file from `/Needs_Action` to `/In_Progress/<agent>/` owns it
- **Markdown format:** All state is stored in `.md` files with YAML frontmatter

### YAML Frontmatter Standard

All action files must include:

```yaml
---
type: email|whatsapp|file_drop|approval_request|plan
from: sender@example.com
subject: Topic
priority: high|medium|low
status: pending|in_progress|done|approved|rejected
created: 2026-01-07T10:30:00Z
---
```

### Human-in-the-Loop Pattern

For sensitive actions (payments, sending messages):

1. Claude creates `/Pending_Approval/ACTION_Description_Date.md`
2. User reviews and moves file to `/Approved` or `/Rejected`
3. Orchestrator executes approved actions via MCP servers

### Logging & Audit

- All actions logged with timestamps
- Weekly audit generates `/Briefings/YYYY-MM-DD_Monday_Briefing.md`
- Transaction categorization for subscription audits

## MCP Servers

| Server | Capabilities | Configuration |
|--------|-------------|---------------|
| `filesystem` | Read/write/list files | Built-in |
| `email-mcp` | Send/draft/search emails | `~/.config/claude-code/mcp.json` |
| `browser-mcp` | Navigate/click/fill forms | Headless mode recommended |
| `calendar-mcp` | Create/update events | Google Calendar API |
| `slack-mcp` | Send messages/read channels | Slack token |

### MCP Configuration Example

```json
// ~/.config/claude-code/mcp.json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "GMAIL_CREDENTIALS": "/path/to/credentials.json"
      }
    },
    {
      "name": "browser",
      "command": "npx",
      "args": ["@anthropic/browser-mcp"],
      "env": {
        "HEADLESS": "true"
      }
    }
  ]
}
```

## Hackathon Tiers

| Tier | Requirements | Estimated Time |
|------|-------------|----------------|
| **Bronze** | Obsidian vault, 1 Watcher, Claude reading/writing | 8-12 hours |
| **Silver** | 2+ Watchers, Plan.md generation, 1 MCP server, HITL workflow | 20-30 hours |
| **Gold** | Full integration, Odoo MCP, weekly briefings, Ralph Wiggum loop | 40+ hours |
| **Platinum** | Cloud deployment, domain specialization, A2A upgrade | 60+ hours |

## Testing Practices

- **Watcher verification:** Each watcher should have a `verify.py` script
- **MCP server testing:** Test each MCP tool independently before integration
- **End-to-end:** Simulate full workflows (email → watcher → Claude → approval → action)

## Resources

- [Hackathon Documentation](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Playwright Tools Reference](./.qwen/skills/browsing-with-playwright/references/playwright-tools.md)
- [Ralph Wiggum Plugin](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- [Agent Skills Documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Odoo Integration](https://github.com/AlanOgic/mcp-odoo-adv)

## Weekly Research Meetings

**When:** Wednesdays at 10:00 PM PKT  
**Zoom:** [Join Meeting](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1) (ID: 871 8870 7642, Passcode: 744832)  
**YouTube:** [Panaversity Channel](https://www.youtube.com/@panaversity)
