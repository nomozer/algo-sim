# E-1 Correction Addendum 2 — correction of [`correction-addendum.md`](correction-addendum.md) (F-1 / F-2 / F-3)

This is a **correction-of-correction**, written append-only. [`correction-addendum.md`](correction-addendum.md),
[`manifest.json`](manifest.json), [`archive-34a04eaf/`](archive-34a04eaf/), [`green-55c657b8/`](green-55c657b8/),
[`reproduced-red-34a04eaf-with-55c657b8-tests.txt`](reproduced-red-34a04eaf-with-55c657b8-tests.txt),
[`../red/red-review-34a04eaf.txt`](../red/red-review-34a04eaf.txt) and [`../verification/`](../verification/) are unchanged.
Wherever this file disagrees with `correction-addendum.md`, **this file governs** for §6 (failure identity), §2.2 (RED
mechanism) and §3 (run environment). Source of each finding: the independent E-1 evidence review of `ae531956`.

## 1. Identity

| item | value |
|---|---|
| evidence commit corrected | `ae53195639ffd5b75f2ebc26269a9ed2f6d8916f` |
| product commit (code-reviewed) | `55c657b8be715cda0edcc9e6e2ec1b3a204bdb65` |
| historical receipts commit | `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7` |
| product tree identity | `backend/app` tree `5bb9a890a1d2bdfb5d747aedfddcf31aa429de6e` and `backend/tests` tree `471bee5ee76b840f1a4360df575de0828ee629c1`, identical at `55c657b8` and `ae531956` |

Git **tree** hashes (`git rev-parse <commit>^{tree}` / `<commit>:<path>`):

| commit | root tree | `backend/app` tree | `backend/tests` tree |
|---|---|---|---|
| `34a04eaf` | `807e26868260b48b4c9f26baa2b1932bd13a6ec1` | `1961c80fb58a793d5fad98d1b3af6b89a1b6c2a1` | `eed62ce15b4bcd54adf6f1896d644940894e006a` |
| `55c657b8` | `d3c8c1f53048ef31514ed950b4c46a67b1a087c7` | `5bb9a890a1d2bdfb5d747aedfddcf31aa429de6e` | `471bee5ee76b840f1a4360df575de0828ee629c1` |
| `ae531956` | `8dcc4f330ec319a831ddf0fadad293ffc20eb8aa` | `5bb9a890a1d2bdfb5d747aedfddcf31aa429de6e` | `471bee5ee76b840f1a4360df575de0828ee629c1` |

## 2. F-1 — the nine full-geometry failures (corrects `correction-addendum.md` §6)

**Retracted.** `correction-addendum.md` line 110 attributed the failures to `test_evaluation_candidate_freeze.py` [6],
`test_single_source_of_truth.py` [2] and `test_migration_gate_enforcement.py` [1]. It also named the candidate path
`docs/evaluation/geometry/EVALUATION_CANDIDATE.json` and an identifier `4b95dcc63d86716a64c2057232c9d7e0c2501ba8`. **None
of the three test files and neither that path nor that identifier exists in the repository** (`git cat-file -e` and `ls`
fail for every one of them).

**Actual failures**, taken verbatim from the `FAILED` lines of
[`green-55c657b8/suite6-full-geometry-regression-55c657b8.txt`](green-55c657b8/suite6-full-geometry-regression-55c657b8.txt).
Every file exists at `ae531956` (checked with `git cat-file -e ae531956:<path>`).

| # | pytest node ID | failing assertion in the receipt |
|---|---|---|
| 1 | `backend/tests/geometry/test_analyze_failure_cluster_diagnosis.py::test_tien_kiem_kho` | `:55 assert pk["CANDIDATE_VERIFY"] is True` |
| 2 | `backend/tests/geometry/test_branch_independent_harness.py::test_diagnose_precheck_independent_of_branch[main]` | `:47 assert pk["PRECHECK_STATUS"] == "PASS"` |
| 3 | `…::test_diagnose_precheck_independent_of_branch[feat/rectangular-base-pyramid-compiler]` | `:47` same |
| 4 | `…::test_diagnose_precheck_independent_of_branch[arbitrary-feature-branch-xyz]` | `:47` same |
| 5 | `…::test_diagnose_precheck_independent_of_branch[hotfix/test-isolation-123]` | `:47` same |
| 6 | `backend/tests/geometry/test_branch_independent_harness.py::test_precheck_accepts_detached_head[precheck]` | `:83 assert precheck()["PRECHECK_STATUS"] == "PASS"` |
| 7 | `backend/tests/geometry/test_docs_information_architecture.py::test_inv_20_candidate_and_cache_verify_only` | `:197 assert cand_cmd.returncode == 0` (`freeze_evaluation_candidate.py --verify` returned 1) |
| 8 | `backend/tests/geometry/test_docs_test_telemetry.py::test_inv_05_candidate_and_cache_verify_only` | `:95 assert res["candidate_valid"] is True` |
| 9 | `backend/tests/geometry/test_thesis_acceptance_matrix.py::test_C2b_candidate_hien_tai_phai_duoc_KHAI` | `:339` declared `4b95dcc665f5930b…`, current `30808cb002b377e4ad68f224363ef58ab6e51e0facba7e2d4c501419f58d91dc` |

**Why all nine are candidate verify-only.**
- #1, #7, #8 and #9 assert candidate verification directly, per the receipt lines above.
- For #2–#6, `PRECHECK_STATUS` in `backend/scripts/diagnose_analyze_failure_cluster.py::precheck()` is the AND of 14 conditions,
  one of which is `freeze_evaluation_candidate.py --verify`. A measurement made **now** (2026-10-16T01:26Z, main checkout at
  `ae531956`, product tree identical to `55c657b8`; not attributed to the historical receipt) gives:
  - `precheck()` → `PRECHECK_STATUS = FAIL`. Among the returned flags only `CANDIDATE_VERIFY` is `false`;
    `CACHE_IDENTITY_VERIFY`, `MANIFEST_LF_MATCH`, `GROUND_TRUTH_LF_MATCH`, `REGISTRY_V1/V2_LF_MATCH` and
    `SOURCE_TREE_DIRTY_ONLY_USER_FAVICON` are `true`.
  - Counterfactual: the same call with only the `freeze_evaluation_candidate.py --verify` subprocess forced to return 0, all
    other checks real, gives `PRECHECK_STATUS = PASS`.
  - `freeze_evaluation_candidate.py --verify` → "MÃ SẢN PHẨM ĐÃ ĐỔI … đã đóng băng: `4b95dcc665f5930b…` (110 file) · hiện tại:
    `30808cb002b377e4…` (110 file)".

**Candidate file and identifier types** (do not interchange them):

| kind | value |
|---|---|
| path | `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` |
| candidate identifier (`measured_system.tree_hash`, the freeze script's own content hash of the 110 measured files) | `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25`, recorded with `"commit": "9ce1298f8f7cef090169c5ae5a64b0625a1ddbd4"` |
| current measured-system hash at `55c657b8`/`ae531956` (same algorithm, from `--verify` and test #9) | `30808cb002b377e4ad68f224363ef58ab6e51e0facba7e2d4c501419f58d91dc` |
| Git blob of the JSON file (`git rev-parse ae531956:<path>`) | `033284ce9e17a17e1ca7af360b64b3bb27e0ee92` |
| SHA-256 of the JSON blob (LF, 3487 bytes) | `a7920951a7e3273559ef7557a812dbebf601e6f302a8c323145c0652c84135bf` |
| SHA-256 of the working-tree file (CRLF, 3603 bytes) | `20ebeaed40dca6cc631b74a737d67c098e5199d784595e45bee6988dc7d8187b` |

The candidate is **not refrozen**. The full geometry gate is **NOT PASS** until refreeze and authoritative T3.

## 3. F-2 — the actual RED mechanism (corrects `correction-addendum.md` §2.2 and `report.md` §10 item 2)

**Retracted:** "1 item (`line:… 2 SC …`) flips to pass" and "the 4 monkeypatch items all pass trivially". The totals in
`correction-addendum.md` happen to match the receipts, but the attribution is wrong.

Method: the `FAILED` node IDs of [`../red/red-review-34a04eaf.txt`](../red/red-review-34a04eaf.txt) (146) and
[`reproduced-red-34a04eaf-with-55c657b8-tests.txt`](reproduced-red-34a04eaf-with-55c657b8-tests.txt) (145) were compared as
sets. Exactly three node IDs differ.

**A. Two items flip FAIL → PASS** (historical only):
- `backend/tests/geometry/test_shared_ask_grammar.py::test_cra_goal_clause_does_not_hide_bare_quantifier_or_incomplete_clause_route_b[line:Chứng minh BD ⊥ SC, gấp đôi {O}, tính {O}.]`
  - historical failure block at line 424; assertion at line 435: `'GOAL_CLAUSE_NOT_PREMISE' == 'QUESTION_CONTEXT_UNSUPPORTED'`.
- `…[line:Chứng minh BD ⊥ SC, một nửa {O}, tính {O}.]`
  - historical failure block at line 471; assertion at line 482: same mismatch.
- Cause: on `34a04eaf` both are **refused** with `GOAL_CLAUSE_NOT_PREMISE`. The committed test at `55c657b8:backend/tests/geometry/test_shared_ask_grammar.py:568` accepts
  `r.code in ("QUESTION_CONTEXT_UNSUPPORTED", "GOAL_CLAUSE_NOT_PREMISE")`, so the same refusal now passes.
- The `…[line:Chứng minh BD ⊥ SC, 2 SC, tính {O}.]` item named in `correction-addendum.md` is **not** one of them. On
  `34a04eaf` it is **served** (`SERVED`, `{'q': '√11'}`, historical block at line 563), so it fails in **both** receipts.

**B. Four monkeypatch items added** (`test_cra_crb_ima_mutants_are_killed_by_regression_suite`, `55c657b8` lines 667–703):
- **3 pass** on `34a04eaf`: `cra_allow_bare_quantifier_in_goal`, `crb_permissive_note_fallback_true`, `ima_allow_so_do_goc_as_cos2`.
  This is derived from the reproduced receipt: the 4 new items are present and only one of them is in its `FAILED` list.
- **1 fails** (reproduced only): `…[cra_skip_relational_predicate_after_comma]`, receipt lines 1191–1194:
  - `test_shared_ask_grammar.py:686` runs `monkeypatch.setattr(RG, "_VI_TU_MUC_TIEU", …)`, which raises
    `AttributeError: <module 'app.simulation.geometry_functions.registry' …> has no attribute '_VI_TU_MUC_TIEU'`;
  - the symbol occurs 0 times in `34a04eaf:backend/app/simulation/geometry_functions/registry.py` and 2 times at `55c657b8`;
  - this is a mutation that **cannot be applied** to the baseline, not a surviving mutation.

**C. Arithmetic.**
- FAILED: 146 − 2 + 1 = **145**.
- PASSED: 459 + 2 + 3 = **464**.
- TOTAL: 605 + 4 = **609**.

The 4 monkeypatch items are targeted single-probe checks, not full mutation testing. The cross-version RED does **not**
show that every mutation is verified. The independent review of `55c657b8` reported two source-level mutations that survive
(the `_bo_cum` "số đo" exclusion and the premise-note denylist); they remain open limitations.

The historical RED state cannot be fully re-created: the intermediate test file that produced 605 items was never
committed (**NOT_VERIFIED**). Only its receipt is preserved.

## 4. F-3 — run environment (corrects `correction-addendum.md` §3 and the receipt headers' claims)

`correction-addendum.md` §3 says every GREEN receipt was produced "in an isolated, clean detached worktree" with
`WORKING_TREE_STATUS: CLEAN (0 modified, 0 untracked)`. The receipts themselves support less than that:

| receipt | evidence of location in the receipt | attested environment |
|---|---|---|
| `reproduced-red-34a04eaf-with-55c657b8-tests.txt` | traceback path `C:\Users\Bunny\AppData\Local\Temp\algosim-e1-wt-34a04eaf\…` | detached worktree at `34a04eaf` with the `55c657b8` test file swapped in (header: `M backend/tests/geometry/test_shared_ask_grammar.py`) |
| `green-55c657b8/mutation-4-monkeypatch-tests-55c657b8.txt` | `rootdir: d:\Documents\projects\algo-sim\backend`; no `WORKING_TREE_STATUS` line | **main checkout**, not a detached worktree. Working-tree state **NOT_ATTESTED**; the main checkout always holds the user's untracked `frontend/public/favicon.svg` |
| `green-55c657b8/suite1…`, `suite2…`, `suite3…`, `suite4…`, `suite5a…`, `suite5b…`, `suite6…` (7 files) | `-q` output: no rootdir and no absolute repository path; the header claims `CLEAN (0 modified, 0 untracked)` | location **NOT_ATTESTED**. The literal "0 untracked" is not verifiable, and would be false in the main checkout (favicon) |

The headers carry no Git tree hash. The tree hashes are supplied in §1 of this file, from Git, not from the run.

The results are independent of this gap: the independent review of `ae531956` re-ran shared 609, result-binding 72,
mutation-4, suite5b 868/1x and grammar probe (195/195 rows identical) in a clean detached worktree. That re-run is a
**new** measurement; it is not attributed back to the historical runs.

## 5. What is verified and what is not

| claim | status | evidence |
|---|---|---|
| 6 archived `34a04eaf` receipts byte-identical to history | VERIFIED | identical Git blob object IDs; 81/81 manifest hash/byte checks (independent review) |
| current `verification/suite1–6` untouched by `ae531956` | VERIFIED | `git diff --name-status 55c657b8..ae531956` |
| nine failures are candidate verify-only | VERIFIED | §2 (receipt assertions + counterfactual precheck now) |
| RED mechanism (2 flips, 3/4 mutation pass, 1 AttributeError) | VERIFIED | §3 (set comparison of both receipts, `55c657b8` test lines 568 and 686) |
| exact intermediate test file behind the 605-item RED | NOT_VERIFIED | never committed |
| run environment of 7 GREEN receipts | NOT_ATTESTED | §4 |
| GREEN numbers on the committed tree | VERIFIED (re-run) | independent review of `ae531956` |

## 6. Gates

- Candidate **not refrozen** (`4b95dcc6…` vs current `30808cb0…`).
- Authoritative T3 **not run**.
- `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid production NO-GO.
- E-1 status: **PENDING INDEPENDENT SHORT REVIEW** of this addendum.
