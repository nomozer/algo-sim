# SYNTHESIS_STRUCTURAL_COVERAGE_REJECTION_DIAGNOSIS

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `f8172b5` · commit mã `2dae29a` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/synthesis-structural-coverage-rejection-diagnosis/`.
> **0 request Gemini · 0 request mạng.**

```text
SYNTHESIS_STRUCTURAL_COVERAGE_REJECTION_DIAGNOSIS = PASS
STRUCTURAL_COVERAGE_DIAGNOSTIC                  = IMPLEMENTED
COVERAGE_DECISION_CHANGED                       = NO
TRACE_VERSION                                   = synthesis-repair-trace/2 (giữ, thêm trường tuỳ chọn)
HISTORICAL_B02_UNCOVERED_OBLIGATION             = NOT_RECOVERABLE
```

## 1. Kết luận

Benchmark đa ca (`f8172b5`) có ca B02 bị loại ở `ROUTE_STRUCTURAL_COVERAGE / requested_operation_uncovered` mà không biết nghĩa vụ nào chưa phủ. Wave này làm cổng phủ **nói ra** điều ấy, dạng máy đọc được, không đổi phán quyết.

- Mỗi nghĩa vụ của `RequestContract` nay có một hàng: con trỏ RFC 6901, loại, kiểu chủ thể, trạng thái phủ, mã lý do theo **đúng nhánh luật** đã quyết, loại và số bằng chứng.
- Hàng được ghi **ngay tại nhánh quyết** trong `check_structural_coverage`. Không có bộ phân tích chuỗi lỗi nào.
- Phán quyết, `missing`, `chan_doan`, envelope, request và phản hồi sửa trùng từng byte với START_HEAD.

Nghĩa vụ thật sự bị thiếu trong lượt live B02 cũ **vẫn không xác định được**: output và chương trình của lượt ấy không được lưu. Fixture ở đây là biến thể offline, không phải output live.

## 2. Audit — `STRUCTURAL_COVERAGE_AUDIT.json`

`check_structural_coverage` (gọi từ `route._sau_grounding`) duyệt thẳng `contract.obligations`, không lọc, không sắp xếp ⇒ chỉ số nguồn là chính xác.

| đo được trước bản sửa | giá trị |
|---|---|
| nhánh kết luận "chưa phủ" | 10 |
| nhánh có `chan_doan` có cấu trúc | 6 |
| nhánh khác nhau cùng mang `RANG_BUOC_THIEU` | 3 |
| nhánh bác không có dòng nào (thiếu toán hạng cấu trúc ×2, quan hệ không dẫn xuất, không dẫn xuất từ chủ thể) | 4 |
| hàng cho nghĩa vụ đã phủ | không có |

Chi tiết rơi mất ở bốn tầng:
1. `chan_doan` cũ chở tên chương trình và không có chỉ số.
2. `route.details` là văn xuôi có tên.
3. Sự kiện `semantic_route` không phát `chan_doan_nghia_vu`.
4. Trace chỉ giữ pha, mã và câu lý do cố định.

## 3. Hợp đồng chẩn đoán — `COVERAGE_DIAGNOSTIC_CONTRACT.json`

**Nguồn:** `coverage_gate.TrangThaiNghiaVu` (một hàng mỗi nghĩa vụ, trên mọi nhánh trả về của C₁a) → `chan_doan_phu_cau_truc` → `SemanticRouteOutcome.coverage_diagnostic` (chỉ khi C₁a bác) → sự kiện `semantic_route` (khoá chỉ có khi khác `null`) → trace.

**Trường trong trace:** `obligation_pointer` · `pointer_status` · `operation_kind` · `canonical_operation_kind` · `target_kind` · `coverage_status` · `reason_code` · `evidence_kind` · `evidence_count`, cùng các số đếm requested/covered/uncovered/not_evaluated.

**Mã lý do — một nhánh, một mã:** `KIND_OUTSIDE_TAXONOMY` · `AMBIGUOUS_BINDING` · `CONTAINER_NOT_DECLARED` · `CONTAINER_TYPE_NOT_ACCEPTED` · `STRUCTURAL_OPERAND_MISSING` · `STRUCTURAL_OPERAND_NOT_CONSTRUCTED` · `WITNESS_NOT_IN_CONTRACT` · `WITNESS_NOT_DECLARED` · `WITNESS_WITHOUT_PRODUCER` · `RELATIONAL_WITNESS_NOT_DERIVED` · `WITNESS_NOT_DERIVED_FROM_CONTAINER` · `COVERED` · `COVERED_WITHOUT_SERVER_CHECKER`.

**Con trỏ:**
- Nguồn dựng con trỏ từ chỉ số vòng lặp rồi **tự kiểm**: phần tử tại con trỏ trong `contract.model_dump(mode="json")` phải mang đúng vân tay của hàng, không thì `null` + `AMBIGUOUS`. Tên trường không được tin suông.
- Runner **kiểm lại** trên hợp đồng nó tự dựng từ phản hồi analyze; lệch vân tay hoặc không giải được ⇒ `null` + `AMBIGUOUS`.
- Vân tay (16 hex SHA-256 của nghĩa vụ) chỉ dùng để kiểm, **không** ghi vào trace.

**Không lưu:** output thô, prompt, chương trình, giá trị hình học, tên/nhãn, `details`/`reason`, vân tay. Runner chỉ chép khoá cho phép; mã ngoài từ vựng đóng ⇒ `OUT_OF_VOCABULARY`.

## 4. Trace — `TRACE_VERSION_DECISION.json` = KEEP_V2

Thêm một trường tuỳ chọn `route_coverage_diagnostic`, không đổi nghĩa trường cũ.
- Lượt route dừng ở `structural_coverage`: có giá trị.
- Mọi lượt khác, kể cả lỗi provider và lượt bị vòng sửa loại: `null`.
- `doc_trace_vong_sua` đặt `null` cho trace v1 lịch sử và v2 cũ; phiên bản lạ vẫn `ValueError`.

## 5. Ma trận B02 offline — `B02_OFFLINE_COVERAGE_MATRIX.json`

Hợp đồng p1 dựng từ `raw/analyze_0.json` đóng băng (3 nghĩa vụ: thể tích, diện tích, khoảng cách); chương trình p1 đã được nhận, sửa nhỏ.

| fixture | route | hàng chưa phủ (con trỏ · mã · bằng chứng) | `chan_doan` cũ |
|---|---|---|---|
| đầy đủ | phục vụ | — | — |
| bỏ producer witness thể tích | `structural_coverage` | `/obligations/0` · `WITNESS_WITHOUT_PRODUCER` | `RANG_BUOC_THIEU` |
| bỏ producer witness diện tích | `structural_coverage` | `/obligations/1` · `WITNESS_WITHOUT_PRODUCER` | `RANG_BUOC_THIEU` |
| bỏ producer witness khoảng cách | `structural_coverage` | `/obligations/2` · `WITNESS_WITHOUT_PRODUCER` | `RANG_BUOC_THIEU` |
| bỏ hai (thể tích, khoảng cách) | `structural_coverage` | `/obligations/0`, `/obligations/2` · `WITNESS_WITHOUT_PRODUCER` | `RANG_BUOC_THIEU` ×2 |
| witness thể tích đo khoảng cách | `structural_coverage` | `/obligations/0` · `WITNESS_NOT_DERIVED_FROM_CONTAINER` · `WITNESS_RESOLUTION_QUANTITY_LECH` | *(không có)* |
| witness có trong bộ nhớ nhưng gán hằng | `structural_coverage` | `/obligations/0` · `WITNESS_NOT_DERIVED_FROM_CONTAINER` · `WITNESS_RESOLUTION_PRODUCER_KHONG_PHAI_MEASURE` | *(không có)* |

B01–B04 (chương trình lịch sử đã được nhận): cả bốn vẫn phục vụ, không có chẩn đoán từ chối.

## 6. Test và tiêm lỗi

**Test viết trước:** `tests/geometry/test_structural_coverage_diagnostic.py`, 25 ca (A–R), **nền đỏ 25/25** trên START_HEAD, 25/25 xanh sau bản sửa.

**Tiêm lỗi — `FAULT_INJECTIONS.json`:** 7/7 bị bắt, cả 7 tệp khôi phục trùng từng byte, test xanh lại sau cùng.

| # | lỗi tiêm | test bắt |
|---|---|---|
| F1 | chỉ số nguồn lệch một | A–D, F, G |
| F2 | gộp hai nhánh vào một mã | F |
| F3 | đổi phán quyết sau lớp chẩn đoán | A–C, M |
| F4 | runner ghi vân tay vào trace | I |
| F5 | runner tin con trỏ nguồn, không kiểm lại | H |
| F6 | pipeline ngừng phát chẩn đoán | J, O, P, R |
| F7 | tên vật lọt qua `target_kind` | I |

## 7. Parity hành vi — `BEHAVIOR_PARITY.json` = PASS

Bốn bộ đo chạy trên START_HEAD và trên mã đã sửa; JSON chính tắc trùng nhau cả bốn:
- phán quyết route B01–B04 + 7 fixture B02 (kể cả băm `missing`, `details`, `chan_doan`, `scene3d`, `final_memory`);
- runner C01/C02 × 3 kịch bản × tắt/bật trace (thân mọi request, phản hồi sửa, bộ đếm HTTP/retry, envelope);
- `scene3d` p1/p6;
- `final_memory` p1/p6 và phản hồi sửa của chương trình C02 dẫn xuất.

## 8. Cổng offline — `OFFLINE_GATES.json` = PASS

| cổng | kết quả |
|---|---|
| bộ test đầy đủ, worktree sạch tại `2dae29a` | 5212 pass · 3 fail · 1 skip |
| — drift candidate trước refreeze | sau refreeze: `--verify` khớp, 65 pass |
| — 2 test băm CRLF | backlog `CROSS_PLATFORM_ARTIFACT_HASH_TESTS`; cây nguồn PASS |
| test chẩn đoán mới · cổng phủ · trace · validator/căn hợp đồng · runner (ngân sách HTTP, khử bí mật) | 25 · 297 · 33 · 142 · 100 — tất cả xanh |
| khoá danh tính cache | khớp, `CACHE_VERSION` 95 |
| quét bí mật — `SECRET_SCAN.json` | 0 rò rỉ |

## 9. Danh tính và cache

- **Candidate:** `37500cd92f134e44…` → `544a0b56a40c6107…` (94 file), đóng băng lại tại `2dae29a` trong worktree sạch; khai ở `CANDIDATE_DIVERGENCE.json`.
- **Bề mặt mô hình không đổi:** prompt, lược đồ synthesis/analyze, thẻ văn phạm, băm năng lực trùng từng byte (khoá danh tính cache khớp).
- **`CACHE_VERSION` giữ 95:** không envelope nào đổi; trường mới không vào envelope.

## 10. Không khẳng định

- Không xác định nghĩa vụ thiếu của lượt live B02 cũ.
- Không đổi kết quả benchmark B02 hay kết luận token của benchmark.
- Không chính sách phủ, prompt, lược đồ hay model nào bị sửa.

## 11. Cây nguồn và commit

- **Commit 1 `2dae29a`:** mã, test, `CODE_INDEX.md`, `CANDIDATE_DIVERGENCE.json`.
- **Commit 2:** manifest candidate, báo cáo này, 9 artifact JSON. Không có output thô, prompt, chương trình, checkpoint riêng tư, khoá API hay JUnit.
- Stage bằng đường dẫn tường minh; staged diff không có `frontend/public/favicon.svg`.
- Không merge, không push; `main` không đổi; worktree thực thi sạch.

`NEXT_ACTION = B02_STRUCTURAL_COVERAGE_LIVE_REVALIDATION`
