# SOURCE_GATE_OWNER_HANDOFF — Native Source Gate Grammar Extensions (Optional Follow-Up)

> **Handoff ID:** `source-gate-handoff/1`  
> **Campaign:** AXO HYBRID /7 (`deterministic-geometry-language-closure-slm-finetuning`)  
> **Ownership Status:** **`BLOCKED_OWNERSHIP`** — `backend/app/simulation/geometry_functions/registry.py` (`Registry /33`, `kiem_nguon`, `_lien_ket_cau`) was NOT modified in `/7`. Upstream normalizer/quote rules in `slm-verified-normalizer/2` and `local-slm-extractor/3` bridge these cases safely inside `HYBRID_ROUTE_MODE=local-slm`, while this handoff documents the exact minimal native Source Gate extensions if the Source Gate / Live-Gemini owner wishes to support raw un-normalized quotes natively across `HYBRID_ROUTE_MODE=live`.

---

## Handoff Item 1 — `_C_VAI` (`registry.py:1778`): Universal Quantifier `"tất cả các"` & Verb `"dài"`

- **Minimal Reproducible Input:** `"Cho hình chóp tam giác đều E.MNP, mặt đáy có cạnh bằng 2a và mọi cạnh bên dài 2a√2. Tính thể tích khối chóp E.MNP."`
- **Expected vs Actual (without upstream `slm-verified-normalizer/2`):**
  - Expected: `segment_length(['E','M'], '2*a*sqrt(2)')` binds via universal `"mọi cạnh bên dài 2a√2"`.
  - Actual: `_C_VAI` matches `(?:=|bằng|là)` but omits `dài`, and `_VAI` prefix lacks `tất cả các`. Un-normalized quote raises `UNGROUNDED_VALUE`.
- **Proposed Grammar Extension:** Allow optional `tất\s+cả\s+` before `(?:các|mọi|mỗi)` and allow `dài` alongside `bằng|là|=` in `_C_VAI` (`registry.py:1778-1780`) ONLY when plural/universal quantifier (`các`/`mọi`/`mỗi`/`tất cả`) or explicit `cạnh bên đều` is present.
- **Positive Examples:** `"tất cả các cạnh bên đều bằng a"`, `"mọi cạnh bên dài 2a√2"`.
- **Adversarial Negatives (MUST STILL REFUSE):** `"cạnh bên dài 2a"` (singular non-regular), `"cạnh bên bằng 2a"`, `"một số các cạnh bên dài 2a"`, `"các cạnh bên không dài 2a"`, `"nếu mọi cạnh bên dài 2a"`.
- **Compatibility & Regression Impact:** None on existing contracts when strictly scoped behind plural quantifier check; requires full `C1–C3` Source Gate security regression.
- **Owner Approval Requirement:** Explicit sign-off by Simulation / Registry `/33` owner (`APPROVED_BY_USER` cannot be self-granted).

---

## Handoff Item 2 — `_C_MAT` (`registry.py:1929`): `"nằm vuông góc với"` (Elliptical Face-Plane Form)

- **Minimal Reproducible Input:** `"Cho khối chóp M.ABCD có đáy ABCD là hình vuông cạnh 2a. Mặt bên MAB là tam giác đều nằm vuông góc với mặt đáy (ABCD). Tính thể tích M.ABCD."`
- **Expected vs Actual (without upstream `VN05_NAM_VUONG_GOC_FACE`):**
  - Expected: `face_perpendicular_base(['M','A','B'], ['A','B','C','D'])`.
  - Actual: `_C_MAT` requires `(?:nằm\s+trong\s+mặt\s+phẳng\s+)?vuông\s+góc\s+với`, rejecting `"nằm vuông góc với"`.
- **Proposed Grammar Extension:** In `_C_MAT` (strictly for 3+-vertex `_MAT_NHAN` / face nouns, NEVER 2-vertex segments!), allow `(?:nằm(?:\s+trong\s+mặt\s+phẳng)?\s+)?vuông\s+góc\s+với`.
- **Adversarial Negatives:** `"SA nằm vuông góc với đáy"` (line, not face), `"mặt bên MAB không nằm vuông góc với đáy"`, `"mặt bên vuông góc với đáy"` (ambiguous unlabelled face).
- **Owner Approval Requirement:** Explicit sign-off by Simulation / Registry `/33` owner.

---

## Handoff Item 3 — `_C_CHIEU` & `construction_source_bound` (`registry.py:1804, 8637`): Merged Compound Projection onto Edge Midpoint

- **Minimal Reproducible Input:** `"Cho hình chóp H.KLM có đáy KLM là tam giác đều cạnh 2a. Hình chiếu vuông góc của H lên mặt đáy (KLM) là trung điểm I của KL, HK=2a. Tính thể tích khối chóp H.KLM."`
- **Expected vs Actual (without upstream `VN05_PROJ_MIDPOINT`):**
  - Expected: `midpoint(I, ['K','L'])` + `orthogonal_projection(H, I, ['K','L','M'])`.
  - Actual: `construction_source_bound` rejects `mặt đáy (KLM)` + `"là trung điểm I của KL"` as `SOURCE_OBJECT_MISMATCH` unless decomposed into atomic clauses `"Gọi I là trung điểm của KL. Hình chiếu vuông góc của H lên mặt phẳng (KLM) là I."`.
- **Proposed Grammar Extension:** Support `"lên (?:mặt )?đáy \((?P<p>...) \)"` and merged `"là (?P<mid>trung điểm I của KL)"` only when point `I` and edge `KL` belong uniquely to the declared solid's base.
- **Adversarial Negatives:** `"Hình chiếu của H là trung điểm I"` (missing edge), `"Hình chiếu của H là M hoặc N"`.
- **Owner Approval Requirement:** Explicit sign-off by Simulation / Registry `/33` owner.

---

## Handoff Item 4 — Live-Gemini Route Compatibility Note (`v6h_f5_02_pp_60_rect` & Contrastive `còn ... thì`)

- Both `v6h_f5_02_pp_60_rect` (rectangle pyramid + dihedral angle) and contrastive `còn DD' thì có độ dài bằng 2a` work end-to-end once properly extracted/normalized: no `Kernel` or `Planner` modification needed. Any downstream extension for contrastive non-conditional `còn ... thì` directly inside `registry.py`'s conditional detector also requires explicit owner review.
