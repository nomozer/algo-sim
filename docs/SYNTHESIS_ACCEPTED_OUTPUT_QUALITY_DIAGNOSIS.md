# SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `ac2e764` · commit mã `a8e0e3b` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/synthesis-accepted-output-quality-diagnosis/`.
> **0 request Gemini · 0 request mạng.**

```text
SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS = PASS
ARCHITECTURAL_GAP_CLASSIFICATION            = MIXED (COMPUTATION_ONLY_COVERAGE → SCENE_TYPE_OR_PROVENANCE_MISMATCH)
HISTORICAL_LIVE_OUTPUT_CAUSE                = NOT_RECOVERABLE
STRUCTURAL_ROUTE_CAN_PASS_WITHOUT_SECTION   = YES (tái hiện offline)
PRODUCT_BEHAVIOR_CHANGED                    = NO
```

## 1. Kết luận

Lượt follow-up B02 được route phục vụ với final_memory và đáp số đúng nhưng cảnh không có vật `section`. Output lượt ấy không lưu, nên **không xác định được** mô hình đã dựng gì. Wave này trả lời câu khác: *kiến trúc có cho phép kết cục ấy không, và vì sao*. Có, vì hai nguyên nhân độc lập, cả hai tái hiện được bằng fixture offline trên hợp đồng B02 đóng băng:

1. **COMPUTATION_ONLY_COVERAGE** (upstream). Hợp đồng B02 chỉ có ba nghĩa vụ đo, không có `section_matches`.
   - `area` nhận chủ thể `polygon3 | section | circle3 | ellipse3`.
   - Cổng phủ cấu trúc chỉ đòi witness được sinh ra và dẫn xuất từ container.
   - `check_area` chỉ so diện tích của chính hình ấy với witness (hợp đồng không khai giá trị).
   - Kết quả: một đa giác vuông ở đáy, hoặc một `polygon3` cùng toạ độ thiết diện, đều **được phục vụ** với đáp số đúng 3/3.
2. **SCENE_TYPE_OR_PROVENANCE_MISMATCH** (downstream, khi hợp đồng có `section_matches`).
   - Chính sách nghĩa vụ nhận `polygon3` là thiết diện, nên đa giác cùng chu trình vẫn qua.
   - Scene builder phát loại theo giá trị runtime: đa giác luôn là `polygon3`.
   - Frontend chỉ nhận thiết diện khi `type === "section"`.
   - Kết quả: vật tồn tại đúng chỗ nhưng không được nhận là thiết diện.

Không có bằng chứng cho `CONSTRUCTION_TO_SCENE_DROP` (mọi `construct_section` đều thành một vật `section`) hay `CAPABILITY_CONTRACT_GAP` (DSL, hợp đồng, cảnh và renderer đều hỗ trợ thiết diện).

## 2. Tiền kiểm — `PRECHECK.json` = PASS

| mục | kết quả |
|---|---|
| nhánh · HEAD · `main` | `feat/photo-problem-to-scene` · `ac2e764` · `085cae6` |
| cây nguồn / worktree | chỉ ` D frontend/public/favicon.svg` / sạch, đưa từ `77ab45c` lên `ac2e764` sau khi xác nhận status rỗng |
| candidate · khoá cache | `544a0b56a40c6107…` khớp · khớp, `CACHE_VERSION` 95 |
| manifest benchmark · RequestContract B02 | `803ff1ad…` · `fd8880c4…` khớp |
| bản ghi follow-up B02 | commit `ac2e764`; `DEVELOPMENT_PILOT_FOLLOWUP` · `SILENT_QUALITY_FAILURE` · không vào mẫu số |

## 3. Audit đường dựng thiết diện — `ACCEPTED_OUTPUT_QUALITY_PATH_AUDIT.json`

| tầng | bằng chứng mã | phát hiện |
|---|---|---|
| RequestContract | `Obligation(kind, container, params)`; hợp đồng B02 = volume · area · distance | không nghĩa vụ nào nói container phải là thiết diện; hợp đồng **biểu diễn được** `section_matches` nhưng bản đóng băng không có |
| DSL | `ConstructSectionStmt` | câu lệnh duy nhất sinh giá trị `Section`; `construct_polygon` sinh bộ đỉnh |
| thực thi | `exec_construct_section` → `cross_section` | kernel quyết thứ tự cạnh, hậu điều kiện đặt mọi đỉnh trên mặt phẳng |
| validator | `validate_semantic_program` | kiểm hình dạng và kiểu toán hạng, không nối chủ thể đo với thứ đề yêu cầu vẽ |
| phủ cấu trúc (C₁a) | `check_structural_coverage` | chỉ đòi đường phép tính: kiểu container được nhận + witness dẫn xuất |
| hậu điều kiện (C₂) | `check_area`; `check_section_matches` | area: tự nhất quán; section_matches dựng lại chu trình nhưng nhận `polygon3` |
| scene builder | `simulation_state._than_hinh_hoc` · `_loai_ngu_nghia`; `scene3d.RENDER_HINT` | `Section` → `section`, bộ đỉnh → `polygon3`; không đổi nhãn qua lại |
| frontend | `deriveSectionSubEntities` · `sectionDetails` | chỉ nhận `type === "section"`; test thiết diện frontend **65 xanh** |
| bộ chấm benchmark | `danh_gia_canh` | đếm `section` và so chu trình — thứ route không đòi |

Trả lời:
- Phủ cấu trúc chỉ kiểm phép tính: **CÓ**.
- Bắt buộc câu lệnh dựng thiết diện: **KHÔNG**.
- Bắt buộc vật cảnh: **KHÔNG** (cảnh dựng sau khi route quyết).
- Đa giác thường bị tính là thiết diện: **CÓ** ở tầng nghĩa vụ (`section_matches`); **KHÔNG** ở tầng cảnh và frontend.
- Thiết diện mất xuất xứ khi đi từ IR sang cảnh: **không có bằng chứng**.
- Renderer hỗ trợ thiết diện: **CÓ**.

## 4. Ma trận bốn lớp — `OBLIGATION_COVERAGE_LAYER_MATRIX.json`

| nghĩa vụ | phép tính | phép dựng | cảnh | đáp số |
|---|---|---|---|---|
| volume | cổng kiểm (C₁a + `check_volume`); dương tính giả thấp | chỉ kiểm tồn tại + kiểu | không cổng nào kiểm | không kiểm với B02 |
| **area (thiết diện)** | cổng kiểm; **dương tính giả cao** khi dùng làm đại diện cho thiết diện | **không kiểm** `construct_section` | **không kiểm** | không kiểm với B02 |
| distance | cổng kiểm (C₁a + `check_distance`) | một phần (grounding điểm) | không cổng nào kiểm | không kiểm với B02 |

Mỗi ô trong artifact nêu tiêu chí PASS, nguồn kiểm, loại bằng chứng, gate hiện tại và rủi ro dương tính giả. Yêu cầu hình gắn theo **con trỏ nghĩa vụ**, không theo tên.

## 5. Fixture offline — `B02_QUALITY_FIXTURE_MATRIX.json`

Tất cả là biến thể nhỏ của chương trình p1 đã được nhận, chạy trên RequestContract B02 đóng băng. Yêu cầu hình và đáp số đăng ký lấy từ manifest benchmark.

| fixture | route hiện tại | phép tính · dựng · cảnh · đáp số (nghĩa vụ area) | thất bại im lặng |
|---|---|---|---|
| A đủ | served | PASS · PASS · PASS · PASS | không |
| B đa giác đáy thay thiết diện | **served** | PASS · FAIL · FAIL · PASS | **CÓ** (bỏ sót trực quan) |
| C đa giác cùng toạ độ | **served** | PASS · FAIL · FAIL · PASS | **CÓ** |
| C + hợp đồng có `section_matches` | **served** | PASS · FAIL · FAIL · UNVERIFIED | **CÓ** |
| D thiết diện sai tập đỉnh (khối khác) | **served** | PASS · PASS · FAIL · FAIL | **CÓ** |
| E đúng đỉnh, sai mặt phẳng nguồn *(sửa cảnh)* | served | PASS · PASS · FAIL · PASS | CÓ |
| F thiết diện đúng, thiếu witness | structural_coverage | FAIL · PASS · PASS · FAIL | không |
| G witness hằng số, không dựng hình | structural_coverage | FAIL · FAIL · FAIL · FAIL | không |
| H scene builder rơi thiết diện *(mô phỏng)* | served | PASS · PASS · FAIL · PASS | CÓ |
| I hai thiết diện, một mục tiêu | served | PASS · PASS · PASS · PASS | không |
| J mang loại `section` nhưng không khép kín *(sửa cảnh)* | served | PASS · PASS · FAIL · PASS | CÓ |

- E, H, J sửa hoặc mô phỏng tầng cảnh. Chương trình hợp lệ không sinh ra được chúng; chúng chỉ chứng minh chẩn đoán tách đúng lớp.
- B01, B03, B04 (chương trình lịch sử đã được nhận): đủ bốn lớp, không thất bại im lặng. B01 dùng capture local, không commit.

## 6. Chẩn đoán — `ACCEPTED_OUTPUT_QUALITY_DIAGNOSTIC_CONTRACT.json`

- **Hàm:** `backend/scripts/accepted_output_quality.py::chan_doan_chat_luong_dau_ra`, phiên bản `accepted-output-quality/1`.
- **Phạm vi:** nằm ngoài `MEASURED_SYSTEM_PATHS`, chỉ quan sát, không đổi quyết định phục vụ.
- **Runner:** cờ `--accepted-output-quality` ghi `{ca}_ACCEPTED_OUTPUT_QUALITY.json`.

**Mỗi hàng nghĩa vụ gồm:**
- con trỏ (tự kiểm bằng vân tay) và loại phép;
- trạng thái bốn lớp;
- loại hình yêu cầu và nguồn của yêu cầu (`REQUEST_CONTRACT` · `REGISTERED_REFERENCE`);
- loại câu lệnh dựng chủ thể và loại vật quan sát được;
- số vật cùng loại, trạng thái topology;
- mã lý do theo đúng nhánh kiểm.

**Cờ tổng hợp:** `SILENT_QUALITY_FAILURE` và `SILENT_VISUAL_OMISSION`.

**Không tự làm hình học:** bản đồ tên, phân giải witness, câu lệnh dựng, `cross_section`, `same_section_cycle`, vị từ mặt phẳng và `display` đều là hàm sản phẩm.

**Không lưu:** đề, chương trình, cảnh, tên hay giá trị bộ nhớ, toạ độ, công thức, prompt, output mô hình. Mọi chuỗi phải thuộc từ vựng đóng (test K khoá).

## 7. Test và tiêm lỗi

**Test viết trước:** `tests/test_accepted_output_quality.py`, 20 ca, **nền đỏ 20/20** (16 lỗi vì module chưa có, 4 fail vì cờ runner chưa có). Sau bản sửa: 20/20 xanh.

⚠️ **Đính chính trước commit — kỳ vọng sai của test G.**
- Ban đầu test giả định lớp đáp số PASS cho witness hằng số.
- Đo được: final_memory có đúng giá trị, nhưng scene builder **không phát readout** cho witness hằng số, nên người học không thấy đáp số.
- Chẩn đoán ghi `ANSWER_NOT_IN_SCENE_READOUT`. Test được sửa theo hành vi đo và thêm cửa sổ chứng; ý của test giữ nguyên: witness ghi thẳng không nâng được lớp nào.

**Tiêm lỗi — `FAULT_INJECTIONS.json`:** 7/7 bị bắt, 7/7 khôi phục trùng byte, 0 dấu tiêm còn lại.

| # | lỗi tiêm | test bắt |
|---|---|---|
| F1 | coi witness diện tích là đủ phủ cảnh | B · C · D · E · J2 |
| F2 | coi mọi `polygon3` là thiết diện | B · C |
| F3 | bỏ kiểm tập đỉnh | D |
| F4 | bỏ kiểm mặt phẳng | E |
| F5 | ghi giá trị đáp số vào chẩn đoán | A · K |
| F6 | lệch con trỏ nghĩa vụ | I · J |
| F7 | cờ chẩn đoán làm đổi envelope | O |

⚠️ **Lỗi bộ đo, sửa trong wave.** Lần tiêm đầu báo F2 còn 1 dấu tiêm dù tệp đã trùng SHA: chuỗi dấu `"polygon3"):` có sẵn trong mã gốc. Đã đổi sang dấu chỉ bản tiêm mới có và chạy lại; bản đầu giữ local.

## 8. Giữ nguyên hành vi — `BEHAVIOR_PARITY.json` = PASS

Cùng bốn bộ đo chạy trên worktree sạch tại START_HEAD và trên mã đã sửa (cờ tắt). JSON chính tắc trùng cả bốn:
- quyết định route B01–B04 + 7 chương trình B02 dẫn xuất (kể cả `scene3d` và `final_memory`);
- runner C01/C02 × 3 kịch bản × tắt/bật trace (thân mọi request, phản hồi sửa, envelope, bộ đếm);
- `scene3d` p1/p6;
- `final_memory` p1/p6 và phản hồi sửa.

Bật/tắt cờ chẩn đoán: request (M), phản hồi sửa (N), envelope (O), cảnh và kiểm tự động (Q) đều trùng.

Lần so đầu chưa loại hai khoá đường dẫn module (`pipeline_file`, `validator_file`) và báo khác đúng hai đường dẫn ấy. Đã loại như khoá định danh lượt chạy rồi so lại.

## 9. Cổng offline — `OFFLINE_GATES.json` = PASS

| cổng | kết quả |
|---|---|
| bộ test đầy đủ, worktree sạch tại `a8e0e3b` | 5235 pass · 2 fail · 1 skip |
| — 2 test băm CRLF | backlog `CROSS_PLATFORM_ARTIFACT_HASH_TESTS`; cây nguồn PASS |
| test mới · scene builder · topology thiết diện · phủ cấu trúc · trace synthesis · validator/căn hợp đồng · runner (ngân sách HTTP, khử bí mật) · danh tính/cache | 20 · 93 · 242 · 138 · 33 · 112 · 100 · 101 — tất cả xanh |
| test thiết diện frontend (`scene3d-subentities`, `scene3d-section`) | 65 xanh (frontend không đổi) |
| candidate · khoá cache (cây nguồn và worktree) | khớp · khớp |
| quét bí mật — `SECRET_SCAN.json` | 0 rò rỉ |

Bộ test đầy đủ trên cây nguồn trước commit: 5236 pass, 1 fail. Test hỏng là `test_holdout_readiness_7b`, vốn đòi cây sạch; nó pass trong worktree sạch.

## 10. Dữ liệu khoá luận — `THESIS_ERROR_ANALYSIS_RECORD.json`

```text
ERROR_CLASS                           = SILENT_VISUAL_OMISSION
DESCRIPTION                           = computation và answer đúng nhưng thiếu đối tượng trực quan bắt buộc
DISCOVERY_CASE                        = B02
DATASET_SPLIT                         = DEVELOPMENT_PILOT_FOLLOWUP
INCLUDE_IN_FINAL_ACCURACY_DENOMINATOR = false
```

Đây là bằng chứng phân tích lỗi, **không** phải kết quả holdout.

## 11. Danh tính và cache

- **Mã sản phẩm:** `backend/app` không đổi dòng nào; candidate giữ `544a0b56a40c6107…` (verify khớp trước và sau).
- **Bề mặt mô hình:** prompt `c50c8c6b…`, thẻ văn phạm `3fb8eeab…`, lược đồ synthesis `08dae8dc…`, lược đồ analyze `515001b5…`, năng lực `72edf39f…` không đổi (khoá cache verify khớp). Model giữ `gemini-2.5-flash`.
- **`CACHE_VERSION`:** giữ 95, vì không envelope hay hành vi sản phẩm nào đổi.
- **Artifact lịch sử:** không sửa.

## 12. Không khẳng định

- Nguyên nhân chính xác của output live B02 cũ: `NOT_RECOVERABLE`.
- Không đổi kết cục follow-up B02 (`SILENT_QUALITY_FAILURE`), không đổi benchmark lịch sử (`PARTIAL`), không có kết luận tối ưu token.
- Chính sách phục vụ không đổi: fixture thiếu thiết diện vẫn được phục vụ; wave này chỉ phát hiện nó.

## 13. Cây nguồn và commit

- **Commit 1 `a8e0e3b`:** `accepted_output_quality.py`, cờ runner, test, `CODE_INDEX.md`.
- **Commit 2:** báo cáo này và 11 artifact JSON đã rút gọn. Không có chương trình, cảnh, prompt, output hay JUnit.
- Stage bằng đường dẫn tường minh; staged diff không có `frontend/public/favicon.svg`.
- Không merge, không push; `main` không đổi; worktree thực thi sạch; thay đổi favicon của user còn nguyên.

`NEXT_ACTION = MIXED → SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE, rồi SECTION_PROVENANCE_NORMALIZATION`
