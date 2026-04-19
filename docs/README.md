# GroundTruth V2 — Documentation

This folder is the authoritative record of the platform's conventions,
workflows, and change history. It complements but does not replace:

- **`CLAUDE.md`** (repo root) — the lean philosophical brain: owner,
  architecture, trigger phrases, analytical standards. Updates on
  methodology change only.
- **`outputs/alpha_ledger.md`** — contemporaneous record of findings
  (ALFs, hardening indicators, resolutions). Append-only per discipline.
- **`GT_Reference.md`, `GT_Pipeline.md`, `GT_BuildLog.md`** — companion
  reference files loaded on demand (see CLAUDE.md companion section).
- **`PHASE*_BRIEFING.md`** — historical milestone briefings (read-only
  archives of past phase transitions).

## What's in this folder

| File | Purpose | Update cadence |
|---|---|---|
| [`README.md`](README.md) | This index | On structural changes to docs/ |
| [`CHANGELOG.md`](CHANGELOG.md) | Chronological log of platform changes (code + schema + conventions) | Every non-trivial commit |
| [`conventions.md`](conventions.md) | Output paths, file naming, cadence, C-tag schema, ledger protocol | When a convention changes |
| [`workflows.md`](workflows.md) | Git workflow, daily capture procedure, weekly Sunday procedure | When a workflow changes |

## Navigation by intent

**"What changed on the platform this week?"** → `CHANGELOG.md`

**"Where should today's brief go? What's the file-naming rule?"** → `conventions.md`

**"How do I run a daily capture? What's the Sunday weekly procedure? When do I commit?"** → `workflows.md`

**"What does this platform actually do at a high level?"** → `../CLAUDE.md`

**"What are the active findings and their VL windows?"** → `../outputs/alpha_ledger.md`

## Discipline

Per [feedback_documentation_discipline.md memory](../memory/feedback_documentation_discipline.md):

1. Every non-trivial platform change is committed with a descriptive
   message AND appended to `CHANGELOG.md` with date + scope.
2. If a change touches a convention or schema, update `conventions.md`
   in the same commit.
3. If a change touches an operational workflow, update `workflows.md`
   in the same commit.
4. `CLAUDE.md` updates only on methodology / owner / architecture
   changes — not every fix. The changelog is the high-frequency record;
   CLAUDE.md is the low-frequency anchor.
