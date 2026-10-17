# Authoring brief given to the corpus author (verbatim)

Recipient: a fresh Claude subagent (general-purpose), 2026-10-17, launched by the main agent; this text was its only
input. Its scratch directory was outside the repository; the files were copied here unmodified afterwards
(`corpus.json` SHA-256 prefix `44b4e502d4f55be2` before and after the copy). Whether the agent obeyed the isolation rules
is attested by its own report only; no tool-level sandbox enforced them.

---

You are Agent 1 — Corpus and Semantic Annotation author for an independent evaluation of how well an LLM understands Vietnamese 3D-geometry problems (Toán 11–12, hình học không gian). You must work BLIND to the system under test.

ISOLATION RULES (mandatory):
- Do NOT open, read, grep or list anything under D:\Documents\projects\algo-sim (no code, no prompts, no docs, no previous corpora, no results). Do not run git. You have no need for the repository.
- Write ONLY inside this directory: C:\Users\Bunny\AppData\Local\Temp\claude\d--Documents-projects-algo-sim\8bead7fe-5200-4fe5-8ac8-70a1c4036b51\scratchpad\agent1-corpus\ (create it). With the Bash tool use the POSIX form /c/Users/Bunny/AppData/Local/Temp/claude/d--Documents-projects-algo-sim/8bead7fe-5200-4fe5-8ac8-70a1c4036b51/scratchpad/agent1-corpus/
- No web access is needed; do not use it. Python is available as /d/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe — you MAY run it with `-I` on your own scripts inside your directory (stdlib only, e.g. fractions), but do not import anything from the repository.
- Do not copy these illustration sentences (they are already public in the task brief): "Tính khoảng cách từ A đến đường thẳng SB.", "A cách đường thẳng SB bao xa?", "Cho biết khoảng cách giữa điểm A và đường SB.", "Mô phỏng cách tìm khoảng cách từ A tới SB.", "Vẽ tiếp đoạn vừa tìm được.", "Tô nổi bật chân đường vuông góc.", "Xoay hình để thấy đường khuất.", "Điểm nằm giữa S và C, cách đều hai đầu mút." Write your own wordings.

TASK: author a Vietnamese problem corpus with gold semantic labels and independently computed exact answers.

Write natural Vietnamese as real Vietnamese high-school students and teachers write (textbook style, homework style, casual student style, some without diacritics-quality issues is NOT wanted — keep proper diacritics; vary punctuation, word order, "hãy/tính/tìm/cho biết/bằng bao nhiêu/là bao nhiêu/bao xa/…", use of parentheses for planes "(SAB)", "mp(SAB)", "mặt phẳng SAB", "đường SB", "đoạn SB", "cạnh SB"). Every case must be self-contained: figure premises + question(s), except group E cases, which carry an explicit prior context (see below).

Phenomenon groups (spread cases across all):
A. Semantic equivalence — several genuinely different wordings of the SAME geometric request on the same figure (give them the same `structure_id`). Keep differences of intent (compute a value vs. show/construct vs. explain) as different intents even when the geometry is the same.
B. Semantic contrast — near-identical wordings with DIFFERENT meaning: line SB vs segment SB (e.g. distance from a point to a line vs to a segment where the foot falls outside the segment), distance vs length, length vs squared length, construct projection vs compute distance, angle vs cos² of the angle, plane (SAB) vs four-label "(SABC)" (which may be a non-plane / invalid), line through two points vs intersection line of two planes.
C. Derived/unnamed objects — midpoints, centroids, projections, intersection points/lines described in words without a name, or named later in the text.
D. Multi-goal — two or three requests in one sentence or in separate sentences, chained ("rồi", "sau đó", "từ đó suy ra") and independent; include one where the second request depends on an object defined by the first.
E. Contextual references — a follow-up request referring to an earlier answer/scene ("đoạn vừa dựng", "điểm đó", "hình trên"). For each, include the `context` field: either a prior turn text that makes it resolvable, or null when the reference is unresolvable (then the gold disposition is clarification_required). Also include requests that are pure display/interaction (highlight, rotate, hide) — label them intent "interaction".
F. Adversarial / insufficient — contradictory data, non-existent object, ambiguous point name, negated premise ("SA không vuông góc với đáy"), conditional clause ("nếu … thì …"), asking the intersection line of two parallel planes, a statement that tempts the reader to add a fact not in the text (e.g. "hình chóp đều" not stated but implied by nothing), a request type outside ordinary computation (e.g. "chứng minh", "tìm giá trị lớn nhất khi M di động"), missing a needed dimension.

Use mostly these figure families (you may vary dimensions; use small integers so exact answers are rational or square roots of rationals): pyramid S.ABCD with square/rectangle base and SA ⊥ base; pyramid S.ABC with right triangle base; cube ABCD.A'B'C'D' (also with side "a" symbolic); rectangular box; tetrahedron OABC with OA, OB, OC pairwise perpendicular; right triangular prism. You may include a few other figures.

SPLITS: produce exactly two splits.
- `dev`: 16 cases (will be used for a small pilot/harness check), covering every group A–F at least twice.
- `locked`: 44 cases, at least 22 distinct `structure_id`s, covering every group at least 5 times, and including at least 10 multi-request cases. No dev case may share a structure_id or near-identical wording with a locked case.

ANNOTATION CONTRACT — write file corpus.json = {"schema": "NLU_EVAL_CORPUS/1", "author": "independent-agent-1 (Claude subagent, blind to system under test)", "created": "2026-10-17", "cases": [...]}. Each case:
{
 "id": "D01".."D16" for dev, "L01".."L44" for locked,
 "split": "dev"|"locked",
 "group": "A"|"B"|"C"|"D"|"E"|"F",
 "structure_id": "S01"…  (same id ⇔ same underlying geometric question on the same figure),
 "source_text": full problem text exactly as the student would type it,
 "context": null or {"prior_turn": "...", "prior_result": "..."} (group E only),
 "entities": [{"kind": "point|segment|line|plane|solid|derived_point|derived_line", "ref": "A" or "SB" or "(SAB)" or a description, "named_in_text": true|false}],
 "premises": [{"relation": short English relation name e.g. "square_base", "perpendicular_line_plane", "length", "midpoint_def", "right_angle", "parallel", "negated:perpendicular_line_plane", "conditional:...", "operands": [...], "value": "3" or "a" or null, "quote": EXACT substring of source_text}],
 "requests": [{"rid": "r1", "intent": "compute_value|construct|prove|interaction|explain|define", "quantity": "distance_point_line|distance_point_segment|distance_point_plane|distance_line_line|length|length_squared|angle_line_plane|angle_line_line|angle_plane_plane|cos_squared_angle|area|volume|intersection_line|section|projection|other", "operands": [{"kind": ..., "ref": ...}], "quote": EXACT substring of source_text that asks it}],
 "n_source_requests": integer = number of distinct requests a complete answer must cover,
 "missing_or_ambiguous": [free text],
 "gold_disposition": "answer_all" | "refuse_contradictory" | "refuse_missing_info" | "refuse_nonexistent_object" | "refuse_ambiguous" | "clarification_required" | "out_of_scope_request" | "answer_supported_part_and_flag_rest",
 "hallucination_traps": [facts a careless reader might add that are NOT in the text],
 "expected_values": {"r1": {"value_squared": "13/5" (exact rational of the value squared for lengths/distances; for angles give "cos_squared": "p/q" AND "degrees": "45" if it is a standard angle; for area/volume give "value": exact expression and "value_squared"), "exact": "√65/5", "computed_by": "agent1_oracle.py"}} — only for requests with a determinate numeric answer,
 "notes": short rationale for tricky labels
}
Quotes MUST be exact substrings (verify programmatically). n_source_requests must equal len(requests) unless a request is explicitly unanswerable (then explain in notes).

INDEPENDENT ORACLE: write agent1_oracle.py (stdlib `fractions` only) that, for every case with expected_values, places the figure in coordinates YOU choose, computes every value exactly (squared distances via cross/dot products; angles via cos²), and asserts the numbers in corpus.json. Run it; it must pass. Also write check_corpus.py that validates: unique ids, split sizes (16/44), group coverage, quotes are substrings, structure_id disjointness between splits, n_source_requests consistency. Run it; it must pass.

Finally write README.md (≤ 60 lines) describing your process, the figure placements, any labeling judgment calls, and an honest statement of independence level: authored by an AI agent blind to the system under test, NOT human-validated.

Your final message must contain: the absolute paths of the files written, the counts (cases per split, per group, distinct structure_ids per split, multi-request count, number of cases with numeric expected values and number of numeric values), the output of the two check scripts, and a list of labeling judgment calls you were least sure about.
