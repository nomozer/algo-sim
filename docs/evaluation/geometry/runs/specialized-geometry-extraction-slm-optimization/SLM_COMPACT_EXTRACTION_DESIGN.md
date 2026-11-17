# AXO HYBRID /6 — Specialized Compact Extraction & Grounding Architecture (`slm-compact-clause/1`)

> **Worktree:** `.superpowers/worktrees/local-first-geometry-understanding` (`feat/local-first-geometry-understanding`)  
> **Runtime / Extractor / Normalizer Contracts:** `local-slm-runtime/2` · `local-slm-extractor/2` · `slm-compact-clause/1` · `slm-grounding-validator/2` · `slm-grounding-envelope/2` · `slm-verified-normalizer/1` · Cache Namespace `HYBRID_V6_LOCAL_SLM`  
> **Locked Surfaces Unchanged:** `CACHE_VERSION = 145`, `ROUTE_D_CACHE_POLICY = 145:route-d`, `Local Parser /2`, `Planner /26`, `Registry /33` (`kiem_nguon`), `Exact Kernel /24`, `Adapter /4`.

---

## 1. Design Thesis: Shifting Deterministic Work Out of `Qwen3-0.6B`

Phase A (`SLM_BOTTLENECK_ROOT_CAUSE.md`) proved that the primary failures of `/5 minimal_ops` (`10/28` on `HOLDOUT_40`, `2/10` on `DEV_CALIBRATION_16`) were **not** caused by `Planner /26` or `Exact Kernel /24` (`26/26` non-typo `HOLDOUT_40` positives and `9/9` non-typo `DEV_CALIBRATION_16` positives passed under `Test C_canon`), nor primarily by abstract reasoning limits alone. Instead, `minimal_ops` forced a 0.6B quantized model (`Qwen3-0.6B-Q4_K_M`) to perform deterministic bookkeeping:

1. **Free-form string & quote reproduction:** Generating `"quote"` substrings consumed ~150–190 output tokens per call (`min/avg/max = 221/267.1/297` completion tokens in `/5` Phase A), inflating generation time to ~7–9s and causing spelling/truncation errors.
2. **Surface wording outside `Registry.kiem_nguon` closed grammar:** Even valid SLM parses failed `Source Gate` on paraphrased Vietnamese phrasing (`"mặt bên ... nằm trong mặt phẳng vuông góc"`, `"đo được 45 độ"`, `"điểm chính giữa"`, `"cạnh đáy đều"`, etc.).
3. **Whole-sentence quote sensitivity (`_lien_ket_cau`):** When a single Vietnamese sentence contained multiple numbers or a multi-clause description (`"có cạnh đáy là a và các cạnh bên bằng a"`), coarse clause quotes triggered `UNGROUNDED_VALUE` or `SOURCE_PREMISE_UNREAD`.
4. **Premature fast-path short-circuit:** `adaptive_input_router.py` trusted `"partial"` fast-path returns when `LOCAL_DETERMINISTIC_HYBRID` only needed escalation for `slm_h01`/`slm_h03`-class paraphrased wording unless `_should_escalate_to_compact_slm` gated properly.
5. **TCP port / socket exhaustion on Windows (`WinError 10013`):** Repeated ephemeral connections without HTTP keep-alive exhausted loopback connections during sustained benchmarks.

`/6` solves these deterministically without changing model size (`Qwen3-0.6B-Q4_K_M` retained) and without modifying `Planner /26`, `Registry /33`, or `Exact Kernel /24`.

---

## 2. Deterministic Indexing Layer: Clauses, Entities (`E`), Quantities (`Q`)

`build_compact_clause_context(working_text)` (`backend/app/ai/local_slm_extractor.py`) builds a typed candidate index before `Qwen3-0.6B` runs:

1. **Indexed Clauses (`index_source_clauses`):** Splits normalized text at sentence boundaries into `[0]`, `[1]`, `[2]`, ... with character spans `(start, end, text)`.
2. **Candidate Entities (`CandidateEntity` table `E`):**
   - **Solids (`kind="solid"`):** Dotted pyramid (`S.ABC`, `S.MNPQ`), dotted prism (`ABC.A'B'C'`, `MNP.M'N'P'`, `ABCD.A'B'C'D'`), and dotless regular/general tetrahedron (`tứ diện [đều] ABCD`) with prime/subscript vertex support (`_SOLID_RE`). Tracks `solid_subtype` (`pyr | pri | cube | box`), `is_regular_solid`, and `clause_ids`.
   - **Polygons (`kind="poly"`):** Explicit parenthesized faces `(SBC)`, `(ABCD)`, named polygons (`đáy ABC`, `tam giác MNP`, `hình vuông ABCD`, `mặt bên XYY'X'`), and base polygons from solid notations.
   - **Segments (`kind="seg"`):** 2-vertex segments/lines (`SA`, `SC`, `AA'`, `MM'`), plus regular lateral anchor (`SA` only when `is_regular_solid` and unambiguous `"cạnh bên"` context) and cube vertical anchor (`AA'`).
   - **Points (`kind="point"`):** All grounded vertices (`S`, `A`, `A'`, `M`, ...).
3. **Candidate Quantities (`CandidateQuantity` table `Q`):**
   - Extracts numeric/symbolic scalars (`a`, `2a`, `a√3`, `3a/2`, `45°`, `60°`, fractions) and ratio words (`_WORD_RATIO_MAP`: `gấp đôi -> 2`, `nửa -> 1/2`), tagging `implied_unit` (`""` for length/area/volume/ratio vs `"deg" | "sin" | "cos" | "tan" | "cot"` for angle clauses) and `clause_ids`.

---

## 3. Span-Audited Conservative Canonicalizer (`slm-verified-normalizer/1`)

Implemented in `backend/app/ai/slm_verified_normalizer.py` (`normalize_for_slm_grounding`):

- **Provenance Ledger:** Every surface rewrite emits a `VerifiedNormalizationStep(rule_id, original_span, original_excerpt, normalized_excerpt, validation_result, ambiguity_status)` recorded inside `grounding_envelope["normalization_provenance"]`.
- **Fail-Closed Typo Guard (`_TYPO_CHECKS`):** Diacritic / orthographic typos (`vuôg góc`, `vuông goc`, `hình chop`, `khối chop`, `chóp ... đên`, `trung điêm`, `lăng tru`) set `typo_detected=True` and abort extraction **without invoking the SLM or rewriting the input**, returning `reason_code="AMBIGUOUS_FACT"`, `failure_taxonomy="TYPO_REQUIRES_CONFIRMATION"`, `grounding_status="REJECTED_TYPO_AMBIGUITY"`.
- **Conditional & Negation Guards (`_apply_safe_sub(..., skip_if_cond_or_neg=True)`):** Rewrites touching sentences with conditional markers (`nếu`, `khi`, `giả sử`) or negated geometric predicates (`không vuông góc`, `chẳng`, `không phải ...`) are blocked with `validation_result="REJECTED_CONSERVATIVE"`.
- **Universal vs Ambiguous Lateral Edges (`VN05_ALL_LATERAL`):** Preserves `"các"` (`"các cạnh bên bằng \1"`) on universally quantified lateral edges (`"tất cả các cạnh bên đều bằng a"`), while leaving bare underspecified `"cạnh bên bằng 2a"` un-rewritten so ambiguity detection triggers deterministically.

---

## 4. Clause-Scoped Bounded Dynamic GBNF (`build_compact_grammar_for_context`)

Instead of a single unconstrained JSON Schema or unbounded free-text generation, each problem compiles a per-problem, whitespace-free, literal-constrained GBNF grammar over exact source literals:

```json
{"s":[0,"pyr","S.ABCD",0],"r":[{"c":0,"p":"reg_poly","a":"ABCD","q":"a"},{"c":1,"p":"perp_lp","a":"SA","b":"ABCD"},{"c":1,"p":"ang_lp","a":"SC","b":"ABCD","q":"45°"}],"g":[{"c":2,"t":"vol","tgt":"S.ABCD"}],"u":[]}
```

Key structural constraints compiled directly into the GBNF grammar:

1. **Zero free-form quotes or invented tokens:** SLM emits only clause IDs (`"c"`), compact predicate/goal codes (`"p"`/`"t"`), and exact entity/quantity string literals from `E` and `Q`.
2. **Solid Anchoring (`solid{idx_s}`):** Each solid entity restricts `"c"` to its occurrence clause(s), fixes `stype` (`pyr | pri | cube | box`), and fixes `reg` (`0 | 1`).
3. **Clause-Local & Lexical-Cue Pruning (`relc{cid}`):**
   - Pure question clauses (`_PURE_QUESTION_RE` without premise markers) are excluded from `relc{cid}`, preventing `GOAL_CLAUSE_USED_AS_PREMISE`.
   - Implicit base polygon labels (e.g., `ABC` inside `S.ABC`) are offered in clause `cid` only when `"đáy"` or explicit `ABC` appears in that clause.
   - Polygon vertex arity splits into `tri` (length 3: `right_tri`, `right_iso_tri`, `iso_tri`, `cent`, `ang_vtx`) and `quad` (length `>= 4`: `rect`, `para`, `trap`, `iso_trap`, `rhom`), preventing type mismatches.
   - Binary same-kind predicates (`face_perp`, `ang_pp`, `perp_ll`, `eq_len`, `dihed`) require `len >= 2` and enumerate distinct `a != b` pairs when `len <= 5`.
   - Quantity slots separate `lqty` (lengths/areas/volumes), `rqty` (dimensionless ratios under explicit ratio cues), and `aqty` (`deg | sin | cos | tan | cot`).
   - Angle sub-spans split on `,|;` ignoring `"vuông góc"` (`(?<!vuông\s)\bgóc\b`) to scope `ang_lp` vs `ang_pp` vs `ang_ll`.
4. **Finite Bounded Clause Sequences (`rseq{cid}` + Right-Fold `rellistreq`):**
   - Each premise clause `cid` bounds emissions at `k_max = min(6, max(2, raw_qty_occ + struct_cues))` via `rseq{cid}`, and clauses compose monotonically (`c0 <= c1 <= ...`) via right-fold `rellistreq`, eliminating both `temperature=0` infinite repetition loops and empty `{"r":[],"g":[],"u":[]}` bailouts.
5. **Goal-Verb Scoping (`_GOAL_VERB_RE`):** Separates question verbs (`tính | tìm | xác định | hỏi | ?`) from premise noun occurrences (`"vuông góc"`, `"độ dài"`).
6. **Two-Branch Root Rule:** Requires non-null solid + non-empty `r` + non-empty `g` (max 2 goals) whenever `u=[]`; otherwise requires explicit unresolved justification `u` (`ambig | missing | unsup | contra`).

---

## 5. Static-Prefix KV Cache, Lowerings & `Source Gate` Compatibility

1. **Static KV-Cached System Prefix (`_build_compact_clause_messages`, `cache_prompt=True`):** All schema rules and 2 dense worked Vietnamese examples (`P.UVW` pyramid with multi-`len` + `ang_lp` + `dist_pt_plane`; `XYZ.X'Y'Z'` right prism with `mid` + `reg_poly` + `face_perp` + `ang_pp` + `vol`) live in a 100% static `system` message. Because per-problem GBNF strictly restricts emitted literals to the current problem's `E` and `Q` tables, few-shot examples teach slot structure without enabling cross-problem symbol hallucination.
2. **Deterministic Composite Lowering (`validate_and_lower_compact_clause`):**
   - `right_iso_tri(ABC, B)` lowers to `right_angle(B, [A, C])` + `equal_length([B, A], [B, C])`.
   - `cube` expands to `right_prism` + `regular_polygon` + `segment_length`; `box` expands to `right_prism` + `rectangle`.
   - Universal regular lateral edge (`is_reg_lat`) accepts `SA` / `S.ABC` with `"cạnh bên" in clow` while `_AMBIGUOUS_LATERAL_SINGLE_RE` continues rejecting non-regular singular `"cạnh bên"`.
3. **`Source Gate` Quote Selection (`_select_source_gate_quote`):** Splits compound conjunction clauses on `, | và | với | đồng thời` for `_VALUE_ROLE_KINDS` (`regular_polygon`, `rhombus`, `segment_length`, `height`), matching `[t]` requirements with minimum extraneous numbers; specifically passes `["cạnh bên", qty]` when `is_reg_lat` holds so `"Cho hình chóp tam giác đều S.ABC có cạnh đáy là a và các cạnh bên bằng a"` lowers `segment_length(["S","A"], "a")` with `"các cạnh bên bằng a"` instead of the base sub-clause.
4. **9-Field Cache Identity & Windows Socket Stability (`local-slm-runtime/2`):**
   - `LocalSlmRuntime` uses a persistent `http.client.HTTPConnection` keep-alive socket with single transient `WinError 10013` retry and exposes `prompt_eval_ms`, `token_gen_ms`, `cached_prompt_tokens`, `json_decode_ms`, `queue_wait_ms`, and `tokens_per_sec`.
   - `LocalSlmExtractionCache` keys singleton extraction responses under `HYBRID_V6_LOCAL_SLM` over 9 dimensions: `exact_input_text`, `model_key`, `model_sha256`, `runtime_version`, `strategy`, `schema_version`, `schema_sha256`, `grounding_policy_version`, `parser_version`, and `capability_identity`.

---

## 6. Observed Verification Stats (Live CPU `Qwen3-0.6B-Q4_K_M`, `ALLOW_LIVE_AI=0`)

Measured directly in [`SLM_LATENCY_OPTIMIZATION.json`](SLM_LATENCY_OPTIMIZATION.json) and `DEV_CALIBRATION_16` paired ablation (`SLM_EXTRACTION_ABLATION.json`):

| Metric | `/5 minimal_ops` (`cache_prompt=False`) | `/6 compact_clause` (`cache_prompt=False`) | `/6 compact_clause` (`cache_prompt=True`, full `/6`) |
| --- | ---: | ---: | ---: |
| `DEV_CALIBRATION_16` Positive (`all / non-typo`) | `2/10` (`2/9`) | — | **`8/10` (`8/9`)** (`cal_p08` refused `TYPO_REQUIRES_CONFIRMATION`) |
| `DEV_CALIBRATION_16` Negative Refusal | `6/6` | — | **`6/6`** (`0` Mode-A leaks) |
| Completion Tokens (paired `n=10`, p50) | `267.1` (Phase A avg across 28 calls) | `98.5` | **`98.5`** (`-63.1%` vs `/5` avg) |
| Prompt Eval Time `pe` (paired `n=10`, p50) | n/a | `2078.93 ms` | **`339.72 ms`** (`p50=901.5` cached prompt tokens) |
| Uncached SLM Inference `p50` (paired `n=10`) | `9012.71 ms` | `5084.77 ms` | **`3429.11 ms`** (`-62.0%`) |
| Uncached SLM Inference `p50 / p95` (`n=30`, `threads=6`) | `6683.53 / 8025.00 ms` (`/5` warm) | — | **`3204.27 / 5392.59 ms`** |
| Uncached SLM Inference `p50 / p95` (`n=12`, `threads=8`) | — | — | **`2993.00 / 4452.59 ms`** |
| Per-Clause Batching Ablation (`n=10`, p50) | — | — | `4319.97 ms` (slower than single-pass) |
| Extraction Cache Hit E2E (`n=30`, separate) | — | — | **`39.64 / 53.92 ms`** (`30/30` hits) |
| Combined Peak RSS (`n=30`, `threads=6`) | `1040.57 MiB` (`/5`) | — | `1042.93 MiB` median, `1049.30 MiB` max |

Representative live `/6` compact trace (`cal_p03_sq_pyramid_angle`, `task-414` / `task-517` / `task-633`):
- **Input:** `"Khối chóp S.ABCD nhận ABCD làm hình vuông cạnh a. Cạnh SA vuông góc với đáy, góc tạo bởi SC và (ABCD) đo được 45 độ. Tính thể tích khối chóp S.ABCD."`
- **Normalized:** `"Cho khối chóp S.ABCD có đáy ABCD là hình vuông cạnh a. Cạnh SA vuông góc với đáy, góc giữa SC và (ABCD) bằng 45°. Tính thể tích khối chóp S.ABCD."`
- **Raw SLM JSON (`102` tokens):** `{"s":[0,"pyr","S.ABCD",0],"r":[{"c":0,"p":"reg_poly","a":"ABCD","q":"a"},{"c":1,"p":"perp_lp","a":"SA","b":"ABCD"},{"c":1,"p":"ang_lp","a":"SC","b":"ABCD","q":"45°"}],"g":[{"c":2,"t":"vol","tgt":"S.ABCD"}],"u":[]}`
- **Output:** `SERVED`, answer `a³√2/3`, `scene3d_continuity_errors = 0`.
