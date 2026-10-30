# Independent final review: READY (0 BLOCKER, 0 MAJOR, 2 MINOR, 6 NOTE)

A fresh-context subagent of this session reviewed HEAD `019b6289` and candidate `4e7fe91d`. It was read-only on the
repositories, made 0 provider calls (sockets blocked) and wrote nothing into any worktree; both trees were clean after
its runs. The harness blocked a report file, so its findings are transcribed here.

The outputs are copied into `final-review/`, and `final-review-files.sha256` lists every file. Two scratch scripts are
listed by hash only and kept local because they contain a local profile path: `gates_ac_scratch.py`, a path-retargeted
copy of `tools/gates_ac.py`, and `replay_wave3_scratch.py`, the same for `tools/replay_wave3.py`.

| id | sev | finding | disposition |
|---|---|---|---|
| FR-1 | MINOR | The status docs were stale and under-claimed: the EVIDENCE_INDEX F7 entry, `handoff.md`, `technical-checkpoint.md`, and AI_CONTEXT_BUNDLE / CURRENT_STATE / OPEN_ISSUES / STATUS_LEDGER (last touched at `df475f06`). | Fixed in this commit: `final-handoff.md` and write-back to the living docs. Docs only, outside `MEASURED_SYSTEM_PATHS`. |
| FR-2 | MINOR | The target-grammar EVIDENCE_INDEX entry still said `CORRECTED_BY = NONE`. | Fixed: it now points to the F7 continuation. |
| N-1 | NOTE | The re-pin maps any `ADAPTER_INTERNAL_ERROR` expectation, but against frozen `observed-red.json` it changes exactly the 8 named cells. | Accepted. |
| N-2 | NOTE | `full-t3.json` hashed the CRLF working-tree file (`8de56ec2…`); the LF git blob hashes to `ea370598…`. Before and after still match. | Disclosed here. |
| N-3 | NOTE | `gate-a.json` names mutant test IDs that RV-1 later renamed. The receipt is historical and correct for its head. | Accepted. |
| N-4 | NOTE | `gate-c.json` and `probes203.json` head labels (RV-6). The reviewer re-ran both on `4e7fe91d`, and the case arrays match exactly. | Accepted. |
| N-5 | NOTE | T0 reported `IMPACT_GATE_FAIL` before the freeze, only on the 11 identity nodes. Full T3 covers them after the freeze (15780 = 15769 + 11). | Accepted, honest. |
| N-6 | NOTE | Git cannot show who wrote `APPROVED_BY_USER`, because all commits share one author. The diff is exactly the 2 sanctioned values. | Authorship rests on the Owner's statement and `publication-approval-receipt.json`. |

What held, independently re-run on the candidate:
- **Publication:** the range scan PASSes. With the pre-approval registry the same range has exactly 10 violations on
  the two blobs, so nothing else is masked. The head-scan note (pre-existing on `main`) is confirmed.
- **Product scope:** the only product change since `1b1a9ed2` is `adapter3_simulation.py` (+3 lines). `CACHE_VERSION`
  is 130 and the default is `LLM_ONLY`.
- **Candidate identity:** the measured-system hash recomputes from git objects. `--verify` passes; 12 passed (the 11
  identity tests plus 1 extra parameter); the divergence chain is consistent; `test_C2b` passes.
- **Full T3:** the log hash, byte count, step counts and verdict match the raw log, which contains 0 tracebacks.
- **Wave 3:** 50/72 · 72/72 · 62/72 · 0 wrong-served, with all 144 rows equal to the receipt.
- **F1/F2/CIC-D1/F7 stay closed:**
  - targeted suites: 2691 passed, plus 1008 passed and 6 skipped;
  - 703 registered payloads × a3/pl/a4: 0 exceptions or internal errors;
  - the 203 locked probes: 0 served negatives;
  - Gate C: 96/96, 0 wrong-served.
- **Historical integrity:** no historical file was modified, deleted or renamed beyond the disclosed in-place changes.
  The docs IA and identity tests: 71 passed.
