# Contract: Text-to-Geometry Functions (`geometry-functions/2`, engine `geometry-function-engine/1`)

Contract **đang hiệu lực** của kiến trúc đích ([`TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`](TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md)).
Sửa contract ⇒ wave mới + test. Bản v1 bất biến: `../evaluation/geometry/runs/text-to-geometry-functions/FUNCTION_REGISTRY_SPEC.md`.

```
đề ──► AI (Gemini function calling, MỘT lượt/đề)        backend/app/ai/function_calling.py
   ──► lời gọi {fn, args, call_id, quotes[], depends_on[]}
   ──► lược đồ đóng · cổng nguồn 5 tầng                  backend/app/simulation/geometry_functions/registry.py
   ──► engine: chuẩn hoá có tiền điều kiện · phụ thuộc · bố cục khung affine + Gram · kiểm MỌI dữ kiện
                                                          backend/app/simulation/geometry_functions/engine.py
   ──► IR SemanticProgram ──► interpreter + kernel dưới metric.using(G)
   ──► Scene3D + chart_metric (+ length_unit)            backend/app/ai/function_route.py
```

## 1. Lời gọi

`{"id"|"call_id": "c1", "fn": <tên trong REGISTRY>, "args": {...}, "source": {"quotes": ["…nguyên văn…"]},
"depends_on": ["c0"]}`. Lược đồ đóng (`extra="forbid"`): không ô toạ độ, không hàm ngoài bảng, không mã. Nhãn
`^[A-Z][0-9]*'?$`; khối `S.ABC` / `ABC.A'B'C'`; số chính xác `4 · 2/3 · 1,5 · √3 · 3√3/4` hoặc theo ký hiệu
`a · 2a · a√3 · a√3/2 · 3a/2`. `depends_on` là khai báo của AI: treo ⇒ `DANGLING_DEPENDENCY`, vòng ⇒ `DEPENDENCY_CYCLE`;
engine tự tính thứ tự dựng, không tin khai báo ấy.

## 2. Thư viện hàm (30)

Danh sách đúng theo mã tại run `hybrid-section-slice`, 2026-10-11. Hằng `REGISTRY_VERSION` trong mã vẫn là
`geometry-functions/3`; bộ hàm được định danh bằng băm khai báo hàm `f2ec9698…`, ghim trong
`test_hybrid_goal_decomposition.py::test_provider_surfaces_are_pinned`.

| nhóm | hàm |
|---|---|
| dữ kiện | `regular_polygon` · `rectangle` · `right_angle` · `segment_length` · `equal_length` · `height` · `perpendicular_line_plane` · `perpendicular_lines` · `altitude` · `orthogonal_projection` · `face_perpendicular_base` |
| dựng | `midpoint` · `centroid` (tam giác) · `pyramid` · `regular_pyramid` · `prism` · `orthogonal_projection_line` · `intersect_line_line` · `intersect_line_plane` · `section` (thiết diện khối × mặt qua ba điểm có tên) · `intersection_line` (giao tuyến hai mặt) |
| hỏi | `ask_volume` · `ask_area` · `ask_section_area` · `ask_length` · `ask_distance_point_plane` · `ask_distance_lines` · `ask_angle_line_plane` · `ask_angle_plane_plane` (góc trả `cos²`) |
| thoát | `unsupported` ⇒ `OUT_OF_SCOPE` |

Thiết diện và giao tuyến dùng **IR chung đã có**: `construct_section`, `assign` với `intersect_plane_plane`, `measure area`.
Hybrid không có engine thứ hai. Mỗi (khối, phương trình mặt cắt) chỉ dựng một thiết diện, dù mặt được gọi bằng các bộ
điểm khác nhau. Các mã từ chối:
- `PARALLEL_PLANES`: hai mặt song song hoặc trùng nhau;
- `SECTION_EMPTY`: mặt cắt không cắt khối;
- mã của kernel: mặt qua ba điểm thẳng hàng; `PLANE_TOUCHES_VERTEX`, `PLANE_TOUCHES_EDGE`, `PLANE_DOES_NOT_CUT`.

Mỗi **cấu trúc câu** là một hàm riêng (đường cao, hình chiếu, hai đường vuông góc…), không phải danh sách đồng nghĩa
của một hàm. Từ khoá định nghĩa của hàm là điều kiện **cần** (§3.4), không phải bộ hiểu câu.

## 3. Cổng nguồn (`kiem_nguon`) — theo thứ tự

1. **Vị trí**: mọi quote nằm trong đề, so sau khi bỏ khoảng trắng (`QUOTE_NOT_IN_SOURCE`); nhãn là nhãn của đề (`UNKNOWN_LABEL`).
2. **Vai trò mệnh đề** (mọi hàm trừ `ask_*`/`unsupported`), đọc tại **mọi mốc** của lời gọi trong quote: đầu quote, từ
   khoá vị từ, nhãn của lời gọi, cụm "X là giao điểm/hình chiếu". Một bộ phân tích chung (`_vai_tro_tai`, run
   `hybrid-gate-clause-role-fix`, sửa ở run `hybrid-slice-review`):
   - sau "chứng minh/CMR/chứng tỏ" mà chưa có "biết" (và không có động từ hỏi riêng sau đó) ⇒ `GOAL_CLAUSE_NOT_PREMISE`;
   - có từ mở điều kiện ở trước mốc trong cùng câu (nếu, khi — trừ "khi đó/cắt/dựng/quay/chiếu", giả sử, trong trường hợp,
     với điều kiện, trừ khi) hoặc mốc đứng trước "thì" ⇒ `CONDITIONAL_CLAUSE`;
   - mệnh đề hỏi có/không (phải chăng, có phải, hay không, "… không?") ⇒ `QUESTION_CLAUSE_NOT_PREMISE`;
   - dữ kiện sau "biết" trong câu hỏi là tiền đề.
   **Câu hỏi** (`ask_*`): xét tại **mốc đối tượng** (danh từ đại lượng của hàm, hoặc nhãn có tập nhãn đúng bằng một toán
   hạng). Đối tượng được hỏi khi có động từ hỏi (tính / tìm / xác định / hỏi) đứng trước nó sau dấu hiệu dữ kiện cuối, không
   bị từ chặn tân ngữ (theo, tỉ số, tổng, sao cho, gấp, so sánh hơn/nhất…) xen giữa; hoặc "bao nhiêu / mấy / ?" sau nó. Không
   được: bị gán giá trị ("bằng 4", "= √17"), là quan hệ có/không không kèm "bao nhiêu", nằm trong mệnh đề chứng minh/điều
   kiện. Sai ⇒ `NOT_ASKED_IN_SOURCE` hoặc mã vai trò. Toán hạng của câu hỏi CHƯA được buộc vào cụm đối tượng — xem
   `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES`.
   **Mặt cắt** (`section`, `ask_section_area`, `intersection_line`): mặt phải là mặt mà quote gọi tên ở vị trí mặt cắt
   ("cắt bởi (P)", "thiết diện của <khối> với (P)", "(P) cắt …" khi (P) là chủ ngữ mệnh đề, "giao tuyến của (P) và (Q)"),
   khối là khối của quote hoặc khối duy nhất của đề ⇒ nếu không `SOURCE_OBJECT_MISMATCH`.
3. **Phủ định** trong quote hoặc ngay trước nó trong cùng mệnh đề (cắt ở `, ; :`) ⇒ `NEGATED_CLAUSE`.
4. **Vị từ + tham chiếu**: từ khoá định nghĩa ⇒ `PREDICATE_NOT_IN_QUOTE`; mặt phẳng được nhắc (nhóm nhãn trùng tập
   điểm, hoặc "đáy" với mặt đáy) ⇒ `PLANE_NOT_IN_QUOTE`; đoạn/đường và điểm đóng vai riêng (ảnh hình chiếu, chân đường
   cao) được nhắc ngoài nhóm mặt phẳng ⇒ `ROLE_NOT_IN_QUOTE`.
5. **Giá trị**: quote có nhãn đoạn ⇒ số ĐẦU TIÊN sau nhãn ấy phải bằng ô số; không có nhãn ⇒ quote đúng một số
   (`AMBIGUOUS_VALUE_QUOTE`); lệch ⇒ `UNGROUNDED_VALUE`.

## 4. Engine

- **Độ dài** (`do_dai`): `segment_length`, lớp `equal_length`, hình đã dựng, cạnh khác của đa giác đều; hai nguồn lệch ⇒
  `INCONSISTENT_FACTS` nêu đủ lời gọi.
- **Bố cục đáy** (khung 2D + Gram G₂ hữu tỉ): đa giác đều k ∈ {3, 4, 6} (khác ⇒ `UNSUPPORTED_REGULAR_POLYGON`), hình chữ
  nhật, tam giác theo cạnh + góc vuông; khác ⇒ `UNSUPPORTED_BASE_SHAPE`. G = G₂ ⊕ h²; đỉnh ngoài đáy ở z = 1.
- **Chuẩn hoá có tiền điều kiện** — ba cách nói về đường vuông góc mặt phẳng thành MỘT ràng buộc:
  `perpendicular_line_plane` (chân = đầu mút trên mặt); `altitude` (đỉnh phải là đỉnh của chính khối chóp, chân trên đáy);
  `orthogonal_projection` (ảnh ≠ điểm, ảnh trên mặt). Hỏng ⇒ `PRECONDITION_FAILED` / `FOOT_NOT_IN_PLANE`.
  `perpendicular_lines`: ⊥ HAI đường không song song trong đáy, đầu kia thuộc đáy ⇒ ⊥ đáy (định lý); một đường ⇒ chưa xác định.
- **Mặt bên ⊥ đáy**: một đỉnh ngoài đáy + hai đỉnh đáy; chân F trên AB **dẫn xuất** t = (SA² − SB² + AB²)/(2AB²),
  h² = SA² − t²AB² (≤ 0 ⇒ `INCONSISTENT_FACTS`; thiếu SA/SB ⇒ `MISSING_DIMENSION`).
- **Độ dài ký hiệu**: mọi độ dài theo a ⇒ dựng ở a = 1 (bước `choose_unit`, `LAYOUT_DERIVED`, không phải dữ kiện), đáp số =
  hệ số · a^bậc (thể tích 3, diện tích 2, độ dài/khoảng cách 1, góc 0); trộn a với số ⇒ `NON_HOMOGENEOUS_LENGTHS`.
- **Không suy chân mặc định**: điểm không có luật xác định ⇒ `UNDERDETERMINED_POINT`.
- **Kiểm**: mọi dữ kiện kiểm lại chính xác dưới G (mặt ⊥ mặt bằng n₁ᵀG⁻¹n₂ = 0). Lời gọi engine đã dùng mà sai ⇒
  `ENGINE_SELF_CHECK_FAILED`; còn lại ⇒ `INCONSISTENT_FACTS`. Điểm kernel thực thi phải trùng bố cục.

## 5. Adapter Gemini (offline ở `ai-function-route`)

Một `generateContent`/đề; `tools.functionDeclarations` dẫn xuất từ REGISTRY (tập con OpenAPI, Type viết hoa, không
`$ref`/`anyOf`); `toolConfig.functionCallingConfig = {mode: ANY | VALIDATED, allowedFunctionNames}`; `maxOutputTokens`
là trần cứng (gồm thinking). Phản hồi: `MAX_TOKENS` ⇒ `RESPONSE_TRUNCATED` (không thực thi kế hoạch cụt);
`MALFORMED_FUNCTION_CALL`; lý do khác ⇒ `PROVIDER_REFUSED`; không ứng viên ⇒ `NO_CANDIDATE`/`PROVIDER_BLOCKED`; không
`functionCall` ⇒ `NO_FUNCTION_CALL`; thiếu `call_id` ⇒ `CALL_ID_MISSING`; trùng id khác nội dung ⇒ `DUPLICATE_CALL_ID`
(y hệt ⇒ bỏ, ghi `dropped_identical_duplicates`). Lỗi transport ⇒ `PROVIDER_ERROR`. Không bao giờ lùi về `LLM_ONLY`.
Vân tay bề mặt mô hình của đường này: `surface_fingerprint()` — mọi lượt đo phải ghi.

## 6. Ranh giới

Đường mặc định (`app.main`, `app.ai.pipeline`) không với tới các module trên — bao đóng import khoá ở
`backend/tests/geometry/test_structured_geometry_relations.py::test_Y_duong_mac_dinh_VAN_khong_tham_chieu_compiler`;
`app/simulation` không nhập `scene3d`/`simulation_state`. Giới hạn hiện tại: một mặt đáy; chóp/lăng trụ đứng; chưa có
song song, góc nhị diện tổng quát, thiết diện, khối tròn, đáy hình thoi/hình thang.
