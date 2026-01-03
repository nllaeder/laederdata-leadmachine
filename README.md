# LaederData Lead Machine

Real estate lead generation platform for South Central Pennsylvania investors.

## What It Does

1. **Scrapes** county deed records daily (Dauphin, Cumberland, York, Lancaster)
2. **Filters** for high-value investment opportunities (LLC buyers, target price range)
3. **Enriches** with property data from county GIS systems
4. **Delivers** leads via Telegram alerts and Google Sheets

## Architecture

```
Home Server (scraper) ──webhook──▶ VPS (n8n processing) ──▶ Telegram + Sheets
```

See [docs/architecture.md](docs/architecture.md) for details.

## Quick Start

### For Developers

This repo is designed to work with AI coding assistants. Each deployment target has its own `CLAUDE.md` context file:

- **Root**: `CLAUDE.md` - Project overview
- **Home Scraper**: `home-scraper/CLAUDE.md` - Python scraper context
- **VPS n8n**: `vps-n8n/CLAUDE.md` - n8n/Docker context

### Deployment

**Home Ubuntu Server** (scraper):
```bash
cd home-scraper
# Follow home-scraper/CLAUDE.md
```

**Hostinger VPS** (n8n):
```bash
cd vps-n8n/docker
docker compose up -d --build
```

## Project Status

See [PLAN.md](PLAN.md) for current implementation status.

## License

Proprietary - LaederData.com
