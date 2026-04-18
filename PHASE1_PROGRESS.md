
GROUNDTRUTH V2 — PHASE 1 MILESTONE
Date: April 11 2026
Component: gs/prices.py — Price Fetch Agent

STATUS: OPERATIONAL

Coverage: 17/18 series passing
  FRED series (14): WTI, Brent, Henry Hub, UST 2/5/10/30Y,
                    SOFR, BBB OAS, HY Spread, USD Index,
                    USD/EUR, USD/JPY, USD/GBP
  gridstatus (3):   ERCOT HB_NORTH, ERCOT HB_SOUTH, MISO Illinois
  Deferred (1):     PJM West — requires PJM_API_KEY — Phase 2

Active threshold breaches at first run:
  WTI    7d: +24.6%  (threshold 8%)   BREACHED
  WTI   30d: +71.0%  (threshold 15%)  BREACHED
  Brent  7d: +17.7%  (threshold 8%)   BREACHED
  Brent 30d: +74.4%  (threshold 15%)  BREACHED

Snapshot written to: groundtruth.db / gs_price_snapshots
Delta calculation: 7d, 30d, 90d operational
Threshold engine: operational
DB write: operational

First live reading:
  WTI:         $114.01/bbl
  Brent:       $127.61/bbl
  Henry Hub:   $3.04/MMBtu
  UST 10Y:     4.29%
  BBB OAS:     1.05 bps
  HY Spread:   2.90 bps
  ERCOT North: $57.58/MWh
  MISO IL Hub: $36.19/MWh

Next: core/schema.py — signal data model

PHASE 1 FINAL — SOURCE STATUS UPDATE
Date: April 11 2026

CONTENT SOURCES — FINAL STATE 14/18:

WORKING (14):
  RSS method (13):
    Federal Reserve News    — C01, C02
    CNBC Economy            — C01, C02
    EIA Today In Energy     — C05, C08
    Al Jazeera Economy      — C08, C05
    DOE News                — C02, C04
    Utility Dive            — C03, C06, C15
    Data Center Dynamics    — C11, C14
    AGC News                — C09, C10
    Construction Dive       — C09, C10
    FT Energy               — C05, C08, C06
    FT Markets              — C01, C02, C12
    FT Companies            — C07, C14, C12
    SEIA News               — C04, C06  [URL fixed]

  SCRAPE method (1):
    IMF News                — C01, C13  [method upgraded]

BLOCKED — PHASE 2 (4):
  IEA News                  — 403, needs authenticated access
  FERC News                 — 403, needs authenticated access
  Recharge News             — 403, paywall bot protection
  Natural Gas Intelligence  — 404, paywall

PHASE 2 SOLUTIONS FOR BLOCKED SOURCES:
  IEA:   Try playwright browser automation or IEA API
  FERC:  FERC EFTS API — free, requires registration
  Recharge/NGI: Sri manual contribution via
                "Add signal from [source]" trigger phrase

PHASE 1 COMPLETE — ALL COMPONENTS OPERATIONAL:
  gs/prices.py    17/18 price series
  gs/fetch.py     14/18 content sources, 38 items per run
  core/schema.py  5 tables, SQLite operational
  gs/store.py     write/read/dedup/latency events
  ge/scorer.py    RED/AMBER/GREEN, deal matching, regime weighting

READY FOR PHASE 2:
  gs/classify.py      — classification prompt
  gi/encyclopedia.py  — encyclopedia loader
  gt/email_builder.py — 10-section email assembly
  gt/orchestrator.py  — daily run sequencer
  infra/scheduler.py  — APScheduler automation
