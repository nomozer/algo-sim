# Final Owner handoff — F2 policy, review, B3 browser E2E, sphere source authority

Authorization `GO_LOCAL_F2_POLICY_REVIEW_B3_VERIFICATION_SPHERE_SOURCE_FIX`, 2026-10-25. Stops at the Owner gate.

**Candidate for Owner review: `integration/visual-b3-sphere-candidate`** (freeze `ddb1a4be`, browser evidence measured at `63faa5af`, this handoff at the branch tip) — one branch containing the
visual closure, B3 distance bridge, the review fixes, the ellipse fix, the sphere source fix and CACHE 129. Local only:
no merge into `main`, no push, no history rewrite. `main` = `9978e512`.

## Reports (this run unless noted)

| Report | File |
|---|---|
| F2 role-aware oracle decision | `F2_ROLE_AWARE_ORACLE_DECISION_REPORT.md` |
| Review result (separate-context, not independent) | `INDEPENDENT_REVIEW_RESULT.md` (+ `review/`) |
| B3 distance browser E2E | `B3_DISTANCE_BROWSER_E2E.md` |
| Sphere source authority fix | `SPHERE_SOURCE_AUTHORITY_FIX_REPORT.md` |
| Updated 18-family matrix | `UPDATED_18_FAMILY_CAPABILITY_MATRIX.md` |

## Answers

**1. Official suite 8/8 or 7/8?** **7/8** on the integrated candidate (desktop 1440 + mobile 390, one uninterrupted run,
inputs rebound with envelopes/oracles byte-identical). `cross_section` fails only `canvas_role_hues.cam` and the
dependent evidence gate; all other assertions pass.

**2. Was the locked oracle changed?** **No.** The role-aware check is a separate proposal. On real Chrome it passes 6/6
baselines (polygon/circle/ellipse × 2 viewports) and catches 30/30 injected faults (boundary → terracotta, → magenta,
fill → grey, fill hidden, wrong object). The separate-context review still lists five ways it can be fooled (colour
family not policy colour, a second smaller cobalt section, a 25 % edge gap, wrong eye frame on rotated/chart scenes,
cone normals). So it is not ready to replace the gate. The proposal's browser run also found and fixed a real product
defect (ellipse rim band flipped outside the curve on left-handed frames).

**3. Was the reviewer independent?** **No.** It was a fresh-context Claude subagent spawned by the author: it wrote no
code and had no access to the authoring conversation, but it is not Owner-appointed or organisationally independent.
Verdict as written: `PASS_WITH_FINDINGS`, 0 blocker. Its I-1/M-1/M-2 (silent plane truncation, degenerate operands) were
reproduced and fixed. I-2 (an unverified "chéo nhau" claim) and the oracle findings remain open. **Owner-appointed
independent review: PENDING.**

**4. B3 distance browser desktop/mobile?** **PASS 10/10** on the integrated tree: 3 served + 2 refused × 1440 / 390.
Each served answer squared equals the closed-form oracle (12, 24/5, 24). The answer-tied witness is drawn when provided
(D1 segment, D3 on the answer). Mode A hides the answer; Mode B shows it once on opening. The inspector adds no
number. Refusals show no scene and no code. Fault injection on the harness: 3/3 detected. Gaps: no witness for
skew-line distance; after selecting the answer it also shows in the inspector and as a canvas label. Offline authored
TypedFacts only; not an extraction-quality claim.

**5. Is sphere source authority correct now?** **Yes for the offline samples and the default-route formation role.**
Only I and R = 5 are given (R labelled by an InputFact). (S) is built from I + R, (P) from its equation and labelled.
Invented points A/H/U/W are gone (and the cylinder sample's invented rim point). The cutting plane of a curved solid is
`CONSTRUCT_CUTTING_OBJECT`, so (P) stays visible. Tangent / no-cut are the typed refusals `CURVED_PLANE_TANGENT` /
`CURVED_PLANE_DOES_NOT_CUT`, never a clamped circle. The integrated browser capture then exposed a learner-visible name
"…, qua đại lượng" for radius-declared solids; fixed in `display_names` (`9ced3d27`). Hybrid curved solids stay
refused (`BRIDGE_UNSUPPORTED_CURVED`).

**6. Did geometry / provenance / default route change?** Geometry kernel and exact engine: unchanged. Default route
stays `LLM_ONLY`, but its **served envelopes change** in two ways:
- the cutting plane of a curved section is now `CONSTRUCT_CUTTING_OBJECT`;
- radius-declared curved solids get a different name.

So `CACHE_VERSION` 128 → **129**, with a v128 cache probe (one replayed case differs only in that role; 3 controls
byte-identical), a migration test and a relocked cache identity. The model surface is unchanged (prompts, grammar card,
schemas, capability table all hash-identical). Hybrid route D: the B3 bridge maps distance goals with exact operands;
the default is unaffected. Provenance: the bridge stays a pure rename; Source Gate, planner and exact engine re-check.

**7. Candidate, tree hash, T3.**

| Candidate | Product | Measured (118 files) | Full T3 |
|---|---|---|---|
| **integrated `ddb1a4be`** (evidence `63faa5af`) | `9ced3d27` | `ee474c819688426f8959daf2129f0273eb3217f039909b8ad9cade0ed740ae9d` | **PASS** (11923 / 1359) |
| integrated `c57c7c05` (before the display-name fix) | `028e8282` | `665886e4…` | PASS (11920 / 1359) |
| F2 + B3 `8ef86b65` | `82097186` | `5f7daa66…` | PASS (11899 / 1356) |
| F2 + B3 `cb8d7c4a` | `3117d513` | `7fbe45b2…` | PASS (11891 / 1356) |
| sphere `98d52e90` | `54f15e92` | `5e353be2…` | PASS (11877 / 1357); `301692c8` FAIL kept (cache lock not relocked) |

**8. Ready for Owner visual approval and a disabled-state local main merge?** **Ready for Owner review, not
self-approved.** Every machine gate on the integrated candidate is green except the official suite's documented 7/8
policy conflict. Before a merge decision the Owner needs to:
- choose an F2 oracle path: keep the locked gate at 7/8, or authorise iteration 2 of the proposal with independent
  review;
- appoint an independent reviewer;
- give human visual approval;
- decide I-2 (the contract of `ask_distance_lines`) and the "answer in one place" interpretation in the selected state.

Hybrid stays disabled (`LLM_ONLY`, production NO-GO, `ALLOW_LIVE_AI=0`, 0 model calls). The 27 publication exceptions
are untouched.

**9. Branches / worktrees and what can be retired.**

All branches below are ancestors of the integrated branch. Nothing is merged into `main`, nothing is pushed.

| Branch / worktree | At | State | Retire safely? |
|---|---|---|---|
| `integration/visual-b3-sphere-candidate` — worktree `.superpowers/worktrees/b3-dist` | tip of this handoff | **the candidate**, clean | keep |
| `research/f2-oracle-b3-e2e` | `8ef86b65` | contained in the candidate | yes (ref only; the commits live on) |
| `research/sphere-sample-source-authority` — worktree `.superpowers/worktrees/sphere-src` (detached `98d52e90`) | `98d52e90` | contained; standalone it lacks the `display_names` fix, **do not merge it alone** | worktree yes after its ignored `.superpowers/closure/` T3 logs are kept or copied (their receipts are committed here) |
| `research/hybrid-b3-v2-distance-bridge` | `a2692503` | contained | yes |
| `research/visual-closure-hybrid-readiness` | `de49c592` | contained; also in the clone `.superpowers/verify-visual-closure` | ref yes; the clone holds ignored full T3 stdout of `c6bdfbcb` — keep until copied |
| Codex clone `.superpowers/workspaces/visual-closure-hybrid-readiness` | `c84392c1` | ACL-locked `frontend/dist`; its evidence is packaged and checksummed | **no** — sandbox-owned; leave to the Owner (never force-remove) |
| `integration/hybrid-visual-candidate` worktree | `1a4a0b93` | older candidate, untouched | Owner's call |
| root checkout `research/hybrid-wave3a-volume-reasoning` | `fe9f5554`, 27 dirty paths | Owner's own work, untouched | no |

Both worktrees created here (`b3-dist`, `sphere-src`) have `frontend/node_modules` as a **junction** to the root install: `rmdir` the junction before `git worktree remove`, never `-f`. Background processes left: my Vite dev server on `127.0.0.1:3142` (stops with this session); Codex's Vite `:3129` / preview `:4179` under `CodexSandboxOffline` — not mine, not stopped.

### Branch-specific limits

- Merging `research/sphere-sample-source-authority` without the integration commits would ship the radius-solid name "…, qua đại lượng". Merge the integrated branch, or nothing.
- The integrated branch carries a join divergence layer (`visual-b3-sphere-integration/inputs/candidate_divergence.json`, `corrects` = both predecessor layers) and a follow-up layer for the display-name fix; the correction chain test resolves to the latter.

## Addendum — `npm run dev` Vite EPERM (Owner requirement, same campaign)

Full report: `VITE_DEV_SERVER_EPERM_FIX.md`.

| Question | Answer |
|---|---|
| Cause | ACL conflict on ONE shared cache: `frontend/node_modules/.vite` of the root install is reached by every worktree/clone through junctions/symlinks; its files were created by the Codex sandbox (owner `CodexSandboxOffline`); `Bunny` may write but not delete there, and Vite deletes old chunks whenever it re-optimises. No process held the files. |
| Fix | `frontend/vite.config.ts` `cacheDir: ".vite-cache"` (one cache per checkout, owned by whoever runs it) + `.gitignore` `.vite-cache/`; commit `88a1b43e`. Old cache untouched; no ACL change, no deletion, no process killed, backend `CACHE_VERSION` untouched. |
| vite.config changed? | **Yes**, one option plus its comment. |
| Two starts | RED before: exit 1, EPERM. After: start 1 and start 2 ready (~0.3 s Vite, ~0.75 s from spawn), plus a `--force` re-optimisation round — no EPERM (`verification/vite-dev-server/`). |
| Hot reload | Works in all three rounds: browser console "[vite] hot updated: /src/styles/global.css"; probe edit restored byte-identical. |
| Other Vite servers | Passed with a second Vite server running on 3142; port 3000 keeps `strictPort`. |
| Still ACL-locked | root `frontend/node_modules/.vite` (Codex-owned, now unused by the fixed config); Codex clone `frontend/dist`; root `.superpowers/t3-closure-final`, `t3-closure-temp`. **The root checkout (old branch, old `vite.config.ts`) keeps failing until `88a1b43e` reaches it** — run the dev server from the candidate worktree meanwhile. |
| Effect on Full T3 / candidate | Config is outside `PRODUCT_PATHS` and the evidence `SOURCE_PATHS`: product `9ced3d27`, measured `ee474c81…`, freeze `ddb1a4be` unchanged; browser evidence not stale. Full T3 re-run: **PASS at `88a1b43e`** (11923 / 1359). Default route `LLM_ONLY` and Hybrid NO-GO unchanged. |

Status: **`VITE_DEV_SERVER_FIXED`** for any checkout that contains `88a1b43e` (verified twice plus a forced re-optimisation, with hot reload, on a clean committed tree); NOT yet in the root checkout's branch.
