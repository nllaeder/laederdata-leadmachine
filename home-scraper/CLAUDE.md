# CLAUDE.md - Home Scraper

> **Purpose**: Context for AI coding assistants working on the Python scrapers that run on the home Ubuntu server.

## Deployment Target

- **Machine**: Home Ubuntu server (residential IP)
- **Location**: `~/laederdata-scrapers/`
- **Purpose**: Scrape county deed records and POST to VPS webhook

## Why This Runs at Home

Government deed recorder websites (like `deeds.dauphincounty.gov`) block datacenter IPs to prevent scraping. The home server's residential IP can access these sites. All business logic runs on the VPS; this server only fetches raw data.

---

## Directory Structure

```
~/laederdata-scrapers/
├── config/
│   └── settings.py       # Webhook URL, secrets, county configs
├── scrapers/
│   ├── dauphin_deeds.py  # Dauphin County scraper
│   ├── cumberland_deeds.py  # (future)
│   ├── york_deeds.py        # (future)
│   └── lancaster_deeds.py   # (future)
├── logs/
│   ├── dauphin.log       # Per-scraper logs
│   └── cron.log          # Cron execution log
└── venv/                 # Python virtual environment
```

---

## Key Files

### config/settings.py
Contains:
- `WEBHOOK_URL` - VPS endpoint (e.g., `http://VPS_IP:5678/webhook/ingest/deeds`)
- `WEBHOOK_SECRET` - Shared secret for authentication
- `COUNTIES` - Dict of county configurations (URLs, filters, doc types)

**NEVER commit real secrets.** Use `settings.py.example` as template.

### scrapers/dauphin_deeds.py
Main scraper for Dauphin County. Pattern for all county scrapers:

1. Build session with browser-like headers
2. POST to county search endpoint
3. Fetch JSON results
4. POST results to VPS webhook

---

## Scraper Output Format

All scrapers must return this structure to the webhook:

```python
{
    "status": "success",  # or "error"
    "county": "dauphin",
    "date_searched": "12/31/2025",
    "record_count": 15,
    "records": [
        {
            "ParcelNumber": "10-001-001",
            "DirectName": "BUYER LLC",      # Grantee
            "IndirectName": "SELLER NAME",  # Grantor
            "Consideration": 150000,
            "RecordDate": "12/31/2025",
            "DocType": "DEED",
            # ... other county-specific fields
        }
    ]
}
```

On error:
```python
{
    "status": "error",
    "county": "dauphin",
    "date_searched": "12/31/2025",
    "error_type": "timeout",  # or "request_error", "parse_error", "unknown"
    "error_message": "Connection timed out"
}
```

**Important**: Do NOT use `error` as a key - n8n v2 reserves it.

---

## Adding a New County Scraper

1. **Research the county site**
   - Find the deed search URL
   - Identify the API endpoints (often XHR requests)
   - Note required form fields and doc type codes

2. **Create the scraper**
   ```bash
   cp scrapers/dauphin_deeds.py scrapers/{county}_deeds.py
   ```

3. **Add county config** to `config/settings.py`:
   ```python
   COUNTIES = {
       # ...existing...
       "newcounty": {
           "name": "New County",
           "base_url": "https://deeds.newcounty.gov",
           "search_url": "/Search/...",
           "data_url": "/Search/GetResults",
           "city_filter": "Target City",
           "doc_types": ["101", "102"],
       },
   }
   ```

4. **Add cron job**:
   ```bash
   crontab -e
   # Add:
   35 7 * * * cd ~/laederdata-scrapers && ./venv/bin/python scrapers/newcounty_deeds.py >> logs/cron.log 2>&1
   ```

---

## Common Commands

```bash
# Activate virtual environment
cd ~/laederdata-scrapers
source venv/bin/activate

# Run scraper manually
python scrapers/dauphin_deeds.py

# Check logs
tail -f logs/dauphin.log
tail -f logs/cron.log

# View cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Test webhook connectivity (without scraping)
curl -X POST http://VPS_IP:5678/webhook/ingest/deeds \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: YOUR_SECRET" \
  -d '{"status":"success","county":"test","records":[]}'
```

---

## Troubleshooting

### Scraper times out
- Check if county site is up (visit in browser)
- County may have changed their site structure
- Try increasing `REQUEST_TIMEOUT` in settings.py

### Webhook delivery fails
- Check VPS is reachable: `curl http://VPS_IP:5678`
- Verify webhook secret matches VPS config
- Check VPS n8n logs: `docker compose logs n8n`

### No records returned
- Normal on weekends/holidays (no recordings)
- Check date logic (scrapes yesterday by default)
- Verify doc type codes haven't changed

### Cron not running
- Check cron daemon: `systemctl status cron`
- Check cron log: `grep CRON /var/log/syslog`
- Ensure script is executable

---

## Dependencies

```
requests>=2.28.0
```

Install:
```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

---

## Testing

### Local Test (no webhook)
Modify scraper to print instead of POST:
```python
result = scrape_deeds()
print(json.dumps(result, indent=2))
# Comment out: send_to_webhook(result)
```

### End-to-End Test
1. Ensure VPS n8n workflow is active
2. Run scraper: `python scrapers/dauphin_deeds.py`
3. Check:
   - Scraper log shows success
   - VPS n8n execution log shows webhook received
   - Telegram alert delivered (if records pass filters)

---

## Security Notes

- Webhook secret authenticates requests to VPS
- Never log the full webhook secret
- Settings.py should be gitignored (use .example template)
- Logs may contain property data - don't expose publicly
