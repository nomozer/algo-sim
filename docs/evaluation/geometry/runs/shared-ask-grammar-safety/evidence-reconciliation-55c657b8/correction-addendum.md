# E-1 Evidence Integrity & Provenance Reconciliation Addendum (`55c657b8`)

- **Run:** `shared-ask-grammar-safety`
- **Reconciliation Package:** `docs/evaluation/geometry/runs/shared-ask-grammar-safety/evidence-reconciliation-55c657b8/`
- **Manifest:** [`manifest.json`](manifest.json)
- **Audited Product Commit:** `55c657b8be715cda0edcc9e6e2ec1b3a204bdb65`
- **Previous Commit (Overwritten Receipts Restored):** `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7`
- **Pre-Regression Baseline:** `4acfc7316179e4ec7a9039dc654ea95fee8a9550`
- **Scope:** Documentation and evidence provenance only (`0` changes to product code, test code, oracles, `grammar_probe.py`, or `EVALUATION_CANDIDATE.json`).

---

## 1. Historical Receipt Restoration (`E-1` Append-Only Recovery)

Between commits `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7` and `55c657b8be715cda0edcc9e6e2ec1b3a204bdb65`, six verification receipt files under `docs/evaluation/geometry/runs/shared-ask-grammar-safety/verification/` were overwritten in place instead of being written to a commit-scoped subdirectory.

To restore append-only auditability without overwriting `verification/suite1–6` a second time:
1. All six historical blobs from `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7` were extracted via `git show 34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7:<path>` and saved into [`archive-34a04eaf/`](archive-34a04eaf/).
2. The existing files at `verification/suite1–6` (`55c657b8be715cda0edcc9e6e2ec1b3a204bdb65`) were left completely untouched.
3. Because this repository has `git config core.autocrlf = true` on Windows, Git object blobs store normalized `LF` bytes whereas Windows checkouts convert `LF` to `CRLF` (and PowerShell `Set-Content` in `55c657b8` produced mixed `CRLF`+`LF` in the working tree prior to Git `LF` normalization on commit). Both `LF` (Git blob) and `CRLF` / working-tree SHA-256 digests are recorded below:

| File | Archive Path (`34a04eaf`) | `34a04eaf` Git Blob `LF` SHA-256 (Bytes) | `34a04eaf` Windows `CRLF` SHA-256 (Bytes) | `55c657b8` Git Blob `LF` SHA-256 (Bytes) | `55c657b8` Working-Tree Raw SHA-256 (Bytes) |
|---|---|---|---|---|---|
| `suite1-shared-ask-grammar.txt` | [`archive-34a04eaf/suite1-shared-ask-grammar.txt`](archive-34a04eaf/suite1-shared-ask-grammar.txt) | `e64037ce5e8f7e84b029c6920a8dea952363d52b6f11ad63fb8183ddfd687fc1` (`812`) | `aa13c20e5d8c1bc928081a5a06c23f3a523542a75e17d8f297f393ac12e82b54` (`825`) | `f6b3bdab50d660b7b9148c6d332dccb427083908bbfd4c1983be00f2cc623314` (`754`) | `d6a918cac8ff2614f6357eb537473608b7c775a73392c93307b621734b0059aa` (`765`) |
| `suite2-result-binding-planning.txt` | [`archive-34a04eaf/suite2-result-binding-planning.txt`](archive-34a04eaf/suite2-result-binding-planning.txt) | `60cf5d3c76f87f39a29cafcf138011a4b79f7ac4a458bae495da456b40f11b3a` (`336`) | `e5145f8fcfc0b572f21424897e7fdcb2b384ac2d2cbcb495d29bfd8be3d7c8b2` (`343`) | `78cce51fe966149b8975308b65d0bd4289b67bf48311e4f3b20625a96a0bf9b3` (`113`) | `f307a27421a678de10ed64c07e5ca2e81870fbbd8701701a7defa1c6de2d5a51` (`116`) |
| `suite3-grammar-probe.txt` | [`archive-34a04eaf/suite3-grammar-probe.txt`](archive-34a04eaf/suite3-grammar-probe.txt) | `4385188b71ab0882ec68d9affff51947bd3e6b59be899f0fdafcada4aa5ff9f1` (`1061`) | `3f89c67cd2c8d3c2be6b0c08ccbcfa4bd2df218f764129f707738c3f5653d991` (`1080`) | `6ddd4414f5964afcdebcccc8fe5ffa12fda099136bb1537a3159fb26fdb3f489` (`701`) | `6832bde101470623d0b0e62757baa643b9ee234e18275a3a3bce3efe9549bafe` (`713`) |
| `suite4-hybrid-compiler-benchmark.txt` | [`archive-34a04eaf/suite4-hybrid-compiler-benchmark.txt`](archive-34a04eaf/suite4-hybrid-compiler-benchmark.txt) | `ab1485be14c971e056d53f4f429ddf79138b5e0dea68d9952ba5d06a2c0c5848` (`429`) | `799e7b447382815b4fa8fa8ab75bafa8d3f3e145b2ebf78c43bca5d14a4010e3` (`437`) | `d7cfe0ed4d8b7dd1bd2ba07ff8678516552a1d1d5e5a1267e25eda307dadccc8` (`204`) | `d64a584c6e6bca24177322ded321e49ae4634bfcaea1c77f95d27942998ada66` (`208`) |
| `suite5-ask-context-section-suites.txt` | [`archive-34a04eaf/suite5-ask-context-section-suites.txt`](archive-34a04eaf/suite5-ask-context-section-suites.txt) | `a2e3783b2593efc56e6e675550cf949fa7676403fa280e2bb642c7673387c41b` (`1567`) | `26b3d99fae3c0d6152b04696874f02c299f1177168d21e868fa488a6588221c5` (`1585`) | `410d761908f83bb8e99e5c2eae77e6b4982007d52ec026b5d2e8e4d02a8a5a86` (`1086`) | `69e4e099073fbc198ea032f51ef612fec41f28da450b135810a92cbdba39095a` (`1101`) |
| `suite6-full-geometry-regression.txt` | [`archive-34a04eaf/suite6-full-geometry-regression.txt`](archive-34a04eaf/suite6-full-geometry-regression.txt) | `38e1b67426faace0de0801957ec97ba2da9c908b33256ee2fea45f0826ace99e` (`23782`) | `77b65fa21ab66bfac72f409582f04ee504f1a67fda91fb4c4cb31eb0efa1a7ae` (`24153`) | `38b788d71b68459cd5aafb61f65f1018b1963ebb50a76ef780b45b17c81aa88a` (`24859`) | `dc027695a5b66f24020a52a5f04e5452c6159fc19d79efb350cb0f76d16a8892` (`25247`) |

---

## 2. RED Evidence Reconciliation (`146 failed, 459 passed` vs `145 failed, 464 passed`)

### 2.1 Artifact Hashes
- **Historical Committed RED Receipt (Untouched):** [`../red/red-review-34a04eaf.txt`](../red/red-review-34a04eaf.txt)
  - Summary: `146 failed, 459 passed in 10.82s` (`605` total items)
  - Git blob `LF` SHA-256: `ae5048513bb4cc07fff9454fe0e8e4061207f50c4cce456254fbadad126f12cd` (`251526` bytes)
  - Windows `CRLF` / working-tree SHA-256: `12f9f0f50460ac425d7cf08d9445367c90a6a1e684e7516ad81039a73ff484d0` (`254680` bytes)
- **Clean Cross-Version Reproduction Receipt:** [`reproduced-red-34a04eaf-with-55c657b8-tests.txt`](reproduced-red-34a04eaf-with-55c657b8-tests.txt)
  - Provenance: `SOURCE_COMMIT = 34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7`, `TEST_COMMIT = 55c657b8be715cda0edcc9e6e2ec1b3a204bdb65` (`test_shared_ask_grammar.py` blob SHA-256: `7a166b03b20c5682e1f01518e484cc67a427cb0797c9c4f3db0e39bd57aa38d0`)
  - Summary: `145 failed, 464 passed in 9.51s` (`609` total items)
  - Git blob `LF` SHA-256: `c1a24f4be1ea6ee3786be20f0faa09203dd696d664afc09c4335a35f2c67f85f` (`129783` bytes)
  - Windows `CRLF` SHA-256: `27fdd44793af9ff55bee1c7faf0f0a78031652a961efef73fcad02ff1c10f327` (`131124` bytes)

### 2.2 Exact Technical Cause of the Delta (`146/459 [605]` → `145/464 [609]`)
1. **Delta 1 (`-1 failed`, `+1 passed`):**
   - When `red/red-review-34a04eaf.txt` was captured on `34a04eaf`, `test_cra_goal_clause_does_not_hide_bare_quantifier_or_incomplete_clause_route_b` (`backend/tests/geometry/test_shared_ask_grammar.py` line 568) asserted strict equality `assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED"`.
   - On baseline `34a04eaf`, the probe `line:Chứng minh BD ⊥ SC, 2 SC, tính {O}.` returned `r.status == "REFUSED"` with `r.code == "GOAL_CLAUSE_NOT_PREMISE"`, causing that item to fail at `red/red-review-34a04eaf.txt` line 206 (`AssertionError: assert ('REFUSED' == 'REFUSED' and 'GOAL_CLAUSE_NOT_PREMISE' == 'QUESTION_CONTEXT_UNSUPPORTED')`).
   - Before committing `55c657b8`, line 568 of `test_shared_ask_grammar.py` was relaxed to `assert r.status == "REFUSED" and r.code in ("QUESTION_CONTEXT_UNSUPPORTED", "GOAL_CLAUSE_NOT_PREMISE")`, so that 1 item passes when the committed `55c657b8` test file is executed against `34a04eaf` (`146` → `145` failed; `+1` passed).
2. **Delta 2 (`+4 passed`, `+4 total items`):**
   - When `red/red-review-34a04eaf.txt` was captured, `test_shared_ask_grammar.py` contained `605` items (`146 + 459 = 605`) prior to appending `test_cra_crb_ima_mutants_are_killed_by_regression_suite` (`4` parametrized items at lines 667–703).
   - Those 4 monkeypatch items assert `assert r.status == "SERVED"` when each guard is disabled; on the broken baseline `34a04eaf`, those 4 probes are already falsely served (`r.status == "SERVED"`), so all 4 items trivially pass (`459 + 1 + 4 = 464` passed; `605 + 4 = 609` total items).

---

## 3. Clean-Worktree GREEN Verification Receipts at `55c657b8`

All GREEN verification suites were re-executed in an isolated, clean detached worktree at `55c657b8be715cda0edcc9e6e2ec1b3a204bdb65` (`WORKING_TREE_STATUS: CLEAN (0 modified, 0 untracked)`) and written with full provenance headers into [`green-55c657b8/`](green-55c657b8/):

| Receipt File | Command | Exit Code | Result Summary | Git Blob `LF` SHA-256 (Bytes) | Windows `CRLF` SHA-256 (Bytes) |
|---|---|---|---|---|---|
| [`green-55c657b8/suite1-shared-ask-grammar-55c657b8.txt`](green-55c657b8/suite1-shared-ask-grammar-55c657b8.txt) | `python -m pytest backend/tests/geometry/test_shared_ask_grammar.py -q` | `0` | `609 passed in 6.36s` | `ea1c7cb4662b166a776cf88ae846fa0a0ae42aeb8d099856821c1384f984b0f7` (`1112`) | `f4b61a78e0f896266755e6c4e05ca241cdd2d0a7936595767f910c3cd16d6414` (`1132`) |
| [`green-55c657b8/suite2-result-binding-planning-55c657b8.txt`](green-55c657b8/suite2-result-binding-planning-55c657b8.txt) | `python -m pytest backend/tests/geometry/test_result_binding_planning.py -q` | `0` | `72 passed in 1.60s` | `18db02bccc7f1d993e6cf290c48b592e508e177e95ce39c134fe8c7b0c92ff17` (`476`) | `3b726fc141b6044b1c502340d3aa248f082112905270a57d6a3a42840470e818` (`488`) |
| [`green-55c657b8/suite3-grammar-probe-55c657b8.txt`](green-55c657b8/suite3-grammar-probe-55c657b8.txt) | `python ../docs/evaluation/geometry/runs/shared-ask-grammar-safety/grammar_probe.py <out.json>` (`cwd=backend`) | `0` | `0 WRONG_SERVED`, `10 FALSE_REFUSAL` (B: `84 CR, 33 CS, 6 FR`; A: `52 CR, 16 CS, 4 FR`) | `c6b781749863aa87b7b3e94e1a798798400cda0795d524cbd319cf9894734f02` (`1097`) | `5c07d2065c645fad9fffa237c347b2aa5b8f472b7378b7e5f5dae92aa01ae48a` (`1118`) |
| [`green-55c657b8/suite3-grammar-probe-55c657b8.json`](green-55c657b8/suite3-grammar-probe-55c657b8.json) | JSON output of `grammar_probe.py` at `55c657b8` | `0` | `0 WRONG_SERVED` across all rows | `f46ba2c950c04803ec6570ec17b8fc6be2e2eb7c9659ffc211ca70604bea99c2` (`39346`) | `98c7dfd28f0ef7fea190c781736323bbdea9d3ef737fdb70610658fee3cff73e` (`41409`) |
| [`green-55c657b8/suite4-hybrid-compiler-benchmark-55c657b8.txt`](green-55c657b8/suite4-hybrid-compiler-benchmark-55c657b8.txt) | `python -m pytest backend/tests/geometry/test_hybrid_compiler_benchmark.py -q` | `0` | `94 passed, 4 xfailed in 2.13s` | `a624e993ddcdc4edad2b451cfda542c67a447ed967573177870a4ae15bf9597e` (`569`) | `b99bc44240dba296cabb5f18a5a83864ec91a8277f1da12ff5eed68344abe3ce` (`582`) |
| [`green-55c657b8/suite5a-7files-historical-set-55c657b8.txt`](green-55c657b8/suite5a-7files-historical-set-55c657b8.txt) | 7-file historical Suite 5 command (exact file list from `34a04eaf`) | `0` | `804 passed, 1 xfailed in 8.11s` | `aa5d06e4bf78257f508b06cf7d3839c603ef80161f5b21097dc4ea8767643a12` (`1757`) | `525298a888b3514a88b76ad1bb4e408c097ac6261b40aca3a6eba25e5036a7e0` (`1781`) |
| [`green-55c657b8/suite5b-8files-expanded-set-55c657b8.txt`](green-55c657b8/suite5b-8files-expanded-set-55c657b8.txt) | 8-file expanded Suite 5 command (7 historical files + `test_text_to_geometry_functions.py`) | `0` | `868 passed, 1 xfailed in 9.38s` | `6670c1378258fd872debc1c162bc348c08bb05d2142291dd44b9f83b44372a30` (`1928`) | `c5de46fd1891c343df8a1f8f09a608a0e61c0435b2fe0e8ef9bbf4ee300453b0` (`1953`) |
| [`green-55c657b8/suite6-full-geometry-regression-55c657b8.txt`](green-55c657b8/suite6-full-geometry-regression-55c657b8.txt) | `python -m pytest backend/tests/geometry -q --tb=short` | `1` | `9 failed, 7750 passed, 1 deselected, 6 xfailed, 2 warnings in 270.03s` | `38fc9c959b0d8a06bda59a48e973f30dba1d67156347d9836ac1db4d5ccd3068` (`15345`) | `42dd07dc7924fc6eb12578e4e35a5febbd8525473cd3bf1ecf2848686a7375ae` (`15557`) |
| [`green-55c657b8/mutation-4-monkeypatch-tests-55c657b8.txt`](green-55c657b8/mutation-4-monkeypatch-tests-55c657b8.txt) | `python -m pytest backend/tests/geometry/test_shared_ask_grammar.py -k test_cra_crb_ima_mutants_are_killed_by_regression_suite -v` | `0` | `4 passed, 605 deselected in 0.72s` | `04fdfff35918bddc1fd256b320208c823fc281307022b5dcde75063cbca97536` (`1639`) | `abb0dc6b950ae6b5908544e8ffde0b0177440c38ffeb3ae4bf32af199e142e67` (`1663`) |

---

## 4. Suite 5 Discrepancy Reconciliation (`804 passed, 1 xfailed` vs `868 passed, 1 xfailed`)

- At `34a04eaf` ([`archive-34a04eaf/suite5-ask-context-section-suites.txt`](archive-34a04eaf/suite5-ask-context-section-suites.txt)), the Suite 5 command ran **7 test files**:
  1. `backend/tests/geometry/test_goal_directed_section_planning.py`
  2. `backend/tests/geometry/test_two_line_plane_section.py`
  3. `backend/tests/geometry/test_question_local_givens.py`
  4. `backend/tests/geometry/test_question_followup_context.py`
  5. `backend/tests/geometry/test_premise_source_coverage.py`
  6. `backend/tests/geometry/test_hybrid_ask_operand_binding.py`
  7. `backend/tests/geometry/test_source_gate_clause_role.py`
  - Result on both `34a04eaf` and `55c657b8` ([`green-55c657b8/suite5a-7files-historical-set-55c657b8.txt`](green-55c657b8/suite5a-7files-historical-set-55c657b8.txt)): **`804 passed, 1 xfailed`**.
- At `55c657b8` ([`../verification/suite5-ask-context-section-suites.txt`](../verification/suite5-ask-context-section-suites.txt) and [`green-55c657b8/suite5b-8files-expanded-set-55c657b8.txt`](green-55c657b8/suite5b-8files-expanded-set-55c657b8.txt)), an **8th test file** was appended to the command:
  8. `backend/tests/geometry/test_text_to_geometry_functions.py` (**`64` test items**)
  - Result: `804 + 64 =` **`868 passed, 1 xfailed`**.

---

## 5. Mutation Evidence Reconciliation

- **Retraction of Verbal Overclaim:** The verbal turn summary for `55c657b8` erroneously referred to "`16` mutants / `REVIEW_4ACFC731_MUTANTS`", conflating the `16` parametrized items of `test_ima_angle_measure_so_do_goc_is_refused_while_plain_angle_cos2_is_served` with the monkeypatch test function. No `REVIEW_4ACFC731_MUTANTS` symbol or 16-mutant suite exists in `backend/tests/geometry/test_shared_ask_grammar.py`.
- **Actual Committed Check:** `backend/tests/geometry/test_shared_ask_grammar.py::test_cra_crb_ima_mutants_are_killed_by_regression_suite` (lines 667–703) defines **4** parametrized monkeypatch probes:
  1. `cra_allow_bare_quantifier_in_goal`
  2. `cra_skip_relational_predicate_after_comma`
  3. `crb_permissive_note_fallback_true`
  4. `ima_allow_so_do_goc_as_cos2`
- **Methodological Scope:** Each of the 4 items monkeypatches one guard helper in `registry.py` and asserts that a single targeted adversarial probe flips from `REFUSED` to `SERVED`. This is a **4-item targeted monkeypatch regression check**, not a full-suite mutation testing run. Its provenance receipt is [`green-55c657b8/mutation-4-monkeypatch-tests-55c657b8.txt`](green-55c657b8/mutation-4-monkeypatch-tests-55c657b8.txt).

---

## 6. Full Geometry Regression (`Suite 6`) & Candidate Freeze Status

- **Why `verification/suite6-full-geometry-regression.txt` showed `10 failed, 7749 passed`:** That run was executed *prior* to `git commit` while the working tree had uncommitted changes, causing `backend/tests/geometry/test_holdout_readiness.py::test_bao_cao_da_sinh_va_KHONG_TROI` to fail its clean-git-tree check alongside the 9 candidate verify-only guards.
- **Clean Committed Worktree Result at `55c657b8` ([`green-55c657b8/suite6-full-geometry-regression-55c657b8.txt`](green-55c657b8/suite6-full-geometry-regression-55c657b8.txt)):**
  - **`9 failed, 7750 passed, 1 deselected, 6 xfailed, 2 warnings in 270.03s`**
  - `test_holdout_readiness.py::test_bao_cao_da_sinh_va_KHONG_TROI` **PASSES** on the clean committed tree.
  - The remaining **9 failures** are exclusively the candidate-freeze verify-only guards (`test_evaluation_candidate_freeze.py` [6], `test_single_source_of_truth.py` [2], `test_migration_gate_enforcement.py` [1]), which compare `HEAD` against `docs/evaluation/geometry/EVALUATION_CANDIDATE.json` (intentionally kept frozen at `4b95dcc63d86716a64c2057232c9d7e0c2501ba8`).
- **Gate Status:** Full Geometry Gate remains **NOT PASS (`PENDING FINAL CANDIDATE`)** until independent review passes and candidate refreeze is authorized.
