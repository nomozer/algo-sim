# Independent adversarial review: eighth continuation (962a0d53..df81deba)

The review covers all three Continuation 8 slices on Route D `/4`:
1. Polyhedral role-phrase Source Gate parity (`_C_VAI` + `_cua_khop` delegating to `_loai_cum_dung`);
2. Pedagogical construction trace hardening (`preconditions` and `postconditions` exported on `KetQuaTuyen.trace` and `route_d.construction_trace`, stripped of post-execution kernel claims on all `REFUSED` paths, and axisless standalone sphere pose);
3. Certified circumscribed spheres of polyhedra on Route D `/4` (`SolidSpec.circumscribes`, exact `Fraction` $3 \times 3$ Gram circumcenter solver, all-vertex cosphericity certificate `NO_CIRCUMSCRIBED_SPHERE`, exact `Fraction` Cholesky Euclidean chart normalization `chuan_hoa_euclid`, G4 IR perpendicular-bisector construction, independent closed-form cross-check, closed Vietnamese Source Gate grammar `_CAU_CONG_NGOAI_TIEP`, and composite polyhedron/sphere `ask_volume` disambiguation).

**Reviewer.** An independent fresh-context subagent (`0ef27125-61ad-4f33-b4aa-e126981ee0e6`) that did not write the code. It ran offline (`ALLOW_LIVE_AI = 0`), made 0 provider calls, strictly respected blind Holdout Wave 3 isolation, and edited no tracked files.

## Verdicts

| Round | Target reviewed | BLOCKER | MAJOR | MINOR | NIT | Verdict |
|---|---|---:|---:|---:|---:|---|
| 1 | Continuation 8 initial implementation on `962a0d53` | 0 | 2 (`MAJOR-1`, `MAJOR-2`) | 2 (`MINOR-1`, `MINOR-2`) | 2 (`NIT-1`, `NIT-2`) | `NOT_READY` |
| 2 | Fixed tree + regression locks (`df81deba`) | 0 | 0 | 1 (`MINOR-R2-1`, also closed in `df81deba`) | 0 | **`READY`** |

## Findings and closures

- **`MAJOR-1` (Slice 1 — `_cua_khop` prism-subclass check):** Omitting `"của"` before `"hình lập phương"` / `"hình hộp chữ nhật"` / `"hình hộp"` initially checked only coarse `khoi.fn == "prism"`. Fixed by delegating `_cua_khop` directly to `_loai_cum_dung(m["qn"], _ten_khoi_goi(khoi), calls=calls)` (checking `base` and `top` polygons), refusing incompatible prism subclasses with `UNGROUNDED_VALUE`. Locked in `backend/tests/geometry/test_route_d_role_phrase_parity.py`.
- **`MAJOR-2` (Slice 3 — composite polyhedron + sphere `ask_volume` disambiguation):** `_khoi_cua_loi_goi` counted only polyhedra (`len(khoi) == 1`), causing bare `"Tính thể tích."` / `"Tính thể tích V."` to serve the pyramid volume and causing multi-goal `"Tính thể tích khối chóp ... và thể tích khối cầu ..."` to refuse `QUESTION_CONTEXT_UNSUPPORTED` in one clause order. Fixed via `_chi_mot_khoi_3d`, updated `_khoi_khop`, and a curved-solid negative lookahead on `_CUM_HOI["ask_volume"]`. Locked in `backend/tests/geometry/test_route_d_circumscribed_spheres.py`.
- **`MINOR-1` (Slice 2 — post-engine `REFUSED` trace claims & `_phong_bi` export):** Removed the skip in `_gan_dieu_kien_vet`, stripped post-execution kernel claims via `_vet_tu_choi` on post-engine `REFUSED` returns in `function_route.py` (`SCENE_BUILD_FAILED`, `NEGATED_CLAUSE`, `PROOF_UNVERIFIABLE`), and exported `construction_trace` in `adapter4_route._phong_bi`. Locked in `backend/tests/geometry/test_route_d_pedagogical_trace.py`.
- **`MINOR-2` (Slice 2 — standalone sphere pose):** Standalone spheres (`not kc.co_truc`) emit `rule="canonical_origin_center"` and postcondition `"center_at_origin"` instead of `"axis(Oz)"`. Locked in `backend/tests/geometry/test_route_d_pedagogical_trace.py`.
- **`NIT-1`, `NIT-2`, and `MINOR-R2-1`:** Tightened `_CAU_CONG_NGOAI_TIEP[0]/[1]` punctuation and `kiem_nguon` `QUESTION` role check, guarded `khoi_cong_ir.get(a.solid)` in `bien_dich`, and applied `_chi_mot_khoi_3d` to `_khoi_thiet_dien` and `mat_cat_dung_nguon` on direct Route A.

## Mathematical & architectural audit highlights

- Exact `Fraction` $3 \times 3$ Gram linear solver (`_tam_bon_dinh`) and all-vertex cosphericity check (`NO_CIRCUMSCRIBED_SPHERE` on oblique pyramids, non-cyclic bases, and oblique prisms).
- Exact `Fraction` Cholesky chart normalization (`chuan_hoa_euclid`) verified algebraically ($\|\phi(u)\|_2^2 = u^\top G u$ for all $u \in \mathbb{Q}^3$, including non-diagonal $G_2$ on Heron triangles) and refused fail-closed (`METRIC_REQUIRES_EUCLIDEAN_CHART`) whenever $s_0, p_x, s_1, s_2 \notin \mathbb{Q}$.
- G4 IR construction via 3 perpendicular bisector planes + post-execution cross-check against `ec_cong`, `r2_cong`, and `_chung_chi_cong`.
- Zero `"circumsphere"` substrings in `backend/app/`; zero `"sphere"`/`"cylinder"`/`"cone"` branching outside `geometry/curved.py`; `DEFAULT_MODE == "LLM_ONLY"` and `CACHE_VERSION == "131"` unchanged; zero edits to `semantic_program/` or `frontend/`.

## Regression replay at `df81deba` (`inventory-phase-l.json`, `wave3-phase-l.json`)

| Set | Result |
|---|---|
| Wave 3 | `67/72` positives served correctly; `72/72` negatives refused (`62` with the exact reason); `0` wrong-served; `0` transitions |
| Locked 96 | `96/96` match, `0` wrong-served |
| 203 probes | `0` served negatives, `0` internal errors; the 12 curved probes match the registered `REFUSED -> REFUSED` transitions |
| Circumscribed sphere probe | `12/12` positives served with exact `π`/radical values; `12/12` adversarial negatives refused fail-closed |
| Registered curved controls | `32/32` remain `REFUSED` (`0` moved `REFUSED -> SERVED`) |
