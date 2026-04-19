# GroundTruth V2 — Project Intelligence
# Version: 2.1 | April 2026 | SPLIT ARCHITECTURE
# Layer A — Philosophical Brain (this file, keep lean)
# Load companion files only when task requires them.

---

## OWNER
Sridhar Nagarajan (Sri)
Head of Project Finance Americas, Standard Chartered Bank, Jersey City NJ
20+ years infrastructure finance. Guest Lecturer Harvard Kennedy School.

---

## COMPANION FILES (load only when needed)
GT_Reference.md      — Signal schema, all tags, macro regimes, InfraOS data
GT_Pipeline.md       — 45 pipeline deals, binary events, sector intelligence
GT_BuildLog.md       — Phase history, known gaps, risk register, file map
docs/                — CHANGELOG, conventions, workflows (2026-04-19 onward)

---

## WHAT GROUNDTRUTH V2 IS
Multi-agent intelligence platform. Eight agents convert public market signals,
commodity prices, regulatory filings, and direct field observations into a
daily intelligence email. North Star: tell Sri one non-obvious thing, in time
to act, on a specific deal, backed by evidence.

---

## CORE THESIS — VERIFICATION LATENCY (PRIVATE)
Systematic gap between when infrastructure market events are economically
realized and when they are institutionally recognized.
First live measurement: LME aluminum Jan 15 → desk confirmation Apr 8 2026.
Latency: 83 days. Second measurement forming: CAISO/ERCOT curtailment Apr 13.
InfraOS operationalizes this thesis. PRIVATE until Month 9-12. Do not mention.

---

## DEPLOYMENT
C:\Users\nagar_7kszmu8\GroundTruth_v2\

---

## AGENT ARCHITECTURE
Eight agents. Facts and judgments separated — GS captures, GE judges.

| Agent | Name            | Owns                                    | Phase |
|-------|-----------------|-----------------------------------------|-------|
| GS    | GroundSignals   | Every external observation              | 1     |
| GE    | GroundEngines   | Every judgment — scoring, regime        | 1     |
| GI    | GroundIntelligence | Patterns over time — latency, hit rate | 2  |
| GR    | GroundResearch  | On-demand deep research briefs          | 4     |
| GPi   | GroundPipeline  | Every live deal — exposure, binary events | 4   |
| GP    | GroundPortfolio | Every closed deal — covenants, refi     | 4     |
| GC    | GroundClients   | Target clients — COMPLIANCE GATE        | 5     |
| GT    | GroundTruth     | Orchestration, email, scoreboard        | 2     |

Flow: GS → GE → GPi/GC → GT → Sri. No agent reaches backward.

---

## TRIGGER PHRASES

**Run GroundTruth capture**
→ Full 3-layer capture. Fetch all P1 sources. Classify. Write DB. Send email.

**Add signal from [source]: [headline]**
→ Classify immediately. Assign all fields. Write DB. For paywalled sources.

**Flag breaking signal — [description]**
→ Classify immediately. Write. Fire alert if warranted. T1 degrades in hours.

**Check pipeline alerts**
→ Pull all RED signals. Summarize by deal. Flag new since last check.

**Log outcome for [signal ID] — [what happened]**
→ Update signal. Feed Alpha Scoreboard. 2 min/week. Non-negotiable.

**Load GT_Reference**
→ Load GT_Reference.md for tag lookups, regime definitions, InfraOS data.

**Load GT_Pipeline**
→ Load GT_Pipeline.md for deal-specific work, binary events, SIL.

---

## EMAIL STRUCTURE (PRD 11.2)
10 sections. GT assembles from all agent outputs.
1. Regime + Binary Events — 3 lines
2. Price Snapshot — 8-10 series with deltas
3. Historical Pattern Match — encyclopedia analogue
4. Signals RED — mechanism + action window + price context
5. Signals AMBER — mechanism + watch item
6. Portfolio Watch — covenant/refi/stress alerts
7. Prospect Watch — client signals (compliance gate)
8. Binary Events Countdown — days remaining, linked deals
9. Alpha Scoreboard Delta — new alerts, resolved, hit rate
10. System Status — fetch stats, failures, next run

---

## ANALYTICAL STANDARDS

**Transmission Mechanism Rule** — every causal claim must state:
1. Mechanism: how does A cause B?
2. Timeline: how long does transmission take?
3. Asset specificity: which assets and why?
Without all three the claim is correlation not causation.

**Modelled vs Measured** — Moody's data = measured. Estimates = labelled
directional. Never present modelled numbers with false precision.

**second_order Field** — the most important intellectual asset in the platform.
Three-layer minimum: mechanism + timeline + named deal impact.
Always anchor to Moody's numbers where construction phase is involved.
Claude drafts. Sri validates on every active deal signal.

---

## SRI LINKEDIN VOICE RULES
Single punchy opener. No listicles, no bullets. 150-250 words.
Practitioner to practitioner — observing, not teaching.
Ends with open question, never an answer.
No SC mentions, no client references. Quiet earned authority.
Never: genuinely, straightforward, game-changer.

---

## SC COMPLIANCE NOTE
GS ingests public sources only. ANECDOTAL = Sri personal observations only.
GC requires internal SC sign-off before activation — do not build until reviewed.
No SC data in system. Local SQLite before Railway.

---

## ARCHITECTURE
Layer A — CLAUDE.md: methodology, standards, triggers. Updates on method change.
Layer B — Encyclopedia: immutable historical record, 8 anchor events.
Live market overlay (regime, active binary events, axis state) is computed
each capture run from the Encyclopedia matcher + gt_binary_events table +
user_sector_risk_frameworks.md memory — no standalone overlay file.

---
*GroundTruth V2 — CLAUDE.md v2.1 | Split Architecture April 2026*
*Target: <2,000 tokens. Companion files loaded on demand.*
