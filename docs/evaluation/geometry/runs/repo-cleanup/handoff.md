# repo-cleanup — handoff

## 1. State

- Branch `feat/regular-square-pyramid`, local only; no push, merge, PR or branch deletion.
- Product `be4b8287` · candidate `b4a33205…` · `CACHE_VERSION` 117 · `LLM_ONLY` · 0 model calls · 0 screenshots.
- User's change kept: `D frontend/public/favicon.svg` (never staged). Local `CLAUDE.md` (gitignored) — one stale T1
  sentence corrected, not committed.
- Human visual review: **NOT_APPROVED** (unchanged).

## 2. Gate

Recorded after T3 and the identity gates on a clean detached checkout of the final docs commit.

## 3. Next decisions for the user

1. The visual review packages still open (exact-dimensions, regular-triangular-pyramid-w01, W5/W4) and the D5 option.
2. Whether to schedule the model-surface wave that removes the remaining Informatics prompts and IR vocabulary
   (`ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`; needs a `CACHE_VERSION` bump and a measured surface).
3. A UI pass for `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` (preview glyphs, dead `geo3d-*` CSS) with a visual check.
