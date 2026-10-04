# MIGRATION PLAN + DANH SÁCH MODULE CẦN CÓ

> **Chưa code.** Tài liệu để review. Mỗi bước ghi rõ: đụng gì · cổng qua · cắt
> được không.

---

## 0. Nguyên tắc thứ tự

Bốn bước đầu **không đảo được** — mỗi bước tiêu thụ đầu ra của bước trước. Từ
bước 5 trở đi mới song song được.

Và một luật vận hành rút từ sáu tháng vừa rồi: **đóng băng mã trước mỗi lượt
đo, khai mọi sai lệch tại chỗ** (`RUN2_PROTOCOL §7b`). Riêng giai đoạn dựng
kernel thì chưa cần — chưa có gì để đo.

---

## Bước 1 — Chốt phạm vi *(0 dòng mã)*

- Ghi ba lớp bài vào `STATUS_LEDGER`; ghi danh sách **ngoài phạm vi**.
- **Trả lời câu chặn**: nhánh LLM còn trong đề không? Chưa có đáp án thì
  **dừng ở đây** — bước 3 trở đi phụ thuộc trực tiếp.
- Đổi tên hệ (`AlgoSim` nay sai miền).

## Bước 2 — Geometry kernel + oracle ⚠️ **ĐƯỜNG GĂNG**

**Hai bản cài ĐỘC LẬP cho cùng bài toán.** Đó là toàn bộ nguồn tính độc lập:
kernel dùng trong sản phẩm; oracle của custodian viết **riêng, Python thuần,
không import kernel** — đúng khuôn `sealed_ground_truth.py` hiện tại.

Nội dung kernel: giao tuyến mp–mp · giao điểm đt–mp · đồng phẳng · hình chiếu
vuông góc · khoảng cách điểm–mp · thể tích khối đa diện · dựng thiết diện.

⚠️ **Bẫy phải xử lý ngay từ dòng đầu**: so sánh dấu phẩy động. `==` trên float
là nguồn sai **lặng lẽ** kinh điển ở hình học — hai mặt phẳng "song song" hoá ra
cắt nhau ở vô cực. Chọn **hữu tỉ chính xác** hoặc **dung sai tường minh có tên**,
quyết một lần, ghi vào docstring.

**Cổng qua**: cùng input = cùng output (test tất định) · oracle khớp kernel trên
một bộ bài **kiểm tay** — không lấy đầu ra của kernel làm đáp án, nếu không
`EXPECTED_RESULT` thành tautology (bẫy đã gặp ở `cross_domain_matrix`).

## Bước 3 — Mở IR *(bump `CACHE_VERSION` 3 chỗ)*

| Thêm | Số |
|---|---|
| `MemoryType`: `point3` `vector3` `line3` `plane3` `polygon3` `solid` | 6 |
| Biểu thức: `intersect_line_plane` `intersect_plane_plane` `midpoint` `project_onto` `cross_dot` | 5 |
| Câu lệnh dựng: `construct_point` `construct_line` `construct_section` | 3 |
| Nghĩa vụ: `incidence` `parallel` `perpendicular` `coplanar` `distance_value` `volume_value` `section_shape` | 7 |

Sửa `contract.py` ⇒ chạy `export_semantic_program_schema.py` (**ghi HAI bản**) ·
`grammar_card` tự dẫn xuất · bump `CACHE_VERSION` ở `main.py` + assert
`test_api.py` + bảng `CURRENT_STATE.md`.

⚠️ **Camera và Transformation KHÔNG vào IR.** Renderer sở hữu camera
(`ARCHITECTURE_MAP §3`). Đưa camera vào IR là để LLM chỉnh góc nhìn — mở đường
cho *"hoạt hình đẹp mà state sai"*.

## Bước 4 — Renderer 3D + picking

Camera orbit/zoom/pan + 4 view đặt sẵn · **nét đứt cạnh khuất** (quy ước vẽ hình
không gian, **không** phải trang trí) · nhãn đỉnh bám 3D · tô thiết diện bán
trong suốt · raycast chọn điểm/cạnh/mặt · **2D↔3D song song** (hình biểu diễn
phẳng cạnh khối thật).

**Cổng qua**: 4 bề rộng · `--faultcheck` phải ĐỎ · renderer **không** tính lại
toạ độ nào.

## Bước 5 — Timeline dựng hình

Mỗi bước dựng = một `trace step` = một `VisualFrame`. Song ánh #31 giữ nguyên.
Gộp bước thuộc `pacer`, **không** thuộc adapter.

**Cổng qua**: narration khớp state ở **mọi** bước (đây chính là bug đã sinh ra
bất biến #31).

## Bước 6 — Tương tác

| Loại | Đường đi | Ghi chú |
|---|---|---|
| Xoay / zoom / pan | **chỉ camera** | không chạm state ⇒ sạch, làm trước |
| Chọn đối tượng | raycast → highlight | `highlight_indices` đã có sẵn |
| **Kéo có ràng buộc** | `USER → controller → CHIẾU VỀ MIỀN HỢP LỆ → kernel → state mới → render` | dựng lại **trọn** timeline sau khi thả |

⚠️ Kéo được đổi **ĐẦU VÀO**, không được đổi **TRACE** trực tiếp. Cập nhật theo
từng pixel là phá song ánh #31 — dùng *thả* làm mốc tính lại.

**Cổng qua**: mọi thay đổi đi qua `module.apply` · fault test: kéo vượt ràng
buộc phải bị **chiếu lại**, không được nhận · renderer sửa toạ độ phải ĐỎ.

## Bước 7 — Đánh giá

Corpus bài hình học Toán 11–12 · custodian chọn theo seed GVHD · SEALED mới.
**Quy trình giữ nguyên**: `RELIABILITY_EVALUATION_PLAN` (7 tầng, 8 lớp thất bại,
luật mẫu nhỏ) áp thẳng, chỉ đổi nội dung.

---

## DANH SÁCH MODULE CẦN CÓ

### Backend — mới

| Module | Trách nhiệm |
|---|---|
| `simulation/geometry/kernel.py` | phép dựng tất định. **Không** biết gì về LLM |
| `simulation/geometry/predicates.py` | thuộc · song song · vuông góc · đồng phẳng — **một chỗ** quyết dung sai |
| `simulation/geometry/measure.py` | khoảng cách · góc · thể tích |
| `simulation/geometry/section.py` | dựng thiết diện (thuật toán riêng, đủ lớn để tách) |
| `semantic_program/geometry_obligations.py` | 7 checker nghĩa vụ |

### Backend — sửa

`semantic_program/contract.py` (6+5+3) · `interpreter.py` (nhánh dựng,
**giữ fail-closed**) · `visual_adapter.py` (4 primitive) · `analyze_contract.py`
(hợp đồng hình học) · `ai/skills/*.md` (viết lại) · `simulation/catalog.py`
(một `SimSpec` hình học thay 24 cái)

### Frontend — mới

| Module | Trách nhiệm |
|---|---|
| `domains/geometry/scene3d.tsx` | dựng cảnh Three.js từ frame |
| `domains/geometry/camera.ts` | orbit/zoom/pan + 4 view đặt sẵn |
| `domains/geometry/picking.ts` | raycast → id đối tượng |
| `domains/geometry/drag-constraint.ts` | **chiếu về miền hợp lệ** trước khi gọi apply |
| `domains/geometry/hidden-edges.ts` | nét đứt cạnh khuất |
| `domains/geometry/layers.tsx` | bật/tắt điểm · cạnh · mặt · đường phụ · chú thích |

### Frontend — sửa

`domains/semantic/` (Workspace → cảnh 3D) · `data/` (bài mẫu hình học) ·
`simulations/index.ts` (đăng ký domain mới)

### Harness — **giữ nguyên, không sửa**

`run_sealed_evaluation` · `replay_harness` · `reliability_v2` ·
`merge_render_v` · `freeze_evaluation_candidate` · `custodian/*`

---

## Cái BỎ, và bỏ thế nào

**Không xoá.** Chuyển 24 module Tin học sang trạng thái **đóng băng, không phát
triển tiếp**, và **kể chúng trong luận văn** như bằng chứng *khung chạy được
trên nhiều miền* — `cross_domain_matrix` đã có sẵn để nói điều đó.

Xoá là vứt mất lập luận mạnh nhất của phương án 3 (`AUDIT §6`): hệ là một
**khung**, hình học là **miền chứng minh**, và có sẵn một miền thứ hai đã chạy
để chứng minh nó là khung thật.

---

## Trước khi code — ba thứ phải xong

1. **Câu chặn về LLM** đã có đáp án của GVHD.
2. **Bốn tài liệu này được review** — đúng yêu cầu *"chỉ sau khi review mới
   triển khai code"*.
3. **Quyết dung sai số học** (hữu tỉ chính xác hay epsilon có tên) — quyết sau
   khi đã viết kernel là phải sửa lại toàn bộ.
