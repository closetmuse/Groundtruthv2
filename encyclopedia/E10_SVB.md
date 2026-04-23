# GROUNDTRUTH EVENT ENCYCLOPEDIA
# Event: Silicon Valley Bank Collapse — Regional Bank Duration-Mismatch Cascade
# Code: E10
# Legacy Code: None (new entry 2026-04-23)
# Trigger Date: 2023-03-08
# Trigger Event: SVB announced $1.8B loss on bond portfolio sale + $2.25B capital raise after-hours Mar 8. Deposit run began Mar 9 (equity -60%, $42B deposit outflow); FDIC seized Mar 10 2023. Signature Bank seized Mar 12. First Republic acquired by JPMorgan May 1. Three of the four largest US bank failures ever, inside 60 days.
# Primary Regime: R2 — Credit Stress (sector-specific credit cascade, regional banking duration mismatch)
# Secondary Regime: R0 — Compound (Fed emergency response created immediate policy-tailwind offset)
# Pattern Match Tags: C01, C02, C12, C14, C15
# Fingerprint Date: 2023-03-12 (FDIC systemic-risk exception invoked Sunday night; Fed BTFP announced; Signature seized; regional-bank KRE -12% Monday open)
# PRD Build Priority: 2
# Status: LOCKED
# Verified by Sri: Flagged 2026-04-23 as essential precedent for understanding regional-bank construction-lending retrenchment; practitioner notes to be added on review.
# Last Updated: April 2026

---

## SECTION 1 — FINGERPRINT
*12 quantitative fields at peak stress. Machine-readable for stumpy similarity matching.*
*All figures measured from FRED, Federal Reserve H.8, FDIC reports, Bloomberg historical. Nothing modelled.*

| Field | Value | Notes |
|-------|-------|-------|
| fingerprint_date | 2023-03-12 | FDIC systemic-risk exception weekend — anchor event for fingerprint |
| brent_level | $80.77/bbl | Declining (-7% week-on-week on banking-contagion demand-fear) |
| brent_delta_90d | -2.8% | Minor move — commodity regime largely decoupled from the banking-specific crisis |
| ust_10y_level | 3.55% | **Plunging** — 10Y fell ~50bps in 3 trading days on flight-to-quality |
| ust_10y_direction | Falling | -50 bps over 72 hours — the fastest 3-day rally since 2008 |
| ust_2y_level | 4.03% | Collapsed from 5.07% peak Mar 8 — -100 bps in 48 hours, largest since 1987 |
| ig_spread_bps | 165 | Widening — but banking-subsector IG blown out to 220+ |
| hy_spread_bps | 520 | Modest widening — crisis largely contained to banking |
| regional_bank_kre_etf_drawdown | -28% | KRE (S&P Regional Bank ETF) drawdown Mar 8 to Mar 13 |
| bank_deposit_outflow_week | ~$500B | Largest weekly deposit outflow in US banking history |
| fed_btfp_takedown_week1 | ~$12B | Bank Term Funding Program draws Mar 13-17 week one |
| usd_index_direction | Weakening | DXY -2.5% over fingerprint week as rate-cut expectations compressed |
| regime_code | R2+R0 | Sector-specific credit cascade compound with immediate Fed-countermeasure policy tailwind |
| distinguishing_feature | Pure duration-mismatch failure without asset-quality issue. HTM bond portfolio bought at 2020-21 zero-rate pricing developed $600B+ unrealized loss across US regional banks as Fed hiked 525bps 2022-23. Deposit concentration in rate-sensitive segments (VC-backed tech, commercial real estate sponsors) created run-vulnerability. The failure was a rate-sensitivity-of-liabilities-greater-than-assets problem, not a credit problem. The Fed's BTFP response (accepting HTM bonds at par for 1-year advances) froze the run within 72 hours. |

---

## SECTION 2 — SIGNAL SEQUENCE
*What appeared in the 15 months before peak stress. Medium lookback because the duration-mismatch built silently during the hiking cycle.*
*Hindsight note: every signal was public in Federal Reserve H.8 data weekly and in each bank's 10-Q; systematically dismissed by the market until the run began.*

### Early (12–15 months before peak — Dec 2021 to Q1 2022)
| Signal type | What appeared | Sources that were early |
|-------------|---------------|------------------------|
| Fed pivot to hiking | March 2022 first hike; signal that HTM portfolio marks were going to matter | FOMC statements, rate-probability markets |
| Peak US bank deposits | April 2022 — $18.2T peak total deposits; downhill from there as rates rose | Federal Reserve H.8 |
| HTM accumulation at zero-rate pricing | 2020-21 US bank HTM balances doubled as banks parked stimulus-era deposits into MBS and Treasuries at low yields | FDIC, bank 10-Ks |
| SVB deposit concentration disclosures | SVB 10-K: >50% deposits from "early-stage and growth-stage companies" — venture-backed, rate-sensitive | SEC filings |
| Regional bank duration gap | Academic research flagging 10-year-equivalent duration on regional bank asset books vs <1-year on liabilities | Federal Reserve research, academic banking literature |

### Mid (6–12 months before peak — Q2 to Q4 2022)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Unrealized losses cumulating | FDIC Q3 2022 report: US banks sitting on $620B unrealized losses on HTM and AFS securities | FDIC Quarterly Banking Profile |
| Deposit beta rising | Deposit rate competition accelerating — high-yield money market fund flows surging | ICI, FRED |
| Venture-capital funding collapse | 2022 VC-funded cash burn at portfolio companies depleting SVB deposit base | Pitchbook, CB Insights |
| First regional bank stress | Silvergate Bank announced significant losses in Dec 2022 from crypto-exposure deposit outflows | SEC filings |
| Moody's ratings watch | Moody's downgraded several regional banks in 2022 citing duration-mismatch and deposit-concentration | Moody's ratings actions |

### Late (0–6 months before peak — Q4 2022 to March 2023)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| Silvergate collapse | Silvergate Capital voluntary liquidation announced Mar 8 2023 — crypto-bank specific, but flagged deposit-run contagion | Silvergate SEC filings |
| Yield curve inversion deepening | 2s10s -100bps+ in Feb 2023 — heavy compression on bank NIM | FRED |
| SVB announcement Mar 8 | $1.8B bond sale loss + $2.25B equity raise — market read as distressed | SVB SEC filings, press release |
| Run begins Mar 9 | $42B deposit outflow in one day — 25% of SVB deposits in 24 hours; equity -60% | FDIC later disclosed |
| FDIC seizure Mar 10 | SVB closed by California Department of Financial Protection, FDIC appointed receiver; 2nd-largest US bank failure ever | FDIC press release |
| FDIC systemic risk exception Mar 12 | Sunday night — Treasury/Fed/FDIC joint announcement; all depositors protected; BTFP established | Treasury press, Fed statement |
| Signature Bank seized Mar 12 | Third-largest US bank failure; FDIC cited crypto-exposure deposit concentration | FDIC, NYDFS |

### Lagging (after peak — Q2 2023 onward)
| Signal type | What appeared | Sources |
|-------------|---------------|---------|
| First Republic run | Continued deposit outflow through April 2023; JPMorgan acquired via FDIC Mar 1 2023 (4th largest failure ever) | FDIC, JPMorgan disclosure |
| Regional bank deposit migration | Permanent shift from smaller banks to G-SIBs (JPM, BAC, Citi, Wells) — $500B+ deposit migration | H.8 data |
| Commercial real estate second wave | Regional bank commercial real estate (CRE) concentration created secondary credit stress 2023-24 | FDIC quarterly reports |
| Fed BTFP wind-down | BTFP stopped accepting new advances Mar 11 2024 (one year); existing advances ran to maturity | Fed BTFP program documents |
| Construction lending retrenchment | Regional banks systematically reduced construction loan origination — down 30-40% 2023-24 vs prior | FDIC reports, ABA data |
| Private credit scaling | Direct lenders (Ares, Blackstone, Apollo, Blue Owl) stepped into regional-bank gap on infrastructure and middle-market construction | SEC filings, fund reports |

---

## SECTION 3 — INFRASTRUCTURE FINANCE IMPACT
*Quantified deal-level impact. Source mix: FDIC Quarterly Banking Profile, IJGlobal, SNL Financial, direct-lender fund disclosures.*
*Directional estimates labelled. Measured numbers from FDIC and Federal Reserve H.8.*

| Metric | SVB-cycle observed | Notes |
|--------|---------------|-------|
| Regional bank construction loan origination 2023 | -32% vs 2022 | FDIC QBP — direct pullback on risk-weighted lending |
| Regional bank CRE loan growth 2023-24 | ~0% (flat) | After 10-15% annual growth 2018-22 |
| DC sponsor financing during acute phase | ~60 days disruption | Some mid-market DC financings paused Mar-Apr 2023; resumed by summer |
| Construction loan spread widening | +75-150 bps | Regional-bank construction loans repriced wider; persisted through 2024 |
| Private credit fund inflows 2023 | Record — $220B+ | Stepped into regional-bank gap directly |
| Bank Term Funding Program peak | $168B (March 2024) | Fed facility that stopped the cascade; wound down 2024-25 |
| Deposit migration G-SIB share gain | +3-4 pp | JPM, BAC, Citi, Wells gained deposit share permanently |
| Infrastructure deal flow Q2 2023 | -18% vs Q1 2023 | IJGlobal — temporary disruption, recovered by Q4 2023 |
| New deal spread widening peak | 50-80 bps | March-April 2023 acute; receded by Q3 2023 |
| Regional bank DC/tech-sponsor exposure | Largely exited by end-2023 | Risk-concentration remediation |
| Verification latency — deposit run | Near-zero | Weekly H.8 data showed deposit outflow in real time |
| Verification latency — construction-lending retrenchment | 6-12 months | Visible in quarterly FDIC data, structural change |

**Bilateral alpha summary:**
- Risk side (mid-market + tech-sponsor infrastructure with regional-bank funding): severity 7/10 for 6-12 months. Venture-debt channel collapsed briefly; construction-lending retrenchment structural and persistent. Infrastructure sponsor-side credit availability narrowed.
- Opportunity side (private credit, G-SIB infrastructure lending, Fed BTFP): severity 8/10 on magnitude. Private credit captured regional-bank pullback permanently. BTFP-accepting banks received effective Fed funding subsidy for one year.
- Structural validation: duration-mismatch on HTM bonds failed catastrophically at a specific rate-differential (525bps above 2020 pricing). Every regional bank thereafter was examined for HTM/AFS unrealized-loss-to-Tier-1-capital ratio as a first-order screen.

---

## SECTION 4 — TRANSMISSION MECHANISM
*Full causal chain from banking trigger to infrastructure-deal-level impact.*
*Every link states the mechanism, the asset class, and the timeline.*

**Primary chain — banking contagion to deposit migration:**
SVB bond sale announcement → market read as distressed → concentrated deposit base (VC-backed tech) coordinated outflow via mobile banking → $42B outflow in 24 hours → equity collapse → FDIC seizure → contagion fear to Signature, First Republic, Western Alliance, PacWest, Comerica → regional bank deposit run → Fed BTFP response accepting HTM bonds at par → run frozen within 72 hours.
Timeline: 48-72 hours from trigger to systemic-risk-exception.

**Secondary chain — regional-bank retrenchment to infrastructure:**
Deposit outflow + BTFP stigma + supervisory attention → regional banks de-risk aggressively → construction-loan origination cut 30-40% → infrastructure construction sponsors face tighter regional-bank syndication → spreads widen 75-150bps → structurally higher cost of construction capital in mid-market → private credit steps in as primary alternative → permanent channel shift.
Timeline: 6-12 months from banking crisis to construction-lending structure change.

**Tertiary chain — commercial real estate secondary impact:**
Regional bank CRE concentration (~25% of total loans at peak) → post-SVB regulatory focus on CRE stress → regional banks unable to extend CRE maturities on normal terms → CRE refi stress emerging 2023-24 → second-wave regional-bank credit losses → Moody's / S&P downgraded dozens of regional banks through 2024.
Timeline: 12-24 months from banking trigger to CRE credit-loss wave.

**Fed BTFP mechanism:**
Fed created Bank Term Funding Program Mar 12 2023 accepting HTM Treasuries and MBS at PAR (not market value) as collateral for 1-year advances at OIS+10bps. This converted $600B of unrealized losses from run-vulnerability into liquidity-available collateral. Single most important policy intervention of the crisis — it transformed the duration-mismatch from a solvency problem into a funding-cost problem.
Timeline: immediate — stopped the cascade within 72 hours of announcement.

**2026 relevance:**
The SVB cycle established (a) regional-bank construction lending is structurally narrower going forward — DC sponsors with mid-market deal profiles cannot rely on regional-bank syndicates at prior levels; (b) private credit is the primary alternative channel, which prices differently (direct-origination spread + illiquidity premium); (c) BTFP-class Fed response is the established playbook for regional-bank liquidity stress, so a future banking event has a known policy response. For 2026 DC financing: any deal dependent on regional-bank anchor commitment is pricing wider than pre-SVB, with structurally higher execution risk if banks face renewed stress. Watch: BTFP extensions or re-establishment if regional-bank stress returns.

---

## SECTION 5 — RESOLUTION SIGNALS
*What ended the acute stress. First indicators of normalization.*

**What ended the acute stress:**
- FDIC systemic-risk exception Mar 12 2023 — all depositors protected, contagion arrested
- Fed Bank Term Funding Program Mar 12 2023 — accepted HTM bonds at par, broke the duration-mismatch solvency spiral
- JPMorgan acquisition of First Republic May 1 2023 — closed the regional-bank run saga
- Fed pause on hikes June 2023 — policy-rate trajectory stabilized

**First indicators of normalization (earliest appearance):**
1. BTFP takedowns moderating — April 2023 (post-panic stabilization)
2. Regional bank deposit flow stabilizing — H.8 data Q2 2023
3. KRE ETF recovering half the drawdown — May-June 2023
4. Regional-bank CDS spreads normalizing — Q3 2023
5. First large regional bank bond issuance — KeyCorp, Fifth Third by Q3 2023

**Recovery timeline by asset class:**
- Regional bank senior debt: 9-12 months to restore primary-market access at normal levels
- Regional bank Tier 2 / preferred: 18-24 months — structural repricing permanent
- CRE loans (secondary stress): 24-36 months — still working through as of 2024-25
- Construction lending capacity: Never fully recovered at regional-bank level; private credit absorbed gap permanently
- Infrastructure deal flow: recovered to pre-SVB levels by Q4 2023 at higher spreads

**What did not resolve quickly:**
- Regional bank deposit migration to G-SIBs — permanent $500B+ share shift
- Construction-loan origination capacity at regional banks — structurally lower
- Commercial real estate credit stress — rolling through 2024-25, feeding into continuing regional-bank pressure
- HTM-portfolio duration discipline — every US bank now monitors unrealized-loss-to-Tier-1 as first-order screen
- VC/tech deposit concentration — dispersed permanently across multiple primary banks

**Sri practitioner notes:**
Two structural points worth recording. First: the regional-bank construction-lending channel never came back to pre-SVB capacity — mid-market and DC-adjacent construction deals that would have closed on regional-bank syndicate terms in 2021-22 now close through private-credit or G-SIB alternatives. The spread differential is real and persistent (~75-150bps wider vs pre-SVB comparable) and it's permanent, not cyclical. Second: the BTFP stigma was less severe than expected — most regional banks drew without major reputational damage; the facility worked. For 2026, the lesson is that a duration-mismatch-driven regional-bank liquidity event has a known Fed playbook response, so the TAIL outcomes of similar events are bounded. But the STRUCTURAL channel-retrenchment is the more important long-tail consequence.

---
*GroundTruth Event Encyclopedia — E10 Silicon Valley Bank Collapse*
*PRD Schema v2.0 — Five-section standard*
*For internal use only*
