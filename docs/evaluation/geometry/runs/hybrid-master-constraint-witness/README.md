# Run `hybrid-master-constraint-witness`

This folder holds the candidate-divergence layer for the seventeenth continuation of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`. It corrects `../hybrid-master-planner-provenance/candidate_divergence.json`.

- **Product change:** constraint-defined planes on Hybrid `/4`.
  - **Contract:** `typed-fact-next/2` `plane_kind = "constrained"`.
  - **Registry `/30`:** rule `MAT_RANG_BUOC`, plus a `Normal` effect on `orthogonal_projection`.
  - **Planner `/25`:** witness planning.
  - **Engine `/21`:** exact existence and uniqueness from the affine rank.
  - **Route:** witnesses outside the span are moved to verification.
  - **Adapter `/4`:** re-checks the result.
- **Verdict:**
  - `CONSTRAINT_TO_WITNESS_SERVICE_VERIFIED_OFFLINE`;
  - `GENUINE_DISCOVERY_NOT_ESTABLISHED` (`../hybrid-master-backend-replacement/constraint-to-witness-c17.md`).
- **Unchanged:**
  - `CACHE_VERSION` 131;
  - `LLM_ONLY`;
  - the locked flat `TypedFact` schema;
  - Route A schemas;
  - prompts;
  - frontend.
- **Candidate:** product `8a89c6fd`, 118 files, `b1b29a13dc4ed5e7…`, frozen at `dbe50238`
  (`frozen-evaluation-candidate.json`).
