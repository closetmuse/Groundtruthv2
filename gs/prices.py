# GS — GroundSignals Price Fetch
# PRD Section 3.3 — Price Store Schema
# PRD Section 3.4 — Price Threshold Definitions
# Phase 1 coverage: 30 of 38 PRD series via FRED + gridstatus
# Metals (8 series): deferred to Phase 2
# Last Updated: April 2026

import os
import json
import sqlite3
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from fredapi import Fred
import gridstatus
import pandas as pd

load_dotenv(r"C:\Users\nagar_7kszmu8\GroundTruth_v2\.env", override=True)

FRED_KEY = os.getenv("FRED_API_KEY")
DB_PATH  = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\groundtruth.db"

# ── FRED SERIES MAP ───────────────────────────────────────────────────────────
# PRD Section 3.3 — all daily series available via FRED
# Format: { field_name: (fred_series_id, unit, category) }

FRED_SERIES = {
    # Rates — FRED is authoritative source
    "ust_2y_pct":           ("DGS2",              "%",       "rates"),
    "ust_5y_pct":           ("DGS5",              "%",       "rates"),
    "ust_10y_pct":          ("DGS10",             "%",       "rates"),
    "ust_30y_pct":          ("DGS30",             "%",       "rates"),
    "sofr_pct":             ("SOFR",              "%",       "rates"),

    # Credit Spreads — FRED weekly, keep as-is
    "bbb_oas_bps":          ("BAMLC0A4CBBB",      "%",       "spreads"),
    "hy_spread_bps":        ("BAMLH0A0HYM2",      "%",       "spreads"),
}

# ── YAHOO OIL PRICES (replaces EIA RWTC/RBRTE — real-time front-month) ───────
# EIA petroleum spot series have observation frequency = daily but release
# cadence = weekly Wednesday, lagging up to 8 days. NYMEX/ICE front-month
# futures publish T+0. Same Yahoo pattern as ALI=F / HG=F.
YAHOO_OIL = {
    "wti_usd_bbl":   {"symbol": "CL=F", "unit": "$/bbl", "category": "oil"},
    "brent_usd_bbl": {"symbol": "BZ=F", "unit": "$/bbl", "category": "oil"},
}

# ── YAHOO GAS (replaces FRED DHHNGSP — real-time NYMEX Henry Hub front-month) ─
# FRED DHHNGSP pulls EIA weekly natural gas spot, which lags 3-5 business days
# on most weeks (empirically observed 4-day lag on 2026-04-18). NYMEX NG=F
# front-month settles T+0. Same Yahoo pattern as CL=F / BZ=F for oil.
YAHOO_GAS = {
    "henry_hub_usd_mmbtu": {"symbol": "NG=F", "unit": "$/MMBtu", "category": "gas"},
}

# ── YAHOO LNG BENCHMARKS (JKM and Dutch TTF front-month futures) ─────────────
# JKM (Platts Japan-Korea Marker): front-month, USD/MMBtu. Direct compare to HH.
# TTF (ICE Dutch Title Transfer Facility): front-month, EUR/MWh. Converted to
# USD/MMBtu using usd_eur rate from YAHOO_FX_SERIES. Conversion factor:
# 1 MWh natural gas = 3.41214 MMBtu, so EUR/MWh ÷ 3.41214 = EUR/MMBtu,
# then × (USD/EUR rate) = USD/MMBtu.
# Both series feed the LNG arbitrage axis (HH + $1.50-2.50 shipping breakeven).
YAHOO_LNG = {
    "jkm_usd_mmbtu": {
        "symbol":   "JKM=F",
        "unit":     "$/MMBtu",
        "category": "gas",
        "raw_unit": "$/MMBtu",
        "needs_conversion": False,
    },
    "ttf_eur_mwh": {
        "symbol":   "TTF=F",
        "unit":     "EUR/MWh",
        "category": "gas",
        "raw_unit": "EUR/MWh",
        "needs_conversion": False,
    },
    # ttf_usd_mmbtu is derived from ttf_eur_mwh × FX ÷ 3.41214 inside
    # fetch_yahoo_lng() after raw TTF and FX are both fetched. Declared
    # here so the conversion loop knows to produce it.
    "ttf_usd_mmbtu": {
        "symbol":   "TTF=F",
        "unit":     "$/MMBtu",
        "category": "gas",
        "raw_unit": "EUR/MWh",
        "needs_conversion": True,
        "source_field": "ttf_eur_mwh",
    },
}

# Natural gas energy equivalence: 1 MWh = 3.41214 MMBtu (HHV basis)
MWH_TO_MMBTU = 3.41214


# ── STALENESS HELPERS (business-day cadence for daily-settle futures) ────────
# JKM and TTF settle once per business day after their respective sessions
# close. Calendar-day staleness misreads a Monday-AM capture as "3 days stale"
# when Friday's close is actually the latest settlement that exists in the
# world. Business-day logic gives the right answer: on Mon AM, Fri close = 1
# business day behind = within-cadence; on Tue AM, Fri close = 2 business
# days = truly stale (Monday settlement missed).

def _business_days_between(start_date, end_date):
    """Count weekdays strictly after start_date, up to and including end_date.

    No holiday calendar — weekends only. Good enough for staleness flagging;
    holidays just appear as a 1-day late settlement which is harmless noise.
    """
    if end_date <= start_date:
        return 0
    days = 0
    d = start_date
    while d < end_date:
        d += timedelta(days=1)
        if d.weekday() < 5:   # Mon-Fri
            days += 1
    return days


def _next_business_day(d):
    """Return the next weekday strictly after d."""
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt


# ── YAHOO FINANCE FX (replaces FRED for real-time FX) ─────────────────────────
YAHOO_FX_SERIES = {
    "usd_index": {"symbol": "DX-Y.NYB", "unit": "index", "category": "fx",
                  "convert": lambda x: x},
    "usd_eur":   {"symbol": "EURUSD=X", "unit": "rate",  "category": "fx",
                  "convert": lambda x: x},
    "usd_jpy":   {"symbol": "JPY=X",    "unit": "rate",  "category": "fx",
                  "convert": lambda x: x},
    "usd_gbp":   {"symbol": "GBPUSD=X", "unit": "rate",  "category": "fx",
                  "convert": lambda x: x},
}

# ── THRESHOLD DEFINITIONS ─────────────────────────────────────────────────────
# PRD Section 3.4 — threshold breach generates DRAFT signal
# Format: { field_name: { "7d": value, "30d": value, "type": "pct"|"abs" } }

THRESHOLDS = {
    "wti_usd_bbl":         {"7d": 8.0,  "30d": 15.0, "type": "pct"},
    "brent_usd_bbl":       {"7d": 8.0,  "30d": 15.0, "type": "pct"},
    "henry_hub_usd_mmbtu": {"7d": 10.0, "30d": 20.0, "type": "pct"},
    "ust_10y_pct":         {"7d": 0.40, "30d": 0.75, "type": "abs"},
    "bbb_oas_bps":         {"7d": 30.0, "30d": 60.0, "type": "abs"},
    "hy_spread_bps":       {"7d": 50.0, "30d": 100.0,"type": "abs"},
    # Power price thresholds — scarcity pricing signals
    "ercot_hb_north_da":         {"7d": None, "30d": None, "type": "abs_floor",
                                  "floor": 200.0},
    "ercot_hb_houston_da":       {"7d": None, "30d": None, "type": "abs_floor",
                                  "floor": 200.0},
    "nyiso_nyc_da":              {"7d": None, "30d": None, "type": "abs_floor",
                                  "floor": 200.0},
    "caiso_th_sp15_gen-apnd_da": {"7d": None, "30d": None, "type": "abs_floor",
                                  "floor": 200.0},
    "aluminum_usd_mt":     {"7d": 8.0,  "30d": 15.0, "type": "pct"},
    "copper_usd_mt":       {"7d": 8.0,  "30d": 15.0, "type": "pct"},
    # Steel HRC: breach detector runs off CME futures (daily); FRED PPI kept
    # for the slow structural overlay but excluded from breach to avoid
    # stale-monthly-data false positives. Added 2026-04-17.
    "steel_hrc_usd_st":    {"7d": 5.0,  "30d": 10.0, "type": "pct"},
    # LNG destination benchmarks — same 10/20 % bands as HH
    "jkm_usd_mmbtu":       {"7d": 10.0, "30d": 20.0, "type": "pct"},
    "ttf_eur_mwh":         {"7d": 10.0, "30d": 20.0, "type": "pct"},
    "ttf_usd_mmbtu":       {"7d": 10.0, "30d": 20.0, "type": "pct"},
    # GPU compute spot (Vast.ai p50). Tight bands — GPU markets move
    # materially on supply events; SemiAnalysis 1yr index moved 40% in
    # six months (Oct-25 to Mar-26), spot will be choppier.
    "gpu_h100_sxm_usd_hr": {"7d": 10.0, "30d": 20.0, "type": "pct"},
    "gpu_h200_usd_hr":     {"7d": 10.0, "30d": 20.0, "type": "pct"},
    "gpu_b200_usd_hr":     {"7d": 15.0, "30d": 25.0, "type": "pct"},
    "gpu_a100_sxm_usd_hr": {"7d": 10.0, "30d": 20.0, "type": "pct"},
}

# ── DATABASE SETUP ────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gs_price_snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            fetched_at  TEXT NOT NULL,
            series_data TEXT NOT NULL,
            deltas_7d   TEXT,
            deltas_30d  TEXT,
            deltas_90d  TEXT,
            breaches    TEXT,
            partial     INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    print("DB initialised — gs_price_snapshots table ready")

# ── FRED FETCH ────────────────────────────────────────────────────────────────

def fetch_fred_series():
    if not FRED_KEY:
        print("  WARN: FRED_API_KEY not set — skipping FRED fetch")
        return {}

    fred = Fred(api_key=FRED_KEY)
    results = {}

    for field, (series_id, unit, category) in FRED_SERIES.items():
        try:
            s = fred.get_series(series_id).dropna()
            if s.empty:
                raise ValueError("Empty series")
            value = round(float(s.iloc[-1]), 4)
            series_date = str(s.index[-1].date())
            results[field] = {
                "value":       value,
                "unit":        unit,
                "category":    category,
                "series_id":   series_id,
                "series_date": series_date,
                "history":     [round(float(v), 4)
                                for v in s.iloc[-95:].tolist()],
            }
            print(f"  OK  {field}: {value} {unit} ({series_date})")
        except Exception as e:
            print(f"  FAIL {field} ({series_id}): {e}")
            results[field] = None

    return results

# ── YAHOO FRONT-MONTH FUTURES FETCH (oil, gas) ────────────────────────────────

def _fetch_yahoo_futures(symbol_dict):
    """Fetch front-month daily closes for any Yahoo symbol dict.

    Used for oil (CL=F, BZ=F — replaces EIA RWTC/RBRTE which lag up to 8 days)
    and gas (NG=F — replaces FRED DHHNGSP which lags 3-5 business days). Sets
    stale=True if last close > 2 days old (weekend/holiday/outage), which
    suppresses threshold breach alerts and surfaces a STALE marker in the
    email price section.
    """
    import requests as _req
    results = {}

    for field, info in symbol_dict.items():
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
                   f"{info['symbol']}?interval=1d&range=120d")
            r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}")

            chart = r.json()["chart"]["result"][0]
            timestamps = chart.get("timestamp") or []
            closes = chart["indicators"]["quote"][0]["close"]
            pairs = [(t, c) for t, c in zip(timestamps, closes) if c is not None]
            if not pairs:
                raise ValueError("No price data")

            last_ts, last_close = pairs[-1]
            value = round(float(last_close), 2)
            last_date = datetime.utcfromtimestamp(last_ts).date()
            pub_date = str(last_date)
            stale_days = (date.today() - last_date).days
            stale_flag = stale_days > 2

            history = [round(float(c), 4) for _, c in pairs[-95:]]

            results[field] = {
                "value":            value,
                "unit":             info["unit"],
                "category":         info["category"],
                "series_id":        info["symbol"],
                "series_date":      pub_date,
                "source":           "Yahoo Finance",
                "publication_date": pub_date,
                "staleness_days":   stale_days,
                "stale":            stale_flag,
                "history":          history,
            }
            stale_marker = f" STALE({stale_days}d)" if stale_flag else ""
            print(f"  OK  {field}: {value} {info['unit']} ({pub_date}){stale_marker}")
        except Exception as e:
            print(f"  FAIL {field} ({info['symbol']}): {e}")
            results[field] = None
    return results


def fetch_yahoo_oil():
    return _fetch_yahoo_futures(YAHOO_OIL)


def fetch_yahoo_gas():
    return _fetch_yahoo_futures(YAHOO_GAS)


# ── YAHOO FINANCE FX (real-time USD Index and FX rates) ───────────────────────

def fetch_yahoo_fx():
    """Fetch real-time FX rates from Yahoo Finance."""
    import requests as _req
    results = {}

    for field, info in YAHOO_FX_SERIES.items():
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
                   f"{info['symbol']}?interval=1d&range=95d")
            r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}")

            chart = r.json()["chart"]["result"][0]
            closes = chart["indicators"]["quote"][0]["close"]
            closes = [c for c in closes if c is not None]
            if not closes:
                raise ValueError("No price data")

            value = round(info["convert"](closes[-1]), 4)
            history = [round(info["convert"](c), 4) for c in closes]

            results[field] = {
                "value":            value,
                "unit":             info["unit"],
                "category":         info["category"],
                "series_id":        info["symbol"],
                "series_date":      str(date.today()),
                "source":           "Yahoo Finance",
                "publication_date": str(date.today()),
                "staleness_days":   0,
                "history":          history[-95:],
            }
            print(f"  OK  {field}: {value} {info['unit']} (real-time)")
        except Exception as e:
            print(f"  FAIL {field} ({info['symbol']}): {e}")
            results[field] = None
    return results


# ── YAHOO LNG BENCHMARKS (JKM and TTF front-month futures) ────────────────────

def fetch_yahoo_lng(fx_data):
    """Fetch JKM and Dutch TTF front-month futures from Yahoo Finance.

    JKM (JKM=F) returns USD/MMBtu directly — stored as jkm_usd_mmbtu.
    TTF (TTF=F) returns EUR/MWh — stored raw as ttf_eur_mwh AND converted
    to USD/MMBtu as ttf_usd_mmbtu using the fx_data['usd_eur'] rate and
    the 3.41214 MWh→MMBtu conversion factor.

    Both feed the LNG arbitrage axis in Sri's sector risk framework —
    breakeven for US Gulf Coast export is HH + $1.50–2.50/MMBtu shipping,
    so JKM minus (HH + shipping) and TTF minus (HH + shipping) are the
    two numbers reported. History arrays are preserved for delta math.

    Args:
        fx_data: dict from fetch_yahoo_fx(), used for EUR→USD conversion.
                 Must be called AFTER fetch_yahoo_fx() in run_price_fetch().

    Returns:
        dict of three fields: jkm_usd_mmbtu, ttf_eur_mwh, ttf_usd_mmbtu.
        Any field that fails is set to None (graceful degradation).
    """
    import requests as _req
    results = {}

    # Raw fetches first — JKM=F and TTF=F
    for field, info in YAHOO_LNG.items():
        if info.get("needs_conversion"):
            continue  # handled in the conversion pass below
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
                   f"{info['symbol']}?interval=1d&range=120d")
            r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}")

            chart = r.json()["chart"]["result"][0]
            timestamps = chart.get("timestamp") or []
            closes = chart["indicators"]["quote"][0]["close"]
            pairs = [(t, c) for t, c in zip(timestamps, closes) if c is not None]
            if not pairs:
                raise ValueError("No price data")

            last_ts, last_close = pairs[-1]
            value = round(float(last_close), 3)
            last_date = datetime.utcfromtimestamp(last_ts).date()
            pub_date = str(last_date)
            today = date.today()
            cal_days_stale = (today - last_date).days
            biz_days_stale = _business_days_between(last_date, today)
            next_expected = _next_business_day(last_date)
            # Business-day semantics: > 1 means we missed a settlement that
            # should already exist. == 1 means the next settlement publishes
            # later today US time — within-cadence at AM capture, truly stale
            # by next-day AM capture.
            stale_flag = biz_days_stale > 1

            history = [round(float(c), 4) for _, c in pairs[-95:]]

            results[field] = {
                "value":                     value,
                "unit":                      info["unit"],
                "category":                  info["category"],
                "series_id":                 info["symbol"],
                "series_date":               pub_date,
                "source":                    "Yahoo Finance",
                "publication_date":          pub_date,
                "settlement_cadence":        "daily_business",
                "business_days_stale":       biz_days_stale,
                "next_expected_settlement":  str(next_expected),
                "staleness_days":            cal_days_stale,   # backward compat
                "stale":                     stale_flag,
                "history":                   history,
            }
            if stale_flag:
                marker = (f" STALE({biz_days_stale}bd — expected "
                          f"{next_expected} settlement missing)")
            elif biz_days_stale == 1:
                marker = f" (next settle {next_expected} pub later today)"
            else:
                marker = ""
            print(f"  OK  {field}: {value} {info['unit']} "
                  f"(settled {pub_date}){marker}")
        except Exception as e:
            print(f"  FAIL {field} ({info['symbol']}): {e}")
            results[field] = None

    # Conversion pass — TTF EUR/MWh → USD/MMBtu using live FX
    for field, info in YAHOO_LNG.items():
        if not info.get("needs_conversion"):
            continue
        source_field = info["source_field"]
        source = results.get(source_field)
        fx = fx_data.get("usd_eur") if fx_data else None

        if not source or not fx or fx.get("value") is None:
            print(f"  SKIP {field}: source={source_field} fx=usd_eur missing")
            results[field] = None
            continue

        try:
            fx_rate = float(fx["value"])  # EUR→USD multiplier (~1.07)
            # EUR/MWh × (USD/EUR) ÷ (MMBtu/MWh) = USD/MMBtu
            value = round(source["value"] * fx_rate / MWH_TO_MMBTU, 3)
            history = [
                round(c * fx_rate / MWH_TO_MMBTU, 4)
                for c in source.get("history", [])
            ]
            results[field] = {
                "value":                     value,
                "unit":                      info["unit"],
                "category":                  info["category"],
                "series_id":                 f"{source['series_id']}+usd_eur",
                "series_date":               source["series_date"],
                "source":                    "Yahoo Finance (derived)",
                "publication_date":          source["publication_date"],
                "settlement_cadence":        source.get("settlement_cadence"),
                "business_days_stale":       source.get("business_days_stale"),
                "next_expected_settlement":  source.get("next_expected_settlement"),
                "staleness_days":            source["staleness_days"],
                "stale":                     source["stale"],
                "history":                   history,
                "derivation":                (
                    f"{source_field}={source['value']} {source['unit']} × "
                    f"usd_eur={fx_rate} ÷ {MWH_TO_MMBTU} MMBtu/MWh"
                ),
            }
            print(f"  OK  {field}: {value} {info['unit']} (derived from "
                  f"{source['value']} EUR/MWh × {fx_rate} ÷ {MWH_TO_MMBTU})")
        except Exception as e:
            print(f"  FAIL {field} conversion: {e}")
            results[field] = None

    return results


# ── RTO DAY-AHEAD HOURLY FETCH ────────────────────────────────────────────────
# Prior day DA statistics — the correct market for infrastructure finance.
# DA is where physical power settles, what PPAs reference, what BESS benchmarks.

RTO_DA_CONFIGS = [
    {"iso": "Ercot",  "locs": ["HB_NORTH", "HB_WEST", "HB_HOUSTON"],
     "method": "get_spp", "price_col": "SPP"},
    {"iso": "MISO",   "locs": ["ILLINOIS.HUB", "INDIANA.HUB"],
     "method": "get_lmp", "price_col": "LMP"},
    {"iso": "NYISO",  "locs": ["N.Y.C.", "CAPITL"],
     "method": "get_lmp", "price_col": "LMP"},
    {"iso": "CAISO",  "locs": ["TH_NP15_GEN-APND", "TH_SP15_GEN-APND"],
     "method": "get_lmp", "price_col": "LMP"},
    {"iso": "ISONE",  "locs": [".H.INTERNAL_HUB"],
     "method": "get_lmp", "price_col": "LMP"},
]


def fetch_rto_prices():
    """
    Fetch prior day day-ahead hourly LMP/SPP statistics.
    Computes: avg, peak avg (7-22), off-peak avg (23-6),
    spread, high, low, negative price hours.
    """
    import pytz as _pz
    ET = _pz.timezone("America/New_York")
    yesterday = (datetime.now(ET) - timedelta(days=1)).strftime("%Y-%m-%d")

    results = {}

    for cfg in RTO_DA_CONFIGS:
        try:
            iso = getattr(gridstatus, cfg["iso"])()
            method = getattr(iso, cfg["method"])
            df = method(date=yesterday, market="DAY_AHEAD_HOURLY")

            if df is None or df.empty:
                print(f"  WARN: {cfg['iso']} DA empty")
                continue

            pcol = cfg["price_col"]
            if pcol not in df.columns:
                print(f"  WARN: {cfg['iso']} — no {pcol} column. Cols: {list(df.columns)[:5]}")
                continue

            for loc in cfg["locs"]:
                loc_df = df[df["Location"] == loc]
                if loc_df.empty:
                    continue

                prices = loc_df[pcol].dropna().astype(float)
                if prices.empty:
                    continue

                # Extract hours for peak/off-peak
                if "Interval Start" in loc_df.columns:
                    hours = pd.to_datetime(loc_df["Interval Start"]).dt.hour
                    peak = prices[hours.between(7, 22)]
                    offpeak = prices[~hours.between(7, 22)]
                else:
                    peak = prices
                    offpeak = pd.Series(dtype=float)

                da_avg = round(prices.mean(), 2)
                da_peak = round(peak.mean(), 2) if not peak.empty else da_avg
                da_offpeak = round(offpeak.mean(), 2) if not offpeak.empty else da_avg
                da_high = round(prices.max(), 2)
                da_low = round(prices.min(), 2)
                spread = round(da_peak - da_offpeak, 2)
                neg_hrs = int((prices < 0).sum())

                # Signals
                bess = ("HOT" if spread > 100 else "WARM" if spread > 50
                        else "WATCH" if spread > 25 else "NORMAL")
                curtail = "RED" if neg_hrs > 4 else ("AMBER" if neg_hrs > 0 else "CLEAR")
                scarcity = "RED" if da_high > 200 else ("AMBER" if da_high > 100 else "CLEAR")

                loc_key = loc.lower().replace(" ", "_").replace(".", "").replace("/", "_")
                key = f"{cfg['iso'].lower()}_{loc_key}_da"

                results[key] = {
                    "value": da_avg, "unit": "$/MWh", "category": "power",
                    "source": cfg["iso"], "market": "DAY_AHEAD",
                    "series_id": f"{cfg['iso']}_DA_{loc}",
                    "series_date": yesterday,
                    "publication_date": yesterday, "staleness_days": 1,
                    "da_peak_avg": da_peak, "da_offpeak_avg": da_offpeak,
                    "da_high": da_high, "da_low": da_low,
                    "peak_offpeak_spread": spread,
                    "negative_price_hours": neg_hrs,
                    "bess_signal": bess, "curtailment_signal": curtail,
                    "scarcity_signal": scarcity,
                    "history": [],
                }
                print(f"  {cfg['iso']} {loc}: avg=${da_avg} peak=${da_peak} "
                      f"off=${da_offpeak} spread=${spread} neg={neg_hrs} BESS={bess}")

        except Exception as e:
            print(f"  WARN: {cfg['iso']} DA failed: {e}")

    return results

# ── HISTORICAL LOOKUP FROM DB ─────────────────────────────────────────────────

def _lookup_historical_price(field: str, days_ago: int, window: int = 2):
    """
    Look up a historical price for a field from gs_price_snapshots in SQLite.

    Used as fallback for series without inline history (power prices from
    gridstatus). Searches for the closest snapshot within a +/-window day
    range of the target date.

    Args:
        field: Series field name (e.g. "ercot_hub_north_mwh").
        days_ago: How many days back to look.
        window: Acceptable +/- day window around target date.

    Returns:
        Float value if found, None if no historical reading exists.
    """
    from datetime import timedelta
    target = date.today() - timedelta(days=days_ago)
    earliest = str(target - timedelta(days=window))
    latest = str(target + timedelta(days=window))

    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT series_data FROM gs_price_snapshots "
            "WHERE snapshot_date BETWEEN ? AND ? "
            "ORDER BY ABS(julianday(snapshot_date) - julianday(?)) ASC "
            "LIMIT 1",
            (earliest, latest, str(target)),
        ).fetchall()
        conn.close()

        if rows:
            snap = json.loads(rows[0][0])
            entry = snap.get(field)
            if entry and entry.get("value") is not None:
                return float(entry["value"])
    except Exception:
        pass

    return None


# ── DELTA CALCULATION ─────────────────────────────────────────────────────────

def calculate_deltas(series_data):
    """
    Calculate 7d, 30d, and 90d deltas for all series.

    For series with inline history (FRED): compute from the history array.
    For series without history (gridstatus power): fall back to historical
    lookups from gs_price_snapshots in SQLite. Returns None for any delta
    where no historical reading is available — never fabricates.
    """
    deltas_7d  = {}
    deltas_30d = {}
    deltas_90d = {}

    for field, data in series_data.items():
        if data is None:
            deltas_7d[field]  = None
            deltas_30d[field] = None
            deltas_90d[field] = None
            continue

        history = data.get("history", [])
        current = data.get("value")
        if current is None:
            deltas_7d[field]  = None
            deltas_30d[field] = None
            deltas_90d[field] = None
            continue

        cat = data.get("category", "")

        if history:
            # Has inline history — compute from array
            def pct_change(periods):
                if len(history) > periods and history[-(periods+1)] != 0:
                    prior = history[-(periods+1)]
                    return round(((current - prior) / abs(prior)) * 100, 2)
                return None

            def abs_change(periods):
                if len(history) > periods:
                    return round(current - history[-(periods+1)], 4)
                return None

            if cat in ("rates", "spreads"):
                deltas_7d[field]  = abs_change(7)
                deltas_30d[field] = abs_change(30)
                deltas_90d[field] = abs_change(90)
            else:
                deltas_7d[field]  = pct_change(7)
                deltas_30d[field] = pct_change(30)
                deltas_90d[field] = pct_change(90)
        else:
            # No inline history — fall back to DB snapshot lookup
            for days, target_dict in [(7, deltas_7d), (30, deltas_30d),
                                       (90, deltas_90d)]:
                prior = _lookup_historical_price(field, days)
                if prior is not None and prior != 0:
                    if cat in ("rates", "spreads"):
                        target_dict[field] = round(current - prior, 4)
                    else:
                        target_dict[field] = round(
                            ((current - prior) / abs(prior)) * 100, 2
                        )
                else:
                    target_dict[field] = None

    return deltas_7d, deltas_30d, deltas_90d

# ── THRESHOLD CHECK ───────────────────────────────────────────────────────────

# Series whose series_date is older than this many days is considered stale.
# Breaches still surface but are flagged so the reader knows the move is
# against an out-of-date anchor (e.g. monthly PPI, weekly EIA, vendor outage).
STALE_DAYS_THRESHOLD = 2


def annotate_staleness(series_data, today=None):
    """
    Mutate each series record in `series_data` to add `staleness_days`
    (int days between today and the series_date). Idempotent. Series with
    no parseable `series_date` get `staleness_days = None`.

    Called once before delta/threshold/write so downstream consumers
    (breach detector, email Section 3) read a consistent annotation.
    """
    if today is None:
        today = date.today()
    for field, data in series_data.items():
        if not data:
            continue
        sd = data.get("series_date")
        if not sd:
            data["staleness_days"] = None
            continue
        try:
            sd_date = datetime.strptime(str(sd)[:10], "%Y-%m-%d").date()
            data["staleness_days"] = (today - sd_date).days
        except (ValueError, TypeError):
            data["staleness_days"] = None


def check_thresholds(series_data, deltas_7d, deltas_30d):
    """
    Emit breach records for any series whose 7d/30d delta exceeds its
    configured threshold. Breaches against stale anchors are LABELLED
    (not suppressed) — `stale=True` and `staleness_days=N` are added to
    the breach record so downstream consumers can decide how to surface
    them. Suppression hides data-source issues; labelling lets the
    reader see the move and act on the metadata.
    """
    breaches = []

    for field, rules in THRESHOLDS.items():
        data = series_data.get(field)
        if data is None:
            continue

        staleness_days = data.get("staleness_days")
        is_stale = bool(data.get("stale")) or (
            staleness_days is not None and staleness_days > STALE_DAYS_THRESHOLD
        )

        current = data["value"]
        d7  = deltas_7d.get(field)
        d30 = deltas_30d.get(field)

        def _emit(window, delta, threshold, type_):
            breaches.append({
                "field":          field,
                "window":         window,
                "value":          current,
                "delta":          delta,
                "threshold":      threshold,
                "type":           type_,
                "stale":          is_stale,
                "staleness_days": staleness_days,
            })

        if rules["type"] == "pct":
            if d7  is not None and abs(d7)  >= rules["7d"]:
                _emit("7d",  d7,  rules["7d"],  "pct")
            if d30 is not None and abs(d30) >= rules["30d"]:
                _emit("30d", d30, rules["30d"], "pct")

        elif rules["type"] == "abs":
            if d7  is not None and abs(d7)  >= rules["7d"]:
                _emit("7d",  d7,  rules["7d"],  "abs")
            if d30 is not None and abs(d30) >= rules["30d"]:
                _emit("30d", d30, rules["30d"], "abs")

        elif rules["type"] == "abs_floor":
            floor = rules.get("floor", 0)
            if current >= floor:
                _emit("current", None, floor, "abs_floor")

    return breaches

# ── SNAPSHOT WRITE ────────────────────────────────────────────────────────────

def write_snapshot(series_data, deltas_7d, deltas_30d, deltas_90d, breaches):
    conn = sqlite3.connect(DB_PATH)

    null_count = sum(1 for v in series_data.values() if v is None)
    partial    = 1 if null_count > 0 else 0

    # Strip history before storing — keep snapshot lean
    lean_data = {}
    for field, data in series_data.items():
        if data is not None:
            lean_data[field] = {
                k: v for k, v in data.items() if k != "history"
            }
        else:
            lean_data[field] = None

    conn.execute("""
        INSERT INTO gs_price_snapshots
            (snapshot_date, fetched_at, series_data,
             deltas_7d, deltas_30d, deltas_90d, breaches, partial)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(date.today()),
        datetime.utcnow().isoformat(),
        json.dumps(lean_data),
        json.dumps(deltas_7d),
        json.dumps(deltas_30d),
        json.dumps(deltas_90d),
        json.dumps(breaches),
        partial,
    ))
    conn.commit()
    conn.close()
    print(f"\nSnapshot written — {len(lean_data)} series, "
          f"{null_count} nulls, {len(breaches)} breaches")

# ── MAIN RUN ──────────────────────────────────────────────────────────────────

# ── METALS FETCH (Yahoo Finance API + FRED) ───────────────────────────────────
# Aluminum: ALI=F (COMEX, USD/MT)
# Copper: HG=F (COMEX, USD/lb → convert to USD/MT)
# Steel HRC: WPU101707 (FRED PPI index, monthly)

METALS_YAHOO = {
    "aluminum_usd_mt": {
        "symbol":   "ALI=F",
        "unit":     "$/MT",
        "category": "metals",
        "convert":  lambda x: x,          # Already USD/MT
    },
    "copper_usd_mt": {
        "symbol":   "HG=F",
        "unit":     "$/MT",
        "category": "metals",
        "convert":  lambda x: x * 2204.62,  # USD/lb → USD/MT
    },
    # CME HRC steel futures front-month — added 2026-04-17 to give the
    # breach detector a daily series; FRED PPI (METALS_FRED below) retained
    # as the slow structural overlay. US industry convention is $/short-ton.
    "steel_hrc_usd_st": {
        "symbol":   "HRC=F",
        "unit":     "$/ST",
        "category": "metals",
        "convert":  lambda x: x,          # Already USD/short-ton
    },
}

METALS_FRED = {
    "steel_hrc_index": {
        "series_id": "WPU101707",
        "unit":      "index",
        "category":  "metals",
    },
}


# ── GPU COMPUTE PRICES (Vast.ai spot + Kalshi forward) ──────────────────────
# Added 2026-04-23. DC Axis 5 (GPU financing) anchor tape — previously QUIET.
# Two free public sources pending Bloomberg (OCPI) or Silicon Data access:
#
# Vast.ai (spot marketplace) — GET console.vast.ai/api/v0/bundles with a
# JSON search query in the ?q= param; returns real rentable on-demand
# offers with dph_total ($/hr total) and num_gpus. Per-GPU-hr is
# dph_total / num_gpus. We take the p50 across verified rentable offers
# per GPU SKU as the spot anchor.
#
# Kalshi (CFTC-regulated forward proxy) — events search returns monthly
# series like KXH100MON / KXH200MON / KXB200MON / KXA100MON. Each series
# has a 40-strike "Above $X" ladder. When untraded, we record the
# midpoint of the strike range as a reference level with volume=0 flag.
# Liquidity is expected to develop — field schema ready in advance.
#
# SKU scope: H100 SXM, H200, B200, A100 SXM4 — the four SKUs that map
# to institutional DC deals and to Ornn's OCPI and Silicon Data
# coverage, enabling a clean swap later.

VAST_GPU_MAP = {
    "gpu_h100_sxm_usd_hr":  {"vast_name": "H100 SXM",  "kalshi_series": "KXH100MON"},
    "gpu_h200_usd_hr":      {"vast_name": "H200",      "kalshi_series": "KXH200MON"},
    "gpu_b200_usd_hr":      {"vast_name": "B200",      "kalshi_series": "KXB200MON"},
    "gpu_a100_sxm_usd_hr":  {"vast_name": "A100 SXM4", "kalshi_series": "KXA100MON"},
}


def fetch_gpu_prices():
    """
    Fetch GPU compute prices.
      Spot  — Vast.ai public marketplace (verified rentable on-demand offers).
      Forward — Kalshi monthly compute-price ladder midpoint + liquidity flag.
    Returns dict of field_name -> snapshot row (same schema as other fetchers).
    Silent failure per SKU; never blocks the run.
    """
    import requests as _req
    import urllib.parse as _up

    results = {}
    today = str(date.today())

    # ---- Vast.ai spot ------------------------------------------------------
    vast_by_gpu = {}  # gpu_name -> list of dph/gpu
    try:
        q = {"verified": {"eq": True}, "rentable": {"eq": True},
             "rented": {"eq": False}, "type": "on-demand", "limit": 1000}
        url = ("https://console.vast.ai/api/v0/bundles?q="
               + _up.quote(json.dumps(q)))
        r = _req.get(url, timeout=25)
        if r.status_code != 200:
            raise ValueError(f"Vast HTTP {r.status_code}")
        for o in r.json().get("offers", []):
            name = o.get("gpu_name")
            dph = o.get("dph_total")
            ng = o.get("num_gpus") or 1
            if not name or not dph or ng <= 0:
                continue
            vast_by_gpu.setdefault(name, []).append(dph / ng)
    except Exception as e:
        print(f"  FAIL Vast.ai fetch: {e}")

    # ---- Kalshi forward ladder ---------------------------------------------
    kalshi_by_series = {}  # series_ticker -> (mid, n_strikes, total_volume)
    for field, info in VAST_GPU_MAP.items():
        series = info["kalshi_series"]
        try:
            r = _req.get(
                "https://api.elections.kalshi.com/trade-api/v2/markets",
                params={"series_ticker": series, "status": "open", "limit": 100},
                timeout=15,
            )
            if r.status_code != 200:
                raise ValueError(f"Kalshi HTTP {r.status_code}")
            mkts = r.json().get("markets", [])
            strikes = []
            vol = 0
            for m in mkts:
                tkr = m.get("ticker", "")
                # Strike is the trailing "-X.XXX" suffix
                tail = tkr.rsplit("-", 1)[-1]
                try:
                    strikes.append(float(tail))
                except ValueError:
                    continue
                vol += (m.get("volume") or 0)
            mid = (min(strikes) + max(strikes)) / 2 if strikes else None
            kalshi_by_series[series] = (mid, len(strikes), vol)
        except Exception as e:
            print(f"  FAIL Kalshi {series}: {e}")
            kalshi_by_series[series] = (None, 0, 0)

    # ---- Assemble per-SKU snapshot rows -----------------------------------
    for field, info in VAST_GPU_MAP.items():
        offers = vast_by_gpu.get(info["vast_name"], [])
        kmid, kstrikes, kvol = kalshi_by_series.get(info["kalshi_series"],
                                                    (None, 0, 0))
        if not offers and kmid is None:
            print(f"  FAIL {field}: no Vast or Kalshi data")
            results[field] = None
            continue

        if offers:
            offers_sorted = sorted(offers)
            n = len(offers_sorted)
            p25 = round(offers_sorted[n // 4], 3)
            p50 = round(offers_sorted[n // 2], 3)
            p75 = round(offers_sorted[(3 * n) // 4], 3)
            value = p50
            extras = {
                "vast_p25": p25,
                "vast_p50": p50,
                "vast_p75": p75,
                "vast_n_offers": n,
            }
        else:
            # Fall back to Kalshi midpoint if no Vast offers this pull
            value = round(kmid, 3) if kmid is not None else None
            extras = {"vast_n_offers": 0}

        extras.update({
            "kalshi_fwd_mid": round(kmid, 3) if kmid is not None else None,
            "kalshi_strikes": kstrikes,
            "kalshi_volume":  kvol,
        })

        results[field] = {
            "value":       value,
            "unit":        "$/GPU-hr",
            "category":    "gpu_compute",
            "series_id":   f"VAST+{info['kalshi_series']}",
            "series_date": today,
            "history":     [],
            **extras,
        }
        liq = "LIQ" if kvol > 0 else "nil-vol"
        print(f"  OK  {field}: spot p50 ${value} (n={extras.get('vast_n_offers',0)}) "
              f"| Kalshi {info['kalshi_series']} mid ${extras['kalshi_fwd_mid']} {liq}")

    return results


def fetch_metals_prices():
    """
    Fetch metals prices from Yahoo Finance API (aluminum, copper)
    and FRED (steel HRC index). Returns dict matching price snapshot schema.
    """
    import requests as _req
    results = {}

    # Yahoo Finance API — aluminum, copper
    for field, info in METALS_YAHOO.items():
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
                   f"{info['symbol']}?interval=1d&range=95d")
            r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}")

            data = r.json()
            result = data["chart"]["result"][0]
            closes = result["indicators"]["quote"][0]["close"]
            closes = [c for c in closes if c is not None]

            if not closes:
                raise ValueError("No price data")

            raw_price = closes[-1]
            value = round(info["convert"](raw_price), 2)

            # Build history (converted)
            history = [round(info["convert"](c), 2) for c in closes]

            results[field] = {
                "value":       value,
                "unit":        info["unit"],
                "category":    info["category"],
                "series_id":   info["symbol"],
                "series_date": str(date.today()),
                "history":     history,
            }
            print(f"  OK  {field}: {value} {info['unit']}")
        except Exception as e:
            print(f"  FAIL {field}: {e}")
            results[field] = None

    # FRED — Steel HRC PPI index
    for field, info in METALS_FRED.items():
        try:
            if not FRED_KEY:
                raise ValueError("FRED_API_KEY not set")
            fred = Fred(api_key=FRED_KEY)
            s = fred.get_series(info["series_id"]).dropna()
            if s.empty:
                raise ValueError("Empty series")
            value = round(float(s.iloc[-1]), 2)
            series_date = str(s.index[-1].date())
            results[field] = {
                "value":       value,
                "unit":        info["unit"],
                "category":    info["category"],
                "series_id":   info["series_id"],
                "series_date": series_date,
                "history":     [round(float(v), 2) for v in s.iloc[-95:].tolist()],
            }
            print(f"  OK  {field}: {value} {info['unit']} ({series_date})")
        except Exception as e:
            print(f"  FAIL {field}: {e}")
            results[field] = None

    return results


# ── FUEL MIX FETCH ────────────────────────────────────────────────────────────

def fetch_fuel_mix():
    """Fetch ERCOT fuel mix — gas/solar/wind/nuclear percentages."""
    results = {}
    try:
        ercot = gridstatus.Ercot()
        df = ercot.get_fuel_mix(date="latest")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            total = sum(v for k, v in latest.items()
                        if k != "Time" and isinstance(v, (int, float)))
            if total > 0:
                for fuel in ["Natural Gas", "Solar", "Wind", "Nuclear", "Coal and Lignite"]:
                    if fuel in latest:
                        pct = round(float(latest[fuel]) / total * 100, 1)
                        key = f"ercot_fuel_{fuel.lower().replace(' ', '_').replace('and_', '')}_pct"
                        results[key] = {
                            "value": pct, "unit": "%", "category": "fuel_mix",
                            "series_id": f"ERCOT_{fuel}", "series_date": str(date.today()),
                            "history": [],
                        }
                print(f"  OK  ERCOT fuel mix: gas={results.get('ercot_fuel_natural_gas_pct',{}).get('value',0)}% "
                      f"solar={results.get('ercot_fuel_solar_pct',{}).get('value',0)}% "
                      f"wind={results.get('ercot_fuel_wind_pct',{}).get('value',0)}%")
    except Exception as e:
        print(f"  FAIL ERCOT fuel mix: {e}")
    return results


def _generate_price_signals(series_data: dict):
    """Auto-generate signals from RTO DA curtailment, BESS, and scarcity events."""
    import pytz
    from gs.store import write_signal, is_duplicate
    from core.schema import Signal, SignalStatus, SourceType

    ET = pytz.timezone("America/New_York")
    today = datetime.now(ET).strftime("%Y-%m-%d")
    count = 0

    for key, v in series_data.items():
        if '_da' not in key or v is None or not isinstance(v, dict):
            continue

        iso = v.get("source", "RTO")
        loc = key.replace("_da", "").replace(f"{iso.lower()}_", "").upper()
        neg_hrs = v.get("negative_price_hours", 0) or 0
        spread = v.get("peak_offpeak_spread", 0) or 0
        da_high = v.get("da_high", 0) or 0
        da_avg = v.get("value", 0) or 0
        da_peak = v.get("da_peak_avg", 0) or 0
        da_offpeak = v.get("da_offpeak_avg", 0) or 0
        pdate = v.get("date", today)

        # CURTAILMENT
        if neg_hrs > 0:
            level = "RED" if neg_hrs > 4 else "AMBER"
            hl = f"{iso} {loc}: {neg_hrs} negative price hours DA {pdate}"
            if not is_duplicate("", hl, days=1):
                geo = "California" if "caiso" in key else ("West Texas" if "west" in key else iso)
                write_signal(Signal(
                    source_type=SourceType.PRICE, status=SignalStatus.ACTIVE,
                    headline=hl,
                    summary=f"{iso} {loc} DA showed {neg_hrs} negative hours on {pdate}. Avg ${da_avg:.2f}/MWh.",
                    source_name=f"{iso} DA Market", publication_date=pdate,
                    c_tags=json.dumps(["C06", "C15"] if "caiso" in key or "west" in key else ["C15"]),
                    t_tag="T2", alert_level=level, confidence=0.90, is_verified=1,
                    second_order=(
                        f"{neg_hrs} negative DA hours in {geo} — structural oversupply. "
                        f"As-produced solar PPAs earned zero/negative revenue for {neg_hrs} hours. "
                        f"Sustained 30+ days compresses DSCR below covenant. "
                        f"Moody's construction CDR 0.94%/yr anchors baseline risk."
                    ),
                ))
                count += 1
                print(f"    CURTAILMENT {level}: {iso} {loc} {neg_hrs} neg hrs")

        # BESS
        if spread > 50:
            label = "HOT" if spread > 100 else "WARM"
            hl = f"{iso} {loc}: DA spread ${spread:.0f}/MWh — BESS {label} {pdate}"
            if not is_duplicate("", hl, days=1):
                write_signal(Signal(
                    source_type=SourceType.PRICE, status=SignalStatus.ACTIVE,
                    headline=hl,
                    summary=f"{iso} {loc} DA: peak ${da_peak:.2f}, off-peak ${da_offpeak:.2f}, spread ${spread:.2f}.",
                    source_name=f"{iso} DA Market", publication_date=pdate,
                    c_tags=json.dumps(["C10", "C15"]), t_tag="T2",
                    alert_level="AMBER" if spread > 100 else "GREEN",
                    confidence=0.85, is_verified=1,
                    second_order=f"DA spread ${spread:.0f}/MWh — BESS arbitrage {label} in {iso}.",
                ))
                count += 1
                print(f"    BESS {label}: {iso} {loc} spread=${spread:.0f}")

        # SCARCITY
        if da_high > 200:
            hl = f"{iso} {loc}: DA scarcity ${da_high:.0f}/MWh {pdate}"
            if not is_duplicate("", hl, days=1):
                write_signal(Signal(
                    source_type=SourceType.PRICE, status=SignalStatus.ACTIVE,
                    headline=hl,
                    summary=f"{iso} {loc} DA peak ${da_high:.2f}/MWh on {pdate}. Avg ${da_avg:.2f}.",
                    source_name=f"{iso} DA Market", publication_date=pdate,
                    c_tags=json.dumps(["C15", "C01"]), t_tag="T1",
                    alert_level="RED", confidence=0.92, is_verified=1,
                    second_order=f"Scarcity ${da_high:.0f}/MWh — supply-demand imbalance in {iso}.",
                ))
                count += 1
                print(f"    SCARCITY RED: {iso} {loc} ${da_high:.0f}")

    print(f"  Price signals generated: {count}")
    return count


def run_price_fetch():
    print("="*55)
    print(f"GS PRICE FETCH — {datetime.now().strftime('%Y-%m-%d %H:%M ET')}")
    print("="*55)

    init_db()

    print("\nFetching Yahoo oil prices (CL=F, BZ=F)...")
    oil_data = fetch_yahoo_oil()

    print("\nFetching Yahoo gas price (NG=F Henry Hub)...")
    gas_data = fetch_yahoo_gas()

    print("\nFetching FRED series (rates, spreads)...")
    fred_data = fetch_fred_series()

    print("\nFetching Yahoo FX (real-time)...")
    fx_data = fetch_yahoo_fx()

    print("\nFetching Yahoo LNG benchmarks (JKM=F, TTF=F)...")
    lng_data = fetch_yahoo_lng(fx_data)

    print("\nFetching RTO hub prices...")
    rto_data = fetch_rto_prices()

    print("\nFetching metals prices...")
    metals_data = fetch_metals_prices()

    print("\nFetching fuel mix...")
    fuel_data = fetch_fuel_mix()

    print("\nFetching GPU compute prices (Vast.ai spot + Kalshi forward)...")
    gpu_data = fetch_gpu_prices()

    series_data = {**oil_data, **gas_data, **fred_data, **fx_data, **lng_data,
                   **rto_data, **metals_data, **fuel_data, **gpu_data}

    print("\nScanning RTO DA for price signals...")
    try:
        _generate_price_signals(series_data)
    except Exception as e:
        print(f"  WARN: Price signal generation failed: {e}")

    annotate_staleness(series_data)

    print("\nCalculating deltas...")
    deltas_7d, deltas_30d, deltas_90d = calculate_deltas(series_data)

    print("\nChecking thresholds...")
    breaches = check_thresholds(series_data, deltas_7d, deltas_30d)
    if breaches:
        print(f"  {len(breaches)} threshold breach(es) detected:")
        for b in breaches:
            stale_tag = (
                f" STALE({b['staleness_days']}d)"
                if b.get("stale") else ""
            )
            print(f"    BREACH {b['field']} "
                  f"{b['window']}{stale_tag}: {b['value']} "
                  f"(delta {b['delta']}, threshold {b['threshold']})")
    else:
        print("  No threshold breaches")

    write_snapshot(series_data, deltas_7d, deltas_30d, deltas_90d, breaches)

    print("\nPRICE FETCH COMPLETE")
    return series_data, breaches

if __name__ == "__main__":
    run_price_fetch()