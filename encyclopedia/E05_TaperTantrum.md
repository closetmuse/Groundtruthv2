# GROUNDTRUTH EVENT ENCYCLOPEDIA
# Event: Taper Tantrum
# Code: E05
# Trigger Date: 2013-05-22
# Trigger Event: Bernanke signals Fed may taper QE purchases — bond markets reprice immediately
# Primary Regime: R2 — Rate Spike
# Secondary Regime: None — pure rate shock, no commodity or credit compound
# Pattern Match Tags: C02, C01, C13, C06, C12
# Fingerprint Date: 2013-09-05 (peak — UST 10Y hit 3.0%, EM capital flight complete)
# PRD Build Priority: 6
# Status: LOCKED
# Verified by Sri: Yes — practitioner notes included
# Last Updated: April 2026

---

## SECTION 1 — FINGERPRINT
*12 quantitative fields at peak stress. Machine-readable for stumpy similarity matching.*
*All figures measured from FRED, Bloomberg historical. Nothing modelled.*

| Field | Value | Notes |
|-------|-------|-------|
| fingerprint_date | 2013-09-05 | UST 10Y at 3.0% — 140bps rise in 16 weeks |
| brent_level | $115.32/bbl | Stable — commodity not the driver |
| brent_delta_90d | +2.1% | Flat — confirms rate spike is independent of commodity |
| ust_10y_level | 3.00% | From 1.60% May 1 — 140bps in 16 weeks |
| ust_10y_direction | Rising sharply | Fastest 16-week move since 1994 bond massacre |
| ig_spread_bps | 135 | Contained — rate stress not credit stress |
| hy_spread_bps | 390 | Moderate — distinguishable from full credit stress |
| lme_aluminum_delta_90d | -6.1% | Mild weakness — EM demand concern |
| steel_hrc_delta_90d | -4.2% | Minimal — construction activity unaffected in developed markets |
| usd_index_direction | Strengthening | Rate differential capital flows — EM currency pressure |
| regime_code | R2 | Pure rate spike — shortest duration stress event in encyclopedia |
| distinguishing_feature | Shortest duration stress in dataset — 16 weeks peak to trough. Rate spike without credit stress or commodity shock. Primary damage was EM infrastructure — currency depreciation plus capital outflow simultaneously. Developed market infrastructure largely unaffected. Identifies EM exposure as the key vulnerability in a pure rate spike regime. |

---

## SECTION 2 — SIGNAL SEQUENCE
*What appeared in the 90 days before peak stress, organized by lag.*
*Hindsight note: sequence reconstructed retrospectively. Forward-looking signal selection will differ.*

### Early (60–90 days before peak — Jun to Jul 2013)
| Signal type | What appeared | Sources that were early |
|-------------|---------------|------------------------|
| Fed communication shift | Bernanke May 22 testimony — taper possibility mentioned | Fed, wire services |
| Bond market repricing | UST 10Y moved from 1.60% to 2.20% in two weeks | FRED |
| EM capital outflow | Portfolio flows reversing from EM to developed markets | IMF, World Bank data |
| EM currency pressure | BRL, INR, IDR, TRY selling off | FRED FX data |
| Infrastructure financing pause | EM infrastructure deals pausing — lender pricing uncertainty | IJGlobal |

### Mid (30–60 days before peak — Jul to Aug 2013)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| EM current account stress | India, Brazil, Indonesia current account deficits widening | IMF |
| EM central bank responses | RBI, BCB hiking rates to defend currencies | Central bank releases |
| Cross-border financing freeze | Japanese and European banks pausing EM infrastructure lending | Deal-level |
| Infrastructure IRR gap | EM infrastructure deals facing currency hedge cost increase | Trade press |
| Developed market stability | US and European infrastructure deals proceeding normally | IJGlobal |

### Late (0–30 days before peak — Aug to Sep 2013)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| UST 10Y at 3.0% | September 5 2013 — psychological ceiling breached | FRED |
| EM infrastructure cancellations | Several EM deals withdrawn — uneconomic at new rates | IJGlobal |
| Fed non-taper surprise | September 18 — Fed holds, does not taper — immediate reversal | Fed, all sources |
| Rate reversal | UST 10Y fell from 3.0% back toward 2.5% within weeks | FRED |
| EM currency stabilization | Capital flows reversed on Fed non-taper decision | FRED FX |

### Lagging (after peak — Q4 2013 onward)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Actual taper December 2013 | $10B per month reduction — orderly this time | Fed |
| EM infrastructure recovery | Deals resuming — orderly taper already priced | IJGlobal |
| Developed market unaffected | No measurable impact on US infrastructure deal flow | IJGlobal |
| Cross-border financing resuming | Japanese banks resumed EM lending H1 2014 | Deal-level |

---

## SECTION 3 — INFRASTRUCTURE FINANCE IMPACT
*Quantified deal-level impact. Source mix: IJGlobal, IMF, World Bank, FRED.*
*Directional estimates labelled. Shortest duration event — impact less severe than other R2 events.*

| Metric | E05 observed | Notes |
|--------|-------------|-------|
| UST 10Y move | +140bps in 16 weeks | Fastest since 1994 — but reversed equally fast |
| EM infrastructure deal pause | 60-90 days | Deals resumed after Fed non-taper September 18 |
| EM currency depreciation | BRL -15%, INR -14%, IDR -16% peak to trough | FRED FX data |
| Cross-border financing pause | 8-12 weeks | Japanese and European lenders paused EM exposure |
| Developed market deal impact | Minimal — near-zero | US and European infrastructure unaffected |
| Infrastructure spread widening | 15-25bps | Contained — not credit stress |
| EM infrastructure IRR gap | 50-100bps directional estimate | Currency hedge cost increase | 
| Duration of stress | 16 weeks | Shortest in encyclopedia — Fed non-taper ended it immediately |
| Verification latency — rate move | Near-zero | Bond market repriced within days of Bernanke testimony |
| Verification latency — deal impact | 4-6 weeks | Lender pricing committees slower than bond markets |

**Bilateral alpha summary:**
- Risk side (EM infrastructure — A19 toll roads, A20 ports, A21 airports in EM): severity 5/10. Short duration. Primary damage from currency depreciation and capital outflow, not rate level.
- Opportunity side (developed market infrastructure — window of spread widening): magnitude 4/10. 15-25bps spread widening created a brief entry window before reversal.
- Key insight: E05 is the control case. It shows what pure rate stress looks like without commodity or credit compound. Damage was real but contained and reversed quickly. Compare to E04 where rate stress persisted 16 months — duration is the variable that determines severity.

---

## SECTION 4 — TRANSMISSION MECHANISM
*Full causal chain from macro trigger to deal-level impact.*
*Every link states the mechanism, the asset class, and the timeline.*

**Primary chain — EM infrastructure stress:**
Bernanke taper signal May 22 → bond markets reprice immediately → UST yields rise → yield differential narrows between EM and developed markets → EM portfolio capital outflows begin → EM currencies depreciate 14-16% → EM infrastructure project revenues in local currency but debt service in USD → currency mismatch stress → cross-border lenders pause new EM commitments → in-flight EM deals repriced or withdrawn → EM central banks hike rates to defend currencies → domestic financing cost compounds.
Timeline: 2-4 weeks from signal to lender pause. 6-8 weeks to deal-level impact.

**Why developed market infrastructure was unaffected:**
No currency mismatch. No capital outflow pressure. Domestic revenues and domestic debt service in same currency. Rate move of 140bps significant but not sufficient to break underwriting assumptions on deals with 6-12 month timelines. The E05 lesson: pure rate stress without currency mismatch is manageable for developed market infrastructure.

**Why the stress reversed immediately:**
Fed non-taper September 18 removed the trigger. Bond markets reversed within days. EM currencies stabilized. Cross-border lenders resumed. The stress was entirely expectation-driven — no fundamental economic damage had occurred in 16 weeks. When the expectation changed, the stress unwound. This distinguishes E05 from E04 where fundamental WACC damage to in-development projects was irreversible regardless of subsequent rate moves.

**2026 relevance:**
FOMC April 28 is a binary event. A surprise hold when market expects hike, or surprise hike when market expects hold, could trigger an E05-pattern in EM infrastructure markets. Duration will determine whether it resembles E05 (16-week reversal) or E04 (16-month damage). The distinguishing signal: does Fed communication resolve uncertainty (E05 pattern) or extend it (E04 pattern)?

---

## SECTION 5 — RESOLUTION SIGNALS
*What ended the stress. First indicators of normalization.*

**What ended the stress:**
- Fed non-taper decision September 18 2013 — immediate and complete reversal
- UST 10Y fell from 3.0% back toward 2.5% within 30 days
- EM currencies stabilized within two weeks of Fed decision
- Cross-border capital flows reversed — EM portfolio inflows resumed
- Actual taper December 2013 — orderly, already priced, no second shock

**First indicators of normalization (earliest appearance):**
1. UST 10Y falling — September 19 2013 (day after Fed non-taper)
2. EM currency stabilization — September 19-20 2013
3. EM infrastructure deal pipeline reactivating — October 2013
4. Japanese bank EM lending resuming — Q4 2013
5. Actual taper December 2013 — market non-event, already priced

**Recovery timeline by asset class:**
- Developed market infrastructure: no recovery needed — unaffected throughout
- EM contracted infrastructure: 8-12 weeks — resumed after Fed non-taper
- EM revenue-risk infrastructure: 12-16 weeks — currency stabilization required first
- Cross-border financing: Q4 2013 — Japanese and European lenders resumed

**What did not resolve quickly:**
- EM structural vulnerabilities — current account deficits remained; next stress event (2018 EM sell-off) hit same countries
- Currency hedge costs — remained elevated in EM for 6-12 months
- EM central bank rates — some held elevated rates into 2014 to maintain credibility

**Sri practitioner notes:**
The Taper Tantrum was the cleanest demonstration of how rate stress propagates differently in EM versus developed market infrastructure. The deals we were working on in developed markets in mid-2013 were largely unaffected — 140bps move over 16 weeks was uncomfortable but not deal-breaking at the timelines we were working with. The EM exposure was a different story entirely — currency depreciation of 14-16% simultaneously with capital outflow and local rate hikes created a triple stress that made cross-border financing economics unworkable in weeks. The lesson that carried forward: any EM infrastructure deal must be stress-tested for a simultaneous currency depreciation of 15-20% and a 150bps domestic rate increase, because that is what a Fed communication shift produces in EM markets within 30 days.

---
*GroundTruth Event Encyclopedia — E05 Taper Tantrum*
*PRD Schema v2.0 — Five-section standard*
*For internal use only*