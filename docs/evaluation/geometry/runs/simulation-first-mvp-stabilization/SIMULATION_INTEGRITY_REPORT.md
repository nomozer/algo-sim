# SIMULATION_INTEGRITY_REPORT — Kiểm Toán Toàn Diện Tính Toàn Vẹn Mô Phỏng (`Phase B / Gate B`)

- **Run ID:** `simulation-first-mvp-stabilization`
- **Cổng kiểm:** **Gate B — Simulation-First Integration Audit (`B1`–`B3`, P1)**
- **Phạm vi:** 9 họ hình học đang hỗ trợ + các biến thể VMMU (`r537`, `r460`, `r463`) + cấu hình minh họa có tham số tự do (`SIMILARITY_SCALE_ILLUSTRATIVE`, `HEIGHT_INVARIANT_ILLUSTRATIVE`). Không mở rộng Kernel/Parser/OCR sang họ bài mới.
- **Định nghĩa sản phẩm được bảo toàn:** Axo là hệ thống **mô phỏng hình học không gian 3D có kiểm chứng toán học** (Chế độ A mặc định ẩn đáp số qua `dapAnAn` & `output-policy/1`, tập trung vào vật thể 3D, quan hệ nhân quả và thuyết minh từng bước dựng).

---

## 1. Bảng Kiểm Tra Chuỗi `Source Facts → Verified Geometry → ConstructionGraph → Scene3D` Trên 9 Họ Hỗ Trợ

Tất cả các bài thử bên dưới được chạy qua tuyến sản phẩm thật `route_text_input` / `Hybrid /4` với `ALLOW_LIVE_AI = 0`, kiểm chứng độc lập bằng `validate_construction_continuity(scene3d, trace=construction_trace)` (`0` lỗi trên mọi ca) và kiểm tra thứ tự phụ thuộc nhân quả (`premature_dependencies = []`).

| # | Họ hình học | Mẫu kiểm chứng thực tế | `objects` | `events` (bước dựng) | Chứng nhận hình học & Nhân chứng (`witness`) | `continuity` & Phụ thuộc sớm | Banner minh hoạ (`scene_configuration`) |
|---|---|---|---|---|---|---|---|
| **1a** | Hình chóp (đều) | `vmmu_r537` (`S.ABCD`, cạnh bên `a`, `S_đáy = a²`, `d(A,(SBC))`) | `14` | `6` | `kq_q1` distance witness `A → foot(2/3,0,2/3) ∈ (SBC)` | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **1b** | Hình chóp (cạnh bên ⊥ đáy) | `vmmu_r460` (`S.ABC`, `ABC` vuông cân `B`, `SA⊥(ABC)`, `SAB` cân) | `10` | `5` | `canh_ben_S_A` mang `perpendicular_witness` `GIVEN` tại `A` | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **2** | Tứ diện | Tứ diện đều `ABCD` cạnh `a`, tính thể tích | `7` | `3` | Đủ 4 đỉnh, cạnh, đa giác khối và chứng chỉ thể tích chính xác | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **3a** | Lăng trụ (viết liền) | `vmmu_r463` (`ABCDA'B'C'D'` thoi `60°`, `AA'=2a`, `∠(AC',(ABCD))=30°`) | **`16`** *(trước sửa: 10)* | **`6`** *(trước sửa: 3)* | **4 `ENGINE_VERIFIED` `perpendicular_witness`** (`canh_ben_A_A_prime..D_D_prime`) | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **3b** | Lăng trụ (có dấu chấm) | `ABC.A'B'C'` vuông tại `A`, `AB=a, AC=2a, AA'=3a` | `13` | `6` | 3 `ENGINE_VERIFIED` `perpendicular_witness` trên 3 cạnh bên | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **4** | Hình hộp / Lập phương | `ABCD.A'B'C'D'` cạnh `a`, góc giữa `AC'` và `(ABCD)` | `18` | `8` | 4 `perpendicular_witness` + `angle-construction/1` (`[0°, 90°]`, chân `C`) | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **5a** | Thiết diện (song song) | `S.ABCD`, `M` trung điểm `SA`, `(P)` qua `M ∥ (ABCD)` | `19` | `16` | `PARALLEL_LINE_PLANE_INTERSECTION` gắn cho từng cạnh cắt của thiết diện | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **5b** | Thiết diện (phương pháp vết) | `S.ABCD` đáy hình thang vuông `A,B`, cắt bởi `(MAB)` | `14` | `11` | `COPLANAR_TRACE_INTERSECTION` + **`2` điểm phụ trợ vết (`auxiliary_points`)** | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **6** | Giao điểm & giao tuyến | `M` trung điểm `SC`, `I = AM ∩ (SBD)`, giao tuyến `(SAB) ∩ (SCD)` | `18` | `11` | Dựng `M → derived_I_line → derived_I_plane → I` rồi tới giao tuyến | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **7** | Góc đường–mặt | `S.ABC`, `ABC` vuông ở `B`, `SA⊥(ABC)`, góc `(SC, (ABC))` | `12` | `7` | `canh_ben_S_A` witness + `angle-construction/1` tia `CS`, `CA`, dấu vuông `A` | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **8** | Quan hệ hai mặt phẳng | `S.ABCD`, góc giữa `(SBC)` và `(ABCD)` | `14` | `7` | `perpendicular_witness` `SA` + `angle-construction/1` hai tia `⊥ BC` | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **9a** | Khoảng cách điểm–mặt | `S.ABCD`, `d(A, (SBC))` | `13` | `6` | `kq_q1` distance witness (chân `H` + dấu vuông trên `(SBC)`) | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **9b** | Khoảng cách đường chéo | `S.ABCD`, `d(SA, BC)` | `14` | `7` | `kq_q1` common-perpendicular witness (`A` → `B`) | `0` lỗi · `[]` sớm | `None` (duy nhất) |
| **M1** | Minh họa tỉ lệ (`unique=false`) | `S.ABCD` vuông, `SA⊥(ABCD)`, `∠(SC,(ABCD))=45°`, hỏi `∠(SB,(ABCD))` | `14` | `7` | `SIMILARITY_SCALE_ILLUSTRATIVE` (`similarity-scale-certificate/1`) + `angle-construction/1` | `0` lỗi · `[]` sớm | **`SIMILARITY_SCALE_ILLUSTRATIVE`** (`banner` minh họa bật) |
| **M2** | Minh họa bất biến cao | `S.ABCD` vuông cạnh `2`, `SA⊥(ABCD)`, hỏi `∠(AC, BD)` | `14` | `7` | `HEIGHT_INVARIANT_ILLUSTRATIVE` (`height-invariance-certificate/2` PO-1..PO-8) + dấu vuông | `0` lỗi · `[]` sớm | **`HEIGHT_INVARIANT_ILLUSTRATIVE`** (`banner` minh họa bật) |

---

## 2. Xác Minh Vai Trò Hình Học, Dòng Thời Gian & Thuyết Minh Sư Phạm (`B1`–`B3`)

1. **Tách vai trò đối tượng rõ ràng (`scene3d-roles.ts` & `Scene3DExplorer.tsx`):**
   - Các điểm, cạnh và mặt giả thiết mang nhóm hiển thị `given`; điểm dựng trung gian, mặt cắt phụ (`mp_q1`, `mp_td_sec`, `derived_*`) mang nhóm `construction`; đối tượng được hỏi (đoạn/mặt/giao tuyến/góc/khoảng cách) mang thêm `target`.
   - Khi `route_d.scene_configuration` có `unique = false` (`M1`, `M2`), adapter frontend (`cauCauHinhMinhHoa`) gắn thông báo minh họa tường minh cho học sinh, không giấu tính không duy nhất của tham số tự do ($h$ hoặc tỉ lệ $a$).
   - **Điểm `O` trên chóp đều (`r537`):** `engine.py` sinh tâm đáy `O(1/2, 1/2, 0)` như điểm cơ sở chính xác tại bước `INIT`; không có `snake_case` hay tên nội bộ rò rỉ ra UI học sinh (`DisplayLabel` chỉ là `O`).
2. **Thứ tự nhân quả hợp lệ 100% (`ConstructionGraph`):**
   - Kiểm tra tự động trên tất cả `14/14` cảnh phục vụ cho thấy **0 vật thể xuất hiện trước điều kiện tiên quyết (`depends`)**, **0 hình phụ biến mất khi đang được tham chiếu ở các bước sau**, và **0 chu trình phụ thuộc giả**.
   - Với `vmmu_r463` (lăng trụ đứng viết liền), trước sửa của **Phase A4** chuỗi bước từng sập về 3 bước; sau sửa (`CACHE_VERSION = 141`), chuỗi dựng phục hồi đúng 6 bước: `Đỉnh khởi tạo → Đáy ABCD → Đáy trên A'B'C'D' → Các cạnh bên (AA'..DD') kèm 4 chứng chỉ vuông góc → Khối lăng trụ → Đại lượng đo (ẩn ở Chế độ A)`.
3. **Thuyết minh sư phạm gọn, có kiểm chứng & Không biến Axo thành Solver (`B3`):**
   - Trong Chế độ A mặc định (`dapAnAn`), toàn bộ đại lượng `FINAL_RESULT` (`kq_q1`) **được ẩn khỏi canvas, nhãn số đo, và ô soi** (`scene3d-annotations.ts`), trong khi hình dựng nhân chứng hình học (chân đường vuông góc `witnessesShown`, cung và tia dựng góc `angleConstructionsAt`, đoạn đường cao `altitudeConstructionsAt`) **vẫn hiển thị để học sinh quan sát cách dựng** (`scene3d-view.tsx:6378-6450`).
   - Mọi bước thiết diện có lý do song song (`PARALLEL_LINE_PLANE_INTERSECTION`) hoặc phương pháp vết (`COPLANAR_TRACE_INTERSECTION`) đều mang câu giải thích tiếng Việt ngắn gọn, không đổ biến đổi đại số lời giải và không chứa trắc nghiệm `A/B/C/D`.
4. **Giới hạn hiện hành được ghi nhận trung thực (`FE-4`):**
   - Đối với thiết diện phương pháp vết (`5b`, ví dụ bước `8` và `9` của `(MAB)` cắt `(SCD)`), backend đã tính và xuất chính xác toạ độ các điểm phụ ngoài đoạn trong `event.details.justification.auxiliary_points` kèm thuyết minh `justification_text` đầy đủ (*"Trong mặt (ABCD), gọi I là giao điểm của AB và đường thẳng CD..."*).
   - Tuy nhiên việc vẽ chấm điểm 3D riêng cho `auxiliary_points` trên canvas Three.js vẫn thuộc **FE-4 (`BLOCKED_OWNERSHIP`)** do phần `Scene3D` frontend đang do phiên làm việc khác sở hữu trên worktree `axo-geometry-library`. Học sinh vẫn đọc được đầy đủ lý do hình học chính xác trên giao diện bước dựng.
