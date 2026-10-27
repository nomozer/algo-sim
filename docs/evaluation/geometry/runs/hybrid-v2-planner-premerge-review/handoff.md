# handoff.md — `hybrid-v2-planner-premerge-review`

- **Status:** `READY_FOR_OWNER_GO_MAIN_REVIEW`. Not merged, not pushed, no cleanup done.
- **Branch / worktree:** `research/hybrid-v2-planner-generalization` · `.superpowers/worktrees/planner-generalization`.
- **Main before:** `386d214952e6a7ba98f0931b5ecfd7a5b89d1667`.
- **Product:** `37e8435213303f54f37a19b6ce85f896fc0631a0`.
- **Candidate (T3):** `99faf026bdcbcaa2f32e07a9f1687416a820dffd`. Freeze `dd5b1f55`: 118 files, `1377e654…`.
- **Full T3:** `FULL_PRODUCT_GATE_PASS` with 12344 backend and 1417 frontend tests. Post-T3 freeze MATCH.
- **Versions:** registry `/16` · planner `/16` · engine `/14` · `CACHE_VERSION 130` · `LLM_ONLY` · Hybrid opt-in.

## Decisions for the Owner

1. **GO MAIN** for the branch: planner `/16` + registry `/16`, with the evidence in `report.md` and `review.md`.
2. **I-1 — symbol outranks kind word.** Should "hình lập phương ABC.A'B'C'" (correct symbol, false kind word) refuse?
   - Today it is served, by a pinned decision from run `hybrid-semantic-hardening`.
   - Reversing it is a one-line change in `_khoi_khop` / `_cum_goi_khoi`, plus flipping the pinned test and the three
     `xfail(strict=True)` rows.
   - It needs its own GO.
3. **`ADAPTER_INTEGRATION_GAP`.** `/4` refuses plane-only derived sections. Fixing it needs a separate wave, because it
   changes the certificate contract of every V2 derived section.

## Leftovers

- **Temporary detached checkout:** `D:/Documents/projects/algo-sim/.superpowers/worktrees/.superpowers/worktrees/premerge-red`
  at `99faf026`. It was used for RED (at `ca0bb5f2`) and for T3, and was left in place.
  - Its `frontend/node_modules` is a junction. Run `rmdir` on it before `git worktree remove`.
- **The predecessor's T3 checkout** `D:/tmp/pg-t3-ca0bb5f2` is untouched.

## Next recommended action

1. Owner GO MAIN review of this branch.
2. Then, as separate waves:
   - (a) the I-1 policy decision;
   - (b) the `/4` plane-only section certificate;
   - (c) an independent Vietnamese holdout for prism/cube sections before any readiness claim.
