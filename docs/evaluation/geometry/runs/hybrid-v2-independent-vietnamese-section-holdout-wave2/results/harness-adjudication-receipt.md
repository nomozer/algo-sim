# Harness Adjudication Receipt (`hybrid-v2-independent-vietnamese-section-holdout-wave2`)

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_SECTION_HOLDOUT_WAVE2`
- **Pre-Execution Freeze Commit:** `7e5c3ddde78710f4ea174956302d11e711b51635`
- **Raw Scored Run (Preserved Untouched):** `results/scored-run-1/`
- **Harness-Corrected Scored Run:** `results/scored-run-2-harness-corrected/`
- **Machine Receipt:** [`results/harness-adjudication-receipt.json`](harness-adjudication-receipt.json)

---

## 1. Summary of the Harness Defect

In `results/scored-run-1/`, the raw scorer (`tools/evaluate_holdout_wave2.py` lines 441–443) reported:
- `SERVED_CORRECT`: `3/48` (`W2-B08`, `W2-B12`, `W2-B14` — all 3 served Category B cases)
- `WRONG_SERVED`: `2/48` (`W2-A01`, `W2-A03` — both served Category A cases)
- `FALSE_REFUSAL`: `43/48`
- `REFUSE` cases refused: `48/48` (`0/48` wrong-served negatives; `33/48` `REFUSED_CORRECT_REASON`)

Inspection of `results/scored-run-1/track-a.json` showed that for both `W2-A01` and `W2-A03`, every geometric, topological, solid-identity, vertex-provenance, and area-squared check passed with zero mismatches, and the **sole** entry in `oracle_mismatches` was:

```json
"oracle_mismatches": [
  "missing or unverified section closure_certificate"
]
```

### Root Cause in `tools/evaluate_holdout_wave2.py`

Prior to checking `is_cat_b`, `tools/evaluate_holdout_wave2.py` lines 441–443 executed:

```python
cert = sec.get("closure_certificate")
if not isinstance(cert, dict) or cert.get("verified") is not True or not cert.get("rule"):
    checks.append("missing or unverified section closure_certificate")
```

However, in the frozen product (`backend/app/ai/adapter4_route.py` lines 69–80 & 280–288 and `backend/app/simulation/geometry_functions/engine.py` lines 1420–1435):
1. **Category B (`ENGINE_DERIVED_SECTION`):** `sec["closure_certificate"]` is always a dictionary (`{"verified": True, "version": "plane-section-certificate/1", "rule": "engine_derived_plane_section", ...}`).
2. **Category A (`DINH_CAT_CANH`):** `_phong_bi` sets `"boundary": (d.get("closure") or {}).get("boundary")` and `"closure_certificate": d.get("closure")`. In `engine.kiem_dinh_cat` (lines 1420–1435), `d["closure"]` is populated **only** when `d.get("declared_boundary") is not None` or `d.get("derived")` (a derived pyramid stands on the section). For standard single-solid Category A section problems without `declared_boundary` or a derived pyramid, `sec["boundary"]` is `None` and `sec["closure_certificate"]` is `None`, which `adapter4_route._validate_sections` (lines 280–283) explicitly accepts while validating the Category A certificate via `sec["vertices"]` (`label`, `edge`, `provenance`, `stated`).

---

## 2. Independent Mathematical Verification of `W2-A01` and `W2-A03`

### Case `W2-A01` (`P-A`, `triangular_pyramid`, `stated_intersections`, `section_only`)
- **Problem Text:** *"Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 7, BC = 7, cạnh bên SA vuông góc với mặt phẳng (ABC) và SA = 7. Mặt phẳng (α) đi qua điểm A và vuông góc với đường thẳng SC, cắt các cạnh bên SB, SC lần lượt tại M, N. Xác định thiết diện của hình chóp S.ABC cắt bởi mặt phẳng (α)."*
- **Independent Exact Geometry:**
  - Orthonormal coordinates: $A=(0,0,0),\ B=(7,0,0),\ C=(7,7,0),\ S=(0,0,7)$.
  - $\overrightarrow{SC} = (7, 7, -7)$; plane $(\alpha)$ through $A(0,0,0)$ perpendicular to $SC$ has equation $x + y - z = 0$.
  - On $SB$: $P(t) = (7t, 0, 7(1-t)) \implies 7t - 7(1-t) = 0 \implies t = 1/2$ ($M$ on $SB$ at $t = 1/2$).
  - On $SC$: $P(t) = (7t, 7t, 7(1-t)) \implies 14t - 7(1-t) = 0 \implies t = 1/3$ ($N$ on $SC$ at $t = 1/3$).
  - Through-point $A$ lies at solid vertex $A$ ($t = 1$ on $SA$).
- **Product Output vs. Oracle:**
  - `route_status = "SERVED"`, `adapter4_status = "SERVED"`, `envelope_status = "ok"`.
  - `certificate_category = "DINH_CAT_CANH"`.
  - `vertices`:
    - `{"label": "A", "edge": ["S", "A"], "provenance": "THROUGH_POINT_REUSE", "stated": false}` ($t = 1 \rightarrow$ `("VERTEX", "A")`)
    - `{"label": "M", "edge": ["S", "B"], "provenance": "SOURCE_NAMED", "stated": true}` ($t = 1/2 \rightarrow$ `("EDGE", "B", "S", 1/2)`)
    - `{"label": "N", "edge": ["S", "C"], "provenance": "SOURCE_NAMED", "stated": true}` ($t = 1/3$ from $S$ to $C \rightarrow$ `("EDGE", "C", "S", 2/3)`)
  - Exact cyclic polygon match (`3` vertices, `0` geometric/provenance discrepancies).

### Case `W2-A03` (`P-A`, `triangular_pyramid`, `stated_intersections`, `section_and_area`)
- **Problem Text:** *"Cho hình chóp S.MNP có đáy MNP là tam giác vuông tại M, MN = 10, MP = 14, cạnh bên SM vuông góc với mặt phẳng (MNP) và SM = 12. Gọi I là trung điểm của cạnh SM. Mặt phẳng (β) đi qua điểm I và vuông góc với đường thẳng SM, cắt các cạnh bên SN, SP. Xác định thiết diện của hình chóp S.MNP cắt bởi mặt phẳng (β). Tính diện tích thiết diện của hình chóp S.MNP cắt bởi mặt phẳng (β)."*
- **Independent Exact Geometry:**
  - Orthonormal coordinates: $M=(0,0,0),\ N=(10,0,0),\ P=(0,14,0),\ S=(0,0,12),\ I=(0,0,6)$.
  - Plane $(\beta)$ through $I(0,0,6)$ perpendicular to $SM(0,0,-12)$ has equation $z = 6$.
  - Cuts $SM$ at $I$ ($t = 1/2$), $SN$ at $I_1(5,0,6)$ ($t = 1/2$), and $SP$ at $I_2(0,7,6)$ ($t = 1/2$).
  - Right triangle $II_1I_2$ has legs $5$ and $7$, so $\text{Area} = 35/2$ and $\text{Area}^2 = 1225/4$.
- **Product Output vs. Oracle:**
  - `route_status = "SERVED"`, `adapter4_status = "SERVED"`, `envelope_status = "ok"`.
  - `certificate_category = "DINH_CAT_CANH"`.
  - `vertices`:
    - `{"label": "I", "edge": ["S", "M"], "provenance": "THROUGH_POINT_REUSE", "stated": false}` ($t = 1/2 \rightarrow$ `("EDGE", "M", "S", 1/2)`)
    - `{"label": "I1", "edge": ["S", "N"], "provenance": "STATED_UNNAMED", "stated": true}` ($t = 1/2 \rightarrow$ `("EDGE", "N", "S", 1/2)`)
    - `{"label": "I2", "edge": ["S", "P"], "provenance": "STATED_UNNAMED", "stated": true}` ($t = 1/2 \rightarrow$ `("EDGE", "P", "S", 1/2)`)
  - `answers = {"mg1": "35/2"}`, `area_squared = "1225/4"` (exact match to oracle `"1225/4"`).

---

## 3. Side-by-Side Comparison (`scored-run-1` vs. `scored-run-2-harness-corrected`)

| Metric | Raw (`results/scored-run-1/`) | Harness-Corrected (`results/scored-run-2-harness-corrected/`) |
|---|---|---|
| Total Cases | `96` | `96` |
| Positive (`SERVE`) Cases | `48` | `48` |
| `SERVED_CORRECT` | `3 / 48` (`6.25%`, CI `[0.0215, 0.1684]`) | **`5 / 48`** (`10.42%`, CI `[0.0453, 0.2217]`) |
| Exact Oracle Agreement Among Served Positives | `3 / 5` (`60.00%`) | **`5 / 5`** (`100.00%`, CI `[0.5655, 1.0000]`) |
| Positive `FALSE_REFUSAL` | `43 / 48` (`89.58%`, CI `[0.7783, 0.9547]`) | `43 / 48` (`89.58%`, CI `[0.7783, 0.9547]`) |
| Positive `WRONG_SERVED` | `2 / 48` (`W2-A01`, `W2-A03`) | **`0 / 48`** (`0.00%`, CI `[0.0000, 0.0741]`) |
| Negative (`REFUSE`) Cases Refused | `48 / 48` (`100.00%`, CI `[0.9259, 1.0000]`) | **`48 / 48`** (`100.00%`, CI `[0.9259, 1.0000]`) |
| Negative `WRONG_SERVED` | `0 / 48` (`0.00%`) | **`0 / 48`** (`0.00%`) |
| Negative `REFUSED_CORRECT_REASON` | `33 / 48` (`68.75%`, CI `[0.5467, 0.8005]`) | `33 / 48` (`68.75%`, CI `[0.5467, 0.8005]`) |
| Total `WRONG_SERVED` (`96` cases) | `2 / 96` (`2.08%`) | **`0 / 96`** (`0.00%`, CI `[0.0000, 0.0385]`) |
| `HARNESS_ERROR` / `PRODUCT_EXCEPTION` | `0` / `0` | `0` / `0` |
