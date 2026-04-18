# GROUNDTRUTH EVENT ENCYCLOPEDIA
# Event: Global Financial Crisis
# Code: E01
# Trigger Date: 2008-09-15
# Trigger Event: Lehman Brothers files Chapter 11 — global credit markets freeze within 72 hours
# Primary Regime: R2 — Credit Stress
# Secondary Regime: R0 — Compound (commodity shock overlaps from oil spike H1 2008)
# Pattern Match Tags: C02, C06, C07, C12, C11
# Fingerprint Date: 2008-10-10 (peak stress — VIX 89, credit markets frozen)
# PRD Build Priority: 2
# Status: DRAFT — Sri practitioner notes pending
# Verified by Sri: No — pending
# Last Updated: April 2026

---

## SECTION 1 — FINGERPRINT
*12 quantitative fields at peak stress. Machine-readable for stumpy similarity matching.*
*All figures measured from FRED, Bloomberg historical. Nothing modelled.*

| Field | Value | Notes |
|-------|-------|-------|
| fingerprint_date | 2008-10-10 | VIX peak 89.53 — credit markets fully frozen |
| brent_level | $77.70/bbl | Falling sharply from $147 July 2008 peak |
| brent_delta_90d | -34.2% | Commodity shock reversing as demand destruction hit |
| ust_10y_level | 3.85% | Falling — flight to safety bid driving yields down |
| ust_10y_direction | Falling | From 4.1% pre-Lehman; Fed cutting aggressively |
| ig_spread_bps | 590 | BBB OAS October 2008 — historic blow-out |
| hy_spread_bps | 1,950 | HY spread October 2008 — near-shutdown |
| lme_aluminum_delta_90d | -28.4% | Demand destruction — smelters curtailing |
| steel_hrc_delta_90d | -22.1% | Construction demand collapse |
| usd_index_direction | Strengthening | Dollar surge — flight to safety |
| regime_code | R2 | Credit stress primary; R0 compound with commodity reversal |
| distinguishing_feature | Financing markets broke before infrastructure assets. Assets kept performing. Lenders faced liquidity cost spikes and invoked MAC/MAE on committed deals with performing collateral. Stress was in bank liability side, not asset side. |

---

## SECTION 2 — SIGNAL SEQUENCE
*What appeared in the 90 days before peak stress, organized by lag.*
*Informs GS source prioritization and GE weighting.*
*Hindsight note: sequence reconstructed retrospectively. Forward-looking signal selection will differ.*

### Early (60–90 days before peak — July to Aug 2008)
| Signal type | What appeared | Sources that were early |
|-------------|---------------|------------------------|
| Commodity reversal | Oil peaked $147 July 11 — began decline | EIA, commodity feeds |
| Bank equity stress | Fannie/Freddie conservatorship August 2008 | FT, WSJ, wire services |
| Monoline stress | Ambac and MBIA ratings under pressure from Q1 2008 | Rating agency releases |
| Credit spread widening | IG spreads began widening from 150bps toward 250bps | FRED BBB OAS |
| Sponsor caution | Infrastructure M&A pipeline beginning to slow | IJGlobal, PFI |

### Mid (30–60 days before peak — Aug to mid-Sep 2008)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Interbank stress | LIBOR-OIS spread blowing out — bank funding stress visible | FRED |
| Deal flow freeze | Infrastructure syndications stalling — banks pulling commitments | PFI, IJGlobal |
| Lehman counterparty risk | Lehman CDS spreads pricing default | CDS market |
| BDC and leveraged finance stress | CLO market freezing — leveraged loan secondary collapsing | Trade press |
| Equity market decline | S&P 500 down 20% from peak — risk appetite collapsing | Market data |

### Late (0–30 days before peak — Sep 15 to mid-Oct 2008)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Lehman filing | September 15 2008 — immediate global credit freeze | All sources simultaneously |
| Money market break | Reserve Primary Fund broke the buck Sep 16 | WSJ, wire |
| LIBOR spike | 3-month LIBOR hit 4.82% — bank funding costs exploded | FRED |
| MAC/MAE invocations | Lenders began invoking material adverse change on committed deals | Deal-level — not public |
| Infrastructure deal freeze | New financial closes halted — committed deals repriced or withdrawn | IJGlobal |

### Lagging (after peak — Q4 2008 onward)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Asset performance held | Infrastructure assets continued operating and paying debt service | Asset-level reporting |
| Distressed sale pressure | Lenders marking positions and pushing distressed sales | Secondary market |
| Rating downgrades | Infrastructure ratings pressure — primarily via sponsor linkage | Moody's, S&P |
| TARP and policy response | October 3 2008 TARP — began stabilizing bank funding | Government |
| Recovery divergence | Assets with long-term contracts recovered fastest | Moody's vintage data |

---

## SECTION 3 — INFRASTRUCTURE FINANCE IMPACT
*Quantified deal-level impact. Source mix: Moody's 1983–2023, IJGlobal, LBNL, FRED.*
*Directional estimates labelled. Measured numbers from Moody's vintage cohort data.*

| Metric | GFC observed | Notes |
|--------|-------------|-------|
| New deal spread widening | 150–200 bps over pre-GFC levels | IG infrastructure spreads blew from L+75 to L+225+ |
| Construction cost contingency | Fell — commodity prices collapsed | Steel and aluminum down 20–28% — cost tailwind |
| Sponsor equity injection requirement | Increased significantly | Lenders requiring more equity as debt markets froze |
| Deal flow collapse | Near-zero new financial closes Q4 2008 | IJGlobal data — worst quarter in decade |
| Mini-perm refinancing failures | Multiple — lenders could not honor commitments | MAC/MAE the mechanism |
| 2008 vintage CDR year 6 | 9.6x baseline | Moody's Exhibit 14 — measured, not modelled |
| 2008 vintage CDR year 1 | 0.07x baseline | Clean early reading — pre-stress calm |
| Infrastructure vs corporate recovery | Infrastructure outperformed after year 7 | Moody's crossover confirmed |
| Workout vs distressed sale premium | 29 percentage points | Moody's LGD data — early ID = workout; late ID = distressed sale |
| Verification latency — financing | Near-zero | Financing markets broke within 72 hours of Lehman |
| Verification latency — assets | 12–24 months | Assets kept performing; stress appeared in refinancing 2010–12 |

**Bilateral alpha summary:**
- Risk side (all construction-phase deals): severity 9/10. Financing markets froze before assets stressed. MAC/MAE on committed deals with performing collateral.
- Opportunity side (distressed debt, post-stress vintage): magnitude 8/10. 2009 vintage assets acquired at distressed pricing outperformed for a decade.
- Critical pattern: the lender who identified bank CDS spread widening as the leading indicator had weeks, not days, of advance warning before the MAC/MAE calls arrived.

---

## SECTION 4 — TRANSMISSION MECHANISM
*Full causal chain from macro trigger to deal-level impact.*
*Every link states the mechanism, the asset class, and the timeline.*

**Primary chain — credit stress (all infrastructure):**
Lehman filing Sep 15 → global interbank market freeze within 72 hours → LIBOR-OIS spread explosion → bank funding cost spikes → committed infrastructure loans become uneconomic for lenders at committed pricing → MAC/MAE invocations begin → in-flight deals repriced or withdrawn → new financial closes halt → mini-perm refinancing windows close → performing assets cannot refinance → covenant breach follows 12–18 months later as mini-perms mature without refinancing options.
Timeline to first capital stack impact: 72 hours (financing). Timeline to asset-level stress: 12–24 months (refinancing cliff).

**Secondary chain — monoline collapse:**
Ambac and MBIA under pressure from Q1 2008 → bond insurance wraps become worthless → wrapped infrastructure bonds reprice → municipal and infrastructure bond market loses credit enhancement mechanism → funding cost for availability-payment P3s rises → deals relying on monoline wraps face restructuring.
Timeline: 6–12 months from first monoline stress signal to deal-level restructuring.

**Why infrastructure assets outperformed despite credit stress:**
Contracted cash flows continued. Long-term offtake agreements with investment-grade counterparties performed. The stress was entirely in the financing structure — the liability side — not the asset. Lenders who could hold rather than sell recovered. The 29pp workout premium over distressed sale is the quantified cost of forced selling vs patient workout.

**The leading indicator that mattered:**
Bank CDS spreads. When Lehman CDS began pricing default in August 2008 — 6 weeks before filing — lenders monitoring bank counterparty credit had advance warning that MAC/MAE calls were coming. The infrastructure deal teams watching asset performance had none.

**BDC gates parallel (2026):**
BlackRock HLEND and Blackstone BCRED gates activated March 7 2026. This is the liability-side stress signal — identical mechanism to 2008 bank funding stress. Infrastructure assets are performing. The question is whether lenders can still fund at committed prices. Monitor BDC gate expansion and bank CDS spreads, not asset performance metrics.

---

## SECTION 5 — RESOLUTION SIGNALS
*What ended the stress. First indicators of normalization.*
*Used by GI to identify early recovery signals in current BDC stress.*

**What ended the stress:**
- TARP October 3 2008 — $700B bank capital injection stabilized funding markets
- Fed emergency facilities — TALF, CPFF, MMIFF — restored short-term credit markets
- LIBOR-OIS spread normalization — 3-month LIBOR fell from 4.82% to under 1% by mid-2009
- Infrastructure asset performance held — no mass defaults, demonstrating asset quality
- 2009 stimulus — ARRA infrastructure spending created new origination pipeline

**First indicators of normalization (earliest appearance):**
1. LIBOR-OIS spread compression — November 2008 (TARP working)
2. Money market fund stabilization — October 2008 after Treasury guarantee
3. Bank CDS spreads falling — Q1 2009 as TARP capital deployed
4. First new infrastructure financial closes — Q2 2009 (6 months after peak)
5. IJGlobal deal flow recovering — H2 2009

**Recovery timeline by asset class:**
- Availability-payment P3s: fastest — zero revenue impact, contracted cash flows held
- Long-term contracted power: fast — offtake agreements performed
- Merchant generation: slow — demand destruction hit revenues 2009–10
- Construction-phase deals: slowest — refinancing cliff hit 2010–12 as mini-perms matured

**What did not resolve quickly:**
- Mini-perm refinancing cliff — persisted 2010–13 as 3–5 year construction debt matured
- European sovereign debt crisis followed 2010–12 — second wave of infrastructure stress
- Monoline insurance market — never recovered; bond insurance as a product effectively ended
- Spread normalization — infrastructure spreads did not return to pre-GFC levels until 2013–14

**The 2008 vintage warning for 2026:**
2008 vintage year 1 CDR was 0.07x baseline — appeared clean. By year 6 it reached 9.6x baseline. The 2020–21 vintage is currently at 0.3x baseline. Its stress window falls 2023–2027. The GFC precedent says clean early readings are not safety — they are the pre-stress calm.

**Sri practitioner notes:**
Bank funding costs spiked immediately and banks restricted new lending to key 
relationship clients only — not asset quality, not deal merit — relationship 
capital determined who got funded. MAC/MAE was invoked selectively where banks 
needed liquidity and could not honor commitments at original pricing. Sponsors 
bifurcated sharply: those with balance sheet capacity and genuine urgency pushed 
forward and absorbed the cost increase; those without either stalled or walked. 
Credit committees ran on near-daily liquidity reviews driven by interbank 
dependency exposure — the question in every committee was not "is this a good 
asset" but "what is our interbank exposure today and how much new commitment 
capacity do we have." The same dynamic appeared in Ukraine 2022 — bank funding 
cost spikes drove the same relationship-first triage, same MAC selectivity, same 
sponsor bifurcation. The pattern is regime-invariant: credit stress always hits 
the liability side first and the asset side months later.

---
*GroundTruth Event Encyclopedia — E01 Global Financial Crisis*
*PRD Schema v2.0 — Five-section standard*
*For internal use only*