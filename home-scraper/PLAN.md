# PLAN.md - Home Scraper Tasks

> **Last Updated**: January 1, 2026

## Current Status: Not Yet Deployed

Waiting for VPS webhook receiver (Phase 1) to be complete before deploying scrapers.

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
| Dauphin | `dauphin_deeds.py` | 7:30 AM | 📝 Ready to deploy |
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
- Created scraper code (not yet deployed)
- Documented in repo structure
- Waiting for VPS webhook to be ready

### Next Session
- Deploy after Phase 1 (VPS webhook) complete
- Test end-to-end flow
- Set up cron job
