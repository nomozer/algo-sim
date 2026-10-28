# Independent Code & Evidence Review — `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`

- **Reviewer Role:** Independent Code & Evidence Reviewer (`fca2b9f1-95b8-4d68-b5a0-f702b1b75e48`, read-only audit)
- **Task / Wave:** `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`
- **Audited Research Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\w3-f1-cross-sentence-plane-grounding` (`research/hybrid-v2-w3-f1-cross-sentence-plane-grounding`)
- **Audited Candidate Commit:** `b02b2c422e4049dc6ff0a94996f335424e7b02b9`
- **Audited Product Commit:** `a609c4871a75426db52eb8b7a7be8ba3460fcf8c`
- **Audited Product Tree Hash (`118` files):** `918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72`
- **Authoritative Baseline (`main = origin/main`):** `e137623c4f674135a8d7884b78614c132eb78085`
- **Preserved Historical Holdout Wave 3 Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\independent-section-holdout-wave3` (`0943f0ee6bd2a2b297827e39fa7c07054d716ea9`)
- **Final Verdict:** `APPROVED_NO_FINDINGS`

---

## 1. Ten-Dimension Mandatory Audit (Owner GO §12)

| # | Dimension | Audit Finding & Machine Evidence | Verdict |
|---|---|---|---|
| 1 | **Scope discipline** | `git diff --name-only e137623c4f674135a8d7884b78614c132eb78085..b02b2c422e4049dc6ff0a94996f335424e7b02b9 -- backend/app frontend/src` touches **only** `backend/app/simulation/geometry_functions/planner.py`, `backend/app/simulation/geometry_functions/registry.py`, and `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`. Zero edits to `engine.py`, `radical.py`, `adapter4_route.py`, `typed_fact_next.py`, or `frontend/src`. No expansion into `W3-F2`, `W3-F3`, `W3-F4`, or `W3-F5`. In the 144-case locked Wave 3 post-feedback replay, the 15 multi-defect cases (`7` `W3-F2`, `6` `W3-F3`, `2` `W3-F4`) remain refused by their respective secondary defect codes after passing `_kiem_phu` plane grounding. | `PASS` |
| 2 | **Anti-hardcode check** | Full line-by-line inspection of the product diff across `planner.py`, `registry.py`, and `typed_fact_next_bridge.py` confirms **zero** hardcoded Wave 3 case IDs (`W3-B*`, `W3-A*`), specific vertex labels, problem texts, or expected answers in product code. All grammar extensions (`_NOI_QUAN_HE_MAT`, `_QUA_HAI_DUONG`, `_DIEM_TRUOC_HAI_DUONG`, `_td_mat_truoc_khoi`, `_het_dinh_nghia`, `mat_song_song_dung_nguon`) are structural and general across Latin/Greek plane symbols and primed/unprimed vertex labels. | `PASS` |
| 3 | **Unique plane definition invariant** | Both `_v2_plane_def_quotes` (`typed_fact_next_bridge.py` lines 149–186: `return [cands[0]] if len(cands) == 1 else []`) and `mat_song_song_dung_nguon` (`registry.py` lines 3788–3790 `if len(khop_de) != 1: continue` and lines 3812–3825 checking all `_ALL_PLANE_DEF_MAU` matches and requiring `len(def_sents) == 1`) strictly enforce that a cross-sentence plane reference `(P)` resolves to a **unique** non-imperative valid plane definition sentence in `problem_text` (`de`). | `PASS` |
| 4 | **Conflicting or missing plane definition refusal** | Missing plane definitions (`DEV-NEG-01`), definitions missing `through_point` (`DEV-NEG-02`) or geometric relation (`DEV-NEG-03`), two contradictory definitions of `(P)` (`DEV-NEG-04`), two distinct planes sharing name `(P)` (`DEV-NEG-05`), wrong plane symbol in question (`DEV-NEG-06`), and source-vs-payload `plane_name` mismatches (`DEV-NEG-07`, `DEV-NEG-18`) all fail closed in `mat_song_song_dung_nguon` / `_mat_fact` with `SOURCE_OBJECT_MISMATCH`. | `PASS` |
| 5 | **Compound `section_and_area` grounding** | Compound `section_and_area` requests are served if and only if both the section construction (`thiet_dien` in `mat_song_song_dung_nguon`) and the area measurement (`hoi_p` in `mat_song_song_dung_nguon` + `_hoi_dien_tich_thiet_dien_phu` in `planner.py`) are grounded in the source text and covered by `_kiem_du_kien_cau_hoi`. When the source asks only for the section and the payload injects an area goal (`DEV-NEG-13`), `_cau_hoi` (`planner.py` lines 1014–1016) refuses with `NOT_ASKED_IN_SOURCE`. When the source asks for the area of a different section (`DEV-NEG-14`), it refuses with `SOURCE_OBJECT_MISMATCH`. | `PASS` |
| 6 | **Category A and Category B certificate & geometric invariants** | `ENGINE_VERSION = "geometry-function-engine/14"`, `ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`, and `PLANE_SECTION_CERTIFICATE_VERSION = "plane-section-certificate/1"` are untouched. Across `results/green-after.json` and `test_w3_f1_cross_sentence_plane_grounding.py`, all served Category B (`P-B`) cases emit `certificate_category == "ENGINE_DERIVED_SECTION"` with `closure_certificate["verified"] is True`, R2 pedagogical auxiliary point distinction, and exact `Fraction` oracle match; all served Category A (`P-A`) cases preserve `DINH_CAT_CANH` (`STATED_INTERSECTION_SECTION`), `closure_certificate is None`, and exact `Fraction` oracle match. | `PASS` |
| 7 | **Mandatory 20 adversarial/tamper vectors** | All `20 / 20` mandatory negative/tamper vectors (`DEV-NEG-01` .. `DEV-NEG-20`) fail closed (`20 / 20` refused, `0` `WRONG_SERVED`, `20 / 20` exact expected refusal code agreement: `17` `SOURCE_OBJECT_MISMATCH`, `1` `NOT_ASKED_IN_SOURCE`, `1` `CONDITIONAL_CLAUSE`, `1` `UNSUPPORTED_CAPABILITY`), independently verified by running `pytest backend/tests/geometry/test_w3_f1_cross_sentence_plane_grounding.py -q` (`23 passed`). | `PASS` |
| 8 | **Honest evidence classification** | `results/wave3-post-feedback-regression.json` is explicitly labeled `"evidence_classification": "POST_FEEDBACK_DEVELOPMENT_REGRESSION"` with `"not_an_independent_blind_holdout": true`. `inputs/development.json` is labeled `"DEVELOPMENT_AND_POST_FEEDBACK_REGRESSION"`, and `results/red-before.json` / `results/green-after.json` are labeled `"DEVELOPMENT_EVALUATION"`. No artifact claims the post-feedback replay as a blind holdout. | `PASS` |
| 9 | **Historical Wave 3 preservation** | `.superpowers/worktrees/independent-section-holdout-wave3` is on `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` at `0943f0ee6bd2a2b297827e39fa7c07054d716ea9` with `git status --porcelain` empty and `results/scored-run-1/` byte-identical (`summary.json`: `ca864b728...`, `track-a.json`: `bf0ddd7a0...`, `track-b.json`: `d358ce4ca...`). Root repository `D:\Documents\projects\algo-sim` remains at `e137623c4f674135a8d7884b78614c132eb78085`. | `PASS` |
| 10 | **Verification & freeze integrity** | Independently executed `freeze_evaluation_candidate.py --verify` (`Candidate khớp bản đã đóng băng (mã sản phẩm: 118 file, 918d3404ac60e81d…).`). `verification/scope-and-evidence.json`, `verification/cache-and-fixtures.json` (`CACHE_VERSION = 130`, `41/41` preview fixtures verified), `verification/tiers.json` (`795 passed, 5 xfailed`), `verification/full-t3/receipt.json` (detached at `b02b2c422e4049dc6ff0a94996f335424e7b02b9`, product commit `a609c4871a75426db52eb8b7a7be8ba3460fcf8c`, tree hash `918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72`, `12592` backend passed, `1417` frontend passed, `FULL_PRODUCT_GATE_PASS`), and `candidate_divergence.json` are 100% consistent with the actual repository state. | `PASS` |

---

## 2. Severity Findings

- `BLOCKER`: `0`
- `MAJOR`: `0`
- `MINOR`: `0`
- `NIT`: `0`

---

## 3. Final Reviewer Verdict

**`APPROVED_NO_FINDINGS`**
