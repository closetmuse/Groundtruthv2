# GroundTruth V2 — Session 6 Summary
# Date: April 13 2026
# Duration: Single session
# Focus: Power markets intelligence layer

## WHAT WAS BUILT

### 1. RTO Day-Ahead Price Intelligence
File: gs/prices.py

Replaced real-time 5-minute RTO spot prices with prior-day day-ahead hourly
price statistics. DA prices are published once per day, represent the same
24-hour period, are what physical power is settled against, and are what
PPA revenue models reference. They are the correct market for infrastructure
finance intelligence.

10 RTO DA hubs now tracked:
  ERCOT: HB_NORTH, HB_WEST, HB_HOUSTON
  CAISO: NP15, SP15
  MISO: ILLINOIS HUB, INDIANA HUB
  NYISO: N.Y.C., CAPITL
  ISO-NE: INTERNAL HUB

Per hub per day: da_avg, da_peak_avg, da_offpeak_avg, peak_offpeak_spread,
da_high, da_low, negative_price_hours, bess_signal, curtailment_signal,
scarcity_signal. All stored as rich dicts in gs_price_snapshots.

### 2. Automatic PRICE Signal Generation
File: gs/prices.py — _generate_price_signals()

Runs inside run_price_fetch() on every capture. Three signal types:
  CURTAILMENT: negative_price_hours > 0 (AMBER 1-4hrs, RED >4hrs)
  BESS: peak_offpeak_spread > $50/MWh (GREEN $50-100, AMBER >$100)
  SCARCITY: da_high > $200/MWh (always RED, T1)

First run results (April 13 2026):
  GS-207 CURTAILMENT AMBER: ERCOT HB_WEST 10 neg hrs
  GS-208 CURTAILMENT AMBER: CAISO NP15 2 neg hrs
  GS-209 CURTAILMENT AMBER: CAISO SP15 10 neg hrs

### 3. Prices Tab — Full Power Market Dashboard
File: sheets/interface.py — _read_prices()

13 columns: Series, Date, Value, Market, Peak Avg, Off-Peak Avg, Spread,
Neg Hrs, BESS Signal, Curtailment, Delta 7d, Delta 30d, Threshold.

Three sections: MACRO & CREDIT, COMMODITIES, RTO POWER MARKETS (Day-Ahead).
Total 33 rows. RTO DA rows show full metadata.

### 4. Price Source Improvements
WTI/Brent: FRED (T+3) → EIA API (same-day)
FX/USD Index: FRED (T+3) → Yahoo Finance (real-time)
BBB/HY: kept on FRED (weekly by design)
All series now store publication_date and staleness_days.

## SECOND LATENCY MEASUREMENT OPPORTUNITY

First measurement: LME aluminum 83 days (Jan 15 → Apr 8 2026)

Second measurement forming: CAISO/ERCOT curtailment
  Signal date: April 13 2026 (GS-207, GS-209)
  Expected latency: 12-18 months to solar PPA DSCR covenant breach

## DB STATE AT SESSION END
  Signals: 134 ACTIVE, 5 ARCHIVED, 74 FILTERED (213 total)
  Alert breakdown: RED 7, AMBER 105, GREEN 22
  Signal types: FETCH 209, PRICE 3, ANECDOTAL 1
  Price snapshots: 43 (32 series, 10 RTO DA)
  Fetch runs: 7 COMPLETE, 27 PARTIAL
  Binary events: 3 OPEN, 1 RESOLVED

## FILES CHANGED THIS SESSION
  gs/prices.py         — DA price fetch, signal gen, EIA/Yahoo sources
  sheets/interface.py  — _read_prices() rebuild, 13 cols, 3 sections