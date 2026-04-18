# GS — GroundSignals Content Fetch
# PRD Section 3.5 — Processing Sequence Steps 1-4
# newspaper4k + feedparser covering majority of 58 P1 sources
# Last Updated: April 2026

import json
import time
import hashlib
from datetime import datetime
from typing import Optional
import feedparser
from newspaper import Article
import requests

# ── P1 SOURCE REGISTRY ────────────────────────────────────────────────────────
# PRD Section 3.6 — Source Registry
# Format: { source_name: { url, method, c_tags, a_tags, priority } }
# method: RSS | SCRAPE | API
# Only ACTIVE sources are fetched

SOURCES = [

    # ── MACRO & MONETARY ──────────────────────────────────────────────────────
    {
        "name":     "Federal Reserve News",
        "url":      "https://www.federalreserve.gov/feeds/press_all.xml",
        "method":   "RSS",
        "c_tags":   ["C01", "C02"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "CNBC Economy",
        "url":      "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "method":   "RSS",
        "c_tags":   ["C01", "C02"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "IMF News",
        "url":      "https://www.imf.org/en/News",
        "method":   "SCRAPE",
        "c_tags":   ["C01", "C13"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },

    # ── GEOPOLITICAL & ENERGY ─────────────────────────────────────────────────
    {
        "name":     "EIA Today In Energy",
        "url":      "https://www.eia.gov/rss/todayinenergy.xml",
        "method":   "RSS",
        "c_tags":   ["C05", "C08"],
        "a_tags":   ["A01", "A12", "A13", "A14", "A15"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "IEA News",
        "url":      "https://www.iea.org/rss/news.xml",
        "method":   "RSS",
        "c_tags":   ["C05", "C08", "C04"],
        "a_tags":   ["A12", "A01", "A04", "A06", "A07"],
        "priority": "P1",
        "active":   False,  # 403 blocked since April 2026
    },
    {
        "name":     "Al Jazeera Economy",
        "url":      "https://www.aljazeera.com/xml/rss/all.xml",
        "method":   "RSS",
        "c_tags":   ["C08", "C05"],
        "a_tags":   ["A12", "A15"],
        "priority": "P1",
        "active":   True,
    },

    # ── REGULATORY & POLICY ───────────────────────────────────────────────────
    {
        # FERC dropped RSS in April 2026; site behind Cloudflare challenge.
        # CF_SCRAPE fetches the news-releases-headlines page via cloudscraper
        # and parses Drupal `.views-row` blocks.
        "name":     "FERC News",
        "url":      "https://www.ferc.gov/news-events/news/news-releases-headlines",
        "method":   "CF_SCRAPE",
        "c_tags":   ["C02", "C03"],
        "a_tags":   ["A01", "A14", "A17"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "DOE News",
        "url":      "https://www.energy.gov/rss.xml",
        "method":   "RSS",
        "c_tags":   ["C02", "C04"],
        "a_tags":   ["A02", "A04", "A25", "A17"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "SEIA News",
        "url":      "https://www.seia.org/feed",
        "method":   "RSS",
        "c_tags":   ["C04", "C06"],
        "a_tags":   ["A04", "A05"],
        "priority": "P1",
        "active":   True,
    },

    # ── DEAL FLOW & ENERGY TRANSITION ─────────────────────────────────────────
    {
        "name":     "Recharge News",
        "url":      "https://www.rechargenews.com/rss",
        "method":   "RSS",
        "c_tags":   ["C06", "C07", "C10"],
        "a_tags":   ["A04", "A05", "A06", "A07"],
        "priority": "P1",
        "active":   False,  # 404 dead since April 2026
    },
    {
        "name":     "Utility Dive",
        "url":      "https://www.utilitydive.com/feeds/news/",
        "method":   "RSS",
        "c_tags":   ["C03", "C06", "C15"],
        "a_tags":   ["A01", "A04", "A17", "A18"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "Natural Gas Intelligence",
        "url":      "https://www.naturalgasintel.com/rss/",
        "method":   "RSS",
        "c_tags":   ["C05", "C08"],
        "a_tags":   ["A01", "A12", "A13", "A14"],
        "priority": "P1",
        "active":   True,  # Re-enabled 2026-04-18 — feed returns 10 entries
    },
    {
        "name":     "Data Center Dynamics",
        "url":      "https://www.datacenterdynamics.com/en/rss/",
        "method":   "RSS",
        "c_tags":   ["C11", "C14"],
        "a_tags":   ["A09", "A10"],
        "priority": "P1",
        "active":   True,
    },

    # ── CONSTRUCTION & SUPPLY CHAIN ───────────────────────────────────────────
    {
        "name":     "AGC News",
        "url":      "https://www.agc.org/rss.xml",
        "method":   "RSS",
        "c_tags":   ["C09", "C10"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "Construction Dive",
        "url":      "https://www.constructiondive.com/feeds/news/",
        "method":   "RSS",
        "c_tags":   ["C09", "C10"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },

    # ── FT & WSJ RSS (headlines + summaries — full articles paywalled) ─────────
    {
        "name":     "FT Energy",
        "url":      "https://www.ft.com/energy?format=rss",
        "method":   "RSS",
        "c_tags":   ["C05", "C08", "C06"],
        "a_tags":   ["A01", "A04", "A12"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "FT Markets",
        "url":      "https://www.ft.com/markets?format=rss",
        "method":   "RSS",
        "c_tags":   ["C01", "C02", "C12"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "FT Companies",
        "url":      "https://www.ft.com/companies?format=rss",
        "method":   "RSS",
        "c_tags":   ["C07", "C14", "C12"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },

    # ── NEW SOURCES — Added April 12 2026 ─────────────────────────────────

    # Energy Transition + Renewables (C06, C07)
    {
        "name":     "PV Magazine US",
        "url":      "https://www.pv-magazine-usa.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C06", "C09"],
        "a_tags":   ["A04", "A05"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "Energy Monitor",
        "url":      "https://www.energymonitor.ai/feed/",
        "method":   "RSS",
        "c_tags":   ["C06", "C07", "C04"],
        "a_tags":   ["A04", "A06", "A07"],
        "priority": "P1",
        "active":   True,
    },

    # Oil + Gas + LNG (C05, C08)
    {
        "name":     "Oil Price",
        "url":      "https://oilprice.com/rss/main",
        "method":   "RSS",
        "c_tags":   ["C05", "C08"],
        "a_tags":   ["A01", "A12", "A14", "A15"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "Rigzone",
        "url":      "https://www.rigzone.com/news/rss/rigzone_latest.aspx",
        "method":   "RSS",
        "c_tags":   ["C05", "C08", "C09"],
        "a_tags":   ["A12", "A14", "A15"],
        "priority": "P1",
        "active":   True,
    },

    # Power + Grid (C15, C03)
    {
        "name":     "T&D World",
        "url":      "https://www.tdworld.com/rss.xml",
        "method":   "RSS",
        "c_tags":   ["C15", "C03", "C09"],
        "a_tags":   ["A17", "A18"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "Power Magazine",
        "url":      "https://www.powermag.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C05", "C15", "C02"],
        "a_tags":   ["A01", "A02", "A17"],
        "priority": "P1",
        "active":   True,
    },

    # Data Centers + Digital (C11)
    {
        "name":     "The Register DC",
        "url":      "https://www.theregister.com/data_centre/headlines.atom",
        "method":   "RSS",
        "c_tags":   ["C11", "C14"],
        "a_tags":   ["A09", "A10"],
        "priority": "P1",
        "active":   True,
    },

    # Infrastructure Finance (C12, C14)
    {
        "name":     "Infrastructure Investor",
        "url":      "https://www.infrastructureinvestor.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C12", "C14"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },

    # Geopolitical + Policy (C08, C04)
    {
        "name":     "Atlantic Council",
        "url":      "https://www.atlanticcouncil.org/feed/",
        "method":   "RSS",
        "c_tags":   ["C08", "C04"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },

    # ── NEW SOURCES — Added April 13 2026 ─────────────────────────────────

    # Oil + Gas (C05) — RBN Energy: premier US midstream/gas analysis
    {
        "name":     "RBN Energy",
        "url":      "https://rbnenergy.com/blogcast.rss",
        "method":   "RSS",
        "c_tags":   ["C05", "C08"],
        "a_tags":   ["A12", "A13", "A14"],
        "priority": "P1",
        "active":   True,
    },

    # Renewables (C06, C07) — Renewable Energy World
    {
        "name":     "Renewable Energy World",
        "url":      "https://www.renewableenergyworld.com/feed",
        "method":   "RSS",
        "c_tags":   ["C06", "C07"],
        "a_tags":   ["A04", "A05", "A06"],
        "priority": "P1",
        "active":   True,
    },

    # Wind (C07) — Windpower Monthly: global offshore/onshore wind
    {
        "name":     "Windpower Monthly",
        "url":      "https://www.windpowermonthly.com/rss",
        "method":   "RSS",
        "c_tags":   ["C07", "C09"],
        "a_tags":   ["A06", "A07"],
        "priority": "P1",
        "active":   True,
    },

    # ── NEW SOURCES — Added April 13 2026 (batch 2) ───────────────────────

    # Nuclear & SMR (C02, A02, A25)
    {
        "name":     "World Nuclear News",
        "url":      "https://www.world-nuclear-news.org/rss",
        "method":   "RSS",
        "c_tags":   ["C02", "C04"],
        "a_tags":   ["A02", "A25"],
        "priority": "P1",
        "active":   True,
    },

    # Solar US (C06, A04)
    {
        "name":     "Solar Power World",
        "url":      "https://www.solarpowerworldonline.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C06", "C09"],
        "a_tags":   ["A04", "A05"],
        "priority": "P1",
        "active":   True,
    },
    {
        "name":     "PV Tech",
        "url":      "https://www.pv-tech.org/feed/",
        "method":   "RSS",
        "c_tags":   ["C06", "C04"],
        "a_tags":   ["A04", "A05"],
        "priority": "P1",
        "active":   True,
    },

    # BESS / Storage (C10, A05)
    {
        "name":     "Energy Storage News",
        "url":      "https://www.energy-storage.news/feed/",
        "method":   "RSS",
        "c_tags":   ["C10", "C06"],
        "a_tags":   ["A05"],
        "priority": "P1",
        "active":   True,
    },

    # LNG (C05, A12)
    {
        "name":     "LNG Prime",
        "url":      "https://lngprime.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C05", "C08"],
        "a_tags":   ["A12", "A13"],
        "priority": "P1",
        "active":   True,
    },

    # Commodities / Geopolitical (C08, C05)
    {
        "name":     "S&P Global Commodity Insights",
        "url":      "https://www.spglobal.com/commodityinsights/en/rss-feed/energy",
        "method":   "RSS",
        "c_tags":   ["C05", "C08"],
        "a_tags":   ["A12", "A14", "A15"],
        "priority": "P1",
        "active":   False,  # Empty feed — RSS blocked April 2026
    },

    # Grid / Transmission (C15, A17)
    {
        "name":     "NERC News",
        "url":      "https://www.nerc.com/news/Pages/rss.aspx",
        "method":   "RSS",
        "c_tags":   ["C15", "C02"],
        "a_tags":   ["A17", "A18"],
        "priority": "P1",
        "active":   False,  # Empty feed April 2026
    },
    {
        # Transmission Hub was merged into T&D World in 2026 — site now
        # redirects. T&D World is already active, so this entry is a
        # permanent dead letter (kept for registry audit trail).
        "name":     "Transmission Hub",
        "url":      "https://www.transmissionhub.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C15", "C03"],
        "a_tags":   ["A17"],
        "priority": "P1",
        "active":   False,  # Permanent — merged into T&D World
    },

    # Policy / Regulatory (C04, C02)
    {
        "name":     "E&E News Climate",
        "url":      "https://www.eenews.net/rss/climatewire.rss",
        "method":   "RSS",
        "c_tags":   ["C04", "C02"],
        "a_tags":   ["A04", "A06", "A07"],
        "priority": "P1",
        "active":   False,  # Empty feed — paywalled April 2026
    },

    # Data Centers / Digital (C11, A09)
    {
        # Bisnow dropped the section-specific DC feed; national feed is the
        # only live RSS and still carries DC stories (keyword filter in
        # classify.py handles topic gating).
        "name":     "Bisnow",
        "url":      "https://www.bisnow.com/rss",
        "method":   "RSS",
        "c_tags":   ["C11", "C14"],
        "a_tags":   ["A09", "A10"],
        "priority": "P1",
        "active":   True,
    },

    # Financing Markets (C12)
    {
        "name":     "Bloomberg Law Energy",
        "url":      "https://news.bloomberglaw.com/rss/environment-and-energy",
        "method":   "RSS",
        "c_tags":   ["C12", "C04"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,  # URL corrected 2026-04-18 (section-specific path)
    },

    # Midstream / Pipelines (C05, A14)
    {
        "name":     "Pipeline & Gas Journal",
        "url":      "https://pgjonline.com/feed/",
        "method":   "RSS",
        "c_tags":   ["C05", "C09"],
        "a_tags":   ["A14", "A15", "A16"],
        "priority": "P1",
        "active":   False,  # Empty feed April 2026
    },

    # Construction Costs / Supply Chain (C09)
    {
        "name":     "Engineering News-Record",
        "url":      "https://www.enr.com/rss/1-news",
        "method":   "RSS",
        "c_tags":   ["C09", "C15"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,  # URL corrected 2026-04-18 (new feed path)
    },

    # Insurance / Risk (C12)
    {
        "name":     "Artemis",
        "url":      "https://www.artemis.bm/feed/",
        "method":   "RSS",
        "c_tags":   ["C12", "C08"],
        "a_tags":   ["ALL"],
        "priority": "P1",
        "active":   True,
    },
]

# ── FETCH FUNCTIONS ───────────────────────────────────────────────────────────

def fetch_rss(source: dict, max_items: int = 5) -> list[dict]:
    """
    Fetch RSS feed and return list of raw article dicts.
    Returns empty list on failure — never raises.

    Two-stage fetch:
      1. browser-UA via requests — works for feeds that block feedparser
         (NGI, Bloomberg Law, many Drupal/WordPress sites)
      2. feedparser direct — works for feeds whose Cloudflare rule
         whitelists feedparser's UA but challenges browser UAs
         (LNG Prime, some others)
    Whichever returns entries first wins.
    """
    feed = None
    try:
        hdrs = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
        }
        r = requests.get(source["url"], headers=hdrs, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            feed = feedparser.parse(r.content)
    except Exception:
        feed = None

    # Fallback: direct feedparser (its default UA is whitelisted on some CF feeds)
    if not feed or not feed.entries:
        try:
            feed = feedparser.parse(source["url"])
        except Exception:
            return []

    items = []
    try:
        if not feed.entries:
            return []

        for entry in feed.entries[:max_items]:
            # Extract publication date
            pub_date = None
            if hasattr(entry, "published"):
                pub_date = entry.published
            elif hasattr(entry, "updated"):
                pub_date = entry.updated

            # Extract URL
            url = entry.get("link", "")

            # Extract summary — prefer summary over content
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary[:500]
            elif hasattr(entry, "content"):
                summary = entry.content[0].value[:500]

            items.append({
                "headline":         entry.get("title", "")[:120],
                "summary":          summary,
                "url":              url,
                "source_name":      source["name"],
                "publication_date": pub_date,
                "c_tags":           source["c_tags"],
                "a_tags":           source["a_tags"],
                "raw_content":      summary,
            })

    except Exception as e:
        print(f"  FAIL RSS {source['name']}: {e}")

    return items


def fetch_article(url: str, timeout: int = 15) -> Optional[str]:
    """
    Extract full article text from URL using newspaper4k.
    Returns text or None on failure.
    Used for SCRAPE method sources.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        if len(article.text) > 100:
            return article.text[:3000]
    except Exception:
        pass
    return None



def fetch_scrape(source: dict, max_items: int = 5) -> list[dict]:
    """
    Fetch articles using newspaper4k browser-like scraping.
    Used for sources that block RSS bot requests (IMF, etc.)
    Returns list of raw article dicts for classification.
    """
    import newspaper
    items = []
    try:
        src = newspaper.build(
            source["url"],
            memoize_articles=False,
            fetch_images=False,
        )
        for article in src.articles[:max_items]:
            try:
                article.download()
                article.parse()
                if not article.title or len(article.text) < 100:
                    continue
                items.append({
                    "headline":         article.title[:120],
                    "summary":          article.text[:500],
                    "url":              article.url,
                    "source_name":      source["name"],
                    "publication_date": str(article.publish_date or ""),
                    "c_tags":           source["c_tags"],
                    "a_tags":           source["a_tags"],
                    "raw_content":      article.text[:3000],
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  FAIL SCRAPE {source['name']}: {e}")
    return items


def fetch_cf_scrape(source: dict, max_items: int = 5) -> list[dict]:
    """
    Fetch a Cloudflare-gated HTML listing page using cloudscraper, parse
    Drupal `.views-row` blocks, return items. Body summary is the visible
    text on the listing row (title + date + category) — the body page itself
    is not fetched to avoid N+1 CF challenges per run.
    """
    import cloudscraper
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    items = []
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        r = scraper.get(source["url"], timeout=30)
        if r.status_code != 200:
            print(f"  FAIL CF_SCRAPE {source['name']}: HTTP {r.status_code}")
            return items

        # FERC serves UTF-8 but requests infers ISO-8859-1 from Content-Type.
        # Force UTF-8 so em-dashes and other non-ASCII chars round-trip cleanly.
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select(".views-row")[:max_items]
        for row in rows:
            link = row.find("a", href=True)
            if not link:
                continue
            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            href = urljoin(source["url"], link["href"])
            row_text = row.get_text(" ", strip=True)[:500]
            items.append({
                "headline":         title[:120],
                "summary":          row_text,
                "url":              href,
                "source_name":      source["name"],
                "publication_date": "",
                "c_tags":           source["c_tags"],
                "a_tags":           source["a_tags"],
                "raw_content":      row_text,
            })
    except Exception as e:
        print(f"  FAIL CF_SCRAPE {source['name']}: {e}")
    return items


def fetch_all_sources(max_items_per_source: int = 5) -> list[dict]:
    """
    Fetch all active P1 sources.
    PRD Section 3.5 Step 1-2 — load source registry, fetch content.
    Returns list of raw article dicts for classification.
    """
    active_sources = [s for s in SOURCES if s.get("active", False)]
    print(f"Fetching {len(active_sources)} active sources "
          f"(max {max_items_per_source} items each)...")

    all_items = []
    failures  = []

    for source in active_sources:
        try:
            if source["method"] == "RSS":
                items = fetch_rss(source, max_items_per_source)
                if items:
                    print(f"  OK  {source['name']}: {len(items)} items")
                    all_items.extend(items)
                else:
                    print(f"  EMPTY {source['name']}: 0 items")
                    failures.append(source["name"])

            elif source["method"] == "SCRAPE":
                items = fetch_scrape(source, max_items_per_source)
                if items:
                    print(f"  OK  {source['name']}: {len(items)} items "
                          f"(SCRAPE)")
                    all_items.extend(items)
                else:
                    print(f"  EMPTY {source['name']}: 0 items (SCRAPE)")
                    failures.append(source["name"])

            elif source["method"] == "CF_SCRAPE":
                items = fetch_cf_scrape(source, max_items_per_source)
                if items:
                    print(f"  OK  {source['name']}: {len(items)} items "
                          f"(CF_SCRAPE)")
                    all_items.extend(items)
                else:
                    print(f"  EMPTY {source['name']}: 0 items (CF_SCRAPE)")
                    failures.append(source["name"])

            else:
                print(f"  SKIP {source['name']}: method {source['method']} "
                      f"not yet implemented")

        except Exception as e:
            print(f"  FAIL {source['name']}: {e}")
            failures.append(source["name"])

        # Rate limiting — be respectful
        time.sleep(0.5)

    # MT Newswires — read from Google Sheets staging tab
    # (populated by Claude.ai scheduled task at 05:27 ET daily)
    try:
        from gs.mt_newswires import fetch_mt_newswires
        mt_items = fetch_mt_newswires()
        if mt_items:
            print(f"  OK  MT Newswires: {len(mt_items)} items (from Sheets)")
            all_items.extend(mt_items)
        else:
            print("  EMPTY MT Newswires: 0 items (tab empty or not yet populated)")
    except Exception as e:
        print(f"  FAIL MT Newswires: {e}")

    # MT Newswires DOCX — read from local file (generated by claude.ai MCP task)
    try:
        from gs.mt_news_docx import generate as mt_docx_generate
        docx_items = mt_docx_generate()
        if docx_items:
            print(f"  OK  MT Newswires DOCX: {len(docx_items)} items")
            all_items.extend(docx_items)
        else:
            print("  SKIP MT Newswires DOCX: no file for today")
    except Exception as e:
        print(f"  FAIL MT Newswires DOCX: {e}")

    print(f"\nFetch complete: {len(all_items)} items from "
          f"{len(active_sources) - len(failures)}/{len(active_sources)} sources")
    if failures:
        print(f"Failures: {', '.join(failures)}")

    return all_items, failures


def deduplicate(items: list[dict],
                existing_urls: set,
                existing_headlines: set) -> list[dict]:
    """
    Remove duplicates from fetched items before classification.
    PRD Section 3.5 Step 3.
    """
    seen_urls      = set(existing_urls)
    seen_headlines = set(existing_headlines)
    unique         = []
    dupes          = 0

    for item in items:
        url      = item.get("url", "").strip()
        headline = item.get("headline", "")[:80].lower()

        if url and url in seen_urls:
            dupes += 1
            continue
        if headline and headline in seen_headlines:
            dupes += 1
            continue

        seen_urls.add(url)
        seen_headlines.add(headline)
        unique.append(item)

    print(f"Deduplication: {len(items)} items → "
          f"{len(unique)} unique ({dupes} dupes removed)")
    return unique


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("="*55)
    print(f"GS FETCH TEST — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)

    items, failures = fetch_all_sources(max_items_per_source=3)

    print(f"\nSample items fetched:")
    for item in items[:5]:
        print(f"\n  Source:   {item['source_name']}")
        print(f"  Headline: {item['headline'][:80]}")
        print(f"  URL:      {item.get('url','')[:60]}")
        print(f"  C-tags:   {item['c_tags']}")

    print(f"\nTotal items ready for classification: {len(items)}")
    print(f"Sources failed: {len(failures)}")
    print("\ngs/fetch.py operational.")