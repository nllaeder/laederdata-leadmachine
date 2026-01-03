# PLAN.md - VPS n8n Tasks

> **Last Updated**: January 1, 2026

## Current Status: Phase 1 - Build Webhook Receiver

Infrastructure is deployed and working. Now need to create the lead processing workflow.

---

## Infrastructure Status ✅

- [x] Docker Compose stack running
- [x] PostgreSQL 16 healthy
- [x] n8n v2.1.4 accessible on port 5678
- [x] Python Task Runner registered
- [x] JavaScript Task Runner registered
- [x] Python packages installed (requests, pandas, etc.)
- [x] Allowlist workaround in place

---

## Phase 1 Tasks: Webhook Receiver

### 1.1 Generate Webhook Secret
```bash
echo "WEBHOOK_SECRET=$(openssl rand -hex 32)" >> ~/n8n-docker/.env
source ~/n8n-docker/.env
echo $WEBHOOK_SECRET  # Copy for home server
```
- [ ] Secret generated and added to .env
- [ ] Secret documented securely (password manager)

### 1.2 Create Workflow: "Lead Ingest Pipeline"

Build in n8n UI with these nodes:

#### Input Stage
- [ ] **Webhook Trigger**
  - Method: POST
  - Path: `ingest/deeds`
  - Response Mode: Using 'Respond to Webhook' node

- [ ] **Validate Secret** (Code - JavaScript)
  ```javascript
  const expected = $env.WEBHOOK_SECRET;
  const received = $json.headers?.['x-webhook-secret'];
  
  if (received !== expected) {
    throw new Error('Unauthorized');
  }
  
  return { json: $json.body };
  ```

- [ ] **IF: Status is Success**
  - Condition: `$json.status` equals `success`
  - True → continue
  - False → log error and respond

- [ ] **IF: Has Records**
  - Condition: `$json.record_count` > 0
  - True → continue
  - False → respond "no records"

#### Processing Stage
- [ ] **Split Out Records**
  - Field to split: `records`

- [ ] **IF: Consideration Filter**
  - Conditions (AND):
    - `$json.Consideration` > 1
    - `$json.Consideration` < 200000

- [ ] **IF: Buyer is LLC-ish**
  - Conditions (OR):
    - `$json.DirectName` contains "LLC"
    - `$json.DirectName` contains "LP"
    - `$json.DirectName` contains "HOLDINGS"
    - `$json.DirectName` contains "PROPERTIES"

#### Enrichment Stage
- [ ] **HTTP Request: DevNet**
  - URL: `https://dauphinpa.devnetwedge.com/parcel/view/{{ $json.ParcelNumber.replace(/-/g, '') }}/2025`
  - Response Format: Text
  - Output Property: `devnetHtml`

- [ ] **Parse DevNet HTML** (Code - JavaScript)
  - Extract: owner name, owner address, mailing address
  - Parse sales history table
  - (Use existing parser from Harrisburg Daily Deeds workflow)

#### Output Stage
- [ ] **Google Sheets: Append Row**
  - Document: n8n-HBGdeedScraperResults
  - Sheet: HBGDeedsToLeads
  - Map fields to columns

- [ ] **Build Telegram Summary** (Code - JavaScript)
  ```javascript
  const count = items.length;
  const first = items[0]?.json;
  return [{
    json: {
      count,
      message: `Harrisburg Daily Deeds: ${count} new leads`,
      recordDate: first?.RecordDate || 'unknown'
    }
  }];
  ```

- [ ] **Telegram: Send Message**
  - Chat ID: `-5105113228`
  - Text: `🏠 [Deeds] {{ $json.message }}`

- [ ] **Respond to Webhook**
  - Status: 200
  - Body: `{ "received": true, "count": {{ $json.record_count }} }`

### 1.3 Test Webhook

```bash
# Test with sample data
curl -X POST http://localhost:5678/webhook/ingest/deeds \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: YOUR_SECRET" \
  -d '{
    "status": "success",
    "county": "dauphin",
    "date_searched": "12/31/2025",
    "record_count": 1,
    "records": [{
      "ParcelNumber": "10-001-001",
      "DirectName": "TEST LLC",
      "IndirectName": "SELLER NAME",
      "Consideration": 150000,
      "RecordDate": "12/31/2025"
    }]
  }'
```

- [ ] Webhook returns 200
- [ ] Invalid secret returns 401
- [ ] Empty records handled gracefully
- [ ] Error status logged appropriately

### 1.4 Backup Workflow

- [ ] Export workflow JSON from n8n
- [ ] Save to `vps-n8n/workflows/lead-ingest-pipeline.json`
- [ ] Commit to repo

---

## Future Tasks

### SSL/Domain Setup (Phase 4)
- [ ] Point `n8n.laederdata.com` → VPS IP
- [ ] Install nginx as reverse proxy
- [ ] Configure Let's Encrypt SSL
- [ ] Update docker-compose to expose only to localhost
- [ ] Update home scraper webhook URL

### Monitoring
- [ ] Create "Health Check" workflow
  - Runs daily at 9 AM
  - Alerts if no data received today
- [ ] Set up log aggregation
- [ ] Configure backup automation

### Multi-County Support
- [ ] Update IF nodes to handle multiple counties
- [ ] Per-county DevNet URLs (or similar)
- [ ] County-specific Google Sheets tabs

### User Management (Future)
- [ ] PostgreSQL user table schema
- [ ] Stripe webhook integration
- [ ] Per-user lead filtering
- [ ] Access control workflow

---

## Credential Status

| Credential | Status | Notes |
|------------|--------|-------|
| Google Sheets account | ✅ Exists | From previous workflows |
| LaederAlertsBot_creds | ✅ Exists | Telegram bot token |
| WEBHOOK_SECRET | ⏳ Needs creation | For scraper auth |

---

## Docker Config Sync

Keep repo in sync with deployed config:

| File | Repo Location | VPS Location |
|------|---------------|--------------|
| docker-compose.yml | `vps-n8n/docker/` | `~/n8n-docker/` |
| Dockerfile.runner | `vps-n8n/docker/` | `~/n8n-docker/` |
| n8n-task-runners.json | `vps-n8n/docker/` | `~/n8n-docker/` |
| .env.example | `vps-n8n/docker/` | N/A (template only) |

After VPS changes, copy back to repo:
```bash
# From repo root on MacBook
scp root@srv1238293:~/n8n-docker/docker-compose.yml vps-n8n/docker/
```

---

## Session Notes

### January 1, 2026
- Deployed n8n v2.1.4 stack
- Resolved Python task runner issues
- Confirmed Python Code node works
- Documented config files in repo

### Next Session
- Generate webhook secret (1.1)
- Build webhook receiver workflow in UI (1.2)
- Test with curl (1.3)
- Export and backup (1.4)
