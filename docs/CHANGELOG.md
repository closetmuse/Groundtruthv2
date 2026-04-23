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

## 2026-04-23 — GPU compute price tape added (Vast.ai spot + Kalshi forward)
**Commit:** (this commit)
**Scope:** code / schema — four new price series in `gs_price_snapshots`,
activating DC Axis 5 (GPU financing) which was previously QUIET by default.

Added `fetch_gpu_prices()` to `gs/prices.py`, wired into `run_price_fetch()`
after fuel-mix, and added THRESHOLDS entries. Four new SKUs tracked:
`gpu_h100_sxm_usd_hr`, `gpu_h200_usd_hr`, `gpu_b200_usd_hr`,
`gpu_a100_sxm_usd_hr`. First-observation Thu AM 2026-04-23 captured
H100 SXM $1.87, H200 $4.58, B200 $3.94, A100 SXM4 $0.85.

**Sources.** Free public endpoints — no auth, no API key.
- **Spot:** `console.vast.ai/api/v0/bundles` GET with JSON search query
  in `?q=` param. Filter `verified=True, rentable=True, rented=False,
  type=on-demand`. Per-GPU-hr = `dph_total / num_gpus`; record p25 / p50 /
  p75 across the marketplace for each SKU. p50 is the snapshot `value`.
- **Forward (ladder midpoint, liquidity flag):** Kalshi monthly-price
  series KXH100MON / KXH200MON / KXB200MON / KXA100MON. 40 strikes per
  series in "Above $X" form. Midpoint of the strike range is the
  recorded forward anchor; volume field captures liquidity state. Volume
  was 0 across all four markets at first capture — ladder presence is
  structurally useful even without liquidity because liquidity is
  expected to develop and the schema is already in place.

**Rationale.** Sri flagged GPU compute lease rates as a missing tape
2026-04-23 post-AM-brief. Ornn OCPI (Bloomberg, paid) and Silicon Data
($499/mo base) are the institutional-grade options; access procurement
deferred pending SC Bloomberg-terminal path. Vast.ai + Kalshi are
free, API-clean, and reference real marketplace transactions — Vast.ai
is actual cleared marketplace prices, Kalshi is CFTC-regulated and
Ornn-OCPI-settlement-referenced. Together they cover spot + forward
without subscription cost. When Bloomberg/Silicon Data access lands the
fetcher can be extended in place rather than rewritten.

**Schema extras.** Each GPU row carries extra snapshot fields beyond the
standard price schema: `vast_p25`, `vast_p50`, `vast_p75`,
`vast_n_offers`, `kalshi_fwd_mid`, `kalshi_strikes`, `kalshi_volume`.
These ride the existing JSON `series_data` column — no SQL migration.

**Thresholds.** 10%/20% bands for H100/H200/A100, 15%/25% for B200
(smaller marketplace, noisier series expected). Same `pct` type as HH /
JKM / TTF.

**Downstream effects.** `gs/prices.py` (fetcher + wire-in + THRESHOLDS);
no changes to brief schema, dashboard, or email builder — new fields
appear in snapshots and will surface in delta/breach detection from
next capture. Integration tested against temp-DB 2026-04-23; deltas
return None on first observation as expected, no spurious breaches.

---

## 2026-04-22 — Encyclopedia E09 added (Infrastructure Overbuild Collapse)
**Commit:** (this commit)
**Scope:** schema / content — encyclopedia expansion from 8 → 9 anchor events.

Added `encyclopedia/E09_InfraOverbuild.md` — combined entry covering the
dot-com fiber overbuild (1998-2002) and the merchant power overbuild
(1999-2003). Both sub-cases share the same fundamental mechanism
(demand-projection-driven capex → generic-merchant financing → revenue
collapse when capacity commissions faster than demand growth) and had
co-incident peak stress in 2002 (WorldCom Chapter 11 anchors the
fingerprint date 2002-07-21).

Primary regime R3 (sectoral demand shock); secondary R2 (sector-specific
credit cascade). Pattern match C-tags: C11, C12, C05, C14, C15.

**Rationale.** Flagged by Sri 2026-04-22 as essential historical
precedent for reasoning about the current DC-power build-out cycle.
Woodmac senior bank/IB dinner 2026-04-21 surfaced the parallel. Both
episodes produced the "generic-merchant is near-unfinanceable" discipline
that held from ~2003 through the mid-2010s; relevant as a precedent
when the merchant-DC-hopeful vs hyperscaler-anchored bifurcation (W2)
is actively sorting credit in real time.

**Downstream effects.**
- `encyclopedia/E09_InfraOverbuild.md` — new file.
- `CLAUDE.md` line 152 — "8 anchor events" → "9 anchor events (E09 infrastructure overbuild added 2026-04-22)".
- Encyclopedia matcher (`gi/encyclopedia.py`) auto-picks up the new file (directory-scan pattern, no code change required).
- Future captures will score the E09 fingerprint against live market state; Wed AM decoupling-direction prints (metals bounce + JKM firming) partially rhyme with E09 sector-specific-not-broad-credit signature — next capture will be the first E09-scored read.

**Flagged for Sri review.** Section 5 "practitioner notes" contains a
placeholder pending Sri validation. The core lesson (contracted off-take
as the binding survive-vs-default sort) is articulated from the
Moody's default data but the Sri-voice practitioner notes on specific
1999-2003 desk experience remain to be added.

---

## 2026-04-21 — Reclassify 2026-04-20 addendums as deep dives
**Commit:** (this commit)
**Scope:** convention (retroactive reclassification).

Moved both 2026-04-20 addendum files from the day folder to
`outputs/deep_dives/` and renamed with the `deep_dive_` prefix:

- `addendum_2026-04-20_0645ET_vg_cp2_waiver.md`
  → `deep_dives/deep_dive_2026-04-20_0645ET_vg_cp2_waiver.md`
- `addendum_2026-04-20_2115ET_dpa_burgum.md`
  → `deep_dives/deep_dive_2026-04-20_2115ET_dpa_burgum.md`

**Rationale.** Both files are Sri-flagged thematic deepenings of specific
brief topics — substantively they fit the deep-dive pattern better than
the addendum pattern (addendums are time-bound same-capture corrections
or follow-ups; these two expanded into multi-mechanism cross-axis reads
that persist beyond their originating capture). The deep-dive convention
landed later the same morning (2026-04-21); these pre-existed the
convention and are being retroactively sorted.

**Edits.** Header line swapped from `GROUNDTRUTH — ADDENDUM` to
`DEEP DIVE — <topic>`. Added a reclassification note to each header.
Parent brief reference preserved. Body content unchanged — git mv
preserves file history.

**Not edited.** The 2026-04-20 committed briefs themselves — per
`feedback_no_retroactive_brief_edits` memory, briefs stay frozen. The
briefs' internal references to "addendum_..." filenames are now
historically stale but remain accurate as-of-commit-time, which is the
contemporaneous-record discipline.

---

## 2026-04-21 — Deep dive convention: `outputs/deep_dives/` thematic series
**Commit:** (this commit)
**Scope:** convention / workflow.

Introduced a new output class — **deep dives** — distinct from addendums.
Filename: `deep_dive_<YYYY-MM-DD>_<HHMM>ET_<topic-slug>.md`. Folder:
`outputs/deep_dives/` at the same level as `outputs/daily/` and
`outputs/weekly/`.

**Why distinct from addendums.** Addendums are post-commit expansions to
a specific brief in the same day folder — time-bound, same-day, freeze
contemporaneous-record discipline preserved (per
`feedback_no_retroactive_brief_edits` memory). Deep dives are thematic,
flagged by Sri post-brief, and not tied to a single day's tape.
They carry a single topic across sectors / axes / timelines and
accumulate substrate toward candidate-future-ALFs without opening them
prematurely.

**What goes in a deep dive.** (1) What the tape said + source refs to
the originating signal(s). (2) Why now — structural pressures. (3)
Mechanism / timeline / asset-specificity per Transmission Mechanism
Rule. (4) US project-finance-specific implications (Sri's domain).
(5) Cross-axis threading. (6) What to watch next 30-90 days. (7)
Alpha-ledger positioning — typically not opening an ALF today, but
flagging substrate-accumulation for existing ALFs or forward-candidate
ALFs.

**Workflow.** (a) Sri flags topic post-brief. (b) Write deep dive into
`outputs/deep_dives/`. (c) Commit same-session. (d) Deep dives may
cross-reference each other and back to briefs; briefs do not reference
deep dives (briefs freeze contemporaneous; deep dives are later
interpretation).

**First deep dives shipped this commit.**
- `deep_dive_2026-04-21_0730ET_uk_gas_power_delink.md` — UK Miliband
  gas-power delink proposal with US state power-market implications.
  Flagged from AM brief 0515ET (GS-1264 / GS-1297).
- `deep_dive_2026-04-21_0745ET_oil_gas_hub_dc_siting.md` — oil-gas-hub
  DC siting locational thesis with ALF-19-1 and candidate-W2
  implications. Flagged from AM brief 0515ET (GS-1290 Bisnow).

**Downstream effects.**
- New folder `outputs/deep_dives/`.
- `docs/conventions.md` updated with deep-dive naming convention and
  delineation vs addendum.
- `docs/workflows.md` updated with Sri-flagged deep-dive workflow.

---

## 2026-04-20 — Relevance-gate whitelist: utilities, privatisations, named EU/LNG entities
**Commit:** (pending)
**Scope:** code (`gs/classify.py`).

Added three term groups to `INFRASTRUCTURE_TERMS` (the gate at
`is_infrastructure_relevant` that runs before classification and scoring):

1. **Asset-class term** — `"utility"`, `"utilities"`. The word appeared in
   another function's `infra_anchors` list (line ~628) but was missing from
   the primary relevance gate. Utility Dive is a named high-trust F-tagged
   source; stories whose summary uses "utilities" without also saying "power"
   or "grid" were being filtered at the gate despite obvious relevance.
2. **Corporate-structural terms** — `privatisation/privatization/privatise/
   privatize`, `state-owned`, `soe`, `capital increase`, `capital raise`,
   `rights issue`, `ipo`, `secondary offering`, `share offering`,
   `nationalisation/nationalization`. These describe financing or ownership
   events on infrastructure entities; thin FT-style paywalled summaries
   often omit commodity keywords entirely.
3. **Named infra-adjacent entities** — `gazprom`, `sefe`, `uniper`, `naturgy`,
   `equinor`, `engie`, `iberdrola`, `enel`, `rwe`, `e.on`, `fortum`,
   `venture global`, `vg`, `cheniere`, `freeport lng`, `bechtel`, `technip`,
   `fluor`. EU gas utilities, US LNG pure-plays, and major EPC contractors.
   Catches thin-summary stories where the only on-axis clue is the entity
   name (today's SEFE/FT Energy case is the canonical example).

**Rationale.** Run-1 (2026-04-20 05:22 ET) filter audit flagged two clear
misses: GS-1104 FT Energy "Germany to begin privatisation of seized
Gazprom division" and GS-1099 Utility Dive "The single-platform utility: A
competitive advantage in the age of AI." Both scored 0.0 because they
never reached the scorer — the gate filtered them on "No infrastructure
terms found." GS-1104's sister print GS-1114 (Oil Price, same story) went
AMBER 51.66 because Oil Price's summary happened to include the words
"energy" and "infrastructure." Same news, two different outcomes, entirely
due to whose wire summary we happened to get — a source-path dependency
that has nothing to do with signal relevance.

**Regression check (8 cases, all correct):**
- GS-1104 (SEFE/FT) → PASS (was FILTER)
- GS-1099 (Utility Dive) → PASS (was FILTER)
- GS-1143 Kenyan fishing → FILTER
- GS-1133 G4 Capital RE → FILTER
- GS-1108 FT stablecoins → FILTER
- GS-1137 DOJ Kambli → FILTER
- GS-1092 Al Jazeera school (hard-exclusion path) → FILTER
- Synthetic VG merchant cargo → PASS

**Downstream effects.**
- `gs/classify.py`: +15 terms in `INFRASTRUCTURE_TERMS`. No change to
  `HARD_EXCLUSIONS`, no change to gate logic, no change to scorer.
- One-time effect: on next capture, previously-filtered stories of this
  class will start reaching the classifier and scorer. Expect modest
  uptick in AMBER count from FT Energy / Utility Dive / LNG Prime; RED
  count is unlikely to move because classifier still has to assign C-tags
  and scorer still has to meet the RED threshold.
- Historical records unchanged. Filtered signals stay filtered in the DB.

**What's NOT in this change.**
- Source-aware gating (FT/Utility Dive/LNG Prime get relaxed gate, FT
  Markets generic stays strict). Deferred — medium-sized change requiring
  source-trust map integration into the gate.
- Dropping the keyword gate entirely for named-infra sources (F6/F7/F8/F16).
  Deferred — bigger design decision; current approach keeps the gate as a
  backstop against classifier over-triggering on trust-weighted sources.

---

## 2026-04-20 — LNG benchmark staleness: business-day cadence + next-settlement field
**Commit:** (pending)
**Scope:** code (`gs/prices.py`).

`fetch_yahoo_lng` now reports JKM and TTF staleness on a business-day basis
instead of calendar-day. The `stale` flag fires when `business_days_stale > 1`,
i.e., when a settlement that should already exist is missing — not when the
weekend is carried forward. Two new fields ride on each LNG series:
`business_days_stale` and `next_expected_settlement`.

**Rationale.** On the 2026-04-20 06:46 ET capture, JKM read $15.00 with a
calendar-day staleness of 3 and `stale: false` (prior threshold was `> 3`).
That misrepresented the data state: Yahoo's $15.00 Friday close is the latest
JKM settlement that exists in the world at Monday AM because CME JKM settles
once per business day after the Asian session closes. Calendar-day math
treated weekend carry as data lag; business-day math correctly reads Mon AM
with Fri-close as within-cadence. The brief body flagged the confusion
explicitly ("JKM tape did not refresh") — the fetcher should not contribute
to that confusion.

**What changed semantically:**
- Mon AM, Fri-close JKM → `business_days_stale=1`, `stale=False`, console
  prints `(next settle 2026-04-20 pub later today)`.
- Tue AM, Fri-close JKM → `business_days_stale=2`, `stale=True`, console
  prints `STALE(2bd — expected 2026-04-20 settlement missing)`. This is the
  case where a settlement we expected to see did not arrive.
- Backward-compat: `staleness_days` (calendar days) and `stale` still written
  to the series dict. `email_builder.py` and `sheets/interface.py` continue to
  read the old fields unchanged; their calendar-day thresholds remain as-is
  for now (candidate for later revisit under the broader per-series staleness
  audit, i.e. Option C from today's discussion).

**Downstream effects.**
- `gs/prices.py`: added `_business_days_between` and `_next_business_day`
  helpers; `fetch_yahoo_lng` populates four new fields on each LNG dict
  entry (raw + derived TTF-USD); updated console output messages.
- Brief rendering can now cite `next_expected_settlement` to explain JKM
  cadence honestly instead of saying "stale 3d."
- No schema change — series_data stays JSON blob, just with richer keys.

**What's NOT in this change.**
- No new JKM data source. Free alternatives (CME JSON, ICE JSON, Barchart,
  MarketWatch) all block automated access; paid feed (Platts/LSEG/ICE) is
  a subscription decision, not a code change. The JKM cadence gap at AM
  captures is a market-structure fact, not a fetch bug — this change makes
  that explicit in the data rather than masking it.
- No audit of oil / gas / FX / FRED series staleness. Those sit behind their
  own thresholds (`_fetch_yahoo_futures` stale > 2; FRED no explicit flag).
  Each has its own cadence; scope is today's discussion Option A only.

---

## 2026-04-20 — Marker-enforced capture workflow (`finalize_capture.py`)
**Commit:** (pending)
**Scope:** infra (`infra/run_manual.py`, new `infra/finalize_capture.py`),
workflow (`docs/workflows.md`), CLAUDE.md trigger phrase, memory consolidation.

"Run GroundTruth capture" is now a **three-command** sequence, with state
flowing through a `.gt_capture_pending` marker file at project root:

1. `python infra/run_manual.py` — capture; writes marker with the exact
   brief filename, slot, signal counts, precedent, runtime.
2. Claude writes the sector brief to the exact path from the marker.
3. `python infra/finalize_capture.py --headline "<theme>"` — verifies the
   brief, git-adds day folder + `outputs/alpha_ledger.md` (if modified),
   commits with auto-generated message, clears the marker. No push.

**Rationale.** Memory-based workflow instructions were drifting across
fresh sessions — the AM capture on 2026-04-20 wrote the brief but left
it uncommitted until Sri reminded me, then was over-corrected (full
brief pasted into chat) and followed by a contemporaneous-record
violation (retroactive edit of the committed brief to expand the VG
waiver section). Root cause: memories are advice that a new session
loads but may skip; they cannot enforce a workflow. The marker file
pushes the protocol into the bash layer — Claude cannot "forget" to
commit because the finalize script IS the commit, and a new session
that sees a marker at project root knows a brief is pending.

**Downstream effects:**
- `infra/run_manual.py` — adds `_write_pending_marker()` + NEXT STEP
  block; consumes `top_precedent` from summary.
- `infra/finalize_capture.py` (new, ~180 lines) — marker read, brief
  verification, git add/commit, idempotent on re-runs.
- `.gitignore` — adds `.gt_capture_pending`.
- `CLAUDE.md` — "Run GroundTruth capture" trigger phrase rewritten as
  the three-command sequence with addendum + no-paste rules.
- `docs/workflows.md` — daily capture procedure section rewritten;
  push cadence flipped from "after every commit" to manual / hold-local.
- Memory consolidation: four overlapping feedback files
  (`feedback_brief_workflow_sequence.md`, `feedback_show_brief_after_write.md`,
  `feedback_brief_git_commit_protocol.md`, and the old workflow fragment
  inside `feedback_documentation_discipline.md`) merged into a single
  `feedback_capture_workflow.md` pointing at the script flow.
  `feedback_no_retroactive_brief_edits.md` retained as a separate
  content-discipline rule.

**Hold-local push protocol.** `finalize_capture.py` never pushes.
Sri decides when to `git push`, typically at EOD or after a review pass.
The old "push after every commit" rule in `docs/workflows.md` is
superseded by this entry.

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
