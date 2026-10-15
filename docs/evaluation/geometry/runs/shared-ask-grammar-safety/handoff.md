# CLAUDE_RESUME_HANDOFF — shared-ask-grammar-safety (2026-10-16)

**Status:** `ASK_GRAMMAR_FINAL_REGRESSION_FIX_READY_FOR_REVIEW` (Full geometry gate: `PENDING FINAL CANDIDATE`). Không merge, không push, không refreeze candidate trước khi review độc lập đạt.

## Kiểm lại trước khi tin

```bash
git rev-parse HEAD main origin/main          # research/source-bound-result-planning; main = origin/main = 2a3c0787
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_shared_ask_grammar.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_result_binding_planning.py -q
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/shared-ask-grammar-safety/grammar_probe.py <out.json>
```

## Trạng thái

- Đã đóng toàn bộ phát hiện trong review độc lập `9ce1298f` (`C1`–`C4`, `I2`, `I3` tại `4acfc731`), phát hiện kiểm toán đối với `4acfc731` (`CR-1`, `CR-2`, `IM-1`, `IM-2` tại `34a04eaf`), **và** toàn bộ phát hiện kiểm toán độc lập đối với `34a04eaf` (`CR-A`, `CR-B`, `IM-A`, cùng hai đính chính tài liệu `IM-2`) (xem [`report.md`](report.md) §8–§9):
  - **CR-A:** `_than_muc_tieu_hop_le` và `_doc_muc_tieu_cau_hoi` yêu cầu mệnh đề mục tiêu phải là quan hệ/tính chất hình học hoàn chỉnh có vị từ (`_VI_TU_MUC_TIEU`). Các cụm bội số/tỉ lệ chỉ hợp lệ trong quan hệ đẳng thức nhị nguyên đóng giữa hai đoạn thẳng (`_QUAN_HE_BOI_SO`, ví dụ `"SC bằng hai lần SA"`), chặn hoàn toàn các mệnh đề mục tiêu cụt hoặc chứa bổ ngữ đổi đại lượng (`"SC gấp đôi"`, `"một nửa SC"`, `"hai lần SC"`, `"2 lần SC"`, `"và gấp đôi"`).
  - **CR-B:** Thay thế `_GHI_CHU` túi từ lặp và nhánh mặc định `return True` trong `_kiem_ghi_chu` bằng 3 mẫu câu đóng (`_GHI_CHU_TRINH_BAY`, `_GHI_CHU_THANG_DO`, `_GHI_CHU_DON_VI_KET_QUA`). Từ chối fail-closed (`QUESTION_CONTEXT_UNSUPPORTED`) mọi câu ghi chú định dạng/làm tròn/thay đổi kết quả chưa được xác minh (`"Kết quả đến hàng phần trăm."`, `"Ghi đáp số ở hàng phần trăm."`, `"Viết kết quả dưới dạng phân số."`, `"Đáp số là phần mười của kết quả."`, `"Ghi kết quả theo hàng nghìn."`, `"Lưu ý: kết quả để ở dạng căn thức."`).
  - **IM-A:** Vì `ask_angle_line_plane` và `ask_angle_plane_plane` trả `cos²=...`, các câu hỏi `"Tính số đo (của) góc giữa ..."` bị từ chối fail-closed (`QUESTION_CONTEXT_UNSUPPORTED`) trên cả Route A và Route B (kể cả khi nối câu hỏi khác trong câu ghép), trong khi vẫn phục vụ bình thường `"Tính góc giữa ..."` (`COMP1`, `DIH1`, `H07`, `H30`, `B29`).
  - **IM-2 (Đính chính tài liệu):**
    - `P11` trong [`grammar_probe.py`](grammar_probe.py) (`lines 89–95`) là `"Gọi M là trung điểm SC, tính {phrase}."` (được phục hồi từ Stage A `I2` — `_doc_phep_dung_cau_hoi`), **không phải** mẫu câu `"bằng hai cách"` (mẫu `"bằng hai cách"` là positive control của `IM-1` trong `test_shared_ask_grammar.py`).
    - Đường dẫn đúng của metrics Benchmark 30 là [`verification/benchmark-30-metrics.json`](verification/benchmark-30-metrics.json) và [`../source-bound-result-planning/verification/benchmark-30/metrics.json`](../source-bound-result-planning/verification/benchmark-30/metrics.json) (`19 correct_served`, `9 correct_refusal`, `0 wrong_served`, `2 false_refusal` strict xfail `B27`/`B28`; `test_hybrid_compiler_benchmark.py`: `98 items = 94 passed, 4 xfailed`).
- Biên lai RED tại `34a04eaf` (`146 failed, 459 passed`) lưu ở [`red/red-review-34a04eaf.txt`](red/red-review-34a04eaf.txt) (`SHA-256: 12f9f0f50460ac425d7cf08d9445367c90a6a1e684e7516ad81039a73ff484d0`) và 6 biên lai GREEN lưu ở [`verification/`](verification/).

## Bước tiếp theo

1. Chạy **Independent Code Review** đối với commit đóng lỗi hiện tại.
2. Sau khi review độc lập đạt (`PASS`), mới thực hiện refreeze `EVALUATION_CANDIDATE.json`, cập nhật `inputs/candidate_divergence.json` và chạy authoritative T3 trên detached worktree sạch.
3. Scene3D product–Playwright parity audit (`ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` OPEN).


