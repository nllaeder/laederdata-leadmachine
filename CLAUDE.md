# CLAUDE.md - LaederData Lead Machine

> **Purpose**: This file provides context for AI coding assistants (Claude, Copilot, Cursor, etc.) working on this project. Read this first.

## Project Overview

**LaederData Lead Machine** is a real estate lead generation platform for South Central Pennsylvania. It scrapes county deed records, filters for high-value investment opportunities, and delivers leads via Telegram and Google Sheets.

### Architecture Summary

```
┌─────────────────────┐     webhook      ┌─────────────────────┐
│  HOME UBUNTU        │ ──────────────▶  │  HOSTINGER VPS      │
│  (Residential IP)   │                  │  (n8n + PostgreSQL) │
│                     │                  │                     │
│  - Python scrapers  │                  │  - Lead processing  │
│  - Cron jobs        │                  │  - Enrichment       │
│  - Raw data fetch   │                  │  - Telegram alerts  │
└─────────────────────┘                  │  - Google Sheets    │
                                         └─────────────────────┘
```

**Why this architecture?** Government deed recorder sites block datacenter IPs. The home server's residential IP can access these sites; the VPS handles all business logic.

### Business Context

- **Brand**: LaederData.com
- **Target Market**: Real estate investors in Dauphin, Cumberland, York, Lancaster counties (PA)
- **USP**: "Engineer-Built" - owner is a Licensed P.E., emphasizing precision and reliability
- **Monetization**: Subscription model via Stripe (future)

---

## Repository Structure

```
laederdata-leadmachine/
├── CLAUDE.md              # THIS FILE - root context for AI assistants
├── PLAN.md                # Implementation roadmap and status
├── README.md              # Human-readable project overview
├── docs/                  # Additional documentation
│   └── architecture.md    # Detailed architecture decisions
├── home-scraper/          # Code deployed to HOME UBUNTU SERVER
│   ├── CLAUDE.md          # Context for working on scrapers
│   ├── PLAN.md            # Scraper-specific tasks
│   ├── config/
│   │   └── settings.py
│   ├── scrapers/
│   │   └── dauphin_deeds.py
│   └── logs/              # Local logs (gitignored)
└── vps-n8n/               # Config deployed to HOSTINGER VPS
    ├── CLAUDE.md          # Context for working on VPS/n8n
    ├── PLAN.md            # VPS-specific tasks
    ├── docker/
    │   ├── docker-compose.yml
    │   ├── Dockerfile.runner
    │   ├── n8n-task-runners.json
    │   └── .env.example
    ├── workflows/         # n8n workflow JSON exports
    └── backups/           # Database/config backups
```

---

## Key Technical Decisions

### 1. n8n v2 Task Runner Bug Workaround
n8n v2.x external task runners ignore environment variables for Python allowlists (`N8N_RUNNERS_STDLIB_ALLOW`, `N8N_RUNNERS_EXTERNAL_ALLOW`). 

**Solution**: Override via config file at `/etc/n8n-task-runners.json` baked into the Docker image. See `vps-n8n/docker/n8n-task-runners.json`.

### 2. Reserved Keys in n8n v2 Python Nodes
Python Code nodes cannot return items with `error` as a key.

**Solution**: Use `error_message` or `status: "error"` instead.

### 3. Package Installation in Runner
The n8n runner image uses `uv` (not pip) for Python package management.

**Solution**: `uv pip install --python .venv/bin/python <packages>`

---

## Environment-Specific Details

### MacBook Pro (Development)
- Full repo clone
- Used for development, testing, documentation
- No production code runs here

### Home Ubuntu Server (Scraper Host)
- Deploy from: `home-scraper/`
- Location: `~/laederdata-scrapers/`
- Runs: Cron jobs → Python scrapers → webhook POST to VPS
- See: `home-scraper/CLAUDE.md`

### Hostinger VPS (n8n Host)
- Deploy from: `vps-n8n/`
- Location: `~/n8n-docker/`
- Runs: n8n, PostgreSQL, Task Runner (Docker Compose)
- See: `vps-n8n/CLAUDE.md`

---

## Credentials & Secrets

**NEVER commit secrets to this repo.**

| Secret | Location | Purpose |
|--------|----------|---------|
| `POSTGRES_PASSWORD` | VPS `~/n8n-docker/.env` | Database auth |
| `N8N_ENCRYPTION_KEY` | VPS `~/n8n-docker/.env` | n8n credential encryption |
| `RUNNER_AUTH_TOKEN` | VPS `~/n8n-docker/.env` | Task runner auth |
| `WEBHOOK_SECRET` | Both servers | Scraper → n8n auth |
| Google Sheets creds | n8n UI | Sheets API access |
| Telegram bot token | n8n UI | Alert delivery |

---

## Common Tasks

### Adding a New County Scraper
1. Create `home-scraper/scrapers/{county}_deeds.py` based on `dauphin_deeds.py`
2. Add county config to `home-scraper/config/settings.py`
3. Add cron job on home server
4. Test webhook delivery to VPS

### Updating n8n Workflows
1. Make changes in n8n UI
2. Export workflow JSON
3. Save to `vps-n8n/workflows/`
4. Commit to repo for backup

### Rebuilding VPS Docker Stack
```bash
cd ~/n8n-docker
docker compose down
docker compose up -d --build
```

---

## Current Status

See `PLAN.md` for detailed implementation status and next steps.

**Quick Status**: 
- [x] VPS n8n running with Python task runner
- [x] Python allowlist bug workaround in place
- [ ] Webhook receiver workflow (Phase 1)
- [ ] Home scraper deployment (Phase 2)
- [ ] End-to-end testing (Phase 3)
- [ ] Production hardening (Phase 4)
