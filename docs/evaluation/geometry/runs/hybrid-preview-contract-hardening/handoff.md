# Handoff — `hybrid-preview-contract-hardening`

**Verdict:** `PREVIEW_CONTRACT_HARDENING_VERIFIED`.
- Branch `research/hybrid-preview-contract-hardening` at the docs commit after `8b17d170`; product commit `bce21d8b`;
  candidate `1b7a6713…` (111 files).
- T3 `FULL_PRODUCT_GATE_PASS` at `8b17d170`.
- Not merged, not pushed. `main = origin/main = 65d6ee97` is unchanged.
- `LLM_ONLY` is the default, `CACHE_VERSION` is 125, Hybrid enablement is NO-GO, 0 live calls.

## What exists now

| item | location |
|---|---|
| refusal classification | `backend/app/ai/hybrid_preview.py::classify_refusal` (adapter `/2`) |
| contract for Scene3D | `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` |
| fixtures | `fixtures-adapter-2/` (41: 12 served / 25 refusal / 4 gate); `fixtures/` is superseded and kept unchanged |
| reproduce fixtures | `cd backend && python scripts/export_hybrid_preview_fixtures.py --verify ../docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2` |

## Open issues (`docs/OPEN_ISSUES.md`)

- Frontend:
  - F1 `ISSUE-ARCH-SCENE3D-ALTITUDE-MARKER-UNCERTIFIED`
  - F2 `ISSUE-ARCH-SCENE3D-CHART-METRIC-UNGUARDED`
  - F3 and F4 under `ISSUE-ARCH-HYBRID-ROUTE-D-NOT-WIRED`
  - F5 `ISSUE-ARCH-SCENE3D-VERIFICATION-GAP-PRESENTATION`
  - F6 `ISSUE-ARCH-SCENE3D-INSUFFICIENT-SPEC-HINT`

  Acceptance criteria for all six are in contract §9.
- Backend: `ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO`. The shared reader reads vector or dot notation `= 0` as a
  length; it is default-route code, so it needs its own wave.
- Ops: `ISSUE-OPS-CACHE-HISTORICAL-MODE-UNKNOWN`.
- Resolved here: `ISSUE-ARCH-HYBRID-PREVIEW-FAILURE-CATEGORY-COLLAPSED`, `ISSUE-ARCH-HYBRID-PREVIEW-PROOF-TEXT-U2212`.

## Preservation inventory (nothing removed)

The only removals were this run's own temporary detached checkouts: two freeze worktrees, one RED worktree, and two T3
worktrees (junction removed first; main `node_modules` intact). Everything else is untouched:
- the active Scene3D worktree `scene3d-plane-grid-camera` (uncommitted, `HUMAN_VISUAL_REVIEW_PENDING`);
- `extraction-v2-safety` (2 unique commits + uncommitted) and `hybrid-semantic-extraction-v2` (14 unique);
- branches without a worktree: `research/compact-geometry-dsl`, `feat/real-model-pilot-tooling`,
  `docs/real-model-e2e-readiness`;
- merged worktrees: contract-driven-goal-composition, hybrid-backend-integration, hybrid-pre-main-hardening,
  hybrid-route-d-preview-wiring, semantic-extraction-v3(-runtime-revision), step-math-validation,
  verify-hybrid-go-main-20261018;
- the three orphan folders: goal-bounded, goal-fixed, semantic-grounding-base-20261017 (with its `algosim.db`);
- `backend/algosim.db`;
- the untracked GO MAIN packages on `main` (`hybrid-go-main/`, `hybrid-route-d-preview-go-main/`), `.vscode/` and
  `frontend/public/`;
- every oracle, protocol, GOLD, receipt and takeover snapshot.

## Exact next GO (owner decides; one at a time)

1. **`GO_MAIN_HYBRID_PREVIEW_CONTRACT_HARDENING`** — fast-forward `main` to this branch tip, run the post-main smoke,
   push without force. The owner runs the merge and push manually if Auto Mode blocks them again. Default stays OFF.
2. **Scene3D wave (frontend owner, after the human visual verdict on `scene3d-plane-grid-camera`):** F1–F6 against
   `fixtures-adapter-2/`. Prove first that `store.loadEnvelope` accepts every `served-*` (vitest). No browser caller to
   the preview.
3. **Backend wave:** fix the shared length reader (`ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO`) with RED tests. It
   touches the default route, so it needs a refreeze, possibly a `CACHE_VERSION` decision, and T3.
4. **Live pilot:** a separate authorization with preregistered budget, stop rule and held-out data. There is still no
   provider transport in the preview.
