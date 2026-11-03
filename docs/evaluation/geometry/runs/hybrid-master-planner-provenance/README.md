# Run `hybrid-master-planner-provenance`

This folder holds the candidate-divergence layer for the sixteenth continuation of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`. It corrects `../hybrid-master-described-points/candidate_divergence.json`.

- **Product change:** planner `/24` classifies `search_telemetry` by step provenance recorded at emission. Building a
  point the question describes is `source_defined`, a declared rule's step is `registered`, and only a search-generated
  step makes a plan `DISCOVERED_FUNCTION_COMPOSITION`. In Registry `/29` no contract can produce a search-generated
  step, so DISCOVERED is currently unreachable (stated in `../hybrid-master-backend-replacement/planner-generalization-c16.md`).
- **Unchanged:** calls, auxiliary certificates, answers and envelopes; registry `/29`; engine `/20`; `CACHE_VERSION`
  131; `LLM_ONLY`.
- **Candidate:** product `9c561ca6`, 118 files, `1725590664c916d3…` (`frozen-evaluation-candidate.json`).
