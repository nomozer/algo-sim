# Run `hybrid-master-composite-relations`

This folder holds the candidate-divergence layer for the ninth continuation of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`. That continuation covers multi-object FactGraph, composite geometry, and generalized geometric relations on Route D `/4` (`registry /26`, `planner /22`, `engine /18`, `geometric-relation-certificate/1`):

- additive `typed-fact-next/2` relation contract (`GeometricRelationSpecV2` kinds `circumscribes`, `inscribed_in`, `tangent_to` + `contact_ref`; `SolidSpec.inscribed_in`) preserving `typed-fact-next/1` compatibility;
- certified sphere inscribed in a convex polyhedron across **all** boundary faces (`_tam_noi_tiep_da_dien` over exact `Fraction` + `_QField` multiquadratic arithmetic, face coplanarity & strict polygon convexity verification, strict inward half-spaces, strict `relint` face contacts, and independent $9V^2 = r^2 (\sum_k S_k)^2$ identity);
- certified sphere–plane tangency (`_chan_tiep_xuc_mat`, $d^2 = R^2$ vs. `PLANE_INTERSECTS_SPHERE_NOT_TANGENT` vs. `PLANE_DOES_NOT_TOUCH_SPHERE`, non-collinear witness triple, optional named contact verification);
- composite topologies (multi-polyhedron `shared_faces` + sphere, dual circumscribed + inscribed spheres named `(S1)`/`(S2)` or unnamed `"()"`, polyhedron section + sphere coexistence, and axial cylinder/cone + circumscribed/inscribed spheres);
- explicit multi-object planner dependency DAG (`DEPENDENCY_CYCLE` detection) + `composition_classification`, closed Vietnamese Source Gate grammar, and 4-layer `relation_certificates` (`SOURCE_GROUNDING_PROOF`, `GEOMETRIC_RELATION_PROOF`, `KERNEL_EXECUTION_PROOF`, `RESULT_CERTIFICATE`).

**Evidence:** in `../hybrid-master-backend-replacement/`:

- `multi-object-factgraph-audit.md`
- `composite-relations-review.md`
- `composite-relations-probe.json` and `tools/composite_relations_probe.py`
- `curved-capability.md`, the ninth-continuation section & 18-group capability matrix
- `migration-ledger.md`
- `inventory-phase-m.json` and `wave3-phase-m.json`
- `fixtures-adapter-2-composition-classification/`
- `schema-census-extension.json`
- `HYBRID_MASTER_EPIC_CURRENT_STATE.md`
