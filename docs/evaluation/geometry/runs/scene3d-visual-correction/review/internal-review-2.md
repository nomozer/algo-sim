# Internal separate-context review — round 2 (verbatim)

Reviewer: a second Claude agent with a fresh context, spawned by the author session. **Internal, not independent.**
Scope: commit `093c0b4c` against `60e569d3` (the round-1 fixes). Read-only, and it ran no code, because a browser
measurement was in progress. Every finding below is reasoned. Disposition: `../REVIEW_REPORT.md` §3b.

---

## Critical
None found.

## Important

**I-A. A cylinder given by height loses its top rim.** `scene3d-view.tsx:1918`
- The new code uses `o.apex_or_top!` as the top-rim centre.
- The backend sends `apex_or_top: null` with `height_sq` when the height is given that way
  (`simulation_state.py:568-575`, `adapter3_simulation.py:2231-2233`).
- With `center` undefined, the recursive build returns null and `if (!rim) continue` drops the rim with no error. The
  generators then end at nothing.
- Before this commit, the synthetic `dinh` was used, which worked for integer heights.
- Fix: use `apex_or_top` when present, otherwise `dinh` passed through the same 1e-6 fraction formatter.

**I-B. The dedupe misses any tilted axis whose components are not exact at 1e-6.** `:1916` together with `:694-697`
- The rim's normal is rounded to 1e-6, but `cungTruc` compares unit directions at an absolute tolerance of about 1e-9.
- Scenario: anchor (0,0,0), apex (1/3,2/3,2/3), with a backend `intersect_plane_curved` cap circle. The direction error
  is about 5e-7, there is no match, and the duplicate rim and its overdraw (round-1 I1) come back.
- Route D is unaffected because its axes are always vertical with planes z=0 and z=h. The new test only uses
  axis-aligned integer axes.
- Fix: store the unrounded `dinh−tam` in `vanhDayCua`, or compare at about 1e-6.

**I-C. The dedupe reads `scene.objects` with no regard for the user's hide or isolate.** `:3563`
- `isVisible` (`interaction-state.ts:135-136`) filters by `hidden_ids` and `isolated_ids`.
- If the user isolates the cylinder, the base circle is not part of the isolation (it depends on the solid, not the
  other way round). The cylinder then has no caps at any step. Hiding the circle has the same effect.
- The dedupe also ignores the presentation translation (`khoaDich`). In an exploded group the cap is removed from the
  solid's displaced position while the circle is drawn somewhere else. Whether this happens depends on the backend's
  `display_group`.
- Suggest comparing against scene objects that are not user-hidden and share the same translation.
- Step gaps: Route D emits the base circle 2 statements after the solid and the top circle 4 after
  (`adapter3_simulation.py:2242-2291`). The frames in between show no caps. That matches #31 (the circle's own step
  decides) and the behaviour before the Codex work, so I accept it.

**I-D. I2 leaves the occlusion convention split.**
- Canonical polyhedron edges now ignore curved occluders. Non-canonical segments and section-polygon borders still use
  them (`:817`, `:884`), and any point inside a ball counts as hidden (`unified-materials.test.ts:79`).
- Scenario: a tetrahedron inscribed in a ball where the ball is the primary solid or sits at a different translation,
  so it still occludes. A section polygon or a median lying in a front face is fully dashed while that face's own edges
  are solid.
- The owner needs to decide whether these should follow the polyhedron-edge rule.

## Minor
- **New 40% node test: probably no red base.** The baseline arc coverage is roughly 0.6–0.7; after erasing 40 % that is
  about 0.36–0.42, near the old 0.4 threshold. The test asserts only `verdict`; erasing ±2 px at the arc ends can also
  hit adjacent front chords, so the FAIL might come from a front edge. Suggest running it once at 0.4 and asserting
  `hidden_arcs.some(a => a.pass === false)` with all front edges passing. Known ceiling: 0.6 still lets about 40 % of a
  0.99-coverage real arc go missing.
- **No curve verdict path still uses 0.4,** but `section-role-oracle.mjs:114` still computes a per-chord `pass` at 0.4
  for curve chords, and the probe exports it. Cosmetic, but a report reader could take it as a verdict.
- **The 1px rim stroke has no depth bias.** `polygonOffset` does not apply to lines; it may stipple against coplanar
  fills under LessEqual.
- **Framing (`diemKhungNhin`) is unchanged by the commit.** It ignores `visible`, and `boQua` skips only
  `curvedSolidVolume`, so an unplaced secondary ring and the zeroed generator buffers still count as framing points.
  Same in the parent; latent, not a regression. Picking is unaffected.

## Checked, nothing found
- C1 is fixed on every path found: the only product caller of `buildObject3D` is the workspace loop (plus the cap
  recursion); both the render loop and `veRef` call `updateCanonicalEdgeVisibility` before every render; the only render
  without an update is a harness hook that runs after a frame.
- The fractional normal is correct (negative values parse; the cone uses only `anchor`). A zero-length axis would give a
  NaN normal — degenerate.
- Ellipse3 and rim_point-only cases are fine. A solid without `radius_sq` now skips its rim instead of crashing.
- Disposal of removed rims is correct.
- No remaining test expects curved occlusion of polyhedron edges.
- R0 tokens: none added to `scene3d-view.tsx`.
