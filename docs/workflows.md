# GroundTruth V2 — Workflows

Operational procedures. Updated whenever a workflow changes — in the same
commit as the code change, with a `CHANGELOG.md` entry referencing the
commit.

---

## Git workflow

### Repository
- **Remote:** `https://github.com/closetmuse/Groundtruthv2.git`
- **Account:** `closetmuse` (personal, private repo)
- **Branch model:** single `main` branch. No feature branches — this is
  a one-operator repo.

### When to commit
Every non-trivial change. Specifically:
- After a capture workflow completes (daily brief written + ledger appended)
- After any classifier / scorer / infra code change
- After a weekly Sunday bundle is written
- After any convention or schema change (bundled with doc updates)

**Do not let changes sit uncommitted across sessions.** The contemporaneous
record discipline requires the git log to reflect the platform's actual
state at any given time.

### Commit message convention
Two-part format using `-m` twice:

```
git commit -m "<short title>" -m "<body>"
```

Title: under 60 characters, imperative voice, dated when scope warrants
(e.g., "Classifier recalibration + weekly sector alpha briefs (2026-04-19)").

Body: one or two paragraphs. What changed, why, what was touched. Matches
the summary-paragraph style of `docs/CHANGELOG.md` entries so the two
are easy to cross-reference.

Always include the co-author line:
```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Use a HEREDOC for multi-line bodies — see git-safety-protocol docs for
the exact pattern.

### Push cadence
Manual. Commits stay local until Sri chooses to push — typically at EOD,
or after a reviewing pass over the day's commits. The capture workflow
(`finalize_capture.py`) never pushes; it only commits.

```
git push
```

Credentials cached via Windows Credential Manager after first push.

*Note: this replaced the "push after every commit" rule on 2026-04-20
when the finalize_capture workflow landed. Hold-local is the default.*

### What not to commit
`.gitignore` already handles:
- `.env` and any `*credentials*.json`, `*token*.json`, `*.pem`, `*.key`
- `groundtruth.db` and `*.db-journal`
- MT Newswires data dumps
- Generated `email_fallback.html` and test renders

Verify `git status` before every commit. If anything sensitive slips in,
fix `.gitignore` first, then unstage, then commit.

---

## Daily capture procedure

Trigger phrase: **"Run GroundTruth capture"**

### Sequence (enforced by `.gt_capture_pending` marker — 2026-04-20)

Three commands. The marker file at project root is the state handoff:
`run_manual.py` writes it, `finalize_capture.py` consumes it. Claude's
only role is step 2 — the bookends are script-enforced, so the workflow
survives a fresh session with no prior context.

1. **`python infra/run_manual.py`** — fetches P1 sources and prices,
   classifies, scores, runs GPi + encyclopedia + health, writes
   `email_fallback.html`, archives the dashboard under the day folder.
   On success, writes `.gt_capture_pending` (JSON) at project root
   containing the exact brief filename Claude must produce, capture slot
   (AM/PM/EOD), signal counts, encyclopedia top, and runtime. Emits a
   "NEXT STEP" block to stdout with the brief path.
2. **Hand-write the consolidated sector brief** to the **exact path**
   in the NEXT STEP block — e.g.
   `outputs/daily/2026-04/04-20/sector_briefs_2026-04-20_0522ET.md`.
   No timestamp drift, no alternate filenames. Follow the standing
   sector-brief template (see `conventions.md`). Append Alpha findings
   to `outputs/alpha_ledger.md` in the same step — the finalizer picks
   up ledger edits automatically.
3. **`python infra/finalize_capture.py --headline "<one-line theme>"`** —
   verifies the brief exists and is non-trivial (>2KB unless `--force`),
   git-adds the day folder + `outputs/alpha_ledger.md` (if modified),
   commits with an auto-generated message (title = slot + capture ts +
   headline; body = signal counts + precedent + runtime + co-author
   trailer), and clears the marker. Idempotent — if the brief is already
   in a prior commit, it exits cleanly without creating an empty commit.
   **Does not push.** Push cadence is manual (hold-local protocol per
   2026-04-20; Sri decides when to sync remote).

After step 3, reply with a markdown link to the brief. Do **not** paste
the brief body into chat. Post-commit expansions go into
`addendum_<HHMM>ET_<topic>.md` in the same day folder — never edit the
committed brief retroactively.

### Error recovery

- `ERROR: no .gt_capture_pending marker` — no capture has run since last
  finalize, or finalize already ran. Check `git log --oneline -5`.
- `ERROR: expected brief not found` — brief was written to a path that
  does not match the marker. Either rename the brief to match or rerun
  `run_manual.py` to get a fresh marker.
- `WARN: brief is only N bytes` — heuristic stub-detection. Use `--force`
  if the brief is legitimately short (rare — captures usually exceed 2KB).

### On-demand consolidated dashboard

If the email-style consolidated view is wanted for a specific capture
(all 37 price series, all RED/AMBER enumerations, binary events
countdown, health panel rendering in one HTML), run:

```
python infra/send_email.py
```

This writes `email_fallback.html` at the project root (gitignored) and —
if Gmail OAuth is valid — also sends. If OAuth is expired, the HTML
still writes locally; you can open it in a browser for the dashboard
view. Ad-hoc tool, not a workflow step.

### Discipline drift checks
Before shipping a brief, run the drift checks documented in
[brief_discipline_drift_checks memory](../memory/feedback_brief_discipline_drift_checks.md):
- **Series-date vs event-time:** on every attribution claim, does the
  cited price / date match the actual tape?
- **Named-deal cap:** no more than 2 deal names in brief body; compress
  broader class to mechanism sentence. (Full overlay lives separately.)

---

## Weekly Sunday procedure

Every Sunday, after the daily capture is complete, produce the weekly
sector-alpha bundle.

### Output path
`outputs/weekly/YYYY-MM/MM-DD/` — where MM-DD is the Sunday's date.

### Files (full bundle)
1. **`GR_Brief_YYYY-MM-DD.md`** — weekly research brief focused on the
   week's most consequential sector. Three-part structure (What moved /
   Non-obvious observation / Act this week) — see
   `outputs/weekly/2026-04/04-19/GR_Brief_2026-04-19.md` as the canonical
   example.
2. **`DC_Sector_Alpha_YYYY-MM-DD.md`** — sector-level alpha brief for
   Data Centers. 8-section template per `conventions.md`.
3. **`Power_Sector_Alpha_YYYY-MM-DD.md`** — same for Power.
4. **`LNG_Sector_Alpha_YYYY-MM-DD.md`** — same for LNG.
5. **Amendment** (if needed) — `GR_Brief_YYYY-MM-DD_amendment.md`. File
   only produced when post-hoc Sunday review surfaces a reframing. Never
   rewrite the original — amend with explicit append file.
6. **Pipeline overlay** (on-demand) — `GR_<sector>_Pipeline_Overlay_YYYY-MM-DD.md`.
   Deal-level action items only when pipeline-specific questions warrant.

### Sequence
1. Daily capture completes (see above).
2. Review the week's signals via
   `python ge/scorer.py --calibrate --days 7` and direct DB query for
   C16/C17/C18 clusters and AMBER distribution.
3. Draft the three sector-alpha briefs.
4. Draft the GR weekly brief.
5. If deal-level actions warrant, draft the pipeline overlay.
6. Append weekly findings to alpha ledger (new ALFs + hardening entries).
7. Commit + push.

### Quality check before shipping
- Every ALF cited has its signal ladder enumerated with IDs + dates.
- Every VL window is explicit (no "~3 months" — always state dates).
- Every "non-obvious observation" has a transmission mechanism attached
  (mechanism + timeline + asset specificity per CLAUDE.md standards).
- Sector-alpha briefs are deal-free in body.

---

## Classifier recalibration workflow

When a classifier or scorer change is made:

### 1. Change the code
Edit `gs/classify.py` (schema, C-tags, second_order logic) or
`ge/scorer.py` (weights, boosts, thresholds). Bump `SCORER_VERSION`
and add a `TUNING_HISTORY` entry for scorer changes.

### 2. Smoke-test against the week's real signals
```
python ge/scorer.py --calibrate --days 7
```
Verify distribution shift makes sense. Spot-check the signals that moved
between alert buckets.

### 3. Backfill stored signals
```
python infra/backfill_ctags.py --days 14             # dry-run
python infra/backfill_ctags.py --days 14 --commit    # tag-only
```

For persistence of new alert levels on existing signals (changes how
briefs pulled months later will read):
```
python infra/backfill_ctags.py --days 14 --commit --rescore
```
⚠️ This writes new `alert_level` + `weighted_score` and stores originals
in `verification_note` as `orig_alert=X orig_weighted=Y`. Use selectively.

### 4. Selective rollback if overreach
If the rescore pass caused collateral downgrades from novelty-context
shift:
```
python infra/rollback_rescore.py                     # dry-run
python infra/rollback_rescore.py --commit            # writes
```
This restores originals for non-structural signals (no C16/C17/C18 tag)
while keeping elevation on signals the new lane was designed to help.

### 5. Document
- Bump `docs/CHANGELOG.md` with a new dated entry (scope + summary +
  rationale + downstream effects).
- Update `docs/conventions.md` if schema or tag list changed.
- Commit all docs + code changes in the same commit with a message that
  references the classifier recalibration.

---

## Health panel

The health panel runs automatically at the end of every capture (see
`gt/orchestrator.py` stage 9). Interpret:

- **HEALTHY** (80%+) — platform is operating correctly.
- **DEGRADED** (50-80%) — one or two real issues to investigate.
- **FAILING** (<50%) — genuine platform breakage.

If the panel reads DEGRADED or FAILING, first check whether it's a
calibration issue (thresholds vs actual operating model) before
investigating as a code bug. The 2026-04-19 recalibration corrected
five such calibration issues — see `CHANGELOG.md` entry.

---

## When to touch `CLAUDE.md`

Rarely. Only when:
- Owner / architecture changes
- Agent roster changes (new agent added, existing agent retired)
- Trigger phrases change
- Analytical standards change (transmission mechanism rule, second-order
  field discipline, etc.)
- New companion-file pattern introduced

Routine fixes / schema additions / cadence refinements: update
`docs/CHANGELOG.md` + `docs/conventions.md` instead. CLAUDE.md stays lean.
