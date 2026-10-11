# Hybrid B slice 1: main integration

- Approved by the user (2026-10-11): integrate slice 1 (B26) with the two Important fixes of the independent review.
- LOCAL. No PR, no cherry-pick, no force.
- LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = `LLM_ONLY`, `CACHE_VERSION` 125.
- Remote state is not recorded here: check `git log -1 origin/main`. A push needs the user's separate confirmation.

## 1. Pre-flight

| Item | Value |
|---|---|
| Main checkout | on `main`; only `?? frontend/public/` untracked (the user's; untouched) |
| `main` = `origin/main` | `548066a8` (`ls-remote` agrees) |
| Research branch | `research/hybrid-compiler-capability-audit` at `a246dd19`; `main` is its ancestor |
| Candidate before | `dda3a884…` (product `62f0b18e`) |

## 2. Integration

```
git merge --ff-only research/hybrid-compiler-capability-audit      # 548066a8 → a246dd19
```

- No merge commit.
- Product files changed against `548066a8`: `backend/app/ai/function_route.py` and `backend/app/simulation/geometry_functions/{engine,planner,registry}.py`. All are on the Hybrid route, which the default `/api/analyze` route does not reach.

## 3. Verification on `main` (clean detached worktree at `a246dd19`)

| Check | Result |
|---|---|
| `freeze_evaluation_candidate.py --verify` | exit 0: 110 files, `dda3a884…` |
| T3 (`npm run test:full`) | **FULL_PRODUCT_GATE_PASS**: pytest 8362 passed, 0 failed (1 skipped, 2 deselected, 4 xfailed); vitest 1051; build; demo replay; crash surface |
| Regressions | none |

**Preserved:**
- the locked A/B candidate `12da4768…`;
- historical A/B evidence;
- the benchmark baseline (`hybrid-compiler-capability-audit/baseline/metrics.json`) and its `after` measurement, byte-for-byte.

## 4. Open after integration

| Issue | Note |
|---|---|
| `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK` | other `ask_*` paths can answer a clause that does not ask (routes A and B) |
| `ISSUE-ARCH-LINE-SEGMENT-SEMANTIC-DISTINCTION` | new. "từ S đến BD" / "đường thẳng BD" → the line. Probe: "đoạn thẳng BD" → `SOURCE_OBJECT_MISMATCH`; "đường thẳng BC" → √13 (oracle 13 for d²). There are no segment semantics |
| `ISSUE-ARCH-HYBRID-AUXILIARY-POINT-LIMITS` | one wording; coinciding or redundant feet; the name can appear in refusal details |
| `ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION` | pre-existing crash |
| `ISSUE-ARCH-HYBRID-COMPILER-NO-GOAL-COMPOSITION` (B27), `ISSUE-ARCH-HYBRID-SOURCE-CUE-CENTRE-OF-SQUARE` (B28) | **not approved for implementation** |
| `ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE` | P1 on `main` |

There is **no claim** that Hybrid B is accurate with real Gemini: the evidence is from verified facts and a fake provider only.

## 5. Clean-up so far

- The verification worktree `main-slice1-verify` was removed without `--force`, after its `node_modules` junction was taken out with `rmdir` (target intact). 1 700 545 088 bytes freed.
- Still kept, until push and remote verification:
  - the research worktree;
  - the `research/hybrid-compiler-capability-audit` branch.
- The two real-model branches are kept and untouched, including the unpushed live-run commit on `feat/real-model-pilot-tooling`.
- `.superpowers/worktrees/geometry-library-expansion` (≈ 551 KB, CodexSandboxOffline) is unchanged and needs an administrator. No ACL was changed.
