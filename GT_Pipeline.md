# GT_Pipeline.md — GroundTruth V2
# Pipeline Deals | Binary Events | Sector Intelligence Layer
# Load when: deal-specific work, binary event tracking, SIL configuration

---

## PIPELINE DEALS
Source of truth: Google Sheets "Pipeline" tab (45 active deals).
gs/classify.py reads dynamically via sheets/pipeline.py — cached per run.
3-tier matching: Tier 1 (deal name) | Tier 2 (A-tag + geography) | Tier 3 (excluded)

### Priority Active Deals

| Deal | Asset Type | Key Exposures | Active Binary Events |
|------|-----------|---------------|---------------------|
| Project Vega | Solar + Storage | Module, aluminum, copper, steel | OBBBA July 4, FERC April 30 |
| GT-108 SB Energy Ohio | Gas + Digital Infra | Natural gas, steel, copper | FERC April 30, PJM April 27 |
| GT-109 SB Energy Milam | Digital Infra + Power | Power prices ERCOT, gas | OBBBA post-2027 risk |

### Pipeline (remaining 39 V1 deals)
Asset types: Solar, Data Center, LNG, Transport
C-tags: auto-populated from deal notes
Geography confirmed: 7/45 deals. 38/45 unknown — Tier 2 matching disabled.

### Flagged Deals (require fixes)
- Temple: "Data Centre" text not "A09" code — SIL mapping broken. Fix in Pipeline tab.
- BLK GIP: no sector definition (SR-09 not built)
- Razorback: no sector definition (SR-09 not built)

---

## ACTIVE BINARY EVENTS
Managed by GT/binary_events.py. Logged in Alpha Scoreboard.

| # | Event | Date | Impact |
|---|-------|------|--------|
| 1 | FOMC | April 28-29 2026 | All floating rate pipeline deals. If hike → E08 Volcker compound |
| 2 | FERC Large Load Rule | April 30 2026 | GT-108 SB Energy Ohio interconnection cost assumptions |
| 3 | OBBBA BOC Deadline | July 4 2026 | Project Vega solar ITC/PTC eligibility |
| 4 | Trump April 8 Deadline | RESOLVED April 12 | Hit: Y. Two-week ceasefire. E07 active. Signals GT-041/042/043 |

---

## SECTOR INTELLIGENCE LAYER (SIL)
File: ge/sector_intelligence.py | Status: LIVE Phase 4

8 sector entries: SR-01 through SR-08.
Each defines: key_c_tags, noise_c_tags, key_keywords, noise_keywords,
              a_tags, material signal types, noise signal types.

### Signal Matching Hierarchy
Tier 1 — DEAL SPECIFIC: deal name in signal text. Full SP weight.
Tier 2 — ASSET + GEO: A-tag + geography match. 0.5 SP weight.
Tier 3 — SECTOR GENERAL: excluded from deal counts. Logged to ge_sil_misses.

### Current SIL State
0 Tier 1 signals — no trade press sources yet (Phase 5 item)
0 Tier 2 signals — 38/45 deals have unknown geography (Sri to populate)
All current signals are Tier 3 — regime/macro level only.

### To Unlock Deal-Specific Matching
1. Sri populates Geography column in Pipeline tab (state + ISO/RTO)
2. Trade press sources added to fetch layer (Phase 5)
3. ANECDOTAL signals via breaking signal trigger name deals explicitly

SIL miss log: ge_sil_misses table in groundtruth.db.
Sri reviews weekly — override column available for incorrect filters.

---

## KNOWN GAPS

### CRITICAL (fix now)
1. Geography: 38/45 deals unknown state/ISO — Tier 2 matching disabled
   Action: Sri populates Pipeline tab Geography column
2. Temple A-tag: "Data Centre" text not "A09" code — SIL mapping broken
   Action: Fix in Pipeline tab

### HIGH (Phase 5)
3. SR-09 Critical Minerals: not built — BLK GIP + Razorback unmatched
4. Trade press sources: 0 Tier 1 signals without IJGlobal/PFI
5. GE-1 Alert Distribution: confirm GREEN on next scheduled run

### MEDIUM (Phase 5 or later)
6. GP GroundPortfolio: not built — H2 2026 mini-perm cliff unmonitored
7. GR GroundResearch: not built
8. Railway deployment: still local Windows Task Scheduler

---

## RISK REGISTER (TOP 3)

1. Geography gap — 38/45 deals no state/ISO. Tier 2 matching disabled.
   Mitigation: Sri populates Pipeline tab incrementally.

2. Tier 1 signal gap — 0 deal-specific signals. No trade press in RSS.
   Mitigation: Sri ANECDOTAL signals + IJGlobal/PFI in Phase 5.

3. GE-1 Alert Distribution — recalibrated, needs live confirmation.
   Target: RED 10-20% / AMBER 40-60% / GREEN 25-45%.
   Mitigation: Monitor on next scheduled run.

---
*GT_Pipeline.md | Load on demand | GroundTruth V2 April 2026*
