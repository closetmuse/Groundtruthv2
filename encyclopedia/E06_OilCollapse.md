# GROUNDTRUTH EVENT ENCYCLOPEDIA
# Event: Oil Price Crash
# Code: E06
# Legacy Code: E11 (GroundTruth v1)
# Trigger Date: 2014-06-20
# Trigger Event: Brent begins sustained decline from $115 — OPEC November 2014 no-cut decision accelerates collapse
# Primary Regime: R3 — Commodity Shock
# Secondary Regime: None — pure commodity deflation, no credit compound
# Pattern Match Tags: C08, C09, C12, C05, C13
# Fingerprint Date: 2016-01-20 (trough — Brent $27.10)
# PRD Build Priority: 5
# Status: LOCKED
# Verified by Sri: Yes — practitioner notes included
# Last Updated: April 2026

---

## SECTION 1 — FINGERPRINT
*12 quantitative fields at peak stress. Machine-readable for stumpy similarity matching.*
*All figures measured from FRED, EIA, Bloomberg historical. Nothing modelled.*

| Field | Value | Notes |
|-------|-------|-------|
| fingerprint_date | 2016-01-20 | Brent trough $27.10 — maximum stress |
| brent_level | $27.10/bbl | Down 76% from June 2014 peak of $115 |
| brent_delta_90d | -28.3% | 90-day move at trough |
| ust_10y_level | 2.05% | Stable — Fed hiking cautiously, no credit stress |
| ust_10y_direction | Stable | First Fed hike December 2015 — minimal market impact |
| ig_spread_bps | 195 | Modest widening — energy sector specific, not systemic |
| hy_spread_bps | 800 | Energy HY blew out; non-energy HY contained |
| lme_aluminum_delta_90d | -12.1% | Demand concern but not acute — China slowdown signal |
| steel_hrc_delta_90d | -18.4% | Steel weak — China overcapacity plus demand concern |
| usd_index_direction | Strengthening | Dollar strong — commodity inverse correlation |
| regime_code | R3 | Pure commodity shock — no credit or geopolitical compound |
| distinguishing_feature | Contractual structure determined survival. Take-or-pay with creditworthy offtakers held. Oil-indexed contracts globally did not. Stress test is offtaker balance sheet, not contract language. US LNG survived; global oil-indexed LNG did not. |

---

## SECTION 2 — SIGNAL SEQUENCE
*What appeared in the 90 days before trough stress, organized by lag.*
*Hindsight note: sequence reconstructed retrospectively. Forward-looking signal selection will differ.*

### Early (60–90 days before trough — Oct to Nov 2015)
| Signal type | What appeared | Sources that were early |
|-------------|---------------|------------------------|
| OPEC production signal | Saudi Arabia signaling market share defense over price | Wire services, IEA |
| Commodity price sustained decline | Brent below $60 and falling — 14-month decline visible | EIA, commodity feeds |
| Sponsor equity stress | Oil and gas developers cutting capex — visible in earnings | Company filings |
| EM currency pressure | Petrocurrency weakness — Nigeria, Venezuela, Russia | FRED, FX data |
| Offtaker credit watch | Oil-indexed LNG offtaker creditworthiness flagged | IJGlobal, rating agencies |

### Mid (30–60 days before trough — Nov 2015 to Jan 2016)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| HY energy spread blow-out | Energy HY spreads exceeded 1500bps | FRED, Bloomberg |
| Developer project cancellations | Upstream oil and gas capex cuts accelerating | Company filings |
| LNG SPA renegotiation attempts | Oil-indexed offtakers seeking price review | IJGlobal, PFI |
| Bank appetite shift | Lenders reducing energy sector exposure limits | Deal-level conversations |
| Construction cost deflation | Steel and aluminum falling — EPC cost tailwind for non-energy infra | EIA, industry data |

### Late (0–30 days before trough — Jan 2016)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Brent sub-$30 breach | January 20 2016 $27.10 — psychological floor broken | Commodity feeds |
| Sponsor distress signals | Several LNG developers unable to proceed with FIDs | IJGlobal |
| Offtaker balance sheet stress | Oil-indexed counterparties visibly impaired | Rating agencies |
| US LNG take-or-pay holding | US SPAs confirmed performing — creditworthy counterparties | DOE, IJGlobal |
| Infrastructure debt bifurcation | Oil-linked assets repriced; contracted infrastructure held | Deal-level |

### Lagging (after trough — Q1 2016 onward)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Commodity price recovery | Brent began recovery from $27 floor | EIA |
| Sponsor restructurings | Several oil-indexed LNG projects restructured | IJGlobal, PFI |
| US LNG vintage validation | Deals closed 2012–14 confirmed performing through collapse | Moody's, deal reporting |
| OPEC deal | November 2016 production cut agreement — price floor established | IEA, wire services |
| Infrastructure spread normalization | Non-energy infrastructure spreads tightened back | Market data |

---

## SECTION 3 — INFRASTRUCTURE FINANCE IMPACT
*Quantified deal-level impact. Source mix: Moody's 1983–2023, IJGlobal, DOE, EIA.*
*Directional estimates labelled. Measured numbers from Moody's vintage cohort data.*

| Metric | E06 observed | Notes |
|--------|-------------|-------|
| Oil and gas 10-year CDR | 7.2% | Moody's 40-year dataset — highest among core infrastructure |
| Non-energy infrastructure CDR | 3.4% | Held through collapse — contractual protection confirmed |
| US LNG take-or-pay performance | 100% — all performing | SPAs with investment-grade counterparties held |
| Oil-indexed LNG performance | Multiple restructurings | Offtaker balance sheet stress broke contracts |
| Construction cost impact | Deflationary tailwind | Steel -18%, aluminum -12% — EPC cost reduction for non-energy |
| New LNG FID activity | Near-zero 2015–16 | No new projects sanctioned at trough |
| Spread widening — energy assets | 150–300 bps | Oil-linked infrastructure repriced sharply |
| Spread widening — contracted infra | Minimal — 20–40 bps | Take-or-pay protection confirmed empirically |
| Verification latency — contracts | Near-zero | Contract performance or failure visible within 90 days of trough |
| Verification latency — balance sheet | 6–12 months | Offtaker impairment took 2–3 quarters to appear in filings |

**Bilateral alpha summary:**
- Risk side (oil-indexed assets, A12 global, A15 oil pipelines): severity 8/10. Timeline 3–6 months. Mechanism: offtaker balance sheet stress breaking oil-indexed contract economics.
- Opportunity side (contracted non-energy infrastructure): magnitude 6/10. Construction cost deflation created EPC budget tailwind for solar, wind, transmission deals closing 2015–16.
- Critical validation: US LNG take-or-pay with investment-grade counterparties is the single most empirically validated contractual protection in 40 years of Moody's data.

---

## SECTION 4 — TRANSMISSION MECHANISM
*Full causal chain from macro trigger to deal-level impact.*
*Every link states the mechanism, the asset class, and the timeline.*

**Primary chain — risk (oil-indexed infrastructure):**
OPEC market share decision June 2014 → sustained Brent decline begins → oil-indexed LNG SPA economics invert → offtaker revenue falls with oil price → offtaker balance sheet stressed → offtaker seeks SPA renegotiation or defaults → lender collateral value impaired → deal restructuring required.
Timeline: 12–18 months from first price signal to offtaker balance sheet stress reaching lender.

**Primary chain — survival (US LNG take-or-pay):**
Brent collapse → US LNG SPA pricing fixed or Henry Hub-linked — not oil-indexed → offtaker obligation unchanged regardless of oil price → take-or-pay enforced → investment-grade counterparties (major European utilities, Japanese trading houses) honor obligations → US LNG lenders experience zero impairment through collapse.
Timeline: immediate confirmation — contract structure determined outcome within first 90 days.

**The offtaker balance sheet test:**
The question is never whether the take-or-pay contract exists. The question is whether the offtaker has the balance sheet to honor it when the commodity moves against them. Oil-indexed offtakers in 2014–16 did not. US Henry Hub-linked offtakers did. This test must be applied to every contracted infrastructure deal at underwriting — not the contract language, the counterparty balance sheet under stress.

**Parallel opportunity chain (non-energy infrastructure):**
Oil price collapse → steel and aluminum prices fall 18–22% → EPC construction costs deflate → non-energy infrastructure deals closing 2015–16 benefit from budget tailwind → solar, wind, transmission deals achieve better-than-underwritten EPC outcomes → vintage 2015–16 non-energy infrastructure outperforms.

**2026 Hormuz parallel:**
Hormuz is the inverse — commodity spike not collapse. But the offtaker balance sheet test applies identically. The stress test for any contracted infrastructure deal in 2026 is: can the offtake counterparty honor obligations if energy costs remain elevated for 24 months? The mechanism is symmetric.

---

## SECTION 5 — RESOLUTION SIGNALS
*What ended the stress. First indicators of normalization.*

**What ended the stress:**
- OPEC November 2016 production cut agreement — first coordinated cut in 8 years
- US shale production decline — market rebalancing via supply response
- Brent recovery above $50 — offtaker balance sheet stress eased
- Chinese demand stabilization — commodity demand floor established

**First indicators of normalization (earliest appearance):**
1. US shale rig count bottoming — June 2016 (supply response visible)
2. OPEC informal talks beginning — September 2016 (cut signaling)
3. Brent sustained above $45 — August 2016
4. Oil-indexed SPA renegotiations concluding — H2 2016
5. New LNG FID pipeline beginning to rebuild — 2017

**Recovery timeline by asset class:**
- A12 US LNG (take-or-pay): no recovery needed — performed continuously
- A12 Oil-indexed LNG: restructuring completed 2016–18
- A14 Gas pipelines (take-or-pay): held — fee-based revenues unaffected
- A15 Oil pipelines (volume-linked): recovery 2017 as volumes recovered
- A04 Solar / A06 Wind: benefited — construction cost deflation tailwind through 2016

**What did not resolve quickly:**
- Global LNG oversupply — persisted 2016–19 as projects sanctioned in 2012–14 came online
- Oil-indexed contract structures — fundamentally repriced; oil-indexed LNG as a structure declined
- Upstream oil and gas capex — took until 2017–18 to recover meaningfully

**Sri practitioner notes:**
US LNG take-or-pay contracts with investment-grade counterparties survived the entire 2014–16 collapse without impairment. The real uncertainty at the time was not whether the contract would be honored — it was whether the offtaker had the balance sheet to honor it when the commodity moved so sharply against them. The deals that held were the ones where we had stress-tested the counterparty, not just read the contract. Oil-indexed structures globally did not survive because the offtaker economics broke before the legal obligation did. The lesson applied directly to Hormuz 2026 — the first question on any contracted infrastructure deal is offtaker balance sheet under a 24-month stress scenario, not contract language.

---
*GroundTruth Event Encyclopedia — E06 Oil Price Crash 2014-16*
*PRD Schema v2.0 — Five-section standard*
*Migrated from: GroundTruth_v1/encyclopedia/Event_E11_OilCollapse.md*
*For internal use only*