# Independent review — solid-scope repair (candidate 55bdd332, product c4d7b759)

Reviewer: separate-context agent, read-only, offline probes only (0 provider calls), reviewed
`git diff 6516d5d4 96cd4c23 -- backend` and the run's new evidence. Verdict: **NOT_READY**.
Claude re-ran findings 1–3 independently on this branch and on main `996f114b`:
`verification/review-solid-scope-repro.txt` (probe source included).

## Clean

- Diff logic of `393864d1` / `c4d7b759` is correct: height/altitude conflict and unknown scope refuse on Bridge,
  Adapter /3 legacy and Adapter /4; unscoped unknown solid name still refuses `UNKNOWN_SOLID` (N006); A3-DEV-02 legacy
  positives (id, notation `D.ABC`, canonical-name aliases) served with exact oracle answers; section-area scope order
  matches Bridge.
- Area-polygon goal with `solid_id='foreign'` and non-derived ratio s2/s1 refuse on both adapters.
- Evidence: T3 receipt candidate `55bdd332`, product `c4d7b759`, `FULL_PRODUCT_GATE_PASS`, post-freeze exit 0, freeze
  hash identical before/after, log hash/bytes match; candidate tree hash `609931…` matches; divergence chain correct;
  run dir has additions only since `6516d5d4`.

## Findings (same defect class: a declared goal/premise `solid_id` unknown or contradicted, yet SERVED)

| # | sev | repro (offline) | this branch | main | location |
|---|---|---|---|---|---|
| 1 | MAJOR | supplementary control + distance (point S, plane ABCD) or angle (SC, ABCD) goal with `solid_id` `s2` / `foreign` | /3 REFUSED; **/4 SERVED** | /4 SERVED; /3 SERVED (angle) | Bridge `_distance_question` / `_angle_question` ignore `g.solid_id`; `_check_qualified_refs` checks existence only |
| 2 | MAJOR | `simulation-coverage-visual-validation` `demo6a-curved-cylinder-sections` with goal (or premise) `solid_id='foreign'` | **/3 SERVED** | **/3 SERVED** | curved payloads go to `_run_curved_route` before the shared gate; it reads only `target.solid`, ignores premise scope |
| 3 | MAJOR (owner semantics) | A3-DEV-02 (also -03, -09, demo1) `volume_ratio` / `residual_volume` goal with `solid_id='foreign'` | **/3 SERVED** | **/3 SERVED** | ratio goals carry numerator/denominator ids; a goal-level `solid_id` has no defined meaning — refuse, or forbid in schema? |
| 4 | MINOR | `coordinate_frame{solid_id:'foreign'}` / `shared_faces{solid_a:'foreign'}` relation | /3 REFUSED; /4 SERVED | — | Bridge `continue`s on these relations; no answer derives from them |
| 5 | MINOR | volume goal whose `solid_id` is a declared derived solid | /4 REFUSED `UNKNOWN_SOLID_ID` (wrong reason; new here) | — | `_pham_vi_khoi` knows primary solids only; latent false refusal for /3 if Bridge reaches the goal loop |
| 6 | MINOR | volume goal `target={'solid_id':'s2'}`, goal scope s1 | SERVED as s1 volume | — | stray `target.solid_id` ignored (section-area goal does read it) |
| 7 | NOTE | `target.solid='S.ABCD'` (notation) with scope s1 | /4 REFUSED capability code, /3 serves | predates | Bridge volume goal accepts ids only |
| 8 | NOTE | `verification/full-t3/full-t3.log` is 0 bytes | — | — | aborted Codex T3; documented in `codex-to-claude-takeover.md` §2 |

Findings 1–3 are pre-existing on main (not regressions of this wave), but they are fail-open provenance paths of
exactly the class Gate A forbids, so Gate A is **FAIL** and the preregistered stop condition
(`codex-to-claude-takeover.md` §7: reviewer finds a new MAJOR) applies. No product change was made after this review.
