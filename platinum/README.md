# Platinum Tier - AI Employee

**Always-On Cloud + Local Executive (Production-ish AI Employee)**

## Overview

Platinum Tier represents the pinnacle of the AI Employee hackathon project. It deploys your AI Employee across **Cloud** (24/7 operation) and **Local** (your machine) environments with secure synchronization.

### Tagline

*Your life and business on autopilot. Cloud-scale, local-control, human-in-the-loop.*

---

## Architecture

### Dual-Agent Design

```
┌─────────────────────────────────────────┐
│          CLOUD (24/7 Always-On)         │
│  ┌─────────────────────────────────┐    │
│  │  Cloud Agent                    │    │
│  │  - Email triage (draft-only)    │    │
│  │  - Social media drafts          │    │
│  │  - Business summaries           │    │
│  │  - NEVER sends/posts directly   │    │
│  └─────────────────────────────────┘    │
│              ↓ creates approval         │
│  ┌─────────────────────────────────┐    │
│  │  Pending_Approval/Cloud/        │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
              ↓ Git Sync (vault)
┌─────────────────────────────────────────┐
│    LOCAL (Your Machine - Secure)        │
│  ┌─────────────────────────────────┐    │
│  │  Human reviews approval         │    │
│  │  Moves file to /Approved/       │    │
│  └─────────────────────────────────┘    │
│              ↓ detects approval         │
│  ┌─────────────────────────────────┐    │
│  │  Local Agent                    │    │
│  │  - Executes approved actions    │    │
│  │  - Sends emails (via MCP)       │    │
│  │  - Posts to social media        │    │
│  │  - Processes payments           │    │
│  │  - WhatsApp (browser session)   │    │
│  │  - ALL sensitive ops local      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Domain Specialization

| Responsibility | Cloud Agent | Local Agent |
|---------------|-------------|-------------|
| Email Triage | ✅ Draft replies | ❌ |
| Social Drafts | ✅ Create drafts | ❌ |
| Business Summaries | ✅ Generate | ❌ |
| **Send Emails** | ❌ Draft only | ✅ **After approval** |
| **Post to Social** | ❌ Draft only | ✅ **After approval** |
| **Payments** | ❌ Never | ✅ **After approval** |
| **WhatsApp** | ❌ Never | ✅ **Local browser** |
| **Banking** | ❌ Never | ✅ **Local only** |

---

## Features

### Platinum Tier Requirements

- [x] **Cloud Agent** - 24/7 operation on Cloud VM or Vercel
- [x] **Local Agent** - Approvals, payments, final actions
- [x] **Vault Sync** - Git-based Cloud ↔ Local synchronization
- [x] **Domain Specialization** - Cloud vs Local responsibilities
- [x] **Security Rules** - Credentials never sync to Cloud
- [x] **Vercel Deployment** - Serverless API for Cloud Agent
- [x] **Health Monitoring** - System health + alerts
- [x] **Odoo Cloud** - 24/7 accounting on Cloud VM with HTTPS

### Key Components

#### 1. Cloud Agent (`platinum/cloud/cloud_agent.py`)

```bash
# Run continuously on Cloud VM
python platinum/cloud/cloud_agent.py --vault-path ./vault --continuous
```

**Capabilities:**
- Email triage and draft replies
- Social media post drafts
- Business summaries
- Creates approval requests (cannot execute)

#### 2. Local Agent (`platinum/local/local_agent.py`)

```bash
# Run on your local machine
python platinum/local/local_agent.py --vault-path ./AI_Employee_Vault --continuous
```

**Capabilities:**
- Process human approvals
- Execute approved actions (send, post, pay)
- WhatsApp browser automation
- Merge Cloud updates into Dashboard

#### 3. Vault Sync (`platinum/sync/vault_sync.py`)

```bash
# Initialize sync (first time)
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local init --remote <git-url>

# Push changes
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local push

# Pull changes
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local pull
```

**Security:**
- `.gitignore` blocks sensitive files
- Credentials never sync to Cloud
- Single-writer rule for Dashboard.md

#### 4. Health Monitor (`platinum/monitoring/health_monitor.py`)

```bash
# Run continuous monitoring
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault monitor --interval 60

# Generate health report
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault report
```

**Monitors:**
- Cloud Agent health
- Local Agent health
- Vault sync status
- Disk space
- Queue sizes
- Log errors

---

## Folder Structure

```
AI_Employee_Vault/
├── Needs_Action/
│   ├── Cloud/          # Cloud agent processes these
│   └── Local/          # Local agent processes these
├── In_Progress/
│   ├── Cloud/          # Files claimed by Cloud
│   └── Local/          # Files claimed by Local
├── Pending_Approval/
│   ├── Cloud/          # Cloud-generated approvals
│   └── Local/          # Local-generated approvals
├── Updates/            # Cloud → Local updates
├── Signals/            # Bidirectional signals
├── Approved/           # Approved actions (Local executes)
├── Rejected/           # Rejected actions
├── Done/              # Completed tasks
├── Plans/
│   ├── Cloud/
│   └── Local/
├── Briefings/         # CEO briefings, health reports
├── Logs/
│   ├── Cloud/         # Cloud agent logs
│   ├── Local/         # Local agent logs (never sync)
│   ├── Monitoring/    # Health monitor logs
│   ├── Sync/          # Vault sync logs
│   └── Alerts/        # Health alerts
├── Dashboard.md       # Single-writer: Local only
├── Business_Goals.md
└── Company_Handbook.md
```

---

## Quick Start

### Prerequisites

- [ ] Gold Tier completed and working
- [ ] Vercel account (free tier)
- [ ] Cloud VM (Oracle Cloud Free Tier recommended)
- [ ] Git remote repository (private)
- [ ] Odoo installed on Cloud VM (optional)

### Step 1: Verify Gold Tier

```bash
python scripts/verify_gold.py --vault-path ./AI_Employee_Vault --project-path .
# Must pass before proceeding to Platinum
```

### Step 2: Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd D:\Hackathon_0\FTE_personel_Ai_Emploae
vercel --prod

# Note your production URL
# Example: https://ai-employee-platinum.vercel.app
```

### Step 3: Setup Cloud VM

```bash
# SSH into your Cloud VM
ssh ubuntu@<VM_PUBLIC_IP>

# Clone repository
git clone <YOUR_GIT_REPO_URL>
cd FTE_personel_Ai_Emploae

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Cloud Agent
python3 platinum/cloud/cloud_agent.py --vault-path ~/vault --continuous &
```

### Step 4: Initialize Vault Sync

```bash
# On Local machine (Windows)
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local init --remote <GIT_REMOTE_URL>

# On Cloud VM
python3 platinum/sync/vault_sync.py --vault-path ~/vault --mode cloud init --remote <GIT_REMOTE_URL>
```

### Step 5: Start Health Monitoring

```bash
# On Local machine
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault monitor --interval 60
```

### Step 6: Verify Platinum Tier

```bash
python scripts/verify_platinum.py --vault-path ./AI_Employee_Vault --project-path .
```

---

## Platinum Demo Workflow

This demonstrates the full Cloud + Local workflow:

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

---

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

## Deployment Options

### Option 1: Vercel (Serverless)

**Best for:** Email triage, webhooks, API endpoints

```bash
# Deploy
vercel --prod

# Test health endpoint
curl https://your-project.vercel.app/health
```

**Limits:**
- Serverless timeout: 60 seconds
- Not suitable for continuous watchers
- Use for API endpoints only

### Option 2: Cloud VM (Always-On)

**Best for:** Continuous agents, Odoo, watchers

**Recommended:** Oracle Cloud Free Tier
- 4 ARM cores, 24GB RAM
- 200GB storage
- Always free

```bash
# Deploy Cloud Agent as systemd service
sudo systemctl enable cloud-agent
sudo systemctl start cloud-agent
```

### Option 3: Hybrid (Recommended)

- **Vercel:** Webhooks, API endpoints, health checks
- **Cloud VM:** Cloud Agent, Odoo, watchers
- **Local:** Approvals, payments, WhatsApp, final actions

---

## Monitoring & Alerts

### Health Check Endpoints

```bash
# Vercel health
curl https://your-project.vercel.app/health

# Local health
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault check
```

### Alert Configuration

Edit `config/health_monitor.json`:

```json
{
  "alerts": {
    "enabled": true,
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "sender": "your-email@gmail.com",
      "recipients": ["your-email@gmail.com"]
    },
    "cooldown_minutes": 15
  }
}
```

### Generate Health Report

```bash
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault report

# Saved to: Briefings/Health_Report_YYYYMMDD_HHMMSS.md
```

---

## Troubleshooting

### Cloud Agent Not Processing

```bash
# Check logs
tail -f AI_Employee_Vault/Logs/Cloud/*.log

# Restart Cloud Agent
pkill -f cloud_agent.py
python platinum/cloud/cloud_agent.py --vault-path ./vault --continuous &
```

### Vault Sync Conflicts

```bash
# Check sync status
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault status

# Resolve conflicts manually
git status
git merge --abort  # If needed
git pull origin main
```

### Local Agent Not Executing

```bash
# Check Approved folder
ls -la AI_Employee_Vault/Approved/

# Check Local logs
tail -f AI_Employee_Vault/Logs/Local/*.log

# Restart Local Agent
pkill -f local_agent.py
python platinum/local/local_agent.py --vault-path ./AI_Employee_Vault --continuous &
```

---

## Testing

### Run Platinum Verification

```bash
python scripts/verify_platinum.py --vault-path ./AI_Employee_Vault --project-path .
```

### Test End-to-End

```bash
# Create test email
echo "Test email content" > AI_Employee_Vault/Needs_Action/Cloud/TEST_EMAIL_$(date +%Y%m%d_%H%M%S).md

# Wait for Cloud Agent to process
# Check Updates folder for results
ls -la AI_Employee_Vault/Updates/

# Check Pending_Approval
ls -la AI_Employee_Vault/Pending_Approval/Cloud/
```

---

## Resources

- **Deployment Guide:** `DEPLOYMENT.md`
- **Hackathon Docs:** `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **Vercel Docs:** https://vercel.com/docs
- **Oracle Cloud:** https://www.oracle.com/cloud/free/
- **Odoo Docs:** https://www.odoo.com/documentation/

---

*Platinum Tier v1.0 - AI Employee*
