# M17 Wave 2B-PATCH2 — Stage-Preserving Spec Generation (offline)

Đóng hai nguyên nhân gốc còn lại sau live W2B-PATCH (`f2b28e2`, strict 1/3).
**Offline XONG; LIVE CHƯA CHẠY LẠI — dừng chờ duyệt ngân sách (§L).**
Không mở Wave 2C. Không ghi đè artifact live cũ (`0afcb37`, `f2b28e2`).

## 0. Trạng thái

| Gate | Trước PATCH2 (`8bd2324`) | Sau PATCH2 |
|---|---|---|
| pytest | 996 | **1044** (2 skip, 1 deselect) |
| vitest | 596 / 46 | **596 / 46** (FE không đổi) |
| build · conformance | sạch · 20/0 | **sạch · 20/0** |
| `CACHE_VERSION` | 20 | **21** |
| `config_contract_version` (bảng) | table-1.1 | **table-1.1** (không đổi) |
| `HISTORY_SCHEMA_VERSION` | 2 | **2** (không đổi) |

## 1. §A — Quyết định sản phẩm

Target `database.relational_table_query` đã KHAI hỗ trợ `filter → projection →
sort → limit → aggregate`. Do đó một request hợp lệ trong hợp đồng **phải có
đường sinh candidate spec đủ tầng, kiểm chứng được**. Cổng completeness
fail-closed vẫn là chốt cuối, **nhưng không được dùng nó thay cho khả năng tạo
spec hợp lệ** — đó chính là chỗ live P2 thất bại (đề 5 tầng hợp lệ bị từ chối).

## 2. P2/L4 — Manifest tầng tất định + merge (§B/§C/§D)

`app/simulation/table_pipeline_manifest.py`:

- **`build_required_pipeline(analysis)`** — từ `requested_requirements` CÓ CẤU
  TRÚC (KHÔNG narration) dựng `RequiredTablePipeline`: các tầng theo thứ tự
  authoritative + tham số canonical (không gian nhãn) + cờ `grounded`/
  `unresolved_fields` + `order_version`. **Không chứa** dòng cuối / giá trị tổng
  hợp / phán quyết giữ-loại / trạng thái tích luỹ.
- **`manifest_prompt_hint`** — nhồi manifest máy-đọc vào prompt simulate để LLM
  điền đúng ngay lượt đầu.
- **`merge_required_stages(config, pipeline)`** — sau khi LLM sinh + validate:
  tầng grounded THIẾU → **chèn** từ manifest; tham số LỆCH → **sửa** về manifest
  (ghi `corrected_stages` from→to); khớp → **xác nhận**; cột không có trong
  schema hoặc tầng chưa đủ tham số → **unresolved, KHÔNG bịa**. Rồi RE-VALIDATE
  bản merge. LLM **không còn là nguồn duy nhất** quyết định tầng tồn tại.

Kết quả (production `run_pipeline`, offline): candidate 3 tầng của live P2 →
merge → 5 tầng → An/Dũng/Lan · AVG **8.5** · counted **3**, **một** lượt
simulate, 0 rò rỉ kết quả.

**§E fail-closed GIỮ NGUYÊN:** analyze thiếu tham số tầng (vd limit không số),
hoặc manifest nêu cột schema không có → merge không bù → completeness từ chối.

## 3. Lỗ đo observer — sự thật bị che ở live P2

Artifact live báo `requested_requirements=null`, khiến tưởng analyze không phát
yêu cầu. **Sai:** event `analyze_done` chỉ lưu `result_ownership`/
`prescribed_procedure`, KHÔNG lưu `requested_requirements` — nhưng analyze THẬT
có điền (thông điệp retry của P2 liệt kê đủ 5 tầng "filter, projection, sort,
limit, aggregate" và "THIẾU: limit, aggregate", chỉ tính được từ
`requested_requirements`). Observer nay lưu `requested_operations/requirements`
+ candidate spec mỗi lượt (thụ động, bất biến #22). Ba failed candidate của §H
được **tái dựng trung thành** từ bằng chứng đã ghi (đã nói rõ trong test).

## 4. P1/L3 — Tương đương ngữ nghĩa hẹp (§F/§G)

`app/evaluation/table_plan_equivalence.py` — **lớp ĐÁNH GIÁ, không đổi
production**. Coi `aggregate null-ignore` ⇔ `filter(cột agg IS NOT NULL) +
aggregate` chỉ khi ĐỒNG THỜI: tầng thừa duy nhất là non-null check trên **chính
cột tổng hợp**, không predicate khác, không projection/sort/limit thừa, mục tiêu
vô hướng, hàm bỏ qua null, giá trị + counted khớp. **KHÔNG** phải tolerance chung
cho operation bị thêm — 8 ca âm khoá: filter cột khác, filter ngưỡng, COUNT(\*),
+limit, +projection, cần trả rows, hai predicate, khác cột agg.

`final_result_accepted` ghép quy tắc này với đối chiếu giá trị+counted và ghi
bằng chứng máy-đọc (raw/represented plan, structural diff, rule, decision).

## 5. §I — Runner stop-check

`supported_stop_reason`: với supported case, **mọi status ≠ "ok"** (error /
unsupported / semantic_incomplete / insufficient / None) đều là lỗi và dừng — vá
lỗ hổng cũ chỉ bắt `"error"` khiến P2 (trả `"unsupported"`) lọt qua tới P4.

## 6. §J — Cache / history

- `CACHE_VERSION` **20→21**: prompt sinh spec nay mang manifest → đầu vào sinh
  đổi → cache cũ MISS, sinh lại dưới cơ chế merge.
- `config_contract_version` GIỮ **table-1.1**, `HISTORY_SCHEMA_VERSION` GIỮ **2**:
  shape envelope LƯU không đổi (merge là việc lúc SINH, không thêm trường lưu) →
  mở lại từ lịch sử (bất biến #17) vẫn hợp lệ.
- Merge KHÓA vào đúng `database.relational_table_query` (guard `simulation_id` +
  `build_required_pipeline` trả None cho target khác) → selector/recovery/generic/
  pattern-reuse **bất biến** (full suite chứng minh).

## 7. Test (§G/§H bắt buộc)

- `test_table_pipeline_manifest.py` (19) — §B manifest đủ tầng/không kết quả +
  §H merge 3→5 tầng, AVG 8.5/3, + 5 fault (xoá limit/aggregate, sai limit, sai
  func, thứ tự canonical) + không-grounded/cột-lạ không bịa.
- `test_table_manifest_pipeline.py` (6) — merge qua production `run_pipeline`;
  hint vào prompt; §E fail-closed khi thiếu evidence.
- `test_table_plan_equivalence.py` (13) — §G 4 ca dương + 8 ca âm + bằng chứng.
- `test_table_live_policy.py` (11) — §F chấp nhận kết quả + §I dừng.
- `test_table_pipeline_completeness.py` — cập nhật sang hợp đồng PATCH2 (thiếu/
  sai tầng grounded → merge; ungroundable → vẫn fail-closed).

## 8. LIVE — chưa chạy (§L)

Runner `scripts/live_table_query_patch.py` đã cập nhật (§F equivalence + §I
stop-check + wants_rows; offline `--lock`/`--selftest` PASS). **Chưa chạy live.**
Đề xuất giữ nguyên 4 case / ≤14 HTTP; trước live phải: commit, rebuild container
kèm danh tính, runtime doctor PASS ở HEAD mới (cache **21**).
