# Final Owner handoff — Codex visual closure + Claude takeover + Hybrid B3

Authorization `GO_CLAUDE_CONTINUE_CODEX_VISUAL_HYBRID_B3_LOCAL_ONLY`, 2026-10-25. Stops at the Owner gate.

**Status: `VISUAL_HYBRID_B3_PARTIAL_WITH_GAPS`.** Both candidates pass Full T3. The gaps are not machine failures:
the official Visual suite is 7/8 because of a locked hue policy that needs an Owner decision, the sphere sample
(P3) is open, no independent review or human visual approval exists, and the B3 slice has no browser row yet.

## Reports

| Report | Location |
|---|---|
| Takeover checkpoint | [`../visual-closure-hybrid-readiness/CODEX_TO_CLAUDE_TAKEOVER_CHECKPOINT.md`](../visual-closure-hybrid-readiness/CODEX_TO_CLAUDE_TAKEOVER_CHECKPOINT.md) |
| T3 failure root cause and recovery | [`../visual-closure-hybrid-readiness/T3_FAILURE_ROOT_CAUSE_AND_RECOVERY.md`](../visual-closure-hybrid-readiness/T3_FAILURE_ROOT_CAUSE_AND_RECOVERY.md) |
| Final visual closure (Codex) | [`../visual-closure-hybrid-readiness/FINAL_VISUAL_CLOSURE_REPORT.md`](../visual-closure-hybrid-readiness/FINAL_VISUAL_CLOSURE_REPORT.md) |
| Official suite F1/F2 (Codex) | [`../visual-closure-hybrid-readiness/OFFICIAL_SUITE_F1_F2_REPORT.md`](../visual-closure-hybrid-readiness/OFFICIAL_SUITE_F1_F2_REPORT.md) |
| 18-family matrix (Codex) | [`../visual-closure-hybrid-readiness/HTML_18_FAMILY_CAPABILITY_MATRIX.md`](../visual-closure-hybrid-readiness/HTML_18_FAMILY_CAPABILITY_MATRIX.md) — delta in the B3 report |
| B3 vertical slice | [`B3_VERTICAL_SLICE_REPORT.md`](B3_VERTICAL_SLICE_REPORT.md) |
| Default migration readiness (Codex) | [`../visual-closure-hybrid-readiness/HYBRID_DEFAULT_MIGRATION_READINESS.md`](../visual-closure-hybrid-readiness/HYBRID_DEFAULT_MIGRATION_READINESS.md) — delta below (§13) |
| Codex's unfinished handoff draft (placeholders) | [`../visual-closure-hybrid-readiness/takeover/codex-scratch/FINAL_OWNER_HANDOFF.draft.md`](../visual-closure-hybrid-readiness/takeover/codex-scratch/FINAL_OWNER_HANDOFF.draft.md) |

Codex's reports were byte-copied from its staged package and not edited; where they name freeze `c84392c1`, the
correction is the re-freeze `c6bdfbcb` (§3).

## Answers

**1. Were all of Codex's uncommitted changes found?** Yes. Codex worked in a separate clone owned by
`CodexSandboxOffline` (`.superpowers/workspaces/visual-closure-hybrid-readiness`), not in a linked worktree. Its tracked
tree was clean (0 staged, 0 unstaged, 0 untracked); the work was in five commits `956b77f8..c84392c1` that existed only in
that clone. The "19 files" in the Codex UI were ignored scratch files under its `.superpowers/` (scripts, probes, draft
reports); all 1161 non-cache ignored files were hashed.

**2. Was any file or receipt lost?** No. The five commits were fetched into the root repository as
`research/visual-closure-hybrid-readiness` before any change. The 1161-file SHA-256 inventory was re-verified
(`sha256sum -c`, 1161/1161 OK) after packaging. Nothing in the Codex clone was moved, rewritten or deleted. Failed T3
receipts are kept.

**3. How was the manifest failure handled?** Root cause: the freeze ran at `53fe3d25` while the run fixtures later
committed with it were still uncommitted, so the manifest correctly recorded `cay_lam_viec_sach: false` and
`test_candidate_ghi_dung_commit_va_cay_sach` failed. The freeze was re-run on a clean tree at `c84392c1` and the manifest
alone committed as `c6bdfbcb`. Only the identity fields changed (product `53fe3d25`, measured hash unchanged). No
receipt or manifest was edited by hand.

**4. How was the `frontend/dist` ACL failure handled; were permissions changed?** The `dist` built by the sandbox user
could not be emptied by `Bunny` (Vite `rmSync` EPERM). It was left in place. T3 ran in `.superpowers/verify-visual-closure`,
a fresh clone owned by `Bunny` that Codex had created for this purpose, with no `dist`. No `takeown`, `icacls`, forced
delete or change of the T3 definition.

**5. Final candidates and measured hashes.**

| Candidate | Branch | Product commit | Freeze commit | Measured system (118 files) |
|---|---|---|---|---|
| Visual closure | `research/visual-closure-hybrid-readiness` | `53fe3d25` (frontend only) | `c6bdfbcb` | `8be632679307a94ce4525ad576a05a9eccffc8ba2bdbf02d4c7dc93c208b7c41` |
| Visual + B3 | `research/hybrid-b3-v2-distance-bridge` | `3524bec8` (bridge only) | `dd5e6748` | `7fbe45b24b41acbc73f8aacd6b8bf163e10172fc8b8d2c08ac8006a6d2dbd284` |

**6. Full T3.** PASS at both:

| Target | pytest | vitest | build | demo / crash surface | tree before/after | freeze verify |
|---|---|---|---|---|---|---|
| `c6bdfbcb` (01:45–01:53 UTC) | 11856 passed, 0 failed | 1354/1354 | PASS | PASS / PASS | clean / clean | match |
| `dd5e6748` (03:37–03:44 UTC) | 11891 passed, 0 failed | 1354/1354 | PASS | PASS / PASS | clean / clean | match |

Receipts: `../visual-closure-hybrid-readiness/verification/full-t3/receipt.json`, `verification/full-t3/receipt.json`.
Machine verification by the author, not independent review. The earlier Codex run (11855 passed, 1 failed, build
EPERM) is `FAIL` and kept.

**7. Are F1 and F2 still defective?** F1: closed (formula shown once in the analysis panel; inspector keeps identity and a
link; Mode A hides the answer). F2: product behaviour matches the Owner's choice (terracotta `#C85A32` fill, cobalt
`#2563EB` boundary when selected, transient hover, no geometry change), but the **locked** role-hue oracle counts the
terracotta fill as a violation in the selected state. The oracle was not changed. Owner decision required; Codex's
role-aware per-edge proposal, with a magenta fault that it detects and a failed first proposal kept, is in the F1/F2
report.

**8. Official Visual suite.** **7/8 PASS** on desktop 1440 and mobile 390; `cross_section` fails only `causal_closure` /
`evidence_gates` through the role-hue rule. Measured by Codex on product `53fe3d25` as a 3+5 aggregate with a
Playwright transport (assertions and thresholds unchanged). The B3 commit changes no frontend code and none of the
suite's fixture envelopes.

**9. Browser desktop/mobile.** All runs by Codex on product `53fe3d25`: official suite (above), Adapter /4 94/94 rows
PASS, refusal surface 21/21, orbit gate PASS (3 cases), hover restore byte-identical, 20 owner camera images. No new
browser run in the takeover. The B3 `/4` distance scene was **not** browser-tested.

**10. Independent review?** **No.** Codex and Claude are both authors. Owner-appointed review is PENDING; human visual
approval is NOT_GRANTED.

**11. 18 HTML families.** 0 FULL_E2E_VERIFIED, 9 PARTIAL, 7 RENDER_ONLY, 2 UNSUPPORTED (Codex's audit; unchanged by
B3). The sphere sample shows helper points H/U/W/A and hides the cutting plane: verified independently that this comes
from the envelope (free points carry `formation_roles: []` and `display_group: ['given']`, the plane carries
`CONSTRUCT_AUXILIARY_GEOMETRY`). Fixing it in the frontend would also hide points a problem really gives, so it needs
backend source authority — **P3 OPEN**.

**12. What general geometry capability did B3 add?** Canonical `typed-fact-next/2` distance goals now reach the existing
planner and exact engine on the `/4` route: point–plane distance, segment length, line–line distance, with the target
keys the `/3` adapter already defined. One 20-line function in the bridge, no new Geometry Function, no IR change, no
second engine. 35 tests with closed-form oracles (right and oblique prisms, renaming, scale, qualified refs, refusals
with pinned codes), six bridge faults injected and detected. Authored development cases only.

**13. What is still missing before replacing `LLM_ONLY`?** Codex's migration report stands (`HYBRID_DEFAULT_READY` not
established). Delta from this checkpoint: the canonical distance-goal gap is closed for the bridge; still required —
angle goals on `/4`; curved solids on the bridge; a `/4` browser row for distance scenes; Owner decision on the hue
policy; source-correct sphere presentation; extraction quality on an independent current-candidate holdout (UNKNOWN);
real independent review; Owner visual approval; shadow/canary/rollback evidence; explicit Owner GO. Default
`LLM_ONLY`, `CACHE_VERSION=128`, `ALLOW_LIVE_AI=0`, Hybrid production NO-GO, 0 live calls, 27 publication exceptions
untouched.

**14. Git, worktrees, branches, uncommitted files.**

| Item | State |
|---|---|
| `research/visual-closure-hybrid-readiness` (root ref) | `de49c592` — Codex commits + re-freeze + evidence package |
| `research/hybrid-b3-v2-distance-bridge` (root ref) | this commit, on top of `de49c592` |
| `main` | `9978e512`, unchanged; nothing merged or pushed; no history rewritten |
| Worktree `.superpowers/worktrees/b3-dist` | this branch, clean; `frontend/node_modules` is a **junction** to the root install — `rmdir` it before `git worktree remove` |
| Clone `.superpowers/verify-visual-closure` | owner Bunny, branch at `de49c592`, clean; its ignored `.superpowers/closure/t3-claude-c6bdfbcb/stdout.log` holds the full T3 log |
| Codex clone `.superpowers/workspaces/visual-closure-hybrid-readiness` | untouched; ACL-locked `frontend/dist` remains |
| Root checkout | `research/hybrid-wave3a-volume-reasoning` @ `fe9f5554`, 19 modified + 8 untracked paths of the owner — untouched |
| Processes | Codex's Vite `:3129` (PID 11120) and preview `:4179` (PID 10496), user `CodexSandboxOffline`, still running — not stopped (not Claude's) |
| ACL-locked, not removed | root `.superpowers/t3-closure-final/`, `t3-closure-temp/`; Codex clone `frontend/dist/` |
| Full T3 stdout of B3 | ignored `b3-dist/.superpowers/closure/t3-b3-dd5e6748/stdout.log` (sha256 `27c8c13488cdeb66db133d086659a1a1d73dfe86be1706b97a78406cb18f45f4`) |

**15. Ready for the Owner to consider a local `main` merge?** The branches are ready for **Owner review**, not for a
merge decision by the authors: every machine gate is green, but the Owner must first decide the F2 hue policy, accept or
defer P3, appoint an independent reviewer and give visual approval. If the Owner wants only the certified visual
closure, merge `research/visual-closure-hybrid-readiness`; `research/hybrid-b3-v2-distance-bridge` contains it plus B3.
