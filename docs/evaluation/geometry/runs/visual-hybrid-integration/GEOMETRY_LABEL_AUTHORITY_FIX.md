# Geometry label authority fix

## Defect

`frontend/src/simulations/domains/geometry/scene3d-presentation.ts::kyHieu` rewrote backend-owned identity:

```ts
if (n === "" || /I\d/.test(n)) return null;   // hid every notation containing I+digit
if (n === "(HUW)") return "(P)";              // renamed one specific string
```

Origin: commit `3bfc8dd0`, the verbatim checkpoint of the owner's uncommitted V6.2 session. Claude committed that checkpoint in the SGK port campaign without reviewing this hunk, and the same code reached `13d28b84` and the integration merge `78e88470`. Codex's review found it. Codex removed it in the working tree; Claude verified the fix and committed it as **`a9d05dda`**.

## Trace: backend → Scene3D

| String | Where it comes from | Mathematical role | What the old frontend did |
|---|---|---|---|
| `I1`, `I2`, `I3` | Point **ids** of engine-introduced intersection points. Their `notation` is `null` (unnamed; label "Giao điểm của SB và (α)") | Internal id, not a learner name | Nothing for the points (already unlabeled) |
| `MI1I2I3`, `S(MI1I2I3)`, `V(S.MI1I2I3)` | `display_names.py` step ⑧ builds a section notation from `section_vertex_names` with `ky_hieu_toan(s) or s`, which falls back to the **id** of an unnamed vertex; quantities compose from the section notation | Backend notation, but it leaks internal ids | **Hid the whole section and quantity notation** (any `I` + digit, e.g. also a valid `AI2`) |
| `(HUW)` | Offline sample `cau-cat-mat-phang`, plane `P`. Notation is composed from the model's construction points H, U, W because `prefer_declared_plane_names` is off on the LLM_ONLY route; `label` is `(P)` | Backend notation; the problem names the plane (P) | **Renamed** to `(P)` by exact string match, a case-specific hardcode |

Point names, plane names and section names are backend authority (`display_names.py`, `function_route.py`, `adapter3_simulation.py`). The only frontend name operation that remains is `chuanTen` in `hybrid-preview-adapter.ts`, a prime-normalised **comparison** used to validate Adapter /4 bindings; it changes no display.

## Fix (`a9d05dda`)

`kyHieu` returns the backend notation verbatim; empty ⇒ `null` (print nothing, invent nothing). There are no regexes, no exception list and no alias table. Coordinates, topology, dependency DAG, provenance and closure certificates are untouched (frontend only).

Regression test `scene3d-presentation.test.ts`, `it.each(["I1","I12","AI2","(HUW)","(α)"])`:
- **RED** on the old code: 4 failures (`I1`, `I12`, `AI2`, `(HUW)`); the `(α)` control passes both ways.
- **GREEN** after the fix: 19/19.
- The suite also keeps "no notation ⇒ print nothing".

## Learner-visible consequence (accepted, owner rule P2.7)

- The `cau-cat-mat-phang` plane now reads `(HUW)` instead of `(P)`.
- Sections and quantities that vertex-cycle through unnamed intersections now read `MI1I2I3`, `S(MI1I2I3)`; the vertices themselves stay unlabeled.

These are backend display-identity gaps. They are now visible instead of being masked.

## Backend display-identity proposal (not implemented)

1. **Section notation must not leak ids.** In `display_names.py` step ⑧, build the vertex-cycle notation only when every vertex has a backend notation (`ky_hieu.get(s)`), not `ky_hieu_toan(s) or s`. Otherwise leave `notation = None`, so the section is named by its construction sentence ("Thiết diện của S.ABCD cắt bởi (α)") and quantities by `_DANH_TU_NGAN`. Alternative: give engine-introduced intersection points a learner notation (e.g. `I₁`) *and* print it on the point, so the cycle name and the canvas agree.
2. **Declared plane names on the default route.** Enable `prefer_declared_plane_names` on the LLM_ONLY scene build (it is already on for function-route and Adapter /3), so a plane the problem calls `(P)` keeps `(P)` instead of a name built from model construction points.
3. Both change default-route scene output. That means a `CACHE_VERSION` decision, measured-system re-freeze, re-generating `geometry-samples.json` with `scripts/build_geometry_samples.py`, and the existing display-name tests. This is outside the current authorization; it needs an owner GO.
