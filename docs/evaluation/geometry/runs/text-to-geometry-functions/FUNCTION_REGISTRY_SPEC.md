# Đặc tả thư viện hàm và hợp đồng AI → lời gọi hàm (`geometry-functions/1`, engine `geometry-function-engine/1`)

Mã: `backend/app/simulation/geometry_functions/` (`registry.py`, `engine.py` — dựng, kiểm, thực thi) +
`backend/app/ai/function_route.py` (điểm vào, bày Scene3D: tầng `app/simulation` không nhập `scene3d`). Điểm vào:
`run_function_route(problem_text, {"calls": [...]}) → KetQuaTuyen`. Khai báo function calling cho mô hình: `function_declarations()`. Đây là contract của
**nhánh nghiên cứu**; khi được chấp nhận làm đường chính, bản này chuyển sang `docs/architecture/`.

## 1. Hình dạng một lời gọi

```json
{"id": "c2", "fn": "perpendicular_line_plane",
 "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
 "source": {"quote": "SA vuông góc với (ABC)"}}
```

Lược đồ **đóng** (`extra="forbid"` ở mọi tầng): không ô toạ độ, không hàm ngoài bảng, không mã. Nhãn điểm `^[A-Z][0-9]*'?$`
(`’`, `′` chuẩn hoá thành `'`). Số `ExactNumber`: `4`, `2/3`, `1,5`, `√3`, `2√3`, `3√3/4` — không float.

## 2. Bảng hàm

| hàm | loại | đối số | vị từ phải có trong quote | ô số neo quote |
|---|---|---|---|---|
| `regular_polygon` | fact | `vertices` (≥3, theo vòng), `side?` | `đều` \| `hình vuông` | `side` |
| `rectangle` | fact | `vertices` (4) | `hình chữ nhật` | — |
| `right_angle` | fact | `vertex`, `rays` (2) | `vuông` | — |
| `segment_length` | fact | `segment` (2), `value` | — | `value` |
| `perpendicular_line_plane` | fact | `line` (2), `plane` (≥3) | `vuông góc` \| `⊥` | — |
| `height` | fact | `solid` (ký hiệu khối), `value` | `cao` | `value` |
| `midpoint` | construct | `point`, `segment` (2) | `trung điểm` | — |
| `pyramid` | construct | `apex`, `base` (≥3) | `chóp` \| `tứ diện` | — |
| `regular_pyramid` | construct | `apex`, `base` | (`chóp` \| `tứ diện`) **và** `đều` | — |
| `prism` | construct | `base`, `top` (cùng thứ tự), `right` | `lăng trụ` \| `hình hộp`; `right=true` cần thêm `đứng` \| `đều` \| `hình hộp` | — |
| `ask_volume` | ask | `solid` | `thể tích` | — |
| `ask_length` | ask | `segment` | `độ dài` \| `tính` \| `tìm` | — |
| `ask_distance_point_plane` | ask | `point`, `plane` (3) | `khoảng cách` | — |
| `ask_angle_line_plane` | ask | `line`, `plane` | `góc` | — (trả `cos²`) |
| `ask_area` | ask | `polygon` | `diện tích` | — |
| `unsupported` | escape | `reason` | — | — |

Từ khoá là **điều kiện cần**, không là bộ hiểu ngữ nghĩa: chúng chặn AI khai một quan hệ mà đoạn trích không nói tới
(ca G3), không chứng minh đoạn trích nói đúng quan hệ ấy.

## 3. Cổng nguồn (`kiem_nguon`) — thứ tự kiểm, theo id lời gọi

1. `QUOTE_NOT_IN_SOURCE` — quote (đã chuẩn hoá NFC, khoảng trắng, dấu phẩy trên) không nằm nguyên văn trong đề.
2. `UNKNOWN_LABEL` — nhãn trong đối số không phải nhãn của đề (nhãn lấy từ các từ toàn chữ HOA: `S.ABC`, `(ABC)`, `SA`).
3. `NEGATED_CLAUSE` — quote chứa `không phải`, `không là`, `không vuông góc`, `không đều`, `không song song`, `chưa chắc`.
4. `PREDICATE_NOT_IN_QUOTE` — thiếu từ khoá vị từ của hàm.
5. `AMBIGUOUS_VALUE_QUOTE` — lời gọi mang số nhưng quote chứa ≠ 1 số (chữ số dính nhãn như `A1` không tính).
6. `UNGROUNDED_VALUE` — số trong đối số khác số duy nhất của quote (so CHÍNH XÁC theo bình phương).

`unsupported` chỉ qua bước 1–2 rồi làm cả kế hoạch `OUT_OF_SCOPE`.

## 4. Engine — luật dựng

- **Khối.** `pyramid` / `regular_pyramid` / `prism` tạo khối tên `S.ABC` / `ABC.A'B'C'`. Mọi khối phải chung **một** tập
  đỉnh đáy (`UNSUPPORTED_MULTIPLE_BASES`). Không khối ⇒ `NO_SOLID`. `height`/`ask_volume` tới khối chưa dựng ⇒ `UNKNOWN_SOLID`.
- **Bố cục đáy** (khung 2D + Gram G₂, hữu tỉ):
  - `regular_polygon` k ∈ {3, 4, 6}: khung chuẩn affine, G₂ = s²·{[[1,½],[½,1]], I, [[1,−½],[−½,1]]}; k khác ⇒
    `UNSUPPORTED_REGULAR_POLYGON` (cos 2π/k vô tỉ). Cạnh lấy từ `side` hoặc từ `segment_length` trên một cạnh.
  - `rectangle`: khung đơn vị, G₂ = diag(a², b²) từ hai cạnh kề.
  - tam giác không khai hình: ba cạnh² từ `segment_length` + `right_angle` (Pythagore khi biết hai trong ba); G₂ theo định
    lý cos (hữu tỉ). Thiếu ⇒ `MISSING_DIMENSION`; không xác định dương ⇒ `INCONSISTENT_FACTS`.
  - đáy khác ⇒ `UNSUPPORTED_BASE_SHAPE`.
- **Trục thứ ba.** G = G₂ ⊕ (h²): e₃ vuông góc đáy theo metric. Đỉnh ngoài đáy ở z = 1 (h có thể vô tỉ, toạ độ vẫn ℚ).
  Hai độ cao độc lập có tỉ số không là bình phương hữu tỉ ⇒ `UNSUPPORTED_MULTIPLE_HEIGHTS`.
- **Phụ thuộc** (mỗi vòng đặt MỘT điểm, ưu tiên cố định, thứ tự chính tắc theo nội dung lời gọi):
  1. `midpoint` khi hai đầu đã có (kernel dựng bằng phép `midpoint` của IR, không khai toạ độ);
  2. `regular_pyramid`: tâm đáy (`O`, hoặc `I`/`O1` nếu đề đã dùng `O`) rồi đỉnh trên tâm — chỉ khi đáy được khai đa
     giác đều, nếu không `REGULAR_PYRAMID_NEEDS_REGULAR_BASE`;
  3. `perpendicular_line_plane`: mặt phẳng phải là mặt đáy (`UNSUPPORTED_PLANE`); chân = đầu mút **nằm trên đáy**; đầu mút
     ngoài đáy đã đặt ⇒ `FOOT_NOT_DETERMINED`; chân chưa dựng (vd trung điểm) ⇒ đợi vòng sau;
  4. `prism` với `right=true`: đáy trên = đáy dưới + e₃. `right=false` không có luật ⇒ đỉnh trên không xác định.
  - h² theo thứ tự: độ dài đoạn đỉnh–chân → `height` của khối → độ dài đỉnh tới một điểm đáy khác (h² = L² − |chân–điểm|²,
    ≤ 0 ⇒ `INCONSISTENT_FACTS`); không có ⇒ `MISSING_DIMENSION`.
  - Điểm cần (đỉnh khối, đối số `ask_*`, `segment_length`, `right_angle`, `perpendicular_line_plane`) chưa đặt được ⇒
    `UNDERDETERMINED_POINT`. **Không có chân mặc định**: không bao giờ tự đặt đỉnh trên tâm hay trên một đỉnh.
- **Kiểm** — MỌI lời gọi fact/construct được kiểm lại chính xác trên bố cục dưới G (độ dài², tích vô hướng, khoảng cách²
  điểm–mặt bằng định thức Gram). Lời gọi engine **đã dùng** để dựng mà sai ⇒ `ENGINE_SELF_CHECK_FAILED` (lỗi engine); lời
  gọi khác sai ⇒ `INCONSISTENT_FACTS` (đề mâu thuẫn), lý do liệt kê id + quote.
- **Thực thi.** IR qua `validate_semantic_program` (`ENGINE_IR_INVALID`), `hoan_thien_dung_hinh`, interpreter dưới
  `metric.using(G)` (`ENGINE_EXECUTION_FAILED`); điểm kernel phải trùng bố cục (`kernel_check`). Đáp số chính xác
  (`4√3`, `12/5`, `cos²=5/14`).
- **Xuất xứ trong trace.** `LAYOUT_DERIVED` (engine chọn khung / đặt theo luật), `DERIVED` (trung điểm, tâm, khối, phép đo);
  mỗi bước mang id lời gọi đã dùng. Không có `GIVEN` toạ độ nào; dữ kiện đề chỉ vào qua đối số có quote.

## 5. Giới hạn đã biết (v1)

Một mặt đáy; chỉ chóp/lăng trụ đứng; đa giác đều 3/4/6, hình chữ nhật, tam giác xác định bởi cạnh/góc vuông; độ dài ký hiệu
(`a`) chưa hỗ trợ; quan hệ khác (song song, mặt bên vuông góc đáy, góc nhị diện, thiết diện, hình chiếu tổng quát, khối
tròn) chưa có hàm ⇒ từ chối trung thực. Từ khoá vị từ là kiểm cần, không đủ. Chuỗi lời gọi đang do fixture cung cấp —
chưa đo AI thật.
