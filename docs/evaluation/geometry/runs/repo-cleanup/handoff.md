# repo-cleanup — handoff

## 1. State

- Branch `feat/regular-square-pyramid`, local only; no push, merge, PR or branch deletion.
- Product `be4b8287` · candidate `b4a33205…` · `CACHE_VERSION` 117 · `LLM_ONLY` · 0 model calls · 0 screenshots.
- User's change kept: `D frontend/public/favicon.svg` (never staged). Local `CLAUDE.md` (gitignored) — one stale T1
  sentence corrected, not committed.
- Human visual review: **NOT_APPROVED** (unchanged).

## 2. Gate

Clean detached worktree `D:/tmp/cleanup gate` (CRLF, path with a space), 0 model calls:

- **T3 `FULL_PRODUCT_GATE_PASS` at `645705ae`** (`diagnostics/t3_645705ae.log`): pytest 7241 passed / 1 skipped / 2
  deselected · vitest 1032/1032 (68 files) · typecheck + build · demo 5/5 · crash surface 6/6.
- **Identity gates** at `645705ae` (`diagnostics/gates_645705ae.log`): all green except `git diff --check` — a trailing
  blank line in `code_index_removed_entries.md` written by the split script. Fixed in `2da4cdeb` (docs only, one line);
  gates rerun at `2da4cdeb` (`diagnostics/gates_2da4cdeb.log`): candidate verify `b4a33205…` (102 files) · cache lock 117 /
  `b1714b56…` · schema export ×2 idempotent · `LLM_ONLY`, routing unchanged · model-surface files changed since `2c2dfbbf`:
  0 · evidence outside this run: only the candidate registry, `EVALUATION_CANDIDATE.json`, `RUN_NAMING.md` · `diff --check`
  clean · docs audit PASS · node harness 95 pass / 2 skipped / 0 fail · tree clean before and after. T3 is not rerun for a
  one-line docs change. The "catalogued reports changed: 1" line is the living `EVIDENCE_INDEX.md`.
- Before deleting, the full pytest at the working tree showed 15 reds, all of three known kinds: dirty-tree prechecks (cleared
  once committed), candidate not yet refrozen (cleared by `372f78c2`), CODE_INDEX stale paths (cleared by `be4b8287`).

## 3. Next decisions for the user

1. The visual review packages still open (exact-dimensions, regular-triangular-pyramid-w01, W5/W4) and the D5 option.
2. Whether to schedule the model-surface wave that removes the remaining Informatics prompts and IR vocabulary
   (`ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`; needs a `CACHE_VERSION` bump and a measured surface).
3. A UI pass for `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` (preview glyphs, dead `geo3d-*` CSS) with a visual check.
