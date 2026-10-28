# Handoff — Hybrid V2 Independent Vietnamese Geometry Holdout Wave 3 (`hybrid-v2-independent-vietnamese-geometry-holdout-wave3`)

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Branch:** `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`
- **Worktree:** `.superpowers/worktrees/independent-section-holdout-wave3`
- **Authoritative `main` baseline:** `e137623c4f674135a8d7884b78614c132eb78085`
- **Product commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Product freeze (`118` files):** `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`)
- **Final status:** `INDEPENDENT_HOLDOUT_WAVE3_EXECUTED`

---

## 1. Chuỗi Commit Cổng Đã Khóa

1. **Gate 1 — Preregistration & Scorer Infrastructure (`f438a62a3485ce9b8d687cb91102c366e6848960`):**
   - Hoàn tất `plan.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `refusal-taxonomy.json`, `curator-brief.md`, `tools/evaluate_holdout_wave3.py`, `tools/test_evaluate_holdout_wave3.py`, `tools/dedup_check_wave3.py`, `tools/audit_curator_log.py` trước khi tạo corpus.
2. **Gate 2 — Scorer Qualification Receipt (`53cba0c8a63ae3cf7c1b058b8b09f07046449f06`):**
   - Hoàn tất kiểm định `24 / 24` test suite tổng hợp + đột biến (`10 / 10` đột biến bị chặn, `0%` sống sót) và khóa `verification/scorer-qualification-receipt.json` trước khi tạo corpus.
3. **Gate 3 & Gate 4 — Blinded Corpus, Independent Oracle Verification & Pre-Execution Freeze (`2332f7ad3d1a73733bbc720bcf36705c67bc2d6b`):**
   - Subagent Curator (`206cf35f-d6b5-4ac4-a16a-38ae2ced52d1`) tạo `144` bài mới hoàn toàn (`inputs/holdout-wave3.json`) và oracle hữu tỷ độc lập (`oracle/geometry.json`, `oracle/oracle_holdout_wave3.py`, `oracle/expected.json`), thay thế `W3-B01` trước khi freeze khi chạm cờ bất biến tỷ lệ và ghi nhận tại `corpus-provenance.md`.
   - Subagent `Independent Holdout Wave 3 Oracle Reviewer` (`9fdf8f17-aeaf-4fd3-8530-34c02d1363c2`) tái tính độc lập 100% cả `72` bài dương tính và kiểm tra `72` bài âm tính trước khi chạy product (`status: "ORACLE_VERIFIED_BEFORE_EXECUTION"`, `discrepancies: []`).
   - Khóa `holdout-manifest.json` trước khi chạy product.

---

## 2. Tóm Tắt Kết Quả One-Shot Scored Execution (`results/scored-run-1/`)

- **Positive Serve Accuracy (Tổng 72 bài `SERVE`):** `20 / 72` (`27.78%`, 95% Wilson CI `[18.76%, 39.05%]`)
  - **Stratum `P-B` (Category B):** `12 / 54` (`22.22%`, 95% Wilson CI `[13.20%, 34.94%]`)
  - **Stratum `P-A` (Category A):** `8 / 18` (`44.44%`, 95% Wilson CI `[24.56%, 66.28%]`)
  - **Câu hỏi đơn (`section_only` + `area_only`):** `20 / 48` (`41.67%`; riêng `P-A` câu hỏi đơn đạt `8 / 12 = 66.67%`)
  - **Câu hỏi ghép (`section_and_area`):** `0 / 24` (`0.00%` — bị chặn bởi `W3-F1: SOURCE_OBJECT_MISMATCH`)
- **Exact Oracle Agreement khi đã phục vụ:** `20 / 20` (`100.00%`, 95% Wilson CI `[83.89%, 100.00%]`)
- **Tỷ lệ thành công của `Planner /17 -> Engine /14 -> Adapter /4 -> Certificate /1` sau khi qua `Source Gate`:** `20 / 20` (`100.00%`, `0` lỗi `RADICAL_DOMAIN_OVERFLOW`, `0` lỗi từ chối oan Category A `PREVIEW_RESULT_INVALID`)
- **Negative Fail-Closed Refusal Rate:** `72 / 72` (`100.00%`, 95% Wilson CI `[94.93%, 100.00%]`)
- **Negative Refusal Reason Agreement:** `60 / 72` (`83.33%`, 95% Wilson CI `[73.09%, 90.20%]`)
- **Wrong-Served Rate (`WRONG_SERVED`):** `0 / 144` (`0.00%`, 95% Wilson CI `[0.00%, 2.60%]`)
- **Track C Scene3D Semantics:** `20 / 20` (`100.00%` sạch, `0` rò rỉ `_prime`, `0` rò rỉ danh tính nguồn)
- **Uncaught Exceptions / Harness Errors:** `0 / 144` (`0.00%`)

---

## 3. Trạng Thái Git & Giới Hạn Phạm Vi

- Không sửa bất kỳ file sản phẩm nào (`freeze_evaluation_candidate.py --verify` trả về `MATCH`, `118` file, `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`).
- Không merge vào `main`, không push lên remote, không xoá worktree.
- `0` live provider calls (`ALLOW_LIVE_AI = "0"`).
