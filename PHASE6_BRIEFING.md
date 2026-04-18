# GROUNDTRUTH V2 — PHASE 6 SESSION BRIEFING
# Power Markets Intelligence Layer
# Updated: April 13 2026

## PHASE 6 BUILD ORDER — UPDATED APRIL 13 2026

### COMPLETED THIS SESSION

Completed: RTO DA price intelligence
  10 hubs, DA prices, full metadata per hub
  Replaces RT spot — correct market for infra finance

Completed: _generate_price_signals()
  Auto PRICE signal generation from DA price data
  3 signal types: curtailment, BESS, scarcity
  First signals: GS-207/208/209 curtailment

Completed: Prices tab rebuilt
  13 columns, 3 section headers, full RTO metadata

Completed: Price source fixes
  WTI/Brent to EIA API (same day)
  FX/USD Index to Yahoo Finance (real-time)

### PRIORITY 1 — Complete Source Expansion
Status: CARRY FORWARD from Phase 5
Additional validated sources ready to add to fetch.py
Target: 35-40 sources, 200+ items/run

### PRIORITY 2 — Geography Population (Sri action)
Status: BLOCKING
GS-207 and GS-209 firing with no deal to alert.
Sri to populate Pipeline tab Geography column.

### PRIORITY 3 — Power Markets Completion
  a. Interconnection queue monitoring
  b. PJM capacity auction alert
  c. ERCOT curtailment 30-day trend
  d. Fuel mix signals

### PRIORITY 4 — GP GroundPortfolio Lite
Maturity ledger, mini-perm cliff, 2020-21 vintage flags.

### PRIORITY 5 — Telegram
RED alert push + screenshot ingestion.

### PRIORITY 6 — Run Frequency
Every 2 hours via Task Scheduler.

### PRIORITY 7 — Railway Deployment
Trigger: first HOT deal OR first Tier 1 signal.

## PHASE 6 SUCCESS CRITERIA

  Done: RTO DA prices: 10 hubs, DA market, full metadata
  Done: Auto PRICE signals: curtailment/BESS/scarcity
  Done: Prices tab: 13 cols, full metadata surfaced
  Open: Sources: 35+ configured, 200+ items/run
  Open: Geography: 15+ pipeline deals with state/ISO
  Open: Power: first PRICE signal linked to named deal
  Open: GP Portfolio: maturity ledger live 10+ deals
  Open: Telegram: RED alert push live
  Open: Tier 1 signal: named deal in corpus
  Open: HOT deal: first heat score >= 75

## NEXT SESSION OPENER

Read CLAUDE.md
Read this briefing file
Check logs/scheduler.log
Check Prices tab — RTO DA section
Check Signals tab — new PRICE signals overnight
Confirm Priority 2 (geography) — has Sri populated?
Begin Priority 1 — source expansion
Then Priority 3 — power markets completion