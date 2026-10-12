# Integration handoff: A (S0 + section baseline) and B (S1 + S2 hardening)

Status: `HYBRID_HARDENING_AWAITING_INTEGRATION_DECISION`.
Next action: `HYBRID_HARDENING_INTEGRATION_DECISION` (the user's).
LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = `LLM_ONLY` (cache 125).
This run does not merge, push or open a PR. The two parts are not combined into one candidate here.

## A. S0 + section baseline (already reviewed)

| Item | Value |
|---|---|
| Branch / tip | `research/hybrid-simulation-capability-audit` @ `9cfd0fca` (unchanged by this run) |
| Content | S0 gate fix, section / intersection-line slice, `hybrid-slice-review` fixes |
| Candidate | `451b046c…` (product `b3e946e9`, refreeze `542e3894`) |
| T3 | `FULL_PRODUCT_GATE_PASS` at `91c33925` (pytest 8 509 / vitest 1 051) |
| Procedure | [`hybrid-slice-review/handoff.md`](../hybrid-slice-review/handoff.md): `main` (`a6e27a78`) is an ancestor, so a fast-forward to `9cfd0fca` |
| Known open in A | the residual false serves A–D, closed by B; the invisible intersection line, fixed by B |

## B. S1 + S2 (this run)

| Item | Value |
|---|---|
| Branch / tip | `research/hybrid-semantic-hardening`, child of `9cfd0fca`; tip: see `run.json` |
| Product commits | S1 `23481bda`, `fda835c3` (`registry.py`); S2 `33e711f9`, `2db6d64b` (`scene3d-model.ts`, `scene3d-view.tsx`) |
| Candidate / T3 | see `run.json` |
| Fast-forward | `main` → B also contains A. Integrating B alone integrates both |

**Options, for your decision:**
1. **A then B:** fast-forward `main` to `9cfd0fca`, run T3, then fast-forward to B's tip and run T3 again. This keeps two reviewable integration points.
2. **B only:** one fast-forward to B's tip. A's open findings never reach `main` as open, but B's evidence then covers both.
3. **A only:** if S1/S2 need more review. Then `main` gets A with its declared residual risk, as in the `hybrid-slice-review` GO.

The same commands as A apply (from the main checkout, on `main`):

```powershell
git status --short                       # expect only: ?? frontend/public/
git fetch origin                          # confirm origin/main is still a6e27a78
git merge --ff-only <chosen branch>
backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py --verify   # from backend/, PYTHONIOENCODING=utf-8
git push origin main                      # only with your explicit permission
```

After each fast-forward, rerun T3 on `main` in a clean detached worktree and record it.

**Keep:**
- `docs/real-model-e2e-readiness`;
- `feat/real-model-pilot-tooling`, which holds an unpushed evidence commit;
- `research/compact-geometry-dsl`, the DSL spike (HOLD). It is not for `main`.

## GO / NO-GO

- **Fast-forward of B** (offline, research route): see the report §6 once T3 and the candidate are recorded.
- **Hybrid in the product, or a live pilot: NO-GO.**
  - `ISSUE-ARCH-HYBRID-QUESTION-LOCAL-GIVENS` is open.
  - There is no measurement with a real model.
  - The DSL stays HOLD.
