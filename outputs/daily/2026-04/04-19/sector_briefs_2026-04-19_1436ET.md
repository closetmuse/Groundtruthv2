GROUNDTRUTH — SECTOR BRIEFS
April 19, 2026  |  14:36 ET (Sunday PM capture, EOD)  |  R0 Compound Stress persists — Hormuz escalation read strengthens on second mainstream source  |  Active book: 0 RED, 69 AMBER, 429 GREEN (post test-signal cleanup)

One thing matters this capture. **GS-1066 (Bloomberg Law Energy, today):** *"Hormuz Shipping Traffic Grinds to a Halt as Tensions Deepen."* This is the **second mainstream-source confirmation** after Oil Price's GS-1017 yesterday EOD. Framing is "grinds to a halt" — closer to escalation than to this morning's Al Jazeera "impasse" read (GS-1025). The Hormuz narrative this weekend is now **three-source and directionally escalating**: Oil Price (Apr 18) → Al Jazeera AM (Apr 19) neutral-to-softening → Bloomberg Law PM (Apr 19) escalating. Monday Brent open remains the market verification, but the probability of a Brent gap-up has strengthened vs the morning read.

Second thing to flag. **GS-1065 (Bloomberg Law, today):** *"US Energy Chief Says Gas May Not Dip Below $3 Until Next Year."* This is direct DOE forward-guidance on HH contradicting this morning's $2.67 refresh. If DOE's view holds, the supply-side catch-down I logged as ALF-15-4 hardening (weak-neutral) this morning was noise, not mechanism. Forward direction resets.

Third thing — **data hygiene action taken this capture.** Three test signals (GS-1039, GS-1040, GS-1041) I wrote during this morning's scorer v2.3.0 smoke-testing were contaminating the production DB as REDs. Marked as FILTERED with `TEST_CONTAMINATION` filter_reason. Documented in docs/CHANGELOG.md. Not a regression — a one-time hygiene issue from today's session. Active-book counts above reflect post-cleanup state.

================================================================
FRAMEWORK COVERAGE SCAN
================================================================

15 axes.

- **LIVE (regime-level):** Macro overlay (Hormuz escalation strengthening via GS-1066 + persistent-damage read via GS-1060 FT "Impact of Iran war will hurt US even after conflict ends"). R0 persists, E01 GFC 78%.
- **LIVE (deal-economic):** LNG Axis 1 (HH-JKM/TTF arbs — DOE forward guidance contradicting morning HH refresh, mechanism-ambiguity gets worse), Power Axis 3 (FERC Large Load Docket June 2026 still binding), Power Axis 4 (curtailment Day 7, pattern unchanged this capture — afternoon).
- **HARDENING:** LNG Axis 4 (DOE/FERC export auth — no new prints).
- **QUIET, explicit:** LNG Axis 2 (construction), LNG Axis 3 (Waha), Power Axis 1 (FEOC), Power Axis 2 (construction), DC Axes 1, 3, 5, 6, 7.
- **INTERESTING BUT SUB-THRESHOLD:** Power Axis / Gas-alternative (GS-1063 Japanese $2B gas plant for Hawaii — sector-level gas-power capex datapoint, not deal-specific to book but context for gas-competition-with-renewables reads). Power Axis / Policy context (GS-1054 DOE Solar Achievements Timeline — policy-continuation narrative).

================================================================
LIVE PRICES AS OF 14:36 ET CAPTURE
================================================================

Prices identical to 06:13 ET — markets closed Sunday. Key anchors:

| Series | Value | 7d | 30d | Source date |
|---|---|---|---|---|
| wti_usd_bbl | $82.59 | -12.52% BREACH | n/a | 2026-04-17 |
| brent_usd_bbl | $90.38 | n/a | n/a | 2026-04-17 |
| henry_hub_usd_mmbtu | $2.67 | -6.69% | -6.69% | 2026-04-17 |
| jkm_usd_mmbtu | $15.00 | -23.04% BREACH | -3.19% | 2026-04-17 |
| ttf_eur_mwh | 38.769 | -14.42% BREACH | -23.58% BREACH | 2026-04-17 |
| ust_10y_pct | 4.32% | n/a | n/a | 2026-04-16 |
| usd_index | 98.1 | -0.91% | -1.10% | real-time |

**ERCOT fuel mix at 14:36 ET:** gas 25.9%, solar 29.8%, wind 28.3% — afternoon solar active, normal Sunday afternoon mix. Curtailment pattern presumably continuing but DA file is for Monday delivery.

**DOE-guidance read against morning HH refresh:** if GS-1065 is DOE's firm view, HH likely rebounds to $2.80-3.00 range by next refresh. That re-compresses HH-JKM arb toward morning levels. The mechanism-ambiguity of ALF-15-4's supply-side widening this morning now reads as **more likely noise than mechanism** — supply-side widening that promptly reverses on policy-guidance publication is weak evidence for the Structural thesis.

================================================================
1. US LNG & NATURAL GAS
================================================================

**Axis 1 — HH-JKM / HH-TTF arbitrage.** LIVE with directional reset. GS-1065 (Bloomberg Law) DOE Secretary guidance that HH won't dip below $3 until 2027 directly challenges this morning's $2.67 refresh interpretation. Two readings:

- **Reading A (weather-driven noise):** HH hit $2.67 on a temporary weather / inventory blip; DOE's view anchors to fundamentals and HH rebounds inside a week. If correct, this morning's ALF-15-4 hardening-indicator read (supply-side widening, weak-neutral) downgrades to **effectively zero** — the widening is transient.
- **Reading B (DOE-cheerleading, HH independent):** DOE Secretary is talking up HH to support domestic producers and LNG-export economics; the $2.67 print reflects actual supply loosening and HH stays sub-$3 near-term. If correct, morning read stands.

Weight of evidence: Reading A is more likely given FRED data is typically lagging, DOE Secretary usually reflects internal forecast, and $2.67 is a 5-day-stale-then-refreshed print rather than a tape-wise established level. **ALF-15-4 hardening-indicator log should be revised downward** — supply-side widening is likely noise. See ALF status section.

**Axis 2 — Construction costs.** QUIET.

**Axis 3 — Waha basis.** QUIET.

**Axis 4 — DOE / FERC export authorization.** HARDENING, no new prints.

**VG merchant-risk lens:** no direct VG news. JKM at $15 unchanged on a Sunday, so merchant-margin compression continues. Implicit watch only.

================================================================
2. US POWER MARKETS (RENEWABLES)
================================================================

**Axis 1 — FEOC / Supply chain.** QUIET.

**Axis 2 — Construction costs.** See LNG Axis 2.

**Axis 3 — Interconnection / FERC.** LIVE — binding June 2026 FERC Large Load Docket ruling unchanged.

**Axis 4 — Power price movement / curtailment.** Day 7 of pattern. No new DA data this capture (ERCOT/CAISO DA runs are ahead of the afternoon; morning brief captured today's DA prints).

**Gas-power sector context (sub-threshold):** GS-1063 (Power Magazine) Japanese group proposes $2B gas-fired plant for Hawaii. Not a pipeline exposure but **a datapoint that gas-power capex announcements are continuing at material scale alongside renewables slowdown**. Relevant to the ALF-20260417-2 structural hypothesis — if gas-power baseload is aggressively bid during the curtailment regime, the "BESS as substitution" path faces gas-competition headwinds not fully priced in current merchant-tail assumptions.

================================================================
3. DATA CENTERS
================================================================

**Axis 1 — Hyperscaler / sovereign-AI durability.** No new prints this capture.

**Axis 2 — Siting / local-government.** No new prints beyond morning Tennessee / Maine coverage. ALF-20260419-1 siting-spread candidate (ALF-20260420-W1) trajectory unchanged.

**Axes 3-7:** QUIET.

**ILS structural-finance thread:** no new Artemis / SIFMA prints this afternoon. ALF-20260419-1 ladder at 18 prints unchanged. Monday / Tuesday Artemis tape is the next corroboration window.

================================================================
MACRO OVERLAY
================================================================

- **GS-1060 "Impact of Iran war will hurt US even after conflict ends, economists warn" (FT Markets, wt=72.0):** economist-consensus post-war persistent-damage framing. Fits the R0 persistence thesis and the E01 GFC encyclopedia match. Not actionable as a new mechanism but reinforces regime duration.
- **GS-1061 "The stock market's new approach to valuation" (FT Markets, wt=72.0):** valuation-regime commentary. High score partly from cluster-amplifier firing on shared structural tags with GS-1060 / GS-1043 cluster. Non-trivial content but editorial framing not directly actionable.
- **GS-1066 Hormuz escalation** — covered at top.
- **GS-1043 Federal Reserve termination of enforcement with Credit Agricole:** regulatory-action-level, normal Fed tape, wt=61.8.
- **GS-1048 EIA fuel-efficiency / gasoline demand destruction, wt=69.4:** secondary to Brent picture — demand-side tailwind for price compression but not deal-specific.
- **GS-1052 "Met Police investigate potential Iran links to London arson attacks":** escalation-adjacent but tangential.
- **Rates / credit / FX:** all unchanged.
- **Encyclopedia top match unchanged: E01 GFC 78%.**

================================================================
ALPHA — April 19, 2026  |  14:36 ET (Sunday PM)
================================================================

**No new Alpha findings this capture.**

Rationale: three of today's AMBERs reinforce existing threads rather than generate new mechanisms. Hormuz escalation (GS-1066) is a second-source confirmation of the ALF-20260417-1 regime reversal read. DOE HH-guidance (GS-1065) is a drift-check on ALF-20260415-4. Economist post-war persistence (GS-1060) reinforces regime duration but no new transmission. Zero-print day on ILS / DC / siting threads — ALF-20260419-1 substrate unchanged.

Discipline tally 2026-04-19 (two captures so far: 06:13 AM, 14:36 PM):
- **New ALFs issued:** 1 total today (ALF-20260419-1 from the ILS recognition pass earlier this evening)
- **Hardening indicator logs appended:** 3 AM (ALF-15-4 weak-neutral, ALF-17-1 softening, ALF-17-2 strong-persistence) + 2 PM (see below)
- **Watch items opened:** 2 (Europe demand-compression 2/3, ALF-20260420-W1 state-level siting-restriction spread)

================================================================
PENDING ALF STATUS CHECK + HARDENING LOG
================================================================

- **ALF-20260415-1 (JKM-TTF bifurcation, Non-structural):** HIT per 2026-04-18 18:00 resolution pass. Unchanged.
- **ALF-20260415-2 (crude 7d reverts, Non-structural):** WRONG per 2026-04-18 resolution pass. Unchanged.
- **ALF-20260415-3 (Maryland flexible-load DC, Hybrid-candidate):** No new state-PUC tape. VL 2026-06-14.
- **ALF-20260415-4 (HH-LNG arb subsidy, Structural):**
  - **Hardening indicator log appended:** 2026-04-19 14:36 ET [Drift-check — DOE guidance contradicts morning supply-side read]: GS-1065 (Bloomberg Law) DOE Secretary guidance that HH won't dip below $3 until 2027 directly challenges the morning $2.67 refresh interpretation. Weight of evidence favors Reading A (weather-driven noise) — HH likely rebounds, this morning's supply-side widening is transient, hardening-indicator log from 06:13 ET should be **downgraded from weak-neutral to effectively-zero**. The Structural thesis test has not gotten meaningful demand-side evidence this weekend; it's had supply-side noise that is about to reverse. Status: unchanged PENDING, but the two-capture picture (06:13 supply-side widening + 14:36 DOE guidance reversing it) demonstrates that this morning's mechanism-ambiguity read was directionally correct. No new hardening. VL 2026-05-15.
- **ALF-20260415-5 (BofA gas / Fed pressure, Non-structural):** No new tape. VL 2026-06-14.
- **ALF-20260416-1 (JKM-TTF widens further, Non-structural):** WRONG per 2026-04-18 resolution pass. Unchanged.
- **ALF-20260416-2 (Wahba positioning, Non-structural):** GS-986 "oil patch securitisation" (now linked to ALF-20260419-1 as cross-asset generalization) remains a weak hardening indicator. VL 2026-05-16.
- **ALF-20260416-3 (Solar PPA Q1 divergence, Non-structural with structural hypothesis):** VL 2026-07-15.
- **ALF-20260417-1 (Crude follows spot LNG on Hormuz, Non-structural candidate-HIT):**
  - **Hardening indicator log appended:** 2026-04-19 14:36 ET [At-risk reading strengthens — second mainstream source confirming escalation]: GS-1066 (Bloomberg Law Energy) *"Hormuz Shipping Traffic Grinds to a Halt as Tensions Deepen"* published today PM. This is the second mainstream-source confirmation of Hormuz deterioration after Oil Price GS-1017 yesterday. Al Jazeera AM GS-1025 "impasse" read now looks like the outlier, not the consensus. Three-source ladder directionally escalating (Oil Price → Al Jazeera neutral → Bloomberg Law escalating). **Candidate-HIT status returns to at-risk**, probability of Monday Brent gap-up strengthens materially vs morning read. VL 2026-05-01.
- **ALF-20260417-2 (CAISO/ERCOT curtailment, Non-structural with structural hypothesis):** No new curtailment DA this afternoon. Day-7 pattern from morning capture intact. VL 2026-05-17.
- **ALF-20260419-1 (ILS-wrapped DC senior debt IG uplift, Non-structural with structural hypothesis):** No new structural-finance prints this afternoon. 18-print substrate from the morning adjacency-log unchanged. Primary VL 2026-07-18 / extended 2026-10-16.

PENDING COUNT: 8 | HIT: 1 | EARLY: 0 | LATE: 0 | WRONG: 2
At-risk pending market verification: 1 (ALF-20260417-1 — strengthened back toward at-risk on GS-1066)
Hardening indicator updates this capture: 2 (ALF-15-4 downgrade-to-zero, ALF-17-1 at-risk-strengthening)

================================================================
SYSTEM STATUS / DATA HYGIENE
================================================================

- **Runtime:** 171s.
- **Signals:** 16 classified (145 dupes — normal Sunday afternoon rate). 0 RED, 10 AMBER, 6 GREEN on new this capture; 69 AMBER / 429 GREEN / 0 RED on the current active book (post test-signal cleanup).
- **Source health:** 35/37 firing. Rigzone + Windpower Monthly silent (pre-existing).
- **Health panel:** 16/18 HEALTHY 89% — vastly cleaner than 06:13 ET (7/18 FAILING) post-recalibration. GS-3 now reading correctly at 38% (10 fresh / 26 post-dedupe) GREEN. GE-1, GE-2, GPi-2, GT-1 all GREEN under new calibration. GS-1 AMBER at 95% (2-source floor). GE-3 AMBER at 23 misses (unchanged borderline).
- **Test-signal cleanup this capture:** GS-1039, GS-1040, GS-1041 (synthetic `https://x.test/*` signals from this morning's scorer v2.3.0 smoke-testing) marked as FILTERED with TEST_CONTAMINATION filter_reason. Active-book counts reflect post-cleanup state. Workflow lesson: scorer/classifier smoke tests should mock the signals in memory only, not hit the DB via `classify_batch`.
- **Drive digest 403:** pre-existing, not a regression.
- **Encyclopedia match:** E01 GFC 78% — unchanged.

================================================================

Tape tone 2026-04-19 EOD: Hormuz tightens, HH guidance firm
