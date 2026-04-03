# Parilongas.fr — GitHub Pages Edition

Agenda automatisé des milongas, bals, pratiques et cours de tango argentin à Paris.

## Architecture

```
parilongas-prototype/
├── index.html                    # Main site template (single-page app)
├── data/
│   ├── sources.json              # Registry of all event sources to scrape
│   └── events.json               # Generated daily by the scraper
├── scripts/
│   ├── scrape_events.py          # Daily scraper (reads sources, writes events.json)
│   └── build_site.py             # Injects events.json into index.html → /site
├── .github/
│   └── workflows/
│       └── update-events.yml     # GitHub Action: daily cron at 6 AM Paris time
├── site/                          # Built output (deployed to GitHub Pages)
│   ├── index.html
│   └── CNAME
└── README.md
```

## How It Works

1. **Every morning at 6 AM (Paris)**, a GitHub Action runs automatically
2. `scrape_events.py` reads `sources.json` and checks each organizer's website/Facebook for updates
3. Fresh event data is written to `events.json`
4. `build_site.py` injects the data into the HTML template
5. The result is deployed to GitHub Pages at `www.parilongas.fr`

## Setup

### 1. Create a GitHub repository

```bash
git init parilongas
cd parilongas
# Copy all these files into the repo
git add -A
git commit -m "Initial setup"
git remote add origin https://github.com/YOUR_USERNAME/parilongas.git
git push -u origin main
```

### 2. Enable GitHub Pages

- Go to **Settings → Pages**
- Source: **GitHub Actions**

### 3. Point your domain

Add a `CNAME` record for `www.parilongas.fr` pointing to `YOUR_USERNAME.github.io`

### 4. Add event sources

Edit `data/sources.json` to add all your organizer URLs. Each source needs:

```json
{
  "id": "unique-id",
  "name": "Milonga Name",
  "type": "website",        // or "facebook", "instagram"
  "url": "https://...",
  "days": [5],              // 0=Sun, 1=Mon, ..., 6=Sat
  "venue": "Salle Name",
  "address": "Full address",
  "metro": "Station (ligne X)",
  "default_dj": "DJ Name",
  "default_price": "10€"
}
```

### 5. Customize scraping logic

Edit `scripts/scrape_events.py` — the `scrape_website()` function needs custom parsing for each source site to detect DJ changes, special events, cancellations, etc.

### 6. (Optional) Facebook API

For Facebook event sources, set up a Facebook App and add the token as a GitHub Secret:
- **Settings → Secrets → `FB_ACCESS_TOKEN`**

## Manual Update

You can trigger an update anytime from the GitHub Actions tab → "Update Parilongas Events" → "Run workflow".

## Cost

**$0/month** — GitHub Pages and GitHub Actions are free for public repositories.

## Advantages vs Google Sites

| Feature | Google Sites | GitHub Pages |
|---------|-------------|--------------|
| Auto-update from sources | ❌ Manual | ✅ Daily via GitHub Actions |
| Custom domain | ✅ | ✅ |
| Mobile-friendly | ✅ | ✅ |
| Full control over HTML/CSS | ❌ Limited | ✅ Full |
| API / data export | ❌ | ✅ JSON endpoint |
| Android app data source | ❌ Scrape site | ✅ Fetch events.json |
| Cost | Free | Free |
| Collaborative editing | ✅ Google Sites UI | Via sources.json or PR |
