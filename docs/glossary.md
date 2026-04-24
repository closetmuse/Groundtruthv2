# GroundTruth Glossary

Persistent reference for recurring terms, codes, and framework language
used across briefs, deep dives, and the alpha ledger. Load once, reference
from any brief. Add terms as they stabilise; remove terms that fall out
of active use.

Last updated: 2026-04-24

---

## Alpha Ledger terminology

**ALF** — *Alpha Ledger Finding.* A falsifiable, time-bound market-price
prediction committed to the ledger at a specific moment. Every ALF has a
type (Non-structural / Structural / Hybrid), a Verification Latency date,
and explicit probability weights that update as evidence accumulates.

**ALF-YYYYMMDD-N** — ALF naming convention: date opened + sequence number
on that date. ALF-20260417-1 is the first ALF opened on April 17 2026.
In conversation shortened to ALF-17-1.

**W / Watch item** — Candidate-ALF in waiting. Thesis is forming but not
yet at the three-test bar for structural alpha (contract-survival +
regime-reset + substitution-closure) and not yet falsifiable at a
specific VL date. Numbered W1, W2, W3... in sequence. Promotion to full
ALF happens at a Sunday weekly review when the evidence crystallises or
at the capture where a triggering event fires.

**VL — Verification Latency.** The date by which the ALF's prediction
must resolve. Past the VL with no resolution → the ALF converts to
LATE. Binary success/failure → HIT or WRONG.

**HIT / WRONG / EARLY / LATE / PENDING** — ALF resolution states.
HIT = thesis confirmed at VL. WRONG = thesis falsified. EARLY = confirmed
pre-VL (early-HIT-confirmation). LATE = unresolved past VL. PENDING =
active, awaiting VL.

**Structural / Non-structural / Hybrid** — ALF type.
- *Non-structural* (default) — tactical observation; a short-duration
  price pattern that may HIT without changing the underlying regime.
- *Structural* — a regime-level claim. Requires all three tests to pass
  (contract-survival + regime-reset + substitution-closure).
- *Hybrid* — has structural elements but conditional on a specific
  event or contingency.

**Hardening indicators** — Evidence that accumulates toward Structural
crystallisation on a Non-structural candidate or a Hybrid. Logged per
capture in the alpha ledger.

**Probability weights** — The three-way split on a candidate-Structural
ALF: HIT / WRONG / PENDING, summing to 100%. Revised as evidence comes
in. Significant revisions (>10pts) are ledger-relevant events.

**Contemporaneous record** — The brief and ledger append at capture-time
are permanent; do not edit retroactively. Follow-ups go to addendum
files or deep dives.

---

## Regime framework

**R0 / R1 / R2 / R3** — Four macro regime states:
- *R0 Compound Stress* — simultaneous multi-channel stress (kinetic-
  commodity + financial + geopolitical). Current state as of 2026-04-24.
- *R1 Inflation / rate shock* — monetary-policy-led stress.
- *R2 Credit / banking stress* — financial-sector-led.
- *R3 Demand / commodity collapse* — cyclical downturn.

**Day N of regime** — counter from regime onset. Current: Day 55 of R0
(Hormuz kinetic re-escalation Apr 2026).

**E01 – E11** — Encyclopedia analogues. Eleven locked historical precedents
the matcher scores each capture against:
- E01 Global Financial Crisis 2008
- E02 COVID Demand Shock 2020
- E03 Ukraine/Energy Crisis 2022
- E04 Fed Rate Hike Cycle 2022-23
- E05 Taper Tantrum 2013
- E06 Oil Price Crash 2014-16
- E07 Hormuz/Iran Conflict 2026 (ACTIVE)
- E08 Second Oil Shock / Volcker 1979-81
- E09 Infrastructure Overbuild — Dot-Com Fiber 2000-02
- E10 Silicon Valley Bank Collapse 2023
- E11 Liberation Day Reciprocal-Tariff Shock 2025

The matcher returns a top-match and percentage. Persistent cadence at a
single match (current: E01 at 78% for 16 captures) raises a methodology
question for weekly review.

---

## Framework axes

Fifteen structural axes the brief scans each capture. An axis is
"QUIET, explicit" when nothing fired; "firing" when a directional print
landed.

**LNG — five axes:**
- *LNG Axis 1* — HH-JKM / HH-TTF arbitrage. Destination-vs-Henry-Hub
  spread driving netback for contracted US LNG.
- *LNG Axis 1 export-capacity sub-lens* — Train COD schedule and
  capacity-build direction.
- *LNG Axis 2* — Construction cost (metals: steel, aluminum, copper).
- *LNG Axis 3* — Waha / Permian basis. Localised basin stress.
- *LNG Axis 4* — DOE / FERC export authorisation tape.
- *LNG Axis 5* — International supply disruption (Australian LNG,
  Qatari, Yamal-LNG outages).

**Power — eight axes:**
- *Power Axis 1* — FEOC (Foreign Entity of Concern) + supply chain.
  Solar/wind/BESS tariffs, component imports, domestic content rules.
- *Power Axis 2* — Construction cost (overlaps LNG Axis 2).
- *Power Axis 3* — Interconnection / FERC queue dynamics.
- *Power Axis 4* — Power price movement / cost-to-system (negative LMPs,
  curtailment).
- *Power Axis 5* — EU/Asian LNG-power transmission.
- *Power Axis 6* — Behind-the-meter / DC coupling.
- *Power Axis 7* — ILS (Insurance-Linked Securities) — shared with
  DC Axis 7.
- *Power Axis 8* — Utility tariff carve-out structuring.

**Data Centers — seven axes:**
- *DC Axis 1* — Hyperscaler investment durability & merchant-DC stress.
- *DC Axis 2* — DC construction cost (shared with LNG Axis 2).
- *DC Axis 3* — Supply-chain binding constraints (GPU, HBM, gas turbine,
  transformer).
- *DC Axis 4* — Power linkage.
- *DC Axis 5* — GPU financing. Captured daily via Vast.ai spot + Kalshi
  forward tape.
- *DC Axis 6* — Behind-the-meter power (BTU-to-GPU thesis).
- *DC Axis 7* — ILS-wrapped DC senior debt / cat-bond substrate.

---

## Standing lenses

Every capture scans these regardless of whether tape fired:

- *VG merchant-LNG lens* — Venture Global's credit/cargo tape. Silent
  streak is itself a data point. Broken by GS-1925 on 2026-04-24.
- *Hyperscaler-concentration lens (6-counterparty)* — direct-named
  presence of Microsoft / Meta / Amazon / Google / Oracle / Apple in
  the tape.
- *Model-hyperscaler pairing lens* — Anthropic / OpenAI / Mistral /
  Cohere relationships with hyperscaler anchors.
- *Power Axis 8 carve-out* — utility-tariff carve-out structuring
  deals, specifically tracked because of novel credit characteristics.
- *DC realness score* — internal 1-5 rubric for evaluating DC-sponsor
  announcements. Memory-backed. 5 = fully-anchored hyperscaler
  execution; 1 = hopeful merchant-pipeline paper.

---

## Breach terminology

**7d / 30d breach** — Price-series delta over 7 or 30 calendar days
relative to a threshold (5-8% for commodities, 20% for equities).
Automatically fired by the price-snapshot module.

**Cumulative-window breach** — A 30d breach is "cumulative" — it averages
over the 30-day window, so a single-session fade does not collapse the
breach unless the entire window rolls off. This is the structural-signal
read.

**Real vs mechanical breach** — a real breach is new-price-information;
a mechanical breach is window-falloff (an old-session extreme rolling off
the window base). JKM 7d -15.3% currently is mechanical, not real.

**Provisional-EARLY / at-risk / structural** — ALF-17-1 framework bands
for crude price at a given threshold. Provisional-EARLY = likely
early-HIT-confirmation-ready; at-risk = in the decision band; structural
= sustained above-band over multi-day cumulative window.

---

## Substrate terminology (ALF-19-1 specific)

**Substrate** — Underlying market-infrastructure prints that make a
mechanism (like DC-peril cat bonds) feasible at scale. Tracked as
broader cat-bond-market-readiness score and DC-specific core score.

**Broader cat-bond-market-readiness** — Count of material ILS-market
prints across all peril types. Current: 35.

**DC-specific core** — Count of DC-peril-specific prints. Current: 16.

**Substrate layers** — The distinct mechanism categories. Currently
tracked: fund formation, named placement, tokenization platform, debut
cat bond, established-issuer placement, DFI-parametric-pricing,
DC-sponsor-anchored (the last remaining gap).

**DFI** — Development Finance Institution. ADB (Asian Development Bank),
World Bank, EBRD, IFC etc. DFI-parametric-cat-bond pricing is a specific
precedent template for DC-peril thesis.

---

## Classifier / signal fields

**GS-NNNN** — GroundSignal ID. Sequential number assigned at classification.

**Alert level** — RED / AMBER / GREEN. Signal importance, computed from
weighted score.

**c_tags** — Content tags. Eleven categorical labels (C01 Rates, C02
FedReg, C03 Geopolitical, C04 Legislation, C05 Oil/Gas, C06 Solar,
C07 Wind, C08 Geopolitical, C09 Commodity, C10 Storage, C11 Digital,
C12 Credit, C13 Currency, C14 Insurance, C15 Policy, C16 Reinsurance).

**f_tags / t_tag / o_tag** — Secondary classification. Most often
shortened to T1/T2/T3 tiers.

**second_order** — The transmission-mechanism field. Must answer:
mechanism + timeline + asset specificity (per the Transmission
Mechanism Rule). Claude drafts; Sri validates on every active deal
signal.

**regime_at_score** — Regime label at scoring time, for historical
matching.

---

## Binary events

**BE-NNN** — Binary Event. A specific dated market-condition watched
for trigger. Example: BE-001 "Brent above $95 sustained 14+ days."
Tracked in `gt_binary_events` table.

---

## Analytical rules

**Transmission Mechanism Rule** — Every causal claim must state:
1. Mechanism — how does A cause B?
2. Timeline — how long does transmission take?
3. Asset specificity — which assets and why?
Without all three, the claim is correlation not causation.

**Structural alpha three tests** — Default is Non-structural. Structural
requires all three:
1. *Contract-survival* — the underlying contract survives the tested
   stress event.
2. *Regime-reset* — the price/spread-level reflects a regime shift,
   not a tactical move.
3. *Substitution-closure* — substitute assets have closed off, so the
   regime is self-reinforcing.

**Modelled vs measured** — Moody's data and comparable third-party data
are measured. Internal extrapolations or GT estimates are modelled —
label them directionally, never with false precision.

**Alpha not portfolio review** — Briefs are alpha-generation exercises,
not deal reviews. No pipeline deal names in briefs; deal overlay lives
in the Sheet and post-brief. Named-deal discipline check is enforced.

**Tape tone** — One line, four words max, on the last brief of each day.
Compressed regime-feel for later pattern analysis.

---

## Deal codes (for post-brief overlay use only)

**GT-NNN** — Active pipeline deal numbering.
**P-name** — Project codename. Used in the 44-deal pipeline Sheet.
No deal codes appear in briefs per the alpha-not-portfolio-review rule.

---

## Workflow codes

**Capture** — Single end-to-end run: prices → fetch → classify → score
→ GPi heat scoring → encyclopedia match → dashboard → brief → finalize.

**Slot** — AM / MIDDAY / PM. Marker file sets the slot.

**Addendum** — Time-bound same-day follow-up, lives in the day folder
as `addendum_HHMMET_<topic>.md`. Distinct from deep dives.

**Deep dive** — Thematic, not tape-bound, lives in `outputs/deep_dives/`.
Sri-flagged post-brief. Not counted in the capture workflow.
