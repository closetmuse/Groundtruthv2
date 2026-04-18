# GI — GroundIntelligence Encyclopedia Loader
# Reads encyclopedia/*.md → structured fingerprint store in memory.
# GT email builder calls match_signals_to_encyclopedia() to populate
# the Pattern Match section (Section 3 of daily email).
# E07 Hormuz is ACTIVE — never used as a historical precedent.
# Last Updated: April 2026

import os
import re
import json
from typing import Optional

# ── DEFAULT PATHS ─────────────────────────────────────────────────────────────

ENC_DIR = r"C:\Users\nagar_7kszmu8\GroundTruth_v2\encyclopedia"

# ── HEADER PARSER ─────────────────────────────────────────────────────────────

def _parse_header(text: str) -> dict:
    """
    Parse the # comment header block at the top of each encyclopedia .md file.

    Extracts code, event name, trigger date, primary/secondary regime,
    pattern match C-tags, status, and fingerprint date from lines beginning
    with '# '.

    Args:
        text: Full file content.

    Returns:
        Dict with parsed header fields.
    """
    header = {}

    def find(pattern, default=None):
        m = re.search(pattern, text, re.MULTILINE)
        return m.group(1).strip() if m else default

    header["code"]             = find(r'^# Code:\s*(.+)', "")
    header["event"]            = find(r'^# Event:\s*(.+)', "")
    header["trigger_date"]     = find(r'^# Trigger Date:\s*(.+)', "")
    header["trigger_event"]    = find(r'^# Trigger Event:\s*(.+)', "")
    header["primary_regime"]   = find(r'^# Primary Regime:\s*(.+)', "")
    header["secondary_regime"] = find(r'^# Secondary Regime:\s*(.+)', "")
    header["fingerprint_date"] = find(r'^# Fingerprint Date:\s*(.+)', "")
    header["status"]           = find(r'^# Status:\s*(.+)', "")

    # Extract pattern match C-tags
    tags_str = find(r'^# Pattern Match Tags:\s*(.+)', "")
    header["pattern_match_tags"] = [
        t.strip() for t in tags_str.split(",") if t.strip()
    ]

    # Extract regime code from primary regime string
    regime_match = re.search(r'(R\d)', header.get("primary_regime", ""))
    header["regime_code"] = regime_match.group(1) if regime_match else ""

    return header


# ── SECTION SPLITTER ──────────────────────────────────────────────────────────

def _split_sections(text: str) -> dict:
    """
    Split encyclopedia file into named sections by '## SECTION N' headers.

    Args:
        text: Full file content.

    Returns:
        Dict keyed by section number (1-5) with section text as values.
    """
    sections = {}
    parts = re.split(r'## SECTION (\d+)\s*[—–-]\s*', text)

    # parts = [preamble, "1", section1_text, "2", section2_text, ...]
    for i in range(1, len(parts) - 1, 2):
        section_num = int(parts[i])
        section_text = parts[i + 1]
        # Trim at next section or end
        sections[section_num] = section_text.strip()

    return sections


# ── FINGERPRINT PARSER (SECTION 1) ───────────────────────────────────────────

def _parse_fingerprint(section_text: str) -> dict:
    """
    Parse Section 1 fingerprint table into a dict of field→value pairs.

    The fingerprint table has format: | Field | Value | Notes |
    Extracts brent, UST, spreads, regime, and distinguishing feature.

    Args:
        section_text: Text of Section 1.

    Returns:
        Dict of fingerprint field names to their values.
    """
    fingerprint = {}
    for line in section_text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or "Field" in line or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            fingerprint[cells[0]] = cells[1]
    return fingerprint


# ── SIGNAL SEQUENCE PARSER (SECTION 2) ────────────────────────────────────────

def _parse_signal_sequence(section_text: str) -> list:
    """
    Parse Section 2 signal sequence tables into a list of signal dicts.

    Each table row becomes a dict with keys: phase, signal_type,
    description, sources.

    Args:
        section_text: Text of Section 2.

    Returns:
        List of signal dicts from all timing phases.
    """
    signals = []
    current_phase = ""

    for line in section_text.split("\n"):
        line = line.strip()

        # Detect phase headers: ### Early, ### Mid, ### Late, ### Lagging
        if line.startswith("### "):
            phase_match = re.match(r'### (\w+)', line)
            if phase_match:
                current_phase = phase_match.group(1)
            continue

        # Parse table rows
        if not line.startswith("|") or "Signal type" in line or "---" in line:
            continue

        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            signals.append({
                "phase":       current_phase,
                "signal_type": cells[0],
                "description": cells[1] if len(cells) > 1 else "",
                "sources":     cells[2] if len(cells) > 2 else "",
            })

    return signals


# ── IMPACT PARSER (SECTION 3) ────────────────────────────────────────────────

def _parse_impact(section_text: str) -> dict:
    """
    Parse Section 3 infrastructure finance impact.

    Extracts the metrics table and bilateral alpha summary.

    Args:
        section_text: Text of Section 3.

    Returns:
        Dict with 'metrics' (list of dicts) and 'bilateral_alpha' (str).
    """
    metrics = []
    bilateral_alpha = ""

    # Extract table rows
    for line in section_text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or "Metric" in line or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            metrics.append({
                "metric": cells[0],
                "value":  cells[1],
                "notes":  cells[2] if len(cells) > 2 else "",
            })

    # Extract bilateral alpha summary
    alpha_match = re.search(
        r'\*\*Bilateral alpha summary[^*]*\*\*:?\s*(.*?)(?=\n\n---|\n\n\*\*[A-Z]|\Z)',
        section_text,
        re.DOTALL,
    )
    if alpha_match:
        bilateral_alpha = alpha_match.group(1).strip()

    # Extract verification latency from metrics
    latency_lines = [
        m for m in metrics
        if "latency" in m["metric"].lower() or "verification" in m["metric"].lower()
    ]

    return {
        "metrics":          metrics,
        "bilateral_alpha":  bilateral_alpha,
        "latency_metrics":  latency_lines,
    }


# ── TRANSMISSION PARSER (SECTION 4) ──────────────────────────────────────────

def _parse_transmission(section_text: str) -> dict:
    """
    Parse Section 4 transmission mechanism chains.

    Extracts primary chain text, secondary chain text, and any named
    leading indicators.

    Args:
        section_text: Text of Section 4.

    Returns:
        Dict with 'primary_chain', 'secondary_chain', 'leading_indicator',
        and '2026_relevance' text blocks.
    """
    result = {
        "primary_chain":     "",
        "secondary_chain":   "",
        "leading_indicator": "",
        "relevance_2026":    "",
    }

    # Extract bold-header blocks
    blocks = re.split(r'\n\*\*([^*]+)\*\*:?\s*\n?', section_text)
    # blocks = [preamble, header1, text1, header2, text2, ...]
    for i in range(1, len(blocks) - 1, 2):
        header = blocks[i].lower().strip()
        text = blocks[i + 1].strip()

        if "primary chain" in header:
            result["primary_chain"] = text[:500]
        elif "secondary chain" in header or "parallel chain" in header:
            result["secondary_chain"] = text[:500]
        elif "leading indicator" in header:
            result["leading_indicator"] = text[:300]
        elif "2026" in header:
            result["relevance_2026"] = text[:500]

    return result


# ── RESOLUTION PARSER (SECTION 5) ────────────────────────────────────────────

def _parse_resolution(section_text: str) -> dict:
    """
    Parse Section 5 resolution signals.

    Extracts what ended the stress, first normalization indicators,
    recovery timeline, and what did not resolve.

    Args:
        section_text: Text of Section 5.

    Returns:
        Dict with 'ended_by', 'first_indicators', 'recovery_timeline',
        'unresolved', and 'sri_notes'.
    """
    result = {
        "ended_by":          [],
        "first_indicators":  [],
        "recovery_timeline": [],
        "unresolved":        [],
        "sri_notes":         "",
    }

    blocks = re.split(r'\n\*\*([^*]+)\*\*:?\s*\n?', section_text)
    for i in range(1, len(blocks) - 1, 2):
        header = blocks[i].lower().strip()
        text = blocks[i + 1].strip()
        lines = [
            l.strip().lstrip("- ").lstrip("0123456789. ")
            for l in text.split("\n")
            if l.strip() and l.strip().startswith(("-", "1", "2", "3", "4", "5"))
        ]

        if "ended the stress" in header or "what ended" in header:
            result["ended_by"] = lines or [text[:300]]
        elif "first indicator" in header or "normalization" in header:
            result["first_indicators"] = lines or [text[:300]]
        elif "recovery timeline" in header:
            result["recovery_timeline"] = lines or [text[:300]]
        elif "not resolve" in header or "did not" in header:
            result["unresolved"] = lines or [text[:300]]
        elif "sri" in header or "practitioner" in header:
            result["sri_notes"] = text[:500]

    return result


# ── MASTER LOADER ─────────────────────────────────────────────────────────────

def load_encyclopedia(enc_dir: str = ENC_DIR) -> dict:
    """
    Load all encyclopedia .md files into a structured fingerprint store.

    Reads all 8 files from the encyclopedia directory. Parses each into
    a structured dict with header metadata, fingerprint fields, signal
    sequence, capital stack impact, transmission mechanisms, and
    resolution signals.

    E07 (Hormuz) is flagged as ACTIVE — it is the current event, not a
    historical precedent, and is excluded from pattern matching.

    Args:
        enc_dir: Path to the encyclopedia directory.

    Returns:
        Dict keyed by encyclopedia code (E01-E08), each containing the
        fully parsed encyclopedia entry.
    """
    encyclopedia = {}

    md_files = sorted([
        f for f in os.listdir(enc_dir) if f.endswith(".md")
    ])

    for filename in md_files:
        filepath = os.path.join(enc_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        header = _parse_header(text)
        code = header.get("code", "")
        if not code:
            continue

        sections = _split_sections(text)

        entry = {
            # Header metadata
            **header,
            "filename":     filename,
            "is_active":    "ACTIVE" in header.get("status", "").upper(),

            # Parsed sections
            "fingerprint":  _parse_fingerprint(sections.get(1, "")),
            "signal_sequence": _parse_signal_sequence(sections.get(2, "")),
            "impact":       _parse_impact(sections.get(3, "")),
            "transmission": _parse_transmission(sections.get(4, "")),
            "resolution":   _parse_resolution(sections.get(5, "")),

            # Derived fields for matching
            "c_tags":       header.get("pattern_match_tags", []),
            "a_tags":       _extract_a_tags(text),
            "verification_latency": _extract_latency_summary(
                sections.get(3, ""), sections.get(4, "")
            ),
        }

        encyclopedia[code] = entry

    print(f"Encyclopedia loaded: {len(encyclopedia)} entries from {enc_dir}")
    for code, entry in sorted(encyclopedia.items()):
        status = "ACTIVE" if entry["is_active"] else "LOCKED"
        print(f"  {code}: {entry['event'][:50]} [{status}] "
              f"regime={entry['regime_code']} "
              f"c_tags={entry['c_tags']}")

    return encyclopedia


def _extract_a_tags(text: str) -> list:
    """
    Extract all A-tag references (A01-A27) from the full encyclopedia text.

    Args:
        text: Full encyclopedia file content.

    Returns:
        Deduplicated sorted list of A-tag codes found.
    """
    matches = re.findall(r'\bA(\d{2})\b', text)
    tags = sorted(set(f"A{m}" for m in matches))
    return tags


def _extract_latency_summary(section3: str, section4: str) -> str:
    """
    Extract a one-line verification latency summary from Sections 3 and 4.

    Looks for 'Verification latency' or 'Timeline to' patterns in the
    impact and transmission sections.

    Args:
        section3: Text of Section 3 (impact).
        section4: Text of Section 4 (transmission).

    Returns:
        Summary string of the key latency finding.
    """
    combined = section3 + "\n" + section4

    # Look for explicit latency lines in tables
    for line in combined.split("\n"):
        lower = line.lower()
        if ("verification latency" in lower or "timeline to capital" in lower) \
                and "|" in line:
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c]
            if len(cells) >= 2:
                return f"{cells[0]}: {cells[1]}"

    # Look for timeline statements in prose
    timeline_match = re.search(
        r'Timeline[^.]*?(\d+[\s–-]+\d+\s*(?:days|months|weeks|hours))',
        combined,
        re.IGNORECASE,
    )
    if timeline_match:
        return f"Timeline: {timeline_match.group(1)}"

    return "See encyclopedia entry for latency details"


# ── PATTERN MATCHER ───────────────────────────────────────────────────────────

def match_signals_to_encyclopedia(signals: list, encyclopedia: dict,
                                  current_regime: str = "R0") -> dict:
    """
    Score each encyclopedia entry against today's signal cluster.

    Matching weights:
      - C-tag overlap: 60%
      - Regime match: 30%
      - A-tag overlap: 10%

    E07 (ACTIVE) is excluded — it is the current event, not a precedent.

    Args:
        signals: List of Signal objects or dicts with c_tags and
                 optionally a_tags fields.
        encyclopedia: Dict from load_encyclopedia().
        current_regime: Current regime code (default R0).

    Returns:
        Dict with keys 'top_match', 'second_match', 'third_match',
        each containing the entry dict plus 'match_score' and
        'matched_c_tags' fields.
    """
    # Collect all c_tags and a_tags from today's signals
    signal_c_tags = set()
    signal_a_tags = set()
    for sig in signals:
        c = sig.get("c_tags", "[]") if isinstance(sig, dict) else getattr(sig, "c_tags", "[]")
        try:
            tags = json.loads(c) if isinstance(c, str) else c
            signal_c_tags.update(tags)
        except Exception:
            pass

        # A-tags may come from affected_deals or source a_tags
        a = sig.get("a_tags", "[]") if isinstance(sig, dict) else getattr(sig, "a_tags", "[]")
        try:
            tags = json.loads(a) if isinstance(a, str) else (a if isinstance(a, list) else [])
            signal_a_tags.update(tags)
        except Exception:
            pass

    if not signal_c_tags:
        return {"top_match": None, "second_match": None, "third_match": None}

    # Score each encyclopedia entry
    scores = []
    for code, entry in encyclopedia.items():
        # Skip E07 — it is the current event, not a precedent
        if entry.get("is_active", False):
            continue

        # C-tag overlap (60% weight)
        enc_c_tags = set(entry.get("c_tags", []))
        c_overlap = len(signal_c_tags & enc_c_tags)
        c_total = max(len(enc_c_tags), 1)
        c_score = (c_overlap / c_total) * 100

        # Regime match (30% weight)
        enc_regime = entry.get("regime_code", "")
        regime_score = 0
        if enc_regime == current_regime:
            regime_score = 100
        elif enc_regime == "R0" or current_regime == "R0":
            # R0 is compound — partial match with any component regime
            regime_score = 60
        elif entry.get("secondary_regime", "") and current_regime in entry["secondary_regime"]:
            regime_score = 50

        # A-tag overlap (10% weight)
        enc_a_tags = set(entry.get("a_tags", []))
        a_overlap = len(signal_a_tags & enc_a_tags)
        a_total = max(len(enc_a_tags), 1)
        a_score = (a_overlap / a_total) * 100

        # Weighted total
        total = (c_score * 0.60) + (regime_score * 0.30) + (a_score * 0.10)

        matched_c = sorted(signal_c_tags & enc_c_tags)

        scores.append({
            **entry,
            "match_score":    round(total, 1),
            "matched_c_tags": matched_c,
            "c_score":        round(c_score, 1),
            "regime_score":   round(regime_score, 1),
            "a_score":        round(a_score, 1),
        })

    # Sort by match score descending
    scores.sort(key=lambda x: x["match_score"], reverse=True)

    result = {
        "top_match":    scores[0] if len(scores) > 0 else None,
        "second_match": scores[1] if len(scores) > 1 else None,
        "third_match":  scores[2] if len(scores) > 2 else None,
    }

    return result


# ── EMAIL BLOCK BUILDER ──────────────────────────────────────────────────────

def build_pattern_match_block(match_result: dict) -> str:
    """
    Format the top encyclopedia match into a 3-line plain text block
    for email Section 3 (Historical Pattern Match).

    Format:
        Closest precedent: [Event name] ([code]) — [regime label]
        Pattern overlap: [score]% on [matched c_tags]
        Latency signal: [verification_latency from encyclopedia entry]

    Args:
        match_result: Dict from match_signals_to_encyclopedia().

    Returns:
        3-line plain text string for email insertion.
        Returns a fallback message if no match available.
    """
    top = match_result.get("top_match")
    if not top:
        return (
            "Closest precedent: No match — insufficient signal data\n"
            "Pattern overlap: N/A\n"
            "Latency signal: N/A"
        )

    code = top.get("code", "")
    event = top.get("event", "Unknown")
    regime = top.get("primary_regime", "")
    score = top.get("match_score", 0)
    matched_tags = ", ".join(top.get("matched_c_tags", []))
    latency = top.get("verification_latency", "See encyclopedia entry")

    block = (
        f"Closest precedent: {event} ({code}) — {regime}\n"
        f"Pattern overlap: {score}% on {matched_tags}\n"
        f"Latency signal: {latency}"
    )
    return block


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("="*55)
    print("GI ENCYCLOPEDIA — MODULE TEST")
    print("="*55)

    # 1. Load all entries
    print("\n1. Loading encyclopedia...")
    enc = load_encyclopedia()
    assert len(enc) == 8, f"Expected 8 entries, got {len(enc)}"
    print(f"   OK — {len(enc)} entries loaded")

    # 2. Verify E07 is flagged active
    print("\n2. Checking E07 active flag...")
    assert enc["E07"]["is_active"] is True
    assert enc["E01"]["is_active"] is False
    print("   OK — E07 active, others locked")

    # 3. Verify parsed structures
    print("\n3. Checking parsed structures...")
    for code in ["E01", "E03", "E08"]:
        entry = enc[code]
        assert len(entry["fingerprint"]) > 0, f"{code} fingerprint empty"
        assert len(entry["signal_sequence"]) > 0, f"{code} signals empty"
        assert len(entry["impact"]["metrics"]) > 0, f"{code} metrics empty"
        print(f"   {code}: fingerprint={len(entry['fingerprint'])} fields, "
              f"signals={len(entry['signal_sequence'])}, "
              f"metrics={len(entry['impact']['metrics'])}")
    print("   OK — all structures parsed")

    # 4. Run pattern match with mock signals
    print("\n4. Testing pattern matching...")
    mock_signals = [
        {"c_tags": '["C08", "C09"]', "a_tags": '["A12", "A15"]'},
        {"c_tags": '["C01", "C12"]', "a_tags": '["A01"]'},
        {"c_tags": '["C08", "C01"]', "a_tags": '["A04", "A06"]'},
    ]

    result = match_signals_to_encyclopedia(mock_signals, enc, "R0")

    top = result["top_match"]
    second = result["second_match"]
    third = result["third_match"]

    print(f"   Top match:    {top['code']} {top['event'][:40]} "
          f"({top['match_score']}%)")
    print(f"   Second match: {second['code']} {second['event'][:40]} "
          f"({second['match_score']}%)")
    print(f"   Third match:  {third['code']} {third['event'][:40]} "
          f"({third['match_score']}%)")

    # 5. Build email block
    print("\n5. Testing email block builder...")
    block = build_pattern_match_block(result)
    print(f"   {block}")
    assert "Closest precedent:" in block
    assert "Pattern overlap:" in block
    assert "Latency signal:" in block
    print("   OK — block formatted correctly")

    print("\ngi/encyclopedia.py operational.")