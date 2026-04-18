# GROUNDTRUTH EVENT ENCYCLOPEDIA
# Event: Fed Rate Hike Cycle 2022-23
# Code: E04
# Trigger Date: 2022-03-16
# Trigger Event: Fed raises rates 25bps — first hike since 2018, beginning fastest tightening cycle in 40 years
# Primary Regime: R2 — Rate Stress
# Secondary Regime: None — isolated from E03 Ukraine for independent pattern matching
# Pattern Match Tags: C02, C01, C04, C06, C12
# Fingerprint Date: 2023-07-26 (peak — Fed Funds 5.25-5.50%, terminal rate reached)
# PRD Build Priority: 3
# Status: LOCKED
# Verified by Sri: Yes — practitioner notes included
# Last Updated: April 2026

---

## SECTION 1 — FINGERPRINT
*12 quantitative fields at peak stress. Machine-readable for stumpy similarity matching.*
*All figures measured from FRED, Bloomberg historical. Nothing modelled.*

| Field | Value | Notes |
|-------|-------|-------|
| fingerprint_date | 2023-07-26 | Terminal rate reached — Fed Funds 5.25-5.50% |
| brent_level | $83.64/bbl | Stable — commodity not the driver in this regime |
| brent_delta_90d | -4.1% | Flat — confirms rate stress is independent of commodity |
| ust_10y_level | 3.97% | Rising toward 5% peak October 2023 |
| ust_10y_direction | Rising | From 1.51% Jan 2022 — 246bps rise over 18 months |
| ig_spread_bps | 148 | Elevated but not blown out — rate stress not credit stress |
| hy_spread_bps | 420 | Moderate — rate stress distinguishable from credit stress |
| lme_aluminum_delta_90d | -8.2% | Weak — demand concern from rate slowdown |
| steel_hrc_delta_90d | -11.3% | Construction activity slowing under rate pressure |
| usd_index_direction | Strengthening | Rate differential driving dollar strength |
| regime_code | R2 | Pure rate stress — independent of E03 geopolitical trigger |
| distinguishing_feature | Fastest tightening cycle in 40 years — 525bps in 16 months. WACC increase made previously-viable infrastructure deals uneconomic without repricing. Offshore wind worst affected — long construction timelines meant underwriting assumptions were 300-400bps stale by financial close. |

---

## SECTION 2 — SIGNAL SEQUENCE
*What appeared in the 90 days before terminal rate, organized by lag.*
*Hindsight note: sequence reconstructed retrospectively. Forward-looking signal selection will differ.*

### Early (60–90 days before terminal — Apr to May 2023)
| Signal type | What appeared | Sources that were early |
|-------------|---------------|------------------------|
| Inflation persistence | CPI remained above 4% despite 400bps of hikes | BLS, FRED |
| Fed language shift | Minutes showing higher-for-longer consensus forming | Fed minutes |
| Infrastructure deal slowdown | New financial closes slowing — pricing uncertainty | IJGlobal |
| Offshore wind distress | OEM losses compounding with rate stress — Siemens Gamesa | Company filings |
| Sponsor IRR gap | Developers publicly flagging return gap vs. lender pricing | Trade press, earnings |

### Mid (30–60 days before terminal — May to Jun 2023)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Terminal rate pricing | Futures markets pricing 5.25-5.50% terminal | CME FedWatch |
| Offshore wind cancellations | US offshore wind developers cancelling PPAs | Recharge News, IJGlobal |
| Solar deal repricing | Utility-scale solar deals requiring equity top-ups | IJGlobal |
| Bank credit appetite | Infrastructure lending committees tightening terms | Deal-level |
| Construction cost compound | Rate stress plus Ukraine commodity inflation simultaneous | EIA, AGC |

### Late (0–30 days before terminal — Jun to Jul 2023)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Final 25bps hike | July 26 2023 — terminal rate confirmed | Fed |
| Orsted warning | Offshore wind impairment signals — full writedown October 2023 | Company filings |
| PPA renegotiation requests | Offshore wind developers seeking PPA price increases | Recharge News |
| Infrastructure spread peak | New deal spreads at widest since 2012 | IJGlobal, PFI |
| Higher-for-longer consensus | Fed signaling no cuts in 2023 | Fed communications |

### Lagging (after terminal — Q3 2023 onward)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Orsted $5.55B writedown | October 2023 — offshore wind capital stack recognition | Company filing |
| Siemens Gamesa losses | Full year 2023 loss EUR 4.3B | Company filing |
| Vineyard Wind stress | US offshore wind restructuring signals | Trade press |
| Rate cut pricing | November 2023 — markets begin pricing 2024 cuts | CME FedWatch |
| Infrastructure deal recovery | Q1 2024 deal flow recovering on cut expectations | IJGlobal |

---

## SECTION 3 — INFRASTRUCTURE FINANCE IMPACT
*Quantified deal-level impact. Source mix: IJGlobal, Moody's, company filings, LBNL.*
*Directional estimates labelled.*

| Metric | E04 observed | Notes |
|--------|-------------|-------|
| WACC increase — infrastructure | 250-350bps | From underwriting to financial close on 2021-22 vintage |
| Offshore wind IRR gap | 3-5% below required returns | Developer public statements, earnings |
| Orsted writedown | $5.55B October 2023 | Largest single infrastructure write-off of the cycle |
| Siemens Gamesa losses | EUR 4.3B FY2023 | OEM compound: rate plus Ukraine commodity |
| US offshore wind PPA cancellations | 12+ GW cancelled or delayed 2022-23 | Recharge News, AWEA |
| New infrastructure deal spreads | L+175 to L+225 peak | vs L+125 to L+150 pre-hike cycle |
| Solar deal repricing | Equity IRR requirement up 150-200bps | Directional estimate — market conversations |
| Mini-perm refinancing stress | 2020-21 vintage facing 375bps rate increase at refi | Moody's vintage data plus FRED |
| Construction cost compound | Rate stress plus commodity inflation simultaneous | EIA, AGC — double stress |
| Verification latency — WACC | 12-18 months | Time from first hike to IE report WACC revision |
| Verification latency — OEM losses | 18-20 months | First hike March 2022 to Orsted writedown October 2023 |

**Bilateral alpha summary:**
- Risk side (A07 offshore wind, A06 onshore wind, A04 solar with long timelines): severity 8/10. WACC increase made underwriting assumptions stale by financial close. Offshore wind worst — longest construction timelines meant maximum staleness.
- Opportunity side (floating rate lenders, short-duration contracted assets): magnitude 6/10. Lenders with floating rate books benefited from margin expansion. Short-duration assets repriced faster.
- Key insight: the asset class most exposed to rate stress is always the one with the longest gap between underwriting and financial close. Offshore wind takes 4-6 years from development to close — guaranteeing maximum WACC staleness in a rising rate environment.

---

## SECTION 4 — TRANSMISSION MECHANISM
*Full causal chain from macro trigger to deal-level impact.*
*Every link states the mechanism, the asset class, and the timeline.*

**Primary chain — WACC stress (long-development assets):**
Fed hike March 2022 → SOFR rising → infrastructure lending spreads widen → WACC increases 250-350bps from underwriting assumptions → offshore wind projects underwritten at 8-9% developer IRR now require 11-12% → equity return gap opens → developer cannot absorb gap without PPA price increase → offtaker (utility) refuses PPA increase → developer cancels or restructures → lender commitment withdrawn → capital stack collapses.
Timeline: 18-24 months from first hike to deal collapse (development timeline dependent).

**Primary chain — mini-perm refinancing cliff:**
2020-21 vintage construction loans at SOFR+175 underwritten when SOFR was near-zero → SOFR rises 525bps → all-in cost moves from ~2% to ~7% → mini-perm refinancing at maturity (2024-26) faces 375bps rate increase → DSCR at refi pricing below covenant → deal cannot refinance at par → lender forced to extend, restructure, or take loss.
Timeline: stress arrives at mini-perm maturity — 2024-26 for 2020-21 vintage.

**Why offshore wind was worst affected:**
Development to financial close: 4-6 years. Underwriting to close WACC staleness: maximum in the asset class. A solar deal closes in 18-24 months — WACC staleness manageable. An offshore wind deal takes 5 years — every 100bps of rate increase over that period is 100bps of uncompensated IRR erosion. The asset class with the longest development timeline always bears maximum rate stress in a rising cycle.

**2026 relevance — current rate environment:**
Fed Funds at 3.50-3.75%. FOMC April 28 is binary — hold or hike. Infrastructure deals underwritten at 2024 rate assumptions face 150-200bps staleness already. If FOMC hikes April 28, the E04 mechanism fires again on 2024-25 vintage deals. The asset classes with longest development timelines — offshore wind, large-scale nuclear, LNG new build — are most exposed. Solar and BESS close faster and are less exposed to WACC staleness.

---

## SECTION 5 — RESOLUTION SIGNALS
*What ended the stress. First indicators of normalization.*

**What ended the stress:**
- Fed pause July 2023 — terminal rate confirmed, uncertainty resolved
- November 2023 — markets begin pricing 2024 cuts — WACC expectations fall
- First Fed cut September 2024 — rate cycle turning confirmed
- IRA tax credit transferability — provided equity IRR relief for solar and wind
- Offshore wind restructuring — market repriced; surviving projects at higher PPA prices

**First indicators of normalization (earliest appearance):**
1. CME FedWatch pricing cuts — November 2023 (forward rate expectation turning)
2. Infrastructure deal flow recovering — Q1 2024 (IJGlobal data)
3. Offshore wind PPA prices clearing at higher levels — Q2 2024
4. New issue spreads tightening — Q1 2024 as rate certainty returned
5. OEM order books recovering — Vestas Q2 2024 results

**Recovery timeline by asset class:**
- A04 Solar / A05 BESS: fastest — shorter development timelines, IRA support
- A14 Gas pipelines: minimal impact — regulated or contracted revenues held
- A06 Onshore wind: moderate — 18-24 months repricing
- A07 Offshore wind: slowest — Vineyard Wind stress persisting into 2025-26
- A02 Nuclear / A25 SMR: structural beneficiary — rate stress drove policy support

**What did not resolve quickly:**
- Offshore wind — structural repricing; several markets effectively paused
- 2020-21 vintage mini-perm cliff — arriving 2024-26 regardless of rate cuts
- OEM manufacturing capacity — Siemens Gamesa restructuring multi-year
- Developer balance sheets — writedowns impaired equity capacity for next cycle

**Sri practitioner notes:**
The rate hike cycle exposed a structural flaw in how infrastructure deals are underwritten — WACC assumptions are set at the start of development and rarely updated through the 3-5 year journey to financial close. Every 100bps of rate increase over that period is real IRR erosion that someone has to absorb. In 2022-23 the developers tried to push it to offtakers via PPA increases, offtakers refused, and the deals collapsed. The lenders who saw the WACC staleness signal early — when SOFR first moved 200bps — had 12-18 months to reduce offshore wind exposure before the Orsted writedown confirmed the thesis. The lenders who waited for the IE report revision had no time to act. This is verification latency operating in a pure rate stress regime — same mechanism, different trigger.

---
*GroundTruth Event Encyclopedia — E04 Fed Rate Hike Cycle 2022-23*
*PRD Schema v2.0 — Five-section standard*
*Separated from E03 Ukraine for independent pattern matching on rate stress signals*
*For internal use only*