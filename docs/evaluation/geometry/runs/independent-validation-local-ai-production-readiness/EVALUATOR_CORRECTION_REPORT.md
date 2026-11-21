# AXO HYBRID /8 — EVALUATOR CORRECTION REPORT (Phase P1 / Gate D1)

- **Evaluator Implemented:** `axo-math-evaluator/2` ([`slm_math_evaluator_v2.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/slm_math_evaluator_v2.py))
- **Unit Test Suite:** [`test_slm_math_evaluator_v2.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_slm_math_evaluator_v2.py) (`56 passed`, positive, negative, trig distinction, goal-kind typing, unparseable/out-of-domain fail-closed)
- **Historical Reconciliation Artifact:** [`EVALUATOR_RECONCILIATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/EVALUATOR_RECONCILIATION.json)
- **Status:** `Gate D1 = PASS` (`VERIFIED` · `evaluate_images.py` untouched under `BLOCKED_OWNERSHIP` / frozen run evidence rule; versioned evaluator + tested handoff patch delivered)

---

## 1. Root Cause of the `/7` `cos²=` Bug (`VERIFIED`)

1. **Primary defect in [`evaluate_images.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/evaluate_images.py#L82-L95) (`EVI.same_value`):**
   - Lines `L85–L91`:
     ```python
     squared = re.fullmatch(r"cos²\s*=\s*(.+)", left.strip())
     degrees = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*°", right.strip())
     if squared:
         value = numeric(squared.group(1), 1.0)
         if value is None or not degrees:
             return None
     ```
   - Whenever `left` is `"cos²=2/3"` **and** `right` (oracle) is ALSO `"cos²=2/3"` (`v7h_p7_06..10`), `degrees` is `None`, so `same_value` returns `None`, and `_grade_positive` evaluates `bool(None) == False`.
   - Additional defects found during audit of `evaluate_images.py`:
     - **Asymmetry:** `same_value("cos²=1/2", "45°") -> True`, whereas `same_value("45°", "cos²=1/2") -> None`.
     - **Floating-point approximation:** numeric probing at two arbitrary points `a ∈ {1.3, 2.1}` via `math.isclose(..., abs_tol=1e-9)` rather than exact algebraic arithmetic.
     - **Incomplete trig / goal typing:** no `sin`, `sin²`, `tan`, `tan²`, `cot`, `cos(2x)`, no `goal_kind` validation, and `"V = 2a³"` vs `"S = 2a³"` stripped LHS blindly.
2. **Secondary defect found in [`nl_eval_scoring.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/nl_eval_scoring.py#L55-L72) (`nl_eval_scoring.same_value`):**
   - Line `L58` strips `re.sub(r"^cos²=", "", s)` **unconditionally**, conflating trig expressions (`cos²=1/2`) with untagged scalars (`1/2`) or incompatible trig kinds (`cos=1/2`), fails on `"45°"`, and fails on symbolic lengths/volumes containing `a` (e.g., `"3a√22/22"`).

---

## 2. Design of `axo-math-evaluator/2` (`slm_math_evaluator_v2.py`)

- **Exact algebraic substrate:** Elements of $\mathbb{Q}(\sqrt{k_1}, \dots) \cdot a^{d_a} \cdot \pi^{d_\pi}$ stored via canonical tuples `(sqfree_k, Fraction)` — rationalizing denominators algebraically (e.g., `3a/√22 == 3a√22/22`, `(√6+√2)/4`, nested radical denesting for `15°`/`75°`) with zero floating-point evaluation.
- **Typed quantity classification:**
  - `SCALAR_OR_DIMENSIONAL` (plus metric SI scaling for `mm/cm/dm/m/km` up to power 3 when both sides carry metric units),
  - `ANGLE_DEG` (`N°`, `độ`) & `rad` multiples of `π`,
  - `TRIG_COS`, `TRIG_COS2`, `TRIG_SIN`, `TRIG_SIN2`, `TRIG_TAN`, `TRIG_TAN2`, `TRIG_COT`, `TRIG_COT2`, `TRIG_COS_2X` (`cos(2x)=...` via $\cos^2 x = (1 + \cos 2x)/2$).
- **Strict safety invariants verified by `56` pytest assertions:**
  - `cos(x)`, `cos²(x)`, and `cos(2x)` are strictly distinguished (`cos=1/2` vs `cos²=1/2` -> `False / MISMATCH_WRONG_TRIG_FUNCTION`; `cos(2x)=0` vs `cos²=0` -> `False / MISMATCH_WRONG_TRIG_FUNCTION`).
  - Untagged scalars never satisfy trig/angle (`cos²=1/2` vs `1/2` -> `False / MISMATCH_SCALAR_VS_TRIG`), except when `goal_kind="trig_cos2"` explicitly asks for `cos²(...)`.
  - Goal-kind & dimension powers enforced (`2a²` rejected under `goal_kind="volume"`).
  - Unparseable strings and out-of-range trig domains (`cos²=3/2`, `cos=2`, `√(3a)`, `NaN`, empty strings) fail closed (`matched = None`).

---

## 3. Case-Level Reconciliation of `v7h_p7_06..10` (`VERIFIED`)

| Case ID | Engine Served | Oracle | `EVI.same_value` (Raw /7) | `axo-math-evaluator/2` | Verdict Code & Exact Form | Error Type |
|---|---|---|---|---|---|---|
| `v7h_p7_06` | `cos²=2/3` | `cos²=2/3` | `None` (`ok=False`) | `True` | `EXACT_EQUIVALENT_SAME_KIND` (`TRIG_COS2`, `2/3`) | Format Mismatch (EVI Bug) |
| `v7h_p7_07` | `cos²=1/2` | `cos²=1/2` | `None` (`ok=False`) | `True` | `EXACT_EQUIVALENT_SAME_KIND` (`TRIG_COS2`, `1/2`) | Format Mismatch (EVI Bug) |
| `v7h_p7_08` | `cos²=2/5` | `cos²=2/5` | `None` (`ok=False`) | `True` | `EXACT_EQUIVALENT_SAME_KIND` (`TRIG_COS2`, `2/5`) | Format Mismatch (EVI Bug) |
| `v7h_p7_09` | `cos²=2/3` | `cos²=2/3` | `None` (`ok=False`) | `True` | `EXACT_EQUIVALENT_SAME_KIND` (`TRIG_COS2`, `2/3`) | Format Mismatch (EVI Bug) |
| `v7h_p7_10` | `cos²=2/3` | `cos²=2/3` | `None` (`ok=False`) | `True` | `EXACT_EQUIVALENT_SAME_KIND` (`TRIG_COS2`, `2/3`) | Format Mismatch (EVI Bug) |

Independent hand derivation confirms every oracle mathematically:
- `v7h_p7_06`: square `2a`, `HU=2a`, diagonal `2a√2`, `tan = 1/√2` ⇒ `cos² = 2/3`.
- `v7h_p7_07`: square `a√2`, `CA=2a`, diagonal `2a`, `tan = 1` (`45°`) ⇒ `cos² = 1/2`.
- `v7h_p7_08`: square `3a`, `NG=3a√3`, diagonal `3a√2`, `tan = √(3/2)` ⇒ `cos² = 2/5`.
- `v7h_p7_09`: square `2a√3`, `PA=2a√3`, diagonal `2a√6`, `tan = 1/√2` ⇒ `cos² = 2/3`.
- `v7h_p7_10`: square `4a`, `ZE=4a`, diagonal `4a√2`, `tan = 1/√2` ⇒ `cos² = 2/3`.

---

## 4. Full Raw vs Corrected Historical Scores (`SLM_V7_HOLDOUT_112` & `/5`–`/7` Check)

### 4.1 `SLM_V7_HOLDOUT_112` (80 Positives · 32 Negatives)

| Configuration | Raw `EVI` Positives | Corrected `v2` Positives | Corrected Rate (Wilson 95% CI) | Negatives Safe (`32`) | Wrong Served (`v2`) | Error Taxonomy on Positive Misses (`v2`) |
|---|---|---|---|---|---|---|
| `Config A` (`deterministic_v145`) | `34/80` (`42.50%`) | `39/80` | **`48.75%`** `[0.3811, 0.5951]` | `32/32` | `0` | `41` Refused/Unserved (`0` wrong served) |
| `Config B` (`/6 compact + orig Qwen3-0.6B`) | `42/80` (`52.50%`) | `47/80` | **`58.75%`** `[0.4780, 0.6889]` | `32/32` | `0` | `33` Refused/Unserved (`0` wrong served) |
| `Config C` (`/7 closure + orig Qwen3-0.6B`) | `53/80` (`66.25%`) | `58/80` | **`72.50%`** `[0.6186, 0.8108]` | `32/32` | `0` | `22` Refused/Unserved (`0` wrong served) |
| `Config D` (`/7 closure + Qwen3-0.6B-AxoV7`) | `69/80` (`86.25%`) | `74/80` | **`92.50%`** `[0.8459, 0.9652]` | `32/32` | `0` | `6` Refused/Unserved (`0` wrong served; see [`SLM_FAILURE_CASE_AUDIT.md`](SLM_FAILURE_CASE_AUDIT.md)) |

- Paired McNemar exact test (`C -> D` under `axo-math-evaluator/2`): **16 gained, 0 lost, `p = 0.000031` (`3.1e-05`)**.
- Zero formatting/grader discrepancies (`0` changed verdicts across `900+` scored rows) were found in `SLM_V7_ABLATION`, `/6` `SLM_NEW_HOLDOUT_EVALUATION`, `/6` `SLM_EXTRACTION_ABLATION`, `/5` `SLM_EXTRACTION_EVALUATION`, or `/5` `SLM_BASELINE_COMPARISON`.
- All 8 frozen historical files checked kept identical LF-normalized SHA-256 hashes before and after execution (`frozen_artifacts_unmodified = true`).

---

## 5. Frozen `evaluate_images.py` Owner Handoff (`BLOCKED_OWNERSHIP / FROZEN_RUN_ARTIFACT`)

Because [`evaluate_images.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/evaluate_images.py) lives inside a frozen historical evaluation run directory (`controlled-vision-real-image-validation/run.json`), modifying it directly would invalidate frozen run hashes (`AGENTS.md §4`). For any future vision/image campaign that reuses that helper, apply or delegate directly to [`slm_math_evaluator_v2.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/slm_math_evaluator_v2.py):

```diff
--- a/docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/evaluate_images.py
+++ b/docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/evaluate_images.py
@@ -80,15 +80,6 @@ def numeric(expr: str, a: float) -> float | None:
     return top / denominator * tail
 
 def same_value(left: str, right: str) -> bool | None:
-    # The engine serves angles between lines/planes exactly as `cos²=<value>`; such angles lie in [0°, 90°],
-    # where cos² determines the angle, so a printed `N°` is compared through cos²(N°).
-    squared = re.fullmatch(r"cos²\s*=\s*(.+)", left.strip())
-    degrees = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*°", right.strip())
-    if squared:
-        value = numeric(squared.group(1), 1.0)
-        if value is None or not degrees:
-            return None
-        return math.isclose(math.cos(math.radians(float(degrees.group(1).replace(",", ".")))) ** 2, value, abs_tol=1e-9)
-    values = [(numeric(left, a), numeric(right, a)) for a in (1.3, 2.1)]
-    if any(x is None or y is None for x, y in values):
-        return None
-    return all(math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9) for x, y in values)
+    from slm_math_evaluator_v2 import same_value_v2
+    return same_value_v2(left, right)
```
