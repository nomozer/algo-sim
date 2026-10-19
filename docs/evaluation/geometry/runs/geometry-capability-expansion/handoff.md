# Handoff — geometry capability expansion (Hybrid Wave 2B)

Verdict: **WAVE2B_READY_FOR_GO_MAIN_REVIEW** — stopped at the GO MAIN gate; nothing merged or pushed.

## Identity

- Branch `research/hybrid-wave2b-geometry-expansion` from `main` = `origin/main` = `224328a2`.
- Commits: product `08596652` · corpus/oracle/harness `8090e8e8` · first freeze `56eff5c3` (superseded) · docs `4f262821` ·
  review fixes `e9ec0f40` · refreeze `b8e3f112` (112 files, `520d414423788f3e9eabfcc5813968a50209b155f560baad8994b1747444730c`) ·
  docs `a52839ae` (T3 head) · this receipt commit.
- Versions `geometry-functions/8` · `geometry-fact-planner/9` · `geometry-function-engine/7`; Adapter `/2`, envelope `/1`.
- Cache **127** (no bump), `LLM_ONLY`, `flat` surface `485d3834…` unchanged (owner decision), TypedFact `aa9d93ee…`,
  v3 `4bff35bb…`, route A `5ceb0f99…` / `7ea511a6…` unchanged. Hybrid product **NO-GO**. Live calls **0**.
- Findings: [`report.md`](report.md) · contract:
  [`GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md`](../../../../architecture/GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md) ·
  data: [`results/`](results/), [`run.json`](run.json).

## Receipts

- Authoritative T3 at `a52839ae` (detached temp worktree, removed): **`FULL_PRODUCT_GATE_PASS`** — backend 11110/0,
  frontend 70 files / 1146, typecheck + build, demo 5/5 (+1/1 reduced), crash 6/6; freeze `--verify` MATCH
  ([`authoritative-t3.json`](authoritative-t3.json), [`verification/t3-authoritative.log`](verification/t3-authoritative.log)).
- Independent read-only review on `56eff5c3`: REQUEST_CHANGES (1 MAJOR face-plane false serve, 2 MINOR) → fixed in
  `e9ec0f40` with 4 RED-first tests, refrozen, re-measured — [`report.md` §10](report.md).
- Dev comparison (20 cases, independent oracle): 12/12 VERIFIED, 16/16 goals, 8/8 correct refusals, 0/20 false serves vs
  pre-run `main` 0/12 ([`results/evaluation-review-fix/metrics.json`](results/evaluation-review-fix/metrics.json), identical to
  the first measurement). Gemini blind holdout BH2A-01..18 not used.
- Compatibility: 174-row regression unchanged; 41/41 Adapter `/2` fixtures via the declared identity chain; NLU gold only
  D04 (declared layer `results/historical-gold-delta.json`); v3 matrix unchanged.

## Open, not hidden

- `ISSUE-RESEARCH-HYBRID-GEOMETRY-CAPABILITY-GAPS` (`docs/OPEN_ISSUES.md`): `flat` has no ratio point; ⊥-line plane on
  prisms; unnamed ratio points; other ratio wordings; irrational trapezoid; oblique prism by angle; the ⊥-line plane is a
  declared rule, not search-discovered.
- Main-checkout pytest shows `test_holdout_readiness` red only because of the user's untracked `*-go-main/` receipts (tree
  not clean); green in the clean T3 worktree.
- Process note: two edits early in the run used shell writes into `backend/` (`sed -i` on `planner.py`, `cat >>` on a
  test) against the repo's Edit/Write rule; the content is in the reviewed diff, the tool rule was not followed.

## If the owner grants GO_MAIN_HYBRID_WAVE2B

Recheck identity (`main` = `origin/main` = `224328a2`, branch head = receipt commit); `git merge --ff-only`; post-main
smoke (capability tests, 174 regression, fixtures `--verify`, freeze `--verify`); `git push origin main` (no force);
verify remote; `git branch -d`; preserve untracked receipts, `algosim.db`, other worktrees.
