# Gold Typed Facts — authoring log

Author: implementer (main agent). Source of truth: `build_gold_facts.py` → `gold_facts.json`.

1. First build: 60 cases, 316 facts; every quote asserted to be a substring of its `source_text`.
2. Deterministic probe of the gold arm (0 calls): 10/60 served (dev D01, D10; locked L01, L04, L06, L09, L14, L15, L24,
   and L41 with its proof flagged). All other outcomes were inspected for authoring errors:
   - Unlabelled base wording (`đáy là hình vuông cạnh 2`, `đáy hình chữ nhật`) → `OBJECT_NOT_IN_QUOTE` in D02, D03, D06,
     D07, D16, L05, L07, L26, L43. Quote variants probed (clause only; clause + solid sentence): all refused the same way.
     Not an authoring error: a Source Grounding false refusal of a common wording. Gold unchanged.
   - D08 (OA, OB, OC pairwise perpendicular): probed as line perpendiculars (gold), as right angles at O, and as pyramid
     O.ABC — all refused (`MISSING_DIMENSION` / `UNDERDETERMINED_POINT`). Capability gap. Gold unchanged.
   - Centroid (D09, L19) and line–line angle (D12, L29): `UNSUPPORTED_CAPABILITY`. Capability gaps.
   - Wording refusals of faithful encodings: L02 `dài bao nhiêu` (`PREDICATE_NOT_IN_QUOTE`), L03 `… thì đoạn AC' bằng
     mấy` (`CONDITIONAL_CLAUSE`), L13/L30 `tính cos²` and L27 `Tính BD'` (`NOT_ASKED_IN_SOURCE`), D11/L25 `dựng hình
     chiếu …, gọi điểm đó là H` (`SOURCE_OBJECT_MISMATCH`), L22 unnamed foot (`SOURCE_OBJECT_MISMATCH`), L23 `suy ra`
     (goal-clause policy), L20/L28 `QUESTION_LOCAL_GIVEN_UNVERIFIED` (cause not diagnosed).
   - L10 `SC²` refused (`SOURCE_OBJECT_MISMATCH`): safe for a semantic contrast the schema cannot express.
3. No fact was edited after the probe. No encoding was changed to obtain a served outcome.
4. Pre-lock amendments from the independent evaluation audit (`audit/evaluation-audit.md`), before any live request and
   before the lock commit; each makes the gold follow the product prompt more strictly, none was chosen by outcome:
   - L10 `Tính SC²` → `unsupported` (squared length has no schema quantity; `length SC` was an approximation).
   - L39 intersection line → three labels per plane (prompt rule 7: "ba điểm của mỗi mặt").
   - L23/L28 triangle-area questions → no `solid` (rule 7 prescribes `solid` only for section area).
   - D04/D05 right trapezoid → two `right_angle` facts (expressible, rule 1) instead of one `unsupported`.
   - L08 → two `unsupported` requests (construct, explain), one per corpus request.
   - AA' of boxes/prisms → alternatives `height` / `lateral_edge` (D11, L01–L03, L13, L14, L21, L24, L27).
   Gold-arm outcomes after the amendments: still 10/60 served. D04/D05 now refuse `UNSUPPORTED_BASE_SHAPE`; L39
   refuses `PLANE_NOT_IN_QUOTE` (the three-label reading of `(ABCD)` that rule 7 asks for is rejected by the source
   gate — a prompt/gate conflict recorded as a finding); L10 refuses `OUT_OF_SCOPE`.
