# Wave 3A — Exact Composite Volume Reasoning (`volume-reasoning`) Plan

- **Branch:** `research/hybrid-wave3a-volume-reasoning`
- **Baseline `main`:** `1613e0d3ebe16f0f2fe4be755052491ff581e51b` (`product_commit_sha` = `050bb35377b40146d4862afe050a40228821a758`)
- **Authorization:** `GO_HYBRID_WAVE3A_LOCAL_RESEARCH` (`LOCAL IMPLEMENTATION — NO GO MAIN`)
- **Contract:** [`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md) / [`docs/architecture/WAVE3A_CONTRACT_DECISION.md`](../../../architecture/WAVE3A_CONTRACT_DECISION.md)

## Phases & Checkpoints

1. **P0 — Baseline & Architecture Context Recovery:**
   - Verify `main == origin/main == 1613e0d3ebe16f0f2fe4be755052491ff581e51b`, clean working tree, and create branch `research/hybrid-wave3a-volume-reasoning`.
2. **P1 — Contract-First Design:**
   - Write [`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md) and [`docs/architecture/WAVE3A_CONTRACT_DECISION.md`](../../../architecture/WAVE3A_CONTRACT_DECISION.md) specifying `ask_volume_ratio`, `ask_residual_volume`, and formal relationship certificates (`VolumeRatioCertificate`, `ResidualVolumeCertificate`).
3. **P2 — Primary Capability (`ask_volume_ratio`):**
   - Register `ask_volume_ratio(numerator_solid, denominator_solid)` (`AskVolumeRatioArgs`, `provider_offered=False`) in `registry.py` with closed Vietnamese source grounding and unit validation.
   - Implement `VolumeRatioCertificate` and independent Gram-metric cross-check in `engine.py` (`bac = 0`, dimensionless).
4. **P3 — Secondary Capability (`ask_residual_volume`):**
   - Register `ask_residual_volume(original_solid, subtracted_solids)` (`AskResidualVolumeArgs`, `provider_offered=False`) in `registry.py` with closed Vietnamese source grounding.
   - Upgrade `interpreter.py::_eval_value(BinaryArithExpr)` to use `radical.add`, `radical.negate`, and `radical.multiply` for exact `Radical` arithmetic.
   - Implement `ResidualVolumeCertificate` (`CONTAINMENT_VERIFIED`, `SHARED_BOUNDARY_VERIFIED`, `DISJOINT_INTERIORS_VERIFIED`, `POSITIVE_RESIDUAL_VERIFIED`) in `engine.py` (`bac = 3`).
5. **P4–P5 — Planner, Source Gate, Scene3D & Pedagogical Consistency:**
   - Extend `planner.py` (`QuantityKind` with `WithJsonSchema` preserving `TypedFact.model_json_schema()`, `_goi_hoi` solid pair/list binding, `Tier 5` dependency edges).
   - Extend `simulation_state.py` and `display_names.py` for `ask_volume_ratio` and `ask_residual_volume` without fabricating unverified residual 3D solid meshes.
6. **P6–P10 — Controlled Development Evaluation, Historical Compatibility & Full T3:**
   - Build independent `oracle.py` (0 imports from `app`/`tests`), `corpus-dev.json` (`>= 10` positive ratio, `>= 5` positive residual, `>= 12` negative/adversarial), and `dev-evaluation.json` (`DEVELOPMENT_EVALUATION_NOT_BLIND`).
   - Run full regression suites, independent subagent review, and authoritative Full T3 in a clean detached worktree.
