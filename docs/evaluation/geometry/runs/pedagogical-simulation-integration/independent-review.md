# Independent adversarial review — run `pedagogical-simulation-integration`

- **Reviewer:** fresh-context `general-purpose` subagent, read-only (no file edits, no git state changes, no live calls;
  targeted tests only; did not run the browser E2E or the full backend suite). Same reviewer for both rounds.
- **Questions:** Master Task §XII — answer seen too early; construction trace revealing the solution; quantity panel;
  inspector; givens lost when hiding results; symbols changed; figure made wrong to hide answers; interaction lost; new
  errors outside the E2E corpus; replay called live.

## Round 1 — `NOT_READY` (0 BLOCKER, 1 MAJOR, 5 MINOR, 3 NIT) — range `5abf8c20..627b7dee`

| ID | Sev. | Finding | Resolution |
|---|---|---|---|
| F1 | MAJOR | «Đề bài» fixed only where the caller passes the text; an envelope assigned to a class is reopened with `loadEnvelope(a.envelope)` and showed the disclaimer again | `928fb880`: `loadEnvelope` stamps the statement on the envelope (`problem_statement`); store round-trip test (red on the previous code) + classroom-gate test |
| F2 | MINOR | E2E leak detector had no positive control and did not search the values Mode B renders or figure-scale values | `6910ef64`, `c62b3aa1`: positive control on the Mode B panel, rendered + `answer_exact.coef` values, distinctive values matched bare, blind values recorded |
| F3 | MINOR | pre-fix audit numbers not reproducible from the repo | `prefix-ui-audit-analyze.mjs` committed (raw DOM dump still not committed — see round 2, R5) |
| F4 | MINOR | E2E overwrote its own receipt | `--out-dir`, refuses an existing receipt |
| F5 | MINOR | living docs and template blobs not written back | `11f5f5f5`: CURRENT_STATE, EVIDENCE_INDEX (C23, C22 `CORRECTED_BY`), STATUS_LEDGER, epic state |
| F6 | MINOR | no test of `perpendicular_line_plane` / `altitude` to a non-vertex foot; SH presented as auxiliary after the solid closes | test `test_stated_perpendicular_to_a_non_vertex_foot_is_drawn_once_in_learner_order`; ordering disclosed (report L5) |
| F7 | NIT | comment named a non-existent helper | `adf4a113` |
| F8 | NIT | source-string tests brittle | regex |
| F9 | NIT | report status lines contradictory | report rewritten |

Verified true in round 1: no `Co-Authored-By`; no `APPROVED_BY_USER`; templates stay `PENDING_OWNER_DECISION`;
`--verify` MATCH; no hardcoded case IDs in product code; engine change emits only `construct_segment` through
`_rang_buoc_vuong()`, prove/negated goals never drawn as givens, exact Gram witness; skipping the `CACHE_VERSION` bump is
correct (Route D cache key contains the engine version); observations rendered only in Mode B, anchor-gated; Mode A shows
no final values; report numbers matched the receipts of that round.

## Round 2 — **`READY`** (0 BLOCKER, 0 MAJOR, 4 MINOR, 2 NIT) — range `627b7dee..11f5f5f5`

| ID | Sev. | Finding | Resolution |
|---|---|---|---|
| R1 | MINOR | positive-control count written as 47/48; the receipt sums to **43/44** (1 blind: `4`) | corrected everywhere (report, CURRENT_STATE, EVIDENCE_INDEX, STATUS_LEDGER, epic state) |
| R2 | MINOR | `history.ts::sanitizeEnvelope` drops `problem_statement`; an assignment reopened later from «Lịch sử» loses «Đề bài»; report over-claimed "history carries it" | report wording corrected; logged with R3 as `ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D` (moot while R3 stands: every geometry envelope is 3D) |
| R3 | MINOR (pre-existing) | the same `sanitizeEnvelope` drops `scene3d`, so a 3D problem reopened from history does not render Scene3D | logged `ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D` (repair needs a storage decision; outside this run) |
| R4 | NIT | EVIDENCE_INDEX cited `independent-review.md` before it existed | this file |
| R5 | NIT | figure-scale values have no positive control (structurally impossible: Mode B shows the symbolic form); raw pre-fix DOM dump not committed; pre-fix rule weaker than the round-2 detector (no bare matching) | stated in report §2 and §10 |
| R6 | NIT | `problem_statement` is free teacher text stored as is (React-escaped; same trust as `title`/`description`/`instruction`); it can disagree with the built figure | stated in report L10 |

Round-1 findings verified fixed: F1 (assignment path), F2, F4–F9; F3 partly (R5). Also verified: `--verify` MATCH
(`39e9f54b…`); templates re-bound to `39e9f54b…`, still `PENDING_OWNER_DECISION`, blobs match `git rev-parse`; history
ids hash `simulation_id + config` only, so the stamped field does not affect dedup; no distinctive answer of the 30 served
cases occurs in its own problem text, so bare matching silently disabled nothing; `full-t3-dbc0316c.json` PASS;
`HYBRID_LIVE_VALIDATED` / `PRODUCTION_CUTOVER_READY` not claimed.
