# GT_Reference.md — GroundTruth V2
# Signal Schema | Classification Tags | Macro Regimes | InfraOS Data
# Load when: classifying signals, interpreting regimes, anchoring to Moody's

---

## SIGNAL SCHEMA — GS CORE FIELDS

Identity: id, legacy_id, created_at, source_type, status, fetch_run_id
Content: headline, summary, raw_content, url, source_name, publication_date
Classification: c_tags, f_tags, t_tag, o_tag, second_order, classifier_model
Price Anchor: anchor_commodity, anchor_value, anchor_unit,
              anchor_delta_7d, anchor_delta_30d, anchor_delta_90d,
              anchor_source, anchor_fetched_at
Confidence: confidence, is_verified, verification_note,
            corroboration_count, related_signal_ids,
            superseded_by, linked_binary_events, binary_event_outcome

Signal types: FETCH | PRICE | ANECDOTAL
Signal status: DRAFT | ACTIVE | ARCHIVED | SUPERSEDED
Alert levels: RED (75-100) | AMBER (45-74) | GREEN (0-44)

---

## CLASSIFICATION TAGS

### C-TAGS (Signal Categories)
C01 = Macro / Rates
C02 = Regulatory — Federal
C03 = Regulatory — State/RTO
C04 = Policy — Legislative
C05 = Energy — Oil and Gas
C06 = Energy Transition — Solar
C07 = Energy Transition — Wind
C08 = Geopolitical
C09 = Construction Commodities
C10 = BESS / Storage
C11 = Digital Infrastructure
C12 = Financing Markets
C13 = FX / International
C14 = Sponsor / Developer Activity
C15 = Grid Infrastructure

### A-TAGS (Asset Classes)
A01 = Natural Gas Power       A10 = GPU Financing
A02 = Nuclear                 A11 = Fiber/Telecom
A03 = Coal                    A12 = LNG
A04 = Solar                   A13 = LNG Feedgas
A05 = BESS                    A14 = Gas Pipelines
A06 = Onshore Wind            A15 = Oil Pipelines
A07 = Offshore Wind           A16 = NGL/Processing
A08 = Hydro/Pumped Storage    A17 = Transmission and Grid
A09 = Data Centers            A18 = Regulated Utilities
A19 = Toll Roads/Transport P3  A24 = Hydrogen
A20 = Ports/Maritime           A25 = SMR/Advanced Nuclear
A21 = Airports                 A26 = CCUS
A22 = Water/Wastewater         A27 = Critical Minerals
A23 = Social Infrastructure

### F-TAGS (Source Confidence)
F1-F5   = Primary institutional (FT, WSJ, Bloomberg, Reuters, FERC official)
F6-F10  = Specialized trade press (IJGlobal, PFI, Recharge, PV Mag)
F11-F15 = Market data (EIA, gridstatus, metals-api, FRED)
F16-F20 = Secondary and aggregator sources
Full lookup: ge/weights.py

### T-TAGS (Time Horizon)
T1 = Days (0-14) — immediate action window
T2 = Weeks (2-12) — near-term monitoring
T3 = Months (3-12) — strategic horizon

### O-TAGS (Opportunity Type)
O1 = Construction Debt Mandate
O2 = Refinancing / Refi Opportunity
O3 = Back-Leverage / Loan-on-Loan
O4 = Advisory / M&A
O5 = Equity / Mezzanine

---

## MACRO REGIME DEFINITIONS

### R0 — Compound Stress
Multiple stress dimensions simultaneously active. All signals amplified.
Current state: Day 42 Hormuz crisis.
Encyclopedia anchors: E07 Hormuz (active), E08 Volcker (resolved).

### R1 — Stagflationary Stress
C08/C03 elevated + C09 elevated + C02 elevated + GDP deceleration.
Construction costs and supply chain break first.
Refinancing pressure follows 6-12 months later.
Verification latency: 6-12 months.

### R2 — Credit Stress
C02 elevated (spread widening) + C12 elevated + C14 elevated + bank deleveraging.
Financing markets break before assets.
Leading indicator: bank CDS spreads and BDC gate activation.
Verification latency: near-zero on financing, 12-24 months on assets.
Encyclopedia anchors: E01 GFC, E04 Fed Rate Hike, E05 Taper Tantrum.

### R3 — Commodity Shock
C08 elevated 30%+ + C09 elevated + C14 elevated + volume/revenue risk.
Contractual structure determines survival.
Stress test the offtaker balance sheet, not the contract language.
Verification latency: contracted assets 12-24 months, merchant 3-6 months.
Encyclopedia anchors: E02 COVID, E03 Ukraine, E06 Oil Collapse.

### R4 — Policy Tailwind
C04/C05 elevated + C06 accelerating + new asset class opening.
Alpha window 12-18 months from policy announcement.
Closes faster for simple assets, slower for complex assets.
Undercapitalized players compress spreads below technical risk threshold.

---

## INFRAOS EMPIRICAL FOUNDATION
Source: Moody's Infrastructure Default and Recovery Rates 1983-2023
8,583 transactions. 40 years.

Construction phase default rate: 0.94% per year (8.5x single-A corporate)
Operations phase default rate:   0.11% per year (crossover at Year 7)
Construction phase LGD: 27.5%
Operations phase LGD:   19.2%
LGD gap: 8.3 percentage points ($41.5M on $500M deal)
Workout premium over distressed sale: 29 percentage points
Recovery rate when loss occurs: 46.2%
62% of defaulted deals recover 100% principal

2020-21 vintage warning:
Current CDR: 0.3x baseline. Stress window: 2023-2027.
Mini-perm refinancing cliff: H2 2026.
Rate environment vs underwriting: +375bps.
Four simultaneous stress vectors — no precedent in dataset.

Sector 10-year CDR:
PPP/Social Infrastructure: 3.3% (lowest)
Infrastructure all: 3.4%
Power: 4.7%
Oil and Gas: 7.2% (highest)
North America: 6.07%
Latin America: 10.78%

---

## ENCYCLOPEDIA
Location: GroundTruth_v2/encyclopedia/
8 entries. PRD schema v2.0. Immutable except E07.

| Code | Event                          | Regime | Status  |
|------|--------------------------------|--------|---------|
| E01  | Global Financial Crisis 2008-09 | R2    | LOCKED  |
| E02  | COVID Demand Shock 2020         | R3    | LOCKED  |
| E03  | Ukraine/Energy Crisis 2022-23   | R3    | LOCKED  |
| E04  | Fed Rate Hike Cycle 2022-23     | R2    | LOCKED  |
| E05  | Taper Tantrum 2013              | R2    | LOCKED  |
| E06  | Oil Price Crash 2014-16         | R3    | LOCKED  |
| E07  | Hormuz/Iran Conflict 2026       | R0    | ACTIVE  |
| E08  | Volcker/Second Oil Shock 1979-82 | R0   | LOCKED  |

E07 is the only entry that updates.
Live Hormuz overlay lives in Current_Application.md — not in E07.

---

## RTO POWER MARKETS — LIVE APRIL 13 2026
10 DA hubs: ERCOT (3), CAISO (2), MISO (2), NYISO (2), ISO-NE (1)
CAISO SP15: $9.22/MWh avg, 10 neg hrs — structural solar oversupply
ERCOT HB_WEST: $10.27/MWh avg, 10 neg hrs — wind/solar oversupply
ISO-NE Hub: $41.65/MWh — highest US hub, LNG dependency premium
NYISO NYC: $35.59/MWh — capacity crunch visible
Auto PRICE signals: _generate_price_signals() fires every capture

### SECOND VERIFICATION LATENCY MEASUREMENT
Forming: April 13 2026
Event: Structural curtailment CAISO SP15 + ERCOT HB_WEST
10 negative DA price hours per zone on April 12 2026.
Mechanism: As-produced solar PPAs earn zero/negative during negative hours.
Revenue underperformance accumulates daily.
DSCR covenant breach notification: 12-18 months from onset.
Signal IDs: GS-207 (ERCOT), GS-209 (CAISO)
Log: "Log outcome for GS-207 — [DSCR event]" when breach received.

---

## ANALYTICAL BIAS TRAPS

### Recency Bias
Do not weight recent signals more heavily than base rates.
Always anchor to 40-year Moody's dataset, not trailing 12 months.

### Hindsight Bias
Backtest signals reconstructed with knowledge of outcomes — label clearly.
Alpha claims validated by real-time outcomes, not backtest reconstruction.

---
*GT_Reference.md | Load on demand | GroundTruth V2 April 2026*
