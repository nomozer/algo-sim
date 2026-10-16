# E-1 Correction Addendum 3 — manifest supersession and consistency closure (IM-1 / IM-2, NB-1…NB-6)

Append-only. [`manifest.json`](manifest.json), [`correction-addendum.md`](correction-addendum.md),
[`correction-addendum-2.md`](correction-addendum-2.md), every receipt in [`archive-34a04eaf/`](archive-34a04eaf/),
[`green-55c657b8/`](green-55c657b8/), [`reproduced-red-34a04eaf-with-55c657b8-tests.txt`](reproduced-red-34a04eaf-with-55c657b8-tests.txt),
[`../red/red-review-34a04eaf.txt`](../red/red-review-34a04eaf.txt) and [`../verification/`](../verification/) are unchanged.
This layer closes the two IMPORTANT findings and six NONBLOCKING notes of the independent short review of `2666d334`.
That review was delivered in conversation; **no review artifact exists in the repository** (see NB-6).

## 1. Identity

| item | value |
|---|---|
| product commit (code-reviewed) | `55c657b8be715cda0edcc9e6e2ec1b3a204bdb65` (`backend/app` tree `5bb9a890a1d2bdfb5d747aedfddcf31aa429de6e`, `backend/tests` tree `471bee5ee76b840f1a4360df575de0828ee629c1`) |
| evidence commits | `ae53195639ffd5b75f2ebc26269a9ed2f6d8916f` (receipts + manifest + addendum 1), `2666d334cd1024c1321fa35c419d636619b47b95` (addendum 2) |
| historical receipts commit | `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7` |

## 2. IM-1 — fields of `manifest.json` superseded by this layer

Scope of supersession: **only the JSON paths below**. Every other field of `manifest.json` keeps its meaning. That includes
all hashes and byte counts, the 6 restored-receipt entries, `green_receipts_55c657b8`, `suite5_reconciliation`,
`mutation_reconciliation` (whose `erroneous_report_claim_retracted` is itself a correct retraction), `gate_status` and the
receipt path in `clean_committed_receipt_path`. Line numbers refer to the blob at `ae531956`/`2666d334`
(`git rev-parse 2666d334:<manifest>` = `9143cd97…`, unchanged since `ae531956`).

| line | JSON path | retracted content (abridged) | why retracted | verified replacement |
|---|---|---|---|---|
| 155 | `$.red_evidence_reconciliation.exact_delta_explanation[0]` | "Delta 1 (-1 failed, +1 passed) … line 206 … `[line:… 2 SC, tính {O}.]` … making that 1 item pass (146 -> 145)" | The `2 SC` item is **SERVED** on `34a04eaf` (historical block at line 563, `{'q': '√11'}`) and fails in both receipts. Two other items flip. | §3 A: two items flip FAIL → PASS. |
| 156 | `$.red_evidence_reconciliation.exact_delta_explanation[1]` | "Delta 2 (+4 passed) … 4 items … trivially pass … (459 + 1 + 4 = 464 passed)" | Only 3 of the 4 pass. `cra_skip_relational_predicate_after_comma` fails with `AttributeError` (reproduced receipt lines 1191–1194). | §3 B: 3 pass, 1 fails. |
| 312 | `$.suite6_full_geometry_reconciliation.clean_committed_worktree_55c657b8_result` (key **and** value) | "… passes on clean committed tree; … EVALUATION_CANDIDATE.json remains frozen at `4b95dcc63d86716a64c2057232c9d7e0c2501ba8`" | The identifier does not exist (`git cat-file -t` fails). The run's working-tree state is not attested (§5). | Counts `9 failed, 7750 passed, 1 deselected, 6 xfailed` stand. Candidate identifier `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25` in `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` (`measured_system.tree_hash`). The source is the committed product tree `55c657b8`; working-tree cleanliness is **NOT_ATTESTED**. |
| 313 | `$.suite6_full_geometry_reconciliation.clean_committed_receipt_path` (key name only) | the word "clean" in the key | Same as line 312. | The path value is correct. Read it as "suite6 receipt for product commit `55c657b8`". |

Related fields checked and **kept** (the evidence supports them):
- `$.suite6_full_geometry_reconciliation.overwritten_pre_commit_55c657b8_result` ("ran before git commit when working tree
  was dirty"). Supported by the overwritten receipt itself: `55c657b8:…/verification/suite6-full-geometry-regression.txt`
  line 312 shows `test_bao_cao_da_sinh_va_KHONG_TROI` failing with blocker `CÂY LÀM VIỆC BẨN` and `git_sha` `34a04eaf…`,
  and its module path is `D:\Documents\projects\algo-sim\…`, i.e. the main checkout before the commit.
- `$.red_evidence_reconciliation.historical_committed_red_receipt.test_state_when_captured` (605 items, strict
  `QUESTION_CONTEXT_UNSUPPORTED`, monkeypatch items not yet present). Consistent with the historical receipt: it never
  names `test_cra_crb_ima_mutants…`, and its two flipping items fail on `== 'QUESTION_CONTEXT_UNSUPPORTED'` (lines 435,
  482). The exact file content was never committed (**NOT_VERIFIED**, as in addendum 2 §3).

**Consumers of `manifest.json`** (searched at `2666d334`):
- No product code, test or script names this file or its run folder. `git grep "shared-ask-grammar-safety|evidence-reconciliation" -- backend frontend/scripts frontend/src`
  finds only code comments.
- `backend/scripts/audit_named_operand_ergonomics.py` and `backend/scripts/replay_nested_operand_history.py` glob every
  `*.json` under `docs/evaluation/geometry`, but they extract only Semantic Program `programs` structures, which the manifest
  does not contain.
- The scripts that read a `manifest.json` (`acceptance_integrity.py`, `certify_*`, `run_*_acceptance.py` …) read their
  own run folders.
- The manifest is cited only by documents: `correction-addendum.md`, `correction-addendum-2.md`, `handoff.md`.

**No automated acceptance consumes the retracted fields**, so this documentation layer is sufficient. Schema and
consumers are not changed.

## 3. RED mechanism (restated; verified in addendum 2 §3 and by the independent short review)

- Historical RED [`../red/red-review-34a04eaf.txt`](../red/red-review-34a04eaf.txt): 146 failed, 459 passed (605 items).
- Reproduced RED [`reproduced-red-34a04eaf-with-55c657b8-tests.txt`](reproduced-red-34a04eaf-with-55c657b8-tests.txt):
  145 failed, 464 passed (609 items).
- **A. Two items flip FAIL → PASS.** `…route_b[line:Chứng minh BD ⊥ SC, gấp đôi {O}, tính {O}.]` (block 424, message 435)
  and `…[line:… một nửa {O}, …]` (block 471, message 482). Both are refused with `GOAL_CLAUSE_NOT_PREMISE` on `34a04eaf`;
  `55c657b8:backend/tests/geometry/test_shared_ask_grammar.py:568` also accepts that code.
- **B. Four monkeypatch items added; 3 pass, 1 fails.** The failing item is `[cra_skip_relational_predicate_after_comma]`:
  line 686 sets `_VI_TU_MUC_TIEU`, which `34a04eaf:registry.py` does not define (0 occurrences; 2 at `55c657b8`), hence
  `AttributeError`. This is a mutation that cannot be applied to the baseline, not a surviving mutation.
- **C.** 146 − 2 + 1 = 145; 459 + 2 + 3 = 464; 605 + 4 = 609.

## 4. Candidate (verified from Git and the file)

| kind | value |
|---|---|
| path | `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` |
| candidate identifier (`measured_system.tree_hash`, content hash of `MEASURED_SYSTEM_PATHS` computed by `freeze_evaluation_candidate.py`; recorded `commit` `9ce1298f8f7cef090169c5ae5a64b0625a1ddbd4`) | `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25` |
| current measured-system hash at `55c657b8` (same algorithm) | `30808cb002b377e4ad68f224363ef58ab6e51e0facba7e2d4c501419f58d91dc` |
| Git blob of the JSON | `033284ce9e17a17e1ca7af360b64b3bb27e0ee92` |
| SHA-256 of the JSON | LF blob `a7920951a7e3273559ef7557a812dbebf601e6f302a8c323145c0652c84135bf` (3487 B); CRLF working tree `20ebeaed40dca6cc631b74a737d67c098e5199d784595e45bee6988dc7d8187b` (3603 B) |

## 5. IM-2 — committed tree vs. checkout vs. clean working tree

These are three different properties. None of them implies another:
- A Git tree hash proves which **committed source** a commit holds.
- A run's location (main checkout or detached worktree) is attested only by paths the run itself printed.
- A **clean working tree** at run time is attested only by a status captured at run time and not contradicted by the
  receipt.

| receipt | committed source under test | location attested by the receipt | working tree at run time |
|---|---|---|---|
| reproduced RED | product `34a04eaf` + test file of `55c657b8` (SHA `7a166b03…`) | detached checkout (`…\Temp\algosim-e1-wt-34a04eaf\…` in traceback) | **modified by design** (`WORKING_TREE_STATUS: M backend/tests/geometry/test_shared_ask_grammar.py`), not clean |
| `mutation-4-monkeypatch-tests-55c657b8.txt` | `55c657b8` (header) | **main checkout** (`rootdir: d:\Documents\projects\algo-sim\backend`) | **NOT_ATTESTED** (no status line; the main checkout always holds the user's untracked favicon) |
| suite1, suite2, suite3, suite4, suite5a, suite5b | `55c657b8` (header) | not attested (`-q`: no rootdir, no absolute path) | **NOT_ATTESTED** (the header's "CLEAN (0 modified, 0 untracked)" is a self-claim with no corroboration) |
| suite6 | `55c657b8` (header) | not attested. Its absolute paths (lines 177, 178, 182) are `d:\…\backend\.venv\…` site-packages, which every run shows, whether worktree or main checkout. | **NOT_ATTESTED** |

Living documents are corrected to match this table (§7).

## 6. NB-1 … NB-6

| note | addendum-2 location | correction |
|---|---|---|
| NB-1 | line 126 "no absolute repository path" | False for suite6: it has `.venv` absolute paths (lines 177, 178, 182). These do not attest the run location, so the NOT_ATTESTED conclusion stands. |
| NB-2 | line 56 "only `CANDIDATE_VERIFY` is false" | `RAW_HISTORICAL_OUTPUT_AVAILABLE` is also `false`, but it is a hardcoded constant (`diagnose_analyze_failure_cluster.py:158`), not part of the `all_pass` AND (lines 125–140). Among the AND conditions, only candidate verification is false. |
| NB-3 | line 52 and row #9 | `test_C2b_candidate_hien_tai_phai_duoc_KHAI` does not call `--verify`. It compares `current_candidate_hash` in the current divergence declaration with `freeze_evaluation_candidate.measured_system_hash()`. That declaration is resolved through the `corrects` chain to [`../inputs/candidate_divergence.json`](../inputs/candidate_divergence.json) (`4b95dcc6…` vs current `30808cb0…`). It is candidate-related and is resolved by refreeze **plus** an updated divergence declaration. |
| NB-4 | line 35 "verbatim" | The node IDs in addendum-2 §2 are normalised: `\` → `/`, and some are shortened with `…`. The verbatim form is in the receipt's `FAILED` lines (`green-55c657b8/suite6-…txt`, lines 203–211). |
| NB-5 | line 98 "present" | The reproduced RED ran with `-q`, so passing items are not named. "3 of 4 pass" is an **inference by elimination**: the test-file SHA matches `55c657b8`, 145 + 464 = 609, and only one mutant id is in `FAILED`. The reviewer's separate `-rA` re-run (3 PASSED, 1 FAILED) is a new measurement outside the repository, not historical provenance. |
| NB-6 | lines 8, 111, 130–132, §5 rows at lines 138 and 144 | The independent reviews of `55c657b8`, `ae531956` and `2666d334` exist only as conversation reports, **not as repository artifacts**. Their re-runs are external corroboration, not committed evidence. The "verify-only" row of addendum-2 §5 splits into two claims: candidate verification failed in the historical run (VERIFIED by receipt #1, line 55); it was the *only* failing condition (shown only by a measurement made 2026-10-16, not historical provenance). |

## 7. Living-document corrections in this commit

- [`../report.md`](../report.md) §10 item 2: "worktree tách biệt sạch" becomes "checkout tách rời; file test được thay có
  chủ đích (không sạch)".
- [`../report.md`](../report.md) §10 item 3: "`suite6` trên cây commit sạch" becomes "mã sản phẩm của commit `55c657b8`;
  trạng thái working tree lúc chạy NOT_ATTESTED".
- [`../handoff.md`](../handoff.md) E-1 bullet: same correction for suite6, plus a link to this layer.

Historical files (manifest, addendum 1, addendum 2, receipts) keep their text and are superseded through this layer.

## 8. Verified / not verified / not attested

| claim | status |
|---|---|
| nine failures, node IDs, files, assertion lines | VERIFIED (receipt + `55c657b8` sources) |
| candidate verification false in the historical suite6 run | VERIFIED (receipt, test #1 line 55) |
| candidate verification is the only failing precheck condition | measured 2026-10-16 only; not historical provenance |
| RED mechanism (2 flips; 3/4 pass by elimination; 1 `AttributeError`) | VERIFIED (receipts + sources); 3/4 is an inference |
| 605-item intermediate test file | NOT_VERIFIED (never committed) |
| working-tree state of mutation, suite1–5b and suite6 runs | NOT_ATTESTED |
| automated consumers of the retracted manifest fields | none found (§2) |

## 9. Gates and known limitations

- Candidate **not refrozen** (`4b95dcc6…` vs current `30808cb0…`); the divergence declaration still names `4b95dcc6…`.
- Authoritative T3 **not run**. Full geometry gate **NOT PASS** (9 candidate-related failures).
- `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid production NO-GO.
- Known non-blocking product limitations from the code review: surviving source mutations M5/M6, rounding and
  angle-measure requests refused by policy, partial answers to multi-question problems.
- E-1 status: **PENDING INDEPENDENT SHORT REVIEW** of this layer.

## 10. Precedence and consistency sweep

Precedence, newest first: this file → `correction-addendum-2.md` → `correction-addendum.md` → `manifest.json`. It is
**limited to the items named here** (§2 paths, §5 environment, §6 NB rows). On every other point the earlier files stand.

Sweep (`clean|sạch|4b95dcc63d|146 -> 145|459 + 1 + 4`) over the six E-1 files at this commit:

| match | class |
|---|---|
| `manifest.json` lines 155, 156, 312, 313 | historical, superseded (§2) |
| `correction-addendum.md` lines 40, 53, 57, 59, 107, 109, 110 | historical, superseded by addendum-2 §2–§3 and §5 here |
| `correction-addendum-2.md` lines 119–120, 126 | current-verified (they record that "CLEAN" is an unattested self-claim); 126 refined by NB-1 |
| `correction-addendum-2.md` line 131 "clean detached worktree" | limitation: external reviewer claim (NB-6) |
| `report.md` lines 48, 54, 57 (`9ce1298f`) | historical: an earlier wave, reviewer-attested, outside E-1 |
| `report.md` §10 items 2–3, `handoff.md` E-1 bullet | living, fixed in this commit (§7) |
| `handoff.md` "detached worktree sạch" for future T3 | current: an instruction, not a claim |
