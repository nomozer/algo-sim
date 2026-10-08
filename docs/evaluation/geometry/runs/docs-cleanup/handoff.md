# docs-cleanup — handoff

## 1. State

- Branch `feat/regular-square-pyramid`, local only; no push, merge, PR or branch deletion.
- Product commit `8c66249d` · candidate `b4a33205…` (unchanged hash, refrozen at `976e0eea`) · `CACHE_VERSION` 117 · `LLM_ONLY` ·
  0 model calls · 0 screenshots.
- User's change kept: `D frontend/public/favicon.svg` (never staged). Local `CLAUDE.md` (gitignored) updated for the new
  layout, not committed.
- Human visual review: **NOT_APPROVED** (unchanged; never written by the agent).

## 2. Gate

Pending — recorded by the commit that follows this one (T3 and identity gates in a clean detached worktree at the
documentation commit of this run).

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
