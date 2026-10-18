# Frontend findings — handoff from `hybrid-pre-main-hardening`

Read-only audit of the candidate's frontend (`frontend/src` is byte-identical to `main` `4abc4afb`). **Nothing here
was changed**: the Scene3D renderer is owned by the active branch `research/scene3d-plane-grid-camera`, whose
worktree has uncommitted edits to `scene3d-view.tsx`, `scene3d-annotations.ts`, `scene3d-model.ts` and others. Each
finding names the owner, a minimal reproduction and the acceptance check. Reproductions marked *by reading* were
derived from the source, not executed in a browser or test runner.

| # | Finding | Severity | Owner |
|---|---|---|---|
| F1 | Right-angle marker at an "altitude" is chosen by name, not by a backend certificate | correctness of presentation | Scene3D (`scene3d-view.tsx`) |
| F2 | `maTranKhung` has no guard: a non-SPD `chart_metric` silently becomes NaN coordinates | defensive (no current producer) | Scene3D (`scene3d-chart.ts`) |
| F3 | `scene3d.length_unit` (route D) is never shown | presentation, route D only | Scene3D / Hybrid envelope adapter |
| F4 | `proof_status` / `can_present_as_proven` have no place in the envelope | blocker for wiring route D | Hybrid envelope adapter (backend) + UI |

## F1 — altitude right-angle marker without certification

`frontend/src/simulations/domains/geometry/scene3d-view.tsx` (segment rendering, comment "Ký hiệu góc vuông …
tại chân đường cao"):

```ts
const laChieuCao =
  o.id.includes("cao") ||
  (o.label && /chiều cao/i.test(o.label)) ||
  (o.role && /chiều cao/i.test(o.role));
const chan = a.z <= b.z ? a : b;
const k = laChieuCao ? khungGocVuong(chan.toArray(), (chan === a ? b : a).toArray()) : null;
```

- The decision is a **substring of an id/label/role**, so any segment whose id contains `cao` gets a right-angle
  mark whether or not anything is perpendicular there. Nothing checks a backend fact.
- The foot is "the endpoint with the smaller z". After the display rotation (`huongLenHienThi`, tilted bases) or
  for a segment whose foot is above its other end in the chart, this picks the wrong endpoint.
- `khungGocVuong` builds the marker in a plane chosen from the x/y axes (`e1` = x projected ⊥ d), not in a plane the
  backend certified as perpendicular. For a vertical segment that coincides with the base plane; for anything else
  the marker can sit in a plane that has no perpendicularity relation.

The backend already emits a certificate for perpendicular feet: `perpendicular_witness` on points built by
`project_onto` (`backend/app/ai/function_route.py::_gan_nhan_chung_hinh_chieu`, foot checked equal to the
constructed coordinates) and annotation witnesses (`scene3d-annotations.ts` consumes `annotation.witness`).

**Minimal reproduction (by reading):** a scene with a `segment3` `{ id: "cao_do_thi", endpoints: [[0,0,0],[1,1,1]] }`
and no perpendicular relation renders `perp_marker:cao_do_thi`. Equivalently a segment labelled
"chiều cao tương đối" between two arbitrary points.

**Acceptance:** a right-angle mark is drawn only from a backend certificate (a `perpendicular_witness` / annotation
witness whose foot and directions come from the scene), at the certified foot, in the certified plane; a test with
the id `cao_*` and no witness renders no marker; existing altitude scenes keep their marker because they carry the
witness (verify per family before removing the name heuristic).

## F2 — `maTranKhung` on a non-SPD `chart_metric`

`frontend/src/simulations/domains/geometry/scene3d-chart.ts::maTranKhung` takes `Math.sqrt` of
`G00`, `G11 − l10²`, `G22 − l20² − l21²` with no check. For `[[1,0,0],[0,-1,0],[0,0,1]]`, `l11 = sqrt(-1) = NaN`, and
`veKhongGian` then writes `"NaN/1000000000"` into every transformed coordinate (`xau`). A singular metric divides by
zero in `nghichChuyenVi`. The shape is not checked either (a 2×2 throws on `G[2]`).

Since `hybrid-pre-main-hardening` the backend type `geometry.metric.Metric` refuses non-symmetric / non-positive-definite
Gram matrices (exact Sylvester), so no current producer emits one. This is a renderer-boundary guard, not a live bug.

**Acceptance:** `maTranKhung` returns a typed failure (or throws a named error the envelope loader maps to a refusal
screen) for non-3×3, non-symmetric, or non-positive pivots; `veKhongGian` never emits a non-finite coordinate; a
vitest with the five matrices of `test_product_metric_type_rejects_non_spd_gram_matrices` passes.

## F3 — `length_unit` not displayed

Route D adds, when the source uses a symbolic length `a`:
`scene3d.length_unit = {"symbol": "a", "display_scale": "a = 1 đơn vị dựng", "is_given": false}`
(`backend/app/ai/function_route.py::run_function_route`). `grep -rn length_unit frontend/src` finds no consumer, so
the learner is never told that the drawing fixes `a = 1` as a display scale that the problem did not give.

**Acceptance:** when `length_unit` is present the scene shows the `display_scale` sentence (Vietnamese, no technical
id), and nothing changes for scenes without it.

## F4 — proof status is not representable

`run_fact_route` records every goal / negated clause checked on ONE configuration as
`{"evidence_state": …, "proof_status": "UNVERIFIABLE", "can_present_as_proven": false}` in `KetQuaTuyen.planner`
(`backend/app/ai/function_route.py::_quan_sat_cau_hinh`). Neither `scene3d` nor `ValidatedSimulationEnvelope`
carries these fields, and no route-D → envelope adapter exists yet. Today nothing is lost because route D is not
wired; the moment it is, a "prove that …" goal checked on a single figure must not be presented as proven.

**Acceptance (for the wiring wave):** the adapter maps goal checks into the envelope; the UI never renders
"đã chứng minh" unless `can_present_as_proven` is true; a test with a served row carrying a goal check asserts the
learner text says it was observed on the constructed figure, not proven.
