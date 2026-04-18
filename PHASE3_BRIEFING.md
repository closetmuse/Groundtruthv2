# GROUNDTRUTH V2 — PHASE 3 SESSION BRIEFING
# For Claude to read at start of Phase 3 session.

## WHAT EXISTS — PHASE 2 COMPLETE

OPERATIONAL COMPONENTS:
  gs/prices.py    — 17/18 series, 7d/30d/90d deltas, divergence footnote
  gs/fetch.py     — 14/18 sources, 62 items/run
  gs/classify.py  — prompt + parser, classify_batch(), classify_and_store()
  gs/store.py     — signal write/read/dedup/latency events
  ge/scorer.py    — RED/AMBER/GREEN scoring, deal matching, regime weights
  gi/encyclopedia.py — 8 entries, pattern match, build_pattern_match_block()
  gt/email_builder.py — 10-section HTML email, Gmail OAuth send
  gt/orchestrator.py  — full chain sequencer, run/run_prices_only/run_breaking_signal
  infra/run_scheduled.py     — Task Scheduler entry point
  infra/run_manual.py        — manual trigger, --breaking, --dry flags

SCHEDULER:
  Task: GroundTruth_DailyRun
  Trigger: daily 06:00 ET
  Status: enabled, first run April 12 2026
  Log: GroundTruth_v2/logs/scheduler.log

DATABASE:
  groundtruth.db — SQLite at GroundTruth_v2/
  Tables: gs_signals, gs_price_snapshots, gs_fetch_runs,
          gt_binary_events, ge_latency_events
  Signal count at Phase 2 close: 2 (GS-001 test, GS-002 Blackstone/Rowan)

PRICE STATE (April 11 2026):
  WTI:     $114.01/bbl  — 30d +71.0% BREACHED
  Brent:   $127.61/bbl  — 30d +74.4% BREACHED
  BBB OAS: 1.05%        — 30d -0.02pp (divergence footnote active)
  HY:      2.90%        — 30d -0.20pp
  UST 10Y: 4.29%
  ERCOT North: $56.68/MWh (deltas pending — accumulating daily)

## PHASE 3 BUILD ORDER

  1. sheets/interface.py   — Google Sheets signal browser
                             Read signals from SQLite, write to Sheets tab
                             Sri can view/search/filter without Claude Desktop

  2. sheets/pipeline.py    — Pipeline deal parameter entry
                             Sri enters deal parameters directly in Sheets
                             Orchestrator reads from Sheets at run time

  3. sheets/scoreboard.py  — Alpha scoreboard Sheets tab
                             Binary event outcomes logged by Sri
                             Hit rate calculated and displayed

  4. gt/binary_events.py   — Binary event manager
                             Countdown, outcome logging, encyclopedia trigger
                             Feeds Section 8 of email and scoreboard

  5. infra/railway.py      — Railway deployment prep
                             Environment variable mapping
                             Health check endpoint
                             Cron trigger via Railway scheduler

## PHASE 3 SUCCESS CRITERION
  Sri can view, search, and annotate signals without opening Claude Desktop.
  Pipeline deal parameters entered in Sheets — no code edit required.
  Alpha scoreboard shows open alerts, resolved events, running hit rate.
  Binary event outcomes logged in under 2 minutes.

## KEY DECISIONS DEFERRED TO PHASE 3
  PJM price feed — requires PJM_API_KEY decision
  Metals price feed — paid API decision (aluminum, copper, steel)
  Railway deployment — after Sheets interface validated locally

## TO START PHASE 3
  Read CLAUDE.md at GroundTruth_v2/
  Read this briefing file
  Check logs/scheduler.log for April 12 first run outcome
  Begin sheets/interface.py

---
## PHASE 3 COMPLETION RECORD
Completed: April 12 2026
Session duration: single session

COMPONENTS DELIVERED:
  sheets/interface.py     COMPLETE — 7 tabs, color-coded, frozen headers
  sheets/pipeline.py      COMPLETE — 48 deals, dynamic Sheets read
  sheets/scoreboard.py    COMPLETE — Scoreboard + Stats, auto-recalculate
  gt/binary_events.py     COMPLETE — seed, countdown, auto-detect, resolve
  gs/classify.py          COMPLETE — pure Python, calibrated, 48-deal match
  infra/run_daily.bat     COMPLETE — batch wrapper, working directory fix
  infra/setup_task_scheduler.py  COMPLETE — re-registered with batch wrapper

KEY NUMBERS:
  Signals in DB:          70
  RED / AMBER / GREEN:    8 / 30 / 32
  Pipeline deals:         48 (6 V2 full + 42 V1 partial)
  Binary events open:     3 (FOMC, FERC, OBBBA)
  Binary events resolved: 1 (BE-004 Trump tariff, Hit=Y)
  Scoreboard hit rate:    100% (1 resolved event)
  Email runtime:          90 seconds
  Sheet tabs:             7 (Signals, Prices, Binary Events,
                             Meta, Pipeline, Scoreboard, Stats)
  Task Scheduler:         Fixed — infra/run_daily.bat, 06:00 ET

VERIFIED LIVE:
  Dynamic 48-deal matching from Sheets — single cached API call
  Score variance: 0.55 (base) / 0.75 (with commodity match)
  Geopolitical-only filter — Benin, teen sprinter correctly GREEN/AMBER
  BE-004 resolved with correct ceasefire outcome, E07 trigger active
  Auto-detect armed — gt_resolution_proposals table live
  Task Scheduler firing clean — exit code 0x0, email confirmed

DEFERRED TO PHASE 4:
  GPi deal engine — active signal-to-deal exposure scoring
  Covenant monitoring on closed book
  Refi calendar alerts
  Mini-perm cliff H2 2026 tracking
  PJM price feed (requires PJM_API_KEY)
  Metals price feed (aluminum, copper, steel — paid API pending)
  Railway cloud deployment (after 2 weeks local validation)
  V1 deal C-Tags + A-Tags completion (Sri data entry task)

PHASE 4 SUCCESS CRITERION:
  Each pipeline deal has a live exposure score updated daily.
  Binary event impact quantified per deal in dollar terms.
  Refi calendar visible in email with days-to-maturity countdown.