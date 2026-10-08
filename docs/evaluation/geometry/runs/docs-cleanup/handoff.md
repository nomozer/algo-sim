# docs-cleanup — handoff

## 1. State

- Branch `feat/regular-square-pyramid`, local only; no push, merge, PR or branch deletion.
- Product commit `8c66249d` · candidate `b4a33205…` (unchanged hash, refrozen at `976e0eea`) · `CACHE_VERSION` 117 · `LLM_ONLY` ·
  0 model calls · 0 screenshots.
- User's change kept: `D frontend/public/favicon.svg` (never staged). Local `CLAUDE.md` (gitignored) updated for the new
  layout, not committed.
- Human visual review: **NOT_APPROVED** (unchanged; never written by the agent).

## 2. Gate

Clean detached worktree `D:/tmp/docs cleanup gate` (CRLF, path with a space; `frontend/node_modules` a junction to the main
checkout, removed afterwards), 0 model calls:

- **T3 `FULL_PRODUCT_GATE_PASS` at `08dd841c`** (`diagnostics/t3_08dd841c.log`): pytest 7241 passed / 1 skipped / 2
  deselected · vitest 1030/1030 (68 files; 1032 before minus the two tests of the removed RULES_v0.3 block) · typecheck +
  build · demo 5/5 · crash surface 6/6.
- **Identity gates at `08dd841c`** (`diagnostics/gates_08dd841c.log`): candidate verify `b4a33205…` (102 files) · cache lock
  117 / `b1714b56…` · schema export ×2 idempotent · `LLM_ONLY`, routing unchanged · model-surface files changed since
  `2a7179a9`: 0 · evidence outside this run: `EVALUATION_CANDIDATE.json`, `RUN_NAMING.md`, `evaluation/README.md` (all
  living) · the one "catalogued report" changed is the living `EVIDENCE_INDEX.md` · `diff --check` clean · docs audit PASS
  · node harness 95 pass / 2 skipped / 0 fail (97/97 in the main checkout) · tree clean before and after.

## 3. Next decisions for the user

1. The visual review packages still open (exact-dimensions, regular-triangular-pyramid-w01, W5/W4) and the D5 option —
   unchanged, still the canonical next action.
2. One backend task proposed (not started): retire the dead Informatics model surface in two steps — first the parts the
   geometry route never sends (six unloaded prompts, `pipeline._call_json`, the `domain=None` branch and the two `semantic_*`
   skills; cache identity re-lock + `CACHE_VERSION` bump, no live call needed because no geometry request changes), then,
   only with a live-budget decision, the IR container vocabulary that does reach the model. Callers:
   `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`.
3. A UI pass for the rest of `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` (`SamplePreview` glyphs, `threeD`, `specDrift`) with a
   visual check.
