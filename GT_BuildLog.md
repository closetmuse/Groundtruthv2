# GT_BuildLog.md — GroundTruth V2
# Phase History | File Map | Deployment Record
# Load when: debugging, continuing build, understanding what exists

---

## BUILD SEQUENCE

### Phase 0 — Encyclopedia Foundation: COMPLETE April 2026

### Phase 1 — GS + GE Core: Weeks 3-6

### Phase 2 — GT Email First Send: COMPLETE April 11 2026
- gs/classify.py      — prompt + parser, 4 fallback strategies, GS-002 written
- gi/encyclopedia.py  — 8 entries loaded, E07 excluded, pattern match live
- gt/email_builder.py — 10 sections, dark theme, Gmail OAuth, divergence footnote
- gt/orchestrator.py  — full chain 80s, independent stage error handling
- gs/prices.py        — units fixed, 90d deltas, BBB/HY divergence footnote
- infra/run_scheduled.py      — Task Scheduler entry point, scheduler.log
- infra/setup_task_scheduler.py — one-time registration, executed April 11
- infra/run_manual.py — manual + breaking signal + dry run flags
- Task: GroundTruth_DailyRun registered, first run April 12 06:00 ET

### Phase 3 — Google Sheet Interface: COMPLETE April 12 2026
- sheets/interface.py   — 7 tabs live, sync_all() + sync_signals_only()
- sheets/pipeline.py    — 48 deals dynamic, read_pipeline_from_sheet()
- sheets/scoreboard.py  — Scoreboard + Stats tabs, log_outcome(), hit rate
- gt/binary_events.py   — 4 events seeded, auto-detect, resolve_event()
- gs/classify.py        — rebuilt as pure Python, calibrated scoring
- Task Scheduler        — fixed via batch wrapper infra/run_daily.bat

### Phase 4 — GPi + Sector Intelligence: COMPLETE April 12 2026
- gpi/pipeline_agent.py  — 45 deals scored, 4-sub-score heat engine
- ge/sector_intelligence.py — 8 sector entries SR-01 to SR-08, SIL filter live
- infra/health_monitor.py — 9 subsystems, RunContext, Health tab in Sheets
- infra/format_sheets.py  — Calibri 12, dark headers, alert-column color only
- infra/populate_ctags.py — C-tags auto-populated from deal notes
- ge/scorer.py            — recalibrated RED/AMBER/GREEN thresholds
- gs/classify.py          — 3-tier deal matching, geography-aware, SIL wired
- gt/email_builder.py     — Section 6 Deal Watch live with definitions + narratives
- groundtruth.db          — ge_sil_misses table added
- Metals price feed       — Yahoo Finance ALI=F/HG=F + FRED steel HRC

### Phase 5 — Source Expansion + Code Review: COMPLETE April 12 2026
- 26 sources active (was 14), 110 items/run
- Code review: 13 issues found, 6 fixed
- AGC reclassified F19→F12, DRAFT cleanup automated
- Health monitor: row range fix, SIL dedup, GE-3 metric fix

### Phase 6 — Power Markets Intelligence: IN PROGRESS April 13 2026
- gs/prices.py     — DA price fetch replacing RT spot,
                     _generate_price_signals() wired, EIA/Yahoo replacing FRED
- sheets/interface.py — _read_prices() rebuilt, 13 columns, 3 sections,
                        RTO DA metadata fully surfaced
- First PRICE signals: GS-207/208/209 (curtailment)
- Second latency measurement forming: CAISO/ERCOT

### Phase 7 — GP Portfolio + Telegram: PENDING
### Phase 8 — GC + Client Intelligence: PENDING (compliance gate)
### Phase 9 — GI Pattern Learning: Months 8-12

---

## DEPLOYMENT RECORD
Phase 2: Windows Task Scheduler (local) — April 11 2026
Phase 3: Google Sheets live — April 12 2026
Phase 4: Deal Watch + Health tabs live — April 12 2026
Phase 5: Source expansion + code fixes — April 12 2026
Phase 6: Power markets DA intelligence — April 13 2026
Trigger for Phase advance: when email tells Sri something he acts on.

---

## FILE MAP
```
GroundTruth_v2/
├── gs/
│   ├── classify.py         # Signal classification, 4 fallback strategies
│   ├── prices.py           # Price fetch, DA hubs, _generate_price_signals()
├── ge/
│   ├── scorer.py           # RED/AMBER/GREEN thresholds, recalibrated
│   ├── sector_intelligence.py  # SR-01 to SR-08, SIL filter
│   ├── weights.py          # F-tag confidence lookup
├── gpi/
│   ├── pipeline_agent.py   # 45 deals, 4-sub-score heat engine
├── gi/
│   ├── encyclopedia.py     # 8 entries, pattern match
├── gt/
│   ├── orchestrator.py     # Full chain 80s, error handling
│   ├── email_builder.py    # 10 sections, dark theme, Deal Watch
│   ├── binary_events.py    # 4 events, auto-detect, resolve
├── sheets/
│   ├── interface.py        # 7 tabs, sync_all(), _read_prices()
│   ├── pipeline.py         # Dynamic read, read_pipeline_from_sheet()
│   ├── scoreboard.py       # Scoreboard + Stats, log_outcome()
├── infra/
│   ├── run_daily.bat       # Task Scheduler entry point
│   ├── run_manual.py       # Manual + breaking signal + dry run
│   ├── run_scheduled.py    # Scheduled entry point
│   ├── health_monitor.py   # 9 subsystems, RunContext, Health tab
│   ├── format_sheets.py    # Calibri 12, dark headers
│   ├── populate_ctags.py   # Auto C-tag population
├── encyclopedia/           # 8 entries E01-E08, immutable except E07
├── groundtruth.db          # SQLite — signals, ge_sil_misses
├── CLAUDE.md               # Layer A — brain (this architecture)
├── GT_Reference.md         # Layer A companion — tags, regimes, data
├── GT_Pipeline.md          # Layer A companion — deals, events, SIL
├── GT_BuildLog.md          # Layer A companion — phases, file map
├── Current_Application.md  # Layer C — live market overlay
```

---
*GT_BuildLog.md | Load on demand | GroundTruth V2 April 2026*
