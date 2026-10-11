# Main integration readiness

Status: `ALGOSIM_MAIN_INTEGRATION_READY_FOR_FINAL_APPROVAL`

Scope:
- **Branches:** `feat/geometry-library-expansion` and the new `integration/geometry-functions`. Both point at the same commit after the final docs commit.
- **Constraints kept:** LIVE GEMINI CALLS = 0. No PR, no merge or push of `main`, default `LLM_ONLY` (`CACHE_VERSION` 125) unchanged.
- **History untouched:** the locked A/B candidate `12da4768…` and its evidence, and every v1/v2 orbit artifact, are unchanged.

## 1. Orbit gate: v3 validated; `main` itself is red because of a product defect

| Version | Change | Validation (pre-registered) | Status |
|---|---|---|---|
| v1 | 700 px drag, read at 250 ms | — | red on `main`: canvas 545→683 px plus truncated damping (`final-integration-gates`) |
| v2 ([protocol](../orbit-gate-v2/protocol.md)) | drag 1.25 × canvas height, `settleCamera` wait | known-good **TRUC_TROI** ×3; injections refused | **failed its validation**, kept on record |
| v3 ([protocol](../orbit-gate-v2/protocol-v3.md)), registered after the user's decision | angle-weighted axis consistency; settle = every per-frame rotation < 0.01° over 30 rAF frames, 20 s budget | historical `eb6d7d5a` **DAT ×3**; azimuth-wall injection `KHONG_DU_VONG` ×3; auto-rotate injection `KHONG_ON_DINH` ×3 | **validated, current** |

**Unchanged in every version:** thresholds (360°, 0.99, 0.9, 25°). The default output went to `scene3d-orbit-gate/v3/`, so the v1 files are not overwritten. A mutant with unweighted axes is killed by the node test (10/10 green).

**A v3 batch that does not count.** One v3 batch ran while vitest, `tsc -b` and an edit ran in parallel. It came out `KHONG_ON_DINH` everywhere plus a Chrome `WS_OPEN_TIMEOUT`. It is kept as `results-v3-invalid-concurrent-load/` and not counted. The clean rerun is `results-v3/`.

**v3 on `main` 28ac1d61, the candidate and the integration branch** (identical):

| Run | p1 (pyramid section + distance) | p6 | p7 |
|---|---|---|---|
| batch p1 → p6 → p7 | KHONG_ON_DINH, allocations 111 | KHONG_ON_DINH | KHONG_ON_DINH |
| each alone (`main`) | KHONG_ON_DINH, allocations 111 | **DAT** | **DAT** |
| p6 → p1 (`main`) | TU_KHOP_KHUNG, allocations 105 | DAT | — |
| historical p1 alone | DAT, allocations 0 | | |

**Product finding (pre-existing on `main`, not caused by this line):**
- Orbiting the p1 scene allocates GPU resources and its camera does not settle.
- Scenes loaded **after** it in the same session do not settle either.
- Root cause UNKNOWN. Hypothesis to check first: camera-dependent hidden-line recomputation or automatic fitting that is not disposed on scene change.
- Out of scope here; recorded as an open issue. The validated gate will tell when it is fixed.

## 2. The 31 untracked files in the main checkout

- **Inventory:** 31 files, 493,448 bytes, all **byte-identical** to the branch's tracked copies (raw bytes, not only after CRLF normalisation). None was locked.
- **Backup:** `D:\Documents\projects\algo-sim-backups\20261011-hybrid-ab-pilot-readiness-untracked\` (`files/`, `MANIFEST.json`, `RESTORE.md`), verified 31/31 by sha256 and not deleted. Manifest copy: `diagnostics/untracked-backup-MANIFEST.json`.
- **Removal from the main checkout: STOPPED, nothing deleted.**
  - The files and `docs/evaluation/geometry/runs` are owned by `DESKTOP-SCQFJL8\CodexSandboxOffline` (another agent's sandbox account). The current user `bunny` has only `Users` rights there (Write, ReadAndExecute), with no Delete.
  - A first deletion script printed `removed=31` although every delete was refused; the count was wrong and the files are intact.
  - Changing ownership or ACLs was not done (security change, not authorised).
- **Merge impact:**
  - Under `runs/` the branch only **adds** 294 files, and `bunny` can create files there (probe created and removed).
  - The other 23 changed files are owned by `bunny`.
  - So the only blocker is these 31 collisions, which an account with Delete rights must remove (see the handoff).

## 3. Intermittent test

**Test:** `test_cross_section_fixture_preserves_verifiable_measurement_provenance`. No new failure this wave: integration T3 and the earlier full runs were green.

| Item | Status |
|---|---|
| Test | kept active; no skip, no retry |
| On failure | reports the child's exit code, stdout and stderr (UTF-8) |
| Cause | UNKNOWN (1 of 9 full runs before this wave) |
| Open risk | an unexplained full-suite red may recur; its next occurrence will carry its own evidence |

## 4. Screenshots and harness versus product

Captures: 17 screenshots in `screenshots/`, `diagnostics/capture-info.json` and `diagnostics/capture-acceptance.mjs`.
- **Source:** built from the integration commit `49cf739e` (`git archive`, no worktree touched).
- **Coverage:** tetrahedron S.ABC with and without projection; A/B/C onto the opposite face; square-pyramid intersections and projections; desktop, auxiliary on, mobile 390 px.

| Label | Scope |
|---|---|
| VERIFIED_BY_AUTOMATED_TEST | topology labels, K/H coordinates, witness = exact foot, witness only once the point is present, A/B scene equality |
| AGENT_VISUALLY_INSPECTED | see below |
| HUMAN_ACCEPTANCE_PENDING | every scene; nothing is recorded as accepted |

What the agent inspected:
- S stays the apex and ABC the base.
- The perpendicular AK and its right-angle marker are anchored at K.
- **Colour change found and fixed in this wave (`74df2a78`).** The always-on perpendicular was drawn in `MAU_VAI_TRO.dich`, the W12 "under consideration" blue. It now uses the auxiliary-line colour; a selected distance witness keeps the blue.

**Harness versus the real product**, on the same p1 fixture scene:
- The renderer's colours and materials are JS constants, and the harness and the product mount the same `Scene3DWorkspace`, so the geometry, plane, section, auxiliary line and dashed hidden edges match.
- The product app shows warm-tinted faces at its final step while the harness shows the default grey.
- The `main` 28ac1d61 product app shows the **same** tint. It is product UI state, not a change made by this line.
- The geometry-functions route is not wired into the product UI, so its scenes are reviewable only in the harness.

## 5. Integration branch and gates

**Branch:**
- `integration/geometry-functions` was created from `main` 28ac1d61 and **fast-forwarded** (`merge --ff-only`) to the verified line.
- No cherry-pick or merge commit; every fix stays in ancestry.
- The candidate was refrozen there (`49cf739e`): product `74df2a78` under the named rule, tree `a8dc02fc` (110 files). `--verify` had flagged exactly `product_commit_sha`, the W12 protection working as designed.

| Gate on `integration/geometry-functions` (clean worktree) | Result |
|---|---|
| T3 `npm run test:full` at `49cf739e` | **FULL_PRODUCT_GATE_PASS**: pytest 8198/0 (1 skipped, 2 deselected), vitest 1051/1051, typecheck + build, demo set, crash surface 6/6 |
| Orbit gate v3 (validated) | red, identical to `main` (§1) |
| Candidate verify | exit 0 |
| Node tests (orbit gate) | 10/10 |
| Docs audit | PASS (docs/telemetry/identity/matrix 119/119; 0 broken links; EVIDENCE_INDEX and OPEN_ISSUES valid; CODE_INDEX sync 3/3) |

## 6. Worktrees

**Before:** 3 registered (main, `geometry-library-expansion`, the `main-integration` created this wave). **After:** 2.

- `main-integration` removed with `git worktree remove` (no `--force`), after:
  - its `node_modules` junction was removed with `rmdir` (target intact 72/72);
  - no process was using it;
  - its status was clean;
  - its ignored content was only `dist`, `algosim.db` and caches.
- Freed 1,732,866,048 bytes.
- The branch is kept.
- Scratch junctions removed; no reparse point left.
- Other `.superpowers/` folders (`brainstorm`, `builds`, `scratch`, `sdd`) are outside the requested scope and were not touched.

## 7. GO / NO-GO for merging `main`

The code is **GO for a fast-forward of `main` to `integration/geometry-functions` once you confirm final acceptance**:
- T3 passes on the exact integration commit.
- The candidate is frozen and verified.
- The orbit gate is now a validated instrument; its red is identical on `main` and is not introduced by this line.

| Before or alongside the merge | Status |
|---|---|
| Your visual acceptance (`screenshots/`) | pending |
| Removal of the 31 Codex-owned files by an account with Delete rights (backup verified) | **required, otherwise the fast-forward refuses** |
| The p1 orbit product defect | open issue on `main`; does not block this merge, but `main` stays red on the browser gate until it is fixed |
| Live pilot | NO-GO |
| Default switch | NO-GO |
