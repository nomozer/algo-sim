# GEOMETRY SEMANTIC GENERATION — báo cáo đóng vòng

> Gộp năm báo cáo yêu cầu ở Phase 7 thành **một** tài liệu. Tách năm file cho
> cùng một wave sẽ chép trùng ~60 % nội dung, và ba tuần sau không ai biết bản
> nào là bản đúng.
>
> Trạng thái: **Phase 0–4 XONG · Phase 5 CHƯA CHẠY** (cần API thật + duyệt).

---

## 0. GAP REPORT — hiện trạng trước wave này

| Thành phần | Trước | Sau |
|---|---|---|
| Geometry IR (6 kiểu, 8 phép) | ✅ có từ Bước 3 | không đổi |
| **Obligation taxonomy hình học** | ❌ **0** | ✅ **8** |
| **Checker** | ❌ 0 | ✅ **8, không cái nào mức yếu** |
| **Oracle độc lập** | ✅ có (bất biến + phân rã khác) | mở rộng |
| **Prompt hình học** | ❌ không một chữ | ✅ `geometry_program_generator.md` |
| **DEV set** | ❌ không có | ✅ 10 bài |
| Kết quả sinh thật | ❌ **0/0 — chưa thử lần nào** | ❌ **vẫn 0/0** |

Dòng cuối là dòng quan trọng nhất: wave này **chưa** tạo ra bằng chứng AI sinh
được. Nó tháo xong **cái chặn** để bằng chứng ấy đo được.

---

## 1. OBLIGATION LAYER — 8 nghĩa vụ

| Nghĩa vụ | Chủ thể hợp lệ | Checker gọi gì |
|---|---|---|
| `point_on_line` | `line3` | `P.point_on_line` |
| `point_on_plane` | `plane3` | `P.point_on_plane` |
| `parallel` | `line3` · `plane3` | `parallel_lines` / `parallel_planes` / `parallel_line_plane` |
| `perpendicular` | `line3` · `plane3` | `perpendicular_lines` / `line_perpendicular_plane` |
| `coplanar` | `polygon3` · `solid` | `P.coplanar` |
| `distance` | `point3` · `line3` · `plane3` | `M.distance_sq_*`, so trên **d²** |
| `angle` | `line3` · `plane3` | `M.cos_sq_*`, so trên **cos²** |
| `volume` | `solid` | `M.volume_tetrahedron`, phân rã |

### Ba quyết định thiết kế, và lý do

**Tách `point_on_line` khỏi `point_on_plane`** thay vì gộp `incidence`: hai cái
nhận **chủ thể khác nhau**. Gộp thì bảng kiểu mất tác dụng và một đề hỏi *"M có
thuộc (SBC)"* sẽ lọt khi LLM gắn nhầm vào một đường thẳng.

**Cả tám đều có checker server-owned — không cái nào ở mức yếu.** Đây là khác
biệt **bản chất** so với miền Tin học, nơi `predicate_verdict` phải để mức yếu
suốt nhiều tháng vì kiểm nó đòi **cài lại chính thuật toán đang kiểm**. Ở hình
học, kiểm là một **phép tính giải tích** (`u·v == 0`) — không phải một lời giải.
Tính độc lập không mất.

**So sánh làm trên bình phương.** `distance` so `d²`, `angle` so `cos²θ` — hai
đại lượng gốc vô tỉ, bình phương của chúng hữu tỉ. Lấy căn rồi so là đưa sai số
float quay lại qua cửa sau.

### Bẫy đã khoá bằng test

- **`d ⊥ (P)` ⇔ phương của `d` CÙNG PHƯƠNG pháp tuyến**, không phải `dot == 0`.
  Một đường **nằm trong** mặt phẳng cũng có `dot == 0` với pháp tuyến.
- **Nằm trong ≠ song song**: `parallel_line_plane` đòi đường **không** nằm trong
  mặt. Gộp là mất một kết luận toán học.
- **Không khai giá trị ⇒ không báo sai.** Nghĩa vụ `distance` thiếu
  `params.value` chỉ kiểm được cấu trúc; báo lệch ở đó là **bắt oan**.

---

## 2. ORACLE — độc lập, và độc lập chứng minh được

`docs/evaluation/geometry/custodian/geometry_oracle.py` · chỉ `import fractions`.

**Hai chiến lược theo bản chất câu hỏi**: thiết diện kiểm **6 bất biến, không
dựng lại**; thể tích dùng **phân rã khác** (kernel chia quạt từ đỉnh chóp, oracle
chia tứ diện từ một điểm trong).

**Ba mức, chỉ mức 3 là bằng chứng**: không import mã sản phẩm (soi bằng `ast`) ·
khớp trên bài kiểm tay (**cần, chưa đủ**) · **tiêm lỗi vào kernel thì oracle bắt
được**. Bốn phép tiêm, cộng hai ca ranh giới chống **bắt oan**.

> Mức 2 một mình không chứng minh gì: hai bản cài cùng một lỗi sẽ khớp hoàn hảo
> và cùng sai.

**Ranh giới với C₂**: `geometry_obligations.py` là cổng **nội bộ** — hỏi *"chương
trình có tự mâu thuẫn với nghĩa vụ nó tự khai không"*. Oracle hỏi câu khác:
*"kết quả có khớp ground truth do người ngoài dựng không"*. Gộp hai tầng là mất
tính độc lập.

---

## 3. PROMPT DESIGN

`skills/geometry_program_generator.md` · 4 638 byte · ngân sách 4 800.

**Không sửa một chữ nào của prompt Tin học** — chúng vẫn là bề mặt thật của lượt
SEALED #1, và số `A 3/40` gắn với chúng.

Prompt dạy đúng bốn thứ **không mã hoá được vào schema**:

1. **Luật số một: bạn KHÔNG tính toán.** Kèm ví dụ đối chiếu đúng/sai. Cám dỗ
   tự điền toạ độ ở miền này **mạnh hơn hẳn** miền thuật toán — model *biết*
   giao tuyến là gì và rất muốn nói ra.
2. **Đặt hệ toạ độ.** Đề hình học **không cho toạ độ**; chọn hệ là nửa khó của
   bài. Không dạy thì model chọn tuỳ tiện rồi ra số vô tỉ mà `Fraction` từ chối.
3. **Bảng "đề hỏi gì → nghĩa vụ nào"** cho 8 nghĩa vụ.
4. **Vuông góc với mặt phẳng** — chỗ lộn dấu kinh điển.

⚠️ **Ngân sách prompt KHÔNG phải chỗ thêm luật mỗi lần một ca hỏng.** Bằng
chứng lượt #1: **30/40 thất bại do hợp đồng cứng nhắc, không phải do prompt**
(`RULES §3c` gọi vá-prompt-theo-ca là DEEP_HARDENING). Khi hỏng: sửa **hợp đồng**
trước.

---

## 4. DEV DATASET — 10 bài

`docs/evaluation/geometry/dev/cases.json`

**Tên gọi là một phần của kỷ luật.** Đây là `geometry_generation_dev_set`,
**không phải benchmark**. Tập tự khai: *"số của nó KHÔNG BAO GIỜ là số held-out
của luận văn"*. Held-out phải do **custodian** chọn bằng **seed của GVHD**, đúng
quy trình SEALED của miền Tin học.

Phủ đủ **8/8 nghĩa vụ** qua 10 bài — thiếu một nghĩa vụ nghĩa là checker của nó
chưa từng được đề nào chạm tới.

Ba luật soạn, có test khoá:
- **Đề không rò toạ độ** — rò thì model khỏi phải đặt hệ, tỉ lệ đẹp và vô nghĩa.
- **Đáp án kiểm TAY**, không chạy hệ rồi chép (bẫy tautology đã gặp ở
  `cross_domain_matrix`).
- **Giá trị khai bằng phân số**, không thập phân.

---

## 5. KẾT QUẢ SINH — **CHƯA CHẠY**

Phase 5 cần **API thật** và **duyệt ngân sách**. Chưa chạy nên **chưa có số**,
và tài liệu này cố ý **không** để chỗ trống nào trông như đã có số.

Khi chạy sẽ ghi: `G1` (cú pháp) · `G2` (ngữ nghĩa) · `A` (chạy trọn) · `O`
(oracle). Không ghi `B` — `servable` cần cổng assurance đầy đủ; và không ghi `V`
— chưa có renderer.

Ước lượng ngân sách: 10 bài × 13 lượt logic = **130**, thực tế nhiều khả năng
40–70.

> **Điều duy nhất được nói lúc này**: hệ đã **đủ điều kiện** để đo *"AI sinh
> Geometry Program đúng"*. Chưa được nói nó **làm được**.

---

## 6. Nguồn tham khảo hình ảnh — chưa dùng

Phase 6 cho phép dùng hình SGK / GeoGebra / Wikimedia để đối chiếu **cách biểu
diễn**, không làm ground truth. Wave này **không dùng hình nào** — mọi đáp án
đến từ tính tay trên hệ toạ độ, và ba lớp bài đã chọn (chóp đáy vuông) đủ đơn
giản để không cần tra hình.

Khi cần (lúc làm renderer), lưu kèm **source · license · purpose**.

---

## 7. Kỷ luật giữ nguyên

`CURRICULUM_SUPPORT_PARTIAL` và `LEARNER_IMPACT_NOT_EVALUATED` **không đổi** —
mở taxonomy không sinh thêm bằng chứng. Số SEALED #1 của miền Tin học
(`A 3/40 · B 1/40`) vẫn là kết quả thật và vẫn trích được.

**Taxonomy 11 → 19 nghĩa vụ.** Chín kind cũ **giữ nguyên, không đụng**. Tám kind
mới là taxonomy của một **miền mới**, không phải bản nới của miền cũ — câu hỏi
bắt buộc của `test_taxonomy_frozen` (*"từ DEV hay từ một ca SEALED?"*) ở đây trả
lời: **không phải cả hai, đề tài đã đổi**.
