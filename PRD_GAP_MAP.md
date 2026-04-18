# GroundTruth V2 — PRD Gap Map
# Tracks what is built vs what is specified in the PRD
# Updated after each session

## SESSION 6 CHANGES — APRIL 13 2026

### NEWLY LIVE

Power Markets — DA Price Intelligence
  STATUS: LIVE
  10 RTO DA hubs tracked daily
  Full metadata: peak/off-peak/spread/neg hrs/signals
  Comparable across days (same 24-hour period)
  Stored as rich dicts in gs_price_snapshots

Power Markets — Auto PRICE Signal Generation
  STATUS: LIVE
  _generate_price_signals() wired into run_price_fetch()
  3 signal types auto-generated from DA thresholds
  First signals: GS-207/208/209 (April 13 2026)
  Curtailment dedup: 24-hour window

Prices Tab — Full Power Market Dashboard
  STATUS: LIVE
  13 columns (was 7)
  3 sections: Macro, Commodities, RTO Power
  RTO DA metadata fully surfaced in Sheets

Price Sources — Real-Time Fixes
  STATUS: LIVE
  WTI/Brent: EIA API (same day, was FRED T+3)
  FX/USD: Yahoo Finance (real-time, was FRED T+3)
  BBB/HY: FRED retained (weekly by design)

### VERIFICATION LATENCY — UPDATED STATUS

Measurement 1: COMPLETE
  LME Aluminum: 83 days
  January 15 2026 to April 8 2026

Measurement 2: FORMING
  Event: CAISO SP15 + ERCOT HB_WEST curtailment
  Signal IDs: GS-207, GS-209
  Signal date: April 13 2026
  Expected latency: 12-18 months
  Outcome trigger: solar PPA DSCR covenant breach

Total measurements: 1 complete, 1 forming
Target for defensible thesis: 5 complete

### ALPHA PLAYS STATUS — UPDATED

Alpha 1 PJM Capacity to DC Debt:
  PARTIAL — Utility Dive RSS covers auction results
  MISSING — pipeline DC deal geography not confirmed

Alpha 2 ERCOT Curtailment to Solar PPA:
  LIVE — GS-207 firing, 10 neg hrs April 12
  MISSING — TX solar deal geography not in Pipeline

Alpha 3 CAISO Duck Curve to BESS Origination:
  LIVE — GS-209 firing, spread tracked
  MISSING — CA solar/BESS deal geography missing

Alpha 4 Gas Price to CCGT Refinancing:
  PARTIAL — Henry Hub tracked, ERCOT North DA live
  MISSING — gas plant deal geography not confirmed

Alpha 5 Interconnection Queue to Origination:
  NOT BUILT — queue monitoring not started

Alpha 6 ISO-NE + LNG to Utility Stress:
  PARTIAL — ISO-NE hub live ($41.65/MWh)
  MISSING — NE utility deal geography missing

BINDING CONSTRAINT ON ALL SIX PLAYS:
  Geography in Pipeline tab.
  Zero TX/CA/PJM/ISO-NE deals have confirmed geography.
  Five minutes of Sri data entry unlocks all six plays.
  This is not a code problem — it is a data problem.