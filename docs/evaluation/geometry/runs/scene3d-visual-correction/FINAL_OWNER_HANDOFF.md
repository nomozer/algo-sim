# Final Owner handoff — Scene3D visual correction (Claude takeover of Codex)

Authorization `GO_CLAUDE_TAKEOVER_SCENE3D_VISUAL_CORRECTION_LOCAL`, 2026-10-25.

**Status: `SCENE3D_VISUAL_PARTIAL_WITH_GAPS`.** The code is stable, and the candidate passes Full T3 and every browser
check run here. But the official Visual suite is still 7/8 (gate red), and the run has gaps listed in §21. So it is not
`READY_FOR_OWNER_REVIEW`.

| Item | Value |
|---|---|
| Branch | `research/scene3d-visual-correction`, local only. Not merged, not pushed; no history rewritten |
| Candidate | freeze `c84e8620`, product `b8b3311b` |
| Measured system | `ee474c81…` (118 files, unchanged: `backend/app` untouched) |
| `CACHE_VERSION` | 129, not bumped (UI-only change) |
| `main` | `9978e512`, unchanged |
| Route defaults | `LLM_ONLY`, `RESPONSE_CONTRACT=flat`, `ALLOW_LIVE_AI=0`, 0 model calls in the whole campaign |
| Hybrid production | NO-GO |
| 27 publication exceptions | not approved |
| Reviews | `INDEPENDENT_REVIEW_PENDING`; `HUMAN_VISUAL_APPROVED = PENDING` |

## Reports

| Report | File |
|---|---|
| Takeover record | `TAKEOVER_FROM_CODEX.md` |
| Renderer changes | `SCENE3D_VISIBILITY_CORRECTION.md` |
| Owner HTML comparison | `HTML_REFERENCE_COMPARISON.md` |
| Family matrix | `GEOMETRY_FAMILY_VISUAL_MATRIX.md` |
| Official suite | `OFFICIAL_VISUAL_SUITE_RESULTS.md` |
| Browser acceptance | `BROWSER_VISUAL_ACCEPTANCE.md` |
| Dev server | `VITE_DEV_SERVER_VERIFICATION.md` |
| Reviews | `REVIEW_REPORT.md` (+ `review/`) |
| Hybrid next phase | `HYBRID_NEXT_PHASE.md` |
| Codex's plan (unchanged) | `plan.md` |

## Commits on the branch (after `fe5f40b7`; no `Co-Authored-By` trailer)

| Commit | What |
|---|---|
| `60e569d3` | **Codex's work, byte-for-byte** (11 tracked files + run plan, tools, evidence) |
| `093c0b4c` | Claude: rim render queue, 1 px rim stroke, round-1 review fixes, role-aware oracle |
| `78aaef2f` | Claude: round-2 review fixes |
| `c9b5d00b` | probe: per-row isolation, recorded single retry |
| `9795567a` | evidence, reviews, draft reports |
| `3c6d1e65` | freeze (superseded) |
| `b8b3311b` | **fix: restore the locked Mode B reveal** |
| `8ad4bd40` | evidence of the 0/8 run and T3 at `3c6d1e65` |
| `c84e8620` | **freeze (current candidate)** |
| later | docs only (this handoff, index write-back), so T3 was not re-run |

## Answers

**1. Did Claude find the workspace Codex actually worked in?** Yes. It is `.superpowers/worktrees/scene3d-visual-correction`,
branch `research/scene3d-visual-correction` at `fe5f40b7`. Codex's session log confirms it.

**2. How many files, and in what state?** At takeover nothing was committed and nothing was staged.

| State | Count |
|---|---|
| Modified tracked files | **11** |
| Untracked | **318** (`plan.md`, 3 tools, 314 evidence files) |
| Ignored | 2 (`.superpowers/vitest-*.json`) |

The "15 files" in the brief are the 11 tracked files plus `plan.md` and the 3 tools. All were committed in `60e569d3`.

**3. Was any Codex line or artifact lost?** No.
- Before any edit, Codex's tracked diff and untracked files were preserved (`TAKEOVER_FROM_CODEX.md` §2).
- The staged Codex commit was checked against those hashes: 11/11 tracked files identical modulo Git's LF
  normalisation, and 317/317 untracked files identical.
- `browser-matrix.mjs` went in from the archive at Codex's original bytes. Claude's later edit to it is a separate
  commit.
- Nothing of Codex's was deleted.

**4. What had Codex finished?**
- Done and verified: Git state and reading.
- Implemented but not verified: exact curved occlusion, tangent silhouettes, hover ≠ selection, reference execution,
  before/after capture.
- In progress: role-aware checker (21/30), Mode A/B in the DOM.
- Not started: dev server, official suite, freeze/T3, review, reports.

Table: `TAKEOVER_FROM_CODEX.md` §4.

**5. What did Claude add?**
- **Two renderer fixes found by measuring:** the selected rim is drawn over solid outlines, and curve rims no longer
  vanish edge-on.
- **Fixes for two internal review rounds:** a stray ring at the origin, duplicate cap rims, inscribed polyhedra fully
  dashed, two latent crashes, and the tolerances of the arc check.
- **Restoration of the locked Mode B reveal**, which Codex had broken (0/8 → 7/8).
- **A complete role-aware checker:** arcs, a three-way verdict, fault counting only on certified views, a hardened
  probe.
- **All the gates, the evidence and the reports.**

**6. Where was the review interrupted?** Codex announced `requesting-code-review`, but no reviewer was ever dispatched.
Its next action was a checkpoint commit, and the session ended there. No Codex review output exists.

**7. Which command did auto-review reject? Did it affect a gate?**
- The rejected call was Codex's escalated `git add` of its 11 files, followed by `git commit -m 'fix(scene3d): correct
  curved visibility, contours and answer presentation'`.
- The reason was the auto-reviewer's **usage limit**: "a review failure, not a determination that the action is
  unsafe".
- No gate was affected. Nothing was executed, and Claude committed the same file set in `60e569d3` after verification.

**8. Are solid and dashed lines correct under camera rotation?**

Yes, for everything measured.
- **Curved occlusion:** an exact ray/finite-volume test for sphere, cylinder and cone (any axis, caps, cone slope).
  The tests run 3 × 48 camera positions against an independent normal.
- **Tangent silhouettes:** they follow the camera.
- **Hidden curve arcs:** dashed. They no longer disappear when seen edge-on.
- **Browser:** 5 cameras × 2 widths for 26 scenes.

One convention is left to you (decision B below): free segments inside a sphere are dashed, and polyhedron edges are
not.

**9. Which families are done?**

Rendered correctly in the browser at both widths (52/52 rows):
- the 7 backend polyhedron families (+ cube in the suite);
- 5 legacy curved samples: sphere cut, oblique cylinder, cylinder section, cone generator, cone axial section;
- audit families 01–12, including multi-solid, cone frustum cut and cylinder ellipse section;
- the circumsphere fixture.

This is rendering, not Hybrid support. The capability matrix is unchanged: 0 FULL_E2E, 9 PARTIAL, 7 RENDER_ONLY,
2 UNSUPPORTED.

**10. Are cylinder, cone and sphere right, and close to the Owner HTML?** Geometrically right, and correct more often
than the reference.

- **Exact where the reference approximates.** Occlusion is exact where the reference samples. The cone silhouette is
  exact where the reference reuses the cylinder formula. Any axis orientation is supported, while the reference assumes
  a vertical axis.
- **Taken from the reference:** a stroke that keeps its width when seen edge-on (the reference uses tubes; we use a
  1 px line), 12 % shell, dashed hidden arcs, and the colour roles.
- **Visible differences:** our strokes are thinner than the reference's tubes, and there are no geometry sliders. Both
  are by design: R0, and invariant #31.

Whether this is "close enough" is your visual call (question 19). Details: `HTML_REFERENCE_COMPARISON.md`.

**11. Are symbols, labels, opacity and colour right?** In code, yes:

| Role | Value |
|---|---|
| Edges | navy `#1e293b` |
| Hidden edges | `#64748b`, 0.78 |
| Shell | 0.12 |
| Section fill | terracotta `#c85a32` at 0.32 |
| Auxiliary / plane | purple `#6d28d9` |
| Selected section boundary | cobalt `#2563eb` |

The locked suite asserts labels, annotations after rotation and resize, and vertex markers on 8 families. All pass.
Right-angle marks are not checked by any automated test in this run. Appearance needs your approval.

**12. Visual suite score?** **7/8** at `c84e8620`, desktop + mobile, one run. Not 8/8. The intermediate candidate
`3c6d1e65` scored 0/8 because of the Mode B regression, which is now fixed.

**13. Is F2 resolved according to policy?**
- **The renderer follows F2:** terracotta fill, cobalt selected boundary. The role-aware check certifies this on
  19 views and catches 95/95 injected faults on them.
- **The locked hue gate still contradicts F2.** It fails `cross_section` because it counts the terracotta fill.
- **Status:** `F2_POLICY_DECISION_REQUIRED` (decision A). The locked oracle was not edited.

**14. Mode A/B?** **PASS** under the locked contract.

| | Result |
|---|---|
| Mode A | nothing shown, 52/52 |
| Mode B, «Kết quả» row | the answer once, with its value |
| Mode B, analysis panel | states the answer |
| Mode B, canvas | the selected result's annotation is shown |
| Mode B, inspector | links instead of repeating: 0/9 repeats, 9/9 links |
| Locked suite | `mode_b_reveal` and `selection_per_quantity` pass in all 8 families |

**15. Does `npm run dev` still hit EPERM?**
- On the candidate checkout, no. Start, restart and `--force` re-optimisation all passed, with HMR and 0 EPERM.
- Plain `npm run dev` exits only because port 3000 is held by another agent's Vite: the designed `strictPort`
  behaviour, not EPERM.
- **The root checkout still has the old config** until `88a1b43e` reaches its branch.
- New trap: Codex's worktree has a Codex-owned `.vite-cache` and `dist`.

**16. Candidate freeze and Full T3?** **PASS.**

| Item | Value |
|---|---|
| Freeze | `c84e8620`, `--verify` exit 0 |
| Full T3 | `FULL_PRODUCT_GATE_PASS` at `c84e8620`, in the clean detached Bunny-owned worktree `.superpowers/worktrees/svc-cand` |
| pytest | 11 923 passed, 1 skipped, 15 xfailed |
| vitest | 1378/1378 |
| Build / typecheck | passed |
| Tree | clean before and after |
| Post-freeze verify | exit 0 |
| Receipt | `verification/full-t3/t3-c84e8620/` |

**17. What did the internal reviewers conclude?** Two fresh-context agents reviewed the code. They are internal, not
independent.

- **Round 1:** 1 Critical, 4 Important and 6 Minor findings. The critical one was a stray ring drawn at the scene
  origin. The important ones were duplicate cap rims covering the selected section, inscribed polyhedra fully dashed,
  an arc check that was too loose, and the UNCERTIFIABLE share.
- **Round 2:** 0 Critical and 4 Important findings: the top rim of a cylinder given by height, tilted-axis dedupe,
  hide/isolate in the dedupe, and the split occlusion convention.

All were fixed with RED-first tests or reported, except the one that needs your decision (B). Neither round caught the
Mode B over-hiding; the locked suite did. `REVIEW_REPORT.md`.

**18. Is there a real independent review?** **No.** `INDEPENDENT_REVIEW_PENDING`.

**19. Which images does the Owner need to approve by eye?** Under `verification/`:

- `after-b8b3311b/`: 52 scenes × 7 frames. Suggested first look:
  - `tru-truc-xien-*-quarter-unselected.png`;
  - `family10_cone_frustum_cut-1440-default-unselected.png`;
  - `scene3d-circumsphere-fixture-1440-default-unselected.png`;
  - `cross_section-390-default-selected-mode-b.png`.
- `role-aware-b8b3311b/ellipse-cylinder-p6-*-none.png`: the selected ellipse boundary at 5 cameras.
- Before/after pairs: `before/` vs `after-b8b3311b/` (oblique cylinder, sphere cut, cone generator).
- The Owner reference screenshots in `reference/`, for comparison.

Watch items: the 1 px rim stroke against coplanar fills (round-2 minor), and stroke weight compared with the
reference's tubes.

**20. Is the branch eligible for a merge into local main?** **Not yet.** Code-wise it is a clean candidate (T3 PASS,
freeze verified, Hybrid disabled, backend unchanged). Still needed:

- decision A (F2 / the 7/8 gate);
- decision B (occlusion convention);
- your visual approval;
- the independent review, if you require it for merge.

No merge or push was done.

**21. Remaining blockers and gaps.**
1. **Official suite 7/8:** the F2 hue gate (decision A).
2. **Curved-occlusion convention** is split (decision B).
3. **`HUMAN_VISUAL_APPROVED = PENDING`, `INDEPENDENT_REVIEW_PENDING`.**
4. **Coverage gaps in this run:**
   - no injected wrong point name in the browser;
   - no automated right-angle-mark check;
   - mobile family matrix at DPR 1;
   - family 13 (refusal record) is not applicable to the matrix tool.
5. **The role-aware check** certifies only 4/10 ellipse views and 5/10 circle views, because labels cover the boundary
   in the others. A hidden arc may lose up to about 40 % of its ink and still pass. It shares the renderer's curve
   discretisation.
6. **Root checkout** still has the old Vite config. Codex's worktree has Codex-owned `.vite-cache` and `dist`.
7. **CPU cost:** rim visibility rebuilds the occluder triangles 96× per rim per camera change (round-1 M3).

**22. After the visual work, what does backend Hybrid still lack to replace `LLM_ONLY`?**
- D-10 (presentation only from certificates, on the decided renderer);
- D-04 (a new pre-registered held-out extraction set);
- family coverage (0 FULL_E2E);
- D-08/D-02/D-12 (serve behind the flag through `/api/analyze`, route cache, rollback);
- D-11 (paired live measurement with an Owner GO);
- D-13 (your decision).

Order and detail: `HYBRID_NEXT_PHASE.md`.

## Owner decisions needed

| # | Decision | Options |
|---|---|---|
| A | F2 vs the locked hue gate (`cross_section` 7/8) | amend the locked gate to role-aware semantics, adopt the role-aware check (proposal) as the gate, or change F2 |
| B | Curved solids and interior lines | keep as is (polyhedron edges follow faces only; free segments and section borders inside a sphere are dashed, as in the reference), or make free segments follow the polyhedron rule |
| C | Visual approval | approve, or list frames to fix |
| D | Merge | after A–C (and independent review if required): a disabled-state merge of this branch into local `main` |

## Workspace state

| Workspace | State |
|---|---|
| `.superpowers/worktrees/scene3d-visual-correction` | this branch, clean apart from ignored `.superpowers/` scratch. Codex's Vite (`:3156`, `CodexSandboxOffline`) still serves it; not touched |
| `.superpowers/worktrees/svc-cand` | detached at `c84e8620`, clean; `node_modules` is a junction to the root install (`rmdir` the junction before any `git worktree remove`). Holds ignored T3 stdout and the official-run output |
| Root checkout | `research/hybrid-wave3a-volume-reasoning` `fe9f5554`, 27 dirty paths, untouched |
| Not touched | other agents' processes (Vite `:3000` PID 19484, uvicorn `:8000`), ACLs, old worktrees, the Codex sandbox |
| Claude's Vite `:3161` | stopped at the end of the run |
