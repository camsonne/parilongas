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


def scrape_aggregator_tango_argentin(source):
    """
    Scrape tango-argentin.fr/ile-de-france for upcoming events.
    Returns a list of event dicts (one per event found).

    Note: the site renders most content via JavaScript. This parser
    handles whatever is present in the static HTML; a headless browser
    (e.g. Playwright) would be needed for full results.

    Event format on the page (text block per event):
        <event title>
        <address>
        de HHhMM à HHhMM  <price>
        DJ : <name>
    """
    events = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Day headers are in <h6> tags; events follow until the next header.
        # We track the current date as we walk the siblings.
        current_date = ""
        current_day_num = None

        for tag in soup.find_all(["h6", "a"]):
            if tag.name == "h6":
                # Date header e.g. "Vendredi 4 avril 2026"
                current_date = tag.get_text(strip=True)
                current_day_num = _parse_fr_day(current_date)
                continue

            if tag.name == "a" and current_day_num is not None:
                # Each linked block is one event
                block = tag.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                if not lines:
                    continue

                title = lines[0]
                address = ""
                time_str = ""
                price = ""
                dj = "nc"

                for line in lines[1:]:
                    if re.match(r"de \d", line, re.I):
                        # "de 19h30 à 01h00  10 euros..."
                        time_match = re.match(r"de (\d+h\d*) à (\d+h\d*)", line, re.I)
                        if time_match:
                            time_str = time_match.group(1).replace("h", ":").ljust(5, "0")
                        price_part = re.sub(r"de \d+h\d* à \d+h\d*\s*", "", line).strip()
                        if price_part:
                            price = price_part
                    elif re.match(r"dj\s*:", line, re.I):
                        dj = re.sub(r"dj\s*:\s*", "", line, flags=re.I).strip()
                    elif not address and re.search(r"\d{5}", line):
                        address = line

                event = {
                    "id": f"tango-argentin-{re.sub(r'[^a-z0-9]', '-', title.lower()[:40])}",
                    "name": title,
                    "address": address,
                    "map_url": f"https://www.google.com/maps/search/{address.replace(' ', '+')}",
                    "venue": "",
                    "metro": "",
                    "time": time_str,
                    "dj": dj,
                    "price": price,
                    "links": {"Site": tag.get("href", source["url"])},
                    "recurrence": "",
                    "image": "",
                    "_day": current_day_num,
                    "_date": current_date,
                }
                events.append(event)

    except Exception as e:
        print(f"  ⚠ Could not scrape {source['url']}: {e}", file=sys.stderr)

    return events


def _parse_fr_day(text):
    """Extract JS-convention day number (0=Sun…6=Sat) from a French date string."""
    fr_days = {
        "lundi": 1, "mardi": 2, "mercredi": 3, "jeudi": 4,
        "vendredi": 5, "samedi": 6, "dimanche": 0,
    }
    word = text.split()[0].lower() if text else ""
    return fr_days.get(word)


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

        if source["type"] == "aggregator":
            # Aggregators return a list of fully-formed events keyed by day
            if source["id"] == "tango-argentin":
                agg_events = scrape_aggregator_tango_argentin(source)
            else:
                agg_events = []
            for event in agg_events:
                day = event.pop("_day", None)
                event.pop("_date", None)
                if day is not None:
                    days[str(day)]["events"].append(event)
            print(f"   → {len(agg_events)} events found")
            continue

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
