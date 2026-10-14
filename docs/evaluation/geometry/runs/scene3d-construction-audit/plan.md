# Plan — Scene3D construction audit of the two-line scenes (2026-10-14)

Branch `research/goal-directed-two-line-plane-section` after `41e02a55`; main `5270f3dd` untouched; no push, no Gemini.

1. Math (offline, 0 model calls): `backend/scripts/audit_scene3d_construction.py` checks every point against its producer,
   the plane (covector, strict parallel), the section against `tests/geometry/two_line_plane_oracle.py`, every trace step
   (inputs, outputs, dependencies, narrated face), and metamorphic variants re-run through the real Hybrid route.
   Fault injection: `backend/tests/geometry/test_scene3d_construction_audit.py`.
2. Browser: `frontend/scripts/hybrid-section-visual-check.mjs --scenes two-line --playback` walks every learner step of
   the product timeline with the real slider; projection of markers/labels vs exact payload; hidden labels must really
   overlap; revisit, second view, H/H1 selection, contact sheet.
3. Defect found (class D): `locNhanChongNhau` hides short labels by a fixed 68×22 px window (S, A′, B′). User decision
   2026-10-14: fix with full gates — RED unit test, fix, before/after playback, re-freeze candidate, T3 clean detached,
   independent review.
4. Construction order (M/H/H1 before the solid, class E): user decision — record as limitation, no Planner change.
