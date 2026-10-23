# Handoff — `hybrid-offline-consumer` (Session 5, Codex → Claude)

- **Status:** `SESSION5_READY_FOR_OWNER_GO_MAIN_REVIEW` — stop at the GO MAIN gate; no merge or push without separate owner authorization.
- **Branch:** `research/hybrid-session5-offline-consumer` in `.superpowers/worktrees/hybrid-session5-offline-consumer`; base local `main` = `3f6d737529af6fc79494fc3baeb340a7ca663b10`.
- **Product commit:** `e090af1c9511bbc83afce92e4d6c88a32d851503` (frontend only; Codex initial `56507602`).
- **Candidate freeze:** `9f06ed2b664f03976f1f7d67b6b0a44f0e5b7f15` — measured `413ee525d20874aa346b13df7e51019266f7d4701af56719c2a2ee736266b5df` (116 files, unchanged vs base).
- **Full T3:** `FULL_PRODUCT_GATE_PASS` at `478d50e8` — [`verification/full-t3/execution.json`](verification/full-t3/execution.json); post-T3 freeze MATCH.
- **Browser acceptance:** `FRONTEND_CONSUMER_ACCEPTANCE_PASS` 94/94 at `9f06ed2b`, tree clean — [`results/browser-final-9f06ed2b/receipt.json`](results/browser-final-9f06ed2b/receipt.json).
- **Independent review:** round 3 `PASS` — [`verification/independent-review.md`](verification/independent-review.md).
- **Report:** [`report.md`](report.md) · **Takeover:** [`SESSION5_TAKEOVER_CHECKPOINT.md`](SESSION5_TAKEOVER_CHECKPOINT.md) · **Gaps:** [`HYBRID_V2_REMAINING_GAPS.md`](HYBRID_V2_REMAINING_GAPS.md) · **Extraction:** [`E2E_EXTRACTION_READINESS_UPDATE.md`](E2E_EXTRACTION_READINESS_UPDATE.md)

Invariants: `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127` (no bump), `MAX_MEMORY_DECLARATIONS=32`, 0 provider calls.

Owner decisions open:
1. GO main (local) of this branch in disabled state.
2. Remote publication — blocked by the inherited raw-traceback blob ([`SECURITY_AUDIT.md`](SECURITY_AUDIT.md)).
3. Visual approval of the screenshots (`human_visual_review: NOT_APPROVED`).
4. Deleting Session 5 temporaries (1,126,927 B; deletion was denied in-session — list in `report.md` §11) and, after review, this worktree (unlink `frontend/node_modules` junction first; never delete its target).
5. Any live/holdout extraction work: needs curator, locks, budget and a separate GO.
