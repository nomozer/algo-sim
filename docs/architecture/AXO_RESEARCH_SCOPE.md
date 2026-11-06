# Axo — phạm vi nghiên cứu chính thức

Ngày chốt: 2026-11-07 (run `axo-postmerge-consolidation`). Tài liệu này là ranh giới sản phẩm; mọi đề xuất tính năng mới đối
chiếu với nó trước khi vào kế hoạch.

## 1. Axo là gì

Axo giúp học sinh **hình dung, quan sát và hiểu quá trình dựng hình học không gian** bằng mô phỏng 3D **có kiểm chứng**.

Pipeline trọng tâm:

```
Đề toán tiếng Việt → Typed Facts → Hybrid Planner → Compiler → Exact Geometry Kernel & Verifier
  → Scene3D Contract → trình tự dựng hình có giải thích → mô phỏng 3D
```

Axo **không** là hệ giải bài tập tổng quát lấy việc trả đáp số làm thành quả chính.

## 2. Giá trị cốt lõi

1. Nhận diện đúng đối tượng và quan hệ hình học.
2. Dựng hình chính xác (toạ độ hữu tỉ/căn thức, không xấp xỉ).
3. Tự kết hợp các hàm hình học có sẵn trong thư viện đóng (`REGISTRY`).
4. Không sinh mã riêng cho từng đề; không hardcode nhãn, dữ kiện hay đáp số.
5. Trình tự dựng theo quan hệ phụ thuộc.
6. Hiển thị đúng đối tượng chính và phụ.
7. Phân biệt rõ **Đề cho / Được dựng / Được suy ra / Hình phụ**.
8. Giải thích nguồn gốc của từng đối tượng (provenance, chứng nhận).
9. Quay, phóng to, quan sát từ nhiều góc.
10. Kiểm chứng tính nhất quán hình học.

## 3. Tính toán ≠ trình bày đáp số

Phép tính (vd thể tích V = 30) có thể **cần** cho Kernel/Verifier: nó là chứng nhận rằng hình dựng ra thoả đề. Giữ năng lực
tính, chứng nhận và test xác minh. Thứ được tinh gọn là **trình bày**: một số đo chỉ hiện khi nó giúp hiểu hình (dữ kiện, chứng cứ
phụ trợ), không bao giờ là đáp số được quảng bá làm trung tâm. Không làm giảm tính kiểm chứng để giao diện trông đơn giản hơn.

## 4. Phân loại thành phần (kiểm toán 2026-11-07)

| Thành phần | Vai trò | Phân loại | Quyết định | Bằng chứng |
|---|---|---|---|---|
| `backend/app/ai/typed_fact_next_extraction.py`, `geometry_functions/typed_fact_next_bridge.py` | trích dữ kiện, cầu sang TypedFact | CORE | giữ | tuyến duy nhất của `/api/analyze` (`AGENTS.md §3`) |
| `geometry_functions/planner.py`, `registry.py`, `engine.py` | phối hợp hàm đóng, bố cục, kiểm dữ kiện | CORE | giữ | 1 577 payload phân loại, 0 từ chối nội bộ (run `axo-final-reliability-premerge-gate`) |
| `simulation/geometry/*`, `certificates.py`, `semantic_program/interpreter.py` | kernel chính xác, verifier, chứng nhận | CORE | giữ | oracle tay + oracle độc lập (`docs/evaluation/geometry/custodian/`) |
| `ai/adapter4_route.py`, `construction_continuity.py`, `semantic_program/route.py` | Scene3D contract, bước dựng tích luỹ | CORE | giữ | — |
| `answer_exact`, `kq_<goal>` trong cảnh, `HybridAnswerView` | đáp số chính xác **là chứng nhận** cho frontend | CORE (verifier) | giữ, **không hiển thị làm đáp số** | `scene3d-student-presentation-policy.ts`: `showMathResultsPanel: false`, `canDisplayEntityValue` ẩn giá trị đáp số |
| `frontend/src/simulations/domains/geometry/scene3d-*` (view, camera, semantic-policy, model) | renderer, camera, provenance, trình tự sư phạm | CORE | giữ | camera 30/30, consistency 41/41 |
| Bước dựng trong xưởng (`buildPedagogicalConstructionPlan`) | trình tự hiển thị | CORE | giữ, không đổi | 29 cảnh thật: 0 bước "Kết luận mục tiêu"/"Kết luận và tính toán"; 2 bước "nhấn mạnh kết quả" là **dựng đoạn được hỏi** |
| Phiên, đăng nhập, lịch sử, quota/sổ ghi lượt dùng, idempotency, migration, telemetry tối thiểu | vận hành | SUPPORTING | giữ, không mở rộng | runs `axo-final-reliability-premerge-gate`, `axo-premerge-closure` |
| Tóm tắt mục tiêu (`dock-goal-summary`) | chỉ hiện khi **chưa** kiểm chứng được mục tiêu (trạng thái không nhất quán/thiếu chứng nhận) | OPTIONAL PRESENTATION | giữ (thông tin cần thiết, không phải đáp số) | `scene3d-goal-authority.test.tsx` |
| `Scene3DExplorer.tsx` (menu "Phân tích toán học… xem kết quả", "Đại lượng") | khung xem cũ | OUT OF SCOPE cho sản phẩm | **chưa gỡ** — sản phẩm không render nó (chỉ 13 file test import); gỡ kéo theo sửa các test đó ⇒ task riêng | `grep "from .*Scene3DExplorer"` chỉ trúng file `*.test.tsx` |
| Chế độ quiz / luyện tập có hướng dẫn | — | OUT OF SCOPE | không làm | quyết định 2026-08-17 (gỡ quiz), 2026-07-19 (không mở practice) |

## 5. Không làm trong phạm vi này

Quiz, luyện tập có hướng dẫn, nhiều chế độ dựng, bảng điều khiển mới, thay header/navigation/màu đã chốt, thay logo Axo,
đổi camera khi không có hồi quy, thay công thức hay cách sinh toạ độ khi không có lỗi đã chứng minh.

## 6. Đề xuất cho task sau (chưa làm)

1. Gỡ `Scene3DExplorer.tsx` và chuyển các test còn giá trị của nó sang `AxoWorkspaceV62`.
2. Backend `learner_messages.py`/`hybrid_preview.py` còn viết "AlgoSim" trong thông điệp người học; frontend đã đổi hiển thị
   (`frontend/src/branding.ts::displayBrand`). Sửa tận nguồn cần chạm `backend/app` ⇒ đóng băng lại candidate và cập nhật test khoá
   văn bản; để task riêng.
