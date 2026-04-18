
GROUNDTRUTH V2 — PHASE 2 SESSION BRIEFING
For Claude to read at start of Phase 2 session.

WHAT EXISTS — PHASE 1 COMPLETE:
Location: C:\Users\nagar_7kszmu8\GroundTruth_v2\

OPERATIONAL COMPONENTS:
  gs/prices.py    — price fetch, 17/18 series, SQLite write
  gs/fetch.py     — content fetch, 14/18 sources, 38 items/run
  gs/store.py     — signal write/read/dedup/latency events
  ge/scorer.py    — RED/AMBER/GREEN scoring, deal matching, regime weights
  core/schema.py  — 5 tables in groundtruth.db

DATABASE:
  groundtruth.db — SQLite at GroundTruth_v2/
  Tables: gs_signals, gs_price_snapshots, gs_fetch_runs,
          gt_binary_events, ge_latency_events
  Current signal count: 1 (GS-001 test signal)

PRICE STATE (last run April 11 2026):
  WTI:   $114.01/bbl  — 7d +24.6%, 30d +71.0% BREACHED
  Brent: $127.61/bbl  — 7d +17.7%, 30d +74.4% BREACHED
  UST 10Y: 4.29%
  BBB OAS: 1.05 bps
  ERCOT North: $57.58/MWh

CURRENT REGIME: R0 Compound Stress — Day 42 Hormuz crisis

ENCYCLOPEDIA: 8 entries at GroundTruth_v2/encyclopedia/
  E01_GFC.md, E02_COVID.md, E03_Ukraine.md, E04_FedRateHike.md,
  E05_TaperTantrum.md, E06_OilCollapse.md, E07_Hormuz.md, E08_Volcker.md
  All PRD schema v2.0 — five sections each.

PHASE 2 BUILD ORDER:
  1. gs/classify.py      — Claude classification prompt + signal writer
                           Input: raw article dict from gs/fetch.py
                           Output: Signal object with all tags written to DB
                           Note: runs via Claude Desktop session not API
                           Reference: V1 capture.py classification prompt

  2. gi/encyclopedia.py  — Encyclopedia loader
                           Reads 8 .md files → structured fingerprint store
                           Enables pattern match section in email

  3. gt/email_builder.py — 10-section PRD email assembly
                           Pulls from all agent outputs
                           Sends via SendGrid (or Gmail OAuth from V1)

  4. gt/orchestrator.py  — Daily run sequencer 06:00-09:00 ET
                           Chains: prices → fetch → classify → score →
                                   encyclopedia → email → log

  5. infra/scheduler.py  — APScheduler automation
                           Runs orchestrator on schedule
                           Local first, Railway Phase 2 deployment

PHASE 2 SUCCESS CRITERION (PRD):
  Email sends autonomously at 08:30 ET.
  Pattern match section populated from encyclopedia.
  RED signal maps to named deal with action deadline.

KEY ARCHITECTURE NOTE:
  No Anthropic API key — Sri is on Claude Max plan.
  Classification runs through Claude Desktop Code tab.
  gs/classify.py = prompt template + parser, not API caller.
  Same architecture as V1 capture.py — proven approach.

V1 REFERENCE FILES (for classify.py prompt):
  C:\Users\nagar_7kszmu8\GroundTruth\capture.py
  C:\Users\nagar_7kszmu8\GroundTruth\schema.py
  C:\Users\nagar_7kszmu8\GroundTruth\email_builder.py

PIPELINE DEALS (for scorer and email):
  Project Vega     — Solar + Storage, OBBBA July 4, FERC April 30
  GT-108 SB Energy Ohio  — Gas + Digital, FERC April 30, PJM April 27
  GT-109 SB Energy Milam — Digital + Power, ERCOT exposure

ACTIVE BINARY EVENTS:
  FOMC April 28-29    — hold or hike — all floating rate deals
  FERC April 30       — GT-108 interconnection costs
  OBBBA July 4        — Project Vega ITC/PTC
  Trump April 8       — E07 window duration (outcome pending log)

DEFERRED TO PHASE 3+:
  PJM price feed     — requires PJM_API_KEY
  Metals price feed  — paid API decision pending
  IEA/FERC/Recharge/NGI feeds — 403 bot blocked
  Redis pub/sub      — simulated via function calls
  PostgreSQL         — SQLite sufficient through Phase 2
  Railway deployment — after email validated locally

TO START PHASE 2:
  Read CLAUDE.md at GroundTruth_v2/
  Read this briefing file
  Read V1 capture.py for classification prompt reference
  Begin gs/classify.py

---
PHASE 2 COMPLETION RECORD
Completed: April 11 2026
Session duration: single session

COMPONENTS DELIVERED:
  gs/classify.py          COMPLETE — all 5 tests passed
  gi/encyclopedia.py      COMPLETE — all 5 tests passed
  gt/email_builder.py     COMPLETE — 9,650 char HTML, 10 sections
  gt/orchestrator.py      COMPLETE — 80s end-to-end chain
  gs/prices.py fixes      COMPLETE — units, 90d deltas, divergence footnote
  infra/run_scheduled.py  COMPLETE — scheduler.log confirmed
  infra/setup_task_scheduler.py  COMPLETE — task registered
  infra/run_manual.py     COMPLETE — 3 run modes confirmed

KEY NUMBERS:
  Price series active:    17/18
  Threshold breaches:     4 (WTI, Brent — 30d)
  Encyclopedia entries:   8 (E07 excluded from matching)
  Email sections:         10
  Orchestrator runtime:   80s
  First automated run:    April 12 2026 06:00 ET

VERIFIED LIVE:
  BBB OAS divergence footnote fired on live data (amber)
  WTI +71% 30d vs BBB OAS -0.02pp 30d — verification latency signal active
  Task Scheduler: GroundTruth_DailyRun enabled, next run April 12 06:00 ET

DEFERRED TO PHASE 3:
  Google Sheets signal browser interface
  Pipeline deal parameter entry by Sri
  Alpha scoreboard visible outside email
  Railway cloud deployment
  PJM price feed (requires PJM_API_KEY)
  Metals price feed (paid API decision pending)

PHASE 3 SUCCESS CRITERION:
  Sri can view, search, and annotate signals without opening Claude Desktop.
