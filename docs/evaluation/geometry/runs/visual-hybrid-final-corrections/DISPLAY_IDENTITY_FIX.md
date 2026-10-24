# Backend display identity fix (P2)

Product commit `af670aa6`. Backend only, apart from the regenerated offline samples. The frontend still prints backend notation verbatim (`a9d05dda`), with no case-specific renaming.

## What changed

| Rule | Where | Before | After |
|---|---|---|---|
| Section vertex cycle | `display_names.ten_hien_thi` step ⑧ | `"".join(ky_hieu_toan(s) or s …)`: a vertex with no math symbol leaked its IR id (`MNgiao_canh_sb`); a vertex whose id is not its shown name spelled the id (`MNtrung_diem_sc`) | Built only from the notation each vertex itself shows (`ky_hieu[s]` after resolving it). If any vertex has none, there is no cycle, and the section is named by its construction sentence |
| Declared plane name, default route | `display_names._ten_mp_khai`, `source_entities.ten_mat_phang_nguon`, `simulation_state.build_scene(source_text=…)` | `prefer_declared_plane_names` off on LLM_ONLY, so a plane the problem calls `(P)` showed a name composed from points: `(HUW)`, `(AB′D′)` | A declared one-letter plane label (`(P)`, `(Q′)`, `(α)`) wins **only** when (1) the problem text (`RequestContract.problem_text`) writes that name in parentheses and (2) exactly one plane in the scene declares it (owner rule "grounded + unique", 2026-10-24). Otherwise the composed name stays |

Function-route / Adapter /4 keep their existing flag (`prefer_declared_plane_names=True` where they set it). Their contract carries no problem text (`hop_dong_to_po_da_khai`: topology only), so the new rule cannot fire there.

## Tests (`backend/tests/geometry/test_display_identity_source_names.py`)

**RED first:** 7 failures on the old code (`verification/red-green/p2-red.txt`). After the fix 14 pass.
- **Section:**
  - no id fallback for an unnamed vertex;
  - the cycle uses each vertex's shown notation;
  - negative control: an all-named cycle keeps `MNP`.
- **Plane:**
  - grounded name wins;
  - Greek and primed names match exactly.
- **Plane negative controls, which keep the composed name:**
  - no contract;
  - empty source;
  - the problem never names the plane;
  - only a **point** named P;
  - `(P')` written while `(P)` is declared;
  - two planes declaring the same name.
- **Geometry unchanged:** every non-name field of the plane object is identical with and without the rule.
- **Adapter /4:**
  - over the locked B1/B2 corpus (22 served), no notation spells a point that has no notation;
  - the check is not vacuous: 9 served scenes have unnamed points (`verification/red-green/p2-adapter4-faultcheck.txt`);
  - fault injection: the same check flags `MI1I2I3`, `S(MI1I2I3)`, `V(S.MI1I2I3)` on the Adapter /3 demo.
- **Adapter /4 export:** re-export of the locked corpus is byte-identical to the integrated export (`fixtures.json` sha256 `1abad7c5…`: 47 cases, 22 served, 25 refused, 0 wrong-served, 0 false-refused).
- **Adapter /3:** no product module imports it (lock test). See the residual below.

## Provenance, geometry, order

Only name fields change. Two pieces of evidence:
- **Cache probe:** cube case with plane `(P)` through A, B′, D′. The fresh v128 envelope equals the genuine v127 envelope with `(AB′D′)` replaced by `(P)`, byte for byte. Ids, coordinates, dependency DAG, provenance, construction order, answers and certificates are all identical (`backend/tests/test_cache_display_identity_invalidation.py`).
- **Seven served controls** are byte-identical.

## Offline samples (`frontend/src/data/geometry-samples.json`)

Regenerating them exposed an inherited problem:
- **The committed file was stale.** It was last regenerated 2026-10-02 and differed by about 5,100 lines from what the code builds.
- **A hidden-answer gap appeared.** Samples carried no contract, so the backend treated only the **last** measurement as the final result. Built fresh, `the-tich-chop` (asks for V and d) would have shown V in Mode A.

Owner decision (2026-10-24): `build_geometry_samples.py` now passes each sample a `RequestContract` with its problem text and the obligations the problem asks for (`DE_HOI`, written by hand from each problem's text), as the product route does. The final-result set of every sample now matches its question (`verification/samples-final-results.txt`). `cau-cat-mat-phang` shows `(P)`.

A Vitest assertion in `hybrid-preview-contract.test.tsx` checked `narrationAt` of **every event** for the final value. That held only because the stale sample's events were untyped, so each event became its own step. It now checks what the learner reads: each construction step's label and narration contain no final value, and no `FINAL_RESULT` event opens a step.

## Residual (not fixed, reported)

**Adapter /3** (`adapter3_simulation.py`) still spells `MI1I2I3` and similar ids in:
- section, quantity and segment roles;
- point-event explanations (`Dựng điểm I1 = …`, `SI1`).

It does so through intersection points it itself declares unnamed. It has no product consumer: the frontend accepts only `hybrid-route-d-simulation/4`, and no product module imports it, which a test locks. Scrubbing every field of a dead research builder is outside this task. Fix it there if `/3` is ever revived.
