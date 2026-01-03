# CLAUDE.md - VPS n8n

> **Purpose**: Context for AI coding assistants working on the n8n instance and Docker infrastructure on the Hostinger VPS.

## Deployment Target

- **Machine**: Hostinger VPS (`srv1238293`)
- **Location**: `~/n8n-docker/`
- **Purpose**: n8n orchestration, lead processing, alerting, data storage

## What Runs Here

- **n8n v2.1.4**: Workflow automation platform
- **PostgreSQL 16**: n8n backend + future user management
- **Task Runner**: External Python/JavaScript execution (sidecar container)

---

## Directory Structure on VPS

```
~/n8n-docker/
├── docker-compose.yml      # Main stack definition
├── Dockerfile.runner       # Custom runner with Python packages
├── n8n-task-runners.json   # Task runner config (allowlist workaround)
├── .env                    # Secrets (NEVER commit)
└── README.md               # Local deployment notes

# Docker volumes (managed by Docker)
# - postgres_data: PostgreSQL database
# - n8n_data: n8n workflows, credentials, settings
```

---

## Key Technical Details

### Docker Services

| Service | Image | Purpose |
|---------|-------|---------|
| `db` | `postgres:16-alpine` | n8n database backend |
| `n8n` | `n8nio/n8n:2.1.4` | Main n8n application |
| `n8n-runner` | Custom (Dockerfile.runner) | Python/JS task execution |

### Ports
- `5678`: n8n web UI and webhooks
- `5679`: Task broker (internal, container-to-container)

### Environment Variables (.env)
```
POSTGRES_PASSWORD=<database password>
N8N_ENCRYPTION_KEY=<n8n credential encryption>
RUNNER_AUTH_TOKEN=<task runner authentication>
WEBHOOK_SECRET=<scraper webhook authentication>
```

---

## Critical Bug Workarounds

### 1. Python Allowlist Bug (n8n v2.0-2.1.x)

**Problem**: External task runners ignore `N8N_RUNNERS_STDLIB_ALLOW` and `N8N_RUNNERS_EXTERNAL_ALLOW` environment variables.

**Solution**: Override via config file baked into Docker image.

File: `n8n-task-runners.json`
```json
{
  "task-runners": [
    {
      "runner-type": "python",
      "env-overrides": {
        "N8N_RUNNERS_STDLIB_ALLOW": "*",
        "N8N_RUNNERS_EXTERNAL_ALLOW": "*"
      }
    }
  ]
}
```

Dockerfile.runner copies this to `/etc/n8n-task-runners.json`.

### 2. Reserved `error` Key

**Problem**: Python Code nodes cannot return items with `error` as a key.

**Solution**: Use `error_message` or `status: "error"` instead.

### 3. Package Manager

**Problem**: Runner image uses `uv`, not `pip`.

**Solution**: Install packages with:
```dockerfile
RUN uv pip install --python .venv/bin/python <packages>
```

### 4. Broker Listen Address

**Problem**: Task broker defaults to `127.0.0.1`, unreachable from runner container.

**Solution**: Set `N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0` in n8n environment.

---

## Common Commands

```bash
# SSH to VPS
ssh root@srv1238293

# Navigate to n8n directory
cd ~/n8n-docker

# Start/restart stack
docker compose up -d

# Rebuild after config changes
docker compose down
docker compose up -d --build

# View logs
docker compose logs -f n8n
docker compose logs -f n8n-runner
docker compose logs -f db

# Check runner registration
docker compose logs n8n | grep -i "registered runner"

# Execute command in container
docker compose exec n8n sh
docker compose exec db psql -U n8n_user -d n8n

# Backup database
docker compose exec db pg_dump -U n8n_user n8n > backup.sql
```

---

## n8n Workflows

### Lead Ingest Pipeline
- **Trigger**: Webhook POST `/ingest/deeds`
- **Function**: Receives scraped data from home server, processes through filters, enriches with DevNet data, delivers to Telegram and Sheets

### Workflow Backup
Export workflows from n8n UI → Save to `vps-n8n/workflows/` in repo.

---

## Credential Management

Credentials are stored encrypted in n8n's database. Current credentials:

| Name | Type | Purpose |
|------|------|---------|
| Google Sheets account | Service Account | Append leads to sheet |
| LaederAlertsBot_creds | Telegram API | Send alert messages |

To add/edit: n8n UI → Credentials

---

## Network Considerations

### What WORKS from VPS
- `dauphinpa.devnetwedge.com` - DevNet GIS enrichment ✅
- Google APIs ✅
- Telegram API ✅

### What DOESN'T work from VPS
- `deeds.dauphincounty.gov` - Blocks datacenter IPs ❌
- Other county deed recorder sites - Likely blocked ❌

This is why scrapers run on home server with residential IP.

---

## Webhook Security

The webhook endpoint validates requests using a shared secret:

```javascript
// In n8n Code node
const expectedSecret = $env.WEBHOOK_SECRET;
const receivedSecret = $input.first().json.headers['x-webhook-secret'];

if (receivedSecret !== expectedSecret) {
  throw new Error('Invalid webhook secret');
}
```

---

## Updating n8n Version

1. Update image tag in `docker-compose.yml`
2. Update runner image tag in `Dockerfile.runner` (must match)
3. Check n8n release notes for breaking changes
4. Backup database first
5. `docker compose down && docker compose up -d --build`

---

## Troubleshooting

### Task runner not registering
```bash
# Check broker is listening
docker compose logs n8n | grep -i "broker"

# Should see: "Task Broker ready on 0.0.0.0, port 5679"

# Check runner logs
docker compose logs n8n-runner
```

### Python imports failing
- Verify package installed: `docker compose exec n8n-runner pip list`
- Check allowlist in `n8n-task-runners.json`
- Rebuild runner: `docker compose up -d --build`

### Webhook not receiving
- Ensure workflow is **active** (not just saved)
- Check webhook path matches
- Test locally: `curl -X POST http://localhost:5678/webhook/...`

### Database connection issues
```bash
# Check db container health
docker compose ps

# Test connection
docker compose exec n8n sh -c 'nc -zv db 5432'
```

---

## Backup Strategy

### Database
```bash
# Manual backup
docker compose exec db pg_dump -U n8n_user n8n > ~/backups/n8n-$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker compose exec -T db psql -U n8n_user -d n8n
```

### Workflows
Export JSON from n8n UI, commit to `vps-n8n/workflows/`

### Docker configs
Already in repo under `vps-n8n/docker/`
