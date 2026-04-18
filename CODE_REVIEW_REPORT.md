# GroundTruth V2 — Code Review Report
# Date: April 12 2026
# Reviewer: Claude Desktop
# Files reviewed: 20 Python files + CLAUDE.md + PHASE5_BRIEFING.md
# DB state at review: 96 signals (49 ACTIVE, 5 DRAFT, 42 FILTERED), 30 price snapshots, 4 binary events, 0 zombie runs

---

## CRITICAL ISSUES (fix before any Phase 5 work)

### ISSUE-1 — Health Monitor Section A Write Range Too Small
Severity: CRITICAL
File: infra/health_monitor.py line 516
Problem: `range=f"'{tab_name}'!A2:F9"` writes 8 rows but 9 subsystems exist (GS-1, GS-2, GS-3, GE-1, GE-2, GE-3, GPi-1, GPi-2, GT-1). The 9th subsystem (GT-1) causes HttpError 400 on every run.
Impact: Health tab Section A never updates. Error logged on every capture run. Health history append also fails because it depends on the same service call.
Fix: Change line 516 to `range=f"'{tab_name}'!A2:F10"` — 9 rows for 9 subsystems.

### ISSUE-2 — SIL Miss Table Accumulating Duplicate Rows
Severity: CRITICAL
File: ge/sector_intelligence.py line 329
Problem: `_log_sil_miss()` is called every time `filter_signals_for_deal()` runs — which happens in both `gpi/pipeline_agent.py` score_deal() AND the email builder Section 6 call. The same signal-deal pair is logged multiple times per run (once per call to pipeline_agent). SIL misses table has 65 rows after ~10 runs, growing at ~6 per run.
Impact: GE-3 SIL Filter health metric shows inflated rates (114%, 133%) because it counts cumulative SIL misses against current active signal count. Metric is meaningless.
Fix: Add dedup check in `_log_sil_miss()`: check if (signal_id, deal_name) already exists before INSERT. Or: truncate ge_sil_misses at start of each run and repopulate.

---

## HIGH ISSUES (fix before next scheduled run)

### ISSUE-3 — DRY_RUN = True Default in orchestrator.py
Severity: HIGH
File: gt/orchestrator.py line 18
Problem: `DRY_RUN = True` is the module-level default. While `run_scheduled.py` correctly overrides to False, and `run_manual.py` respects the `--dry` flag, any direct import of orchestrator.run() will suppress email sending.
Impact: If orchestrator is called outside the run_manual/run_scheduled wrappers, email silently fails. Future code paths could hit this.
Fix: Change to `DRY_RUN = False` (production default). The `--dry` flag in run_manual.py explicitly sets True when needed.

### ISSUE-4 — 5 Signals Stuck in DRAFT Permanently
Severity: HIGH
File: gs/classify.py + ge/scorer.py
Problem: 5 AGC News signals (GS-043 through GS-047) have status=DRAFT since April 12. The scorer sets DRAFT when `confidence < 0.60 and source_type == "FETCH"`. AGC News maps to F19 (trade association) with confidence 0.55 — permanently below the 0.60 threshold. These signals will never transition to ACTIVE.
Impact: 5 signals invisible in email and Sheets (DRAFT not shown). Construction workforce data is relevant in R0 stress regime but never surfaces.
Fix: Either (a) raise AGC News F-tag to F16 (0.60+) in gs/classify.py SOURCE_CONFIDENCE, or (b) lower the DRAFT threshold to 0.50, or (c) add a manual override in store.py to promote DRAFT→ACTIVE after Sri review.

### ISSUE-5 — affected_deals at 0% Population
Severity: HIGH
File: gs/classify.py match_deals()
Problem: After the 3-tier matching fix, affected_deals is 0/49 (0%) populated across all ACTIVE signals. The 3-tier system requires Tier 1 (deal name in text) or Tier 2 (A-tag + geography), but zero current signals contain any deal name or state/RTO geography keyword.
Impact: pipeline_risk_alert is never set. Section 4 RED signals show no deal associations. Deal Watch narratives show 0 deal-specific signals. The deal matching pipeline is architecturally correct but functionally inactive.
Fix: This is a data gap, not a code bug. Requires: (a) Sri populating geography in Pipeline tab (38/45 unknown), (b) trade press sources that publish deal names (Phase 5), (c) Sri contributing ANECDOTAL signals naming deals. No code fix needed — the system correctly reports zero when zero genuine matches exist.

### ISSUE-6 — GE-3 SIL Filter Health Metric Calculation Wrong
Severity: HIGH
File: infra/health_monitor.py _check_ge3_sil()
Problem: Metric divides `total SIL misses (cumulative all-time)` by `current active signal count`. This produces nonsensical percentages (114%, 133%) because the numerator grows every run while the denominator stays ~49.
Impact: GE-3 always shows RED. Health score degraded by a broken metric.
Fix: Change to per-run SIL filter rate. Either (a) count SIL misses from last run only (filter by logged_at within last run window), or (b) store SIL filter count in RunContext and use that instead of the cumulative table count.

---

## MEDIUM ISSUES (fix within Phase 5)

### ISSUE-7 — o_tag at 24% Population Rate
Severity: MEDIUM
File: gs/classify.py classify_item()
Problem: Only 12/49 ACTIVE signals have o_tag populated. The keyword matching for O1-O5 is too narrow — many infrastructure-relevant signals don't contain "construction", "refinancing", "acquisition" etc.
Impact: Opportunity tagging underperforms. Email Section 5 AMBER signals lack opportunity context.
Fix: Expand O-tag keyword lists in classify_item(). Add: "financial close", "mandate", "awarded", "RFP", "shortlist" for O1. Add: "maturity", "extend", "amend" for O2.

### ISSUE-8 — Price History Series Key Names May Not Match Future Changes
Severity: MEDIUM
File: sheets/interface.py _append_price_history()
Problem: The function hardcodes series key names ("wti_usd_bbl", "brent_usd_bbl", etc.) that must match exactly what gs/prices.py writes to gs_price_snapshots. If prices.py adds or renames a series, the Price History tab silently shows blank cells.
Impact: No error — just missing data in the Price History ledger.
Fix: Read series keys dynamically from the latest snapshot rather than hardcoding. Or add a validation check that prints a warning if a key returns empty.

### ISSUE-9 — Dedup Window May Suppress Legitimate Follow-Up Signals
Severity: MEDIUM
File: gs/store.py is_duplicate()
Problem: Dedup matches on first 80 characters of headline (case-insensitive). Wire services frequently publish follow-up articles with similar opening headlines but materially different content. Example: "Iran talks stall" followed by "Iran talks stall as deadline passes" — the second would be suppressed.
Impact: Legitimate signals filtered as duplicates. Difficult to detect because suppressed signals are never written.
Fix: Increase headline match threshold from 80 to 120 characters. Or add URL-based dedup as primary (exact match) and headline as secondary (fuzzy match with higher threshold).

### ISSUE-10 — Encyclopedia Match Always Returns E01 GFC at 78%
Severity: MEDIUM
File: gi/encyclopedia.py match_signals_to_encyclopedia()
Problem: The signal cluster for matching is built from scored_signals which are heavy on C02/C12 (financing/credit tags). E01 GFC has C02/C06/C07/C12/C11 — strong overlap with the current signal distribution. The match score doesn't weight by signal alert level (RED signals should count more than GREEN).
Impact: Pattern match section always shows E01 GFC regardless of actual market conditions. The E03 Ukraine or E08 Volcker patterns (more relevant to current Hormuz R0 stress) are ranked lower.
Fix: Weight signal C-tags by alert level before matching: RED tags count 3x, AMBER 2x, GREEN 1x. This would push C08/C05 (geopolitical/oil — RED signals) higher and reduce C12/C14 (financing/sponsor — GREEN signals) weight.

---

## LOW ISSUES (backlog)

### ISSUE-11 — ge/weights.py is Placeholder
Severity: LOW
File: ge/weights.py
Problem: File contains only 3 lines of placeholder comments from Phase 1. The F-tag confidence lookup table referenced in CLAUDE.md ("Full confidence lookup table: ge/weights.py") does not exist here — it's hardcoded in ge/scorer.py instead.
Impact: Documentation mismatch. No functional impact.
Fix: Either move F_TAG_CONFIDENCE from scorer.py to weights.py and import, or update CLAUDE.md reference.

### ISSUE-12 — Drive API Not Enabled
Severity: LOW
File: gt/email_builder.py save_digest_to_drive()
Problem: Google Drive API is not enabled in GCP project 825607905075. The function handles this gracefully (WARN message, continues) but the permanent digest URL feature is non-functional.
Impact: No permanent browser-viewable digest link. Email works fine.
Fix: Enable Drive API at https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=825607905075

### ISSUE-13 — MISO Illinois Showing Negative Price
Severity: LOW
File: gs/prices.py fetch_rto_prices()
Problem: MISO Illinois Hub occasionally shows negative prices (-$1.56/MWh) which are legitimate market prices but may confuse non-energy readers in the email price table.
Impact: Visual confusion only. Price is real.
Fix: Add a footnote in email Section 2 when any power price is negative: "Negative power price reflects curtailment or oversupply conditions."

---

## ARCHITECTURAL OBSERVATIONS

1. **Field ownership is clean.** After the affected_deals dual-write fix, every field in gs_signals has exactly one writer module. This is the most important architectural property and it holds.

2. **The information flow is one-directional.** GS→GE→GI→GPi→GT→Sheets→Infra. No agent imports from a downstream agent. The orchestrator is the sole sequencer. This is correct per PRD.

3. **store.py is the exclusive gs_signals writer.** All signal writes go through write_signal() and update_signal(). No direct sqlite3 writes to gs_signals found anywhere.

4. **The 3-tier deal matching is architecturally correct but data-starved.** The system correctly reports 0 deal-specific matches because no current signal mentions a deal by name or geography. This is honest — the previous 23-44 match counts were noise. The system needs trade press sources and geography data to activate Tiers 1 and 2.

5. **The SIL (Sector Intelligence Layer) is well-designed but the miss logging creates a growing unbounded table.** Need per-run truncation or dedup.

6. **The health monitor is the right idea but two metrics are broken** (Section A row range, SIL cumulative count). Fix these and the health score will accurately reflect system state.

---

## WHAT IS WORKING WELL

1. **Signal relevance filter** — 42/96 signals correctly filtered. No sports, retail, entertainment noise in the active corpus.

2. **Alert distribution** — R10% A63% G27% after recalibration. Close to target. Genuine RED signals are infrastructure-relevant.

3. **Price feed** — 20 series live including metals (aluminum, copper, steel). 30 snapshots accumulated. Price History tab appending correctly.

4. **Binary events** — 4 events tracked, 1 resolved with correct outcome, E07 trigger active. Countdown block rendering correctly.

5. **Fetch run audit trail** — 0 zombie runs. close_fetch_run() working correctly after fix. Every run has start/end timestamps and counts.

6. **Sheets integration** — 10+ tabs syncing reliably. Formatting consistent (Calibri 12, white rows, dark headers, alert-column color only).

7. **Email delivery** — Gmail OAuth working. 10-section email sending successfully on every production run.

8. **Encyclopedia pattern matching** — 8 entries loaded, E07 excluded as active event. Pattern match block rendering in email.

9. **geo_no_infra_nexus penalty** — Election signals without infrastructure nexus correctly penalized (-15 points). Viktor Orban signal would have been RED without this fix.

---

## RECOMMENDED FIX SEQUENCE

1. **ISSUE-1** Health monitor row range — 2 minutes, 1 line change
2. **ISSUE-2** SIL miss dedup — 15 minutes, add dedup check to _log_sil_miss()
3. **ISSUE-6** GE-3 metric fix — 10 minutes, change to per-run count
4. **ISSUE-3** DRY_RUN default — 1 minute, change True to False
5. **ISSUE-4** DRAFT signal promotion — 5 minutes, raise AGC confidence to 0.60
6. **ISSUE-10** Encyclopedia match weighting — 20 minutes, add alert-level weighting

Total: ~53 minutes for issues 1-6. Issues 7-13 are backlog.

---

Total issues: 13
CRITICAL: 2 | HIGH: 4 | MEDIUM: 4 | LOW: 3
Estimated fix time: 53 minutes (CRITICAL + HIGH)
Recommendation: Fix CRITICAL issues 1-2 and HIGH issue 3 immediately, then run a full capture to confirm health score improves from FAILING to DEGRADED or HEALTHY.