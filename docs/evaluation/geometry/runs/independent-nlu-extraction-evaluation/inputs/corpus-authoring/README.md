# NLU_EVAL_CORPUS/1 — Vietnamese 3D-geometry problem corpus (agent 1)

**Independence level:** written by an AI agent (Claude subagent) that never looked at the system
under test: no repository code, prompts, docs, earlier corpora or results were opened. The only
inputs were the task brief and the agent's own knowledge of Vietnamese Toán 11–12 conventions.
**Nobody has checked it by hand.** Treat the gold labels as one careful annotator's judgement.
A native-speaker teacher should review it before it supports any claim about held-out quality.

## Files
- `build_corpus.py` holds the hand-written case table and writes `corpus.json`. It assigns ids
  in order. Its expected values were worked out by hand.
- `corpus.json` has 60 cases: 16 `dev` (D01–D16) and 44 `locked` (L01–L44).
- `agent1_oracle.py` uses only `fractions`. It places each figure in its own coordinates,
  recomputes every numeric value, and fails if `corpus.json` disagrees. It also checks the
  `exact` strings by parsing `k√m/n`, and runs 12 structural checks behind refusal and
  construction labels.
- `check_corpus.py` checks ids, split sizes, group coverage, that every quote is an exact
  substring, that `structure_id`s don't overlap across splits, `n_source_requests`, enum values,
  and that no dev/locked wording pair is near-identical (difflib ratio < 0.85).
- `*.out.txt`: output of the last passing runs of both checks. Run with `python -I build_corpus.py && python -I check_corpus.py && python -I agent1_oracle.py`.

## Figure placements (oracle)
- S.ABCD with a rectangle base AB×AD and SA⊥ base: A(0,0,0) B(ab,0,0) C(ab,ad,0) D(0,ad,0) S(0,0,sa).
  Dimensions used: 2×2,2 · 3×4,5 · 4×4,3 · 1×1,1 (edge a) · 2×3,4.
- Right trapezoid (D04/D05): A(0,0,0) B(2,0,0) C(4,2,0) D(0,2,0) S(0,0,2). Angle ABC is obtuse.
- Parallelogram (L11/L12): A(0,0,0) B(2,0,0) C(1,1,0) D(−1,1,0) S(0,0,1). This gives AD=√2 and
  angle BAD=135° with rational coordinates.
- Box/cube: A at the origin, AB on x, AD on y, AA' on z (edge a ⇒ a=1). OABC: O at the origin, A, B, C on the axes.
- Right prism ABC.A'B'C' with the right angle at A: A at the origin, B on x, C on y.
- S.ABC with the right angle at B: A(0,0,0) B(ab,0,0) C(ab,bc,0). With the right angle at A, C is on the y axis.

## Value conventions
- Lengths: `value_squared` exact square, `exact` closed form; `unit: "a"` = multiple of a (volume `a^3`).
- Angles: `cos_squared`, plus `degrees` only when the angle is standard (0/30/45/60/90).
- `cos_squared_angle` and `length_squared` requests: `value` is the requested number itself.
- Construction answers are given as text in `expected_objects` and are not numeric.
- `quote_in: "context.prior_turn"` marks premise quotes in group E. Those premises live in the prior turn.
- Extra fields: `depends_on`, `accept_equivalent_quantities`, `of` (underlying angle / optimisation target).

## Judgment calls (least sure first)
1. L16 `(ABC'D)`: I labelled it `refuse_nonexistent_object`. Asking whether (ABC'D') was meant
   is arguably just as good. The same goes for L39 (parallel planes, no intersection line).
2. L41 (prove + compute): `answer_supported_part_and_flag_rest`. This treats any "chứng minh"
   request as outside the scope of computation. Another rubric might accept a visual justification.
3. L43 (one label defined twice): I chose `refuse_ambiguous`. `clarification_required` is close.
4. L38 (a conditional clause that supplies the edge length): `answer_all`. I read "Nếu … thì" as
   a premise, not as a hypothetical to reject.
5. D08, L22 and L19 ask for the length of a segment to a derived point. They are labelled `length`,
   with `distance_point_plane` accepted where the two mean the same thing. In L19 the two only
   give the same number by coincidence.
6. L08 is the same geometry as S22, but the intents are construct + explain. I gave it its own
   structure_id (S60) and kept it in group A as the control for "a different intent is not equivalent".
7. L32 and L36: hiding labels, recolouring and hiding a face each count as one `interaction` request.
8. L37 and L40 are `refuse_missing_info`. A system might fairly ask for the missing data instead.
9. Group E premises come from the prior turn. Scorers that only read `source_text` will see no premises.

## Limitations
- The L40 oracle check is an arithmetic witness (two heights), not a constructed coordinate
  placement. The equilateral base has an irrational vertex.
- No fault-injection run of the oracle or checker was kept. Phrasing variety comes from one author, so it is narrower than real student writing.
