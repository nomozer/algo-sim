# Grounded goal completeness — extraction v2

Research contract, 2026-10-17. **Status on `main`:** the evaluation part (scorer /2, source obligations) and the
bounded Source Grounding fixes are in force; the extraction-prompt part was measured on a paired dev pilot and **not
integrated** (owner disposition, `runs/hybrid-semantic-extraction-v2/disposition.md`) — the product prompt is unchanged. Implements the owner's Semantic Extraction v2 request within the accepted Hybrid B architecture. No new TypedFact fields, planner, parser or geometry capability.

Each source request must have its own fact or an explicit unsupported/ambiguous representation with a faithful source quote. Numeric questions retain all operands and the owning solid where required. Missing source information stays missing; the extractor never invents coordinates, intermediate labels, a function sequence or geometric consequences.

Named points use their source identity. An unnamed described point uses the existing question `point_kind` and `points`, with no invented `point` or `points_a`. Schema expressibility does not imply planner capability (notably unnamed centroid and line–line angle).

Ordinary plane operands retain every written label; the engine checks coplanarity. Existing referenced intersection-line producers require exactly three labels per plane: broader groups must be explicitly unsupported rather than silently truncated. Finite-segment distance, squared length, optimisation and interaction must not be approximated by nearby quantities.

Evaluation source obligations are authored independently of TypedFact role. Served values are matched against actual planner/execution bindings and an independent mathematical oracle, never through extraction fact pairing. Every required request, including constructions and unsupported requests, participates in completeness. Missing measurement evidence is UNKNOWN, not success or a numeric zero.

Prompt effectiveness requires new live measurement. Offline authored-fact replay proves wiring and deterministic checks only. LLM_ONLY, Hybrid NO-GO and separate exact-identity live/integration approvals remain in force.

Implementation/evidence: `docs/evaluation/geometry/runs/hybrid-semantic-extraction-v2/`.
