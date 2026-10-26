# Next agent handoff — hybrid-v2-nl-certificates-e2e

Branch `research/hybrid-v2-nl-certificates-e2e`, worktree `.superpowers/worktrees/hybrid-v2-nl-cert` (from `main` `dd557f8f`). Report:
[`report.md`](report.md). Status: **`MERGE_READY_PENDING_OWNER_GO`** — nothing merged or pushed; `main` is untouched.

## Identities

Product `059daadc` (earlier product commits `4eae907d`, `30530cf8`), freeze `28a6a348` (118 files, `fef0b050…`), divergence declared
`34ecce49`, Full T3 on the clean detached checkout of `34ecce49` — see `report.md` §7 and `full-t3/receipt.json`. Registry `/14`, planner
`/15`, engine `/14`, bridge `/2`, `CACHE_VERSION` 130, `DEFAULT_MODE LLM_ONLY`, Hybrid opt-in, live calls 0.

## What is open (in priority order)

1. **Independent holdout** — author it with `protocol/HOLDOUT_AUTHORING_BRIEF.md` (no repository access), register
   `{dataset_sha256, registered_before_tuning: true}` **before** any tuning, then run `backend/scripts/run_nl_eval_offline.py`
   (GOLD/STRESS arms; REPLAY with a recorded extractor). Until then every statement about extraction quality is `NOT_MEASURED`.
2. **Live NL pilot** — needs its own protocol, the registered holdout and a separate Owner GO (`LIVE_PROVIDER_GO_REQUIRED`;
   packet in `protocol/NL_EVAL_PROTOCOL.md` §7). The runner has no transport by design.
3. **Source Gate wording gaps NL-2…NL-5** (`audit/NL_GAP_MATRIX.md`), pinned by `test_known_wording_gaps_stay_visible`; closing one
   changes that list on purpose and needs fresh held-out data (the clause grammar was rewritten after several review rounds
   because wider reading produced false serves).
4. **Line–plane distance** has no drawn foot segment (the witness annotation exists for point–plane only); plane operands named by
   the word `đáy` with labels (`mặt phẳng đáy (ABCD)`) are refused.
5. Missing `/4` sections and circumscribed-sphere capabilities (roadmap) — not started.

## Do not

Merge or push this branch without an explicit Owner GO for that task; enable Hybrid by default; treat the DEV_AUTHORED data
as independent; edit locked oracles; reuse the 44 locked items of `independent-nlu-extraction-evaluation` as held-out.

## Continue after a limit

```bash
git -C .superpowers/worktrees/hybrid-v2-nl-cert status --short            # expect empty
git -C .superpowers/worktrees/hybrid-v2-nl-cert log --oneline -12
# targeted checks (venv lives in the root checkout; run from the worktree's backend/)
cd .superpowers/worktrees/hybrid-v2-nl-cert/backend && PYTHONIOENCODING=utf-8 \
  ../../../../backend/.venv/Scripts/python.exe -m pytest tests/geometry/test_nl_eval_scoring.py \
  tests/geometry/test_typed_fact_next_v2_line_plane_distance.py tests/geometry/test_point_line_distance_presentation.py \
  tests/geometry/test_base_side_wording_variants.py -q
# integration, only after an Owner GO for this task: ff-only from a clean main worktree, then freeze --verify
git -C <clean main worktree> merge --ff-only research/hybrid-v2-nl-certificates-e2e
cd <clean main worktree>/backend && PYTHONIOENCODING=utf-8 ../../../../backend/.venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
```

Browser corpora: `tools/make_point_line_corpus.py`, `tools/make_line_plane_corpus.py` (run from `backend/` with `PYTHONPATH=.`), servers on
`:8891` (uvicorn with `HYBRID_V2_LOCAL=offline-replay` and `HYBRID_V2_LOCAL_REPLAY_CORPUS`) and `:3391` (`tools/vite.e2e.config.ts`);
harness `frontend/scripts/b3-distance-browser-e2e.mjs --analyze`. Both dev servers were stopped at the end of the run. The
`frontend/node_modules` of the two worktrees is a junction to the root checkout's (`rmdir` the link before removing a worktree).
