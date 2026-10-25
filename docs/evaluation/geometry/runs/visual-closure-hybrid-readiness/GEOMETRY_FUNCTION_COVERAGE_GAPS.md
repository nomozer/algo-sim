# Reusable geometry coverage gaps

## Reuse inventory

The actual architecture already contains one Registry, source gate, goal/effect resolver, exact engine, kernel, canonical V2 bridge and Adapter /4. `catalog-audit.json` binds the inspected files by SHA-256 and lists 35 `_F(...)` registry declarations. No new parallel geometry engine or case-ID branch was added.

| Responsibility | Existing implementation | Remaining gap |
|---|---|---|
| Typed facts / source identity | `typed_fact_next.py`, `typed_fact_next_extraction.py`, Registry `kiem_nguon` | Curved enums parse but parsing is not semantic/source/solve support. Live extraction quality remains UNKNOWN. |
| Right prism | Registry `prism`, base/length/perpendicular facts; engine right-prism placement | Many determined bases already work. Arbitrary-base claims exceed current premise vocabulary/metric closure and memory bounds. |
| Oblique prism | Engine `prism_lateral_vector_*` propagation and common-vector consistency checks | No perpendicular-side assumption; a top vertex needs enough source facts. New authored cases pass; arbitrary oblique section goals remain bounded. |
| Goal composition | Planner `_EffectResolver`, midpoint/centroid producers, distance/angle/area goal contracts | Canonical V2 bridge currently maps volume, ratios, residual volume and section area, not general point–plane distance/angle/area targets. Route B capability is not canonical /4 reachability. |
| Sphere–plane | Kernel `intersect_plane_curved` / `_giao_cau`, projection and exact `radius_sq` | Bridge raises `BRIDGE_UNSUPPORTED_CURVED`; Registry/planner/source contracts for canonical sphere-distance/plane construction are missing. Tangency must yield a point or explicit refusal, never a zero-radius fabricated circle. |
| Cone / cylinder | Existing curved kernel and bounded circle/ellipse/axial constructions | No canonical curved Registry/planner chain; distinguish radius/height/generator and section preconditions before enabling. |
| Composite / inscribed / circumscribed solids | Some polyhedral shared-face/residual-volume paths | Rendering two solids proves no containment/tangency/incidence theorem. Mixed curved composites and inscription certificates lack a canonical end-to-end contract. |
| Coordinates | Exact kernel coordinates and root chart, qualified identity schema | Bridge rejects non-root/renamed qualified identity; arbitrary source coordinate input and Oxyz goals are not general canonical capabilities. |
| Presentation | Existing verified scene/formation/identity consumer | Legacy sphere sample still exposes free helper identities and weak plane patch. Backend source/construction authority must fix this; frontend must not infer geometry or names from source text. |

## Measured checks in this run

Seven new authored canonical V2 prism cases pass volume oracles and /4 wrapper validation: four right and three oblique cases, renamed vertices, new dimensions, and a scale-2 pair. All top/base pairs retain one lateral vector. Five negatives refuse for missing base/height, zero height, inconsistent height and invented rightness. Sphere/cone/cylinder declarations validate schema but all three refuse at the bridge. See `capability-probe.json`.

These probes do not estimate independent holdout coverage, provider extraction fidelity or arbitrary rotation/translation handling through a nonexistent coordinate-input contract. No such evidence is invented.

## Priority

First expose already-supported canonical V2 goals through the existing planner with strict source/target validation; do not rewrite prism placement. Then add a source-grounded sphere–plane function chain reusing exact kernel classification, projection and circle construction. Cone/cylinder composites follow only after their preconditions and certificates exist. `B3_VERTICAL_SLICE_REPORT.md` specifies one bounded prism-distance slice for an Owner-approved next checkpoint.
