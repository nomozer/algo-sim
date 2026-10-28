# W3-F1 handoff correction addendum

Task: `HYBRID_V2_WAVE3_EVIDENCE_W3_F1_MAIN_INTEGRATION` · 2026-10-28.
Classification: `DOCUMENTATION_CORRECTION_ONLY`.

This addendum corrects **handoff.md §3, “Remaining Open Wave 3 Failure Clusters (For Next Repair Waves)”**, items 1–4. That section incorrectly renames W3-F2, W3-F3 and W3-F4 and assigns the negative refusal-reason disagreements to W3-F5. The original handoff and all historical evaluation receipts remain unchanged. This addendum supersedes that section only.

The authoritative cluster identities come from the original Wave 3 `results/diagnostics.json` and `report.md` at `0943f0ee6bd2a2b297827e39fa7c07054d716ea9`, consistent with this run's `plan.md`. Counts below were checked against the original scored cases and the locked W3-F1 regression, then verified by an offline 144-case replay whose outcomes, refusal codes and transitions match every recorded case. Machine receipt: [verification/handoff-correction.json](verification/handoff-correction.json).

| Cluster | Authoritative identity | Historical first refusal | After W3-F1 |
|---|---|---:|---:|
| W3-F1 | SECTION_AND_AREA_COMPOUND_QUESTION_GROUNDING | 24 | 0 |
| W3-F2 | DIVIDE_SEGMENT_AND_PROJECTION_KEYWORD_LEXICON | 14 | 21 |
| W3-F3 | PARALLEL_TWO_LINES_SLICE_GRAMMAR_COVERAGE | 10 | 16 |
| W3-F4 | CUBE_BASE_SQUARE_EDGE_LENGTH_BINDING | 3 | 5 |
| W3-F5 | GIA_SU_PREMISE_OPENER_CONDITIONAL_FALSE_POSITIVE | 1 | 1 |
| Total positive false refusals | | 52 | 43 |

Of the 24 historical W3-F1 cases, 9 become `SERVED_CORRECT`, 7 expose W3-F2, 6 expose W3-F3, and 2 expose W3-F4. The other 28 historical positive false refusals retain the same outcomes and codes. These are first-refusal counts; a case can contain a masked secondary defect. This classification does not establish that every other defect has been identified.

Negative refusal-reason disagreement is a separate measurement: **12/72 historically, 10/72 after W3-F1**. All 72 negative cases remain refused; correct reason agreement is 60/72 → 62/72. Those 10 disagreements are **not W3-F5**. Positive served-correct is 20/72 → 29/72 and wrong-served remains 0/144.

Historical Wave 3 remains `INDEPENDENT_HOLDOUT_WAVE3_EXECUTED`, independence class `AI_CURATED_PROCEDURAL_INDEPENDENCE`. The W3-F1 replay remains `POST_FEEDBACK_DEVELOPMENT_REGRESSION`, not a new independent blind holdout. This correction changes documentation interpretation only: no product code, corpus, oracle, original scored result, historical count, or locked receipt is modified. F2–F5 repairs remain outside this integration's scope.

## Original T3 log byte preservation

Pre-merge inspection found that the original T3 log mixes CRLF and LF. Its original worktree bytes match the locked receipt: **167,582 bytes**, SHA-256 `885333241d4d723d73edad5b8f2e98ccf3da0700361fbe4eb974893037ddb2f7`. Git's text normalization stores the same log as LF, SHA-256 `103d56849edcf2b956b8f88d0577f751ef6a146a54d81a80a3d111d9ca631623`; a fresh checkout cannot recover the mixed line endings from that blob alone.

The append-only [verification/full-t3/original-log.gz](verification/full-t3/original-log.gz) preserves the exact original raw bytes. Decompress it and verify against `verification/full-t3/receipt.json:log.sha256`. Its compressed hash is recorded in the correction receipt. The existing log and T3 receipt remain untouched. This preserves the existing evidence and does not claim a new T3 run.
