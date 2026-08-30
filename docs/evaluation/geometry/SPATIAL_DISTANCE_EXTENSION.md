# CAPABILITY EXTENSION 01 — CẦU NỐI KHOẢNG CÁCH KHÔNG GIAN

> **Wave đóng 2026-08-30.** Ba cặp toán hạng `distance` mở thêm: đường–đường ·
> đường–mặt · mặt–mặt. Bằng chứng chạy được ở §5.

---

## 1. Vấn đề, nói bằng bằng chứng chứ không bằng tên hàm

`measure.distance_sq_skew_lines` và `distance_sq_parallel_lines` nằm trong kho
**từ đầu**. `hp_b01_032` vẫn chết **hai lượt liền** ở Phase 7B / V3 với đúng câu
*"cặp đối tượng không hợp lệ cho khoảng cách"*.

Kernel có phép tính mà cầu nối IR không nối ⇒ **năng lực ấy không tồn tại với
hệ**. Đó là lý do `audit_geometry_capability.py` gọi thẳng `geometry_exec._do`
chứ không hỏi *"kernel có hàm ấy không"*.

## 2. Đã sửa ở đâu — bốn tầng, không tầng nào tính lại toán

| Tầng | File | Việc |
|---|---|---|
| kernel | `geometry/measure.py` | `distance_sq_lines` · `distance_sq_line_plane` · `distance_sq_planes` — **hỏi `predicates` rồi uỷ cho hàm cũ**, không có công thức mới |
| cầu nối | `semantic_program/geometry_exec.py` | bốn nhánh `isinstance`; `distance` nay nhận **9** cặp |
| thẩm định | `semantic_program/ir_static_check.py` | `_KIEU_DO["distance"]` chặn cặp khối/thiết diện **TRƯỚC kernel**, để mô hình còn lượt sửa |
| kiểm chứng | `semantic_program/geometry_obligations.py` | C₂ **tự tính lại** ba cặp mới, không tin giá trị chương trình khai |

Ba trường hợp suy biến trả `0` chứ không ném, vì cả ba có kết luận hình học
đúng: hai đường **cắt** · đường **nằm trong** mặt · hai mặt **trùng**.
`distance_sq_lines` tự phân nhánh nên tầng gọi không phải kết luận quan hệ
trước khi đo — đó là lý do ba hàm này ở kernel chứ không ở cầu nối.

## 3. Cái KHÔNG mở, và vì sao

**Miền số không đổi.** Nền là `Fraction`; kết quả vô tỉ vẫn
`GEOMETRY_IRRATIONAL_RESULT`. Đo lại chính bộ đo:

```
✅ khoảng cách đường–đường CHÉO (hữu tỉ)   2
❌ khoảng cách đường–đường CHÉO (VÔ TỈ)    GEOMETRY_IRRATIONAL_RESULT
✅ khoảng cách đường–đường SONG SONG       1
✅ khoảng cách đường–mặt (∥)               1
✅ khoảng cách mặt–mặt (∥)                 1
```

⇒ Ba ô trong ma trận phủ lên **PARTIAL**, **KHÔNG** lên SUPPORTED. Đề thi thật
rất hay cho đáp án `a√3/2`, `a√6/3`; "nối được ba cặp" **không** đồng nghĩa với
"làm được các bài khoảng cách trong SGK". Muốn thế phải làm **căn thức chính
xác** — một wave riêng.

**`DISTANCE_VISUAL_WITNESS = NONE.`** Kernel không có chân đường vuông góc
chung của hai đường chéo nhau, và luật cấm suy witness ở renderer. Vẽ một đoạn
"nhìn cho giống" là đúng thứ R0 tồn tại để ngăn.

## 4. Ma trận phủ — số cũ và số mới, cả hai

| | trước | sau |
|---|---|---|
| cầu nối IR đi trọn tới một số | 15/22 | **19/23** |
| chủ đề SUPPORTED | 12/23 | 12/24 |
| PARTIAL | 3 | **6** |
| UNSUPPORTED | 7 | **5** |
| DEFERRED | 1 | 1 |

Chi tiết: `docs/geometry/CAPABILITY_GAP_AUDIT.md` §1 · §4b.

## 5. Bằng chứng chạy được

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q          # 3473 passed, 18 skipped
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q tests/geometry/test_spatial_distance.py   # 36 passed
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/audit_geometry_capability.py
cd frontend && npx vitest run && npm run build                                      # 1745 passed · tsc + build OK
```

`test_spatial_distance.py` (36) gồm: A–C đường×đường · D–F đường×mặt ·
G–I mặt×mặt · J–L thẩm định tĩnh · M–P **fail-closed khi vô tỉ**, cộng một lượt
quét mã nguồn cấm `float(` / `math.sqrt` / `** 0.5` / `round(` trong đường này,
và `test_C2_chuong_trinh_khai_SAI_thi_bi_bat` — C₂ phải bắt được chương trình
khai sai giá trị.

## 6. §11 LIVE SANITY — chạy 1/3 bài, do người dùng duyệt

Tập DEV có 10 bài và **không có ca nào** cho ba cặp này, nên §11 không chạy
được trên vật liệu DEV sẵn có. Ba đề **thăm dò** soạn riêng, để **ngoài**
`dev/cases.json` (gộp vào là đổi hash DEV đang đóng băng):
`docs/evaluation/geometry/probe-spatial-distance/cases.json`.

Kiểm tất định trước, 0 API call: kernel ra đúng `4 · 2 · 3`, khớp `oracle_result`
tính tay ⇒ bài thăm dò **thắng được**, hỏng ở lượt live là hỏng ở mô hình.

Người dùng duyệt chi **1 bài**, không phải 3:

```
probe_dist_01 · k=1 · G1 1/1 · G2 1/1 · A 1/1 · O 1/1 · obligation khớp 1/1
3/6 lượt logic · 3/8 HTTP · 18778 token · ~$0.0311 · 51.4s
```

Mô hình dựng `line_AB`, `line_CC_prime` rồi phát
`measure distance of=line_AB wrt=line_CC_prime` — đúng cặp `Line3×Line3` mới mở;
oracle độc lập chấm PASS, không lệch.

⚠️ **n = 1.** Không phải accuracy rate, không phải số DEV, không so được với bất
kỳ baseline nào. Hai cặp còn lại (**đường–mặt**, **mặt–mặt**) hiện **chỉ có bằng
chứng tất định** — chưa có lượt live nào chạm tới chúng.
Artifact: `probe-spatial-distance/live-k1/geometry_dev_results.json`.
