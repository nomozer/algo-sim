# M17 W3-SIM — `binary.character_encoding` từ PARTIAL lên REAL_SIMULATION

**Ngày:** 2026-07-27 · **Nhánh:** `main` · **Phân loại:** CORE
**Audit trước:** `PARTIAL_SIMULATION` (`docs/evaluation/m17/simulation-authenticity/`)

---

## 1. Vấn đề audit chỉ ra

`runCharacterEncoding` gọi thẳng `toBase(codePoint, 2)` rồi **công bố** dãy bit:

> *"Đổi mã 65 sang nhị phân: 1000001."*

Đó là **tuyên bố**, không phải **dẫn xuất**. Trong khi `divideSteps()` — cơ chế
chia lấy dư có thật, có thuyết minh từng phép chia — đã nằm sẵn trong **chính
module mà W3 import**. Bước tra mã là mô phỏng thật; bước đổi cơ số thì không.

## 2. Đã sửa gì

| | |
|---|---|
| Cơ chế **dùng lại** | `divideSteps()` của `base_conversion` |
| Trích ra | `frontend/src/simulations/domains/binary/base-conversion.ts` — phần thuần tất định, **không** React/renderer/store |
| Bộ chuyển đổi thứ hai | **không có** — `convert-module.tsx` re-export chính hàm đó (test so **tham chiếu**, không so tên) |
| `toBase()` ở runtime W3 | **không còn** — chỉ dùng trong test hồi quy |
| Kết quả nhị phân | **dẫn ra từ chuỗi số dư**, không lấy từ đường thứ hai |

**`base_conversion` không đổi hành vi** — 41 test của nó vẫn xanh sau khi trích.

## 3. State model mới

`EncStepMeta` song ánh **1:1** với `trace.steps`:

```
charIndex · phase · detailed · division? · committed
division = { value, base, quotient, remainder, digit, stepIndex, collected[] }
```

Phase: `select_character → map_to_code → begin_conversion →
divide_step×n → read_remainders → commit_row` (ký tự chi tiết) ·
`… → convert_compact → commit_row` (ký tự rút gọn) · `complete`.

**Đã bỏ `floor((cursor + 1) / 4)`.** Công thức cũ đúng khi mỗi ký tự cố định 4
phase; số bước chia nay thay đổi theo giá trị mã nên số học trên cursor **sai**.
Renderer tra metadata theo cursor thay vì tự suy.

## 4. Bằng chứng phép chia là THẬT

Từ `visual/captures.json` — số do **engine trong trình duyệt** phát ra:

| Fixture | Bước | Phép chia | Số dư đã thu |
|---|---|---|---|
| `A` (65) | first_division | `65 : 2 = 32 dư 1` | `1` |
| `A` (65) | middle_division | `8 : 2 = 4 dư 0` | `1000` |
| `ế` (7871) | division_over_255 | `7871 : 2 = 3935 dư 1` | `1` |
| `Tin` → `T` (84) | first_char_detail | `21 : 2 = 10 dư 1` | `001` |

Chuỗi đầy đủ của `A`: **65 → 32 → 16 → 8 → 4 → 2 → 1**, 7 phép chia, số dư
`1 0 0 0 0 0 1`, đọc ngược ra `1000001`. Số bị chia **giảm thật** qua từng bước
và không lặp lại — không phải một bảng dựng sẵn rồi đổi highlight.

`7871` vượt xa trần **255 / 8 bit** của `decimal_to_binary` — đúng lý do W3 đi
đường `base_conversion`.

## 5. Chính sách rút gọn nhiều ký tự (§10) — và giới hạn phải nói rõ

- **Ký tự đầu tiên:** bung **đầy đủ** chuỗi chia.
- **Ký tự thứ hai trở đi:** engine vẫn chạy **cùng `divideSteps()`**, chỉ trình
  bày rút gọn và **nói thẳng**: *"Mã 105: áp dụng CÙNG quy tắc chia lấy dư cho 2
  qua 7 phép chia → 1101001."*

> **Giới hạn:** chi tiết phép chia **chỉ mở đầy đủ cho ký tự đầu tiên**. Không
> claim rằng mọi phép chia của chuỗi dài đều được bung. Lý do: 12 code point ×
> ~13 phép chia cho timeline vài trăm bước.

Có test khoá **không lệch kết quả** giữa đường chi tiết và đường rút gọn.
Timeline: `A` = **13 bước** · `Tin` = **21 bước**.

## 6. Chrome review

Chrome thật qua CDP, **12 ảnh** (desktop 11 · 768px 1). Harness dùng lại
`capture-w3-encoding.mjs`; mốc chụp nay **giải theo tên phase** thay vì chỉ số
cứng — mốc cũ (`["convert_to_binary", 2]`) trỏ vào phase không còn tồn tại.

| Fixture | Ảnh | Kết luận |
|---|---|---|
| SIM-ENC-1 `A` ascii | 5 + 1 (768px) | **REAL_SIMULATION** |
| SIM-ENC-2 `ế` unicode | 3 | **REAL_SIMULATION** |
| SIM-ENC-3 `Tin` ascii | 3 | **REAL_SIMULATION** |

**Emoji refusal:** dùng lại ảnh W3-VR — UI từ chối không đổi, chụp lại là lãng phí.

**Đo trong trình duyệt:** 0 rò token kỹ thuật (quét cả tên phase mới) · 0 phần tử
bị cắt · không tràn ngang ở mọi ảnh · controls nhìn thấy và bấm được.

### Lỗi CHỈ review ảnh mới thấy

**W3-SIM-VR1 — lặp kết luận.** Panel chia viết *"Đọc NGƯỢC từ dưới lên: 1000001
→ nhị phân là 1000001."* trong khi băng thuyết minh nói **y hệt**. Đây là **cùng
lớp lỗi W3-VR1 và W2C-VR3** — lần thứ ba. **Vá:** panel chỉ **đối chiếu hai
chiều đọc**; kết luận để một chỗ. Có test hồi quy.

### Giới hạn nhận, không sửa

1. **`A` = 65 = `1000001` là chuỗi đối xứng**, nên hai dòng "từ trên xuống" và
   "từ dưới lên" trông **giống hệt nhau** — đúng ở chỗ khó thấy nhất. Đây là
   trùng hợp của riêng giá trị 65, không phải lỗi (`T` = 84 → `0010101` vs
   `1010100` cho thấy rõ). Nếu cần một ví dụ demo thì **`T` tốt hơn `A`**.
2. **Learner action vẫn chỉ là điều khiển timeline** — chưa prediction/what-if.
   Mức tương tác giữ nguyên `TIMELINE_CONTROL`.
3. Chip domain vẫn hiện "HỆ CƠ SỐ" — giới hạn đã nhận từ W3-VR.

## 7. Claim đúng sau checkpoint

> Target `binary.character_encoding` mô phỏng quá trình ánh xạ ký tự sang code
> point và minh họa **chi tiết cơ chế chia lấy dư** để chuyển mã của **ký tự đầu
> tiên** sang nhị phân. Các ký tự tiếp theo áp dụng **cùng cơ chế** ở chế độ
> trình bày rút gọn.

**KHÔNG claim:** byte UTF-8 · toàn bộ Unicode · emoji · mọi phép chia của chuỗi
dài đều bung chi tiết · prediction/what-if · 3D · live LLM đã kiểm chứng.

## 8. Phân loại sau sửa

| Trục | Trước | Sau |
|---|---|---|
| Tính xác thực | `PARTIAL_SIMULATION` | **`REAL_SIMULATION`** |
| Tương tác | `TIMELINE_CONTROL` | `TIMELINE_CONTROL` *(không đổi)* |
| Thị giác | `2D` | `2D` *(không đổi)* |

Đủ điều kiện §15: cơ chế tra mã có state authoritative · cơ chế chia lấy dư có
state authoritative · timeline thể hiện **từng** phép chia · nhị phân **dẫn ra
từ số dư** · renderer không tự tính (test trace bịa `65 : 2 = 30 dư 5` buộc màn
hình hiện 30/5) · **ảnh Chrome chứng minh học sinh nhìn thấy cơ chế**.

## 9. Giới hạn khi trích dẫn

Đây là mô phỏng tất định + review thị giác **offline**. **Chưa chạy live LLM** —
chưa có bằng chứng Gemini sinh được `CharacterEncodingSpec` hợp lệ từ đề tiếng
Việt thật. Ảnh ở đây là **bằng chứng state engine đã chạy**, không phải hình
minh họa: không có ảnh nào do AI sinh.

**Part B (đối chiếu luận văn): `BLOCKED_NO_DOCX`** — chưa tạo
`thesis_evidence_crosswalk.md`.
