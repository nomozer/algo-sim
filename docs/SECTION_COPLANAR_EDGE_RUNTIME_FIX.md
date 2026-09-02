# SECTION_COPLANAR_EDGE_RUNTIME_FIX — đóng G3

> Thực hiện **2026-09-02**. **0 lượt gọi model.** Sửa TÍNH ĐÚNG của một năng
> lực đã có; không thêm primitive, không đổi lược đồ model-facing, không một
> nhánh nào theo họ hình.

---

## 1. Nguyên nhân gốc — là ĐẾM TRÙNG, không phải hình học

`cross_section` đi theo MẶT: mỗi mặt của khối cho một đoạn giao, rồi các đoạn
được nối thành chu trình. Thuật toán ấy đúng, và nó vẫn nguyên vẹn.

Chỗ vỡ nằm ở một điều hiển nhiên mà không ai viết ra: **một cạnh nằm trọn trong
mặt phẳng cắt thuộc về HAI mặt kề**, nên cả hai mặt cùng báo **đúng một đoạn**.

Thiết diện `(SAC)` của hình chóp `S.ABCD`:

| mặt | đoạn báo về |
|---|---|
| đáy `ABCD` | `A–C` ← dây cung thật |
| `SAB` | `A–S` ← **cạnh `SA`, nằm trong mặt phẳng** |
| `SBC` | `C–S` ← **cạnh `SC`** |
| `SCD` | `C–S` ← **bản sao** |
| `SDA` | `A–S` ← **bản sao** |

Năm đoạn cho một tam giác ba cạnh. Vòng nối tiêu thụ `A→C→S→A`, còn thừa hai bản
sao, không nối tiếp được, và ném:

```
MALFORMED_SOLID: không nối được thiết diện thành đa giác kín
                 — khối có thể KHÔNG LỒI, hoặc bảng mặt khai thiếu
```

Bảng mặt hoàn toàn đúng. Khối hoàn toàn lồi.

**Vì sao điều kiện là CẠNH chứ không phải ĐỈNH.** Ba đỉnh cùng nằm trên mặt
phẳng mà không cặp nào kề nhau (`A`, `C`, `B′` của hình lập phương) thì không
sinh bản sao nào, và lượt dựng chạy đúng từ trước tới nay. Tên cũ
`SECTION_VERTEX_INTERSECTION_GAP` mô tả sai đúng chỗ quan trọng nhất.

---

## 2. Bản sửa

### 2.1 Khử trùng theo cặp đầu mút chính xác

```python
khoa = frozenset(c)          # `Point3` là frozen dataclass trên `Fraction`
if khoa in da_gap: continue
```

Không khử bằng chuỗi định dạng, không khử bằng toạ độ làm tròn. `frozenset` cho
đúng quan hệ **bằng hình học**, trong miền số chính xác đang dùng.

**Vì sao an toàn:** hai mặt phân biệt của một đa diện lồi chung nhau nhiều nhất
một cạnh, nên hai mặt cho cùng một đoạn ⇔ đoạn ấy là cạnh chung của chúng. Khử
trùng vì thế **không thể** xoá mất một cạnh thật của thiết diện.

**Vì sao không mất trường hợp đúng nào:** bản sao luôn dẫn tới lỗi, chưa bao giờ
dẫn tới một đa giác kín-nhưng-sai. Vòng nối chỉ khép khi `dinh[-1] == dinh[0]`
và `con_lai` rỗng; còn bản sao thì hoặc vấp `for…else`, hoặc đi thêm rồi kết
thúc ở một đỉnh khác đỉnh đầu. Bằng chứng vận hành: `geometry-samples.json` sinh
lại **byte-đối-byte y hệt**.

### 2.2 Mặt phẳng trùng một mặt của khối

Trước: `CONTAINED_INFINITE_INTERSECTION` — mã ấy đúng cho **giao của hai mặt
phẳng** (vô hạn) và sai ở đây: giao của một *khối* với một mặt phẳng bị chặn bởi
khối, nên hữu hạn.

Nay: thiết diện **chính là mặt ấy**, với `steps` là các cạnh của nó. Đề *"thiết
diện của hình chóp cắt bởi mp(ABCD)"* có một câu trả lời mà học sinh biết.

Thử bằng mệnh đề chính xác *"mọi đỉnh của mặt này có `signed_eval == 0`"*, chạy
**trước** vòng gom đoạn — không đếm điểm giao, vì đếm điểm lẫn với ca một mặt
suy biến, và hai ca ấy cần hai câu trả lời khác nhau.

### 2.3 Ba mã lỗi, ba nghĩa

| mã | nghĩa | ai sai |
|---|---|---|
| `MALFORMED_SOLID` | khối khai sai: mặt < 3 đỉnh, chỉ số ngoài biên, mặt suy biến | **dữ liệu vào** |
| `SECTION_INTERSECTION_DEGENERATE` *(mới)* | giao có tồn tại nhưng ở chiều thấp hơn — không có đa giác để dựng | **mặt phẳng người dùng chọn** |
| `SECTION_CONSTRUCTION_INTERNAL_FAILURE` *(mới)* | gom đủ đoạn mà không nối được chu trình | **chính phép dựng** |

Ba ca chạm đã có tên (`PLANE_DOES_NOT_CUT`, `PLANE_TOUCHES_VERTEX`,
`PLANE_TOUCHES_EDGE`) giữ nguyên — chúng vốn đã chẩn đoán đúng.

Mọi thông điệp trên đường suy biến nay **không nhắc tới bảng mặt**: tới được đó
nghĩa là khối đã qua `Polyhedron.__post_init__`, tức bảng mặt hợp lệ về cấu
trúc. `test_E_loi_chieu_thap_KHONG_do_toi_bang_mat` khoá điều ấy.

---

## 3. Một khẳng định cũ của tôi, SAI, nay sửa

`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT §18` và mục backlog kèm theo viết
rằng thông điệp sai khiến *"vòng sửa ≤3 lượt tiêu quota vào chỗ không có lỗi"*.

**Không đúng.** Đọc lại đường mã: vòng sửa của `stage_semantic_program`
(`ai/pipeline.py:365`) đóng ở tầng **TĨNH** — `ir_static_check` rồi
`grounding_gate` — và trả `spec`; interpreter chạy ở `ai/pipeline.py:504`,
**sau** và **ngoài** vòng ấy. Một `GeometryError` vì thế là lỗi **cuối**, không
bao giờ tới prompt sửa. `CODE_INDEX` đã ghi đúng điều này từ trước (*"vòng sửa
của `stage_semantic_program` đã đóng trước đó"*); lượt soát suy ra hệ quả mà
không tra đường mã.

Cái giá thật của thông điệp sai: **một chẩn đoán sai gửi tới người đọc và ghi
vào artifact đánh giá**. Đáng sửa, và không tốn token nào.

---

## 4. Ma trận nghiệm thu

`tests/geometry/test_section_coplanar_edge.py` — 19 ca. Ca đầu tiên
(`test_do_luong_TO_PO_dung_nhu_da_khai`) kiểm **luận cứ** của mọi ca sau: nếu
phép đếm cạnh đồng phẳng sai thì các ca còn lại nói về một thứ khác mà vẫn xanh.

| | ca | trước | sau |
|---|---|---|---|
| T1 | đỉnh trên mặt phẳng, **0** cạnh đồng phẳng | PASS | PASS |
| T2 | **1** cạnh đồng phẳng + cắt ruột (2 cấu hình) | FAIL | PASS |
| T3 | **≥2** cạnh đồng phẳng — (SAC), (SBD), ACC′A′ | FAIL | PASS |
| T4 | mặt phẳng trùng một mặt | FAIL | PASS — cho ra chính mặt ấy |
| T5 | chạm đúng một đỉnh | `PLANE_TOUCHES_VERTEX` | giữ nguyên |
| T6 | chạm đúng một cạnh | `PLANE_TOUCHES_EDGE` | giữ nguyên |
| T7 | khối hỏng thật | `MALFORMED_SOLID` | giữ nguyên |
| T8 | **bát diện đều** — không helper họ hình nào dựng nó | FAIL | PASS |
| T9 | hoán vị bảng mặt ⇒ cùng một chu trình chuẩn hoá | — | PASS |
| T10 | mọi toạ độ là `Fraction`, không float | — | PASS |

Thêm: `test_J_*` đi hết chuỗi IR → runtime → trace → Scene3D, và
`test_J_checker_*` xác nhận `section_matches` chấp nhận thiết diện có đỉnh sinh
từ cạnh đồng phẳng (nó dựng lại rồi so `canonical_cycle`, không có nhánh riêng).

Ba ví dụ `(SAC)` · `(SBD)` · `ACC′A′` là **ví dụ nghiệm thu**, không phải nhánh
cài đặt: ca khẳng định theo *số cạnh đồng phẳng ≥ 2*, và `grep` cho `chop|prism|
cube|tetrahedron` trên `backend/app/**` vẫn chỉ trả về helper tổng quát và
fixture test.

---

## 5. Một hồi quy của wave trước, do lượt đo này bắt được

Trình duyệt hiện ô soi thiết diện là **`"Điểm AĐiểm CĐiểm S"`**.

Sau khi G1 tách `label` (câu đọc được) khỏi `notation` (ký hiệu), bốn chỗ ở
`scene3d-subentities.ts` vẫn **ghép `label`** để dựng một ký hiệu: nhãn chu
trình thiết diện, tên đỉnh thiết diện, tên cạnh thiết diện, và nhãn mặt của
khối. Chúng nay ghép `notation`.

Không có lượt đo trình duyệt thì hồi quy này im lặng: vitest xanh vì fixture của
nó viết trước khi `notation` tồn tại. Fixture `scene3d-section-fixture.json` đã
sinh lại từ đúng chương trình đã sinh ra nó.

---

## 6. Phiên bản và cache

**`CACHE_VERSION` giữ nguyên 61.** Không bump, và đây là lý do chứ không phải
sự lười:

- cache **chỉ giữ envelope THÀNH CÔNG** (`main.py`: *"CHỈ cache kết quả THÀNH
  CÔNG… chống stale"*);
- các ca wave này mở khoá trước đây **thất bại**, nên chưa bao giờ được cache;
- không envelope thành công nào đổi nội dung — chứng minh vận hành:
  `build_geometry_samples.py` sinh lại `geometry-samples.json` **không một byte
  khác** trước khi thêm bài mẫu mới.

**`stable_capability_hash()` giữ nguyên.** Nó băm `_CHU_KY`, `_KIEU_DUNG`,
`_TOAN_HANG_LENH`, `_KIEU_DO`, `MemoryType`, `GEOMETRY_CHECKERS` — không bảng
nào đổi. Đúng: `construct_section` vốn đã là năng lực đã khai; wave này sửa
tính đúng của nó, không thêm năng lực.

---

## 7. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2798 passed**, 1 skipped (+19 ca mới) |
| `vitest` | **668 passed** (48 tệp) |
| `npm run build` | PASS |
| `replay_demo_cases.py` | **5/5**, chuỗi rút gọn **1/1** |
| `audit_demo_crash_surface.py` | biên **6/6**, ném ra ngoài **0** |
| `certify-section-coplanar-edge.mjs` | **7/7**, 0 lỗi bảng điều khiển |
| `certify-display-metadata.mjs` | **4/4** |
| `certify-journey-integration.mjs` | **13/13** |
| `certify-offline-journey.mjs` | **11/11** |
| `certify-refusal-surface.mjs` | **21/21** |

Bài mẫu offline mới **`mat-cheo-sac`** — thiết diện theo mặt phẳng (SAC). Nó ở
**thư viện**, không ở bộ gợi ý trang chủ: bộ gợi ý cố ý nhỏ và phủ ba loại hoạt
động chứ không phủ mọi bài.
