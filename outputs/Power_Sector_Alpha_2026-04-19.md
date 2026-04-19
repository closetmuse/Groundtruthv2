# POWER SECTOR ALPHA — 2026-04-19

**Scope:** US power markets — merchant renewables, solar + storage, wind, grid/interconnect, curtailment economics. Sector-level analytical view.
**Cadence:** Weekly (Sunday).
**Discipline:** sector-level, deal-free. Deal overlay is separate.
**Cross-reference:** `alpha_ledger.md` ALF-20260417-2, ALF-20260420-W1 (watch), ALF-20260415-3.

---

## Sector state

R0 Compound Stress, Day 50+. Cost stack mixed: HRC $1,079 (elevated vs Jan baseline), Aluminum $3,512 (softening week-over-week), Copper $13,480. Rates anchored UST10Y 4.32%, BBB OAS 101 bps. FOMC 2026-04-29 binding event at T-10 days.

**RTO state:** Day 7 of curtailment pattern across three nodes. ERCOT HB_WEST 10 negative DA hours, CAISO NP15 7 neg, SP15 10 neg — consistent magnitudes across a full calendar week. HB_WEST peak $5.35 vs off-peak $19.70 (spread -$14.35) is the duck-curve peak-below-off-peak inversion fingerprint — midday solar forcing, not thermal-demand weakness. ISONE $39.41, NYISO NYC $35.90, MISO Illinois $15.60 / Indiana $31.53 — unremarkable.

**Silence that matters:** no new sponsor-specific PPA prints, no interconnect-queue movement prints outside the pending FERC Large Load Docket, no merchant-tail repricing transactions. In a week where curtailment hardened to a 7-day three-node pattern, the absence of commercial response is itself a sector signal.

---

## 1 — THE SECTOR ALPHA: Curtailment persistence as structural merchant-tail repricing risk

**What hardened this week.** ALF-20260417-2 (CAISO/ERCOT curtailment, Non-structural with structural hypothesis) — Day 7 of pattern with consistent magnitudes at three nodes. The duck-curve inversion fingerprint (HB_WEST peak $5.35 < off-peak $19.70) confirms the mechanism is midday solar forcing, not thermal-demand weakness. Seven consecutive days, three nodes, same mechanism is the hardening-strong signature on the Non-structural side.

**Mechanism — why this matters at sector level.**

As-produced solar PPAs carry capture-rate assumptions typically in the 85-95% range on P50. A negative-DA-hour delivers zero or negative revenue against a PPA priced off a positive capture assumption. If negative hours stay at ~10 per day on the affected hubs, annualized curtailment runs ~15-20% — double or triple the underwriting assumption. The compression path:

1. **DSCR compression** — capture-rate haircut flows through to revenue, then DSCR on 1.30-1.35 underwrites compresses toward 1.15-1.20 on a year-forward basis.
2. **Moody's construction CDR 0.94%/yr anchors baseline risk** but construction-phase is not the binding channel here. The binding channel is operating-phase capture rate.
3. **Merchant-tail assumptions.** Operating solar deals with merchant-tail exposure beyond year 10-15 of a PPA face revenue floors that were priced against historical curtailment norms. Those norms are being revised in real-time.

**Structural hypothesis test — three conditions:**

- **Contract-survival:** PENDING. The pattern must survive spring→summer demand recovery. Summer air-conditioning load typically absorbs midday solar without curtailment. If the 7-day pattern survives through late May / June into real summer load, the structural thesis hardens materially. If curtailment collapses with June heat, the pattern was seasonal not structural.
- **Regime-reset:** PENDING. Would require a regulatory/RTO response that institutionalizes curtailment as a pricing norm (e.g., CAISO price-floor changes, ERCOT ORDC recalibration affecting midday hours). No such response this week.
- **Substitution-closure:** BESS deployment is the obvious substitution — co-located or grid-level storage soaks up negative-hour energy and releases it at peak. The substitution question is whether BESS deployment pace is fast enough to absorb the curtailment before PPA revenue compression hits DSCR covenants at scale.

Trajectory is consistent with hardening Structural over 60-90 days, contingent on June-July pattern persistence.

**Federal-layer hardening:** **GS-977 FERC commits to act on Large Load Interconnection Docket by June 2026** — same approximate window as the structural test (late May / June). This is the single most important binary event in the sector's next 90 days because a FERC large-load-interconnection framework *either* creates a price signal that rewards load flexibility co-located with solar (supporting structural repricing) *or* doesn't (leaving the curtailment problem with RTOs alone). Both outcomes are knowable from the ruling text.

**VL windows (active for ALF-20260417-2):** primary 2026-05-17 (closes soon); hardening-strong trajectory argues for extension to 2026-07-31 aligned with the June FERC ruling + early-summer load data.

**Binary events to watch:**
1. FERC Large Load Interconnection Docket ruling (stated June 2026 — T-~60d).
2. First major RTO market-design proposal explicitly addressing midday-solar curtailment pricing (CAISO or ERCOT).
3. First meaningful as-produced solar PPA renegotiation tied to observed curtailment (public-source).
4. FOMC 2026-04-29 — not curtailment-specific but changes WACC anchor for any solar refinancing exposed to curtailment.

---

## 2 — Sector secondary: State-level siting-restriction spreading cross-asset (watch)

**Watch item — candidate ALF-20260420-W1.** The 2026-04-13 GS-107 Utility Dive print *"Kansas county weighs moratorium on solar development"* surfaced during the 2026-04-19 classifier backfill pass. State/county-level restriction applied to **solar**, not DC — same mechanism as the Maine DC moratorium but different asset class.

**Why this matters at sector level.** If state-level siting-restriction is generalizing from DC to solar, the finding is no longer a DC-specific risk. It's a **cross-asset renewables sector siting-risk escalation** that compounds with interconnect costs and approval-timeline buffers.

**The read for Power sector specifically:**
- Solar development that assumes zero state-level escalation needs to add 9-12-month approval-timeline buffer as a sensitivity.
- Paired with the curtailment-repricing thread above: a developer facing *both* state-level siting escalation AND structural-curtailment pricing is looking at a compound risk repricing rather than one or the other.
- The mechanism that drives state-level siting restriction — ratepayer politics + grid-stress concerns — is exactly the mechanism that argues for curtailment-aware rate design. States that pass moratoria are also states where curtailment is politically legible. Same institutional venues, same underlying constituency.

**Threshold for promoting the watch item:** 2+ more state-level moratorium or restrictive-zoning prints across asset classes (solar, wind, DC, storage) in the next 30 days. Kansas + Maine = 2 events but across 2 asset classes in 2 geographies. A third state print would cross the bar for a standalone ALF.

---

## 3 — Sector drift-check: OBBBA reconciliation + FEOC supply chain

**Current state.** OBBBA solar ITC/PTC elimination language continues to advance in reconciliation per Apr 14 brief (GS-336 equivalent). BOC (Beginning-of-Construction) deadline at T-81 days per the Apr 14 framing. FEOC (Foreign Entity of Concern) supply-chain enforcement overhang not advanced this week.

**This week:** No new OBBBA-specific prints at AMBER level. One adjacent print — **GS-941** *"Toyo centres US efforts in Texas as it looks to build policy-proof supply chain"* — indicates supply-chain response to the policy uncertainty. Sits at weighted 45.0 just at the AMBER threshold; not decisive.

**Sector-level read.** The OBBBA policy-risk overhang compresses developer IRR thresholds on any pre-BOC project. This is not new; what matters for the weekly brief is that the overhang persists without resolution. Reconciliation timing remains the binary event.

---

## 4 — Thread with attention but below threshold: Europe demand-compression

**Two FT prints this week** — GS-1029 *"Brussels pushes remote working to ease energy crisis"* (FT Energy) + GS-1033 (FT Markets) BlackRock warns of European stocks hit from energy crisis. European policy-driven demand compression.

**Why this appears in a US Power sector brief.** The mechanism transmits asymmetrically to US renewables through two channels:
- **Capital flow redirection** — European infrastructure capital that might otherwise fund European renewables gets redirected to US if European policy closes capex windows. Potential tailwind for US developer financing.
- **Module / BESS cost effects** — European demand compression could marginally depress global solar module pricing if European installation slows. Small effect given US-made-in-America policy push, but not zero.

Needs a third corroborating print with a named policy instrument (EU Commission directive, capacity-mechanism change) before promoting to an ALF candidate. Currently 2/3.

---

## 5 — What's quiet and why it matters at sector level

- **Zero new sponsor-named PPA prints** — consistent with the DC sector finding that deal flow is pausing for structural clarity. Power deal flow mirrors this.
- **Zero new FERC tape outside Large Load Docket** — unusual for a typical week. The docket itself is the entire sector regulatory story right now.
- **Zero prints on CAISO / ERCOT market-design proposals** addressing curtailment — the curtailment pattern hardens day-over-day but the regulatory response is absent. That absence is itself informative: RTOs and PUCs are watching, not acting.
- **Zero BESS-specific deployment announcements** at major scale — three separate ILS / Artemis-source AMBER prints (GS-813, GS-814, GS-875) touched data-center financing innovation this week; the same innovation lane is available for BESS operational risk, and nobody announced anything.

The silence argues for the same sector reading as DC: mid-cycle pause before a structural repricing. For Power specifically, the repricing event is either (a) the FERC Large Load ruling or (b) the first as-produced solar PPA renegotiation tied to curtailment.

---

## 6 — Sovereign / cross-asset spillovers

- **ILS → DC senior debt IG uplift** (ALF-20260419-1 — see DC Sector Alpha brief). If this structural-finance mechanism generalizes, BESS operational risk is a natural candidate for the same wrap structure. ILS capital writing BESS revenue-risk would transform merchant-tail pricing. No prints this week but mechanism is in adjacent scope. Watch over 90 days.
- **GS-986 FT "oil patch securitisation"** — structural-finance mechanism applied to upstream oil & gas. Cross-asset demonstration that the structure is not sector-specific. Reinforces the possibility of Power-sector applications.

---

## Sector-level action items

Framed for desk-level use, not deal-specific. Deal-specific versions live in the weekly pipeline overlay if produced.

1. **Curtailment-aware capture-rate stress test.** For any as-produced solar PPA in the book with CAISO NP15/SP15 or ERCOT-West exposure: run the operating model with capture rate haircut 10-15 points below underwriting. If DSCR compresses below covenant at that haircut, flag for attention before the FERC June ruling lands.
2. **State-level siting buffer.** Add 9-12-month approval-timeline buffer sensitivity to any solar development that assumes zero state-level siting escalation. Not deal-specific — a sector risk-premium adjustment.
3. **BESS as structural substitution.** Track BESS deployment pace relative to curtailment pattern. If BESS deployment is not visibly accelerating in the curtailed hubs by July 2026, the substitution-closure assumption in the structural hypothesis weakens.
4. **Watch for FERC market-design proposals** as early signals of the curtailment-pricing regulatory response.
5. **Cross-asset ILS-wrap watch** — monitor for any sidecar or cat-bond structure explicitly naming BESS or solar operational risk. First such print would be a material sector signal.

---

## Sector reading — one-line summary

The sector is running two structural questions in parallel: **can the curtailment pattern survive into summer demand** (answer visible by July), **and can state-level siting-restriction be contained to DC** (answer visible within 30 days). FOMC and FERC both land inside that window. A patient sector; not a quiet one.

---

*GroundTruth V2 | Power Sector Alpha | 2026-04-19 | Private & Confidential*
