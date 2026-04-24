# Sector Brief Template — v2 (readability-oriented)

Supersedes the v1 template (implicit in captures through 2026-04-24).
v2 adds a top-of-brief executive card, enforces inverse-pyramid on the
"what matters" paragraphs, and compresses the low-signal repeat sections
into a footer.

**Target total read-time:** 5-7 minutes (vs v1's 15-25). Deep-read
remains available for anyone who wants to drill into the full analysis.

---

## Structure

### (1) HEADER — one line

```
GROUNDTRUTH SECTOR BRIEFS — {DATE} {TIME} ET ({SLOT})
R{N} {regime-name} Day {N}  |  Book: {R}/{A}/{G}  |  Captured: {N} new signals
```

### (2) EXECUTIVE CARD — 30-60 second read

A five-block panel at the top. Every brief has it; every brief has it
in the same order. Readers can scan in under a minute and decide
whether to read deeper.

```
================================================================
EXECUTIVE CARD
================================================================

TAPE TONE       : {one line, ≤8 words, regime-feel}
MATCHER         : {encyclopedia top + % + consecutive-captures note}

WHAT CHANGED (vs last brief):
  • {delta-framed bullet: what moved, how much, why it matters}
  • {up to 5-6 bullets; lead with magnitude, not context}

WHAT'S BINDING NEXT:
  • {specific next data point + which ALF it settles}
  • {3-5 items max; concrete date or event}

IF YOU ONLY READ ONE THING:
  {one sentence — the single most-action-relevant takeaway}

================================================================
```

### (3) WHAT MATTERS — inverse-pyramid, 3-5 paragraphs

Rule: each paragraph **leads with the bottom line in bold**, then the
evidence. No paragraph starts with context-setting; the context follows
the claim.

Before (v1):
> "First thing. SMH $504.94 — session-level +4.8% move from AM pre-open
> $481.85, firing 7d +11.47% breach (NEW first 7d SMH breach) on top of
> 30d +30.1% (expanded from AM's +20.15%), and the merchant-power cohort
> is coupling hard to the AI-narrative beta for the first time at
> session-scale..."

After (v2):
> **1. W2 trifurcation thesis fires at session-scale for first time —
> proposed for Sunday promotion to active ALF.** SMH +4.8% session /
> 7d +11.47% (NEW breach) with merchant cohort coupling (VST +4.4%, CEG
> +5.3%, TLN +5.1%, NRG +2.7%). KRE / ICLN / XLE not coupling = pure
> AI-factor rotation, not sector rally. This is the cleanest confirming
> data point for the merchant-power lead-lag deep dive thesis (Thu
> 1430ET) — intraday beta coupling at session cadence. Sunday weekly
> review decision is whether to promote to active ALF-20260424.

Each paragraph: ≤120 words. Maximum 5 "what matters" paragraphs.

### (4) FRAMEWORK COVERAGE SCAN — compact axis-by-axis

Retain the 15-axis scan but **only for axes that fired or changed
materially this capture.** Axes that are QUIET compress to a single
footer line. Hardening notes move to the Alpha-ledger section below.

Format per firing axis:
```
{Axis label} — {what fired, one sentence}  [GS-NNNN, score]
```

### (5) PRICES TABLE — reduced

Keep the table but drop:
- Rows that moved <0.5% and haven't breached.
- Context rows that restate the last brief.
- GPU table expands only if a material move fired.

Add a single-line summary above the table: "PRICES: {headline direction}.
Breaches: {N}. See table for full deltas."

### (6) SECTOR SECTIONS — LNG / POWER / DC

Retained, but each opens with **TL;DR** (1-2 sentences on what this
section establishes this capture) before the axis detail. If nothing
non-trivial fired in a sector, collapse to a single line: "LNG — quiet;
see Axis 3 carry-forward."

### (7) MACRO OVERLAY — unchanged

Bullet list of non-sector macro signals. Keep as-is.

### (8) ALPHA LEDGER — per-ALF, compressed

Each active ALF and Watch item gets a **one-paragraph update** with a
mandatory structure:
- Status line (PENDING / HIT / WRONG / EARLY / LATE)
- What fired this capture (if anything)
- Probability-weight change (if any)
- Next binding data point

If no change since last capture: "ALF-{X} — no change. See prior."

Candidate ALF Watch items get the same treatment but shorter.

### (9) PENDING ALF STATUS TABLE — table form

All active ALFs in a single table with columns:
Status | ALF | Type | Last update | Probability weights | VL | Binding next

Drop the prose per-ALF list. Table is scan-able in seconds.

### (10) FOOTER — one paragraph

Collapses System Status + Data Hygiene + Named-deal discipline into a
single paragraph unless a flag fires. If a flag fires, it gets its own
line.

Format:
```
FOOTER: {runtime}s | {signals new/R/A/G} | GS-coverage {N/N} | {flags if any}
  | Encyclopedia top E{N} {%} ({N}-consecutive-capture hold)
  | Dashboard: {path} | Named-deal check: CLEAN
```

### (11) TAPE TONE (EOD only)

Retained. One line, four words max, on the last brief of each day.

---

## Inverse-pyramid paragraph template

Each "what matters" paragraph:

```
**{bottom line in bold, one sentence, ≤25 words}.** {2-3 sentences of
evidence and magnitude — what prints drove it, what the numbers are,
what the mechanism is}. {1-2 sentences on cross-link — which ALF or
axis or prior observation this connects to, and what's changed in the
framework read}.
```

Explicitly **not** allowed:
- Starting a paragraph with context-setting or background.
- Multi-claim opening sentences that bury the punchline.
- Framework re-explanation inside the paragraph (glossary handles it).

---

## Glossary integration

All jargon resolves via `docs/glossary.md`. First use in a brief gets
no inline definition — the glossary is always available. This is the
same convention as the encyclopedia references.

If a new term enters active use, add to glossary same-commit as the
first brief that uses it.

---

## Migration approach

v2 takes over starting the next capture after Sri approves. v1 briefs
remain committed as-is (no retroactive edits per discipline memory).
Mixed v1/v2 briefs in the same day are fine during transition.

The first v2 brief should additionally carry a small "(v2 format —
executive card + inverse-pyramid + glossary integration)" label in
the header, so future readers know which template was in use.

---

## What's lost in v2

Being honest about the tradeoff:

- **Single-brief context for first-time-readers** — v1 repeated framework
  context so each brief was standalone. v2 requires the glossary to be
  available.
- **Drift-check visibility** — Named-deal discipline, temporal causality,
  data hygiene all get compressed to a footer. If a flag fires, it still
  gets surfaced, but the routine scan is less visible.
- **Coverage-scan completeness** — QUIET axes compress to a footer line.
  A reader cannot at a glance confirm that all 15 axes were scanned —
  they have to trust the discipline.

These are the trades for a 5-7 minute read vs 15-25. Net-positive if
the deep-read is still available (which it is, via the full axis
detail sections and the full-prose prior-brief history).
