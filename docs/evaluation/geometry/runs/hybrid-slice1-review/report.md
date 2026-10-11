# Hybrid B slice 1: independent review and main integration readiness

Status: `HYBRID_SLICE1_INTEGRATION_AWAITING_APPROVAL`.

- Reviewed range: `4a3a4938..0e28d2f3`. Slice 1 product commit `f874b4dd`, run [`hybrid-goal-decomposition`](../hybrid-goal-decomposition/report.md).
- Branch `research/hybrid-compiler-capability-audit`, LOCAL. Not merged, not pushed, no PR.
- LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = `LLM_ONLY`, `CACHE_VERSION` 125.

**This report is a correction layer.** The slice 1 report stated that "negated, conditional and proof-only goals are refused" and that an auxiliary label collision is "excluded by construction". Both statements were incomplete (Important 1 and 2 below). The slice 1 report itself is not edited.

## 1. How the review was done

**Independent reviewer.**
- A reviewer agent with no access to the implementation session read the diff. It worked read-only and wrote its probe scripts outside the repository.
- It traced the path Typed Facts → planner → auxiliary construction → source gate → engine → kernel → IR → Scene3D, and tried to break the requirements adversarially.
- It recomputed the benchmark on its own.

**Implementer.**
- I re-measured the benchmark from the current code: byte-identical to [`after/metrics.json`](../hybrid-goal-decomposition/after/metrics.json), and only the B26 rows differ from the pre-change baseline.
- I verified the candidate and listed the files the branch changes against `main`.
- I reproduced every finding as a RED test before fixing it.

## 2. Findings

### Critical
None. The reviewer found no forgery path, and every served answer it checked equals its own oracle:
- equilateral-triangle and regular-pyramid figures in non-orthonormal charts;
- symbolic `a` (`a√6/2`);
- distance 0 for a point on the line.

### Important

**1. The gate checked clause roles only by a deny-list. It never checked that the matched phrase is actually asked.** Fixed.
- **What was served** (√11) when the AI mis-typed the clause as a question:
  - "Hãy chỉ ra rằng khoảng cách từ S đến BD bằng √11."
  - "Gọi d là khoảng cách từ S đến BD. Chứng minh rằng d = √11."
  - "Chứng minh rằng, biết khoảng cách … bằng √11, thì SA = 3."
  - "Giả sử khoảng cách … bằng 4. Tính SC."
  - "Khi khoảng cách … bằng 4 thì SC bằng bao nhiêu?"
  - "Biết khoảng cách … bằng 4. Tính SC."
  - "… không bằng 3." / "chẳng bằng 3." / "khác 3."
- **Fix** — an allow-list in `_kiem_phu`:
  - the sentence holding "khoảng cách từ P đến XY" must contain an interrogative cue (tính, tìm, xác định, bao nhiêu, ?);
  - no value may be asserted right after the line ("bằng 4", "không bằng 3", "khác 3"; "bằng bao nhiêu" still counts as a question);
  - otherwise the gate refuses with `NOT_ASKED_IN_SOURCE`.
- **Tests:** 9 parametrised negatives, 5 question wordings that must still be served, and 2 mutants.
- **Not fixed here:** the same hole exists, pre-existing, in the gate for every other `ask_*` function, which skips role checks entirely. That is out of slice 1 scope and recorded as `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK`.

**2. The auxiliary label could collide with text labels the scanner reads differently.** Fixed.
- **What happened:**
  - "H₁" and "H_1" are read as `H`, so `H1` looked free.
  - "ΔSHD" and "điểmH" hide `H` from the scanner.
- **Fix:** `nhan_phu_da_dung` treats a name as taken whenever the letter H stands alone or is glued to other letters, with any index (`1`, `_1`, `₁`). It is used both when the planner chooses a label and when the gate checks one.
- **Tests:** 5 parametrised cases ("Hình …" at the start of a sentence still leaves `H` free), a gate tamper test, and 2 mutants.

### Minor

| # | Finding | Disposition |
|---|---|---|
| 1 | The trace attributed auxiliary calls to the wrong fact when the id contains `_` (`cau_2` → `cau`) | fixed for the auxiliary entries; the same pre-existing pattern elsewhere in `phat` is unchanged |
| 2 | Construct id `<id>_aux` could clash with a fact id, giving a false `DUPLICATE_CALL_ID` | fixed: the id is chosen outside fact and call ids |
| 3 | A refusal's `details.points`/reason can name the auxiliary (`['H', 'S']`) | recorded in the limits issue; route D is not shown to learners yet |
| 4 | The gate accepted two declarations with the same label (only a tampered plan can produce this) | fixed: `AUXILIARY_RULE_MISMATCH`, with a mutant |
| 5 | `lap_ke_hoach(raw, problem_text="")` default: a caller without the text chooses labels blind | recorded. The gate still fails closed with a collision. The only product caller passes the text |
| 6 | Redundant feet: two questions on the same point and line, or a stated projection plus the question, give H and H1 at one spot | recorded in the limits issue |

### Recorded, outside slice 1

- `engine._mot_buoc` crashes with `StopIteration` when the text uses every one of O, I, O1, O2 and the base centre needs a name. This predates slice 1. Recorded as `ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION`.

## 3. Auxiliary identity and forgery

**Forgery: not possible through the inputs we checked.**
- **Route A:** `function_calling.py` calls `run_function_route(text, plan)` with no declaration. The planner's own calls without the declaration are still refused `UNKNOWN_LABEL`.
- **Facts JSON:** `TypedFact` is `extra="forbid"`, and an extra `auxiliary` key gives `SCHEMA_INVALID`.
- **Tampered declarations:** a wrong rule, label, point, quote or call, or a duplicate label, is refused by the gate, which re-derives every check from the source text and does not trust the planner.

**The auxiliary never acts as a given.**
- The engine builds it forward only, after its operands.
- Its relation is verified independently, and it is marked `DERIVED` / `binding: AUXILIARY`.
- In the scene it is a construction object, never "given".
- No premise call can mention it.
- Goal checks stay `can_present_as_proven: False`.
- Under-determined figures are refused, never sampled.

**Could the internal identity be separated from the display label?**
- **Feasible below the call level** without touching the provider surface: give auxiliaries a reserved IR / scene id (e.g. `aux_1`) and keep `label = "H"` for display.
- **Not at the call level:** the Registry `Label` pattern belongs to A's function declarations (`41e090cd…`), and planner calls pass the same validation. A truly reserved call namespace would need a second, planner-only argument model.
- **Recommendation:** keep the current design. "H" is the textbook name for a foot, collisions are now excluded against the conservative scanner, and the separation adds a second identity path for no measured benefit.

## 4. Benchmark and regression

| Check | Result |
|---|---|
| Benchmark, both evaluations | 19 correct served / 9 correct refusals / **0 wrong served** / 2 false refusals (B27, B28) |
| Changes against the pre-change baseline | only B26 (both evaluations); 29 cases unchanged |
| After the review fix | rows byte-identical to the slice 1 measurement (re-measured in a scratch directory, nothing overwritten) |
| RED for the review findings, at `0e28d2f3` | 17 failed, 46 passed ([log](red-at-0e28d2f3.txt)) |
| `test_hybrid_goal_decomposition.py` | 68 passed, including 14 source mutants killed (6 new) |
| Hybrid / function-route cluster | 657 passed, 4 xfailed |
| Provider surfaces A / B, function declarations | unchanged (pinned) |

Full backend and T3: [`handoff.md`](handoff.md) §2.

## 5. Candidate identity

| | tree hash | product commit | refreeze commit |
|---|---|---|---|
| slice 1 | `cac3022f…` | `f874b4dd` | `d8d636b5` |
| **after review fix** | **`dda3a884…`** | **`62f0b18e`** | **`9da4e853`** |
| locked A/B (untouched) | `12da4768…` | — | — |

The divergence is declared as a correction layer: [`candidate_divergence.json`](candidate_divergence.json) corrects the slice 1 declaration.

## 6. Remaining limits

- **Wording.** Only "khoảng cách từ P đến (đường thẳng) XY" in a sentence that asks it. Other wordings are refused (fail-closed, not measured).
- **Coinciding foot.** A point on the line, or a redundant foot, is drawn on an existing point under a second label. No human visual review.
- **Visible auxiliary name.** It can appear in refusal details.
- **No real-model evidence.** Whether Gemini extracts (point, line) distance questions correctly was not measured; the prompt is unchanged.
- **Out of scope:** the other `ask_*` functions lack the question check; B27 needs a schema change and is not approved; B28 is a grounding issue.
