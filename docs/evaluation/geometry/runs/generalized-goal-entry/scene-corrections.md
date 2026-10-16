# Correction layer — Scene3D W1–W3 evidence interpretation

CORRECTS: `scene3d-architecture-visual-reliability` report/findings. Original artifacts unchanged. Independent read-only review in this session inspected eight stored images and verified all 140 state-manifest image hashes. These are technical image inspections, not human approval. Earlier user-sent images are unavailable in this session; no claim to have viewed them.

- `Scene3DWorkspace` imports `maTranKhung4`; mapping is performed by Product `Scene3DExplorer` and explicitly by the harness. The older report's claim that Workspace itself calls `veKhongGian` is wrong.
- Mapper transforms witness `foot`, `marker.u`, `marker.v`; normalization occurs when drawing, and there is no `marker.dinh` field.
- Harness exposes `g`/`step` and an aria-labelled learner-step selector, not the claimed `lstep`/test-ID API.
- Coincident labels group exact coordinate strings, not a `1e-3` tolerance.
- `section-MAB-trapezoid` final aux0 telemetry has 29/29 product/harness objects, not 30/30.
- State manifests reference 140 retained screenshots, not 134.
- Sixth stored RED failure is W2 plane sizing/opacity, not a premature-section-face regression test.

One inherited interaction defect was found in code: hidden foot/source points could leave a perpendicular witness visible. This run adds a RED→GREEN regression and filters witnesses by interaction visibility. Hiding a carrier plane alone does not suppress a witness whose foot/source remain visible; auxiliary planes may intentionally be hidden by default. Canonical solid edge ownership, visibility classifier and exact geometry are reused unchanged.
