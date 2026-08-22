# GROUND TRUTH AUDIT — SEALED 40 case

## Phương pháp

Ground truth tính bằng **Python thuần**, deterministic, trong một file duy nhất:

```
docs/evaluation/semantic-benchmark/custodian/sealed_ground_truth.py
```

Vì sao tính bằng máy chứ không tính tay: 40 đáp án tính tay là 40 cơ hội sai số
học, và một đáp án sai sẽ **âm thầm chấm hệ là SAI trong khi nó ĐÚNG** — sai
lệch đó đi thẳng vào con số chính của luận văn.

## Dependency audit

Toàn bộ `import` của solver:

```python
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
```

Chỉ có thư viện chuẩn. Solver **không** phụ thuộc:

| | |
|---|---|
| `backend/app` production route | ✗ không import |
| `SemanticProgramInterpreter` | ✗ không import |
| production checker (`postconditions`, `coverage_gate`, `grounding_gate`) | ✗ không import |
| production renderer / visual adapter | ✗ không import |
| semantic-program generation code (`pipeline`, `contract`, `validator`) | ✗ không import |

Kiểm lại bất cứ lúc nào:

```bash
grep -nE "^\s*(import|from)\s" sealed_ground_truth.py
grep -nE "backend|app\.|SemanticProgram|interpreter|checker|renderer" sealed_ground_truth.py
```

Lần chạy audit: dòng thứ hai chỉ khớp **văn bản trong docstring**, không khớp
một câu lệnh nào.

## Số liệu

| | |
|---|---|
| N ground truth | **40** |
| Case có `expected` (chấm được) | **31** |
| Case `expected` rỗng (UNGRADED) | **9** |

## Hai loại case, khai rõ để kiểm toán

**ĐỀ CÓ DỮ LIỆU** — sách cho sẵn số liệu và/hoặc đáp án; ground truth tính
thẳng từ đó. Ví dụ: `T10-C5-062` (`"abababab".find("ab",4)`), `T10-C5-079`
(merge_str với ví dụ in trong sách), `T11CS-C6-027` (bảng điểm trang 98).

**ĐỀ TRỪU TƯỢNG** — sách viết "nhập từ bàn phím", không có dữ liệu cụ thể.
Custodian **cụ thể hoá** dữ liệu và ghi rõ trong `ground_truth.provenance` của
từng case; đề gốc được giữ nguyên ở `source.problem_text_goc` để đối chiếu.
Ví dụ: `T10-C5-039` (dãy 3 8 1 10 7 4), `T10-C5-076` (m = 10, n = 30),
`T10-C5-104` (P₀ = 600 N, Mặt Trăng g = 1,62).

## Chín case UNGRADED — vì sao, và vì sao đó là câu trả lời trung thực

Taxonomy nghĩa vụ có **đúng 9 loại** và cố ý **không** có `predicate_verdict`
(lý do ghi trong `obligations.py`: kiểm một phán quyết kiểu "dãy ngoặc có hợp lệ
không" đòi cài lại chính thuật toán đang kiểm, nên oracle mất tính độc lập).

Bịa một nghĩa vụ gần đúng rồi chấm theo nó thì con số thu về không còn nghĩa.
Nên `expected` để rỗng, và runner đếm chúng là `UNGRADED`, **tách hẳn khỏi tử số
lẫn mẫu số** của mọi tỉ lệ.

| case | lý do |
|---|---|
| `T10-C5-020` | phán quyết chẵn/lẻ |
| `T10-C5-024` | phán quyết năm nhuận |
| `T10-C5-071` | phán quyết số nguyên tố |
| `T11CS-C6-053` | phán quyết số nguyên tố (CÓ/KHÔNG) |
| `T11CS-C6-056` | phán quyết dãy có là hoán vị của 1..n |
| `T11CS-C6-057` | phán quyết có hai phần tử trùng nhau |
| `T11CS-C6-058` | phán quyết xâu đối xứng |
| `T10-C5-080` | số học vô hướng thuần tuý `(a+b)^c` — ngoài taxonomy |
| `T10-C5-099` | tập nghiệm **phân nhánh** của phương trình bậc hai — ngoài taxonomy |

Chín case này vẫn **ở trong** SEALED. Chúng đóng góp vào **A** (hệ có sinh được
mô phỏng chạy được không) và **B** (có qua nổi cổng nội bộ không); chỉ riêng
trục oracle độc lập là không chấm được.

## Bốn case cần diễn giải đặc biệt — đã ghi `custodian_note`

| case | điều phải diễn giải |
|---|---|
| `T10-C5-038` | ý d) `A[len(A)]` cố ý vượt chỉ số và sinh lỗi, không phải một giá trị ⇒ đã loại khỏi `expected`; chỉ chấm ba ý a, b, c |
| `T10-C5-084` | đáp án phụ thuộc **quy tắc phạm vi biến**: `f` gán lại `a`, `b` ở phạm vi cục bộ nên `a`, `b` ở chương trình chính **không đổi** — đó chính là điểm bài học của Bài 28 |
| `T11CS-C6-068` | `insert()` của thư viện LinkedList trong SGK chèn vào **đầu** danh sách, nên thứ tự duyệt từ head là **ngược** với thứ tự chèn |
| `T11ICT-003` | ngữ nghĩa hiệu ứng **Blend** của GIMP: 5 lớp có 4 khoảng, mỗi khoảng 5 khung trung gian ⇒ 20 |

Bốn trường hợp này được ghi thành `custodian_note` **trong chính dữ liệu**, để
người đọc kết quả thấy ngay thay vì phải suy ra.

## Provenance chain

Ghi trong `sealed/cases.json`, khoá `provenance_chain`:

```
SOURCE UNIVERSE V2      4a9c3564…
→ EXTERNAL SELECTION POOL   34d11adc…
→ EXTERNAL SELECTION        6efe2450…   (seed 23082026, external_GVHD_or_custodian)
→ SEALED                    7e5df014…
```
