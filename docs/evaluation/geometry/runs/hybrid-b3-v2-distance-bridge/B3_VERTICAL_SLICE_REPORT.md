# B3 vertical slice — canonical V2 distance goals reach the existing planner

Authorization `GO_CLAUDE_CONTINUE_CODEX_VISUAL_HYBRID_B3_LOCAL_ONLY`, 2026-10-25. Branch
`research/hybrid-b3-v2-distance-bridge` from the certified visual closure commit `de49c592`.
Evidence class: **offline authored development cases** — not a holdout, not an extraction-quality measurement, no
provider call.

This supersedes the "specified, implementation deferred" status of Codex's
[`visual-closure-hybrid-readiness/B3_VERTICAL_SLICE_REPORT.md`](../visual-closure-hybrid-readiness/B3_VERTICAL_SLICE_REPORT.md)
for the slice it selected (distance from a described point of a prism to a plane). That report stays unchanged.

## What was missing

The `/4` route (`adapter4_route.run_typed_fact_next_v2_route`) translates a `typed-fact-next/2` payload with
`typed_fact_next_bridge.bridge_v2` and then runs the one planner, Source Gate and exact engine. The bridge handled
`measurement` goals only for `volume` and section `area`; every `goal_type: "distance"` was refused with
`BRIDGE_UNSUPPORTED_MEASUREMENT`, although the registry already has `ask_distance_point_plane`,
`ask_distance_lines`, `ask_length` with exact witnesses.

Codex's blocker 3 was that `MathGoalSpec.target` is a free `dict`, so the bridge must not invent key meanings. The
takeover found the meanings are **already fixed in product code**: the `/3` adapter reads exactly
`{point, plane}`, `{segment}`, `{line1, line2}` for distance goals. The slice adopts that contract verbatim; it adds no
new semantics, no new function, no IR change.

## Change (one function, 20 lines)

`typed_fact_next_bridge._distance_question` (only for `/2`; `/1` keeps refusing):

| `/2` target (exact key set) | planner question |
|---|---|
| `{point: ref, plane: [≥3 refs]}` | `quantity: distance, points_a: [point], points_b: plane` |
| `{segment: [2 refs]}` | `quantity: length, points: segment` |
| `{line1: [2 refs], line2: [2 refs]}` | `quantity: distance, points_a: line1, points_b: line2` |
| anything else (missing/extra keys, wrong arity, non-list) | `INVALID_MATH_GOAL` (already in the `/4` refusal taxonomy) |

Refs go through the bridge's existing `_ref` (solid-qualified `pr::A` checked by `_check_qualified_refs`). The bridge
still reads no problem text; the quote is re-checked by Source Gate, which also checks that the quote names the
asked objects (`SOURCE_OBJECT_MISMATCH`).

Harness: `INVALID_MATH_GOAL` classified `malformed` in `tests/geometry/hybrid_compiler_benchmark.py` (taxonomy only;
frozen labels unchanged). No corpus in the repository contains a distance math goal, so no measured number moves.

## Tests — `backend/tests/geometry/test_typed_fact_next_v2_distance_bridge.py` (35)

Closed-form oracles from the stated facts of prism ABC.A'B'C', right angle at A, AB = x, AC = y — no engine coordinates:

| Case | Oracle | Result |
|---|---|---|
| A' to (ABC), right prism, 4 label/size sets (ABC, DEF, KLM 3-4-5, RST) | d² = h² | PASS |
| A to (BCC'B') | x²y²/(x²+y²) | PASS |
| segment B'C | x²+y²+h² | PASS |
| lines AA', BC | x²y²/(x²+y²) | PASS |
| oblique prism, A' projects on midpoint of BC, 2 sizes | d² = l² − (x²+y²)/4 = h², asserted ≠ lateral edge² | PASS |
| plane order reversed + solid-qualified refs | same answer | PASS |
| uniform scale ×2 | d² × 4 | PASS |
| `/4` envelope | SERVED, exact `12`, provenance `ask_distance_point_plane` + verbatim quote; engine witness `ENGINE_VERIFIED` | PASS |
| 10 malformed targets | `INVALID_MATH_GOAL` | PASS |
| unknown qualified vertex | `UNKNOWN_VERTEX_REF` | PASS |
| missing height / missing base angle | `MISSING_DIMENSION` | PASS |
| zero height | `NON_POSITIVE_LENGTH` | PASS |
| contradictory height | `INCONSISTENT_FACTS` | PASS |
| collinear "plane" (AMB), M midpoint of AB | `SOURCE_OBJECT_MISMATCH` | PASS |
| quote not in source | `QUOTE_NOT_IN_SOURCE` | PASS |
| unknown label | `UNKNOWN_LABEL` | PASS |
| sphere | `BRIDGE_UNSUPPORTED_CURVED` (before the mapping) | PASS |
| pure rename, 3 forms | exact planner fact | PASS |
| `/1` bridge | still `BRIDGE_UNSUPPORTED_MEASUREMENT` | PASS |

RED before the change: 21 of 30 initial tests failed with `BRIDGE_UNSUPPORTED_MEASUREMENT` (the 9 that passed were
refusals that were trivially true while everything was refused; they were re-checked after the change with pinned
codes).

Fault injection on the bridge (each reverted, file byte-identical afterwards): swap point/plane → 14 failed; plane
truncated to 2 points → 15 failed; enable for `/1` → 1 failed; segment as point–point distance → 1 failed; accept
extra keys → 1 failed; accept a 3-point segment → 1 failed. The last three were initially undetected and led to the
pure-rename and extra-key tests.

## Candidate and gates

| Item | Value |
|---|---|
| product commit | `3524bec8945c451655e92d77aba3016a9c6065cc` (backend `geometry_functions` only) |
| divergence layer | `inputs/candidate_divergence.json` (`corrects` the visual closure layer) — commit `5e59f7dd` |
| freeze (clean tree) | `dd5e6748` — measured 118 files `7fbe45b24b41acbc73f8aacd6b8bf163e10172fc8b8d2c08ac8006a6d2dbd284` |
| CACHE_VERSION | 128, NO_BUMP: `/api/analyze` (LLM_ONLY), prompts, routing policy unchanged; route D not wired |
| model surface | unchanged (no prompt, schema, grammar card, capability table; surface fingerprints test green) |
| Full T3 | **`FULL_PRODUCT_GATE_PASS` at `dd5e6748`** — pytest 11891 passed / 0 failed, vitest 1354/1354, build, demo, crash surface PASS; tree clean before/after; freeze verify match (`verification/full-t3/receipt.json`; the verify line in the receipt is mojibake from the console code page, exit 0) |

## Effect on the 18-family matrix

Codex's matrix (`visual-closure-hybrid-readiness/HTML_18_FAMILY_CAPABILITY_MATRIX.md`) stays the record. Delta:
the reason "canonical V2 measurement bridge does not expose general distance goals" no longer holds for
point–plane, segment and line–line distance. Measured here only on triangular prisms (#12 right, #13 oblique), where
the `/4` adapter column for distance goals becomes OFFLINE_GEOMETRY_VERIFIED. Pyramids, cuboids and skew-line
families (#1–#6, #11) are expected to benefit through the same planner functions but were **not** tested in this
slice. No overall classification changes: still 0 FULL_E2E, 9 PARTIAL, 7 RENDER_ONLY, 2 UNSUPPORTED.

## What this does not establish

- Not NL quality: payloads are authored; whether an extractor emits these target keys is UNKNOWN.
- Angle goals (`/3` adapter reads `angle` too) remain refused on `/4` — next candidate slice, same method.
- No browser acceptance of a `/4` distance scene was run in this checkpoint; the envelope is checked offline only.
  Whether the Scene3D consumer presents this `/4` distance scene correctly is NOT verified here; a `/4` browser row
  (desktop + mobile) is required before claiming FULL_E2E for any family.
- Curved solids stay refused on the bridge; the sphere/plane P3 issue is unrelated to this slice.
- Independent review: NOT performed.
