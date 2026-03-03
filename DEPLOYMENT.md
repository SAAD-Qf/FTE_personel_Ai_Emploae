# Platinum Tier Deployment Guide

**Complete guide for deploying AI Employee Platinum Tier to Vercel + Cloud VM**

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Vercel Deployment](#vercel-deployment)
4. [Cloud VM Deployment](#cloud-vm-deployment)
5. [Odoo Cloud Deployment](#odoo-cloud-deployment)
6. [Vault Sync Setup](#vault-sync-setup)
7. [Health Monitoring](#health-monitoring)
8. [Security Checklist](#security-checklist)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Platinum Tier deploys your AI Employee across two environments:

| Component | Location | Purpose |
|-----------|----------|---------|
| **Cloud Agent** | Vercel + Cloud VM | Email triage, social drafts (draft-only) |
| **Local Agent** | Your machine | Approvals, payments, WhatsApp, final actions |
| **Vault Sync** | Git remote | Synchronizes state between Cloud and Local |
| **Health Monitor** | Both | Monitors system health, sends alerts |
| **Odoo** | Cloud VM | Accounting, invoicing, business metrics |

### Key Security Rules

1. **Credentials NEVER sync to Cloud**: `.env`, tokens, sessions, banking info stay local
2. **Cloud is draft-only**: Cloud Agent creates drafts, Local must approve before sending
3. **Single-writer Dashboard**: Only Local Agent writes to Dashboard.md
4. **Claim-by-move**: First agent to move a file owns it

---

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

---

## Vercel Deployment

### Prerequisites

- Vercel account (free tier works)
- Vercel CLI installed: `npm install -g vercel`
- GitHub repository with your code

### Step 1: Prepare Vercel Configuration

The `platinum/vercel/vercel.json` is already configured. Review and adjust:

```json
{
  "version": 2,
  "name": "ai-employee-platinum",
  "env": {
    "VAULT_PATH": "/tmp/ai-employee-vault",
    "AGENT_MODE": "cloud",
    "LOG_LEVEL": "INFO"
  }
}
```

### Step 2: Deploy to Vercel

```bash
# Navigate to project root
cd D:\Hackathon_0\FTE_personel_Ai_Emploae

# Login to Vercel
vercel login

# Deploy to preview
vercel --prod

# Follow prompts to configure:
# - Set up and deploy? Y
# - Which scope? (select your account)
# - Link to existing project? N
# - Project name? ai-employee-platinum
# - Directory? ./ (root)
# - Want to override settings? N

# After deployment, note your production URL
# Example: https://ai-employee-platinum.vercel.app
```

### Step 3: Configure Environment Variables

In Vercel Dashboard → Settings → Environment Variables:

```
VAULT_PATH=/tmp/ai-employee-vault
AGENT_MODE=cloud
LOG_LEVEL=INFO
```

### Step 4: Test Vercel Deployment

```bash
# Test health endpoint
curl https://your-project.vercel.app/health

# Expected response:
# {"status": "healthy", "timestamp": "...", "mode": "cloud"}
```

### Step 5: Setup Webhooks (Optional)

Configure external services to send webhooks to your Vercel API:

- **Email**: SendGrid/Mailgun → `https://your-project.vercel.app/webhook/email`
- **Social**: Twitter/Facebook → `https://your-project.vercel.app/webhook/social`

---

## Cloud VM Deployment

### Option 1: Oracle Cloud Free Tier (Recommended)

Oracle Cloud offers generous free tier: 4 ARM cores, 24GB RAM, 200GB storage.

#### Step 1: Create Oracle Cloud Account

1. Visit: https://www.oracle.com/cloud/free/
2. Sign up for free account
3. Always Free resources:
   - Up to 4 ARM Ampere A1 Compute instances
   - 24 GB RAM total
   - 200 GB block volume total

#### Step 2: Create VM Instance

```bash
# In Oracle Cloud Console:
# 1. Go to Compute → Instances
# 2. Click "Create Instance"
# 3. Configuration:
#    - Image: Ubuntu 22.04 or 24.04
#    - Shape: VM.Standard.A1.Flex (2 OCPUs, 16GB RAM)
#    - Network: Default VCN
#    - SSH keys: Upload your public key (~/.ssh/id_rsa.pub)
# 4. Click "Create"
```

#### Step 3: Connect to VM

```bash
# SSH into VM (replace with your VM's public IP)
ssh -i ~/.ssh/id_rsa ubuntu@<VM_PUBLIC_IP>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Python
sudo apt install -y python3 python3-pip python3-venv git

# Verify installations
docker --version
python3 --version
git --version
```

#### Step 4: Deploy Cloud Agent

```bash
# Clone your repository
git clone <YOUR_GIT_REPO_URL>
cd FTE_personel_Ai_Emploae

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # Create this if doesn't exist

# Create systemd service for Cloud Agent
sudo nano /etc/systemd/system/cloud-agent.service
```

**cloud-agent.service**:

```ini
[Unit]
Description=AI Employee Cloud Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/FTE_personel_Ai_Emploae
Environment="PATH=/home/ubuntu/FTE_personel_Ai_Emploae/venv/bin"
Environment="VAULT_PATH=/home/ubuntu/vault"
Environment="AGENT_MODE=cloud"
ExecStart=/home/ubuntu/FTE_personel_Ai_Emploae/venv/bin/python3 platinum/cloud/cloud_agent.py --vault-path /home/ubuntu/vault --continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cloud-agent
sudo systemctl start cloud-agent

# Check status
sudo systemctl status cloud-agent
sudo journalctl -u cloud-agent -f
```

#### Step 5: Setup Vault Sync on Cloud VM

```bash
# Initialize Git sync (first time only)
cd /home/ubuntu/FTE_personel_Ai_Emploae
python3 platinum/sync/vault_sync.py --vault-path /home/ubuntu/vault --mode cloud init --remote <YOUR_GIT_REMOTE_URL>

# Configure cron for auto-sync
crontab -e

# Add these lines (sync every 5 minutes):
*/5 * * * * cd /home/ubuntu/FTE_personel_Ai_Emploae && git pull origin main
*/5 * * * * cd /home/ubuntu/FTE_personel_Ai_Emploae && git add . && git commit -m "Auto-sync: Cloud updates" && git push origin main
```

---

## Odoo Cloud Deployment

### Step 1: Deploy Odoo on Cloud VM

```bash
# On your Oracle Cloud VM (or separate VM)

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create Odoo directory
mkdir -p /home/ubuntu/odoo
cd /home/ubuntu/odoo

# Create docker-compose.yml
nano docker-compose.yml
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  odoo:
    image: odoo:17.0
    container_name: odoo
    ports:
      - "8069:8069"
    environment:
      - ODOO_ADMIN_PASSWORD=your_admin_password
      - ODOO_DB_NAME=odoo_db
      - ODOO_DB_USER=odoo
      - ODOO_DB_PASSWORD=your_db_password
    volumes:
      - odoo-data:/var/lib/odoo
      - ./config:/etc/odoo
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    container_name: odoo-postgres
    environment:
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=your_db_password
      - POSTGRES_DB=postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  odoo-data:
  postgres-data:
```

```bash
# Start Odoo
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f odoo
```

### Step 2: Configure HTTPS with Nginx + Let's Encrypt

```bash
# Install Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/odoo
```

**/etc/nginx/sites-available/odoo**:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Step 3: Configure Odoo MCP Server

On your **Local** machine:

```bash
# Create Odoo config
mkdir -p ~/.config
nano ~/.config/odoo_config.json
```

**~/.config/odoo_config.json**:

```json
{
  "odoo_url": "https://your-domain.com",
  "odoo_db": "odoo_db",
  "odoo_username": "admin",
  "odoo_password": "your_admin_password",
  "api_key": "your_api_key"
}
```

```bash
# Test Odoo MCP connection
cd D:\Hackathon_0\FTE_personel_Ai_Emploae
python scripts/odoo_mcp_server.py --config-path ~/.config/odoo_config.json
```

---

## Vault Sync Setup

### Step 1: Create Git Remote

You can use GitHub, GitLab, or any Git service:

```bash
# On GitHub, create a PRIVATE repository
# Name: ai-employee-vault-sync

# Note the repository URL:
# https://github.com/yourusername/ai-employee-vault-sync.git
```

### Step 2: Initialize Sync on Local Machine

```bash
# On your Local machine (Windows)
cd D:\Hackathon_0\FTE_personel_Ai_Emploae

# Initialize vault sync
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local init --remote https://github.com/yourusername/ai-employee-vault-sync.git

# First push
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local push
```

### Step 3: Initialize Sync on Cloud VM

```bash
# On Cloud VM
cd /home/ubuntu/FTE_personel_Ai_Emploae

# Initialize vault sync (cloud mode)
python3 platinum/sync/vault_sync.py --vault-path /home/ubuntu/vault --mode cloud init --remote https://github.com/yourusername/ai-employee-vault-sync.git

# Pull initial state
python3 platinum/sync/vault_sync.py --vault-path /home/ubuntu/vault --mode cloud pull
```

### Step 4: Verify Sync

```bash
# On Local machine - check sync status
python platinum/sync/vault_sync.py --vault-path ./AI_Employee_Vault --mode local status

# Expected output:
# {
#   "is_git_repo": true,
#   "mode": "local",
#   "remote_url": "https://github.com/...",
#   "branch": "main",
#   "changes": []
# }
```

---

## Health Monitoring

### Step 1: Configure Health Monitor

```bash
# Create health monitor config
mkdir -p D:\Hackathon_0\FTE_personel_Ai_Emploae\config
nano config/health_monitor.json
```

**config/health_monitor.json**:

```json
{
  "alerts": {
    "enabled": true,
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender": "your-email@gmail.com",
      "recipients": ["your-email@gmail.com"],
      "password_env": "SMTP_PASSWORD"
    },
    "webhook": {
      "enabled": true,
      "url": "https://your-webhook-url.com/alerts",
      "method": "POST"
    },
    "cooldown_minutes": 15
  },
  "checks": {
    "agent_timeout_minutes": 30,
    "disk_usage_threshold": 90,
    "queue_size_threshold": 100
  },
  "dashboard": {
    "enabled": true,
    "refresh_interval_seconds": 60
  }
}
```

### Step 2: Start Health Monitoring

```bash
# On Local machine
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault --config config/health_monitor.json monitor --interval 60

# On Cloud VM (as systemd service)
# Create /etc/systemd/system/health-monitor.service
```

**health-monitor.service**:

```ini
[Unit]
Description=AI Employee Health Monitor
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/FTE_personel_Ai_Emploae
Environment="PATH=/home/ubuntu/FTE_personel_Ai_Emploae/venv/bin"
ExecStart=/home/ubuntu/FTE_personel_Ai_Emploae/venv/bin/python3 platinum/monitoring/health_monitor.py --vault-path /home/ubuntu/vault --continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable health-monitor
sudo systemctl start health-monitor
sudo systemctl status health-monitor
```

### Step 3: Generate Health Report

```bash
# Generate health report
python platinum/monitoring/health_monitor.py --vault-path ./AI_Employee_Vault report

# Report saved to: AI_Employee_Vault/Briefings/Health_Report_YYYYMMDD_HHMMSS.md
```

---

## Security Checklist

### Before Deployment

- [ ] All sensitive files in `.gitignore`
- [ ] Git repository is PRIVATE
- [ ] HTTPS enabled on Odoo
- [ ] Strong passwords for all services
- [ ] SSH keys (not passwords) for VM access
- [ ] Firewall configured (only necessary ports open)

### Credentials That NEVER Sync to Cloud

- [ ] `.env` files
- [ ] `credentials.json` (Gmail, Google APIs)
- [ ] `.whatsapp_session/` folder
- [ ] `odoo_config.json` (Local copy only)
- [ ] `mcp.json` (Local MCP config)
- [ ] Banking credentials
- [ ] Payment tokens

### Network Security

```bash
# On Cloud VM, configure firewall
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp     # HTTPS (Odoo)
sudo ufw enable

# Verify firewall
sudo ufw status
```

---

## Troubleshooting

### Cloud Agent Not Starting

```bash
# Check systemd service status
sudo systemctl status cloud-agent
sudo journalctl -u cloud-agent -f

# Check if port is available
sudo netstat -tulpn | grep <PORT>

# Restart service
sudo systemctl restart cloud-agent
```

### Vault Sync Failing

```bash
# Check Git status
cd /path/to/vault
git status

# Resolve conflicts
git pull origin main
# If conflicts, edit files, then:
git add .
git commit -m "Resolve sync conflicts"
git push origin main

# Check Git remote
git remote -v
```

### Health Monitor Sending Too Many Alerts

```bash
# Increase cooldown period in config
# Edit config/health_monitor.json:
# "cooldown_minutes": 30  # Increase from 15 to 30

# Restart health monitor
sudo systemctl restart health-monitor
```

### Odoo Connection Failing

```bash
# Check Odoo container
docker ps | grep odoo
docker logs odoo

# Test connection from Local machine
curl https://your-domain.com:8069

# Check SSL certificate
sudo certbot certificates
```

### Vercel Deployment Errors

```bash
# Check build logs
vercel logs <DEPLOYMENT_URL>

# Test locally
vercel dev

# Redeploy
vercel --prod
```

---

## Post-Deployment Verification

### Run Platinum Tier Verification

```bash
# On Local machine
python scripts/verify_platinum.py --vault-path ./AI_Employee_Vault --project-path .

# Expected: All checks pass
# ✓ Platinum Tier Verification Passed!
```

### Run Platinum Demo Workflow

```bash
# Simulate Platinum demo
python scripts/verify_platinum.py --vault-path ./AI_Employee_Vault --demo

# This simulates:
# 1. Email arrives → Cloud drafts reply
# 2. Cloud creates approval request
# 3. Vault sync to Local
# 4. User approves
# 5. Local executes send
# 6. Task complete
```

### Test End-to-End Flow

```bash
# 1. Create test email file
cat > AI_Employee_Vault/Needs_Action/Cloud/TEST_EMAIL_$(date +%Y%m%d_%H%M%S).md << 'EOF'
---
type: email
from: test@example.com
subject: Test Email for Platinum Demo
received: $(date -Iseconds)
priority: medium
status: pending
---

## Email Content

This is a test email to verify Platinum tier deployment.

Please draft a reply and create an approval request.

## Suggested Actions
- [ ] Draft reply
- [ ] Create approval request
EOF

# 2. Wait for Cloud Agent to process (check Updates folder)
ls -la AI_Employee_Vault/Updates/

# 3. Check Pending_Approval folder
ls -la AI_Employee_Vault/Pending_Approval/Cloud/

# 4. Approve (move to Approved)
mv AI_Employee_Vault/Pending_Approval/Cloud/APPROVAL_*.md AI_Employee_Vault/Approved/

# 5. Local Agent executes action
# 6. Check Done folder
ls -la AI_Employee_Vault/Done/
```

---

## Next Steps

After successful deployment:

1. **Configure real email integration**: Set up Gmail API credentials
2. **Configure social media MCP**: Connect Facebook, Twitter, LinkedIn APIs
3. **Setup WhatsApp session**: Run WhatsApp Watcher on Local machine
4. **Configure Odoo integration**: Set up chart of accounts, products, customers
5. **Enable health alerts**: Configure email or webhook alerts
6. **Monitor and optimize**: Review logs, adjust thresholds, scale as needed

---

## Support & Resources

- **Hackathon Documentation**: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **QWEN.md**: Project overview and quick reference
- **Vercel Docs**: https://vercel.com/docs
- **Oracle Cloud Docs**: https://docs.oracle.com/en-us/iaas/
- **Odoo Docs**: https://www.odoo.com/documentation/

---

*Generated by AI Employee Platinum Tier Deployment Guide v1.0*
