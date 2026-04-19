# GroundTruth V2 — Conventions

Canonical reference for output paths, file naming, cadence, schema, and
ledger protocol. When a convention changes, update this file in the same
commit as the code change, and log the change in `CHANGELOG.md`.

---

## Output paths

All generated content lives under `outputs/`.

### Daily captures (multiple per day possible)
```
outputs/daily/YYYY-MM/MM-DD/sector_briefs_YYYY-MM-DD_HHMMET.md
```

- **YYYY-MM** — month folder for archive browsing (e.g. `2026-04`)
- **MM-DD** — day folder inside the month (e.g. `04-19`)
- **`sector_briefs_YYYY-MM-DD_HHMMET.md`** — the consolidated per-capture
  brief. Multiple captures per day get different `_HHMMET` suffixes.
- **Variants:** `_addendum.md` for same-capture corrections,
  `_framework.md` for captures that introduced framework changes.

### Weekly bundle (every Sunday)
```
outputs/weekly/YYYY-MM/MM-DD/<file>
```

Expected files in a full Sunday bundle:
- `GR_Brief_YYYY-MM-DD.md` — weekly research brief (sector of focus)
- `GR_Brief_YYYY-MM-DD_amendment.md` — post-hoc reframing if caught on
  Sunday review
- `GR_<sector>_Pipeline_Overlay_YYYY-MM-DD.md` — deal-level overlay when
  pipeline action is warranted
- `DC_Sector_Alpha_YYYY-MM-DD.md`
- `Power_Sector_Alpha_YYYY-MM-DD.md`
- `LNG_Sector_Alpha_YYYY-MM-DD.md`

### Always-current (stay at `outputs/` root)
- **`alpha_ledger.md`** — contemporaneous record of findings. Append-only.
- **`alpha/`** — directory for ledger-adjacent structured records.

### Audits and one-offs
Co-located with the day they belong to:
- `outputs/daily/YYYY-MM/MM-DD/green_audit_*.txt` etc.

---

## Cadence

### Daily
One-to-four captures per day. Trigger phrase: **"Run GroundTruth capture"**
→ runs `python infra/run_manual.py` which fetches, classifies, scores,
writes the fallback HTML, and suppresses email. Claude then hand-writes
the consolidated sector brief, appends to the alpha ledger, and sends
email via `python infra/send_email.py`.

### Weekly (Sunday)
Sunday capture is followed by the **weekly sector-alpha brief trio**:
- `DC_Sector_Alpha_YYYY-MM-DD.md`
- `Power_Sector_Alpha_YYYY-MM-DD.md`
- `LNG_Sector_Alpha_YYYY-MM-DD.md`

Plus a `GR_Brief_YYYY-MM-DD.md` research brief focused on whichever sector
the week's tape made most consequential. Pipeline overlay produced
on-demand when deal-level action is warranted.

Sunday procedure: see `workflows.md`.

### Ad-hoc
GR briefs can be triggered on demand via the **"Load GR_Reference"** or
similar trigger phrase (see CLAUDE.md). Not tied to Sunday.

---

## Sector-alpha brief template (weekly)

Each of the three sector-alpha briefs follows the same 8-section shape:

1. **Sector state** — regime, price stack relevant to the sector, the
   "silence that matters" observation.
2. **§1 — THE sector alpha** — one ALF-grade structural finding with full
   mechanism + Structural-test read + VL windows + binary events.
3. **§2 — Sector secondary** — hardening/softening on existing pending
   ALFs + watch items.
4. **§3 — Sector drift-check** — mechanism that's quietly breaking
   underwriting assumptions.
5. **§4 — Thread at threshold** — 2-of-3 candidates.
6. **§5 — What's quiet and why it matters** — absence-as-signal read.
7. **§6 — Cross-sector / sovereign spillover** where relevant.
8. **Sector-level action items** — desk-level, NOT deal-specific.
9. **Sector reading — one-line summary.**

Deal-level actions go in a separate `GR_<sector>_Pipeline_Overlay_*.md`
file. Sector-alpha briefs are deal-free in body per the
[alpha-not-portfolio-review memory](../memory/feedback_alpha_not_portfolio_review.md).

---

## Classifier schema

### C-tags (content tags)
Numeric codes, semantic names in parentheses when displayed:

| Code | Name | Scope |
|---|---|---|
| C01 | Rates | Macro, Fed, rates, FOMC |
| C02 | FedReg | Federal regulatory (FERC, SEC, DOE, EPA, NRC) |
| C03 | RTO/ISO | PJM, ERCOT, MISO, CAISO, SPP, NERC, state PUCs |
| C04 | Legislation | Congress, legislation, IRA, OBBBA, tax credits |
| C05 | Oil/Gas | Oil, gas, LNG, pipelines, Brent, WTI, HH |
| C06 | Solar | Solar PV, utility-scale, modules |
| C07 | Wind | Wind, offshore wind, turbines |
| C08 | Geopolit | Iran, Hormuz, sanctions, conflict, war |
| C09 | Commodity | Steel, aluminum, copper, concrete, supply chain |
| C10 | Storage | BESS, battery, lithium, grid storage |
| C11 | Digital | Data centers, hyperscalers, GPU, AI infra |
| C12 | Credit | Credit spread, bonds, financing, lenders |
| C13 | FX | Dollar, euro, FX, currency |
| C14 | Sponsor | Acquisitions, sponsors, developers, JVs |
| C15 | Transmission | Grid upgrade, interconnect, transmission, substation |
| **C16** | **Struct** | **Structured finance, ILS, cat bond, sidecar, IG uplift** |
| **C17** | **Siting-State** | **State-legislative siting, moratorium, bit-barn ban** |
| **C18** | **RatingMethod** | **Rating agency methodology, credit rating events** |

### Abbreviation matcher (word-boundary)
Short uppercase abbreviations that need word-boundary matching to avoid
substring collisions (e.g., `"ils"` in `"hails"`):

| Abbreviation | C-tag |
|---|---|
| ILS, PCC | C16 |
| KBRA, DBRS, IG | C18 |

Add new abbreviations to `C_TAG_ABBREVS` in `gs/classify.py`. Require
(a) high distinctiveness in domain, (b) low collision risk with common
English words.

### Scorer
Current version: **v2.3.0**. Bumped via `SCORER_VERSION` + `TUNING_HISTORY`
entry in `ge/scorer.py`. Structural-candidate lane (cluster amplifier +
keyword bonus) added v2.3.0. Raw-score budget 0.55 invariant preserved —
all new contributions live in the boost layer.

---

## Alpha ledger protocol

### File
`outputs/alpha_ledger.md` — single always-current file at root. Never
move, never rewrite prior content. Append-only.

### ALF naming
`ALF-YYYYMMDD-N` where N is the sequence on that day (1-indexed).

### ALF fields
- **Sector class / vehicle** (not deal names in primary fields)
- **Type** — `Non-structural` | `Structural` | `Hybrid-candidate` |
  `Non-structural with structural hypothesis`
- **Mechanism** — transmission chain
- **Signal ladder** — cited signal IDs with dates
- **VL windows** — primary + extended
- **Binary events to watch** — numbered list
- **Hardening indicators** — log of per-date entries appended over time
- **Structural tests** (if applicable) — contract-survival, regime-reset,
  substitution-closure

### Hardening-indicator entries
Per-date log under each ALF. Format:
```
- YYYY-MM-DD HH:MM ET [short-status-phrase]: mechanism detail...
```
Append-only. Never rewrite.

### Resolution
ALFs close via an explicit resolution pass. Resolution notes append under
the original ALF; the contemporaneous record (cited signal ladder + VL
stated windows) is preserved intact for VL-compression audit.

Types: `HIT` | `EARLY` | `LATE` | `WRONG`. Resolution requires an
observable event — not speculation.

### Watch items
Candidate ALFs below the 2+ independent signal threshold. Named
`ALF-YYYYMMDD-W1` etc. Promoted to full ALF when threshold crosses.

---

## Git

Repo: **`closetmuse/Groundtruthv2`** (private, GitHub).

See `workflows.md` for git cadence, commit conventions, and push discipline.

---

## Memory files

User memory lives at
`C:\Users\nagar_7kszmu8\.claude\projects\C--Users-nagar-7kszmu8-GroundTruth-v2\memory\`
indexed in `MEMORY.md`. Memory files hold:
- `user_sector_risk_frameworks.md` — Sri's sector risk axes
- `feedback_*.md` — discipline feedback / workflow rules
- `project_*.md` — deal-specific state persisting across sessions

When a discipline rule changes, the corresponding memory file gets
updated (by memory tool) and referenced here or in `docs/CHANGELOG.md`.
