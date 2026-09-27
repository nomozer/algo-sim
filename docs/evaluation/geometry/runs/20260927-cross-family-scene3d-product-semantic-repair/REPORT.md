# Cross-family Scene3D product semantic repair

Status: `READY_FOR_HUMAN_VISUAL_REVIEW`

This wave repairs the product regression recorded by
`GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION`. Historical reports and
artifacts remain unchanged; the correction is additive.

## Identity

- Branch: `fix/cuboid-visual-semantic-closure`
- Start HEAD: `686a8e0e5f8540725c0a500429cc18a7faf1015a`
- Origin main at remote gate: `a9492ee98ff9dc3302d1ff64465f1c06e9001bce`
- Product commit: `5dd9f2b2851cdef64de0272f9a3d2b41bb05ad45`
- Product Git root tree: `16c1541796f8c57aea7633c4305588c5f361615b`
- Candidate measured-system hash: `5d8eb3af49a14a52e5fc3f9517ada06bbb4612711c0921b3ccdc1cb1971d4e2a`
- Measurement commit: `f5fefce02bf6f930c29b58a12979340ac2affe5d`
- Evidence commit: `5f2f24f064d8f06de41e76353fb61ff5a74e7afa`
- Cache: version `102`, fingerprint `b1714b566e25c912…`, unchanged
- Default mode: `LLM_ONLY`
- Live Gemini requests: `0`

The detached measurement worktree was checked to contain product paths byte-identical
to the product commit. The scenario manifest is tied to independent oracle source
hashes and the evidence run records zero application LLM calls.

## Product repair

The backend now emits learner-facing text, display labels, structured formula
references, typed numerical/structural/topological/layout dependencies, and exact
formation snapshots. Global `_last_base_sym` / `_last_height_sym` state is removed.
Numerical volume closure contains base area and height; solid topology remains
structural/topological context.

The frontend no longer falls back to raw machine IDs. Formation playback applies
exact visibility snapshots forward and backward. Each geometric edge has one
canonical visual owner; derived geometry is hit-only. Camera-relative visibility
renders visible edges solid and hidden edges dashed, while highlight changes only
color/weight. Orbit recomputes the visibility sets.

The browser harness captures default state before causal interaction, resets between
paths, requires semantic state and bounded canvas-pixel deltas, exercises trusted
orbit gestures, checks exact formation snapshots, and rejects all registered false
positive fault injections.

## Six-family browser evidence

All positive desktop/mobile and negative desktop/mobile scenarios passed for
triangular pyramid, triangular prism, rectangular pyramid, cuboid, cube, and
cross-section.

| Family | Visible / hidden edges | Formation steps | Desktop / mobile causal pixel ratio |
| --- | ---: | ---: | ---: |
| Triangular pyramid | 3 / 3 | 6 | 0.06357595 / 0.07216965 |
| Triangular prism | 6 / 3 | 6 | 0.09193658 / 0.13948424 |
| Rectangular pyramid | 5 / 3 | 8 | 0.06855182 / 0.08459928 |
| Cuboid | 9 / 3 | 9 | 0.09964647 / 0.15799325 |
| Cube | 9 / 3 | 11 | 0.10116392 / 0.16155010 |
| Cross-section | 5 / 3 | 13 | 0.11596234 / 0.18043555 |

Across all six families: mixed edge sets `0`, duplicate visual owners `0`, future
object leakage `0`, raw-token leaks `0`, unresolved formula references `0`, uncaught
exceptions `0`, failed API calls `0`, and serious console errors `0`. Every desktop
orbit changed projection and recomputed visibility. Every causal path changed the
selected state, closure, highlighted render owners, and bounded canvas pixels.

## Verification

- Focused backend Scene3D and product-route gates: pass.
- Full backend: 6,284 passed, 1 skipped, 1 deselected.
- Frontend Vitest: 62 files, 895 tests passed.
- TypeScript: `npx tsc -b` passed.
- Node browser-harness tests: 10/10 passed, including all registered fault injections.
- Production build: passed in the detached measurement and passed locally through a
  fresh isolated Vite output directory. The normal local `frontend/dist` output was
  locked by another process and returned `EPERM` during cleanup; compilation and the
  isolated production bundle both completed successfully.
- Schema export: two consecutive exports byte-identical at
  `d852b47c08b7ac0e2a41155366ac1ff88e7d08875cb1cfe718326c543b2951e7`.
- Cache identity and candidate verification: pass.
- Cross-section fail-closed contract: `PLANE_DOES_NOT_CUT`, pass.
- `git diff --check`: pass.

## Evidence integrity

- Scenario manifest SHA-256 as measured in the detached LF checkout:
  `a8041af72dc70df1e64efda7b857ec376a3a00a2ecbdfc6204f7180676760d58`.
- Scenario manifest working-copy SHA-256 on Windows (CRLF checkout only):
  `dcf8e5e6af73bb92afc2b0706b237c95e395d458cd54be5d0b3862543a163d04`.
- Contact sheet SHA-256:
  `76fccf5cbb9c240e7ebd25c420fadfefc8a5a60e35dbe858ec18169b2140a9d5`.
- The manifest excludes its own hash and does not claim the SHA of the commit that
  contains itself.

## Human visual review checklist

- [ ] Visible edges are solid.
- [ ] Hidden edges are dashed.
- [ ] Highlight preserves the existing solid/dashed class.
- [ ] No edge has overlapping solid and dashed render owners.
- [ ] Orbit changes projection and recomputes visibility.
- [ ] Default and causal captures differ only as intended.
- [ ] Formation genuinely adds/removes objects in both directions.
- [ ] Learner surfaces contain no machine IDs or snake_case.
- [ ] Formula symbols resolve to visible learner entities.
- [ ] Height is present in the numerical dependency closure for volume.

Automation stops here. It does not promote the result beyond
`READY_FOR_HUMAN_VISUAL_REVIEW`.
