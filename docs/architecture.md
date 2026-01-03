# Architecture Documentation

## System Overview

LaederData Lead Machine is a distributed system for real estate lead generation. It scrapes county deed records, filters for investment opportunities, and delivers leads to subscribers.

## Why Hybrid Architecture?

### The Problem
Government deed recorder websites (county clerk offices) actively block datacenter IP addresses to prevent automated scraping. This is a common practice for public records sites.

When we attempted to scrape from the Hostinger VPS:
```
curl: (28) Failed to connect to deeds.dauphincounty.gov port 443: Timeout
```

But the same request from a residential IP works fine.

### The Solution
Split responsibilities between two servers:

| Server | IP Type | Responsibility |
|--------|---------|----------------|
| Home Ubuntu | Residential | Scrape raw data from county sites |
| Hostinger VPS | Datacenter | Process data, run workflows, deliver leads |

This gives us the best of both worlds:
- Residential IP for accessing blocked sites
- VPS reliability for 24/7 business logic and alerting

## Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         HOME UBUNTU SERVER                                │
│                         (Residential IP)                                  │
│                                                                          │
│   ┌─────────┐     ┌─────────────────────────────────────────────────┐   │
│   │  Cron   │────▶│              Python Scraper                      │   │
│   │ 7:30 AM │     │                                                  │   │
│   └─────────┘     │  1. Connect to county deed recorder site         │   │
│                   │  2. POST search query (date, doc types, city)    │   │
│                   │  3. Fetch JSON results                           │   │
│                   │  4. Package as webhook payload                   │   │
│                   └──────────────────┬──────────────────────────────┘   │
│                                      │                                   │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       │ HTTPS POST
                                       │ X-Webhook-Secret: <shared secret>
                                       │ Content-Type: application/json
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         HOSTINGER VPS                                     │
│                         (Datacenter IP)                                   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    n8n Workflow Engine                           │   │
│   │                                                                  │   │
│   │   Webhook ──▶ Validate ──▶ Filter ──▶ Enrich ──▶ Deliver       │   │
│   │   Trigger     Secret       Leads      DevNet     Alerts         │   │
│   │                                                                  │   │
│   │   Filters:                        Enrichment:                   │   │
│   │   • $1 < Consideration < $200k    • Owner name/address          │   │
│   │   • Buyer contains LLC/LP/etc     • Mailing address             │   │
│   │                                   • Sales history               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                           │                      │                       │
│                           ▼                      ▼                       │
│                    ┌─────────────┐        ┌─────────────┐               │
│                    │  Telegram   │        │   Google    │               │
│                    │   Alert     │        │   Sheets    │               │
│                    └─────────────┘        └─────────────┘               │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Docker Compose Stack                                            │   │
│   │  • PostgreSQL 16 (n8n backend)                                  │   │
│   │  • n8n v2.1.4 (workflow engine)                                 │   │
│   │  • Task Runner (Python/JS execution)                            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Home Scraper

**Language**: Python 3
**Dependencies**: `requests` only
**Scheduling**: System cron

The scraper is intentionally minimal:
- Single responsibility: fetch raw data
- No business logic (filtering happens on VPS)
- Sends all results to webhook, including errors
- Runs once daily per county

### VPS n8n Stack

**n8n v2.1.4**: Workflow automation platform
- Handles all business logic
- Manages credentials securely
- Provides web UI for workflow editing

**PostgreSQL 16**: Database
- n8n workflow storage
- Execution history
- Future: user management for subscriptions

**Task Runner**: Code execution
- Isolated Python/JavaScript execution
- Custom image with data processing packages
- Workaround for allowlist bug in n8n v2.x

### External Services

**Google Sheets**: Lead storage
- Simple, accessible format
- Easy for end users to integrate with CRMs
- Append-only pattern

**Telegram**: Real-time alerts
- Instant notification of new leads
- Daily summary messages
- Error alerting

**DevNet Wedge**: Property enrichment
- County GIS/tax assessment data
- Owner information
- Sales history
- Note: This site DOES work from VPS (different from deed recorder)

## Security Model

### Webhook Authentication
```
Home Server                              VPS
    │                                     │
    │ POST /webhook/ingest/deeds          │
    │ X-Webhook-Secret: <sha256-token>    │
    │────────────────────────────────────▶│
    │                                     │
    │                      Validate token │
    │                      against env var│
    │                                     │
    │◀────────────────────────────────────│
    │            200 OK or 401 Rejected   │
```

### Credential Storage
- All API credentials stored in n8n (encrypted with N8N_ENCRYPTION_KEY)
- Webhook secret in environment variables on both servers
- Database password only on VPS

### Network Exposure
- VPS port 5678 open (n8n web UI + webhooks)
- Home server: no inbound connections required
- All communication initiated by home server

## Failure Modes

| Failure | Impact | Detection | Recovery |
|---------|--------|-----------|----------|
| Home server down | No new scrapes | Missing daily data | Manual catch-up scrape |
| VPS down | No processing/alerts | Webhook failures in logs | Docker restart |
| County site changed | Parse errors | Error status in webhook | Update scraper |
| County blocks home IP | Connection timeout | Error logs | Very unlikely (residential) |

## Scaling Considerations

### Adding Counties
1. Research county site structure
2. Create new scraper script
3. Add to cron schedule
4. Update n8n workflow for county-specific logic

### Multiple Customers
Future architecture:
- PostgreSQL user table with subscription status
- Stripe webhooks for payment events
- Per-user lead filtering in n8n
- Separate Telegram channels or email delivery

### High Volume
Current architecture handles ~100s of leads/day easily.
For higher volume:
- Add Redis for caching
- Queue-based processing
- Dedicated worker nodes
