# Final visual closure — PARTIAL / OWNER GATE

Authorization `GO_LOCAL_VISUAL_CLOSURE_AND_HYBRID_GEOMETRY_READINESS`, 2026-10-25.

F1 is fixed in product code. F2 selection/hover UX is fixed; the locked hue policy still conflicts with the required terracotta section fill. Complete visual closure is **not certified**: F2 policy, sphere-source/plane presentation, independent review and human approval remain open.

## Product changes and scope

- `Scene3DExplorer`: a selected quantity's coherent formula remains in the open analysis panel; inspector retains identity, geometric/numerical dependencies and a link. Only an actually matching analysis formula suppresses the inspector formula. Mode A remains unchanged.
- Analysis uses a separate CSS class with the same style. This prevents the established inspector selector from accidentally selecting the analysis paragraph and counting that paragraph twice. No official oracle code or threshold changed.
- `buildObject3D`: selected section/SECTION_REGION polygon, circle or ellipse has cobalt `#2563EB` boundary; default semantic fill/outline remain terracotta `#C85A32`. Other planes retain their roles. Geometry and source envelopes do not change.
- Canvas pointer hover uses separate presentation state, clears on leave/drag, and reuses existing picking. It never calls selection or geometry mutation. Actual desktop/mobile screenshots change on hover and restore the original PNG hash on leave.
- Sphere rendering no longer invents three equator/meridian loops. Existing surface/depth/occlusion machinery remains.

RED/GREEN receipts: `red-green.json`, `targeted-green.json`, `supplemental-red-green.json`; final frontend 80 files / 1354 Vitest tests, typecheck and production build pass. A source-regex assertion and two older semantic-color/decorative-sphere assertions were updated to the explicit Owner UX; locked mathematical/visual oracles were retained.

## P3 acceptance and remaining defects

| Area | Scope and outcome |
|---|---|
| Camera-dependent visible/hidden strokes; mathematical dash policy | Official scenario assertions plus orbit gate; per-camera geometry signatures and selected/neutral dash preservation are retained. See official receipts. |
| Right angles, midpoints, intersections, sections, intersection lines | Existing official witness/formation/identity assertions retained. No frontend theorem or geometry reconstruction added. |
| Named planes / unnamed vertices / coincident points | Prior backend fix retained; final browser package includes `(MNP)` section and `A ≡ H ≡ H1`. Unnamed vertices are not assigned synthetic mathematical names. |
| Hover / selected | VERIFIED on 1440 / 390; selected persists after pointer leave; scene payload bytes unchanged in the probe. |
| Shell opacity | Existing `solid=0.12` and secondary=0.10 retained, not recolored to satisfy a test. |
| Camera SGK/default, free orbit, top | 20 Owner images, six viewport/case rows, polar |cos|≈0.9999875, no page errors; source geometry unchanged. Human judgement remains pending. |
| Sphere decorative loops | VERIFIED absent by rendered Three.js regression. |
| Sphere plane clarity and helper identity | **OPEN / PARTIAL**. The offline `cau-cat-mat-phang` sample still declares free A/H/U/W; H/U/W are visible, although the source only names I and plane (P). Plane is hidden/small relative to the section in the captured states. |
| Tangent / nonintersection | Exact kernel distinguishes d²<R², d²=R² and d²>R². The canonical Hybrid bridge refuses curved solids; no sphere Hybrid E2E acceptance is claimed. |

The sphere issue is not repaired by parsing names or hiding arbitrary IDs in frontend. `build_geometry_samples.py::chuong_trinh_cau_cat_mp` declares free basis points and a three-point plane; its sample-building path is not an end-to-end source/assumption-gated production request. Replacing that construction requires source-grounded center–plane distance/gauge authority, not merely a prettier mesh. Existing `plane_perpendicular_to_line` is a reuse candidate, but the source does not supply the line/point identities needed to justify it by itself. Do not claim the sample is Hybrid-supported.

The Owner HTML is a visual reference, not an oracle: its sphere branch clamps `sqrt(max(0.1,R²-d²))` and its UI range does not exercise tangent/no-cut cases. None of those algorithms was copied.

## Certification

See `OFFICIAL_SUITE_F1_F2_REPORT.md` for measured suite results and `verification/full-t3/receipt.json` for the final T3 verdict. Historical T3 at a084c180 is not certification of this product. Current baseline identity: product `53fe3d25243fe1e99410dfc52546e16225f19e75`, freeze `c84392c15dbd08e4a59a6083ace17b577b8b2cb7`, 118 measured files / `8be632679307a94ce4525ad576a05a9eccffc8ba2bdbf02d4c7dc93c208b7c41`. That measured hash excludes Scene3D frontend; the new product SHA separately binds its changes.

`LLM_ONLY`, cache 128, `ALLOW_LIVE_AI=0`, Hybrid production NO-GO. No backend product code/schema/default/provider/prompt changes. No merge, push, ACL changes, history rewrite or publication-exception changes.
