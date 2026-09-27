# Cuboid visual-semantic closure and cross-family regression audit

**Wave:** `CUBOID_VISUAL_SEMANTIC_CLOSURE_AND_CROSS_FAMILY_REGRESSION_AUDIT`

**Date:** 2026-09-27

**Mode:** offline deterministic replay; `LIVE_GEMINI_REQUESTS = 0`

## Recovery and scope

- `START_BRANCH = fix/cuboid-visual-semantic-closure`
- `START_HEAD = d9e79a0022a6e1dc6dfb9fc80488484b629c9105`
- `BASE_FEATURE_HEAD = 51e0c9ca40ff1ec442d51d93669a2a71f3ec5611`
- `ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce`
- `END_PRODUCT_HEAD = 2822beb389f8bdb253f26b8c6d6db1860d184cc6`
- `CANDIDATE_HEAD = 97d0b32b74267343d47cb66d83e2fb06a1a0ede7`
- `SKILLS_VISIBLE = diagnose, review, and the repository skill catalog`
- `IMPECCABLE_AVAILABLE = NO`
- `AGENTS_MD_LOADED = YES`
- `DESIGN_MD_LOADED = YES`
- The user-owned deletion `frontend/public/favicon.svg` remained unstaged and uncommitted.

The architecture remains contract-first:

`RequestContract → typed topology/relations → FactGraph → deterministic primitive compiler → SemanticProgramSpec → validator/kernel → Scene3D → trace/provenance`.

## Independent findings

### FINDING CUBOID-AUDIT-01

- `SEVERITY = HIGH`
- `CLASSIFICATION = CONFIRMED_REGRESSION`
- `AFFECTED_LAYER = compiler provenance / pedagogical trace`
- `REPRODUCTION = compile a cube with only AB=4, or a square prism with base side AB=3 and height AA′=7`
- `EXPECTED = only the stated lengths are GIVEN; equal dimensions are executable derived facts`
- `ACTUAL = AD and/or AA′ copied AB's source fact and initial value, falsely presenting them as GIVEN`
- `ROOT_CAUSE = the cuboid compiler materialized definitional equality by cloning a memory declaration instead of emitting an assignment`
- `CONFIRMED_BY_TEST = test_cube_causal_chain_single_edge_reuse; test_square_prism_inferred_second_base_edge_is_derived_not_given`
- `RECOMMENDED_SCOPE = fixed in this wave`

### FINDING CUBOID-AUDIT-02

- `SEVERITY = MEDIUM`
- `CLASSIFICATION = CONFIRMED_REGRESSION`
- `AFFECTED_LAYER = interpreter narration`
- `REPRODUCTION = change only the localized program title of a cube`
- `EXPECTED = formula narration follows typed/structural semantics`
- `ACTUAL = the interpreter searched Vietnamese title text for “lập phương” or “chóp”`
- `ROOT_CAUSE = presentation prose was used as a semantic discriminator`
- `CONFIRMED_BY_TEST = test_volume_narration_is_independent_from_localized_title plus historical scene snapshots`
- `RECOMMENDED_SCOPE = fixed; enhanced narration is now gated by deterministic compiler provenance and solid structure`

### FINDING CUBOID-AUDIT-03

- `SEVERITY = MEDIUM`
- `CLASSIFICATION = CONFIRMED_REGRESSION`
- `AFFECTED_LAYER = learner UI`
- `REPRODUCTION = enable technical detail and select a Scene3D object`
- `EXPECTED = learner-facing labels and dependency labels only`
- `ACTUAL = raw enums, producers, fact IDs and stable machine IDs were visible`
- `ROOT_CAUSE = the diagnostic panel rendered transport fields directly`
- `CONFIRMED_BY_TEST = Scene3DExplorer tests and browser raw-token assertion`
- `RECOMMENDED_SCOPE = fixed; stable IDs remain internal`

### FINDING CUBOID-AUDIT-04

- `SEVERITY = MEDIUM`
- `CLASSIFICATION = CONFIRMED_REGRESSION`
- `AFFECTED_LAYER = responsive layout`
- `REPRODUCTION = canonical prism/pyramid scenes at 1440×900 with multiple readouts`
- `EXPECTED = both timeline controls remain in the viewport and unobscured`
- `ACTUAL = a 68vh canvas plus a vertical readout list pushed controls below the viewport`
- `ROOT_CAUSE = desktop readout wrapping was declared without a flex container, and the canvas budget omitted the readout/control height`
- `CONFIRMED_BY_TEST = real-browser rectangular pyramid, triangular prism and cuboid replays`
- `RECOMMENDED_SCOPE = fixed with a 58vh desktop canvas cap and horizontal wrapping readouts`

### FINDING CUBOID-AUDIT-05

- `SEVERITY = MEDIUM`
- `CLASSIFICATION = MISSING_TEST`
- `AFFECTED_LAYER = browser evidence harness`
- `REPRODUCTION = inspect the former replay assertions and failure exit path`
- `EXPECTED = topology, distinct projections, exact causal closure, overflow, raw-token leakage and failures affect exit status`
- `ACTUAL = the harness primarily proved canvas existence/subsets and could leave false results insufficiently guarded`
- `ROOT_CAUSE = the evidence runner predated the semantic-closure contract`
- `CONFIRMED_BY_TEST = the revised replay exits 0 only when all six scenarios pass`
- `RECOMMENDED_SCOPE = fixed; temporary mobile/debug runners were removed`

### FINDING CUBOID-AUDIT-06

- `SEVERITY = LOW`
- `CLASSIFICATION = MISSING_TEST`
- `AFFECTED_LAYER = production contract boundary`
- `REPRODUCTION = canonical fixtures alone cannot detect hard-coded dimensions or order-sensitive fact traversal`
- `EXPECTED = asymmetric values and reordered facts preserve semantics through the production pipeline with zero synthesis calls`
- `ACTUAL = cuboid/cube/square-prism and rectangular-pyramid production tests had only canonical values`
- `ROOT_CAUSE = coverage stopped at one representative per specialization`
- `CONFIRMED_BY_TEST = eight new positive production variants; 190-test focused matrix`
- `RECOMMENDED_SCOPE = fixed`

### FINDING CUBOID-AUDIT-07

- `SEVERITY = INFO`
- `CLASSIFICATION = NOT_AN_ISSUE`
- `AFFECTED_LAYER = architecture`
- `REPRODUCTION = inspect topology, primitive registry, routing default and cache identity`
- `EXPECTED/ACTUAL = cuboid and cube reuse `construct_prism`; compiler consumes typed fields; bounded segments remain finite; default remains LLM_ONLY; cache remains 102`
- `ROOT_CAUSE = N/A`
- `CONFIRMED_BY_TEST = compiler/production/section matrix and full backend suite`
- `RECOMMENDED_SCOPE = no product change`

### FINDING CUBOID-AUDIT-08

- `SEVERITY = LOW`
- `CLASSIFICATION = EVIDENCE_GAP`
- `AFFECTED_LAYER = unchanged-family browser depth evidence`
- `REPRODUCTION = inspect the new triangular-pyramid, triangular-prism and rectangular-pyramid browser artifacts`
- `EXPECTED = Tier-A orbit, complete formation captures, causal selection and family-specific negative presentation`
- `ACTUAL = the new artifacts prove desktop/mobile structure, labels, answer, step forward/back, controls, overflow and console health; they do not measure orbit or causal closure`
- `ROOT_CAUSE = the generic historical replay runner does not expose those assertions`
- `CONFIRMED_BY_TEST = EVIDENCE_MANIFEST scope declaration`
- `RECOMMENDED_SCOPE = FUTURE_RECOMMENDATION; do not convert NOT_MEASURED to PASS`

## Results

| Family | Structural replay | Visual depth fidelity | Formation trace | Causal chain | Mobile layout | Negative presentation |
|---|---|---|---|---|---|---|
| Cuboid | PASS | PASS | PASS (9 browser steps) | PASS (exact closure) | PASS | PASS |
| Cube | PASS | PASS | PASS (runtime navigation) | PASS (shared typed dependency contract) | PASS | PASS (shared refusal surface) |
| Square-prism control | PASS | PASS | PASS | PASS (programmatic) | PASS | PASS (compiler fail-closed matrix) |
| Right-triangle pyramid | PASS | NOT_MEASURED | PASS (step navigation) | NOT_MEASURED | PASS | NOT_MEASURED |
| Right-triangle prism | PASS | NOT_MEASURED | PASS (step navigation) | NOT_MEASURED | PASS | NOT_MEASURED |
| Rectangular pyramid | PASS | NOT_MEASURED | PASS (step navigation) | NOT_MEASURED | PASS | NOT_MEASURED |
| Cross-section boundary | PASS (automated boundary suite) | NOT_MEASURED in this wave | PASS (automated) | PASS (automated) | NOT_MEASURED in this wave | PASS (automated) |

Cuboid/cube/square-prism numerical results are respectively 60, 64 and 63. Each emitted solid has 8 vertices, 12 bounded edges, 6 faces and Euler characteristic 2. Browser evidence reports zero console errors, zero uncaught exceptions, zero unexpected unbounded objects, no horizontal mobile overflow, and no leaked internal token. Negative refusal does not mount a canvas.

The compiler/production subset contains 124 collected tests, including 14 positive production-boundary scenarios and 33 node IDs explicitly exercising negative/fail-closed conditions. Eight positive production variants were added in this wave.

## Verification

- Focused backend cross-family matrix: `190 passed` in 2.41s, exit 0.
- Full backend: `6273 passed, 1 skipped, 1 deselected` in 239.27s, exit 0.
- Frontend typecheck: `npx tsc --noEmit`, exit 0. (`npm run typecheck` is not defined.)
- Frontend Vitest: 61 files, `890 passed`, 6.54s, exit 0.
- Frontend production build: exit 0; Vite emitted only the existing >500 kB chunk warning.
- Cuboid browser replay: six scenarios PASS; 9 formation steps; exact causal closure; exit 0.
- Unchanged-family browser replay: desktop/mobile PASS for triangular pyramid, triangular prism and rectangular pyramid; application LLM calls 0.
- Candidate verify: PASS, 103 files, `72516eb576a173a0…`; candidate was frozen from clean product commit `2822beb3`.
- Cache verify: PASS, `CACHE_VERSION 102`, environment `b1714b566e25c912…`.
- Schema sync: two exports are byte-identical; on-disk SHA-256 begins `D852B47C08B7AC0E…`.
- `DEFAULT_MODE = LLM_ONLY`; `LIVE_GEMINI_REQUESTS = 0`.

## Evidence and correction

- Full cuboid Tier-B evidence: `docs/evaluation/geometry/cuboid-cube-semantic-closure-20260927/`.
- Cross-family structural/mobile evidence: `docs/evaluation/geometry/cross-family-regression-20260927/`.
- Candidate divergence correction is additive; the historical `product-response-contract-alignment/CANDIDATE_DIVERGENCE.json` was not edited.
- The previous `cuboid-cube-visual-integrity/` directory remains immutable and is superseded by this wave for current cuboid claims.

## Future recommendations

1. Extend `compiler-scene-replay.mjs` with generic orbit-delta, exact causal-closure and negative-refusal assertions, then recapture Tier A for the three unchanged polyhedron families.
2. Add a canonical cross-section browser replay to the same current-wave evidence format instead of relying on automated boundary tests plus older immutable browser evidence.
3. Split the large frontend bundle using route/domain-level dynamic imports; this is a performance enhancement, not a correctness repair for this wave.

## Required handoff

- `TASK = RESUME_CUBOID_VISUAL_SEMANTIC_CLOSURE_AND_CROSS_FAMILY_REGRESSION_AUDIT`
- `START_BRANCH = fix/cuboid-visual-semantic-closure`
- `START_HEAD = d9e79a0022a6e1dc6dfb9fc80488484b629c9105`
- `END_HEAD = commit containing this report (product identity remains 2822beb3)`
- `BASE_FEATURE_HEAD = 51e0c9ca40ff1ec442d51d93669a2a71f3ec5611`
- `ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce`
- `SKILLS_VISIBLE = diagnose, review, repository catalog`
- `IMPECCABLE_AVAILABLE = NO`
- `AGENTS_MD_LOADED = YES`
- `DESIGN_MD_LOADED = YES`
- `RECOVERY_STATUS = PASS`
- `FILES_CHANGED = compiler/interpreter/display/UI/layout; focused tests and offline evidence runners; additive evidence/correction/index files; candidate refreeze`
- `CONFIRMED_REGRESSIONS = 5`
- `MISSING_TESTS_ADDED = production variants, provenance, title independence, UI leak, topology/projection/causal/mobile browser assertions`
- `FUTURE_RECOMMENDATIONS = generic Tier-A orbit/causal/negative browser capture; current-wave cross-section browser capture; frontend chunk splitting`
- `ARCHITECTURE_INTEGRITY = PASS`
- `HARDCODED_FAMILY_LOGIC_FOUND = NO new renderer hardcoding; compiler specialization remains typed and scoped`
- `RAW_STRING_PARSING_FOUND = title parsing regression removed; no raw-string parsing in compiler rule`
- `CUBOID_RESULT = PASS (V=60)`
- `CUBE_RESULT = PASS (V=64; no fake GIVEN)`
- `SQUARE_PRISM_CONTROL_RESULT = PASS (V=63; not classified as cube)`
- `TRIANGULAR_PYRAMID_REGRESSION = STRUCTURAL/MOBILE PASS; DEPTH/CAUSAL/NEGATIVE NOT_MEASURED`
- `TRIANGULAR_PRISM_REGRESSION = STRUCTURAL/MOBILE PASS; DEPTH/CAUSAL/NEGATIVE NOT_MEASURED`
- `RECTANGULAR_PYRAMID_REGRESSION = STRUCTURAL/MOBILE PASS; DEPTH/CAUSAL/NEGATIVE NOT_MEASURED`
- `CROSS_SECTION_BOUNDARY_RESULT = AUTOMATED PASS; NEW BROWSER DEPTH NOT_MEASURED`
- `POSITIVE_VARIANT_COUNT = 14 production-boundary scenarios (8 added)`
- `NEGATIVE_VARIANT_COUNT = 33 explicitly named fail-closed node IDs in the compiler/production subset`
- `DISPLAY_LABEL_RESULT = PASS`
- `FORMATION_TRACE_RESULT = PASS for changed family; partial Tier A as classified above`
- `CAUSAL_CHAIN_RESULT = PASS for changed family; NOT_MEASURED for unchanged browser replays`
- `PROVENANCE_RESULT = PASS`
- `BOUNDED_GEOMETRY_RESULT = PASS`
- `MOBILE_LAYOUT_RESULT = PASS for all newly replayed families`
- `BROWSER_REPLAY_RESULT = PASS within each artifact's declared scope`
- `CONSOLE_ERRORS = 0`
- `FULL_BACKEND_RESULT = 6273 passed, 1 skipped, 1 deselected`
- `FULL_BACKEND_EXIT_CODE = 0`
- `FRONTEND_TYPECHECK = PASS`
- `FRONTEND_TEST_RESULT = 890 passed`
- `FRONTEND_BUILD_RESULT = PASS`
- `CANDIDATE_VERIFY = PASS`
- `CACHE_VERIFY = PASS`
- `SCHEMA_SYNC = PASS`
- `DEFAULT_MODE = LLM_ONLY`
- `CACHE_VERSION = 102`
- `LIVE_GEMINI_REQUESTS = 0`
- `COMMITS_CREATED = 2822beb3, 40c20948, 97d0b32b, 86f10b73, plus the documentation commit containing this report`
- `PUSH_RESULT = NOT_EXECUTED (repository AGENTS.md forbids push)`
- `MERGE_EXECUTED = NO`
- `USER_FAVICON_DELETION_PRESERVED = YES`
- `FINAL_DECISION = NOT_READY_FOR_MERGE until Tier-A NOT_MEASURED browser cells are closed or explicitly waived`
- `NEXT_ACTION = user reviews the contact sheet and decides whether to require the remaining generic Tier-A browser captures before merge`
