# Parilongas — Project Context for Claude

## What This Is

Parilongas.fr is an automated agenda of Argentine tango events (milongas, practicas, classes) in Paris. It is a static site deployed on GitHub Pages, rebuilt daily by a GitHub Actions workflow.

**Live site:** https://camsonne.github.io/parilongas/ (temporary — target domain: www.parilongas.fr)
**GitHub repo:** https://github.com/camsonne/parilongas
**Branch:** `master`

## Architecture

```
parilongas-prototype/
├── index.html                    # Single-page site template (inline CSS + JS)
├── data/
│   ├── sources.json              # Registry of event sources to scrape
│   └── events.json               # Generated daily by the scraper (not committed)
├── scripts/
│   ├── scrape_events.py          # Reads sources.json → writes events.json
│   └── build_site.py             # Injects events.json into index.html → /site/
└── .github/workflows/
    └── update-events.yml         # Daily cron at 6 AM Paris time (5 AM UTC)
```

## How It Works

1. GitHub Action runs daily at 6 AM Paris time
2. `scrape_events.py` reads `data/sources.json`, scrapes each source, writes `data/events.json`
3. `build_site.py` injects the JSON into the `index.html` template, outputs to `/site/`
4. The action commits any changes and deploys `/site/` to GitHub Pages

## Event Sources (`data/sources.json`)

Three source types are supported:
- `website` — scrape a URL with BeautifulSoup (custom parsing per source in `scrape_website()`)
- `facebook` — placeholder; needs Facebook Graph API token in secret `FB_ACCESS_TOKEN`
- `aggregator` — returns multiple events; has its own scraper function per source ID

Current sources:
| ID | Name | Type | Days |
|----|------|------|------|
| cascabelito | Pratique Cascabelito | website | Friday |
| milonga-du-chat | La Milonga du Chat | facebook | Friday |
| parisiana | La Parisiana | facebook | All days |
| tango-argentin | Tango-Argentin.fr | aggregator | All days (Île-de-France) |
| la-cosy | La Cosy | website | Tuesday |

## Known Issues / TODOs

- **tango-argentin.fr scraper**: The site is largely JS-rendered; the current BeautifulSoup scraper gets partial results. A headless browser (Playwright) would give full results.
- **Facebook sources**: `scrape_facebook()` is a placeholder returning `{}`. Needs Facebook Graph API or Apify integration.
- **la-cosy URL**: Still set to `https://example.com/la-cosy` — needs the real URL.
- **GitHub Pages source**: Currently serves from the repo root (`/`), but the workflow builds to `/site/`. The Pages source setting may need to be changed to GitHub Actions mode once the workflow deploy step is verified.
- **Domain**: `build_site.py` writes a `CNAME` file for `www.parilongas.fr` — DNS not yet configured.
- **Branch mismatch**: The deploy job in `update-events.yml` checks out `ref: main` but the repo uses `master`. This needs fixing.

## Adding a New Source

1. Add an entry to `data/sources.json` (see README for schema)
2. If type is `website`, add custom parsing logic inside `scrape_website()` keyed by `source["id"]`
3. If type is `aggregator`, add a new `scrape_aggregator_<id>()` function and a branch in `main()`

## Running Locally

```bash
cd parilongas-prototype
pip install requests beautifulsoup4 lxml
python scripts/scrape_events.py   # writes data/events.json
python scripts/build_site.py      # writes site/index.html
```
