# Independent review packet: visual–Hybrid final corrections

You are the independent reviewer. Claude, the author, did not choose you and does not run you. Please review the code and receipts only:
- read-only;
- 0 model calls, no live provider;
- no merge, push or history rewrite.

Record your verdict in `INDEPENDENT_REVIEW.md` in this run directory (a new file; nothing here pre-fills it).

## Identity

| | |
|---|---|
| Repository | `D:\Documents\projects\algo-sim` |
| Branch | `integration/hybrid-visual-candidate` |
| Base for this task | `2c82c4fb` (after the integration report) |
| Product commits | `0645de46` (P3 diagnostics UI), `af670aa6` (P2 display identity + samples + `CACHE_VERSION` 128) |
| Harness commits | `e3e77a0f`, `4ec36db9` (official Visual suite learner-mode split) |
| Candidate freeze | `a636a0e5`: product `af670aa6`, 118 measured files, tree `8be632679307a94ce4525ad576a05a9eccffc8ba2bdbf02d4c7dc93c208b7c41`, cache 128 |
| Correction chain | `7c296be1` (`candidate_divergence.json`, corrects `visual-hybrid-integration`) |

**Diff to review:** `git diff 2c82c4fb..HEAD -- backend frontend` (product, tests, harness), and `docs/` for the reports.

## Questions to answer

1. **Backend display identity** (`display_names.ten_hien_thi` step ⑧ and rule ①; `source_entities.ten_mat_phang_nguon`; `simulation_state.build_scene` / `build_simulation_state`):
   - Can a section cycle still be built through an id or an unnamed vertex?
   - Can the declared-plane rule fire without the problem text writing the name, or when two planes declare it?
   - Does it change anything but names (ids, coordinates, DAG, provenance, order, answers, certificates)?
   - Is Adapter /4 truly unaffected? Its contract has no `problem_text`, and the re-export is byte-identical (`1abad7c5…`).
2. **`CACHE_VERSION` 127 → 128:** is the evidence (`cache/decision.json`, genuine v127 rows, `test_cache_display_identity_invalidation.py`) sufficient? Is the bump complete in every sync place? Is the model surface really unchanged (`cache_identity.lock.json`: only the version moved)?
3. **Offline samples:**
   - Is `DE_HOI` in `build_geometry_samples.py` faithful to each problem's text?
   - Is passing a `RequestContract` there a fair mirror of the product route?
   - Is the retargeted assertion in `hybrid-preview-contract.test.tsx` (step label/narration instead of every event's narration) a weakening, or the correct learner-visible check?
4. **P3:** is any technical code still reachable in learner-visible UI? Are the strict assertions really strict (`final-quality.test.tsx`, `hybrid-preview-contract.test.tsx`)?
5. **Official suite harness**, the most important question. Does any change turn a real failure into a pass?
   - The Mode A exemptions: `revealFinal: false` in `expectedSolutionRows`, `expectedAnnotationIds`, `assessQuantityPicker`, `assessGeometrySteps`, `assessStructuredReferences`, `assessWitness`.
   - The gate change `ANSWER_SHOWN_IN_MODE_A` / `ANSWER_NOT_SHOWN_ONCE`.
   - The Mode B dash baseline.
   - The `.geo3d-bang-noi` overlay mask.
   - The Mode B per-quantity selection.
   - `finalResultIds` is meant to be independent of the product's `tapKetQuaCuoi`. Is it?
6. **The two remaining product findings** (OFFICIAL_SUITE_RESULTS.md F1, F2): are they correctly classified as product, not harness?
7. **Default route:** LLM_ONLY default, prompts, routing, Hybrid disabled. Any change?

## Receipts

| What | Where |
|---|---|
| RED/GREEN | `verification/red-green/` |
| Adapter /4 fault check | `verification/red-green/p2-adapter4-faultcheck.txt` |
| Cache probe | `cache/` |
| Official suite before/after | `visual/official-suite-run1/`, `visual/official-suite-run2/`; Codex's earlier run: `../visual-hybrid-integration/visual/official-suite-complete/` |
| Browser | `verification/browser/` |
| Full T3 + post-T3 freeze verify | `verification/full-t3/` (see FINAL_OWNER_HANDOFF.md) |
| Reports | DISPLAY_IDENTITY_FIX.md, DIAGNOSTICS_UI.md, OFFICIAL_SUITE_RESULTS.md, BROWSER_ACCEPTANCE.md, REGRESSION_RESULTS.md, FINAL_OWNER_HANDOFF.md |

## Useful commands (offline)

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_display_identity_source_names.py tests/test_cache_display_identity_invalidation.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
cd frontend && node --test "scripts/*.node-test.mjs"
cd frontend && npx vitest run src/components/hybrid-preview-contract.test.tsx src/simulations/domains/geometry/final-quality.test.tsx
```
