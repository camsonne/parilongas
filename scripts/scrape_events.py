#!/usr/bin/env python3
"""
scrape_events.py — Daily event scraper for Parilongas

Reads data/sources.json, checks each source for updates,
and writes data/events.json with structured event data
for each day of the week.

Usage:
    python scripts/scrape_events.py

Environment variables:
    SOURCES_FILE  — path to sources.json (default: data/sources.json)
    OUTPUT_FILE   — path to events.json output (default: data/events.json)
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCES_FILE = os.environ.get("SOURCES_FILE", "data/sources.json")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "data/events.json")

HEADERS = {
    "User-Agent": "ParilongasBot/1.0 (+https://parilongas.fr)"
}

DAY_NAMES = {
    0: {"fr": "DIMANCHE", "en": "SUNDAY"},
    1: {"fr": "LUNDI", "en": "MONDAY"},
    2: {"fr": "MARDI", "en": "TUESDAY"},
    3: {"fr": "MERCREDI", "en": "WEDNESDAY"},
    4: {"fr": "JEUDI", "en": "THURSDAY"},
    5: {"fr": "VENDREDI", "en": "FRIDAY"},
    6: {"fr": "SAMEDI", "en": "SATURDAY"},
}


def load_sources():
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["sources"]


def scrape_website(source):
    """
    Attempt to scrape a website for event updates.
    Returns dict with any dynamic info found (dj, time, special notes).
    Falls back to source defaults if scraping fails.
    """
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        
        # --- Customise parsing per source ---
        # This is where you add source-specific scraping logic.
        # For now, return empty (use defaults).
        # 
        # Example pattern:
        # text = soup.get_text()
        # dj_match = re.search(r'DJ\s*[:\-]?\s*(.+)', text)
        # if dj_match:
        #     return {"dj": dj_match.group(1).strip()}
        
        return {}
        
    except Exception as e:
        print(f"  ⚠ Could not scrape {source['url']}: {e}", file=sys.stderr)
        return {}


def scrape_facebook(source):
    """
    Attempt to get event info from Facebook.
    Note: Facebook scraping is fragile. Consider using:
    - Facebook Graph API (requires app + token)
    - Apify Facebook scraper (paid)
    - Manual override in sources.json
    """
    # Placeholder — in production, implement Graph API call or Apify
    return {}


def build_event(source, dynamic_data):
    """Merge source defaults with any scraped dynamic data."""
    event = {
        "id": source["id"],
        "time": dynamic_data.get("time", source.get("default_time", "")),
        "name": source["name"],
        "address": source["address"],
        "map_url": f"https://www.google.com/maps/search/{source['address'].replace(' ', '+')}",
        "venue": source.get("venue", ""),
        "metro": source.get("metro", ""),
        "dj": dynamic_data.get("dj", source.get("default_dj", "nc")),
        "price": dynamic_data.get("price", source.get("default_price", "")),
        "links": {},
        "recurrence": source.get("recurrence", ""),
        "image": dynamic_data.get("image", ""),
    }
    
    # Build links from source URL
    if "facebook" in source.get("url", ""):
        event["links"]["Facebook"] = source["url"]
    elif source.get("url"):
        event["links"]["Site"] = source["url"]
    
    if source.get("email"):
        event["links"]["Email"] = f"mailto:{source['email']}"
    
    if source.get("phone"):
        event["phone"] = source["phone"]
    
    return event


def get_date_for_day(day_num):
    """Get the next occurrence date for a given day of the week (0=Sun...6=Sat)."""
    today = datetime.now()
    # Python weekday: 0=Mon...6=Sun. We use JS convention: 0=Sun...6=Sat
    # Convert: JS 0(Sun) = Python 6, JS 1(Mon) = Python 0, etc.
    py_day = (day_num - 1) % 7
    days_ahead = (py_day - today.weekday()) % 7
    target = today + timedelta(days=days_ahead)
    return target.strftime("%d/%m/%Y")


def main():
    print("🔄 Loading sources...")
    sources = load_sources()
    print(f"   Found {len(sources)} sources")
    
    # Initialize days structure
    days = {}
    for d in range(7):
        days[str(d)] = {
            "name_fr": DAY_NAMES[d]["fr"],
            "name_en": DAY_NAMES[d]["en"],
            "date": get_date_for_day(d),
            "events": []
        }
    
    # Process each source
    for source in sources:
        print(f"📡 Processing: {source['name']}")
        
        # Scrape for dynamic data
        dynamic = {}
        if source["type"] == "website":
            dynamic = scrape_website(source)
        elif source["type"] == "facebook":
            dynamic = scrape_facebook(source)
        
        # Build event and add to each relevant day
        event = build_event(source, dynamic)
        for day in source.get("days", []):
            days[str(day)]["events"].append(event.copy())
    
    # Sort events by time within each day
    for d in days.values():
        d["events"].sort(key=lambda e: e.get("time", "99:99"))
    
    # Write output
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "days": days
    }
    
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    total_events = sum(len(d["events"]) for d in days.values())
    print(f"✅ Wrote {total_events} events across 7 days to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
