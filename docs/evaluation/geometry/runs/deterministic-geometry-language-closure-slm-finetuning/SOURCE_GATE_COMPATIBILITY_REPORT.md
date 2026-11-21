# SOURCE_GATE_COMPATIBILITY_REPORT — AXO HYBRID /7 (`§7`)

> **Campaign:** AXO HYBRID /7 (`deterministic-geometry-language-closure-slm-finetuning`)  
> **Boundary Statement:** `backend/app/simulation/geometry_functions/registry.py` (`kiem_nguon`, `_lien_ket_cau`, `_C_KHOI`, `_C_VAI`, `_C_MAT`, `_C_CHIEU`, `_khoi_dung`, `_co_doi_tuong_hinh`, `construction_source_bound`), `planner.py`, `engine.py`, and `adapter4_route.py` were **inspected read-only and NEVER modified** during AXO HYBRID /7.

---

## 1. Compatibility Findings Verified on Real Code

### 1.1 `v6h_f5_02_pp_60_rect` (`§5 Nhóm D` Special Audit)
- **Failure in `/6`:** `REFUSED (UNSUPPORTED_BASE_SHAPE)` — `"đáy 4 đỉnh không có lời gọi xác định hình (đa giác đều / hình chữ nhật)"`.
- **Verified Root Cause (`engine.py:1459-1503` + `hybrid_offline` Gold probe):**
  - `Exact Kernel /24` (`engine.py:1459`) already implements `elif rect:` (`rectangle_chart`) for pyramids with rectangular bases and plane-plane angles.
  - Feeding the exact Gold `compact_clause` JSON (`s=[0,"pyr","P.EFGH",0]`, `r=[rect(EFGH), len(EF,2a), len(EH,a√3), perp_lp(PE,EFGH), ang_pp(PGH,EFGH,60°)]`, `g=[vol(P.EFGH)]`) through `validate_and_lower_compact_clause` → `run_hybrid_offline` returns **`SERVED`** (`100%` accepted by `Source Gate`, `Planner /26`, and `Exact Kernel /24`).
  - Therefore, `/6`'s refusal on `v6h_f5_02_pp_60_rect` was **purely an SLM omission (`Qwen3-0.6B` omitted `rect(EFGH)` under 5-constraint load)** — **NOT** a Kernel capability limitation and **NOT** a Source Gate rejection.

### 1.2 Upstream Bridges vs Protected `Source Gate` Grammar Rules
| Observed Failure Signature | Source Gate Function Checked (Read-Only) | True Root Cause | Handled Upstream in `/7`? | Status |
|---|---|---|---|---|
| `PREDICATE_NOT_IN_QUOTE` on `slm_h23` (`S.ABC` solid quote) | `_co_doi_tuong_hinh` (`registry.py:1556`) | `select_clean_quote` picked `'SA vuông góc với (ABC)'` because `{S,A,B,C}` matched without requiring `"chóp"`/`"S.ABC"` | Yes (`select_clean_quote` contiguous + cue enforcement) | `RESOLVED_UPSTREAM` |
| `ROLE_NOT_IN_QUOTE` on `v6h_f5_03` (`"EM vuông góc..."`) | `_co_doan` (`registry.py:1670`) | `_CONVERSATIONAL_PREFIX_RE` (`re.IGNORECASE`) stripped `"EM "` as Vietnamese pronoun `"em"` | Yes (case-safe greeting regex in `local-slm-extractor/3`) | `RESOLVED_UPSTREAM` |
| `UNGROUNDED_VALUE` on `v6h_f6_04` (`M.ABCD`, `MAB`) | `_co_doi_tuong_hinh` + `_C_MAT` (`registry.py:1929`) | (1) `select_clean_quote` matched scattered `M,A,B` inside `Cho khối chóp M.ABCD`; (2) `_C_MAT` does not accept `"nằm vuông góc với"` without `"trong mặt phẳng"` | Yes (`_cand_has_contiguous` + `VN05_NAM_VUONG_GOC_FACE` → `"và nằm trong mặt phẳng vuông góc với"`) | `RESOLVED_UPSTREAM` (`Source Gate` variant logged in Handoff) |
| `SOURCE_OBJECT_MISMATCH` on `v6h_f8_03` (`hình chiếu ... là trung điểm I của KL`) | `construction_source_bound` (`registry.py:8637`) | Merged projection+midpoint phrasing + `mặt đáy (KLM)` not parsed as single atomic point+projection pair | Yes (`VN05_PROJ_MIDPOINT` atomic split + comma quote trim) | `RESOLVED_UPSTREAM` (`Source Gate` variant logged in Handoff) |
| `CONDITIONAL_CLAUSE` on `v6h_f8_02` (`còn DD' thì có độ dài bằng 2a`) | Conditional classifier in `registry.py` | Surface contrastive `"còn ... thì có độ dài bằng"` left literal `"thì"` in text | Yes (`VN05_CON_THI` v2 with full-sentence conditional guard) | `RESOLVED_UPSTREAM` |
| `PREDICATE_NOT_IN_QUOTE` on `v6h_f1_04` / `slm_h04` (`lăng trụ đứng`) | `_khoi_dung` (`registry.py:1522`) & `perp_lp` keyword check | SLM emitted redundant `perp_lp(GG', GHK)` where text said `"chiều cao GG'=2a"` without `"vuông góc"`; plus comma connector `, đáy GHK` | Yes (`VN03_SOLID_COMMA_DAY` + `VN05_CHIEU_CAO_PRISM` + `v7` GBNF `perp_lp` tightening) | `RESOLVED_UPSTREAM` |
| Direct bare `"mọi cạnh bên dài X"` / `"nằm vuông góc với"` / compound projection inside `registry.kiem_nguon` itself | `_C_VAI` (`1778`), `_C_MAT` (`1929`), `construction_source_bound` (`8637`) | Native Source Gate grammar does not recognize those raw surface forms if submitted un-normalized | No direct edit to `registry.py` permitted in `/7` | `BLOCKED_OWNERSHIP` (documented in [SOURCE_GATE_OWNER_HANDOFF.md](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SOURCE_GATE_OWNER_HANDOFF.md)) |
| Unconfirmed diacritic typos (`slm_h24`, `slm_h26`, `cal_p08`) | Input ambiguity policy (`§6.C2`) | Intentionally refused as `TYPO_REQUIRES_CONFIRMATION` without auto-correction | Preserved fail-closed | `INTENTIONAL_SAFETY_REFUSAL` |
| SLM predicate omissions on multi-constraint clauses (`v6h_f1_03`, `v6h_f2_04`, `v6h_f5_02_pp_60_rect`, `v6h_f6_02`, `v6h_f6_03`) | `Exact Kernel /24` supports all 5 when extracted correctly | Base `Qwen3-0.6B` omits 1 of 4–5 predicates (`rect`, `right_tri`, `right_iso_tri`, `rhom`) | Handled by `P4` Targeted LoRA Fine-Tuning (after `P2`/`P3` gating) | `DEFERRED_TO_P4_FINETUNING` |

---

## 2. Guarantee of Non-Relaxation

- Zero edits to `registry.py`, `kiem_nguon`, `_lien_ket_cau`, or `typed_fact_next_extraction.py`.
- Zero bypass flags or mock Source Gate receipts.
- All outputs from `local-slm` continue to pass verbatim through `run_hybrid_offline` → `doc_typed_fact_next_v2` → `kiem_nguon` → `Planner /26` → `Exact Kernel /24` → `Adapter /4`.
