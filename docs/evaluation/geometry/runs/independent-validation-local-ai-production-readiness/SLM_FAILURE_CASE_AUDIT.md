# AXO HYBRID /8 — FAILURE CASE AUDIT & CAPABILITY MATRIX REPORT (Phase P2 / Gate D2)

- **Machine Trace Receipt:** [`SLM_FAILURE_AUDIT_TRACES.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/SLM_FAILURE_AUDIT_TRACES.json)
- **Capability Matrix:** [`SLM_CAPABILITY_MATRIX.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/SLM_CAPABILITY_MATRIX.json)
- **Evaluated Script:** [`audit_slm_v8_failures_and_capabilities.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/audit_slm_v8_failures_and_capabilities.py)
- **Gate D2 Status:** `PASS` (`VERIFIED` · all 6 unresolved `/7` positives + `slm_h23` + blast-radius probes audited end-to-end with 13 mandatory fields and Gold interventions; 26 capability categories quantified with exact empirical denominators)

---

## 1. Key Correction to `/7` Narrative Diagnosis (`VERIFIED`)

In `/7`, prose reports hypothesized that `v7h_p8_01..05` failed because Source Gate rejected conversational sentence prefixes (`"Thưa thầy, nhờ giải bài: "`, `"Đề thi thử: "`, etc.). Live 13-field extraction + Gold-intervention traces disproved that hypothesis:

1. Sibling cases `v7h_p8_06..10` carry the **exact same 5 conversational prefixes** and **SERVED** (`5/5`) under `Config D`.
2. Gold `compact_clause` payloads on **`v7h_p8_01..05`** pass `slm-grounding-validator/3` → `Source Gate` (`registry.kiem_nguon`) → `Planner /26` → `Exact Kernel /24` and **`SERVED` (`5/5`, exact oracle match)** with the conversational prefixes present.
3. On all five cases (`v7h_p8_01..05`), `Qwen3-0.6B-AxoV7` emitted 5/6 premises (`perp_lp`, height `len`, two base edge `len`s, midpoint `mid`) and **omitted `{"c": 1, "p": "rect", "a": "<base>"}`** when the base shape was reordered into Sentence 1 without the keyword `"đáy"` (`"Biết UVWX là hình chữ nhật với ..."`).
4. Controlled probe `probe_reordered_rect_with_day_kw` — identical prefix `"Thưa thầy, nhờ giải bài: "`, identical reordered sentence order, changing ONLY `"Biết UVWX là hình chữ nhật"` → `"Biết đáy UVWX là hình chữ nhật"` — caused `AxoV7` to emit `rect(UVWX)` and **immediately `SERVED`**.
5. **`Source Gate` was NOT at fault:** `doc_rang_buoc` correctly detected that `"Biết UVWX là hình chữ nhật với ..."` had no lowered fact consuming the rectangle assertion and faithfully refused with `SOURCE_PREMISE_UNREAD`. A minor `slm-verified-normalizer/2` quirk also rewrote `"Thưa thầy,"` → `"Cho"` on `v7h_p8_01`, though `Gold` served despite that quirk.

---

## 2. Six Unresolved `/7` Positive Cases — 13-Field Evidence Summary (`Config D`)

| Case ID | 1. Original (Excerpt) | 2. Norm Change (`v2`) | 4. Parser (`norm`) | 5. Raw SLM (`AxoV7`) Error | 6. Grounding | 7–10. Source Gate / Planner / Kernel | 11. Refusal Reason | 12. Gold Result | 13. Root Cause & Owner Boundary |
|---|---|---|---|---|---|---|---|---|---|
| `v7h_p8_01` | `"Thưa thầy, nhờ giải bài: ... Biết UVWX là hình chữ nhật..."` | `"Thưa thầy,"` → `"Cho"`, `"với đáy"` | `LOCAL_PARSE_PARTIAL` | **Omitted `rect(UVWX)`** in clause 1 | `GROUNDED_AND_LOWERED` | Blocked in Source Gate; Planner/Kernel not served | `SOURCE_PREMISE_UNREAD` | **`SERVED`** (`3a√22/22`, match `True`) | **`MODEL_SEMANTIC_ERROR`** (`AxoV7` omission when `"đáy"` absent) + minor normalizer `"Thưa thầy,"→"Cho"` |
| `v7h_p8_02` | `"Đề thi thử: Cho khối chóp C.ABDE ... Biết ABDE là hình chữ nhật..."` | `"mặt đáy"` → `"với"` | `LOCAL_PARSE_PARTIAL` | **Omitted `rect(ABDE)`** | `GROUNDED_AND_LOWERED` | Blocked in Source Gate | `SOURCE_PREMISE_UNREAD` | **`SERVED`** (`a√3/2`, match `True`) | **`MODEL_SEMANTIC_ERROR`** (`AxoV7` omission) |
| `v7h_p8_03` | `"Câu hỏi hình không gian: ... Biết GHIK là hình chữ nhật..."` | `"mặt đáy"` → `"với"` | `LOCAL_PARSE_PARTIAL` | **Omitted `rect(GHIK)`** | `GROUNDED_AND_LOWERED` | Blocked in Source Gate | `SOURCE_PREMISE_UNREAD` | **`SERVED`** (`a√21/7`, match `True`) | **`MODEL_SEMANTIC_ERROR`** (`AxoV7` omission) |
| `v7h_p8_04` | `"Hướng dẫn giải: ... Biết ABCD là hình chữ nhật..."` | `"mặt đáy"` → `"với"` | `LOCAL_PARSE_PARTIAL` | **Omitted `rect(ABCD)`** | `GROUNDED_AND_LOWERED` | Blocked in Source Gate | `SOURCE_PREMISE_UNREAD` | **`SERVED`** (`3a√10/10`, match `True`) | **`MODEL_SEMANTIC_ERROR`** (`AxoV7` omission) |
| `v7h_p8_05` | `"Bài tập tự luận: Cho khối chóp Z.EFGH ... Biết EFGH là hình chữ nhật..."` | Stripped prefix; `"mặt đáy"` → `"với"` | `LOCAL_PARSE_PARTIAL` | **Omitted `rect(EFGH)`** | `GROUNDED_AND_LOWERED` | Blocked in Source Gate | `SOURCE_PREMISE_UNREAD` | **`SERVED`** (`3a√13/13`, match `True`) | **`MODEL_SEMANTIC_ERROR`** (`AxoV7` omission) |
| `v7h_p5_09` | `"Cho hình chóp G.RST ... Gọi I là trung điểm RS, hình chiếu ... của G lên (RST) trùng I..."` | Unchanged | `LOCAL_PARSE_PARTIAL` | **Swapped args:** `proj(pt="G", a="R", b="RST")` + spurious `perp_lp("RS","RST")` | `GROUNDED_AND_LOWERED` | Blocked in Source Gate (`_C_CHIEU`) | `SOURCE_OBJECT_MISMATCH` | **`SERVED`** (`8a³√3`, match `True`) | **`MODEL_SEMANTIC_ERROR`** (argument swap caught faithfully by Source Gate) |
| `v7h_p8_06` *(passing comparator)* | `"Thưa thầy, nhờ giải bài: Cho lăng trụ đứng ABC.A'B'C' ..."` | Stripped `"đồng thời"` | `LOCAL_PARSE_PARTIAL` | All 4 premises + goal extracted cleanly | `GROUNDED_AND_LOWERED` | Source Gate / Planner / Kernel **`SERVED`** | `None` | **`SERVED`** (`6a³√3`, match `True`) | `PASSING_COMPARATOR` |
| `v7h_p5_08` *(passing comparator)* | `"Cho hình chóp L.PQR ... Gọi I là trung điểm PQ, hình chiếu ... L lên (PQR) trùng I..."` | Unchanged | `LOCAL_PARSE_PARTIAL` | Correct `proj(pt="I", a="L", b="PQR")` | `GROUNDED_AND_LOWERED` | Source Gate / Planner / Kernel **`SERVED`** | `None` | **`SERVED`** | `PASSING_COMPARATOR` |

*(Full JSON dumps for all 13 fields including raw strings, spans, provenance steps, entities, predicates, and lowered `TypedFactNext /2` payloads live in [`SLM_FAILURE_AUDIT_TRACES.json`](SLM_FAILURE_AUDIT_TRACES.json).)*

---

## 3. Historical Regression Audit: `slm_h23_ocr_extra_spaces` (`HOLDOUT_40`, `25/28 -> 24/28`)

- **Input:** `"Cho hình chóp S.ABC có đáy ABC đều cạnh 2a , SA vuông góc với ( ABC ) , SA = 3a . Tính thể tích khối chóp S.ABC."`
- **Normalized (`v2`):** Spaces cleaned and `"đáy ABC đều cạnh 2a"` expanded via `VN04_DAY_DEU_CANH` into `"Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SA vuông góc với (ABC), SA = 3a. Tính thể tích khối chóp S.ABC."`
- **Config C (`qwen3-0.6b-q4_k_m`):** Extracted `reg_poly(ABC,2a)`, `len(SA,3a)`, `perp_lp(SA,ABC)` (repeated, deduplicated downstream) + `g=[vol(S.ABC)]` → `GROUNDED_AND_LOWERED` → **`SERVED` (`a³√3`, exact match)**.
- **Config D (`qwen3-0.6b-axo-v7-q4_k_m`):** Extracted `s=[0,"pyr","S.ABC",0]` + the 3 premises, but emitted **`g=[]`, `u=[{"c": 0, "k": "missing"}]`** → `SLM_REPORTED_UNRESOLVED` → **`REFUSED` (`AMBIGUOUS_FACT`)**.
- **Is it a fine-tuned model regression?** **YES (`VERIFIED`)** — fine-tuning induced an over-conservative false `unresolved` refusal (`0` wrong-served risk, safe refusal).
- **Blast-Radius Probes (5 controlled `S.ABC` equilateral-base variants under `Config D`):**
  1. `probe_clean_the_tich` (no OCR spaces): `REFUSED` (`AMBIGUOUS_FACT`, `SLM_REPORTED_UNRESOLVED`).
  2. `probe_ocr_the_tich` (`"Tính thể tích S.ABC."`): emitted `u=[{"c":0,"k":"missing"}]` cleanly -> `REFUSED` (`AMBIGUOUS_FACT`). *(Note: earlier intermediate multi-call diagnostic run observed KV-slot order sensitivity when two sequential calls ran back-to-back with `cache_prompt=True`; single-pass canonical `run_local_slm_extraction` confirmed `SLM_REPORTED_UNRESOLVED` consistently.)*
  3. `probe_ocr_V_cua` (`"Tính V của S.ABC."` with OCR spaces): `REFUSED` (`AMBIGUOUS_FACT`).
  4. `probe_ocr_la_tam_giac_deu` (already un-abbreviated `"là tam giác đều"` with OCR spaces): `REFUSED` (`AMBIGUOUS_FACT`).
  5. `probe_clean_V_cua` (`"Tính V của S.ABC."` clean spacing): extracted `g=[vol(S.ABC)]`, passed validator (`GROUNDED_AND_LOWERED`), then safely refused at Source Gate (`NOT_ASKED_IN_SOURCE` because `"V"` is not spelled `"thể tích"`).
- **Conclusion:** Fine-tuned `AxoV7` shows localized over-conservative `missing` emission on short equilateral `S.ABC` + `SA ⊥ (ABC)` prompts (no product rule hack added in `/8`).

---

## 4. Capability Matrix Summary (`SLM_CAPABILITY_MATRIX.json`)

Aggregated over **`140`** verified positives across `V7H_112` (`80`, `axo-math-evaluator/2`), `NH48` (`32`), and `HOLDOUT_40` (`28`), plus negative safety suites (`32/32` safe in `V7H_112` + `0` wrong-served across baseline suites):

| Domain / Construct Group | Status | `Config D` Pass Rate | Scope Notes |
|---|---|---|---|
| Triangular pyramid (`S.ABC`) | `VALIDATED_LOCAL_PRIMARY` | `35/39` (`89.74%`) | `S.ABC` missing cases from `p5_09` & `H40` |
| Quadrilateral pyramid (`S.ABCD`) | `VALIDATED_LOCAL_PRIMARY` | `62/68` (`91.18%`) | 5 misses from reordered `p8_01..05` |
| Regular pyramid (`chóp đều`) | `VALIDATED_LOCAL_PRIMARY` | `7/7` (`100.0%`) | Verified |
| Right / regular prism (`lăng trụ đứng/đều`) | `VALIDATED_LOCAL_PRIMARY` | `20/20` (`100.0%`) | Verified |
| Rectangular box (`hình hộp chữ nhật`) | `VALIDATED_LOCAL_PRIMARY` | `5/5` (`100.0%`) | Verified |
| Cube (`hình lập phương`) | `EXPERIMENTAL` | `2/2` (`100.0%`) | `n < 5` in SLM positive holdouts (`< 5` rule) |
| Regular tetrahedron (`tứ diện đều`) | `EXPERIMENTAL` | `3/3` (`100.0%`) | `n < 5` in SLM holdouts (`< 5` rule) |
| Right / right-isosceles triangle base | `VALIDATED_LOCAL_PRIMARY` | `33/34` (`97.06%`) | Verified |
| Equilateral / isosceles triangle base | `VALIDATED_LOCAL_PRIMARY` | `37/39` (`94.87%`) | Verified |
| Square / rectangle base | `VALIDATED_LOCAL_PRIMARY` | `47/53` (`88.68%`) | Requires `"đáy"` or unambiguous wording (`p8_01..05`) |
| Rhombus / parallelogram / trapezoid base | `VALIDATED_LOCAL_PRIMARY` | `12/12` (`100.0%`) | Within contracted Registry metric slots |
| Perpendicular line–plane & face–base | `VALIDATED_LOCAL_PRIMARY` | `93/102` (`91.18%`) | Verified |
| Parallel relation | `EXPERIMENTAL` | `3/3` (`100.0%`) | Sparse in SLM holdouts (`n=3`) |
| Midpoint (`trung điểm`, excl. `p8` rect misses) | `VALIDATED_LOCAL_PRIMARY` | `12/13` (`92.31%`) | Single miss `p5_09` (projection swap) |
| Centroid (`trọng tâm`) | `VALIDATED_LOCAL_PRIMARY` | `5/5` (`100.0%`) | Verified |
| Orthogonal projection (`hình chiếu`) | `EXPERIMENTAL` | `7/9` (`77.78%`) | `p5_09` argument-swap risk + H40 phrasing sensitivity |
| Segment ratio division (`SM = k·SC`) | `VALIDATED_LOCAL_PRIMARY` | `5/5` (`100.0%`) | Verified |
| Point-to-plane distance goal | `VALIDATED_LOCAL_PRIMARY` | `32/37` (`86.49%`) | 5 misses from reordered `p8_01..05` |
| Skew-line distance goal | `VALIDATED_LOCAL_PRIMARY` | `7/7` (`100.0%`) | Verified |
| Line-plane angle goal (incl. `cos²=`) | `VALIDATED_LOCAL_PRIMARY` | `5/5` (`100.0%`) | Verified via `axo-math-evaluator/2` |
| Plane-plane / dihedral angle (as premise) | `VALIDATED_LOCAL_PRIMARY` | `19/19` (`100.0%`) | Verified as height-determining premise |
| Plane-plane / dihedral angle (as **goal**) | `NOT_MEASURED` | `0/0` | Not directly asked as goal in `V7H/NH48/H40` |
| Volume & area/length goals | `VALIDATED_LOCAL_PRIMARY` | `78/83` (`93.98%`) | Verified |
| Complex derived cross-sections / multi-step intersections | `UNSUPPORTED` | `0/0` | Out of `slm-compact-clause/1` scope |
| Spheres, cones, cylinders, multi-solid compositions | `UNSUPPORTED` | `0/0` | Safely refused as negative OOS traps in `V7H_112` |
| Non-Registry auxiliary constructions / general extrema | `UNSUPPORTED` | `0/0` | Out of `Registry /33` & `Planner /26` scope |
| Conversational intro + reordered `"Biết <base> là hcn"` without `"đáy"` | `EXPERIMENTAL` | `5/10` (`50.0%`) | Fails cleanly (`0` wrong served) |
