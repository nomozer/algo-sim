# Report — `segment-witness-cache-invalidation`

Corrects run `hybrid-architecture-wave1-exact-certificates-planner` (branch
`research/hybrid-architecture-wave1-exact-certificates-planner`, base `main` = `origin/main` = `f0560449`). Owner
authorization `GO_WAVE1_CACHE127_FIX_AND_FINALIZATION`; owner decision: `CACHE_VERSION = 127`. 0 model calls.

## 1. Defects

1. **Stale cache (pre-main verification).** Wave 1A makes the default `LLM_ONLY` route emit
   `segment3.perpendicular_witness` on served scenes, and Scene3D draws the right-angle marker from it. `/api/analyze`
   returns a cache hit's `envelope_json` without rebuilding the scene. Wave 1 kept `CACHE_VERSION = 126` ("no bump
   required", no evidence) while `main` is also at 126, so every row already cached for such a problem kept serving the
   scene without the marker. Precedent 95/97/103/104/112–116: a change of served envelope content requires a bump.
2. **False provenance label (found by this run's probe).** Path A labelled every `CONSTRUCT_HEIGHT` witness
   `rule = regular_pyramid_altitude_to_base_center`, `status = DERIVED`, including a given `SA ⟂ (ABC)` on a non-regular
   base whose foot is not the base centre.
3. **Dead prism branch (independent review IMPORTANT-1).** `_gan_chung_chi_vuong_goc_doan` detected prisms by
   `solid_family`, a field no scene carries (`formation` sets `shape_class`), so since `fd310cd9` right prisms, cuboids
   and cubes never received the lateral-edge witness that Wave 1 and the first cache rationale (`2635cbd6`) claimed.

## 2. Evidence (`cache/`)

`cache/cache_probe.py` (v2; v1 kept unchanged in `../hybrid-architecture-wave1-exact-certificates-planner/cache/`)
drives the real `POST /api/analyze` of a tree (domain gate, cache lookup, `run_pipeline`, cache write) with only the two
LLM stages replaced by a fixed contract + program; temp SQLite, outbound sockets refused.

| case | v126 row (`main` f0560449) | final (127) | rest of envelope |
|---|---|---|---|
| `S1_side_height_volume` / `S6_renamed_vertices` / `S7_named_centre` | 0 segment witnesses | S→O, `formation_construct_height` | identical |
| `SA_given_right_triangle_pyramid` / `SA_given_rectangular_pyramid` | 0 | S→A only; oblique lateral edges none | identical |
| `right_triangular_prism` (ABC.DEF) | 0 | D→A, E→B, F→C, `prism_lateral_altitude` | identical |
| `cuboid` / `cube` / `square_prism` | 0 | A′→A, B′→B, C′→C, D′→D; base/top edges none | identical |
| `REFUSED_oblique_prism` | refused, not cached | refused, not cached | — |

"Identical" = the envelope with `segment3.perpendicular_witness` removed equals the genuine v126 envelope (answers,
provenance, formation steps, labels). Request 2 is an `exact_cache` hit equal to request 1 in every case. Files:
`legacy-v126-rows.json`, `cache-probe-main.json`, `cache-probe-new.json`, `decision.json` (supersedes the first decision
of this run in the Wave 1 run's `cache/`, whose prism claim was false at `2635cbd6`).

## 3. Changes

- `2635cbd6` — `backend/app/main.py`: `CACHE_VERSION` 126 → 127 with the reason; pinned assertions (`test_api.py` and
  six identity tests), `backend/cache_identity.lock.json` (semantic environment hash `b1714b56…` unchanged — model
  surface unchanged) and the `CURRENT_STATE` identity table follow. Path A witness labels state only what is checked —
  formation role + exact Gram orthogonality: `formation_construct_height` / `prism_lateral_altitude`, always
  `ENGINE_VERIFIED`. The rule names are borrowed from `certificates._infer_segment_provenance`; route D pairs
  `formation_construct_height` with `GIVEN`, Path A deliberately does not.
- `008918cb` — prism detection reads `shape_class` (`PRISM_LIKE`), the field route D also reads. The LLM_ONLY
  pre-wiring parity test (`test_hybrid_preview_api.py`, prism P01) keeps its historical digest `e6695fe6…` (6592306d) and
  compares it with the new witnesses removed — equal — while asserting the three witnesses AD, BE, CF.
- `backend/tests/test_cache_segment_witness_invalidation.py` (16 tests): for 9 served problems the genuine v126 row
  misses under 127; the re-analysis stores one v127 row (no duplicate) carrying EXACTLY the hand-written expected
  witnesses (from the problem statements, not the output), each verified by `verify_perpendicular_witness`; the second
  request is an `exact_cache` hit with 0 stage calls and the same envelope; the envelope minus the witness equals the
  v126 envelope; the refusal stays uncached; another route identity (`127:<fp>`) never shares the default row; Hybrid
  preview never uses the product cache; an oblique height / prism lateral edge never gets a marker (fault injected both
  ways); a pyramid lateral edge never qualifies.

RED → GREEN: stage 1 (Wave 1 code at 126) — each genuine v126 row is a valid hit (5 failed); stage 2 (after the bump) —
provenance `('regular_pyramid_…', 'DERIVED')` (4 failed); stage 3 (after review) — 4 prism problems get 0 witnesses and
the prism unit fault injection fails (5 failed); GREEN 16/16.

## 4. Scope and limits

Wave 1A certificate scope (exact `Fraction` Gram line–plane certificates, deductive certificate, tamper verifier, Path A
segment witness, `point3` guard) and Wave 1B planner scope (dependency-aware tiered ordering, fail-closed
`DANGLING_DEPENDENCY` / `UNKNOWN_DERIVED_REFERENCE` / `UNKNOWN_SOLID` / `DEPENDENCY_CYCLE` / `UNDERDETERMINED_POINT`)
are those of the corrected run's report; the planner is untouched here. Limits: on Path A only a pyramid's
`CONSTRUCT_HEIGHT` segment or a `PRISM_LIKE` height / lateral edge, against the `CONSTRUCT_BASE` polygon, can carry a
marker — other perpendicularities (face ⟂ face, a line ⟂ a non-base face, an altitude without the formation role) get
none; the offline UI samples (`frontend/src/data/geometry-samples.json`, last built 2026-10-02, no drift lock) were not
rebuilt and show no segment marker; Adapter `/2` still lacks exact relation operands (HFOI-F4); route D stays unwired;
`ISSUE-OPS-CACHE-HISTORICAL-MODE-UNKNOWN` unchanged.

## 5. Verification

Candidate freeze, authoritative T3 and the independent review (incl. cache invalidation) are recorded in
[`handoff.md`](handoff.md). The first candidate `f8ac1ec7` (product `2635cbd6`) passed T3
(`verification/superseded-t3-f8ac1ec7.json`) but is superseded by the review fix.
