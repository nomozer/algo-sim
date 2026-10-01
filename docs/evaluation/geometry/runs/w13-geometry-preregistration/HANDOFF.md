# Handoff — w13 geometry preregistration

Nothing to look at in a browser in this run: it is an audit and a preregistration.
What needs a person is two decisions before the next wave starts (below).

## Decisions needed before W14

| Id | Question | Proposed |
|---|---|---|
| D2 | Assumption policy: refuse and label only, or also ask the user to confirm an assumption in the UI? | refuse + label in W14; confirmation UI later |
| D3 | Does cone/sphere formation (axis, radius, circle, generator, surface as separate steps) join W14? It needs IR/event changes and the curved product is still `foundation_only`. | no |

D1 (amber section in the neutral view), D4 (frustum in scope?) and D5 (regular solids:
feasibility check first, or Q(√d) coordinates) can wait — see the preregistration §8.

## Reading order

1. `REPORT.md` (this run)
2. `docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md`
3. `docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md` — §2 formation
   model, §3 assumption policy, §6 W14
4. `results/ABSOLUTE_ASSUMPTION_INVENTORY.json`, `docs/architecture/geometry_capability_matrix_v2.json`

## Required fields

```text
TASK = W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION
START_HEAD = bf5a7907157be6c1e30801e485faa0d9fbdfd290
END_HEAD = SELF (the documentation commit that adds this file; resolve with git log -1)
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce
ORIGIN_MAIN_FETCHED = YES (git fetch --prune origin, 2026-10-01: no new objects; equals ls-remote)
PRODUCT_CODE_CHANGED = NO

W12_AUTOMATION_RESULT = READY_FOR_HUMAN_VISUAL_REVIEW
W12_HUMAN_REVIEW = NEEDS_CHANGES
W12_MERGE_APPROVAL = NO

ABSOLUTE_ASSUMPTIONS_FOUND = 67
SAFETY_INVARIANTS = 4
CONFIGURABLE_DEFAULTS = 13
CAPABILITY_REQUIREMENTS = 3
HISTORICAL_MEASUREMENTS = 8
UNSUPPORTED_ABSOLUTES_REQUIRING_REPAIR = 10 (NA-05, NA-11, NA-23, NA-31, NA-37, NA-40, NA-42, NA-52, NA-53, NA-57)

POLYHEDRAL_CAPABILITY = PARTIAL
CURVED_SOLID_CAPABILITY = PARTIAL
AUXILIARY_GEOMETRY_CAPABILITY = PARTIAL
SECTION_CAPABILITY = PARTIAL
COMPOSITE_SCENE_CAPABILITY = MISSING (SINGLE_SOLID_ONLY)

TRIANGULAR_PYRAMID_FORMATION = NEEDS_CHANGES — root cause identified (compiler.py::bien_dich emits no height, no lateral-edge group); repair preregistered as generic PYRAMID_LIKE formation
TRIANGULAR_PRISM_FORMATION = NEEDS_CHANGES — root cause identified (_bien_dich_prism emits no top face, no lateral edges); repair preregistered as generic PRISM_LIKE formation
ASSUMPTION_CHANNEL_POLICY = PREREGISTERED (GIVEN_VALUE / DERIVED_VALUE / MODEL_ASSUMPTION / VISUAL_DEFAULT; P1–P6; AC1–AC7); issue still OPEN
SOURCE_GROUNDING_GENERALIZATION = ASSESSED (offline probe, 25 phrasings, 0 calls): 1 soundness gap ("AB dài 5 cm" false accept, W14 Track C), 1 false refusal ("AB = AC = 5"), radicals unread by the length invariant; no fuzzy matching; no claim of full Vietnamese support
ENVIRONMENT_CAPABILITY_POLICY = DEFINED (capability record per gate; SKIP never counts as PASS; real-GPU performance BASELINE_NOT_ESTABLISHED)

DOCS_CREATED = docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md · docs/architecture/geometry_capability_matrix_v2.json · docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md · run README, RUN.json, REPORT, HANDOFF, MANIFEST, inputs/W12_HUMAN_VISUAL_REVIEW.json, results/ABSOLUTE_ASSUMPTION_INVENTORY.json, results/REMAINING_GEOMETRY_CAPABILITY_MATRIX.json, diagnostics (probe, logs, worktree cleanup)
LIVING_DOCS_UPDATED = CURRENT_STATE · ROADMAP · AI_CONTEXT_BUNDLE · OPEN_ISSUES · STATUS_LEDGER · EVIDENCE_INDEX · THESIS_READINESS · ARCHITECTURE_MAP · docs/README · CODE_INDEX (+ docs-audit allow-list in backend/scripts)
BROKEN_LINK_COUNT = 0 (docs audit over canonical docs; 58 relative links across every touched markdown file, docs/architecture/*.md and the run documents)
DOCS_TEST_RESULT = PASS in a clean detached worktree at 7202befe (507/507); main tree 506/507 — the one failure needs a clean tree (user's favicon deletion + uncommitted w13 docs)
CANDIDATE_VERIFY = PASS (548f5b3b…, 103 files)
CACHE_VERIFY = PASS (CACHE_VERSION 105, environment b1714b566e25c912)
SCHEMA_SYNC = PASS (both mirrors d852b47c…, two exports, no file changed)
DEFAULT_MODE = LLM_ONLY
FULL_PRODUCT_SUITE = NOT_RUN_NOT_REQUIRED_FOR_DOCS_ONLY_AUDIT
LIVE_GEMINI_REQUESTS = 0

COMMITS_CREATED = 2 (7202befe docs(architecture) · SELF docs(eval))
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES

FINAL_DECISION = ARCHITECTURE_PREREGISTRATION_READY
NEXT_ACTION = W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (after D2 and D3)
```

## Known leftovers

- `D:/tmp/w13-verify-c1` — temporary worktree directory, unregistered from git, about
  500 MB of checked-out files, no unique artifacts; safe to delete by hand
  (`diagnostics/WORKTREE_CLEANUP.json`).
