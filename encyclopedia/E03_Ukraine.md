# GROUNDTRUTH EVENT ENCYCLOPEDIA
# Event: Ukraine/Energy Crisis
# Code: E03
# Legacy Code: E18 (GroundTruth v1)
# Trigger Date: 2022-02-24
# Trigger Event: Russian forces invade Ukraine — European gas supply disruption begins immediately
# Primary Regime: R3 — Geopolitical Supply Shock
# Secondary Regime: R0 — Compound (rate stress overlaps from March 2022 onward)
# Pattern Match Tags: C03, C08, C09, C05, C12
# Fingerprint Date: 2022-03-15 (peak stress conditions)
# PRD Build Priority: 1
# Status: LOCKED
# Verified by Sri: Partial — practitioner notes pending
# Last Updated: April 2026

---

## SECTION 1 — FINGERPRINT
*12 quantitative fields at peak stress. Machine-readable for stumpy similarity matching.*
*All figures measured from FRED, EIA, Bloomberg historical. Nothing modelled.*

| Field | Value | Notes |
|-------|-------|-------|
| fingerprint_date | 2022-03-15 | Date of peak stress conditions |
| brent_level | $127.98/bbl | Intraday peak March 8; settled ~$127 March 15 |
| brent_delta_90d | +78.3% | From $71.82 Dec 2021 to $127.98 |
| ust_10y_level | 2.15% | Rising — Fed had not yet hiked at fingerprint date |
| ust_10y_direction | Rising | From 1.51% Jan 2022; full hike cycle begins March 16 |
| ig_spread_bps | 165 | BBB OAS at peak stress |
| hy_spread_bps | 450 | HY spread March 2022 |
| lme_aluminum_delta_90d | +19.2% | Energy-intensive smelter cost spike |
| steel_hrc_delta_90d | +24.1% | Global supply chain plus energy input compound |
| usd_index_direction | Strengthening | Flight to safety plus Fed expectation |
| regime_code | R3 | Geopolitical supply shock; R0 compound from March 16 Fed hike |
| distinguishing_feature | Structural supply destruction (Russian gas cannot be quickly replaced) vs transport chokepoint (Hormuz can reopen). New build LNG benefits more than operating assets or FSRUs. |

---

## SECTION 2 — SIGNAL SEQUENCE
*What appeared in the 90 days before peak stress, organized by lag.*
*Informs GS source prioritization and GE weighting.*
*Hindsight note: sequence reconstructed retrospectively. Forward-looking signal selection will differ.*

### Early (60–90 days before peak — Dec 2021 to Jan 2022)
| Signal type | What appeared | Sources that were early |
|-------------|---------------|------------------------|
| Geopolitical tension | NATO/Russia diplomatic breakdown public | Wire services, FT, defense press |
| Commodity price move | Brent +18% sustained from Nov 2021 | EIA, commodity feeds |
| Gas supply tightening | European gas storage below seasonal norm | IEA, Eurostat |
| Sponsor activity | LNG developers accelerating SPA negotiations | IJGlobal, PFI |

### Mid (30–60 days before peak — Jan to mid-Feb 2022)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Construction cost adjustment | EPC contractors flagging steel and aluminum exposure | Industry press, EPC earnings |
| Developer delays | Several offshore wind projects pausing financial close | IJGlobal, Recharge News |
| Bank credit signals | Credit committee caution on European merchant exposure | Deal-level conversations |
| OEM margin warning | Siemens Gamesa losses visible in results — flagged April 2022 | Company filings |

### Late (0–30 days before peak — Feb 24 to mid-March 2022)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Deal repricing | LNG SPA pricing moved to oil-indexed or hybrid | IJGlobal, PFI, direct market |
| Credit hesitation | European merchant power deals paused at credit committee | Bank internal |
| PPA renegotiation | European offtakers seeking price review | Trade press |
| US LNG origination surge | 19 SPAs signed in 4-month window beginning March 2022 | IJGlobal, DOE |

### Lagging (after peak — Q2 2022 onward)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| IE report revisions | Independent engineers revised EPC budgets upward | IE firms |
| Rating agency commentary | Offshore wind rating pressure flagged | Moody's, S&P |
| Official data | EIA construction cost indices confirmed +12–15% | EIA, LBNL |
| Orsted writedown | $5.55B writedown announced October 2023 — 20 months after peak | Company filing |

---

## SECTION 3 — INFRASTRUCTURE FINANCE IMPACT
*Quantified deal-level impact in 90 days following peak stress.*
*Source mix: IJGlobal, DOE, LBNL, Moody's, company filings. Directional estimates labelled.*

| Metric | E03 observed | Notes |
|--------|-------------|-------|
| New deal spread widening | 35–50 bps | Measured against pre-event comparable deals |
| Construction cost contingency | ~12–14% (from 5–8% pre-event) | EPC contract values; LBNL data |
| Sponsor unlevered IRR requirement | ~11% (from 8–9% pre-event) | Directional estimate — market conversations |
| Japanese bank appetite (JBIC/NEXI) | Held through stress | Did not withdraw — critical data point |
| Solar deals delayed or repriced | 4 in PJM/MISO Q2–Q3 2022 | IJGlobal data |
| Verification latency — EPC costs | 90–180 days | IE report lag vs sponsor knowledge of cost moves |
| US LNG opportunity window | 4–6 months | 19 SPAs signed March–June 2022; market flooded H2 2022 |
| Plaquemines FID | $13.2B, May 2022 | Largest single LNG FID of the crisis period |
| Offshore wind IRR collapse timeline | 18–20 months post-peak | Orsted writedown Oct 2023 confirms timeline |

**Bilateral alpha summary:**
- Risk side (A07 offshore wind): severity 8/10. Timeline 12–20 months post-trigger. Mechanism: rate shock plus OEM margin compression.
- Opportunity side (A12 US LNG): magnitude 9/10. Window 4–6 months from trigger. First movers captured; latecomers entered flooded market.
- Verification latency — opportunity: 29 days (near-zero — LNG origination opened immediately)
- Verification latency — risk: 12–20 months (offshore wind stress reached capital stack October 2023)

---

## SECTION 4 — TRANSMISSION MECHANISM
*Full causal chain from macro trigger to deal-level impact.*
*Every link states the mechanism, the asset class, and the timeline.*
*No direct causation claimed without named intermediate steps.*

**Primary chain — risk (A07 offshore wind):**
Russian invasion Feb 24 → European gas supply disruption → TTF spike → Brent follows → Global energy inflation → LME aluminum +19% via smelter energy cost → Steel HRC +24% via energy input → EPC construction cost indices rise → Sponsor budget contingencies exhausted → Developer equity return requirement increases → Lender credit approval hesitation → Deal repricing or delay.
Timeline to capital stack recognition: 90–180 days from commodity move to IE report revision. 12–20 months to balance sheet recognition (Orsted Oct 2023).

**Primary chain — opportunity (A12 US LNG):**
Russian gas supply destruction → Europe needs non-Russian LNG immediately → US becomes global backstop → LNG SPA demand surge → 19 SPAs signed in 4 months → US LNG developers advance FID timelines → Construction debt demand surge → Plaquemines $13.2B FID May 2022 → Market flooded H2 2022 as all developers moved simultaneously → Spreads compressed → Origination window closed.
Timeline to opportunity close: 4–6 months from Feb 24 trigger.

**Parallel chain — rate shock (tracked separately in E04):**
Geopolitical risk premium → inflation expectations → Fed accelerates hiking cycle → March 16 2022 first hike → 525bps total through July 2023 → WACC increase → Offshore wind IRR compression compounds with OEM cost inflation → Bilateral stress on A07 amplified.

**Why US LNG survived and global oil-indexed LNG did not:**
Take-or-pay contracts with creditworthy US counterparties held. Oil-indexed LNG globally saw offtaker balance sheet stress when commodity moved against them. The stress test is the offtaker balance sheet, not the contract language. Confirmed by 2014–16 oil collapse precedent (E06).

---

## SECTION 5 — RESOLUTION SIGNALS
*What ended the stress. First indicators of normalization.*
*Used by GI to identify early recovery signals in E07 Hormuz and future events.*

**What ended the stress:**
- IRA passage August 16 2022 — policy response redirected capital from European energy crisis into US renewables and LNG
- European gas storage normalization by winter 2022–23 via emergency LNG imports, demand destruction, and warm weather
- Fed hike cycle plateau — rates peaked July 2023; market began pricing cuts
- US LNG supply increase — export capacity additions absorbed European demand; spot LNG market normalized

**First indicators of normalization (earliest appearance):**
1. European gas storage returning to seasonal norms — September 2022
2. TTF forward curve flattening — October 2022
3. US LNG origination pipeline filling — IJGlobal deal flow data H2 2022
4. Siemens Gamesa and Vestas OEM results stabilizing — Q1 2023 (18 months post-trigger)

**Recovery timeline by asset class:**
- A12 US LNG: normalization H2 2022 (new build window closed; operating assets benefited through 2023)
- A07 Offshore wind: normalization 2024 (Orsted writedown Oct 2023 marked the trough)
- A04 Solar / A06 Onshore wind: faster recovery via IRA tailwind from August 2022

**What did not resolve quickly:**
- OEM manufacturing cost inflation — persisted through 2023
- Offshore wind project cancellations — Vineyard Wind stress 2024 reflects lingering effects
- European energy security premium — structural repricing, not fully unwound as of 2026

**Sri practitioner notes:**
*[To be added: What did you observe at the deal level during 2022 from the SC Project Finance desk? Which credit committees changed behavior? What did Japanese lenders do differently from European lenders? One or two sentences. This is the most defensible data in the entry.]*

---
*GroundTruth Event Encyclopedia — E03 Ukraine/Energy Crisis*
*PRD Schema v2.0 — Five-section standard*
*Replaces legacy: GroundTruth_v1/encyclopedia/Event_E18_Ukraine.md*
*For internal use only*