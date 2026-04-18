# GROUNDTRUTH V2 — PHASE 4 SESSION BRIEFING
# For Claude to read at start of Phase 4 session.

## WHAT EXISTS — PHASE 3 COMPLETE

OPERATIONAL COMPONENTS:
  gs/prices.py    — 17/18 series, 7d/30d/90d deltas, divergence footnote
  gs/fetch.py     — 14/18 sources, 63 items/run, RSS + SCRAPE methods
  gs/classify.py  — pure Python keyword classification, 48-deal dynamic match
  gs/store.py     — signal write/read/dedup/latency events
  ge/scorer.py    — RED/AMBER/GREEN scoring, deal matching, regime weights
  gi/encyclopedia.py — 8 entries, pattern match, build_pattern_match_block()
  gt/email_builder.py — 10-section HTML email, Gmail OAuth send
  gt/orchestrator.py  — full chain sequencer, 90s runtime
  gt/binary_events.py — 4 events, auto-detect, resolve, scoreboard integration
  sheets/interface.py — 7 tabs, sync_all(), color-coded alert column
  sheets/pipeline.py  — 48 deals, read_pipeline_from_sheet(), seed_pipeline_sheet()
  sheets/scoreboard.py — Scoreboard + Stats tabs, log_outcome(), hit rate calc
  infra/run_scheduled.py — Task Scheduler entry point
  infra/run_daily.bat    — batch wrapper for working directory
  infra/run_manual.py    — manual trigger, --breaking, --dry flags
  core/schema.py         — 7 tables including gt_resolution_proposals

SCHEDULER:
  Task: GroundTruth_DailyRun
  Trigger: daily 06:00 ET via infra/run_daily.bat
  Status: enabled, firing clean (exit code 0x0)
  Log: GroundTruth_v2/logs/scheduler.log

DATABASE:
  groundtruth.db — SQLite at GroundTruth_v2/
  Tables: gs_signals, gs_price_snapshots, gs_fetch_runs,
          gt_binary_events, ge_latency_events, gt_resolution_proposals
  Signal count at Phase 3 close: 70
  Alert breakdown: RED 8 / AMBER 30 / GREEN 32

GOOGLE SHEETS (7 tabs):
  Sheet ID: 10i__P3EWcBt49af72vRD7BUIEINaWx-7vIG_Y6eauy0
  Signals     — 70 rows, alert-column color-coded, frozen headers
  Prices      — 17 series, BREACHED rows highlighted
  Binary Events — 4 events (3 OPEN, 1 RESOLVED)
  Meta        — last sync, signal count, system status
  Pipeline    — 48 deals (6 V2 full, 42 V1 partial)
  Scoreboard  — 2 entries, 100% hit rate (1 resolved)
  Stats       — auto-calculated summary

PIPELINE DEALS (48):
  6 V2 seed deals: Project Vega, GT-108, GT-109, Falcon, Atlas, Meridian
    — full C-Tags, A-Tags, Key Commodities, Binary Events
  42 V1 imports: Solar, Data Center, LNG, Transport deals
    — A-Tags mapped from V1, C-Tags pending Sri data entry
    — match coverage limited until C-Tags filled

BINARY EVENTS:
  BE-001 FOMC April 28-29 — OPEN, T-16d, triggers E08 if hike
  BE-002 FERC Large Load Rule — OPEN, T-18d, GT-108 exposure
  BE-003 OBBBA BOC Deadline — OPEN, T-83d, Project Vega ITC/PTC
  BE-004 Trump April 8 — RESOLVED, Hit=Y, E07 trigger active

PRICE STATE (April 12 2026):
  WTI:     $114.01/bbl  — 30d +71.0% BREACHED
  Brent:   $127.61/bbl  — 30d +74.4% BREACHED
  BBB OAS: 1.05%        — 30d -0.02pp (divergence footnote active)
  HY:      2.90%        — 30d -0.20pp
  UST 10Y: 4.29%
  ERCOT North: $23.52/MWh

## PHASE 4 BUILD ORDER

  1. gpi/deal_engine.py (GPi — GroundPipeline)
     Live deal exposure engine.
     Reads pipeline deals from Sheets via sheets/pipeline.py.
     Scores each deal daily against active signals in gs_signals.
     Outputs deal exposure report for email Section 6.
     Tracks: signal count per deal, RED exposure, binary event proximity.
     Per-deal composite score: signal exposure + binary event risk +
     commodity sensitivity + regime stress multiplier.
     Outputs single number 0-100 per deal per day.

  2. gp/portfolio_watch.py (GP — GroundPortfolio)
     Closed book monitoring.
     Covenant breach detection.
     Refi calendar — days to maturity, mini-perm cliff alerts.
     H2 2026 refinancing cliff: flag all deals with maturity 2026-2027.
     Data source: Sri enters maturity dates in Pipeline tab or
     separate GP tab in Sheets.

  3. sheets/deals.py
     Deal detail tab in Sheets — one row per deal, live exposure score,
     signal count, binary event flags, last updated.
     Sri can drill into any deal without opening Claude Desktop.

  4. gt/email_builder.py updates
     Section 6 Portfolio Watch — top 3 stressed deals with scores
     and signal count, replacing Phase 4 placeholder text.
     Section 7 Prospect Watch — placeholder until Phase 5 GC.

  5. gt/orchestrator.py updates
     Add deal_engine step between score and encyclopedia steps.
     Add portfolio_watch step after deal_engine.
     Add sheets/deals.py sync after sheets/interface.py sync.

## PHASE 4 SUCCESS CRITERION
  Each pipeline deal has a live exposure score updated daily.
  Top 3 stressed deals appear in email with score and signal count.
  Refi calendar visible with days-to-maturity.
  Mini-perm cliff H2 2026 flagged by name.

## KEY DECISIONS FOR PHASE 4
  Deal score formula — weights for signal vs binary event vs commodity
  Refi calendar data source — Sri enters manually in Pipeline tab or
  separate GP tab
  Closed book vs pipeline — GP tracks closed deals, GPi tracks pipeline
  H2 2026 cliff deal list — Sri to provide names
  PJM price feed — requires PJM_API_KEY registration decision
  Metals price feed — aluminum, copper, steel API cost decision
  Railway deployment — after 2 weeks local validation confirmed stable

## TO START PHASE 4
  Read CLAUDE.md at GroundTruth_v2/
  Read this briefing file
  Check logs/scheduler.log for latest run outcome
  Confirm Pipeline tab has current deal list with C-Tags
  Begin gpi/deal_engine.py