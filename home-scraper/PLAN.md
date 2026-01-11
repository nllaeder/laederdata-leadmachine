# PLAN.md - Home Scraper Tasks

> **Last Updated**: January 11, 2026

## Current Status: Development Complete, Ready for Deployment

Scraper code developed and tested successfully. Waiting for VPS webhook receiver (Phase 1) to be complete before deploying to home server.

---

## Deployment Checklist

### Initial Setup
- [ ] Create directory structure: `mkdir -p ~/laederdata-scrapers/{scrapers,config,logs}`
- [ ] Create Python venv: `python3 -m venv ~/laederdata-scrapers/venv`
- [ ] Install dependencies: `source venv/bin/activate && pip install requests`

### Configuration
- [ ] Copy `config/settings.py` from repo
- [ ] Update `WEBHOOK_URL` with VPS address
- [ ] Update `WEBHOOK_SECRET` (get from VPS `.env`)

### Scrapers
- [ ] Copy `scrapers/dauphin_deeds.py` from repo
- [ ] Test manually: `python scrapers/dauphin_deeds.py`
- [ ] Verify webhook delivery successful

### Cron Jobs
- [ ] Add Dauphin scraper to crontab (7:30 AM daily)
- [ ] Verify cron executes next morning
- [ ] Check logs for successful run

---

## Scraper Status

| County | Scraper File | Cron Time | Status |
|--------|--------------|-----------|--------|
| Dauphin | `dauphin_deeds.py` | 7:30 AM | ✅ Tested, ready to deploy |
| Cumberland | `cumberland_deeds.py` | 7:35 AM | ⏳ Not started |
| York | `york_deeds.py` | 7:40 AM | ⏳ Not started |
| Lancaster | `lancaster_deeds.py` | 7:45 AM | ⏳ Not started |

---

## Dauphin County Scraper Details

### Target Site
- URL: `https://deeds.dauphincounty.gov/AcclaimWeb`
- API: POST to `/Search/SearchTypeComments` then `/Search/GetSearchResults`

### Document Types
| Code | Type |
|------|------|
| 105 | DEED |
| 108 | DEEDS IN HARRISBURG |
| 226 | R/R CRCTD DEED |
| 227 | R/R DEED |

### City Filter
- Default: "Harrisburg City"
- Can be expanded to other municipalities

### Output Fields
- ParcelNumber
- DirectName (buyer/grantee)
- IndirectName (seller/grantor)
- Consideration (sale price)
- RecordDate
- DocType
- InstrumentNumber
- Book/Page (if available)

---

## Future County Research

### Cumberland County
- [ ] Identify deed search URL
- [ ] Map API endpoints
- [ ] Document form fields
- [ ] List doc type codes

### York County
- [ ] Identify deed search URL
- [ ] Map API endpoints
- [ ] Document form fields
- [ ] List doc type codes

### Lancaster County
- [ ] Identify deed search URL
- [ ] Map API endpoints
- [ ] Document form fields
- [ ] List doc type codes

---

## Maintenance Tasks

### Weekly
- [ ] Check logs for errors
- [ ] Verify cron jobs executed
- [ ] Spot-check data quality

### Monthly
- [ ] Rotate logs (or set up logrotate)
- [ ] Update Python packages if needed
- [ ] Verify county sites haven't changed

### As Needed
- [ ] Update scrapers if county site changes
- [ ] Add new doc types if discovered
- [ ] Expand city filters

---

## Known Issues

| Issue | Workaround | Permanent Fix |
|-------|------------|---------------|
| Weekend/holiday gaps | Expected - no recordings | N/A |
| County site maintenance | Retry next day | Add retry logic |
| Power outage at home | Data gap | UPS + VPS alerting |

---

## Session Notes

### January 1, 2026
- Created initial scraper code structure
- Documented in repo structure
- Waiting for VPS webhook to be ready

### January 11, 2026
- **Scraper Development Complete**: Built and tested Dauphin County deed scraper
- Successfully tested with date 01/05/2026 - retrieved 5 deed records
- Verified scraper functionality:
  - Date parameter handling (defaults to yesterday, accepts manual date)
  - County API integration working
  - Data extraction and parsing successful
  - DRY_RUN mode tested (prevents accidental webhook calls during dev)
  - Logging system operational
- Scraper ready for deployment to home server once VPS webhook receiver is ready

### Next Session
- Build VPS webhook receiver workflow (Phase 1.2)
- Deploy scraper to home server after webhook is ready (Phase 2)
- Test end-to-end flow
- Set up cron job
