# LƯỢT LIVE — một đề học sinh gửi thật (2026-08-25)

> Ba lượt trên **đường sản phẩm** (`run_pipeline(..., semantic_route="serve")`),
> `gemini-2.5-flash`, ~30 lượt LLM tổng. Không phải harness đo: không ép skill,
> không truyền miền, không tắt đoạn nào.

Đề do người dùng dán vào app và nhận **"NGOÀI DANH MỤC MÔ PHỎNG"**:

> *Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt
> phẳng đáy và SA=5. Gọi M, N lần lượt là trung điểm của SB, SD; P là trung điểm
> của AB. Hãy dựng mặt phẳng (PMN), xác định giao tuyến d của hai mặt phẳng
> (PMN) và (ABCD), đồng thời xác định giao điểm Q=d∩AD…*

---

## 1. Ba lượt, ba lỗi khác nhau — và cả ba đều là lỗi của HỢP ĐỒNG

| | Sau khi sửa gì | Chết ở đâu | Ai sai |
|---|---|---|---|
| **P1** | nối định tuyến miền + cổng bề mặt hai nửa | `semantic_program`, 3/3 lượt thử | **hợp đồng** |
| **P2** | thêm `intersect_line_line` | `semantic_program`, 3/3 lượt thử | **hợp đồng** |
| **P3** | thẻ văn phạm gọi đúng kiểu `list[str]` | **`served`** ✅ | — |

Không lượt nào thất bại vì mô hình hiểu sai đề. Cả ba lần nó viết ra thứ **đúng
về mặt hình học** và bị hợp đồng từ chối.

---

## 2. P1 — IR không có từ để nói "giao điểm hai đường thẳng"

Mô hình viết, ở **cả ba** lượt thử:

```json
{"kind": "intersect_line_line", "line_a": "d", "line_b": "AD"}
```

Đó chính xác là thứ đề hỏi (`Q = d ∩ AD`) và là dạng **cực phổ biến** của bài
thiết diện: dựng giao tuyến rồi cắt nó với một cạnh của đáy.

`kernel.intersect_line_line` **đã tồn tại từ đầu** — chính xác trên `Fraction`,
ném đúng khi hai đường chéo nhau hoặc song song. Chỉ tầng nối IR bỏ sót. Cùng
lớp với lỗ `distance` cho cặp đường–đường ở `GEOMETRY_CURRICULUM_COVERAGE §5`.

Nối xong lộ ra **bất biến #33 chưa có cổng**: thêm biểu thức vào `contract.py`
mà quên `validator._BIEU_THUC_HINH_HOC` thì validator trả *"không được hỗ trợ"*.
May là nó nổ to. May mắn không phải một cổng ⇒ đã thêm
`test_MOI_bieu_thuc_hinh_hoc_deu_co_NGUOI_THUC_THI`, và đã tiêm lỗi để thấy nó đỏ.

---

## 3. P2 — thẻ văn phạm của TA nói sai kiểu, mô hình làm theo

```
construct_plane: target_var:tên through:khối lệnh   ← through là list[str]!
```

`grammar_card._kieu` gọi **mọi** `list[…]` là `"khối lệnh"`. Nên ba TÊN ĐIỂM
được giới thiệu với mô hình như một thân câu lệnh, và nó làm đúng cái duy nhất
hợp lý: bọc giá trị lại.

```json
"through": {"kind": "literal", "value": ["A", "B", "C"]}
```

Cả ba lượt thử, cả ba trường `through` / `vertices` / `faces`. **Nhãn sai của ta
đẻ ra lỗi của nó.** Sửa: `list[str]` → `danh sách TÊN`, `list[list[…]]` →
`danh sách các danh sách`, còn `body`/`then_body` giữ nguyên `khối lệnh`.

---

## 4. P3 — chạy trọn

```
stage_reached  served     executable  true     servable  true
simulation_id  generic.semantic_program        source    semantic_program
scene3d        14 đối tượng · 10 sự kiện       khung 2D  10
```

| Đối tượng | Loại | Render |
|---|---|---|
| A B C D S P M N | `point3` | `point_marker` |
| `solid_S_ABCD` | `solid` | `mesh` |
| `plane_PMN` · `plane_ABCD` | `plane3` | `surface` |
| `line_d` · `line_AD` | `line3` | `line` |
| `point_Q` | `point3` | `point_marker` |

Toạ độ **hữu tỉ đúng**, kiểm tay: `A(0,0,0) B(4,0,0) C(4,4,0) D(0,4,0) S(0,0,5)`
khớp *"cạnh 4, SA = 5"*; `M = (2,0,5/2)` là trung điểm `SB`; `N = (0,2,5/2)`
trung điểm `SD`; `P = (2,0,0)` trung điểm `AB`. Cảnh có đủ `d` và `Q` — đúng hai
thứ đề yêu cầu xác định.

---

## 5. ⚠️ ĐIỀU LƯỢT NÀY **KHÔNG** CHỨNG MINH

**`so_nghia_vu = 0`.** Lượt `geometry_analyze` của P3 khai **tám dữ kiện, KHÔNG
nghĩa vụ nào** — trong khi P1 khai 3 và P2 khai 2 trên cùng đề ấy.

Hệ quả phải nói thẳng: C₁a/C₁b/C₂ **không có gì để kiểm**, và `servable=true` ở
đây nghĩa là *"chương trình chạy trọn và mọi thứ nó dựng đều lên được hình"*,
**không** phải *"đáp án đã được đối chiếu"*. Cảnh đúng — tôi kiểm tay — nhưng
**hệ không tự biết** nó đúng.

Đó đúng là chỗ luận điểm của đề tài mỏng nhất, và một lượt đẹp không được phép
che nó. `so_nghia_vu` dao động `3 → 2 → 0` trên **cùng một đề, cùng một prompt**
là một quan trắc về **độ ổn định của lượt đọc đề**, và nó thuộc về Phase 7.

**N = 1.** Ba lượt trên một đề. Không suy ra tỉ lệ nào.

**Hai yêu cầu trình bày của đề KHÔNG được phục vụ**: *"tô mặt phẳng bán trong
suốt"* và *"biểu diễn cạnh khuất bằng nét đứt"*. `RENDER_HINT` có bảy mục và
không mục nào là hai thứ đó — cảnh mô tả **hình được dựng thế nào**, chưa mô tả
**hình trông thế nào**.

---

## 6. Thu hoạch phụ: trần khai báo

Lượt thử đầu của P3 chạm `MAX_MEMORY_DECLARATIONS = 20`, lượt hai sửa được. Trần
cũ không **chặn sai** — nó thu một khoản thuế ~30 giây và một call cho gần như
mọi đề thiết diện, vì mỗi ĐIỂM là một khai báo (đề này cần 16). Đã nâng lên 32
kèm lý do và một test ghim con số.

---

## 7. Bản mã

`CACHE_VERSION 43` · pytest 2757 passed · vitest 1598 passed.
