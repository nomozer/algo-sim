# Preregistration — hybrid-semantic-grounding-reliability

Written 2026-10-17 on branch `research/hybrid-semantic-grounding-reliability` from `main` = `origin/main` = `1f635ed5`,
before any product change and before the BASE measurement. Committed together with `corpus_build.py`, `corpus.json`,
`unseen/authored.json`, `unseen/build.py`, `unseen/cases.json`, `oracle.py`, `oracle.json` and `measure.py`.
`LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid product NO-GO, 0 model calls. Live extraction: `LIVE_EXTRACTION_NOT_MEASURED`.

## 1. Failures reproduced at `1f635ed5` (authored Typed Facts, real fact route)

| # | reported case | reproduced | layer |
|---|---|---|---|
| 1 | four-label plane read as three: "đến (SABC)" with facts (SAB) | SERVED, named and descriptor paths | source grammar: `registry._cung_mat` accepts any written group that shares 3 labels with the call's plane |
| 2 | second listed object dropped: "… đến (SAB) và AC" | SERVED, both paths | source-coverage gate: `_kiem_du_kien_cau_hoi` counts every asked object phrase of any function as read, answered or not |
| 3 | two requests, one answered: "… đến (SAB) và độ dài SC" | SERVED, both paths | same as 2 |
| 4 | follow-up dropped: ", sau đó tính thể tích …", "rồi suy ra thể tích …", and a whole next sentence "Sau đó tính thể tích …" | SERVED, both paths | same as 2 |
| 5 | reversed operands "đoạn nối A với trung điểm của SC" | REFUSED `SOURCE_OBJECT_MISMATCH` | contract phrase (`ask_length.planning_extra.phrase`) fixes the operand order |
| 6 | "Độ dài đoạn nối … bằng bao nhiêu?" | REFUSED `QUESTION_CONTEXT_UNSUPPORTED` | descriptor length binder demands the bare sentence form `(tính|tìm)? <phrase>` instead of the shared ask grammar |
| 7 | cube + `line_ref` | REFUSED `SOURCE_PREMISE_UNREAD` | closed line_ref premise grammar `_kiem_nguon_dong` has no cube form |
| 8 | live extraction of unnamed derived objects | not reproducible offline | `LIVE_EXTRACTION_NOT_MEASURED` |
| — | construction wording ("Kẻ AH vuông góc với SB tại H") | REFUSED `PREDICATE_NOT_IN_QUOTE` | construction grammar (`ISSUE-ARCH-CONSTRUCTION-WORDING-BREADTH`); measured, not targeted |

Cases 1–4 are false serves on the deterministic gate for an extraction that omits or shortens what the source says.
They are not Planner, Engine or Scene3D errors. 5–7 are false refusals in the source grammar.

## 2. Mechanisms (the whole slice; nothing else changes)

- **M1 — request coverage.** In a request sentence, an object phrase that the shared ask grammar reads as *asked* is
  read only when a validated answering call binds that exact span. That call can be an `ask_*` call with `_cum_hoi`,
  an effect-chain certificate span, or a validated auxiliary distance span. An asked phrase that no call answers ⇒
  refuse with the new code `REQUEST_NOT_ANSWERED`, before any geometry. One rule in `_kiem_du_kien_cau_hoi`, shared by
  routes A and B. No new grammar.
- **M2 — plane identity.** A written plane group with more than three labels names the call's plane only when it is
  the same label set, or a face the figure declares coplanar: the base or top of a declared solid, or a lateral face
  of a declared prism. Otherwise it does not name it ⇒ the existing `SOURCE_OBJECT_MISMATCH`. One change in
  `_cung_mat`, the single authority all binders already call.
- **M3 — descriptor length goal.** The contract phrase accepts both operand orders. The bare-sentence form check is
  replaced by the shared ask grammar (`_hoi_dung_cum`) plus M1, the same as every other ask. No new wording list.
- **M4 — cube premise.** One closed atomic form, "(Cho) hình/khối lập phương <solid> (có) cạnh <number>", added to
  the line_ref premise grammar for the calls a cube premise produces (prism, regular polygon, edge length).

Not changed: TypedFact schema, provider prompt/declarations, Planner search and limits, Engine, Kernel, Scene3D,
`/api/analyze`, `CACHE_VERSION` (route D is not on `/api/analyze`). If a fix turns out to need a schema or provider
change, work stops at that decision point.

## 3. Corpus, oracle, authorship

- `corpus.json` (58 cases, groups A equivalence, B contrast, C grounding, D multi-goal, E adversarial). It was written
  by the implementing agent, the same agent that writes the fix, so its status is **DEVELOPMENT_NOT_HELD_OUT**.
  Expected outcome, registered refusal codes and the number of requests the source makes are semantic labels, fixed
  here.
- `unseen/authored.json` (40 items) was written by an independent subagent. It had no repository access and saw only
  the figure and the intent families. It labelled meaning only (requests and correct behaviour), not refusal codes.
  sha256 `8eb393cf3d9590f7bd2dc546fcdcdc8a85109ffad340116d955182b890b4c672`.
  `unseen/build.py` adds the faithful extraction in the current schema. Items the schema cannot express are marked
  `schema_gap`: they get the nearest extraction and must be refused, and they are counted as capability gaps. The
  extraction mapping is the implementer's (a declared limitation). Status
  **UNSEEN_WORDING_INDEPENDENT_AUTHOR_NOT_HUMAN_HELD_OUT**. No product change is tuned on these items: they are
  measured on BASE and on the final candidate only.
- `oracle.py`: exact squared values from coordinates (Fractions), no `app` import.

## 4. Metrics (reported separately, never pooled)

Correct served · wrong served · correct refusal · wrong-code refusal · false refusal, by group and by mechanism;
source certification precision and recall (accept = served); multi-goal completeness (silent omissions among cases
whose source makes ≥ 2 requests); schema-gap items served wrongly. Intent, entity-grounding and goal-interpretation
accuracy **of an extractor** are NOT_MEASURED offline (the extraction is authored); the live protocol defines them.

## 5. Predictions and pass criteria

- P1: BASE has WRONG_SERVED > 0 on the M1/M2 cases; the final candidate has 0 WRONG_SERVED on the whole corpus.
- P2: unseen — the final candidate has no more WRONG_SERVED than BASE and no WRONG_SERVED on a `schema_gap` item.
- P3: FALSE_REFUSAL of the M3/M4 cases → 0. Any other case that changes class is listed with its reason. More false
  refusals outside M1's intended refusals fail the slice.
- P4: historical corpora (goal-entry 174-row bundle, result binding, two-line, benchmark 30, function-discovery corpus
  tests) keep their outcomes, except rows the frozen oracle of that run does not license. Each changed row is listed;
  frozen labels are never edited.
- Stop rules: M1 or M2 is not weakened to make a case pass. A historical SERVED row that M1 refuses is investigated
  and reported, not silently relabelled. Any need for a schema, prompt or provider change stops the slice at a user
  decision. No live call.
