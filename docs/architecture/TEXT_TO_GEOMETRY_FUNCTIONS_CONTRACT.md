# Contract: Text-to-Geometry Functions & Kiến trúc Hybrid (`geometry-functions/14`, planner `geometry-fact-planner/15`, engine `geometry-function-engine/14`)

Contract **đang hiệu lực** của nền tảng hàm hình học và kiến trúc mục tiêu **Hybrid**
([`TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`](TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md),
[`HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](HYBRID_B_TARGET_ARCHITECTURE_DECISION.md),
[`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md),
[`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md)).
Sửa contract ⇒ wave mới + test. Bản v1 bất biến: `../evaluation/geometry/runs/text-to-geometry-functions/FUNCTION_REGISTRY_SPEC.md`.

> **Phiên bản `/12`–`/13` (Backend Hybrid Session 1–3, tích hợp ở run `hybrid-disabled-integration`):** số hàm và phân loại
> ở §2 không đổi. Phần thêm vào sống ở báo cáo của từng wave, không chép lại đây: chứng chỉ đỉnh thiết diện `DINH_CAT_CANH`
> và cổng nguồn dùng chung cho Adapter `/3` ([`HYBRID_BACKEND_TARGET_ARCHITECTURE.md`](HYBRID_BACKEND_TARGET_ARCHITECTURE.md),
> run `backend-hybrid-contract-unification`); canonical `typed-fact-next/2`, `bridge_v2`, Adapter `/4`, văn phạm nguồn G1–G7 và
> đỉnh cắt dẫn xuất `derived_fresh` có chứng chỉ khép kín
> ([`CONTRACT_V2_IMPLEMENTATION_REPORT.md`](../evaluation/geometry/runs/hybrid-contract-v2/CONTRACT_V2_IMPLEMENTATION_REPORT.md)).

> **Phân biệt AS-IS và TO-BE:**
> - **AS-IS (Tuyến sản phẩm mặc định hiện hành):** `DEFAULT_MODE = LLM_ONLY` (`CACHE_VERSION = 127`). Tuyến mặc định của
>   `/api/analyze` chưa chuyển sang **Hybrid** cho tới khi vượt qua đủ 20 cổng tại [`../MIGRATION_CHECKLIST.md`](../MIGRATION_CHECKLIST.md).
> - **TO-BE (Kiến trúc mục tiêu — Hybrid):** AI chỉ trích xuất JSON Typed Facts (`TypedFact` ở `fact_extraction.py`
>   `hybrid-semantic-extraction/3`, hoặc `TypedFactNext` ở `typed_fact_next.py` `typed-fact-next/1`), đi qua cổng kiểm
>   chứng nguồn **Semantic Grounding**, sau đó **Goal-Directed Construction Planner** tất định (`planner.py`,
>   `geometry-fact-planner/15`) tự chọn và phối hợp các **Geometry Functions** (`registry.py`, `geometry-functions/14`)
>   → **Compiler / Construction IR** → **Engine / Kernel** (`engine.py`, `geometry-function-engine/14`;
>   `adapter3_simulation.py`, `hybrid-simulation-adapter/3`) → **Scene3D**.
> - **Tuyến đối chứng trực tiếp (Baseline A):** AI gọi trực tiếp hàm dựng hình (`function_calling.py` →
>   `function_route.py`) chỉ giữ làm baseline đối chứng thực nghiệm.

```text
[Tuyến mục tiêu TO-BE — Hybrid]
đề tiếng Việt
   ──► AI trích xuất JSON Typed Facts                     backend/app/ai/fact_extraction.py (`hybrid-semantic-extraction/3`)
       (`TypedFact` / `TypedFactNext`)                    backend/app/simulation/geometry_functions/typed_fact_next.py (`typed-fact-next/1`)
   ──► Semantic Grounding & chuẩn hoá dữ kiện             backend/app/simulation/geometry_functions/planner.py (`geometry-fact-planner/15`)
   ──► Goal-Directed Construction Planner (tất định tự phối hợp lời gọi Geometry Functions)
   ──► lược đồ đóng · cổng nguồn 6 tầng (`kiem_nguon`)    backend/app/simulation/geometry_functions/registry.py (`geometry-functions/14`)
   ──► Engine: chuẩn hoá có tiền điều kiện · phụ thuộc · bố cục khung affine + Gram · kiểm MỌI dữ kiện
                                                          backend/app/simulation/geometry_functions/engine.py (`geometry-function-engine/14`)
   ──► IR SemanticProgram ──► interpreter + kernel dưới metric.using(G)
   ──► Scene3D + chart_metric (+ length_unit)             backend/app/ai/function_route.py · backend/app/ai/adapter3_simulation.py (`hybrid-simulation-adapter/3`)

[Tuyến đối chứng Baseline A — Direct Function Calling]
đề ──► AI (Gemini function calling, MỘT lượt/đề)          backend/app/ai/function_calling.py
   ──► lời gọi {fn, args, call_id, quotes[], depends_on[]} ──► registry.py ──► engine.py ──► Scene3D
```

## 1. Lời gọi

`{"id"|"call_id": "c1", "fn": <tên trong REGISTRY>, "args": {...}, "source": {"quotes": ["…nguyên văn…"]},
"depends_on": ["c0"]}`. Lược đồ đóng (`extra="forbid"`): không ô toạ độ, không hàm ngoài bảng, không mã. Nhãn
`^[A-Z][0-9]*'?$`; khối `S.ABC` / `ABC.A'B'C'`; số chính xác `4 · 2/3 · 1,5 · √3 · 3√3/4` hoặc theo ký hiệu
`a · 2a · a√3 · a√3/2 · 3a/2`. `depends_on` là khai báo phụ thuộc: treo ⇒ `DANGLING_DEPENDENCY`, vòng ⇒ `DEPENDENCY_CYCLE`;
engine tự tính thứ tự dựng, không tin khai báo ấy.

## 2. Thư viện hàm (`geometry-functions/14` — 37 hàm trong `REGISTRY`)

Danh sách đồng bộ trực tiếp theo mã nguồn tại `backend/app/simulation/geometry_functions/registry.py`
(`REGISTRY_VERSION = "geometry-functions/14"`, `PLANNER_VERSION = "geometry-fact-planner/15"`,
`ENGINE_VERSION = "geometry-function-engine/14"`):
- Tổng số hàm đăng ký trong `REGISTRY`: **37 hàm** (`11` hàm `fact`, `12` hàm `construct`, `11` hàm `ask`, `1` hàm `escape`).
- Trong đó **31 hàm** có `provider_offered = True` (30 hàm trong `PROVIDER_FUNCTIONS` cho bề mặt function-calling đối chứng +
  `translate_point` có `auxiliary_only = True` chỉ dành cho Planner), và **4 hàm** có `provider_offered = False`
  (`divide_segment`, `ask_angle_lines`, `ask_volume_ratio`, `ask_residual_volume`) được biên dịch tất định từ
  Typed Facts qua `planner.py` / `engine.py` để giữ nguyên vân tay bề mặt khai báo hàm của Baseline A
  (`test_hybrid_goal_decomposition.py::test_provider_surfaces_are_pinned`). `PlanningContract` chỉ là metadata nội bộ,
  không vào khai báo hàm.

| nhóm | hàm (`provider_offered = True`) | hàm nội bộ tuyến Hybrid / Planner (`provider_offered = False` hoặc `auxiliary_only = True`) |
|---|---|---|
| dữ kiện (`fact`, 11) | `regular_polygon` · `rectangle` · `right_angle` · `segment_length` · `equal_length` · `height` · `perpendicular_line_plane` · `perpendicular_lines` · `altitude` · `orthogonal_projection` · `face_perpendicular_base` | — |
| dựng (`construct`, 12) | `midpoint` · `centroid` (tam giác) · `pyramid` · `regular_pyramid` · `prism` · `orthogonal_projection_line` · `intersect_line_line` · `intersect_line_plane` · `section` (thiết diện khối × mặt qua ba điểm có tên) · `intersection_line` (giao tuyến hai mặt) | `translate_point` (`auxiliary_only = True`) · `divide_segment` (`provider_offered = False`, chia đoạn theo tỉ số dương) |
| hỏi (`ask`, 11) | `ask_volume` · `ask_area` · `ask_section_area` · `ask_length` · `ask_distance_point_plane` · `ask_distance_lines` · `ask_angle_line_plane` · `ask_angle_plane_plane` (góc trả `cos²`; đề hỏi `"số đo (của) góc"` hoặc theo `độ`/`radian` ⇒ `QUESTION_CONTEXT_UNSUPPORTED`) | `ask_angle_lines` (`provider_offered = False`, góc giữa hai đường thẳng) · `ask_volume_ratio` (`provider_offered = False`, tỉ số thể tích hai khối, Wave 3A) · `ask_residual_volume` (`provider_offered = False`, thể tích phần còn lại có chứng chỉ bao hàm, Wave 3A) |
| thoát (`escape`, 1) | `unsupported` ⇒ `OUT_OF_SCOPE` | — |

**Hàm chỉ dành cho planner** (run `goal-directed-section-planning`, mở rộng ở `two-line-plane-section`): `translate_point` (`auxiliary_only`) — ảnh của
một điểm qua phép tịnh tiến theo vectơ hai điểm đã có. Không khai cho provider (tuyến A vẫn đúng 30 hàm trong
`PROVIDER_FUNCTIONS`), chỉ hợp lệ trong các phân rã mặt phẳng đã đăng ký của Planner (`MAT_SONG_SONG`, mặt phẳng qua một
đường và song song đường kia, hoặc hai đường cắt nhau/song song theo [`TWO_LINE_PLANE_SECTION_CONTRACT.md`](TWO_LINE_PLANE_SECTION_CONTRACT.md)):
biểu thức IR `vector_from_points` + `translate`, không thêm primitive mới. Engine kiểm: song song (Q), không trùng (Q)
(`DERIVED_PLANE_IS_REFERENCE`), không là mặt biên (`SECTION_PLANE_IS_FACE`); hàm phụ ngoài phân rã ⇒ `AUXILIARY_ONLY_FUNCTION`.

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

6. **Ngữ cảnh yêu cầu & văn phạm câu hỏi dùng chung** (runs `question-local-givens`, `shared-ask-grammar-safety`,
   `source-gate-hardening`): sau khi mọi lời gọi vượt cổng nguồn thường, `_kiem_du_kien_cau_hoi` và `_kiem_vung_tien_de`
   kiểm toàn bộ câu hỏi, mệnh đề mục tiêu/phép dựng đứng trước động từ hỏi, việc kế tiếp, câu theo sau và câu ghi chú.
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
   Engine tiếp tục sở hữu dựng hình và kiểm ràng buộc. Hai route (Baseline A và **Hybrid**) dùng chung cổng; `LLM_ONLY` mặc định không đổi.

## 4. Engine (`geometry-function-engine/14`)

- **Mặt phẳng câu hỏi gọi bằng nhiều nhãn** (run `hybrid-v2-backend-generalization`): mục tiêu `/2` `distance`/`angle` nêu
  mặt bằng ≥ 3 nhãn phân biệt — (ABCD), (BCC′B′). Mọi nhãn tới engine (lời gọi khoảng cách giữ ô ba nhãn của registry;
  nhóm đầy đủ đi qua `KeHoach.named_planes`); `chon_ba_mat` đo qua bộ ba KHÔNG thẳng hàng đầu tiên của cả nhóm (thứ tự
  viết không bao giờ gây từ chối), `kiem_mat_viet` kiểm mọi nhãn đồng phẳng (`SOURCE_OBJECT_MISMATCH`, kể cả khi mọi điểm
  thẳng hàng), lệnh IR của mặt mang tên đầy đủ (`label`) ⇒ học sinh thấy (BCC′B′), không phải (BCC′). Mục tiêu
  `{point, line}` đi vào phân rã điểm–đường sẵn có (chân trên nhãn phụ mới, `orthogonal_projection_line`).
- **Độ dài** (`do_dai`): `segment_length`, lớp `equal_length`, hình đã dựng, cạnh khác của đa giác đều; hai nguồn lệch ⇒
  `INCONSISTENT_FACTS` nêu đủ lời gọi.
- **Bố cục đáy** (khung 2D + Gram G₂ hữu tỉ): đa giác đều k ∈ {3, 4, 6} (khác ⇒ `UNSUPPORTED_REGULAR_POLYGON`), hình chữ
  nhật, hình bình hành / hình thoi / hình thang vuông hoặc cân khi đủ kích thước xác định, tam giác theo ba cạnh hoặc hai
  cạnh + góc vuông; khác ⇒ `UNSUPPORTED_BASE_SHAPE`. G = G₂ ⊕ h²; đỉnh ngoài đáy ở z = 1 (hoặc hệ trục nhiều khối chung mặt
  theo [`COMPOSITE_GEOMETRY_CONTRACT.md`](COMPOSITE_GEOMETRY_CONTRACT.md)).
- **Chuẩn hoá có tiền điều kiện** — ba cách nói về đường vuông góc mặt phẳng thành MỘT ràng buộc:
  `perpendicular_line_plane` (chân = đầu mút trên mặt); `altitude` (đỉnh phải là đỉnh của chính khối chóp, chân trên đáy);
  `orthogonal_projection` (ảnh ≠ điểm, ảnh trên mặt). Hỏng ⇒ `PRECONDITION_FAILED` / `FOOT_NOT_IN_PLANE`.
  `perpendicular_lines`: ⊥ HAI đường không song song trong đáy, đầu kia thuộc đáy ⇒ ⊥ đáy (định lý); một đường ⇒ chưa xác định.
- **Mặt bên ⊥ đáy**: một đỉnh ngoài đáy + hai đỉnh đáy; chân F trên AB **dẫn xuất** t = (SA² − SB² + AB²)/(2AB²),
  h² = SA² − t²AB² (≤ 0 ⇒ `INCONSISTENT_FACTS`; thiếu SA/SB ⇒ `MISSING_DIMENSION`).
- **Độ dài ký hiệu**: mọi độ dài theo a ⇒ dựng ở a = 1 (bước `choose_unit`, `LAYOUT_DERIVED`, không phải dữ kiện), đáp số =
  hệ số · a^bậc (thể tích 3, diện tích 2, độ dài/khoảng cách 1, góc 0); trộn a với số ⇒ `NON_HOMOGENEOUS_LENGTHS`.
- **Tỉ số thể tích & thể tích phần còn lại** ([`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md)): chứng chỉ bình
  phương thể tích hữu tỉ (`_the_tich2_khoi`), kiểm bao hàm nửa không gian ngoài và mặt biên chung (`_mat_ngoai_khoi` ⇒
  `RESIDUAL_CONTAINMENT_UNPROVED` khi không chứng minh được).
- **Không suy chân mặc định**: điểm không có luật xác định ⇒ `UNDERDETERMINED_POINT`.
- **Kiểm**: mọi dữ kiện kiểm lại chính xác dưới G (mặt ⊥ mặt bằng n₁ᵀG⁻¹n₂ = 0). Lời gọi engine đã dùng mà sai ⇒
  `ENGINE_SELF_CHECK_FAILED`; còn lại ⇒ `INCONSISTENT_FACTS`. Điểm kernel thực thi phải trùng bố cục.

## 5. Adapter Gemini (offline ở `ai-function-route` & `fact_extraction.py`)

- **Tuyến Hybrid (`fact_extraction.py`, `hybrid-semantic-extraction/3`):** Một lượt `generateContent`/đề với JSON Schema đóng
  (`RESPONSE_CONTRACT = "flat"`); chuẩn hoá và kiểm chứng nguồn trước khi chuyển cho `planner.py` (`geometry-fact-planner/15`).
  Với hợp đồng mở rộng hướng mô phỏng (`typed-fact-next/1`), `adapter3_simulation.py` (`hybrid-simulation-adapter/3`) biên
  dịch sang `Scene3D` có kiểm chứng (xem [`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md)).
- **Tuyến đối chứng Baseline A (`function_calling.py`):** Một `generateContent`/đề; `tools.functionDeclarations` dẫn xuất từ
  `REGISTRY` (tập con OpenAPI, Type viết hoa, không `$ref`/`anyOf`); `toolConfig.functionCallingConfig = {mode: ANY | VALIDATED, allowedFunctionNames}`;
  `maxOutputTokens` là trần cứng (gồm thinking). Phản hồi: `MAX_TOKENS` ⇒ `RESPONSE_TRUNCATED` (không thực thi kế hoạch cụt);
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
`app/simulation` không nhập `scene3d`/`simulation_state`. Phạm vi năng lực đã mở rộng theo từng đợt (thiết diện qua mặt
phẳng song song / hai đường thẳng, hình hộp / lập phương, đáy hình bình hành / hình thoi / hình thang, tổ hợp đa khối, tỉ số
thể tích và thể tích phần còn lại, cùng đường `TypedFactNext` + `Adapter /3` cho đỉnh thiết diện không tên và khối tròn xoay)
được định nghĩa tại [`TWO_LINE_PLANE_SECTION_CONTRACT.md`](TWO_LINE_PLANE_SECTION_CONTRACT.md),
[`GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md`](GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md),
[`COMPOSITE_GEOMETRY_CONTRACT.md`](COMPOSITE_GEOMETRY_CONTRACT.md),
[`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md) và
[`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md).
