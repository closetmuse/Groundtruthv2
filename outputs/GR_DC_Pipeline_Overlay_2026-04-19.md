# GR DC Pipeline Overlay — 2026-04-19

**Companion to:** [`GR_Brief_2026-04-19.md`](GR_Brief_2026-04-19.md)
**Scope:** 16 DC-category active deals from the 44-deal pipeline, mapped against the three threads from this week's GR weekly.

**Method caveat up front.** This overlay relies on the deal sheet fields that are actually populated: `State`, `RTO`, `Sponsor`, `Asset Type`, stage note in `Notes`. Two critical fields for this exercise are **not** structured in the deal sheet — power-source assumption per deal (gas baseload? solar-plus-storage? SMR pairing?) and siting-approval stage (local vs state). Both are called out as GR-improvement findings at the bottom.

---

## DC deals in pipeline, by stage

| Stage | Count | Deals |
|---|---|---|
| Approved / closing | 2 | Storybook TX (Mar 2026), Storybook WI (May 2026) |
| In execution | 5 | Temple (Rowan, TX), Project Temple (Rowan, TX, Apr 2026), Powerhouse Prairie (BX, TX, May 2026), Edgeconnex New Albany (Apr 2026), Delta Stack (Blue Owl, TX, Apr 2026) |
| RFP stage | 3 | Jayhawk (location TBD), Hampton (Equinix, GA), QTS Tidal (Cedar Rapids, IA) |
| Early pipeline | 4 | Edged DC Javelin 2 (KOCH, TBD), QTS 2 (TBD), QTS 3 (TBD), Edgeconnex Atlanta |
| Live structured | 2 | GT-108 SB Energy Ohio (PJM), GT-109 SB Energy Milam (ERCOT) |

**Timeline concentration:** 5 DC deals close or execute inside the next ~6 weeks (Apr-May 2026). Siting approval is already in place for those; the residual risk is construction-phase (cost stack, interconnect cost escalation) rather than permit-phase.

---

## Thread B — Siting / Local-Govt Regulatory Risk

**Framework:** Maine-precedent spread is most likely to reach states with (a) active AI load growth and (b) live retail-rate politics. The ranking inferred from public-source data: VA first, OH and IA second, GA and TX third.

| Exposure | Deals | Rationale |
|---|---|---|
| **HIGH** | **GT-108 SB Energy Ohio** (PJM), **Edgeconnex New Albany** (Ohio cluster), **QTS Tidal** (Iowa, Cedar Rapids) | Ohio has multiple hyperscale-driven ratepayer debates live; PJM is the exemplar ISO for AI-driven load stress. Iowa is second-tier on the Maine-spread list and QTS Tidal is still RFP-stage, meaning full state-level approval risk is ahead. |
| **MEDIUM** | **Hampton** (Equinix, Georgia), **Edgeconnex Atlanta** (Georgia) | Georgia has active grid-stress commentary. Hampton is RFP-stage (full approval risk ahead); Atlanta is early pipeline (even earlier). |
| **LOW-MEDIUM, different political economy** | **GT-109 SB Energy Milam** (ERCOT), **Temple** and **Project Temple** (Rowan, Texas), **Storybook TX** (Vantage), **Powerhouse Prairie** (BX), **Delta Stack** (Blue Owl) | ERCOT's political structure makes state-level moratorium unlikely short-term. But ratepayer-stress narrative could re-emerge via the PUCT — worth tracking. Texas-cluster deals at "in execution" stage face construction-phase risk, not approval-phase. |
| **LOW** | **Storybook WI** (Vantage) | Wisconsin is not on the Maine-spread list; deal is approved/closing. |
| **DATA GAP** | **Jayhawk**, **QTS 2**, **QTS 3**, **Edged DC Javelin 2** | Location TBD. Cannot map until geography locks. |

**Concrete action:** for GT-108, Edgeconnex New Albany, and QTS Tidal specifically, the desk question is whether the approval-timeline assumption embeds "no state-level siting escalation." If yes, revise against the Maine + Tennessee legal architecture: the probability is no longer zero on a 12-month view. Add 9-12 months of approval-timeline buffer as a sensitivity test on IRR.

---

## Thread C — SMR / Nuclear-for-DC Execution Risk

**Framework:** political-vs-construction drift. DC power plans that reference SMR uptake as baseload on a 3-year horizon are underwriting on a construction-feasibility timeline with no at-scale empirical basis (GS-707 Energy Monitor Apr 16).

**Deal-level read:** cannot be produced from the available sheet data. The `Key Commodities` field is populated for only one DC deal (GT-109: "ERCOT power prices, gas"). No DC deal in the active book has an explicit SMR or nuclear dependency flagged in the structured data. Two possibilities:

1. **No DC deal in the book actually banks on SMR uptake.** Power plans are gas + grid + PPA across the board. In that case, Thread C's sector-level read is informative as a *market* read but carries no specific pipeline exposure to flag.
2. **Some DC deal has an implicit SMR/nuclear pairing in its long-dated PPA or power plan** that is not captured in the sheet's Commodities field. In that case, the data gap is the finding — we have no way to know.

**Concrete action:** desk check on any DC deal with a long-dated power plan (>7-year PPA) — does the forward-year energy-source mix assume any SMR uptake? If yes, stress with SMR replaced by brownfield gas + battery holding cost flat; if IRR collapses, flag. Two candidates where this matters most given size and duration:

- **GT-108 SB Energy Ohio** — Asset Type is "Gas + Digital Infra" (explicit gas), so SMR dependency is unlikely. But PJM's long-dated interconnect queue is SMR-dense at the pipeline level; worth confirming the PPA doesn't index to a nuclear-weighted generation mix.
- **QTS Tidal** (Iowa) — Iowa's long-dated generation mix is increasingly nuclear-discussed. RFP stage means the power plan is still being written.

---

## Thread A — Sovereign-AI Uptake

**Framework:** EU €180m sovereign cloud tender (GS-1028) + Anthropic/Mythos Apr 17 thread. Continuation of the sovereign-uptake narrative on the hyperscaler side.

**Deal-level read:** thin. No DC deal in the active book is a sovereign-AI-uptake direct play. The closest indirect exposures:

- **Edgeconnex deals** (New Albany, Atlanta) — Edgeconnex's broader platform has European sovereign-cloud customer exposure; two deals in the book give a lens into sponsor-level tailwind rather than deal-specific transmission.
- **KOCH as sponsor of Edged DC Javelin 2** — no known sovereign-AI exposure; pass.
- **QTS deals** — primarily US-facing; pass.

**Action:** none at deal level. This is a sponsor-strategy tailwind to watch for Edgeconnex.

---

## Sponsor concentration

| Sponsor | DC deal count | Concentration read |
|---|---|---|
| QTS | 3 (Tidal, 2, 3) | Two of three are TBD-geography, early pipeline — concentration is speculative until locations lock |
| Vantage | 2 (Storybook TX, WI) | Both approved/closing; concentration is contained |
| Rowan | 2 (Temple, Project Temple) | Both in execution, both Texas — sponsor-geography doubled up |
| Edgeconnex | 2 (New Albany, Atlanta) | One in execution, one early pipeline — split stages |
| SB Energy | 2 (GT-108, GT-109) | Both live, one PJM + one ERCOT — sponsor-regime hedged |

No concentration warrants a flag today. QTS three-deal cluster is worth monitoring because two are still TBD-geography — if they land in the same state (likely Virginia given QTS's footprint), that triples Thread B exposure for one sponsor.

---

## Summary — week-over-week pipeline reads

- **5 DC deals close or execute in the next 6 weeks.** Siting-risk repricing would primarily hit the RFP-stage and early-pipeline deals, not these.
- **3 deals are in the HIGH siting-exposure bucket** (GT-108, Edgeconnex New Albany, QTS Tidal). These are where the Maine-precedent read matters.
- **No DC deal in the book has an explicit SMR dependency flagged** in the sheet. Thread C is primarily a market read, not a pipeline read — unless the power-source data gap hides something.
- **No DC deal is a direct sovereign-AI uptake play.** Thread A is sponsor-strategy color at most.

---

## GR-improvement findings (data gaps surfaced by this exercise)

Flagged here because Sri asked to run GR as-built and then review what should improve. Four structural issues surfaced:

1. **Power-source assumption is not a structured deal field.** `Key Commodities` is populated for 1 of 16 DC deals. To properly map Thread C (SMR exposure) at the deal level, we'd need a mandatory field for primary baseload source assumption (gas / grid / PPA-solar / PPA-nuclear / SMR-paired).

2. **Siting-approval stage is not structured.** The `Notes` field distinguishes "approved / closing" vs "in execution" vs "RFP stage" vs "early pipeline" by free text, not by a structured stage code. For Thread B (siting risk) to be mappable reliably, a controlled-vocabulary stage field would let us auto-filter which deals are still exposed to approval-phase risk vs only construction-phase.

3. **Four DC deals have TBD geography.** Jayhawk, Edged DC Javelin 2, QTS 2, QTS 3. Until these lock, they are unmappable on Thread B. Either the sheet should carry "expected state" as a soft field for early-pipeline deals, or the GR overlay should track "unmappable" as an explicit count rather than a silent omission.

4. **The GR pipeline (`gr/agent.py`, `gr/briefs.py`) is stub-only.** Both files are 3-line placeholders. The Apr 14 GR brief was hand-assembled against the daily capture output. Today's was the same. The path from "weekly GR" as a repeatable product to a scheduled / semi-automated brief requires (a) a weekly signal-density query over the full seven-day window, (b) a thread-detection pass that clusters signals by common C-tag + source pattern + headline co-occurrence, (c) a drift-check pass against prior briefs to see what hardened vs softened over the week, and (d) an explicit deal-overlay step that runs after the body is drafted. Today's brief did (a) and (c) manually, skipped a formal (b) in favor of my strawman clustering, and did (d) only because you explicitly asked. A proper build would make (b) and (d) first-class steps rather than ad-hoc.

---

*GroundTruth V2 | GR Pipeline Overlay | 2026-04-19 | Private & Confidential*
