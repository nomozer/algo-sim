# Independent review — delta `10dd6d6e..efb756aa` (2026-10-15)

**Reviewer:** fresh-context, read-only Claude Code subagent (LOCAL), launched by the integration session. It had no
access to that session's reasoning, only the repository and a written brief. It made 0 model/network calls. It
modified no repository file and no ref. Its three temporary detached worktrees (efb756aa, main, 10dd6d6e) were removed.

**Scope:** `git diff 10dd6d6e efb756aa -- backend/app/simulation/geometry_functions/registry.py` (+3/−3).

**VERDICT for the delta: PASS.** CRITICAL 0 · IMPORTANT 2 (both pre-existing, not introduced by the delta,
also present on `main`) · NONBLOCKING 4.

This file records the reviewer's report. The integration session re-ran four of the probes at the research tip and
at `main` in a clean detached worktree (`probes/repro.py`) and got identical results: `SERVED {'q': '√11'}` for
"hai lần", "… BD bình phương." and the space-squeezed quote "bìnhphương", on both trees.

## Answers

1. **Shared regex `_CHAN_TAN_NGU`** is byte-identical to `main`, so other `_duoc_hoi`/`_hoi_dung_cum` callers behave
   as on main. The ordinary ask_* paths still refuse modifiers through the closed `_GIUA_HOP_LE` grammar (probes:
   squared/half distance to (ABCD), half length SC, half/squared section area, "hai lần" distance to (ABCD) are all
   REFUSED `NOT_ASKED_IN_SOURCE`). The motivation is confirmed:
   `test_hybrid_ask_operand_binding.py::test_mutant_is_killed[words before the phrase not checked]` is red at
   `10dd6d6e` (1 failed / 370 passed) and green at `efb756aa`.
2. **`_kiem_phu` (registry.py:734)** is correct for the listed modifiers. NFC-normalised text, `(?i)` and `\s+` work.
   `_bien_cau(s,dau)[0]` is the start of the enclosing sentence. "bình phương", "nửa", "một nửa", "bình phương của",
   uppercase and quote-outside modifiers are REFUSED. "… và nửa chu vi đáy" and "Hơn nữa, …" are correctly SERVED.
3. **`_kiem_result_binding` (registry.py:869)**: `vt` (offset in normalised `de`) is mixed with `m.start()` (offset
   in the raw quote), so the offsets can drift. This is harmless because the sentence `fullmatch` at line 872 is the
   real authority. No false serve was found on the `line_ref` path.
4. **Coverage:** see NONBLOCKING-1/2 and the mutation results.
5. **False serves:** the delta only adds refusal conditions and restores the shared regex to main. A full 36-probe
   diff between `efb756aa` and `10dd6d6e` shows no new serve. The only difference is one refusal code.

## Findings

- **IMPORTANT-1 (pre-existing false serve, guard bypass).** `_kiem_phu` runs the check on
  `s = de[:vt0] + chuan_hoa(q) + de[vt1:]`, which is the source with the AI quote spliced in. `_vi_tri` ignores
  whitespace, so the quote "Tính bìnhphương khoảng cách từ S đến BD." (spaces removed) matches the source
  "Tính bình phương …" while the regex no longer sees the modifier. Result: SERVED `√11`, but the asked value is 11.
  Same at `10dd6d6e`. `main` serves even the exact quote. Fix direction: check the prefix on the original `de`.
- **IMPORTANT-2 (pre-existing false serve, open denylist).** The auxiliary distance(point, line) path uses
  `_duoc_hoi` plus a 2-word denylist, not the closed `_GIUA_HOP_LE`/`_SAU_HOP_LE` grammar used by ordinary asks.
  SERVED `√11` at `efb756aa`, `10dd6d6e` and `main`: "hai lần", "căn bậc hai của", "lập phương", "nghịch đảo",
  "một phần ba", "1/2", "… BD bình phương.". The same sentence aimed at (ABCD) on the ordinary path is REFUSED.
- **NONBLOCKING-1.** The check at line 869 has no observable effect. Removing it leaves the inputs refused, now with
  `SOURCE_PREMISE_UNREAD`. The test asserts REFUSED, not the code.
- **NONBLOCKING-2.** The `nửa` branch at line 734 is untested: the `|nửa`-only mutant survives. "một nửa", uppercase
  and "bình phương của" have no tests.
- **NONBLOCKING-3 (fail-closed).** "Trong nửa mặt phẳng bờ BD chứa S, tính khoảng cách …" is refused. It was
  already refused before, with a different code.
- **NONBLOCKING-4 (environment).** `test_holdout_readiness.py::test_bao_cao_da_sinh_va_KHONG_TROI` fails only in the
  main checkout. `test_analyze_failure_cluster_diagnosis.py::test_tien_kiem_kho` fails only in clean worktrees, both at
  `efb756aa` and at `main`. Both look like local state, unrelated to the delta.

## Tests and mutations (offline)

- The 4-file suite (result binding, ask-operand, clause-role, goal decomposition) passed 371 in the main checkout and
  371 in the `efb756aa` worktree. At `10dd6d6e` it was 1 failed / 370 passed.
- `tests/geometry` in the main checkout: 7117 passed, 1 failed (NONBLOCKING-4), 6 xfailed, 1 deselected.
- M1, removing the line-734 check: KILLED by
  `test_enclosing_sentence_outside_truncated_quote_or_modifier_is_refused[named-line-squared-goal]`.
- M2, removing the line-869 check: SURVIVED. M3, dropping only `|nửa`: SURVIVED.

## Probe evidence

Files in `probes/`, with outputs `probe_{efb,10dd,main}.txt` (`probe.py` + `probe2.py`). The `probe3.py` output
(ordinary-path controls) is summarised in answer 1 and not stored. Comparing `main` with `efb756aa`: main serves 11
additional modifier/whitespace cases that the branch refuses, and the branch adds no serve. The 10 false serves at
`efb756aa` (7 open-denylist wordings, the bare-quote "hai lần" case and 2 space-squeezed quotes) are served
identically on `main`.
