# STATUS_LEDGER.md — SỔ TRẠNG THÁI SẢN PHẨM

> **Luật của file này:** mỗi dòng phải trỏ tới **bằng chứng chạy được**. Không
> có bằng chứng ⇒ không được ghi DONE. Bằng chứng sinh từ commit khác HEAD ⇒
> `STALE_EVIDENCE`, cũng không được ghi DONE (`evidence.mjs::assertFresh`).
>
> Cập nhật ở CUỐI mỗi wave. Số sống vẫn ở `CURRENT_STATE.md`.

**HEAD lúc lập sổ:** `a3dac3b` (Wave 0–1 làm trên đó, commit ngay sau).

## 1. Kiến trúc & năng lực

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Kiến trúc mô phỏng tất định (R0: LLM đọc đề, engine diễn hoạt) | **DONE** | bất biến #1–#3 + `algorithms.test.ts`, `generic.test.ts`; pytest 1212 | — |
| Danh mục 23 target / 12 family | **DONE** | `catalog_runtime_matrix.py` → 23 target, conformance/ownership/parity 0 | — |
| Đường AI sinh spec (analyze→classify→simulate→validate) | **DONE** | `test_pipeline`, `test_capability_boundary`; bất biến #22 | W2 (oracle mới) |
| Đường demo công khai (thư viện offline) | **DONE** | `sample-coverage-w4b3d.test.ts` | W3 (lọc phạm vi) |
| **Parity demo ↔ AI** | **DONE (W1)** | `generation-parity.test.ts` — 22 target × 4 nguồn pipeline; `docs/evaluation/m20/generation-parity.json` | — |
| Bố cục sân khấu dùng chung (khung theo cơ chế, một rail) | **DONE (M19)** | `audit-composition.mjs` 92/92 ở 4 bề rộng; bất biến #30 | W7 (tách transport) |
| Khay điều khiển (transport) | **PARTIAL** | cùng cột với thẻ nên co theo cơ chế; W7 muốn nó có bề rộng workspace ỔN ĐỊNH | **W7A** |

## 2. Tương tác học sinh theo miền

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Thao tác trực tiếp HTML/CSS (chọn khối, đổi thứ tự) | **DONE** | `direct-manipulation-w4b4d.test.tsx`; mồi hai chiều | W9 (bàn phím/WCAG) |
| Truy vấn CSDL có ràng buộc | **DONE** | `query-first-w4b4b.test.ts` | — |
| Logic (bật/tắt đầu vào, lan truyền) | **DONE** | `dag.test.tsx`, `logic` domain tests | — |
| Điều kiện `count_if`/`sum_if` | **DONE** | `condition-param.test.ts`, `explore-ownership-w4b3a` | — |
| Trải nghiệm toàn danh mục | **PARTIAL — 20/23 thao tác được** | `w4b4a-experience/probe.json`, `VERDICT.md` | **W5F** |
| 3 target giữ trace có lý do cơ chế | **DONE (quyết định)** | `KEEP_TRACE` + guard hai chiều | W5F (rà lại) |
| RGB/CSS color (Tin 12) | **OPEN — chưa có target** | — | **W5A** |
| Nhãn giá trị vị trí theo cơ số | **OPEN** | — | **W5B** |
| Ký tự & mã hoá theo tham số | **PARTIAL** | đổi được `text`/`encoding` | **W5C** |

## 3. Sản phẩm & lớp học

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Trang khách (không thanh bên, một ô nhập, dùng thử 1 lượt) | **DONE** | `accept-classroom-m18.mjs` 4 bề rộng | **W7C** (đổi bản sắc sang LAB) |
| Xác thực + vai trò do máy chủ sở hữu | **DONE** | `test_auth_api.py`, 6 ca từ chối của `§36` | — |
| Lớp · mã vào lớp · giao bài · thực hành | **DONE** | `test_classroom_api.py` | — |
| Giáo viên quan sát (trạng thái có cấu trúc, 5s) | **DONE** | bất biến #27; `accept-classroom-m18.mjs` | — |
| Giáo viên CẤP tài khoản học sinh | **MISSING** | — (khai ở `CLASSROOM_AUTH_CONTRACT §3`) | ngoài chương trình |
| Tiếp tục ở nhà | **PARTIAL** | khôi phục BẢN GHI tiến độ, KHÔNG khôi phục state engine | W5F |
| Vỏ ứng dụng theo vai trò | **DONE** | `ux-shell.test.tsx`, `accept-classroom-m18.mjs` | W7D |

## 4. Đo lường & chất lượng

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| **Xuất xứ bằng chứng (dấu HEAD)** | **DONE (W0)** | `scripts/evidence.mjs`; đã gắn 3 script | — |
| Bằng chứng cũ trước W0 | **STALE_EVIDENCE** | không mang `head` ⇒ phải sinh lại trước phán quyết cuối | W14 |
| Dataset đánh giá AI 30 case | **DONE, đã đổi vai (W2)** | `LEGACY_AI_COMPOSITION_REGRESSION` — còn nguyên 30 case, hết làm thước đo phủ | — |
| Benchmark theo chương trình học | **DONE (W2/W2A/W2B/W2C)** | `curriculum_schema.py` + `metamorphic.py` + `product_scope.py`; `test_curriculum_benchmark.py` 23 test; `docs/evaluation/m20/curriculum-benchmark.json` | W3 dùng làm oracle |
| Phép đếm phủ từng nói dối | **ĐÃ SỬA (W2A)** | đếm chuỗi thô ⇒ 14 đơn vị (6 là câu ghi chú); rút regex ⇒ `T10.CD1` 12 case. Thật: **8 đơn vị**, `T10.CD1` 9–24 tùy pool | — |
| Cổng phạm vi + khả-mô-phỏng | **DONE (W3)** | `simulation/scope_gate.py` — cổng thứ NĂM, trước đường generic; `test_scope_gate.py` 15 test + 4 phép tiêm lỗi | — |
| Phán quyết phạm vi do LLM sở hữu (lỗ R0) | **ĐÃ BỊT (W3)** | trước W3, đề ngoài môn chỉ bị chặn khi `classify` tự từ chối; nay LLM KHAI, server PHÁN | — |
| Lời từ chối cho học sinh | **DONE (W3)** | 3 hạng mục riêng: `out_of_scope` · `not_simulation_suitable` · ngoài danh mục — không hứa sai “sẽ mở rộng dần” | W12 (soát ảnh) |
| Chứng nhận từng target | **PARTIAL (W4)** | manifest `target-certification.test.ts` — 4 cổng ĐỀU ĐÃ có chủ; ghi rõ cổng nào CHƯ A có bằng chứng tươi | W12 (sinh lại bằng chứng trình duyệt) |
| Join target ↔ đơn vị chương trình | **DONE (W4)** | 22/23 có bằng chứng, dẫn xuất từ case; ngoại lệ `binary.base_conversion` (cơ số 8/16 ngoài neo SGK) | — |
| Hai hệ ký hiệu neo trong cùng kho | **ĐÃ BẮC CẦU (W4)** | catalog ghi số BÀI, benchmark ghi mã CHỦ ĐỀ — join qua case thay vì chép tay SGK | W13 (hợp nhất?) |
| Kim tự tháp test (T0–T3) | **OPEN** | hiện chỉ có "chạy hết" | **W8** |
| Nghiệm thu trình duyệt 4 bề rộng | **DONE** | composition + classroom + experience | W12 (mở rộng) |
| Hook chất lượng phân biệt SVG vs HTML | **OPEN** | false positive đã xác định ở `ArrayView` | **W10** |

## 5. Phủ chương trình

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Ma trận phủ chương trình | **PARTIAL** | `COVERAGE.md` + `catalog_runtime_matrix` + báo cáo W2A (8 đơn vị, mọi đơn vị ≥3 case) | **W13** |
| Đơn vị chương trình mỏng (<3 case) | **DONE (W2A)** | T10.CD2 2→3, T12CS.CD7 1→3 (3 case cross-domain mới); khoá bởi guard ngưỡng | — |
| Tuyên bố bị cấm (không claim phủ toàn chương trình) | **DONE** | `COVERAGE.md §O` | giữ nguyên |
| `CURRICULUM_SUPPORT_PARTIAL` | **GIỮ** | — | W13 |
| `LEARNER_IMPACT_NOT_EVALUATED` | **GIỮ** | chưa có nghiên cứu trên người học | — |
