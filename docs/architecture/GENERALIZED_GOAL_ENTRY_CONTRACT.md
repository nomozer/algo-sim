# Generalized Goal Entry — bounded length slice

Effective research contract: run `generalized-goal-entry`, based on Function Discovery `96569792`. Hybrid remains disabled in the product.

`TypedFact` fields and provider schema are unchanged. A question with `quantity=length`, `point_kind=midpoint`, `points=[S,C]`, `points_b=[A]` precisely describes a length from the unnamed midpoint to A. The Planner now admits this combination; the provider prompt has not been taught it and extraction is NOT_MEASURED.

Each function can carry its original `planning` contract plus `planning_extra`: alternative mathematical effects of the same function, not problem recipes. `ask_length` retains its distance-witness effect and gains `AnswerLength(P,Q)` with two Point prerequisites, `segment=[P,Q]`, goal quantity `length`, and its source phrase. A contract never names a producer such as midpoint. Registry goal metadata selects the effect; `_EffectResolver` selects producer contracts, unifies by position, reuses constructions, and writes calls. Every Answer effect bypasses answer memoization so repeated questions keep their IDs.

The existing effect-chain certificate records which effect an alternative contract claims. The source gate replays the template, checks typed dependencies, descriptor operands, exact target and complete requested phrase, and verifies `labels` are precisely fresh outputs. The engine checks the descriptor by its mathematical definition, then checks the composed answer squared against direct Gram distance to the point target. Source certification, mathematical checking and presentation provenance remain separate authorities.

Supported new meaning: length between a described point and one named point; named segment lengths also enter through the contract. Existing distance goals retain their established entry/certificates. Arbitrary area, volume, angle, nested descriptions or two unnamed operands are not implied. The current generalized source/engine path verifies length only; a new measurement meaning still needs an independent verifier and exact source interpretation. A new producer with an existing descriptor predicate, e.g. centroid, can be added as contract data without changing Planner/gate/engine.

Budgets and safe refusal remain authoritative. Registry-order independence is deterministic tie-breaking, not proof that every semantic ambiguity has been solved. The inherited named-distance source grammar issues in OPEN_ISSUES still prohibit general Hybrid enablement.
