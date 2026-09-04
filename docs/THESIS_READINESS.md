# THESIS_READINESS — tuyên bố ↔ bằng chứng ↔ giới hạn

> Chốt phạm vi 2026-09-01 (`THESIS_SCOPE_FREEZE_AND_DEMO_READINESS`).
> **Benchmark ĐÓNG.** Không đo thêm, không mở năng lực mới, 0 lượt gọi model.
> Đây là **bảng đối chiếu duy nhất** cho khoá luận — mọi số sống trỏ về
> artifact nêu tên; không chép số vào đây lần thứ hai.

## 0. Trạng thái đóng băng

| tuyến | trạng thái |
|---|---|
| `SYNTHESIS_BENCHMARKING` | **CLOSED** |
| `TRANSLATION_EVIDENCE` | **CLOSED** |
| `NAME_ONLY_EVIDENCE` | **CLOSED** |
| `ANALYZE_STABILITY` | **NOT_MEASURED_BY_SCOPE_DECISION** |

`ANALYZE_STABILITY` không đo **vì quyết định phạm vi**, không phải vì thiếu
điều kiện: đề tài không nghiên cứu độ ổn định thống kê của trích xuất thông
tin. Điều kiện kỹ thuật cũng chưa có (artifact không lưu đầu vào analyze — xem
`docs/evaluation/geometry/analyze-fact-stability/PREFLIGHT_STOP.md`), nhưng **lý do dừng là phạm vi**.

## 1. Bảng chính

| tuyên bố | bằng chứng | giới hạn | trạng thái |
|---|---|---|---|
| LLM tổng hợp Semantic Program cho bài **chưa từng thấy** | `clean-baseline-v2` 6/6 · `translation-probe` 4/4 trong ngân sách · `name-contract-probe` 2/4 một lượt | mẫu nhỏ (n = 4–6 mỗi lượt), không phải ước lượng tổng thể | **SUPPORTED** |
| Engine tất định thực thi, **chính xác tuyệt đối** (hữu tỉ + căn) | `replay_demo_cases.py` 5/5 · suite hình học · `geometry_oracle.py` cài ĐỘC LẬP với kernel | chỉ trong phạm vi IR đã thi hành; khối **lồi**. Mặt cong (cầu · trụ · nón) nay CÓ nền tất định (`geometry/curved.py`, 2026-09-03) — nhưng **sản phẩm** vẫn `foundation_only` | **SUPPORTED** |
| **Bài mới ≠ mã mới** — không nhánh theo dạng bài | runtime đóng băng qua 4 wave đề mới · `PROBLEM_FAMILY_SPECIAL_CASES = 0` (quét AST mã sản phẩm) | chỉ đúng **trong IR hiện có**; bài ngoài IR bị từ chối chứ không tự mở rộng | **SUPPORTED** |
| Cảnh 3D + dòng thời gian **dẫn xuất** từ trạng thái tất định | `replay_demo_cases.py`: `producer`/`depends` có mặt trên mọi vật dựng · bất biến #31 `frame k ⇔ trace[k]` | renderer chỉ ĐỌC state; không có đường ngược | **SUPPORTED** |
| Học sinh **truy ngược được** quan hệ nhân quả bằng thao tác chọn | `test_dependency_visibility.py` (14) + `scene3d-causal-selection.test.ts` (11) trên artifact THẬT `probe-contract-waves-2`: chọn `R` → bao đóng 10 vật, khớp bao đóng dựng ĐỘC LẬP từ `events` | ⚠️ đúng từ 2026-09-04 (`GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE`). TRƯỚC đó `dependency_graph` lọc cạnh qua `memory_declarations` nên mọi cạnh trỏ tới vật DẪN XUẤT bị mất — chọn `R` trả về **rỗng**. Chỉ *chọn* hỏng; *tua* vẫn đúng | **SUPPORTED** |
| Ranh giới **R0** giữ được dưới áp lực tổng hợp thật | `NAME_ONLY_CONTRACT_LIVE_PROBE`: 42/42 ô toán hạng là TÊN ở bản THÔ · `RAW_GEOMETRY_LITERAL_ATTEMPTS = 0` | n = 4, k = 1 | **SUPPORTED** |
| Hệ **từ chối có địa chỉ** thay vì chết câm | `audit_demo_crash_surface.py` 6/6 biên, **0 đường ném** · ca demo `n4` bị chặn đúng ở grounding | sáu biên đã biết, không phải fuzzing toàn diện | **SUPPORTED** |
| `analyze` trích **đủ** dữ kiện đề cho | `n1` 3 fact toạ độ, `n2` 4 · **`n3`/`n4` không fact toạ độ nào** | quan sát trên 4 đề, **chưa đo lặp lại** | **PARTIAL** |
| Phủ chương trình hình học THPT | `GEOMETRY_CURRICULUM_COVERAGE.md` | phủ **một phần**, có chủ đích | **PARTIAL** |
| Tác động lên người học | — | **chưa đánh giá** | **OPEN / NGOÀI PHẠM VI** |

## 2. `ANALYZE_SOURCE_FACT_COMPLETENESS = PARTIAL`

Bằng chứng hiện có, nguyên văn: `n1`/`n2` có dữ kiện toạ độ trong
`RequestContract`; `n3`/`n4` **không có**, trên bốn đề nêu toạ độ cùng một kiểu
(`Oxyz`, dạng `A(0; 0; 0)`).

**Không tuyên bố** đây là ngẫu nhiên, hệ thống, ổn định hay bất ổn — bốn chữ ấy
đều đòi một phép đo lặp lại chưa được thực hiện. Ghi đúng thứ quan sát được và
dừng ở đó.

Hệ quả đã biết: `n4` không có fact để trích dẫn nên viết chính chữ trong đề vào
`source_fact_id`, và `grounding_gate` từ chối — **đúng**. Cổng làm việc của nó.

⚠️ Không sửa `analyze` trong wave này: **không ca demo nào hỏng vì lỗ này**
(`DEMO_REPLAY 5/5`).

## 3. Đính chính đã ghi (không hồi tố điểm)

| đính chính | nội dung |
|---|---|
| `translate` | **`CANONICAL_ERGONOMIC_PRIMITIVE`**, không phải năng lực tổng quát mới. `PRE_EXTENSION_SEMANTIC_EXPRESSIBLE = YES` — `divide_segment(R, midpoint(P,S), 2)` = `P + S − R`. Nó làm phép affine **dễ biểu diễn và dễ tổng hợp hơn**, không mở thêm thứ biểu diễn được |
| oracle `n3` | **không phân biệt được hai cách dựng**: `F = (0,4,2)` và `F = (0,12,−6)` cùng cho số 4. ⇒ **`n3` KHÔNG được dùng làm bằng chứng đúng đắn ngữ nghĩa.** Đây là lỗi của **artifact đánh giá**, không phải của sản phẩm — không sửa mã |
| `angle_cos_sq` | từng trả `sin²` cho cặp (đường, mặt); đã sửa, `ANGLE_SEMANTICS_ERRATUM.md` |

Mọi điểm số lịch sử (`GENERALIZATION_MATRIX`, `CLEAN_BASELINE_V1/V2`,
`SYNTHESIS_STABILITY_K3`, translation probe, `NAME_ONLY` probe) **giữ nguyên**.

## 4. Giới hạn — phân loại

### A. PHẢI SỬA TRƯỚC DEMO
**Không có.** `P0 = 0`, `P1 = 0`. `DEMO_REPLAY = 5/5`, 0 đường ném.

### B. GIỚI HẠN CHẤP NHẬN CỦA KHOÁ LUẬN
| giới hạn | vì sao chấp nhận |
|---|---|
| `CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL` | chương trình hình học gần như không rẽ nhánh; ca ấy bị **từ chối tĩnh** chứ không chạy sai. Kernel vẫn fail-closed |
| `ANALYZE_SOURCE_FACT_COMPLETENESS = PARTIAL` | không chặn demo; đo nó là nghiên cứu trích xuất thông tin, ngoài đề tài |
| chỉ khối **lồi** | ranh giới phạm vi có chủ đích (`GEOMETRY_ROADMAP`) |
| mặt cong: HỆ đóng, SẢN PHẨM `foundation_only` | ⚠️ ĐÍNH CHÍNH 2026-09-04. Bảng này từng ghi *"không mặt cong"* và câu ấy hết đúng từ `169b8ef` (2026-09-03). Phân biệt hai câu: năng lực **hệ** (IR + kernel + vẽ) = `CLOSED`; năng lực **sản phẩm** `ball`/`cylinder`/`cone` = `foundation_only` — chưa lượt tổng hợp cong nào của mô hình đạt `servable` trên bất kỳ artifact nào. Thẩm quyền: `product_capability.py` |
| hình thành khối bằng quay/quét liên tục | `OUTSIDE_CURRENT_MODEL` — `construct_curved_solid` là bước NGUYÊN TỬ (1 lệnh → 1 trace → 1 khung) |
| phủ chương trình **một phần** | có chủ đích; `COVERAGE.md` cấm tuyên bố phủ toàn bộ |
| `SECTION_COPLANAR_EDGE_GAP` | ca demo thiết diện (`v2_04`) **không chạm** lỗ này. Đã sửa 2026-09-02 ở bản sản phẩm hiện tại, **sau** `SEALED_RESEARCH_BASELINE` — số liệu không đổi theo |
| `literal` bọc quanh vô hướng ở `divide_segment.ratio` | quan sát 1 lần; cùng lớp đã vá cho `for_range.step` |

### C. HƯỚNG PHÁT TRIỂN
Kéo–thả liên tục kiểu GeoGebra (phá song ánh `frame k ⇔ trace[k]`) · **bật
sản phẩm** cho mặt cong (nền hệ đã có; thiếu bằng chứng mô hình tổng hợp) ·
đánh giá tác động người học · đo độ ổn định trích xuất · viết lại thân README
cho đề mới · `REPLAYABLE_ANALYZE_SEED` (chụp đầu vào analyze, đối xứng với tầng
tổng hợp đã có).

## 5. Tập demo

`backend/scripts/replay_demo_cases.py` — **0 lượt gọi model**, chạy từ chương
trình đã lưu trong artifact có xuất xứ rõ.

| ca | vai trò | nguồn |
|---|---|---|
| `n1_thoi_dinh_thu_tu` | dựng đỉnh thứ tư từ vectơ → đo tới đường, đáp số `√3` | `name-contract-probe` |
| `n2_lang_tru_xien_hai_vecto` | lăng trụ **xiên**, hai vectơ dẫn xuất + trung điểm, `3√3` | `name-contract-probe` |
| `t3_hop_tinh_tien_day_chuyen` | dây chuyền tịnh tiến 4 đỉnh, chuỗi sâu, `3√89/5` | `translation-probe` |
| `t4_mat_xich_trong_chuoi_sau` | hình chiếu trong chuỗi phụ thuộc, `2√2` | `translation-probe` |
| `n4_giao_duong_mat_roi_do` | **CỔNG TỪ CHỐI** — trích dẫn dữ kiện không có trong hợp đồng | `name-contract-probe` |

Ca thứ năm là **cố ý**: một demo chỉ toàn ca xanh giấu mất nửa luận điểm. Hệ
phải nói KHÔNG có địa chỉ, và đây là chỗ trình bày điều đó.

**Thiết diện** chạy riêng ở chế độ rút gọn (`v2_04_thiet_dien_goc_va_the_tich`,
cảnh có `section` + `solid`): artifact `clean-baseline-v2` **không lưu
`RequestContract`** nên không chạy được cổng grounding. Đếm riêng, không gộp
vào `DEMO_REPLAY` — gộp là báo cáo một chuỗi đủ mà thực ra thiếu một cổng.

## 6. Smoke trình duyệt cho tập demo

`frontend/scripts/spot-check-demo.mjs` — Chrome thật, WebGL:
**`DEMO_BROWSER_SMOKE = 12/12`, 0 lỗi console** (`DEMO_SPOT_CHECK.json`).

Số bước đọc từ màn hình khớp **chính xác** bộ replay Python — `n1` 6, `n2` 7,
`t3` 10, `t4` 9 — tức hai bộ đo độc lập nói cùng một điều về cùng một trace.
Đã tiêm lỗi giả để chứng minh nó đỏ được (8/12).

## 7. Lệnh kiểm lại (0 lượt gọi model)

```bash
cd backend && .venv/Scripts/python.exe scripts/replay_demo_cases.py
cd backend && .venv/Scripts/python.exe scripts/audit_demo_crash_surface.py
cd backend && .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build
cd frontend && npm run dev          # cửa sổ khác, rồi:
cd frontend && node scripts/spot-check-demo.mjs
```
