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

Danh sách đúng theo mã tại run `hybrid-section-slice`, 2026-10-11. Từ run `source-bound-result-planning`
(product `efb756aa`): `REGISTRY_VERSION = geometry-functions/4`, `orthogonal_projection_line` nhận thêm `line_ref`
tuỳ chọn (`line` xor `line_ref`; tuyến A gửi `line_ref` ⇒ `RESULT_BINDING_UNVERIFIED`); băm khai báo hàm `5ceb0f99…`
(trước đó `f2ec9698…`), ghim qua `runs/source-bound-result-planning/provider-surfaces.json` trong
`test_hybrid_goal_decomposition.py::test_provider_surfaces_are_pinned`. `PlanningContract` chỉ là metadata nội bộ,
không vào khai báo hàm.

| nhóm | hàm |
|---|---|
| dữ kiện | `regular_polygon` · `rectangle` · `right_angle` · `segment_length` · `equal_length` · `height` · `perpendicular_line_plane` · `perpendicular_lines` · `altitude` · `orthogonal_projection` · `face_perpendicular_base` |
| dựng | `midpoint` · `centroid` (tam giác) · `pyramid` · `regular_pyramid` · `prism` · `orthogonal_projection_line` · `intersect_line_line` · `intersect_line_plane` · `section` (thiết diện khối × mặt qua ba điểm có tên) · `intersection_line` (giao tuyến hai mặt) |
| hỏi | `ask_volume` · `ask_area` · `ask_section_area` · `ask_length` · `ask_distance_point_plane` · `ask_distance_lines` · `ask_angle_line_plane` · `ask_angle_plane_plane` (góc trả `cos²`; đề hỏi `"số đo (của) góc"` hoặc theo `độ`/`radian` ⇒ `QUESTION_CONTEXT_UNSUPPORTED`) |
| thoát | `unsupported` ⇒ `OUT_OF_SCOPE` |

**Hàm chỉ dành cho planner** (run `goal-directed-section-planning`): `translate_point` (`auxiliary_only`) — ảnh của
một điểm qua phép tịnh tiến theo vectơ hai điểm đã có. Không khai cho provider (tuyến A vẫn đúng 30 hàm trên,
`PROVIDER_FUNCTIONS`; băm khai báo `f2ec9698…` không đổi ở run đó), chỉ hợp lệ trong một phân rã đã khai `MAT_SONG_SONG`:
thiết diện / diện tích thiết diện với mặt (P) qua điểm đã xác minh M song song mặt có tên (Q) = mặt qua M và hai
ảnh tịnh tiến của M theo Q₀Q₁→, Q₀Q₂→ (biểu thức IR `vector_from_points` + `translate`, không primitive mới).
Typed Facts: `section` / `question(area)` mang `point` + `points_b` + `plane_relation` thay cho `points`;
`perpendicular` ⇒ `PLANE_NOT_UNIQUE`. Engine kiểm: song song (Q), không trùng (Q) (`DERIVED_PLANE_IS_REFERENCE`),
không là mặt biên (`SECTION_PLANE_IS_FACE`); hàm phụ ngoài phân rã ⇒ `AUXILIARY_ONLY_FUNCTION`.

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
   **Câu hỏi** (`ask_*`, S1 — run `hybrid-semantic-hardening`, đóng an toàn ở run `shared-ask-grammar-safety`): đề phải có một
   **cụm đối tượng** thuộc văn phạm đóng của hàm (`_CUM_HOI`: "khoảng cách từ P đến (Q)", "thể tích khối chóp S.ABCD", "góc
   giữa SC và (ABCD)", "diện tích thiết diện … cắt bởi (P)" …) mà toán hạng ĐÚNG là toán hạng của lời gọi (mặt: chung ba điểm
   có tên; "đáy": đáy của khối duy nhất; ký hiệu và loại khối phải khớp) — không có ⇒ `SOURCE_OBJECT_MISMATCH`. Cụm phải được
   hỏi NGUYÊN VẸN: trước nó (từ động từ hỏi cuối) chỉ có từ nối và cụm hỏi khác; sau nó chỉ "bằng / là bao nhiêu", "?", "theo a"
   (khi đề khai báo tham số `a` và không dùng đơn vị mét), "theo <đơn vị>" / ngoặc đơn vị khớp chiều đại lượng và cơ sở đơn vị
   của đề, "đã cho / đó", "của <khối>", rồi kết câu thật, lời dẫn dữ kiện (biết, với, cho, trong đó) hay việc kế tiếp (rồi,
   sau đó, từ đó, bằng cách); không bị gán giá trị, không là câu có/không, không trong mệnh đề chứng minh/điều kiện — sai ⇒
   `NOT_ASKED_IN_SOURCE` hoặc mã vai trò. Vì engine chỉ trả biểu thức căn/hữu tỉ chính xác và trả `cos²=...` cho góc, mọi yêu
   cầu làm tròn số thập phân (`_LAM_TRON` khi có `ask_*`), ghi kết quả ở dạng phân số / căn thức / hàng thập phân chưa xác
   minh, đổi đơn vị chưa hỗ trợ, hoặc hỏi `"số đo (của) góc"` / góc theo `độ` hay `radian` đều từ chối fail-closed với
   `QUESTION_CONTEXT_UNSUPPORTED`.
   **Vai trò tiền đề** (S1) còn nhận: mục tiêu "chỉ ra / giải thích / kiểm chứng / kiểm tra / tìm điều kiện / suy ra / xác
   minh / vì sao / lập luận"; giả định và tường thuật "hễ / xét trường hợp / cho rằng / cho là / coi như / giả định / muốn
   / khẳng định / theo bạn"; điều kiện đặt SAU quan hệ ("… khi M trùng S"); mệnh đề kết bằng "?" hay "có … không.".
   **Mặt cắt** (`section`, `ask_section_area`, `intersection_line`): mặt phải là mặt mà quote gọi tên ở vị trí mặt cắt
   ("cắt bởi (P)", "thiết diện của <khối> với (P)", "(P) cắt …" khi (P) là chủ ngữ mệnh đề, "giao tuyến của (P) và (Q)"),
   khối là khối của quote hoặc khối duy nhất của đề ⇒ nếu không `SOURCE_OBJECT_MISMATCH`.
3. **Phủ định** trong quote hoặc ngay trước nó trong cùng mệnh đề (cắt ở `, ; :`) ⇒ `NEGATED_CLAUSE`. S1 thêm: phủ định
   mạnh / tình thái ("không hề", "chẳng", "chưa", "không thể", "có thể" …), tuyển "hoặc" trong mệnh đề, câu tự phủ nhận
   ("… là sai", "vô lí").
4. **Vị từ + tham chiếu**: từ khoá định nghĩa ⇒ `PREDICATE_NOT_IN_QUOTE`; mặt phẳng được nhắc (nhóm nhãn trùng tập
   điểm, hoặc "đáy" với mặt đáy) ⇒ `PLANE_NOT_IN_QUOTE`; đoạn/đường và điểm đóng vai riêng (ảnh hình chiếu, chân đường
   cao) được nhắc ngoài nhóm mặt phẳng ⇒ `ROLE_NOT_IN_QUOTE`.
5. **Giá trị**: quote có nhãn đoạn ⇒ số ĐẦU TIÊN sau nhãn ấy phải bằng ô số; không có nhãn ⇒ quote đúng một số
   (`AMBIGUOUS_VALUE_QUOTE`); lệch ⇒ `UNGROUNDED_VALUE`. S1: số neo sau nhãn đoạn phải nối bằng PHÉP BẰNG ("=", "bằng",
   "là", "dài", "có độ dài", chuỗi "SA = SB = 3") và sau số chỉ có đơn vị rồi hết mệnh đề — "SA ≥ 3", "SA ≈ 3", "SA bằng 3
   lần AB", "SA = 3 là sai" ⇒ `UNGROUNDED_VALUE`.

6. **Ngữ cảnh yêu cầu & văn phạm câu hỏi dùng chung** (runs `question-local-givens`, `shared-ask-grammar-safety`, research
   branch): sau khi mọi lời gọi vượt cổng nguồn thường, `_kiem_du_kien_cau_hoi` và `_kiem_vung_tien_de` kiểm toàn bộ câu hỏi,
   mệnh đề mục tiêu/phép dựng đứng trước động từ hỏi, việc kế tiếp, câu theo sau và câu ghi chú.
   - Mọi chữ trong câu có cụm được hỏi phải thuộc một vùng đã đọc (`_vung_hoi`, động từ hỏi, fragment dữ kiện đã cover, việc
     kế tiếp hợp lệ, mệnh đề mục tiêu hoàn chỉnh có vị từ quan hệ/tính chất `_VI_TU_MUC_TIEU` hoặc quan hệ bội số nhị nguyên
     `_QUAN_HE_BOI_SO` giữa hai đoạn thẳng, hoặc phép dựng hợp lệ); phần dư chỉ được khớp `_DAN_CAU_HOI`.
   - Câu ghi chú chỉ hợp lệ theo 3 mẫu câu đóng (`_GHI_CHU_TRINH_BAY`, `_GHI_CHU_THANG_DO`, `_GHI_CHU_DON_VI_KET_QUA`), không
     dùng túi từ lặp và không có nhánh mặc định cho qua.
   - Độ dài trực tiếp và cạnh kề của đa giác đều đã khai, hình đáy và các quan hệ trong vocabulary đóng phải khớp.
   - Dữ kiện mâu thuẫn ⇒ `QUESTION_LOCAL_GIVEN_CONFLICT`; chưa có thẩm quyền xác minh ⇒ `QUESTION_LOCAL_GIVEN_UNVERIFIED`.
   - Ngữ cảnh giả định/thay cấu hình, câu theo sau chưa được phủ, yêu cầu làm tròn/định dạng kết quả/đổi đơn vị hoặc hỏi số
     đo góc ⇒ `QUESTION_CONTEXT_UNSUPPORTED`.
   - Dữ kiện cùng câu đã xác minh vẫn phục vụ, kể cả "Tính thể tích …, biết SA = 3." và cạnh AB = 2 của đáy vuông cạnh 2.
   Engine tiếp tục sở hữu dựng hình và kiểm ràng buộc. Hai route A/B dùng chung cổng; LLM_ONLY mặc định không đổi.

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

Đường mặc định (`app.main`, `app.ai.pipeline`) không với tới các module trên — khoá ba lớp ở
`backend/tests/geometry/test_structured_geometry_relations.py::test_Y_*` (run `hybrid-pre-main-hardening`; thay guard
`test_Y_duong_mac_dinh_VAN_khong_tham_chieu_compiler`, vốn xanh sai vì `pipeline.py` nạp compiler qua `__import__` cắt
chuỗi): không nạp động trong mã sản phẩm · bao đóng import tĩnh chỉ với compiler qua cổng `routing` đã khai · module nạp
thật khi chạy `run_pipeline` ở `LLM_ONLY` ⊆ bao đóng tĩnh và không có module nào ở đây;
`app/simulation` không nhập `scene3d`/`simulation_state`. Giới hạn hiện tại: một mặt đáy; chóp/lăng trụ đứng; chưa có
song song, góc nhị diện tổng quát, thiết diện, khối tròn, đáy hình thoi/hình thang.
