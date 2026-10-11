# Final integration gates and worktree cleanup

Status: `ALGOSIM_FINAL_INTEGRATION_GATES_AWAITING_APPROVAL`

Scope:
- **Branch:** `feat/geometry-library-expansion`. The wave runs from `ee104a43` to the final docs commit.
- **No product code changed.** One test gained failure diagnostics; diagnostics, docs and local git configuration were added.
- **No live calls or main changes:** LIVE GEMINI CALLS = 0. No merge, push, PR or default switch (`LLM_ONLY`, `CACHE_VERSION` 125).
- **History untouched:** no historical artifact was rewritten.

## 1. Orbit gate: root cause found, product not at fault, gate red on `main` too

The gate (`frontend/scripts/scene3d-orbit-gate.mjs`) makes one 700 px horizontal drag, waits a fixed 250 ms, and requires the unwound azimuth to be at least **360°** (`NGUONG.VONG_NGANG_DO`).

Note on numbers: 437° was the value *measured* on 2026-09-11; it is not the threshold.

OrbitControls rotates `2π·dx/clientHeight` by design, so a fixed drag gives fewer degrees on a taller canvas.

Every row below is the same machine, the same viewport (1440×900, DPR 1), the same fixtures p1/p6/p7, and the gate's own drag replayed by `diagnostics/orbit-damping-probe.mjs`. Only the post-release wait varies:

| Build | Canvas height | Wait 250 ms (as the gate) | Wait 5000 ms | `360·700/h` |
|---|---|---|---|---|
| historical `eb6d7d5a` | 545 px | 433.5–440.8° | 462.4° | 462.4° |
| `main` `28ac1d61` | 683 px | 337.5–347.0° | 368.4–369.0° | 369.0° |
| pre-fix `c6a99ac6` | 683 px | 336.1–345.6° | 368.4–369.0° | 369.0° |
| current renderer | 683 px | 336.1–345.1° | 368.4–369.0° | 369.0° |

**Unmodified gate:**
- On the historical build: **DAT** today (433–438°).
- On `main`: **KHONG_DU_VONG** (338–346°). A first attempt on `main` returned `KHONG_DOC_DUOC_CAMERA` once, did not repeat, and is recorded.

**Root cause.** Two things combine:
1. The canvas grew from 545 to 683 px through layout commits of 2026-10-08/09 that are **already in `main`**: `c9bcdcdb`, `d8ad153b`, `95a56a17`, `45f5a7f0` and others among the 101 `frontend/src` commits since `eb6d7d5a`.
2. The 250 ms read cuts off the damping tail by about 24–33°. The old 437° margin used to absorb that.

**What this rules out.**
- **The camera.** It reaches exactly the OrbitControls-defined angle, about Z, with no snap and no azimuth wall.
- **The machine.** The historical build passes today on it.
- **This branch.** Main fails identically.

**Correction.** The previous wave attributed the failure to "the measurement environment". That is withdrawn by this report (`EVIDENCE_INDEX`).

**Not done.** The 360° threshold was not lowered, the gate was not edited, and it was not marked PASS.

**Proposed replacement acceptance (needs the user's approval; a new pre-registration, not a rescoring):**
- The drag is a fixed multiple of `clientHeight` (for example 1.25 × h, i.e. 450° by OrbitControls' own definition).
- Read only after the pose is stable for N frames (condition-based wait), not after a fixed 250 ms.
- Keep `VONG_NGANG_DO = 360` and every other threshold.
- Validate the new gate on a known-good window (historical build) **and** a known-bad injection (`ORBIT_GATE_TIEM_*`) before trusting it.

## 2. Intermittent backend test: cause UNKNOWN, now self-reporting

**Test:** `test_generic_tier_a_fixture_generator.py::test_cross_section_fixture_preserves_verifiable_measurement_provenance`.

**What was checked:**

| Check | Result |
|---|---|
| Full-suite runs since `811896f8` | failed **1 of 9** (the one red came from a generator subprocess exit ≠ 0, with stderr discarded by `check=True`) |
| Instrumented repetitions (`diagnostics/capture_generator_subprocess.py`, loaded with `-p`; no test changed during them) | 3/3 green. Each child: exit 0, empty stderr, 51 files, environment drift only `DATABASE_URL`/`PYTEST_CURRENT_TEST`. The `DATABASE_URL` drift is present in green runs too, so it does not explain the red |
| Isolated test runs | green |
| Direct generator runs | 6/6 green |
| Time dependence | none: no timeout or wall-clock dependence in the pipeline or generator |
| Code-page decoding | `text=True` decoded the child's UTF-8 with the console code page; possible garbling, but not a non-zero exit |

**Handling** (`d5f6784c`, no retry):
- Same pass/fail rule.
- A failure now reports the child's exit code, stdout and stderr, decoded as UTF-8.
- Fault injection (a fake generator exiting 3) confirms the evidence appears in the assertion.

**Status:** the issue stays OPEN until the next occurrence.

## 3. Windows long paths

| Checkout | Files over 260 characters |
|---|---|
| Main checkout `D:\Documents\projects\algo-sim\` | 0 (longest relative path 228 + 30 = 258) |
| A worktree under `.superpowers/worktrees/<name>/` | 153 |

The repository's own measurement protocol (clean detached worktree) needs it there.

| Setting | Before | After |
|---|---|---|
| local | UNSET | **`true`** (`.git/config`) |
| global | UNSET | UNSET |
| system | UNSET | UNSET |

Effect: the branch worktree's 151 phantom deletions disappeared (the files had always been present), and no file needed restoring.

## 4. Visual acceptance

- The renderer is unchanged since the 24 screenshots of `geometry-library-important-fixes` (`git diff 811896f8..HEAD -- frontend/src` is empty), and so is the product (candidate verify). Those screenshots and their checks remain valid:
  - S.ABC apex/base;
  - perpendiculars with their marker at the foot;
  - intersections;
  - formation order (witness and point appear together);
  - rotate, zoom, mobile.
- No educational-correctness blocker found.
- Cosmetic items move to the backlog: view-dependent label collision, a midpoint appearing before its segment.
- **HUMAN_ACCEPTANCE_PENDING:** not recorded as accepted.

## 5. Integration gates (latest commits)

| Gate | Result |
|---|---|
| **T3 `npm run test:full`, clean detached worktree at `ffe7fd68`** | **FULL_PRODUCT_GATE_PASS**: pytest 8198 passed / 0 failed / 1 skipped / 2 deselected; vitest 1050/1050 (68 files); typecheck + build; thesis demo set; demo crash surface 6/6. Log: `diagnostics/t3-full-gate-clean-ffe7fd68.log` |
| T3 in the branch worktree at `d5f6784c` (untracked evidence present) | FAIL, **invalid by protocol** (`test_holdout_readiness` sees a dirty tree). Disclosed, not counted |
| Geometry oracle, source grounding (35 test files), negative/metamorphic/mutation suites | inside the green pytest run |
| Candidate `--verify` | exit 0 at `ffe7fd68` (`a8dc02fc`, product `4ad89909`; only test/docs commits since the freeze, as the I2 rule intends) |
| Scene3D browser: orbit gate | **red**, root cause in §1, identical on `main` |
| Scene3D browser: visual harness | valid from the previous wave (§4) |
| Documentation audit | PASS (docs/telemetry/identity/matrix 119/119; audit: 0 broken links, CODE_INDEX current, EVIDENCE_INDEX and OPEN_ISSUES valid) |
| Not run | `photo-problem-browser-check.mjs` (photo flow untouched); live/provider checks (forbidden) |

## 6. Candidate identity

| Candidate | Hash |
|---|---|
| Current | `a8dc02fc…` (110 files, product `4ad89909`, rule `product-paths-excluding-test-only/1`) |
| Locked A/B | `12da4768…` (unchanged) |
| `main` | candidate of its own run (see `CURRENT_STATE`), unchanged |

## 7. Git integration readiness

**Ancestry:**
- `main` = `28ac1d61` is the merge-base; `main` has no commits since.
- The branch is linear on top of it: the 28 `text-to-geometry-functions`/hybrid commits, then expansion, review, fixes and this wave.

**Plan** (not executed):
1. Create `integration/geometry-functions` from `main`.
2. Fast-forward it to the branch HEAD.
3. Rerun T3 there; then the user decides `main`.

**Blocking file collision in the main checkout:** `docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/` exists there as 31 **untracked** files.
- They are byte-identical (CRLF-normalized) to the branch's tracked copies.
- A fast-forward there will refuse to overwrite them.
- Removing or keeping them is the user's decision; this run did not touch them.

`frontend/public/favicon.svg` (untracked) does not collide.

## 8. Worktree cleanup

**Before:** 8 registered (main + 7). **After:** 2 (main + `geometry-library-expansion`).

| Worktree | HEAD | Class | Action |
|---|---|---|---|
| `geometry-library-expansion` | branch | ACTIVE | kept |
| `geometry-library-expansion-verification` | `ddb0ce34` | REMOVABLE | removed |
| `…-verification-2` | `1bbd0edb` | REMOVABLE | removed |
| `…-verification-3` | `3b6104e3` | REMOVABLE | removed |
| `…-verification-4` | `815f06be` | REMOVABLE | removed |
| `hybrid-ab-pilot-readiness` | `2990d87d` | REMOVABLE | removed |
| `geometry-library-fixes-freeze` | `ffe7fd68` | REMOVABLE after T3 | removed |

Eligibility for each removed worktree:
- clean status;
- HEAD contained in at least one branch;
- ignored content only `__pycache__`/`algosim.db`/`dist`;
- no process using it.
- The `ALGOSIM_FROZEN_AB_WORKTREE` consumer of `hybrid-ab-pilot-readiness` was removed in I3; its evidence is committed.

How each was removed:
- `git worktree remove` without `--force` for all six, then `git worktree prune`.
- The `node_modules` junction in the freeze worktree was removed with `rmdir` first. The target was intact (72/72 package directories).
- The freeze directory itself was refused once (it was this shell's working directory). After that it held **0 files**, and the empty directory was removed with non-recursive `rmdir`.
- Two scratch junctions into `node_modules` were also removed; no reparse point is left in scratch.

**Freed:** 10,350,596,096 bytes (≈ 9.6 GiB) on D:. No branch was deleted.

## 9. Remaining blockers and user decisions

1. **Human visual acceptance** of the screenshots (`geometry-library-important-fixes/screenshots/`).
2. **Orbit gate.** Approve the replacement acceptance of §1 (it is red on `main` already), or another procedure.
3. **The 31 identical untracked files** in the main checkout, before any fast-forward there.
4. **Intermittent test:** cause UNKNOWN (1/9). Not a product signal so far, but OPEN.
5. Live pilot NO-GO; default switch NO-GO.

## 10. Recommendation for merging into `main`

**Product gate:** T3 PASS in a clean worktree; candidate verified.

**Recommendation: CONDITIONAL GO.** Merge only after these:
- item 1 (human visual acceptance);
- item 3 (the colliding untracked files);
- a decision on item 2, since the orbit gate red predates this line and is identical on `main`.

**Not ready on its own:** a merge right now, without those decisions, is NO-GO.
