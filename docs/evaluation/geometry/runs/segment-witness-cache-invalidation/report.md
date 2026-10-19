# Report — `segment-witness-cache-invalidation`

Corrects run `hybrid-architecture-wave1-exact-certificates-planner` (branch
`research/hybrid-architecture-wave1-exact-certificates-planner`, base `main` = `origin/main` = `f0560449`). Owner
authorization `GO_WAVE1_CACHE127_FIX_AND_FINALIZATION`; owner decision: `CACHE_VERSION = 127`. 0 model calls.

## 1. Defect

Wave 1A makes the default `LLM_ONLY` route emit `segment3.perpendicular_witness` on served scenes (altitude `SO` of a
regular pyramid, a given `SA ⟂ (ABC)`, right-prism lateral edges), and Scene3D draws the right-angle marker from it.
`/api/analyze` returns a cache hit's `envelope_json` without rebuilding the scene. Wave 1 kept `CACHE_VERSION = 126` with
"no bump required" and no evidence, while `main` is also at 126 — so every row already cached for such a problem keeps
serving the scene without the marker, i.e. the issue Wave 1 resolves (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING`)
stays visible for those problems. Repository precedent 95/97/103/104/112–116: a change of served envelope content
requires a bump.

## 2. Evidence (`../hybrid-architecture-wave1-exact-certificates-planner/cache/`)

`cache_probe.py` drives the real `POST /api/analyze` of a tree (domain gate, cache lookup, `run_pipeline`, cache write)
with only the two LLM stages replaced by a fixed contract + program; temp SQLite, outbound sockets refused.

| case | v126 row (`main` f0560449) | Wave 1 + 127 | rest of envelope |
|---|---|---|---|
| `S1_side_height_volume` | 0 segment witnesses | `chieu_cao_SO_2` S→O on `day_ABCD` | identical |
| `S6_renamed_vertices` | 0 | `chieu_cao_SO_2` S→O on `day_MNPQ` | identical |
| `S7_named_centre` | 0 | `chieu_cao_SO_2` S→O on `day_ABCD` | identical |
| `SA_given_right_triangle_pyramid` | 0 | `chieu_cao_SA` S→A on `day_ABC`; oblique SB, SC none | identical |
| `REFUSED_oblique_prism` | refused, not cached | refused, not cached | — |

"Identical" = the envelope with `segment3.perpendicular_witness` removed equals the genuine v126 envelope (answers,
provenance, formation steps, labels). Files: `legacy-v126-rows.json` (the genuine rows), `cache-probe-main.json`,
`cache-probe-new.json`, `decision.json`.

## 3. Changes (product `2635cbd6`)

- `backend/app/main.py`: `CACHE_VERSION` 126 → 127 with the reason in the bump history. The pinned assertions
  (`test_api.py` and six identity tests), `backend/cache_identity.lock.json` (semantic environment hash
  `b1714b56…` unchanged — model surface unchanged) and the `CURRENT_STATE` identity table follow.
- `quantity_annotations._gan_chung_chi_vuong_goc_doan`: found by the probe, the Path A witness was labelled
  `rule = regular_pyramid_altitude_to_base_center`, `status = DERIVED` for every `CONSTRUCT_HEIGHT` segment, including a
  given `SA ⟂ (ABC)` on a non-regular base whose foot is not the base centre. It now states only what is checked — the
  formation role and exact Gram orthogonality — in the route D vocabulary (`formation_construct_height` /
  `prism_lateral_altitude`, `ENGINE_VERIFIED`). Geometry, marker vectors and every other byte unchanged.
- `backend/tests/test_cache_segment_witness_invalidation.py` (9 tests): genuine v126 row is a miss under 127; the
  re-analysis stores one v127 row (no duplicate) whose scene carries exactly the expected witness, verified by
  `verify_perpendicular_witness`, with no marker on oblique lateral edges; the second request is an `exact_cache` hit
  with 0 stage calls and the same envelope; the envelope minus the witness equals the v126 envelope; the refusal stays
  uncached; another route identity (`127:<fp>`) never shares the default row; Hybrid preview never uses the product
  cache; an oblique `CONSTRUCT_HEIGHT` segment never gets a marker (fault injected both ways).

RED → GREEN: stage 1 (Wave 1 code at 126) — `_cache_lookup` returns each genuine v126 row as a valid hit (5 failed);
stage 2 (after the bump) — the provenance assertion fails on `('regular_pyramid_…', 'DERIVED')` (4 failed); GREEN 9/9.

## 4. Scope unchanged from Wave 1

Wave 1A certificate scope (exact `Fraction` Gram line–plane certificates, deductive certificate, tamper verifier, Path A
segment witness, `point3` guard) and Wave 1B planner scope (dependency-aware tiered ordering, fail-closed
`DANGLING_DEPENDENCY` / `UNKNOWN_DERIVED_REFERENCE` / `UNKNOWN_SOLID` / `DEPENDENCY_CYCLE` / `UNDERDETERMINED_POINT`)
are those of the corrected run's report. Limits stay: the Path A witness is attached only to segments with a
`CONSTRUCT_HEIGHT` role (or right-prism lateral edges) against the `CONSTRUCT_BASE` polygon; other perpendicularities
(e.g. face ⟂ face, a line ⟂ a non-base face) get no marker on Path A; Adapter `/2` still lacks exact relation operands
(HFOI-F4); route D stays unwired; `ISSUE-OPS-CACHE-HISTORICAL-MODE-UNKNOWN` unchanged.

## 5. Verification

Focused gates, candidate freeze, authoritative T3 and the independent review (incl. cache invalidation) are recorded in
[`handoff.md`](handoff.md).
