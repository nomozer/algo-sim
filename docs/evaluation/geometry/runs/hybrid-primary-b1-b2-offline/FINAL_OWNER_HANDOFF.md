# Final owner handoff: Hybrid B1/B2 offline + Scene3D visual reference

Authorizations: `GO_AUTONOMOUS_HYBRID_B1_B2_LOCAL_DEVELOPMENT` (Codex), then `GO_HYBRID_B1_B2_TAKEOVER_AND_SCENE3D_VISUAL_RESEARCH_LOCAL` (Claude takeover), 2026-10-24.

**Classification:** `HYBRID_B1_B2_OFFLINE_E2E_COMPLETE` · `SCENE3D_VISUAL_SPEC_ONLY` · `LIVE_PROVIDER=NO-GO` · `HYBRID_DEFAULT=NO-GO` · `REMOTE_PUSH=NO-GO`.
Sub-status: `B1_EXTRACTION_INTERFACE_VERIFIED`, `B2_HYBRID_OFFLINE_ROUTING_VERIFIED`, `OFFLINE_NL_TO_SCENE3D_VERIFIED`, `LIVE_EXTRACTION_QUALITY_UNKNOWN`, independent holdout `NOT_EXECUTED`.

## Identity

| Item | Value |
|---|---|
| Branch | `research/hybrid-primary-b1-b2-offline` (local only; not pushed, not merged) |
| Baseline C0 | `5ee97340` · main untouched at `9978e512` |
| Product commit | `c3c1eb80` |
| Candidate freeze | `d8a22dbe` (measured 118 files, `71dd6aa6e277cd1f…`) |
| Authoritative T3 target | `f72ccc82` = candidate + docs-only takeover commits |
| Full T3 | **FULL_PRODUCT_GATE_PASS** (attempt 4) |

## Backend

1. **Codex before the limit:** all product work, committed. B1 source-bound extraction (`9b71fc3c`), product Adapter /4 producer (`48d46bf1`), B2 offline service (`c3c1eb80`), fresh 47-case service export and frontend consumer tests (`97072a72`), browser acceptance 94/94 and migration docs (`795cc241`), candidate freeze (`d8a22dbe`). Independent review with six Important groups fixed. Full T3 attempt 1 ran to completion.
2. **Claude added:** no product code. Root cause of the T3 failure; three more T3 attempts ending in PASS; takeover checkpoint; visual spec; runtime visual previews; this handoff and run.json.
3. **Old T3:** completed, **FAIL**. Two pre-existing watchdog tests failed because the Codex sandbox denied `taskkill /T`. The same tests pass outside the sandbox. Attempts 2–3 failed on Claude's over-long pytest temp root and on Codex-ACL'd `frontend/dist`. Attempt 4, in a fresh clean detached worktree, passed (CLAUDE_TAKEOVER_CHECKPOINT.md).
4. **End-to-end offline:** yes. Problem text -> ReplayExtractor (source only) -> canonical V2 validation -> Source Gate / Planner / exact engine -> product /4 wrapper -> existing frontend consumer. 47 locked development cases: 22 served, 25 refused, 0 wrong-served, 0 false-refused, 0 oracle mismatch; one pre-existing refusal-category mismatch (`NEG-per-edge-same-name`) preserved (OFFLINE_E2E_ACCEPTANCE.md).
5. **Adapter /4 product producer:** yes, `adapter4_route.build_adapter4_response`. It binds source hash, quotes, planner identity, execution-memory coordinates, answers and certificates (ADAPTER4_WRAPPER_INTEGRATION.md).
6. **Hybrid opt-in routing:** an internal service, `hybrid_offline.run_hybrid_offline`, behind an explicitly enabled existing research policy. There is no HTTP endpoint and no client flag. The existing operator preview is unchanged (HYBRID_BACKEND_ROUTING_REPORT.md).
7. **Default LLM_ONLY:** unchanged. Default import closure, cache 127, flat contract and route-policy tests all pass in the PASS T3.
8. **Hardcoding in the Planner:** no case-ID switch. Specialized reusable orchestration remains (`_dinh_cat_canh`, `_khoi_tren_thiet_dien` for pyramid/prism cuts), and the Source Gate is a closed grammar (PLANNER_GENERALIZATION_GAP_REPORT.md).
9. **Live extraction quality:** still **UNKNOWN**. Replay fixtures are authored and are not model evidence.

## Frontend / visual

10. **Reference read in full:** yes. The whole HTML/JS file and all eight screenshots. Values come from the file, not from the brief: section fill is 0.27, cutting-plane fill 0.065, shell front 0.12 + back 0.09 (SCENE3D_VISUAL_SPEC.md §2).
11. **Colors selected (spec, not applied):** edge `#1E293B`, hidden `#64748B` (or darker `#475569`, see §3), section `#C85A32`, auxiliary `#0F766E`, plane `#6D28D9`, shell `#7C8B9E`. Canvas warm tint `#F8F6F1` is an owner decision: the product deliberately rejects a warm tint.
12. **Shell opacity 0.12 default:** **not set in product code.** It was shown only as a runtime preview. Measured: at 0.12 every line role stays ≥3:1; at 0.30 hidden edges drop to 2.73:1. A slider should cap near 0.20.
13. **Style vs geometry:** nothing was changed in product. All proposed deltas are material color/opacity only. The shell must keep its depth layer (`lopChieuSau`), which decides edge occlusion. Section fill opacity is guarded by the `SECTION_FILL_DISTINGUISHABLE` gate. The demo's section and visibility algorithms are explicitly **not** adopted (spec §4).
14. **Scenes tested:** 6 owner categories (5 served + 1 refusal). 62 captures over 2 viewports and up to 6 variants. 0 console errors, 0 forbidden requests.
15. **Screenshots:** `verification/visual-reference/` with `receipt.json`; analysis in BROWSER_VISUAL_COMPARISON.md.
16. **Rendering problems found:** in C0, amber dashed hidden section edges blend into the amber fill. The prism top face shares the section color family. In the lit renderer, a 0.27 fill does not reproduce terracotta. Coincident points are handled by a merged label (`A ≡ H ≡ H1`). No depth artifacts were seen.
17. **LLM_ONLY impact:** none. No product frontend code changed.

Why spec-only: the root checkout holds a large **uncommitted** Scene3D rework (`PHONG_CACH_SCENE3D` in `scene3d-roles.ts`, ~2k lines across `scene3d-view.tsx`/`scene3d-model.ts`/`tokens.css`). It edits exactly these constants and already moves toward the reference (derived `#C85A32`, plane outline `#6D28D9`, section 0.28, shell 0.16). A parallel implementation on this branch would duplicate that work and conflict with it, and uncommitted owner work must not be touched.

## Acceptance

18. **Final candidate:** `d8a22dbe` (product `c3c1eb80`); T3 target `f72ccc82` (docs-only on top, same measured hash).
19. **Final Full T3:** **PASS** (attempt 4; attempts 1–3 FAIL for environment/harness reasons, all receipts kept).
20. **Browser acceptance:** Codex `FRONTEND_CONSUMER_ACCEPTANCE_PASS` 94/94 rows (desktop+mobile, source `97072a72`, same fixture SHA `1abad7c5…`). The visual captures are review material, not an acceptance gate.
21. **Independent review:** Codex's review found no Critical issue and six Important groups, all fixed with RED->GREEN tests. That makes it **PASS_WITH_LIMITS**: the fix diff itself was not independently re-reviewed, and Claude did not run a second independent review. No product code changed after it.
22. **Incomplete because of limits/permissions:** no second independent review; no live provider run; no independent holdout. Codex-ACL'd files (`frontend/dist`, shared `node_modules/.vite`, attempt-1 scratch) cannot be removed by Claude and were worked around, not modified. The measurement worktree `.superpowers/worktrees/t3-b1b2` is kept. Its `node_modules` is a junction: remove it with `rmdir` before `git worktree remove`.
23. **Ready for owner to consider merging B1/B2 as disabled:** the machine gates are met (T3 PASS, candidate verified, default isolation). The owner still has to decide on the missing second review and the remote/publication blocks. Merge, push and enablement remain owner-only; none was done.

## Governance (unchanged)

`DEFAULT_MODE=LLM_ONLY` · `RESPONSE_CONTRACT=flat` · `HYBRID_PRODUCT_ENABLEMENT=NO-GO` · `ALLOW_LIVE_AI=0` (0 provider calls) · `CACHE_VERSION=127` (no bump: no prompt/policy change) · `MAX_MEMORY_DECLARATIONS=32` · `REMOTE_SECURITY_BLOCKED` · 27/27 publication exceptions PENDING. No push, merge, history rewrite or ACL change.
