# Hybrid V2 planner generalization: prism planes through a point perpendicular to a line

Run `hybrid-v2-planner-generalization`, 2026-10-27. Branch `research/hybrid-v2-planner-generalization` from `main`
`386d214952e6a7ba98f0931b5ecfd7a5b89d1667`. Codex started the run and was interrupted after the baseline audit; Claude
continued it in the same worktree and run folder (`takeover-checkpoint.md`). Owner decisions taken during the run are
quoted in §4. Not merged, not pushed, 0 live provider calls.

## 1. Outcome

| | before (`results/baseline.json`, 386d2149) | after (`results/after.json`, de7b2813) |
|---|---|---|
| positives served with exact oracle agreement | 0/10 | **10/10** |
| negatives refused | 8/8 (5 with the wrong reason) | **8/8, all with the registered reason** |
| wrongly served | 0 | **0** |
| false refusals | 10 | 0 |

Same registered inputs (`inputs/development.json`, LF sha256 `0e638742…`) and oracle (`inputs/oracle.json`, `572f3ff0…`)
in both columns. Classification `AUTHORED_DEVELOPMENT_NOT_HOLDOUT`: the corpus was written by the agent that also
studied the code, so this shows the slice works on its registered development cases, not that it generalises.

Versions: planner `/15 → /16`, registry `/14 → /15`, engine `/14` and bridge V2 unchanged. CACHE_VERSION 130 (NO_BUMP),
`DEFAULT_MODE = LLM_ONLY`, Hybrid opt-in only.

## 2. Baseline RED (inherited, re-verified)

Codex registered 18 cases before any product change: 10 positives (right/oblique triangular prism, cuboid, cube;
base-, top-, lateral- and diagonal lines; renamed labels, reversed endpoints and fact order; a symbolic unit) and 8
negatives (missing dimension, conflicting length, constructed or unmentioned line endpoint, wrong source line, plane
instead of line, plane on a face, plane touching only a vertex). The oracle (`tools/oracle.py`) clips the prism's edges
with an authored Euclidean realisation in `Fraction` arithmetic; it imports nothing from the product.

Claude re-ran the slice test on the unchanged product: all 10 positives refused at the Planner with
`UNSUPPORTED_CAPABILITY` ("bản này chỉ chọn điểm neo trên khối chóp"); the 10 volume controls with the same facts served;
3 negatives refused with their registered code, 5 at the same Planner guard, before their intended stage.
`results/baseline.json` hashes (planner, inputs, oracle) reproduce from the checkout.

## 3. Root causes and changes

1. **PLANNER_COMPOSITION_GAP** — `planner._mat_vuong_duong` refused every non-pyramid. The plane through M ⊥ d is built
   from two anchors Z₁, Z₂ (foot of Zᵢ on d, then M + Fᵢ→Zᵢ); they only need d ∪ {Z₁, Z₂} to span space. Planner /16
   reads the solid as two layers — base/apex for a pyramid, base/top for a prism. With d inside one layer: a vertex of
   that layer off d plus a vertex of the other layer; otherwise two base vertices off d. For pyramids this is exactly
   the old choice. The Planner still computes no coordinates; the Engine re-checks Gram orthogonality, independence, the
   kernel's `plane_through_point_perpendicular_to` and the boundary-face rule. Section and area goals share one derived
   plane (2 projections, 2 translations, 1 section, 1 area call per plan; 4 reused auxiliary constructions).
2. **SOURCE_GROUNDING_GAP (grammar coverage)** — with (1) alone, 2/10 served (cube, cuboid) and the 8 triangular-prism
   cases refused at the Source Gate: their section phrase is "thiết diện của **lăng trụ đứng** ABC.A'B'C' với (P)", and
   `_KHOI_NGU` / `_khoi_cum` required "hình" or "khối" before the solid word. Registry /15 adds `_TU_KHOI`, which also
   accepts bare "chóp" / "lăng trụ" / "tứ diện" — the same closed set `_MO_KHOI_DUNG` already accepted.
3. **SOURCE_GROUNDING fail-open (pre-existing)** — found while attacking (2). When a section goal and an area goal share
   one derived plane, their quotes are merged, and `_khoi_trong_quote` accepts a solid symbol from *any* of them. On a
   pristine export of 386d2149 the pyramid fixture served "Tính diện tích thiết diện của hình chóp **T.XYZ** với (P)"
   and "… của hình **lăng trụ** ABC.A'B'C' …". Registry /15 adds `_cum_goi_khoi`: every section reference the Gate binds
   to the derived plane must name the cut solid (a written symbol is that solid; without one, a kind word is its kind,
   the `_khoi_khop` rule). This only narrows acceptance.

Product commit `de7b2813`: `planner.py`, `registry.py`; harness: version pins in four tests, the declared identity delta
in `export_hybrid_preview_fixtures.py`, `test_prism_perpendicular_section_planning.py`, `CODE_INDEX.md`.

## 4. Owner decisions in this run

- Close the 8 grammar refusals by widening the Source Gate grammar (rather than revising the corpus or stopping at 2/10).
- Record the /4 consumer-wrapper refusal (§6) as a separate gap; pin it.
- Harden the Gate against the fail-open in §3.3 in this wave.

## 5. Verification

| check | result |
|---|---|
| slice test `test_prism_perpendicular_section_planning.py` | 47 passed (positives vs oracle, producer reuse/ordering, negatives with reason, V2 route, reversed operands/fact order, bare/wrong solid words, wrong solid on a shared plane for prism and pyramid, pyramid ⊥ regression, cycle/dangling authority) |
| red before the fix | the 9 solid-binding cases failed before `_cum_goi_khoi` was wired in; the 10 positives failed at baseline |
| committed Hybrid preview fixtures | regenerate identically apart from the declared identity delta (no served behaviour change) |
| T0 `npm run test:impact -- --base main` | IMPACT_GATE_PASS (backend 12275 passed, 0 failed; vitest 3) |
| T1 `test:domain:geometry` / `semantic` | 44 files / 872 tests; 1 / 24 — PASS |
| T2 `test:wave` | 83 files / 1417 tests — PASS |
| candidate freeze | `23669d09`, 118 files, tree hash `316f66cc…`; divergence declared `ca0bb5f2` |
| Full T3 on clean detached `ca0bb5f2` | see §5a |

### 5a. Full T3

`FULL_PRODUCT_GATE_PASS` on the clean detached checkout of `ca0bb5f2` (git tree `6f29d76f…`, product `de7b2813`),
2026-10-27 05:06–05:16 UTC, run by the committed `hybrid-v2-after-main-integration/tools/run_t3.py`
(`ALLOW_LIVE_AI=0`, `HYBRID_V2_LOCAL` unset):

- pytest 12275 passed, 1 skipped, 2 deselected, 15 xfailed; vitest 83 files / 1417 tests; build PASS;
  demo replay 5 PASS + the expected `n4` GROUNDING refusal; demo crash surface 6/6 refusals of the right kind.
- Working tree empty before and after, HEAD and tree unchanged, post-T3 `freeze_evaluation_candidate.py --verify`
  MATCH (118 files, `316f66cc…`), freeze file sha256 `0a31eae0…` before = after.
- `full-t3/receipt.json` with `stdout.log` (sha256 `28be73dd…`, 1615959 bytes) and `stderr.log` (`aa9b7207…`, 342 bytes).
  The copies were verified against the receipt before commit; Git may normalise line endings in the stored blobs.

## 6. Known gaps (not closed here)

- **ADAPTER_INTEGRATION_GAP (pre-existing).** The V2 route serves all 10 canonical payloads, but the `/4` consumer
  wrapper `build_adapter4_response` refuses them fail-closed (`PREVIEW_RESULT_INVALID`): `/4` requires a `DINH_CAT_CANH`
  vertex certificate for every section, and a plane-only derived section (no stated cuts, no declared boundary, no
  derived solid) has none. The pyramid plane-only case behaves identically at 386d2149; the existing test
  `test_v2_plane_only_section_area_without_derived_solid_is_served` checks the route only. Pinned in the slice test.
- Bare kind words are checked coarsely (pyramid-like vs prism-like), as `_khoi_khop` already did: "hình lập phương"
  without a symbol is accepted for a triangular prism.
- `evaluate.py` reports `dependency_depth = 1` for every plan: it calls `lap_ke_hoach` directly, which does not run
  `_bind_result_dependencies`, so the metric is NOT_INFORMATIVE. Ordering is tested in the slice test instead.
- Not measured: `INDEPENDENT_HOLDOUT_NOT_EXECUTED`, `LIVE_NL_E2E_NOT_MEASURED`, no browser evidence for this slice, no
  independent code review.

## 7. Artifacts

`takeover-checkpoint.md` · `plan.md` · `capability-gap-matrix.md` · `inputs/` · `tools/` · `results/baseline.json` ·
`results/after.json` · `verification/` · `candidate_divergence.json` · `full-t3/` · `run.json` · `handoff.md`.
