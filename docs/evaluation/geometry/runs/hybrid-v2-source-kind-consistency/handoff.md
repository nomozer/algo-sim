# handoff.md — `hybrid-v2-source-kind-consistency`

- **Status:** `READY_FOR_OWNER_GO_MAIN_REVIEW`. Not merged, not pushed, no worktree cleanup performed.
- **Branch / worktree:** `research/hybrid-v2-planner-generalization` · `.superpowers/worktrees/planner-generalization`.
- **Main before:** `386d214952e6a7ba98f0931b5ecfd7a5b89d1667`.
- **Previous reviewed candidate:** `99faf026bdcbcaa2f32e07a9f1687416a820dffd` (product `37e8435213303f54f37a19b6ce85f896fc0631a0`, `registry /16`).
- **New product commit:** `ff48db2a0c3f4424fc91c313a9bfaee8e3646bc1` (`registry /17`).
- **New frozen candidate (T3):** `71029809201ca691e583943cc5cf1c74d6bd5d73` (freeze commit `4581886f`, `118` files, `tree_hash = 31bb915d3550e58ca9985afa607c0664f480acacdcb223b82451cc06d649f8b8`).
- **Full T3:** `FULL_PRODUCT_GATE_PASS` (`12,382 passed, 1 skipped, 2 deselected, 15 xfailed` backend; `83 files / 1,417 passed` frontend; post-T3 freeze `MATCH`, [`full-t3/receipt.json`](full-t3/receipt.json)).
- **Independent Review:** `INDEPENDENT_REVIEW_PASS` (`0 BLOCKER`, `0 MAJOR`, `3 MINOR`, `1 NIT`; [`review.md`](review.md)).
- **Versions:** `registry /17` · `planner /16` · `engine /14` · `Adapter /4` (unchanged) · `CACHE_VERSION = 130` (`NO_BUMP`) · `DEFAULT_MODE = LLM_ONLY` · Hybrid opt-in only · `0` live provider calls.

## Summary of `I-1` Closure (`SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`)

1. **Adversarial 124-case suite (`adversarial.py`):** `118/124` (`6` `fail_open`) → **`124/124` (`0` `fail_open`, `0` `false_refusal`)** ([`results/green-124-after.json`](results/green-124-after.json)).
2. **Symbol+Kind 31-case suite (`symbol_cases.py`):** `16/31` (`15` `fail_open`) → **`31/31` (`0` `fail_open`, `0` `false_refusal`)** ([`results/green-symbol-after.json`](results/green-symbol-after.json)).
3. **Development corpus (`regression.py`):** **`10/10` positives served (`10/10` exact oracle agreement), `8/8` negatives refused with registered code, `0` wrong-served** ([`results/development-regression-registry17.json`](results/development-regression-registry17.json)).

## Leftovers Preserved Per Authorization

- **Detached T3 checkout:** `D:/Documents/projects/algo-sim/.superpowers/worktrees/.superpowers/worktrees/premerge-red` (currently detached at `71029809201ca691e583943cc5cf1c74d6bd5d73`; `frontend/node_modules` is a directory junction — use `rmdir` on the junction before `git worktree remove` when cleanup is eventually authorized).
- **Predecessor T3 checkout:** `D:/tmp/pg-t3-ca0bb5f2` (untouched).

## Decisions for the Owner

1. **GO MAIN** for `research/hybrid-v2-planner-generalization` (`planner /16` + `registry /17` + `engine /14`), with `I-1` closed and verified under Full T3.
2. **Subsequent waves after GO MAIN:**
   - Adapter `/4` certificate support for plane-only derived sections (`ADAPTER_INTEGRATION_GAP`);
   - Independent Vietnamese holdout evaluation before any curriculum readiness claim.
