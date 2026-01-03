#!/usr/bin/env python3
"""
Dauphin County Deed Scraper

Scrapes deed records from Dauphin County recorder and sends to VPS webhook.

Usage:
    python dauphin_deeds.py                    # Scrape yesterday's deeds
    python dauphin_deeds.py --date 12/31/2025  # Scrape specific date
    python dauphin_deeds.py --dry-run          # Scrape but don't send to webhook

Cron example (7:30 AM daily):
    30 7 * * * cd ~/laederdata-scrapers && ./venv/bin/python scrapers/dauphin_deeds.py >> logs/cron.log 2>&1
"""

import argparse
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    WEBHOOK_URL,
    WEBHOOK_SECRET,
    COUNTIES,
    REQUEST_TIMEOUT,
    LOG_DIR,
)

# =============================================================================
# Logging Setup
# =============================================================================

logger = logging.getLogger("dauphin_scraper")
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(LOG_DIR / "dauphin.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)


# =============================================================================
# Scraper Functions
# =============================================================================


def scrape_deeds(target_date: date = None) -> dict:
    """
    Scrape Dauphin County deed records for a given date.

    Args:
        target_date: Date to scrape. Defaults to yesterday.

    Returns:
        dict with status, records, and metadata
    """
    county = COUNTIES["dauphin"]

    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    d_str = target_date.strftime("%m/%d/%Y")
    logger.info(f"Scraping {county['name']} deeds for {d_str}")

    # Set up session with browser-like headers
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )

    # Build search payload
    history_dict = {
        "FromDatePicker": {"BE": d_str, "UI": d_str},
        "ToDatePicker": {"BE": d_str, "UI": d_str},
        "Comments": {"BE": county["city_filter"], "UI": county["city_filter"]},
        "DocTypesList": {
            "BE": ",".join(county["doc_types"]),
            "UI": county["doc_types_display"],
        },
    }

    payload = {
        "HistoryObject": json.dumps(history_dict),
        "Comments": county["city_filter"],
        "DateRange": "SpecificDateRange",
        "DateFrom": d_str,
        "DateTo": d_str,
        "DocTypesGroupList": f"{county['doc_types_display']}|{','.join(county['doc_types'])}",
        "DocTypesList": county["doc_types"],
        "ctl00$ContentPlaceHolder1$btnSearch": "Search",
    }

    try:
        # Step 1: Prime the session with the search
        search_url = county["base_url"] + county["search_url"]
        logger.debug(f"Priming session at {search_url}")
        session.post(search_url, data=payload, timeout=REQUEST_TIMEOUT)

        # Step 2: Fetch the grid data
        data_url = county["base_url"] + county["data_url"]
        grid_params = {
            "page": 1,
            "pageSize": 500,
            "group": "",
            "filter": "",
        }

        logger.debug(f"Fetching data from {data_url}")
        resp = session.post(data_url, data=grid_params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        json_data = resp.json()
        records = json_data.get("Data", [])

        logger.info(f"Found {len(records)} records")

        return {
            "status": "success",
            "county": "dauphin",
            "date_searched": d_str,
            "record_count": len(records),
            "records": records,
        }

    except requests.exceptions.Timeout:
        error_msg = f"Timeout connecting to {county['base_url']}"
        logger.error(error_msg)
        return {
            "status": "error",
            "county": "dauphin",
            "date_searched": d_str,
            "error_type": "timeout",
            "error_message": error_msg,
        }

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "county": "dauphin",
            "date_searched": d_str,
            "error_type": "connection_error",
            "error_message": str(e),
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "county": "dauphin",
            "date_searched": d_str,
            "error_type": "request_error",
            "error_message": str(e),
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse response as JSON: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "county": "dauphin",
            "date_searched": d_str,
            "error_type": "parse_error",
            "error_message": str(e),
        }

    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "county": "dauphin",
            "date_searched": d_str,
            "error_type": "unknown",
            "error_message": str(e),
        }


def send_to_webhook(data: dict) -> bool:
    """
    Send scraped data to VPS webhook.

    Args:
        data: Scraper result dict

    Returns:
        True if successful, False otherwise
    """
    record_count = data.get("record_count", 0)
    logger.info(f"Sending {record_count} records to webhook: {WEBHOOK_URL}")

    try:
        resp = requests.post(
            WEBHOOK_URL,
            json=data,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Secret": WEBHOOK_SECRET,
            },
            timeout=30,
        )
        resp.raise_for_status()

        logger.info(f"Webhook response: {resp.status_code}")
        return True

    except requests.exceptions.Timeout:
        logger.error("Webhook request timed out")
        return False

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to webhook: {e}")
        return False

    except requests.exceptions.HTTPError as e:
        logger.error(f"Webhook returned error: {e.response.status_code} - {e.response.text}")
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send to webhook: {e}")
        return False


# =============================================================================
# Main Entry Point
# =============================================================================


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape Dauphin County deed records"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to scrape (MM/DD/YYYY format). Defaults to yesterday.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape but don't send to webhook. Print results instead.",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    logger.info("=" * 60)
    logger.info("Starting Dauphin County deed scraper")

    # Parse target date if provided
    target_date = None
    if args.date:
        try:
            from datetime import datetime
            target_date = datetime.strptime(args.date, "%m/%d/%Y").date()
            logger.info(f"Using specified date: {target_date}")
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use MM/DD/YYYY.")
            sys.exit(1)

    # Scrape deeds
    result = scrape_deeds(target_date)

    # Handle dry run
    if args.dry_run:
        logger.info("DRY RUN - Not sending to webhook")
        print(json.dumps(result, indent=2))
        logger.info("=" * 60)
        return

    # Send to webhook (even on error - let VPS handle it)
    success = send_to_webhook(result)

    if success:
        logger.info("Scraper completed successfully")
    else:
        logger.error("Failed to deliver results to webhook")
        sys.exit(1)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
