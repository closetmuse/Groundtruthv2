# GROUNDTRUTH V2 — PHASE 5 SESSION BRIEFING
# For Claude to read at start of Phase 5 session.

## WHAT EXISTS — PHASE 4 COMPLETE

OPERATIONAL COMPONENTS:
  gs/prices.py          — 20 series (14 FRED + 3 RTO + 3 metals), divergence footnote
                          Yahoo Finance ALI=F/HG=F for aluminum/copper, FRED WPU101707 for steel
  gs/fetch.py           — 23/27 sources (23 active, 4 deactivated), 110 items/run
                          9 new sources added April 12: PV Magazine, Energy Monitor,
                          Oil Price, Rigzone, T&D World, Power Magazine, The Register DC,
                          Infrastructure Investor, Atlantic Council
                          4 deactivated (403/dead): IEA, FERC, Recharge, NGI
  gs/classify.py        — 3-tier deal matching, geography-aware, SIL wired
                          Tier 1: deal name match | Tier 2: A-tag + geo
                          Tier 3: excluded from counts, logged to ge_sil_misses
  gs/store.py           — signal write/read/dedup/latency, FILTERED status
  ge/scorer.py          — RED/AMBER/GREEN scoring, recalibrated thresholds
                          Tiered regime boost: raw>=45 full, 30-44 half, <30 minimal
  ge/sector_intelligence.py — 8 sector entries SR-01 to SR-08
                          SIL filter: key/noise keywords + C-tag sets per sector
                          ge_sil_misses table for Sri weekly review
  gi/encyclopedia.py    — 8 entries, pattern match, build_pattern_match_block()
  gpi/pipeline_agent.py — 45 deals, 4-sub-score heat engine (SP/CE/BP/RA)
                          3-tier signal matching, sector-filtered narratives
                          Deal Watch tab in Sheets, Section 6 email block
                          Heat definitions: HOT 75-100 / WARM 45-74 / COOL 0-44
  gt/email_builder.py   — 10-section HTML email, Gmail OAuth send
  gt/orchestrator.py    — full chain sequencer, RunContext populated
  gt/binary_events.py   — 4 events (3 OPEN, 1 RESOLVED)
  infra/health_monitor.py — 9 subsystems, Health tab appends per run
  infra/format_sheets.py  — Calibri 12, dark headers, alert-column color only
  infra/populate_ctags.py — C-tags auto-populated from deal notes
  infra/run_scheduled.py  — Task Scheduler entry point
  infra/run_daily.bat     — batch wrapper
  infra/run_manual.py     — manual + --breaking + --dry flags
  sheets/interface.py     — 9 tabs live including Health and Deal Watch
  sheets/pipeline.py      — 45 deals, geography-aware, read_pipeline_from_sheet()
  sheets/scoreboard.py    — Scoreboard + Stats tabs, log_outcome(), hit rate

SCHEDULER:
  Task: GroundTruth_DailyRun
  Trigger: daily 06:00 ET via infra/run_daily.bat
  Status: enabled, firing clean

DATABASE:
  groundtruth.db — SQLite at GroundTruth_v2/
  Tables: gs_signals, gs_price_snapshots, gs_fetch_runs,
          gt_binary_events, ge_latency_events, gt_resolution_proposals,
          ge_sil_misses
  Signal count at Phase 4 close: 78
  Alert breakdown: RED 4 / AMBER 30 / GREEN 12 (post-recalibration)

GOOGLE SHEETS (9 tabs):
  Sheet ID: 10i__P3EWcBt49af72vRD7BUIEINaWx-7vIG_Y6eauy0
  Signals     — alert-column color-coded
  Prices      — 20 series including metals, BREACHED highlighted
  Binary Events — 4 events (3 OPEN, 1 RESOLVED)
  Meta        — last sync, signal count, system status
  Pipeline    — 45 deals (6 V2 full, 39 V1 partial, 3 flagged)
  Scoreboard  — hit rate tracking
  Stats       — auto-calculated summary
  Health      — 9 subsystems, history appended per run
  Deal Watch  — 45 deals, heat scores, narratives

PIPELINE STATE:
  45 active deals
  Heat: 0 HOT / 45 WARM / 0 COOL
  Signal matches: 0 Tier 1 / 0 Tier 2 / all Tier 3
  Geography confirmed: 7/45 deals
  Sectors mapped: SR-01 14 deals / SR-02 20 deals / SR-03 3 deals
                  SR-04 2 deals / SR-06 1 deal / No sector 3 deals
  Metals live: aluminum $3,414/MT, copper $12,976/MT, steel HRC 405

BINARY EVENTS:
  BE-001 FOMC April 28-29 — OPEN, T-17d
  BE-002 FERC Large Load Rule April 30 — OPEN, T-18d, GT-108
  BE-003 OBBBA BOC Deadline July 4 — OPEN, T-83d, Project Vega
  BE-004 Trump April 8 — RESOLVED Hit=Y, E07 trigger active

HEALTH STATE AT PHASE 4 EXIT:
  GS-1 Fetch Coverage: 14/18 — AMBER (4 sources failing)
  GS-2 Signal Volume: 23/run — GREEN
  GS-3 Relevance Filter: 28% — GREEN
  GE-1 Alert Distribution: recalibrated — confirm on next run
  GE-2 Deal Match Rate: 0% — correct (all Tier 3, not a bug)
  GE-3 SIL Filter: calibrating
  GPi-1 Deal Heat Coverage: 45/45 — GREEN
  GPi-2 HOT Detection: 0 HOT — AMBER (expected until metals history + T-7 event)
  GT-1 Email Delivery: GREEN

## PHASE 5 BUILD ORDER

### PRIORITY 0 — BEFORE BUILDING ANYTHING (Sri actions required)
These are blocking items that Sri must complete in Google Sheets
before Phase 5 code builds are meaningful:

  1. Fix Temple A-tag: change "Data Centre" to "A09" in Pipeline tab
  2. Populate Geography: add State + ISO/RTO for as many deals as possible
     Focus on: all SR-02 solar deals, all SR-01 data center deals
     Even 15 deals unlocks Tier 2 matching for majority of portfolio
  3. Confirm Project Vega geography (state and ISO)

### PRIORITY 1 — SR-09 Critical Minerals Sector
File: ge/sector_intelligence.py — add SR-09 entry
Deals affected: BLK GIP Industrial (A27), Razorback (A27)
Key signals: lithium/cobalt/nickel price, IRA critical minerals guidance,
FEOC rules on battery supply chain, Chinese export restrictions

### PRIORITY 2 — Metals Price Feed Validation
Current state: Yahoo Finance ALI=F/HG=F live, FRED steel HRC live
Validate 30d history accumulation — confirm deltas computing
Impact: removes METALS_PENDING, unlocks CE scoring component
Target: first HOT deal when CE + approaching binary event compound

### PRIORITY 3 — Trade Press Sources (Tier 1 signal unlock)
Target sources to add to gs/fetch.py:
  IJGlobal RSS, PFI, Recharge News, Wood Mackenzie headlines
Impact: first Tier 1 signal validates full deal matching pipeline

### PRIORITY 4 — GP GroundPortfolio (Closed Book Monitoring)
File: gp/portfolio_watch.py
Refi Calendar, Mini-perm Cliff, Covenant Monitor, Vintage Warning
Email Section 6 Portfolio Watch (currently Deal Watch placeholder)

### PRIORITY 5 — GE-1 Scorer Recalibration Confirmation
Confirm GREEN on scheduled run after recalibration applied

### PRIORITY 6 — Fetch Coverage (GS-1 AMBER fix)
4 sources failing — diagnose and fix or replace

## PHASE 5 SUCCESS CRITERIA
  SR-09 Critical Minerals sector defined and wired
  Metals 30d deltas computing — METALS_PENDING fully removed
  At least 1 Tier 1 signal (trade press or Sri ANECDOTAL)
  At least 15 deals with confirmed geography (Tier 2 active)
  GE-1 Alert Distribution GREEN on scheduled run
  GP GroundPortfolio refi calendar live
  GS-1 Fetch Coverage GREEN (16/18+)
  First HOT deal detected

## KEY DECISIONS FOR PHASE 5
  GP data entry method — Sri manual entry vs Pipeline tab extension
  Trade press scraping vs Sri contribution — which comes first
  Railway deployment trigger — reassess after first HOT alert

## PHASE 5 OPENER
  Read CLAUDE.md at GroundTruth_v2/
  Read this briefing file
  Check logs/scheduler.log for runs since Phase 4
  Check Health tab — confirm GE-1 recalibration status
  Check ge_sil_misses table — any Sri overrides?
  Confirm Priority 0 Sri actions complete
  Begin Priority 1 — SR-09 Critical Minerals