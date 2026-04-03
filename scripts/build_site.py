#!/usr/bin/env python3
"""
build_site.py — Inject events data into the static HTML site.

Reads data/events.json and index.html template,
replaces the SAMPLE_DATA placeholder with real data,
and writes the final site to the /site directory for deployment.
"""

import json
import shutil
from pathlib import Path


def main():
    print("🔨 Building site...")
    
    # Paths
    events_file = Path("data/events.json")
    template_file = Path("index.html")
    output_dir = Path("site")
    
    # Clean output
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Load events data
    if events_file.exists():
        with open(events_file, "r", encoding="utf-8") as f:
            events_data = f.read()
        print(f"   Loaded events from {events_file}")
    else:
        print("   ⚠ No events.json found, using sample data")
        events_data = None
    
    # Read template
    with open(template_file, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Replace sample data with real data
    if events_data:
        # Find and replace the SAMPLE_DATA block
        import re
        pattern = r"const SAMPLE_DATA = \{[\s\S]*?\n\};"
        replacement = f"const SAMPLE_DATA = {events_data};"
        html = re.sub(pattern, replacement, html, count=1)
        print("   Injected real event data into HTML")
    
    # Write output
    with open(output_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # Copy any static assets (images, css, etc.)
    assets_dir = Path("assets")
    if assets_dir.exists():
        shutil.copytree(assets_dir, output_dir / "assets")
    
    # Create CNAME file for custom domain
    with open(output_dir / "CNAME", "w") as f:
        f.write("www.parilongas.fr\n")
    
    print(f"✅ Site built in {output_dir}/")


if __name__ == "__main__":
    main()
