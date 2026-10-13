# Independent LOCAL Source Grounding review

Scope: final product `b264828f`, branch documentation tip `0bb3f3ed`, main baseline `7767c7e1`, prior review tip `90ce6497`, and the subsequent working-tree numeric-ownership fix. Read-only review of tracked files; no provider calls, network, issue filing, staging, or edits to user files. This is a targeted review, not a repository audit.

## Verdict

**NON-BLOCKING after the numeric-ownership working-tree fix. Integrate the research source with Hybrid off / `LLM_ONLY` default.** No remaining new Critical or Important finding outside the declared limits was found in this review. This verdict is independent of the parent agent's later clean T3/integration checks.

The first review pass found one Important gap outside the declared limits. It was preexisting at main and the prior review tip, not a regression from `f8ac9f4b` or `b264828f`. The subsequent minimal fix closes the reproduced gap; the independent follow-up verification is green.

## Important finding, now closed: overlapping quotes duplicated a value's authority

Use the canonical square pyramid: base ABCD is a square of side 2; SA is perpendicular to the base; SA = 3; ask SC. Replace the length sentence with `SA = 3 và SB = 3.` and give the single SA-length fact quotes `["SA = 3", "SA = 3 và SB = 3."]`.

Before the fix, both A and B served `SC = √17` with a scene, despite SB = 3 contradicting the constructed geometry (SB² = 13). `["SA = 3", "SA = 3, đổi AB thành 3."]` also served even though the source explicitly replaced AB's square-side value. Reversing the first pair of quotes caused refusal on the hardened tips, so the result depended on quote order.

Cause: `backend/app/simulation/geometry_functions/registry.py:1233` created one numeric range record per quote/value, and `:1294` spent records by tuple object identity. Overlapping quotes therefore gave one call field more than one numeric allowance. The report's declared numberless-long-quote limitation did not cover this numerical case.

The working diff now gives each range an owner `(call index, value field)` and spends that owner across all its quotes (`registry.py:1233`, `:1239`, `:1259`, `:1294`, `:1300`). This preserves quote-based positioning while keeping numerical authority with the validated field. It adds no second geometry state or extraction authority.

Independent follow-up probes on both routes:

- Short-first and long-first overlapping quotes carrying SB = 3 now refuse `SOURCE_PREMISE_UNREAD`, with empty answers and no scene.
- Overlapping quotes carrying `đổi AB thành 3` now refuse with the same code and empty output.
- Overlapping quotes of the one legitimate SA = 3 occurrence serve `SC = √17` in either order.
- Separate validated fields with the same value remain usable: square side = 2 and SA = 2, with overlapping quotes of SA, serve `SC = 2√3` (SC² = 12) on both routes.

## Seven requested checks

1. **One semantic authority:** A enters `engine.dung_tu_loi_goi`; B plans and enters the same function. `engine.py:966` invokes `registry.kiem_nguon`, which invokes `_kiem_du_kien_cau_hoi` (`registry.py:969`), which invokes `_kiem_vung_tien_de` (`:1066`). The new helper only checks source coverage and refuses; it does not alter geometry. B's `read_quotes` are restricted by the same gate's role/negation readers.
2. **Premises outside quotes:** `Đổi SA thành 5.`, `Nhân đôi mọi kích thước.`, and `Giả sử SA = 5.` now refuse before a scene/answer. The same inputs served at main baseline.
3. **Long quotes:** Extra numerical claims in a single long quote refuse. The overlapping-quote numerical escape discovered here is now closed. Numberless relation/scale claims inside another call's long quote remain a declared, preexisting gap.
4. **Connectors:** `do`, `vì`, `bởi vì`, `nhờ`, `còn`, and `ngoài ra` cannot carry an unread changed premise through a goal. `rồi suy ra` and `do đó / vì vậy / vì thế suy ra` preserve chained goals; a later causal changed premise still refuses. Bare `và` and contrast `song` remain declared gaps.
5. **Goal / hypothesis / negation separation:** A plain premise mislabeled `prove`, and `SA = 5 và chứng minh ...`, refuse. Valid proof facts stay in `goal_checks` with `proof_status=UNVERIFIABLE` and `can_present_as_proven=False`; conditions and unsupported negations refuse. Goals are not promoted to GIVEN.
6. **Positive controls:** Canonical/chained goals serve again after `f8ac9f4b`. Right-prism lateral height and regular-pyramid centre height serve. AB' as a right-prism height, and SA/AO as the regular-pyramid height, refuse. No new false refusal from the final fixes was found.
7. **Connected construction paths:** Construction-only, auxiliary distance decomposition, and derived-plane section paths retain the same coverage obligation. Their focused tests pass; the premise-changing refusal cases pass. No bypass specific to these paths was found.

## Declared residuals reproduced and classified

All three groups below reproduce on A and B at final tip, prior tip, and main baseline. Every serve used the original figure (`SC = √17`). They are preexisting declared safety gaps, not regressions from the final two product commits:

| Input change | Result | Exact cause/location |
| --- | --- | --- |
| `Chứng minh SC ⊥ BD và đáy là hình chữ nhật.` | SERVED; also with a B prove quote | Bare `và` does not terminate a goal: `_KET_MUC_TIEU` / `_ket_muc_tieu`, `registry.py:1475`, `:1490` |
| `Chứng minh SC ⊥ BD song đáy là hình chữ nhật.` | SERVED; also with a B prove quote | `song` is intentionally absent to preserve `song song`; same goal-end locations |
| Another call quotes `SA vuông góc với (ABCD) và SB ⊥ (ABCD).`, or `SA = 3 và mọi kích thước gấp đôi.` | SERVED | A sentence-local validated quote blanks the whole span, `registry.py:1235–1246`; numberless claims have no extra numeric obligation |
| `Suy ra SB = 7.` | SERVED | Goal length check only compares existing validated segment candidates, `registry.py:1276–1280`; SB has no validated value |

Conservative false refusals reproduced: `Cạnh bên SA là đường cao.`, `Câu 2 (1 điểm).`, and `Chứng minh ... bằng cách áp dụng định lý Pythagoras.` They were already present at the prior review tip and are declared. Open unsupported wording and unverified true second clauses remain closed-grammar refusals. They do not justify presenting coverage as arbitrary Vietnamese completeness.

## Verification and limits of this review

- Before numeric follow-up: four focused modules, **397 passed, 1 xfailed**.
- After the ownership fix: `test_premise_source_coverage.py`, `test_source_grounding_closure.py`, `test_goal_directed_section_planning.py`, and `test_hybrid_compiler_selection.py`: **415 passed, 1 xfailed**.
- Independent comparative probes: **104 route evaluations per revision**, **312 total**, at final tip / prior tip / main. No probe raised an exception. Follow-up fix probes: **12 route evaluations** including independent same-value owners.
- Prior/main comparison used isolated process-local execution of `git show <rev>:.../registry.py` and the shared route harness. The engine/route differences from main were inspected and are only `read_quotes` plumbing. This is a narrow gate comparison, not authoritative clean-worktree baseline verification.
- No full T3, browser harness, live provider measurement, or whole-repository audit was run by this reviewer.
- Scratch probe code/JSON files were removed after transmitting their findings. This review note remains for the parent to copy. No tracked file was modified by the reviewer.
