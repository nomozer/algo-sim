# AXO HYBRID /20 — Final direct merge & two-session bootstrap (`FINAL_MASTER_REPORT`)

**Date:** 2026-11-22 · **Run:** `final-direct-merge-two-session-bootstrap` · **Merged branch:** `feat/model1-final-text-acceptance`

> **Verdict:** `CODE_INTEGRATION_COMPLETED = TRUE`, `MODEL1_TEXT_ACCEPTANCE = FAIL`. Candidate 158 is on `main` as
> code behind dormant local flags; `HYBRID_ROUTE_MODE = live` stays the default; Holdout-7 stays FAIL
> (`46/58`, fallback `3/15`, isolated SLM `25/58`); `LOCAL_TEXT_MODEL1_VERIFIED = false`;
> `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED = false`. No pull request was created; nothing was force-pushed.

## 1. Pre-merge conditions and how each was closed

| Condition | Result | Evidence |
|---|---|---|
| Candidate 158 identity | PASS: 0 product lines changed since `2bb0211a1`, freeze `bdb737bb…` (127 files), cache lock 158, 0 migrations | `run.json` |
| Authoritative Full T3 (/19, `b10c0a1e4`) | PASS, reused only for the pre-merge decision | `../model1-final-text-acceptance/AUTHORITATIVE_FULL_T3_RECEIPT.json` |
| Dormant-flag integration despite Holdout-7 FAIL | accepted by the Owner (session 2026-11-22) | `run.json` |
| Publication safety, full range | 12 `HARDCODED_PASSWORD` hits (11 path/blob pairs, 3 synthetic loopback sign-up values) → Owner approved exactly those 11 entries through the interactive permission prompt (`approve_d4.ps1`, sha256 `3df15e5c…`); range gate `violations=0`, exit 0. The 96 `--head` hits already on `main` were not approved here. | `run.json` · `../publication-safety-remediation/publication_exceptions.json` |
| Gemini live | smoke (5 calls, `gemini-2.5-flash`): L1–L3 exact, L4/L5 fail-closed `INVALID_TYPED_FACT_NEXT`, N1 gated, verdict INCONCLUSIVE (3/5 < 4/5). Paired diagnosis (4 calls): `main` and the branch both refuse L4/L5 at the same stage; the request is byte-identical and the rejecting normalization is AST-identical. Pre-registered verdict INCONCLUSIVE (no payload capturable); attribution: shared pre-existing limit. Owner decided to merge. 9 of 12 budgeted calls used. | `LIVE_SMOKE_*` · `LIVE_PAIR_DIAGNOSIS_*` |
| Owner's untracked data on `main` | 6 files in `post-merge-cleanup-closure/` byte-identical before and after | `POSTMERGE_RECEIPT.json` |

## 2. Merge

- Local `main` had moved during the session to `dde2dcfd9` (another session merged and later pushed
  `feat/axo-hero-enter-portals`). The Owner chose to merge on top of it.
- Rollback anchor: local annotated tag `pre-model1-merge` → `dde2dcfd9` (not pushed).
- **Merge commit `3104635db`** — first parent `dde2dcfd9`, second parent `46f87eaec`. Three test-file conflicts, both
  sides having made the same tests portable; resolutions in `POSTMERGE_RECEIPT.json`.
- Follow-ups on `main`: `a66ec7936` (docs test pin 109 → 127), `4978ac01f` (auth CLI test decodes UTF-8; red on
  `dde2dcfd9` too), `f2cc62b1e` (**evaluation candidate re-frozen** at the merge on Owner decision: CACHE 158, 127 files,
  tree `7bd85b6e…`), `e6ba1fea1` (3 PENDING C21 approval templates re-bound; still PENDING).

## 3. Post-merge verification

- First Full T3 on `4978ac01f`: FAIL — 9 evaluation-guard refusals (`measured_system differs from frozen
  EVALUATION_CANDIDATE.json`, 8 of them already red on `dde2dcfd9`), plus a launch-environment vitest failure
  (lower-case `d:` cwd from Git Bash). Not used as evidence of the code.
- **Authoritative Full T3 on `e6ba1fea1`: `FULL_PRODUCT_GATE_PASS`** in a fresh clean detached worktree — 15,200 pytest
  (0 failed), 189 files / 2,302 vitest, build, demo 5/5 + 1/1, crash surface 6/6; log sha256 `265a6b90…`.
- After the merge: freeze `--verify` PASS, `--verify-historical` PASS, cache lock PASS, `HYBRID_ROUTE_MODE` default `live`.

## 4. Push, cleanup, bootstrap

Done after this commit and recorded outside the repo in `D:/tmp/axo20/GIT_CLEANUP_AND_BOOTSTRAP_RECEIPT.json`, so
that no unpushed commit stays on `main`: one plain push of `main` (no tags, no force), removal of the shared worktree
`simulation-intent-slm-recovery` and `git branch -d` of the 10 merged /10–/19 branches, and the two session worktrees
from the same pushed commit.

## 5. Handed to the next sessions

- **Session 1 — `feat/model1-text-capability-performance`:** Holdout-7 failure groups (`learner_colloquial` 1/10,
  `teacher_wording` 12/15; 19 `SLM_UNRESOLVED`, 12 Source Gate quote-binding rejections) as an exposed regression set —
  new prospective data needed for any new acceptance; live L4/L5 refusal in transport normalization (shared with old
  `main`); latency, queue, Linux runtime, GGUF provisioning.
- **Session 2 — `feat/dynamic-construction-planner-model2`:** integrate frozen Construction Planner /2, verify Scene3D
  handoff and dynamic steps, then a small CPU-friendly Model 2 whose every step goes through Registry and Exact Kernel.
- **Shared contracts** (TypedFactNext, Source Gate, Planner, Registry, Exact Kernel, Adapter schema, `CACHE_VERSION`,
  live-acceptance harness): one owner at a time, change by proposal → contract tests → ordered merge.
- **Not ours, still open:** publication hit in `frontend/scripts/accept-landing-cutover-and-admin.mjs:402` (already on
  `origin/main` via hero-portals); the hero-portals freeze contract and CLAUDE.md §4.5 disagree on re-freezing after
  app-layer changes and need one Owner wording. OCR stays out of scope.

## 6. Rollback

Operational: redeploy `dde2dcfd9` (tag `pre-model1-merge`; 0 migrations in the merge; cache rows are policy-isolated).
Git, forward only: `git revert -m 1 3104635db` (plus reverting the four follow-ups if needed); never reset or force-push `main`.
