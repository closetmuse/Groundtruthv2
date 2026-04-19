# GroundTruth V2 — Changelog

Chronological record of platform changes. Newest on top. Entries document
code changes, schema changes, workflow changes, and cadence changes — but
not routine brief / ledger content (those are their own records).

Format per entry:
- **Date** (YYYY-MM-DD) + **commit SHA** where applicable
- **Scope** — code / schema / convention / workflow / infra
- **Summary** — one paragraph
- **Rationale** — why, and what failure mode drove it
- **Downstream effects** — what files / workflows / conventions were touched

Older platform history pre-dating this changelog lives in `PHASE*_BRIEFING.md`
at the repo root and in the git log.

---

## 2026-04-19 — Dashboard HTML archived under outputs/daily/
**Commit:** (pending)
**Scope:** infra (`gt/orchestrator.py`, `infra/send_email.py`), convention.

Every capture run now writes the email-style consolidated dashboard HTML
to **both**:
- **Root `email_fallback.html`** (gitignored, latest-run scratch / ad-hoc
  send fallback) — unchanged behavior.
- **New: `outputs/daily/YYYY-MM/MM-DD/dashboard_YYYY-MM-DD_HHMMET.html`**
  (git-tracked, dated archive) — one file per capture.

Applies to both the orchestrator's in-run render and `infra/send_email.py`
ad-hoc renders.

**Rationale:** the 2026-04-19 email-step drop moved the narrative brief
into Git but left the consolidated visual-dashboard view (price-series
table, full RED/AMBER enumeration, binary events countdown, health panel)
gitignored at root. The dated archive preserves that view per capture
alongside the brief, so future VL audit can reconstruct "what the platform
was displaying at time T" without the Google Sheets tab history.

**Downstream:**
- `gt/orchestrator.py` stage 6 renamed EMAIL → DASHBOARD, with
  `_archive_dashboard_html()` helper.
- `infra/send_email.py` `_archive_dashboard()` helper mirrors the logic.
- `docs/workflows.md` on-demand-dashboard note remains accurate.
- Storage cost: ~50 KB per capture × 2-4 captures/day × 365 days ≈ 60 MB/yr.
  Acceptable for a private repo archive.

---

## 2026-04-19 — Email step dropped from capture workflow
**Commit:** (pending)
**Scope:** workflow, convention.

Capture workflow reduced from 4 steps (capture → brief → ledger → email)
to 4 steps with email replaced by `git commit + push`:
1. Capture (`python infra/run_manual.py`)
2. Brief (hand-written consolidated sector brief)
3. Ledger (append findings to `alpha_ledger.md`)
4. Commit + push to GitHub

**Rationale:** email was solving a mobile-delivery problem that Git +
GitHub mobile now solve more cleanly. Gmail OAuth token maintenance is
recurring friction (expired during 2026-04-19 PM capture, required
manual re-auth). The email's consolidated dashboard view is recoverable
on-demand via `python infra/send_email.py` writing `email_fallback.html`
locally, so the capability is not lost — it's unbundled from the
standing workflow.

**Downstream:**
- `memory/feedback_brief_workflow_sequence.md` updated to step-4 =
  commit+push, with "on-demand dashboard" footnote for ad-hoc rendering.
- `docs/workflows.md` updated with the new daily-capture sequence.
- `send_email.py` code untouched — remains available as an ad-hoc tool.
- No net loss of capability: brief content (step 1) ✓ git, signals +
  prices + binary events (email sections 5/6/9) ✓ Google Sheets tabs,
  health panel (email section 10) ✓ console + Sheets Health tab,
  consolidated dashboard ✓ available on-demand.

---

## 2026-04-19 — Documentation system formalized
**Commit:** (pending)
**Scope:** documentation, memory, repository structure.

Created `docs/` folder to hold non-code documentation (this changelog,
conventions, workflows). Added `memory/feedback_documentation_discipline.md`
recording the discipline rules. Added a one-line pointer to `docs/` in
`CLAUDE.md` COMPANION FILES section.

**Rationale:** fixes / schema changes / convention shifts accumulated across
the Apr 19 session with no central place to document them. Commit messages
alone are insufficient for cross-referencing ("which fix changed the scorer
to v2.3.0?" is legible; "what conventions does the platform follow right
now?" previously was not).

**Downstream:** `docs/README.md`, `docs/CHANGELOG.md`, `docs/conventions.md`,
`docs/workflows.md`, `memory/feedback_documentation_discipline.md`, MEMORY.md
index updated, CLAUDE.md companion section updated.

---

## 2026-04-19 — Chronological outputs reorganization
**Commit:** `1cfcf55`
**Scope:** file-system layout, convention.

Moved all `outputs/` files into a chronological hierarchy:
- Daily captures → `outputs/daily/YYYY-MM/MM-DD/sector_briefs_*.md`
- Weekly Sunday bundle → `outputs/weekly/YYYY-MM/MM-DD/*.md`
- `alpha_ledger.md` and `alpha/` stay at `outputs/` root as the always-current
  contemporaneous-record anchors.

All 33 files moved as `git mv` (history preserved, 100% rename detection).

**Rationale:** as the archive grows (multi-month retention for VL tracking),
flat `outputs/` becomes unnavigable. Chronological structure matches how
briefs will be looked up ("pull up the DC sector alpha from early April").

**Downstream:**
- `gt/email_builder.py._find_latest_brief_for_today()` glob changed to
  recursive pattern (`outputs/**/sector_briefs_*.md`) so email Section 1
  continues to embed today's brief under the new subtree.
- `infra/run_manual.py` help text updated to new path convention.
- `docs/conventions.md` documents the layout as canonical.

---

## 2026-04-19 — Weekly sector-alpha brief cadence established
**Commit:** `301de77` (bundled with classifier recalibration).
**Scope:** convention, workflow.

Every Sunday: produce a sector-level alpha brief for each of the three core
sectors (DC, Power, LNG). Format follows a consistent 8-section template:
sector state, the sector alpha, secondary alphas / pending ALF hardening,
drift-check, at-threshold watch items, silence-that-matters, cross-asset
spillover, sector-level action items, one-line summary.

**Rationale:** the GR weekly brief (Apr 14 prior pattern) mixed sector-level
analysis with deal-specific exposure. Splitting the deal overlay into a
separate file and the sector-alpha read into three sector files (one per
sector) produces a cleaner analytical artifact that stands alone when pulled
up months later for VL audit.

**Downstream:**
- `outputs/weekly/YYYY-MM/MM-DD/` now expects: `GR_Brief_*.md` (weekly
  research), three `<Sector>_Sector_Alpha_*.md` files, and overlay/amendment
  files as needed.
- `docs/conventions.md` documents the template.
- `docs/workflows.md` documents the Sunday procedure.

---

## 2026-04-19 — Scorer v2.3.0: structural-candidate lane
**Commit:** `301de77`
**Scope:** code (`ge/scorer.py`), schema (`gs/classify.py`).

Added a structural-candidate scoring lane triggered by this week's miss of
a pre-issuance ILS → DC-finance thread (7 Artemis prints decayed at GREEN
across Apr 13-18; see `alpha_ledger.md` ALF-20260419-1).

Three additions, all in the boost budget (raw-score invariant preserved):
1. **Regime weights extended** — C16 (Struct), C17 (Siting-State), C18
   (RatingMethod) added to all regime maps. R0: 1.4/1.3/1.3. R2 (credit
   stress): 1.5/1.2/1.5 — structural finance most relevant there.
2. **`score_cluster_amplifier`** — +5/sibling-with-same-structural-tag, cap
   +20. Catches pre-issuance ladders that no single print elevates.
3. **`score_structural_keyword_bonus`** — per-phrase flat additive points
   for IG-uplift / rating-methodology / first-in-class / capital-pool
   language. Cap +15. 22 phrases in the config dict.

**Rationale:** the classifier was tactically weighted (price-moving, crisis-
framed, deal-matched signals elevated). Structural signals that don't carry
a price number and don't match a deal kept scoring GREEN despite structural
importance. The new lane elevates them without distorting the non-structural
distribution.

**Downstream:** scorer version bumped 2.2.0 → 2.3.0. `TUNING_HISTORY` entry
added. Distribution impact on the real 7-day window: +3 signals AMBER,
surgical (0.5% shift). Top GREEN stays at honest 45.0 boundary.

---

## 2026-04-19 — Classifier schema: C16 / C17 / C18 + abbreviation matcher
**Commit:** `301de77`
**Scope:** code (`gs/classify.py`), schema.

Added three C-tags plus a word-boundary abbreviation matcher.

- **C16 (Struct)** — structured finance / ILS / cat bond / sidecar / IG
  uplift. 17 multi-word keyword patterns.
- **C17 (Siting-State)** — state-legislative siting restriction / moratorium
  / bit-barn ban. 16 keyword patterns.
- **C18 (RatingMethod)** — rating agency methodology / credit rating
  events. 12 keyword patterns.
- **`C_TAG_ABBREVS`** — word-boundary regex matching for distinctive short
  abbreviations (ILS, PCC, KBRA, DBRS, IG). Prevents substring collisions
  like `"ils"` in `"hails"`.
- **`C_TAG_NAMES`** — semantic-name map surfaced in UNMAPPED diagnostics
  so `c_tags=[C11 (Digital), C16 (Struct)]` replaces opaque numbers.

**Rationale:** the week's missed ILS ladder had no C-tag to cluster under —
the schema literally did not recognize structured-finance signals as a
discoverable category. Adding the tags unlocks cluster queries for the GR
weekly workflow and feeds the new structural-candidate scoring lane.

**Downstream:** existing C-tags untouched (no regression risk). Pre-existing
substring collision on C02's `"sec"` keyword flagged but deferred (fix
pattern identical — move to abbreviation matcher).

---

## 2026-04-19 — `second_order` template fallback removed
**Commit:** `301de77`
**Scope:** code (`gs/classify.py`).

Removed the silent template fallback where
`MECHANISM_TEMPLATES[c_tag]` was emitted as the primary `second_order`
text whenever any of the signal's c_tags had a template registered. The
template-as-analysis behaviour made every Artemis signal this week stamp
*"Federal regulatory action affects permitting timelines..."* regardless
of content.

New behaviour:
- If `matched_deals` exists (only current signal-specific inference path),
  emit `"Direct pipeline exposure: X via Y on Z timeline..."` with an
  explicit `Mechanism: UNMAPPED` note.
- Otherwise emit `"UNMAPPED — classifier produced no signal-specific
  mechanism. c_tags=[...], source='...', ..."` with diagnostic context.

`MECHANISM_TEMPLATES` dict retained in module as dormant reference for
future signal-specific inference logic.

**Rationale:** templated output that looks like analysis is actively worse
than admitting "mechanism unclear" — it masked the 7-print ILS thread by
making mis-reads look considered. UNMAPPED count becomes a quality metric
for GR weekly review.

**Downstream:** email / digest / sector-brief modules display the UNMAPPED
text as-is — graceful degradation. Price-module-authored `second_order`
strings (curtailment / BESS / scarcity) are unchanged (they compose from
actual price logic, not templates).

---

## 2026-04-19 — Additive c_tag backfill + selective rescore rollback
**Commit:** `301de77`
**Scope:** infra (`infra/backfill_ctags.py`, `infra/rollback_rescore.py`).

New utilities:
- **`backfill_ctags.py`** — re-classifies stored signals under the current
  classifier and UNIONs new tags with existing (never removes). Optional
  `--rescore` also persists v2.3.0-scored `alert_level` / `weighted_score`,
  preserving originals in `verification_note` as
  `[backfill:2026-04-19-fix2] orig_alert=X orig_weighted=Y`.
- **`rollback_rescore.py`** — selectively reverts a prior rescore pass.
  Restores original alert levels for signals that did NOT gain structural
  tags (C16/C17/C18), keeping v2.3.0 elevation for signals the new lane
  was designed to help.

**Rationale:** the full-week rescore overreached — novelty component saw a
larger sibling context than the original daily-batch context, causing
hundreds of collateral score shifts unrelated to v2.3.0. Selective
rollback restores the contemporaneous record for non-structural signals
while keeping structural elevation intended.

**Outcome:** 49 signals gained c_tags additively (persisted). 28 signals
kept the new alert_level (only the ones C16/C17/C18 was designed to help).
218 signals restored to original live scoring with provenance stripped.

**Downstream:** `docs/workflows.md` documents when / how to run each
utility. Provenance tag `backfill:2026-04-19-fix2` traceable via
`classifier_model` field.

---

## 2026-04-19 — Health panel recalibration (5 checks)
**Commit:** `301de77`
**Scope:** code (`infra/health_monitor.py`, `gt/orchestrator.py`),
calibration.

Five health-panel checks were miscalibrated relative to the actual
operating model, producing 7/18 FAILING consistently across runs despite
the platform itself operating correctly. All five fixed in one pass:

| Check | Before | After |
|---|---|---|
| **GS-1 Fetch Coverage** | 16/18 (hardcoded 18-source denom) | proportional (35/37 95% AMBER) |
| **GS-3 Relevance Filter** | 90% RED (dedupes conflated with irrelevance) | 5-40% target on fresh-only denominator; AMBER when nothing fresh after dedupe |
| **GE-1 Alert Distribution** | fixed bands assumed crisis regime | regime-conditional (R0-R4 each with own bands) |
| **GE-2 Deal Match Rate** | ≥40% target (contradicted deal-free brief policy) | 5-30% target |
| **GPi-2 HOT Detection** | 0 HOT = RED always | 0 HOT = GREEN in R0-R2 (expected baseline), RED only in R3-R4 |
| **GT-1 Email Delivery** | "failed: unknown" RED in split workflow | GREEN with "deferred" note when `email_deferred=True` |

Plus `gs/classify.py.classify_batch` now returns
`(signal_ids, stats_dict)` splitting `dedupes` / `filtered` / `classified`
/ `errors` so the orchestrator can plumb accurate counts into RunContext.

**Rationale:** the panel was consistently lying about system health. Each
failing check told a false story — filter rate misclassified as broken,
alert distribution miscalibrated to a crisis floor, deal-match rate
contradicting the platform's own operating policy.

**Outcome:** 7/18 FAILING (39%) → 15/18 HEALTHY (83%). Remaining AMBERs
are now honest.

---

## 2026-04-18 — v2.2.0 baseline
**Commit:** `e3ebee1` (pre-existing)
**Scope:** baseline commit, platform v2.2.0.

Multi-agent capture pipeline established. Scorer v2.2.0 (source-type-
confidence recalibration, AMBER threshold 48→45). Full sector brief
cadence at daily capture level. Alpha ledger discipline operational.
Eight agents per CLAUDE.md architecture section. See
`SESSION6_SUMMARY.md` for session-level narrative.

Earlier phase history: `PHASE1_PROGRESS.md` through `PHASE6_BRIEFING.md`.
