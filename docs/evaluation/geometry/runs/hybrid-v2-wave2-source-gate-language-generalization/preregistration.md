# Preregistration lock before product repair

2026-10-28. Baseline product remains d7a94d3c (no product diff).
inputs/development.json: 24 positive, 37 negative, SHA-256
d5d8d8ac94071bcced3522fe8f4bc7b93313fe927a70c7c8902122902663d9fa.
The exact horizontal-section oracle and outcomes were authored before product execution.
Six families, four language/order variants each; dimensions and fractions differ from prior development cases.
Baseline RED: 6/24 served correct, 18 false refusals; 37/37 negatives refused in registered groups;
0 wrong-served. All served boundaries and squared areas agree exactly.

Two pre-product gold-input corrections are retained transparently:
- inputs/development-initial.json / results/red-initial-gold-error.json: four-vertex source plane versus three-vertex fact.
- inputs/development-gold-revision1.json / results/red-gold-revision1.json: attempted four-vertex parallel_plane exceeds
  the current V2 schema. Final inputs explicitly name a three-vertex plane in both text and facts.
Neither mathematical outcome nor area/boundary oracle changed. No product change preceded any RED run.
Final corrected RED is results/red-before.json; earlier attempts are not counted as product failures fixed by this wave.

Acceptance: 24/24 positives actually served through route and Adapter4, exact area and boundary agreement;
37/37 negatives refused in the preregistered codes, 0 wrong-served and no internal error as accepted refusal.
The broad registered codes all concern source/fact insufficiency or refusal; green reports retain exact first codes.
Do not expand accepted groups after observing GREEN. Further adversarial controls are additive and reported separately.
Keep old grammar and I-1 consistent. The entire 96-case Wave2 replay is post-feedback regression only.
No fixed 48/48 expected. T3 and independent review gate readiness. W2-M4/M5 remain excluded.
