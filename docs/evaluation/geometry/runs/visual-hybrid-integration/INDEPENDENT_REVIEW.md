# Integrated review: INTERNAL, not independent

**Classification: INTERNAL REVIEW.** The reviewer was a fresh Claude subagent started by the same session that did the takeover. It had no conversation context, only the prompt, and it was read-only: git, grep and file reads, no edits, no tests. Because it is the same model family directed by the author, it is **not** an independent review in the repository's sense.

Codex's earlier *second independent review* (PASS_WITH_LIMITS, SECOND_INDEPENDENT_REVIEW.md) covers only the Visual product `852f6501`, not this integration.

## Scope

1. The merge `78e88470` against both parents. Merge base `43247c9e`; nine paths changed on both sides.
2. The label fix `a9d05dda`.
3. The harness commit `1fcbe7e5`.
4. The freeze `aec7b183`.
5. The join layer in `b99afd32`.
6. Default-route safety.
7. Commit trailers.

## Verdict: PASS_WITH_FINDINGS. 0 BLOCKER, 0 MAJOR, 2 MINOR

### Clean

**Merge correctness.** `git diff-tree --cc 78e88470` lists exactly the nine overlapping paths.
- `adapter3_simulation.py`: each side's diff against the merge equals the other side's own diff (70 vs 61+9; 73 vs 70+3), so no hunk was dropped or duplicated. Hunks:
  - from B1/B2: Source Gate, closure certificate, internal-error boundary;
  - from Visual: curved-route naming, `_clean_curved_text`.
- `scene3d-subentities.ts` keeps both `diemTaiDinhThietDien` and B1/B2's `_diemCuaDinh` wiring.
- No leftover expectations of renamed strings.
- Docs hunks are unions of both sides.

**Label authority.** After `a9d05dda`, `kyHieu` only trims, and an empty notation becomes null. The only notation-touching code left in non-test `frontend/src` is `chuanTen` (`hybrid-preview-adapter.ts:108`). Its only use (line 126) is a comparison inside the validator, and it changes no display.

**Default route.** No change, from the merge base to `b99afd32`:
- `CACHE_VERSION = "127"` at base, both parents and HEAD;
- `app/ai/skills`, `main.py`, `pipeline.py`, `routing.py`, `api` are unchanged;
- `CHE_DO_MAC_DINH = "LLM_ONLY"`;
- no default-route import of `adapter3_simulation`, `adapter4_route` or `hybrid_offline`.

**Join layer.**
- It matches the freeze manifest (`d22d27e7…`, `a9d05dda`).
- `run_candidate_hash` equals IDENTITY_LOCK.
- demo6b has exactly two successors, and the join `corrects` both.
- Nothing corrects the join, so it is terminal.
- No measured path changed after the freeze.

**Harness.** The new `catch` in `runServed` returns `pass: false` with a failing `run_completed`. The suite combines results with `every(item.pass)`, so an aborted run counts as FAIL. Thresholds are untouched.

**Trailers.** `Co-Authored-By` count is 0 in all five commits.

### Findings and disposition

| # | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | MINOR | The integration wave was not written back (EVIDENCE_INDEX, CURRENT_STATE, AI_CONTEXT_BUNDLE, `run.json`); the integration report and `verification/` were still uncommitted | **Fixed in the reports commit:** `VISUAL_HYBRID_INTEGRATION` entry in EVIDENCE_INDEX (with `CORRECTED_BY` on both parent waves); banner lines in CURRENT_STATE, STATUS_LEDGER, AI_CONTEXT_BUNDLE; `run.json`; all reports and receipts committed |
| F2 | MINOR, inherited | `SimulationWorkspace.tsx:352` shows `reason_code ?? error_code` inside a `<details>` "Chi tiết chẩn đoán" drawer. The Visual-side test strips `<details>` before asserting the code is absent. CLAUDE.md §3 says the UI must not expose technical identifiers | **Not changed: owner decision.** It comes from `7ce563b3` (2026-10-22), in the Visual parent's ancestry and not in `main`. The root checkout's uncommitted owner work also edits `SimulationWorkspace.tsx` and that test. Options: accept a collapsed diagnostics drawer, or remove it and restore the strict test |

### Not checked by the reviewer

- It ran no tests. Claude's Full T3 PASS and browser runs cover this; see REGRESSION_RESULTS.md and BROWSER_ACCEPTANCE.md.
- It did not recompute the measured hash. Claude's `--verify` after T3 matched.
- It did not inspect browser bytes.
- It did not judge whether each parent's own changes are correct, e.g. Visual's `D(pyr2)` → `D1` naming.

An independent review (a different reviewer, not directed by this session) is still open for the owner if wanted.
