# Plan: visual–Hybrid final corrections

Authorization `GO_LOCAL_VISUAL_HYBRID_FINAL_CORRECTIONS_ONLY` (2026-10-24).
- Branch `integration/hybrid-visual-candidate`, worktree `.superpowers/worktrees/hybrid-visual-candidate`.
- Baseline: product `a9d05dda`, freeze `aec7b183`, verified T3 target `b99afd32`, docs head `2c82c4fb`.
- Local only.

## Owner decisions taken in this session

- **Independent review:** run by the owner (Codex or a person) from a review packet written here. Claude does not substitute a subagent. Until the owner records it, the status reports the review as PENDING.
- **Plane-name rule (LLM_ONLY):** use a declared one-letter plane name (`(P)`, `(α)`) only when the bare name is a source name in the problem text (`source_entities.la_ten_nguon`) **and** exactly one plane in the scene declares that label. Otherwise keep the name composed from the points.

## Preflight (2026-10-24)

- Tree clean at `2c82c4fb`; `main` `9978e512` unchanged.
- Root checkout: owner's work, 27 entries, 79 hashed files unchanged.
- Codex worktree `visual-hybrid-integration`: dirty, left untouched; Codex Vite on 3117 still running.
- Classification: CORE/SUPPORTING. Correctness of learner-visible names, the learner-UX oracle, and learner hygiene; no new family, no renderer rewrite.

## Work items

- [ ] **P3** Learner diagnostics.
  - RED: restore the strict `not.toContain(reason_code)` in `hybrid-preview-contract.test.tsx` (no `<details>` stripping).
  - Remove the `<details>` "Chi tiết chẩn đoán" drawer in `SimulationWorkspace.tsx`.
  - Codes stay in the envelope/API, logs and receipts.
- [ ] **P2a** `display_names.ten_hien_thi` step ⑧: build the vertex-cycle notation only from resolved vertex notations; no `or s` id fallback.
  - RED with an unnamed vertex.
  - Negative control: an all-named cycle keeps `MNPQ`.
- [ ] **P2b** Adapter /3 anonymous-vertex scrub: also cover the section and the quantities built on it, matching the `function_route._an_dinh_thiet_dien_phu` policy.
  - RED on `demo1`/`demo2` (`MI1I2I3`).
  - Negative control: named sections unchanged.
- [ ] **P2c** LLM_ONLY declared plane name per the rule above, source text taken from `RequestContract.problem_text`.
  - RED on the `cau-cat-mat-phang` program with a contract.
  - Negative controls: label not in source; two planes with one label; no contract.
- [ ] **P2d** Adapter /4 regression: re-export the B1/B2 offline corpus and diff it against `visual-hybrid-integration/integrated/offline` (expected identical, or explained).
- [ ] **CACHE_VERSION** decision with evidence. The default-route scene output changes ⇒ expected bump 127 → 128, with the four-place sync and a migration test.
- [ ] Regenerate `geometry-samples.json` (`scripts/build_geometry_samples.py`) and the official-suite fixtures (`generate_generic_tier_a_fixtures`).
- [ ] Re-freeze the candidate in a clean worktree, as its own commit.
- [ ] **P1** Official suite: validate the current learner UX.
  - Mode A (default): the final answer is absent from the drawer, labels and visible text.
  - Mode B («Phân tích toán học», an explicit learner action): the answer appears exactly once, and the causal target is selected from there.
  - Independent geometry, section-fill, error and provenance oracles and the thresholds stay unchanged.
  - Diagnose all 8 scenarios one by one; keep before/after receipts.
- [ ] **P4** Targeted tests, Vitest, typecheck, node harness, official suite, Adapter /4 browser, refusal surface, orbit gate, owner screenshots, Full T3 on the final candidate, post-T3 freeze verify.
- [ ] **P5** Review packet, reports, EVIDENCE_INDEX / CURRENT_STATE write-back. Stop at the owner gate.

## Outcome (2026-10-25)

Every work item above was executed except the independent review, which waits for the owner-appointed reviewer. Results are in FINAL_OWNER_HANDOFF.md.

## Excluded

- B1/B2 restart, renderer rewrite, new families.
- Frontend renaming.
- Live calls, push, main merge, publication exceptions, ACL changes, other worktrees.
