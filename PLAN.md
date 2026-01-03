# PLAN.md - Implementation Roadmap

> **Last Updated**: January 3, 2026

## Current Phase: Phase 1 - VPS Webhook Receiver

---

## Phase Overview

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | VPS n8n Setup | ✅ Complete |
| **Phase 1** | VPS Webhook Receiver | 🔄 In Progress |
| **Phase 2** | Home Scraper Deployment | ⏳ Pending |
| **Phase 3** | Testing & Validation | ⏳ Pending |
| **Phase 4** | Production Hardening | ⏳ Pending |

---

## Phase 0: VPS n8n Setup ✅

### Completed Tasks
- [x] n8n v2.1.4 deployed via Docker Compose
- [x] PostgreSQL 16 backend configured
- [x] External Python Task Runner working
- [x] Python packages installed (requests, beautifulsoup4, pandas, numpy, etc.)
- [x] Allowlist bug workaround implemented via config file
- [x] Verified Python Code node execution

### Technical Notes
- Task runner config: `~/n8n-docker/n8n-task-runners.json`
- Uses `uv` for package management in runner container
- Broker listens on `0.0.0.0:5679` for container networking

---

## Phase 1: VPS Webhook Receiver 🔄

### Goal
Create n8n workflow that receives scraped deed data via webhook and processes it through the lead pipeline.

### Tasks

#### 1.1 Generate Webhook Secret ✅
```bash
# On VPS
echo "WEBHOOK_SECRET=$(openssl rand -hex 32)" >> ~/n8n-docker/.env
source ~/n8n-docker/.env
echo $WEBHOOK_SECRET  # Save this for home server
```
- [x] Secret generated
- [x] Secret saved securely

**Generated Secret**: `62c697bfa327c42627309045f97c3d0ac1387b6df3e3c6af2227d0815cb11858`
(Store this in home scraper config during Phase 2.2)

#### 1.2 Create "Lead Ingest Pipeline" Workflow
- [ ] Webhook Trigger node (POST /ingest/deeds)
- [ ] Validate Secret (JavaScript Code node)
- [ ] IF: Has Records check
- [ ] Split Out Records
- [ ] IF: Consideration Filter ($1 < price < $200k)
- [ ] IF: Buyer is LLC-ish
- [ ] HTTP Request: DevNet Enrichment
- [ ] Parse DevNet HTML (JavaScript Code node)
- [ ] Google Sheets: Append Row
- [ ] Build Telegram Summary
- [ ] Telegram: Send Alert
- [ ] Response node (acknowledge webhook)

#### 1.3 Test Webhook
```bash
# Test command
curl -X POST http://localhost:5678/webhook/ingest/deeds \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: YOUR_SECRET" \
  -d '{"status":"success","county":"dauphin","records":[{"ParcelNumber":"10-001-001","DirectName":"TEST LLC","Consideration":150000}]}'
```
- [ ] Webhook responds 200
- [ ] Validation rejects bad secret
- [ ] Records flow through pipeline

#### 1.4 Export & Backup Workflow
- [ ] Export workflow JSON from n8n
- [ ] Save to `vps-n8n/workflows/lead-ingest-pipeline.json`
- [ ] Commit to repo

---

## Phase 2: Home Scraper Deployment ⏳

### Goal
Deploy Python scrapers on home Ubuntu server with cron scheduling.

### Tasks

#### 2.1 Directory Setup
```bash
# On home Ubuntu
mkdir -p ~/laederdata-scrapers/{scrapers,config,logs}
```
- [ ] Directory structure created

#### 2.2 Deploy Configuration
- [ ] Copy `home-scraper/config/settings.py`
- [ ] Update `WEBHOOK_URL` with VPS IP/domain
- [ ] Update `WEBHOOK_SECRET` from Phase 1.1

#### 2.3 Deploy Scraper
- [ ] Copy `home-scraper/scrapers/dauphin_deeds.py`
- [ ] Create Python venv: `python3 -m venv venv`
- [ ] Install deps: `pip install requests`

#### 2.4 Configure Cron
```bash
# Add to crontab
30 7 * * * cd ~/laederdata-scrapers && ./venv/bin/python scrapers/dauphin_deeds.py >> logs/cron.log 2>&1
```
- [ ] Cron job added
- [ ] Verified cron is running (`crontab -l`)

---

## Phase 3: Testing & Validation ⏳

### Goal
Verify end-to-end data flow from scraper to alerts.

### Tasks

#### 3.1 Local Scraper Test (Home)
```bash
cd ~/laederdata-scrapers
source venv/bin/activate
python scrapers/dauphin_deeds.py
```
- [ ] Scraper runs without error
- [ ] Logs show records found
- [ ] Webhook delivery successful

#### 3.2 Webhook Processing Test (VPS)
- [ ] n8n execution shows in logs
- [ ] Records flow through filters
- [ ] DevNet enrichment works (VPS can reach devnetwedge.com)

#### 3.3 Output Verification
- [ ] Telegram alert received
- [ ] Google Sheet updated with lead data
- [ ] Data matches expected format

#### 3.4 Error Handling Test
- [ ] Test with no records (holiday/weekend)
- [ ] Test with network timeout
- [ ] Test with invalid webhook secret

---

## Phase 4: Production Hardening ⏳

### Goal
Make the system reliable and ready for customers.

### Tasks

#### 4.1 SSL/Domain Setup
- [ ] Point `n8n.laederdata.com` to VPS IP
- [ ] Install nginx reverse proxy
- [ ] Configure Let's Encrypt SSL
- [ ] Update webhook URL in home scraper

#### 4.2 Monitoring
- [ ] Daily health check workflow (ping home server)
- [ ] Alert if no data received by 9 AM
- [ ] Log rotation on home server

#### 4.3 Reliability
- [ ] Home server: UPS for power protection
- [ ] VPS: Automated backups of PostgreSQL
- [ ] Retry logic for failed webhook deliveries

#### 4.4 Multi-County Expansion
- [ ] Cumberland County scraper
- [ ] York County scraper
- [ ] Lancaster County scraper

---

## Future Enhancements

### Customer Management
- [ ] Stripe integration for subscriptions
- [ ] PostgreSQL user table
- [ ] n8n webhooks for payment events
- [ ] Per-user lead filtering

### Landing Page
- [ ] LaederData.com intake funnel
- [ ] Multi-step qualification form
- [ ] Example leads delivery

### Advanced Filtering
- [ ] Equity analysis integration
- [ ] Property condition indicators
- [ ] Owner occupancy detection

---

## Blockers & Issues

| Issue | Status | Resolution |
|-------|--------|------------|
| County site blocks VPS IP | ✅ Resolved | Hybrid architecture - scrape from home |
| n8n Python allowlist bug | ✅ Resolved | Config file workaround |
| Reserved `error` key | ✅ Resolved | Use `error_message` instead |

---

## Session Notes

### January 1, 2026
- Deployed n8n v2.1.4 with Docker Compose on Hostinger VPS
- Discovered and resolved Python task runner allowlist bug
- Discovered county site blocks datacenter IPs
- Designed hybrid architecture (home scraper → VPS processing)
- Created implementation documentation

### January 3, 2026
- **Phase 1.1 Complete**: Generated webhook secret and stored in VPS .env file
- Secret: `62c697bfa327c42627309045f97c3d0ac1387b6df3e3c6af2227d0815cb11858`
- Ready for Phase 1.2: Building Lead Ingest Pipeline workflow in n8n UI

### Next Session
- Build Phase 1.2: Create webhook receiver workflow in n8n UI (manual in browser)
- Build workflow nodes: webhook → validation → filtering → enrichment → alerts
- Export workflow JSON for backup
