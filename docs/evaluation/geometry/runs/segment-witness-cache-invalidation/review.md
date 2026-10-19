# Independent Review — `segment-witness-cache-invalidation`

- **Reviewer:** independent read-only subagent `a54ef7cce8afe99ff` (fresh context; no edits, no commits, temp databases
  only, 0 provider requests). Dimensions: cache invalidation, provenance, unintended change, governance/evidence.

## Round 1 — at candidate `f8ac1ec7` (product `2635cbd6`): `INDEPENDENT_REVIEW_FAIL`

| id | severity | finding | resolution |
|---|---|---|---|
| IMPORTANT-1 | IMPORTANT | `quantity_annotations.py` detected prisms by `solid_family`, which no scene carries (`formation` sets `shape_class`): the prism branch was dead since `fd310cd9`, so right-prism / cuboid / cube lateral edges never got a witness, contradicting `main.py`, `CURRENT_STATE`, the first `decision.json` and `report.md` | product `008918cb` reads `shape_class`; regression extended to 9 served problems incl. the prism family; RED stage 3 (5 failed) → GREEN 16/16 |
| NONBLOCKING-1 | NONBLOCKING | "route D vocabulary" only half true (route D pairs `formation_construct_height` with `GIVEN`) | comment / report / decision state the deliberate `ENGINE_VERIFIED` pairing |
| NONBLOCKING-2 | NONBLOCKING | probe docstring named a non-existent test | fixed in probe v2 |
| NONBLOCKING-3 | NONBLOCKING | correction evidence filed in the corrected run's folder | v2 evidence in this run's `cache/`; first decision kept as written, marked superseded |
| NONBLOCKING-4 | NONBLOCKING | receipts pending; T3 log carries no SHA | receipts committed at finalization; `verification/t3-head.txt` records the gate's HEAD |

Verified correct in round 1: `CACHE_VERSION` 127 consistent on every read/write path (`_cache_key`, `_policy_identity`,
`_cache_lookup`, cache write, `cache_clear.py`, runtime identity, image extraction); no 126 pin left; legacy rows
reproduced byte-identically from `main`; with `CACHE_VERSION` monkeypatched, 126 ⇒ 4/4 hits, 127 ⇒ 4/4 misses;
cross-identity and Hybrid preview isolation; pyramid provenance truthful; fail-closed intact; T3 log matches receipt.

## Round 2 — at candidate `1117cfd4` (product `008918cb`): `INDEPENDENT_REVIEW_PASS` (0 blockers, 0 important)

- Prism witnesses: every lateral edge of the triangular prism, cuboid, cube and square prism (`prism_lateral_altitude`,
  `ENGINE_VERIFIED`), each passing `verify_perpendicular_witness`; 13 servable regular-prism cases in affine charts ⇒
  120/120 witnesses verify under `chart_metric`; oblique prisms (control + OP01–06 served, ON01–10 refused) ⇒ 0
  witnesses; pyramids only the altitude.
- Cache: v2 probe on `main` reproduces `legacy-v126-rows.json` and `cache-probe-main.json` byte-identically; on the
  worktree, `cache-probe-new.json`; monkeypatched 126 ⇒ 9/9 hits, 127 ⇒ 9/9 misses; strip-equality 9/9.
- Byte-parity oracle (`test_hybrid_preview_api.py`): intent preserved — unchanged historical digest over the full
  response minus only `segment3.perpendicular_witness`, witness set asserted exactly; witness payload covered by the
  cache test on the same P01 contract.
- Governance: freeze `--verify` MATCH (112 files, `8cb9857f…`); `EVALUATION_CANDIDATE.json`, `candidate_divergence.json`
  and `run.json` agree; T3 receipt matches its log (sha256 `e2fcbcee…`, 252 lines, 10986/0, 70/1146, 5/5 + 1/1, 6/6)
  and `t3-head.txt` = `1117cfd4…`; Wave 1 historical receipts unchanged since `14cc4eb4`; 0 `Co-Authored-By` in 16
  commits since `f0560449`.
- Checks: 668 pytest (19 files) passed; 35 vitest files / 778 tests passed (geometry domain + hybrid preview contract;
  per-object `perp_marker` through the chart transform renders several markers per scene).

Remaining NONBLOCKING:

- **NB-A** — `quantity_annotations.py:100,109-110`: in a composite scene with both a `PRISM_LIKE` solid and a pyramid
  `CONSTRUCT_HEIGHT` segment, that segment would be labelled `prism_lateral_altitude`; status stays truthful
  (`ENGINE_VERIFIED`); 0 such scenes in `frontend/src/data` and `docs/evaluation`. Recorded as a limit.
- **NB-B** — receipts pending at review time (committed at finalization).
- **NB-C** — offline samples `geometry-samples.json` carry no witness (disclosed, not served by `/api/analyze`).
