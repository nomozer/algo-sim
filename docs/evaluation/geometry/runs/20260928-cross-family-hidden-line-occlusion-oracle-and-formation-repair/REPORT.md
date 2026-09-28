# Cross-family hidden-line occlusion oracle and formation repair

Status: `VERIFICATION_NOT_CLEAN`

This wave is an additive correction to
`CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR`. Historical reports and
artifacts were not rewritten. The earlier `READY_FOR_HUMAN_VISUAL_REVIEW`
conclusion is corrected because it did not yet have an implementation-independent
perspective oracle, frozen camera identities, or the recovery audit recorded here.

## Identity and commit chain

- Branch: `fix/cuboid-visual-semantic-closure`
- Start HEAD: `532d436611d58023cfabac6020f1ad85e2446e16`
- Merge base / `origin/main`: `a9492ee98ff9dc3302d1ff64465f1c06e9001bce`
- Red regressions: `bc19021e7bf138ec303c547a27ae9a54614a9775`
- Topology, ownership and adaptive occlusion: `b8880d774d9a798af73669c6358c827e049bbcfb`
- Product formation and stable section identity: `50a31e0b7124cb038ff5c56dd9c856778a263725`
- Independent oracle and browser gates: `1dab0f7db516e8ce8eee1280ded4d220a10018d5`
- Frozen human expectations: `80766b909d09fc71d6ff05f79b29bd1091ea7d40`
- Candidate / measurement commit: `e115c31df24efc35fe1d5590e3cab6737b5b13d8`
- Evidence and recovery commit: `09934eb7d0850d3f1f6d5c4f4c79f93b33bb92d9`
- Candidate measured-system hash: `31725284b92c87f1de4bb8ebf08d7d178082e097c2a6198a39770d2b86a3b6d1`
- Cache: version `102`, provider-facing fingerprint `b1714b566e25c912…`, unchanged
- Default mode: `LLM_ONLY`
- Live Gemini requests: `0`

`PRODUCT_COMMIT_SHA` follows the approved eight-commit handoff convention and
therefore names commit 3. The candidate manifest truthfully records commit 4 as
the last commit touching a measured frontend product path because that commit
added browser-observability hooks. Both identities are retained; neither history
nor provenance was rewritten to make the labels coincide.

## Closed gates

- Canonical edge IDs use semantic endpoint IDs ordered by stable vertex ordinal.
  Cuboid/cube machine IDs use `A_prime`; `A′` exists only as `display_label`.
- Solid edges have one canonical visual owner. `SOLID_FACE` is the only default
  occluder; base, section, cutting-plane and auxiliary surfaces do not occlude.
- Product visibility and the independent oracle agree on exact visible, hidden
  and mixed ID sets and on span transitions within `0.5` physical pixel for all
  measured neutral and rotated states. There are zero ID-set and span mismatches.
- The analytic projected-interval oracle uses clip-`w` perspective correction.
  Its independent ray–triangle reference has zero disagreements. The strong
  perspective and small-occluder fault regressions pass.
- Oracle dependency, duplicate-owner, stale-orbit, hidden-span, dash-overwrite,
  incorrect-surface, untyped-formation and anonymous-section-endpoint fault gates
  are registered and pass their targeted tests.
- Formation emits explicit semantic kinds and ordered geometry progress. Section
  provenance distinguishes solid vertices from solid-edge intersections;
  authoritative evidence contains no anonymous endpoint fallback.
- Targeted gates passed: 10 frozen/oracle backend tests, 20 frontend hidden-line
  and fault tests, 10 Node evidence tests, and 28 candidate/cache tests.
- Production TypeScript/Vite build passed from the detached candidate worktree.

## Verification failures retained as evidence

The authoritative browser run passed all semantic, causal, formation, dash,
owner, API and console assertions. It failed one performance assertion on mobile
for five families: `OrbitControls` damping still changed the camera after auto-fit,
so the harness called moving frames “immutable” and observed valid recomputation.
Only rectangular pyramid reached zero recomputation during its 120-frame window.

Frozen identity then failed for desktop triangular prism and cube. Their oracle
visibility sets still exactly equal the reviewed sets, but raw terminal damping
floats produced different camera hashes. The runner emitted
`FROZEN_CAMERA_IDENTITY_MISMATCH` with proposed oracle diagnostics and did not
modify `human_expected_visibility.json`.

Full verification also remained red:

- Frontend: 904 passed, 1 failed. A legacy whole-source regex forbids the word
  `boundary` and now matches the required `boundary_edge_ids` contract.
- Backend: 6,268 passed, 35 failed, 1 skipped, 1 deselected. Failures include
  historical candidate/report/hash guards, live-case runner fixtures and legacy
  Scene3D golden hashes.
- The full-gate wrapper itself could not locate a backend venv inside the detached
  worktree; backend was therefore rerun directly with the repository venv and the
  counts above are from that authoritative standalone run.

These failures are not promoted into occlusion-oracle failures: exact product vs
oracle visibility and the perspective reference cross-check both passed.

## Worktree recovery

All five pre-existing evidence worktrees were inventoried before removal:

- `DUPLICATE_OF_CANONICAL = 244`
- `UNIQUE_DIAGNOSTIC = 153` (copied under `worktree-recovery/recovered/`)
- `GENERATED_BUILD_OUTPUT = 331`
- `REQUIRED_EVIDENCE_NOT_CANONICALIZED = 0`
- `UNKNOWN_ARTIFACT_COUNT = 0`
- `UNIQUE_COMMITS_AT_RISK = 0`
- `TEMP_WORKTREES_FOUND = 5`
- `TEMP_WORKTREES_REMOVED = 5`
- `TEMP_WORKTREES_RETAINED = 0`

Each removal happened only after SHA verification, recovery commit `09934eb7`,
HEAD reachability, and a clean status. Dependency junctions were removed as links
without traversing their shared targets. The detached measurement worktree was
also removed after its 153 generated artifacts matched commit 7 byte-for-byte.

## Final-decision precedence

1. Repository/base safety: pass.
2. Exact product/oracle edge IDs and spans: pass.
3. Oracle independence and perspective reference: pass.
4. Formation semantics and section identity: pass.
5. Recovery required/unknown counts: pass (`0` / `0`).
6. Candidate/cache/schema/full-test/browser gate: **fail**.

Therefore:

`FINAL_DECISION = VERIFICATION_NOT_CLEAN`

Automation does not emit `READY_FOR_HUMAN_VISUAL_REVIEW` or `MERGE_READY`.

## Invariants

```text
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
DEFAULT_MODE = LLM_ONLY
CACHE_VERSION = 102
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
COMMITS_SQUASHED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES
```
