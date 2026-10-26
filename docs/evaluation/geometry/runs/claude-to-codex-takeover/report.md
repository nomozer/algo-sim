# Scene3D / Hybrid V2 continuation — checkpoint

Status: LOCAL_PARTIAL_WITH_GAPS. No main merge, push, provider request or production Hybrid enablement. Default `LLM_ONLY`, CACHE_VERSION 130. Current-candidate Full T3 is pending a clean freeze; the inherited T3 receipt belongs to `e1ebc72c`, not this product.

## Preservation and provenance

Read `CLAUDE_TO_CODEX_TAKEOVER.md` and `preservation.json`. Claude source HEAD `3dcd6d9f`; all 108 changed/new nonignored files were copied verbatim into a separate worktree before editing. Backup retains 112 hashed files including ignored campaign evidence. No root-checkout or source-Claude edit, deletion, ACL change or process termination.

## Completed slices

Claude's local opt-in route and angle bridge were retained and verified. TypedFactNext V2 angle targets reuse `ask_angle_line_plane`, `ask_angle_lines`, `ask_angle_plane_plane`; outputs are explicitly cos², not degrees. `/api/analyze` uses the existing /4 reader/store when loopback plus `HYBRID_V2_LOCAL=offline-replay` is enabled; all other clients use the existing default policy. Replay refusals never fall back to LLM_ONLY; cache is bypassed.

Codex completed the unfinished skew check: exact scalar triple product rejects coplanar lines called skew. Registry `_cum_hoi` binds the claim to the measured pair, preventing a shared quote from applying another pair's claim. The refusal is classified INVALID_DATA and engine identity is `/12`. Unicode normalization is used for matching, never to rename points. Adapter /4 restores verbatim planner quotes only after canonical equality with the verified quote; source hash and raw substring checks remain required. Tampered provenance still refuses.

The offline image guard runs before ingestion, preventing Vision calls even if a server key exists. Local out-of-scope refusals also carry `no-store`. No schema, prompt, IR, dependency or default-mode migration was introduced.

Reused: bridge, Registry question grammar, bounded planner, exact engine, ReplayExtractor, Adapter /4, frontend reader/store/Scene3D, existing B3 browser harness. Created product modules: none. Duplicate search: no parallel planner/engine/renderer or second response reader.

## Verification and honest limits

- Focused geometry/HTTP: 80 passed before one additional provenance fault test; skew tests now 9 passed. Related /4/offline/extraction/contract suite: 197 passed. Static lazy-import guard: passed in a standalone run.
- Frontend related tests: 152 passed (7 files). Production typecheck/build: passed; existing chunk-size advisory remains.
- `browser-auth-settled/receipt.json`: 20/20 rows, 0 browser errors, 0 external requests. Ten authored cases × desktop/mobile through the actual input UI and HTTP server, no response mocks. Seven served cases check exact hand-derived oracle values, Mode A hidden, Mode B once and checked scene binding. Three refusal cases check no scene, visible explanation and hidden internal code.
- `local-route-results.json`: 43/47 scored; 22 correct served, 20 correctly grouped refusals, 0 wrong served, 0 false refusal, 1 historical refusal-category mismatch. Four ambiguous extraction variants excluded explicitly. Authored development data, not independent holdout or provider quality.
- Retained failures: initial missing interpreter/pytest-temp ACL setup; one static-guard MemoryError later passed serially; browser oracle-field mismatch; browser auth SQLite locking (17 completed rows before failure). The final browser run waits for real auth bootstrap network idle. No auth product fix was bundled; concurrent bootstrap robustness remains unverified.

Browser evidence is not a blanket geometry-family certification. The skew-distance answer has no rendered common-perpendicular segment: the harness reports witness availability and only requires a supplied witness to render. Do not read that conditional check as proof that every answer has a witness. Likewise a non-right angle is measured but has no geometric angle-arc witness. These remain replacement-readiness gaps.

## Phase 1 Scene3D

Claude committed producer-plane naming, anchored certified right-angle marks, witness legs and rejection of invalid marks (`f3ae506c`), cache130 fixture export, 60 P0 frames and 204 camera frames. Codex preserved those bytes. This continuation changes no Scene3D renderer, camera, theme or layout.

Actual inherited Official Visual receipt at `3dcd6d9f`: **7/8**, only `cross_section` fails. Locked F2 oracle unchanged; Owner policy remains terracotta fill with blue selected border. Proposed role-aware V2: **2 PASS / 10 UNCERTIFIABLE / 0 baseline FAIL**; 10/10 faults detected only on certified views. Proposal not adopted or Owner-approved. Author frame review is not human approval or independent review.

Remaining visual scope: all-label continuity/performance certification, tangent/no-cut sphere browser rows, arbitrary oblique-prism cuts, unsupported cone conics, redundant foot dots and unobservable role-aware views. No claim of zero P0 errors outside the measured scope.

## Hybrid replacement readiness

The following are VERIFIED_OFFLINE_BROWSER_SLICES: determined right/oblique triangular-prism point-plane distances, skew-line scalar distance, line-plane/line-line/dihedral cos² angles, NFC/NFD quote handling and explicit refusals. The overall prism/reference families remain PARTIAL because their full sections, sphere combinations and independent NL extraction are not covered.

Keep the 18-family matrix in `../visual-closure-hybrid-readiness/HTML_18_FAMILY_CAPABILITY_MATRIX.md` with this delta: canonical distance and angle mapping plus actual UI/HTTP slices now exist. No complete reference family is promoted to FULL_E2E_VERIFIED. Curved canonical bridge, inscribed/circumscribed/composite solids, general coordinate goals and arbitrary underdetermined constructions remain UNSUPPORTED/PARTIAL as recorded there. Four-label measurement targets refuse explicitly; they are not silently reduced, and coplanar four-label targets are not newly supported.

Extraction quality on current independent holdout: UNKNOWN. Live provider: NOT_MEASURED (0 calls). Independent Owner review and human visual approval: PENDING. Migration checklist, common-perpendicular witnesses, additional geometry families, source extraction reliability, shadow/canary/rollback evidence and explicit Owner migration GO remain required before replacing `LLM_ONLY`.

## Next

Checkpoint this verified slice, generate a new clean candidate while retaining the previous manifest bytes, then run Official Visual and Full T3 in a clean detached worktree. Record actual results and exact continuation state in `NEXT_AGENT_HANDOFF.md`; do not promote inherited T3 to the new candidate.
