# W4B-2D §4 — HỆ ĐẾM VỊ TRÍ CỦA HỌ TÌM KIẾM

Phân loại: **MAJOR_SEARCH_SEMANTIC_CONSISTENCY** (§12).
Runner: `frontend/scripts/audit-search-position.mjs` · Chrome thật qua CDP · chỉ ĐỌC.

## Ba lượt đo — đọc theo thứ tự này

| Thư mục | Nguồn | Kết luận |
|---|---|---|
| `before/` | HEAD `489f6a5`, chưa vá | `SAME_SCREEN_CONTRADICTION` — 4 mâu thuẫn |
| `fault-injection/` | đã vá, nhưng **lùi** `ArrayView`+`VarsView` về HEAD | `SAME_SCREEN_CONTRADICTION` — 4 mâu thuẫn |
| `after/` | đã vá đầy đủ | `NO_CONTRADICTION` — 0 |

`fault-injection/` không thừa. Phép đo trong `before/` chạy bằng một phiên bản
script **sai**: nó suy "VarsView 0-based" từ việc vùng hành động in `i+1`, tức
khẳng định về một bề mặt nó không hề đọc. Script sau đó được sửa để so CHIP
THẬT với VÙNG HÀNH ĐỘNG THẬT — và một guard vừa được sửa là một guard chưa được
chứng minh (`ARCHITECTURE_MAP §8` #14). Lượt tiêm lỗi chạy **script mới** trên
**mã cũ** để chứng minh nó vẫn bắt được lỗi; không có nó thì `after/` chỉ chứng
minh được rằng script đã hoá mù.

## Sự cố

Trên CÙNG một màn hình `binary_search`, ở bước có thể cam kết, panel Giải thích mở:

| Bề mặt | Trước | Sau |
|---|---|---|
| Mã giả (`PSEUDOCODE`) | `trái ← 1; phải ← n` | *không đổi* |
| Chip BIẾN | `trái 0 · phải 9 · giữa 4` | `trái 1 · phải 10 · giữa 5` |
| `SearchActionZone` | `vùng xét 1–10` | *không đổi* |
| Nhãn cột `ArrayView` | `0 … 9` | `1 … 10` |

Hệ quả đo được, không phải suy đoán: học sinh lần theo mã giả tính
`giữa ← (trái + phải) div 2` ra **5**, còn bảng biến bên cạnh hiện **4**. Mã giả
KHÔNG lần theo được bằng chính bảng biến đứng cạnh nó. Sau khi vá: (1+10) div 2
= 5 = đúng chip.

`linear_search` cùng dạng: mã giả `với mỗi i từ 1 đến n`, chip `i 0`, vùng hành
động `Phần tử vị trí 1`, nhãn cột `0`. Cùng định danh `i`, hai giá trị, cách
nhau 300px trên một màn hình.

## Vì sao trôi được lâu đến vậy

`core/algorithms.ts::pos()` đã chốt luật *"Vị trí nói với học sinh — luôn đếm từ
1"* và áp cho THUYẾT MINH, kết quả, banner nhánh; `SearchActionZone` cũng in
`i+1`. Nhưng chưa ai áp cho hai bề mặt in **giá trị thô**: `VarsView` và
`ArrayView`. Đúng anti-pattern #10 — vá một bề mặt, quên bề mặt kia. Suite 998
test vẫn xanh suốt thời gian đó vì **không test nào chạm tới hệ đếm hiển thị**.

## Bản vá — phạm vi và thứ bị loại trừ

Chủ sở hữu mới: `POSITION_VARS` ở `core/pseudocode.ts`, đặt cạnh `PSEUDOCODE` vì
chính bảng mã giả sinh ra nghĩa vụ 1-based. `VarsView` nhận nó qua **tham số**,
không tra bảng nội bộ.

**Không** dùng bản đồ theo tên biến — tra thật cho thấy tên không suy ra được
tính-vị-trí: `core/program.ts` để ĐỀ BÀI đặt tên biến (một chương trình khai
biến `i` mà bị cộng 1 là sai câm), còn `core/scan.ts::trackIndexVar` LÀ vị trí
0-based thật nhưng tên do spec đặt.

Hai biến cố ý vắng mặt vì engine **đã** ghi 1-based: `luot` (`setVar("luot",
i+1)`) và `vi_tri_cuc_tri` (`setVar(..., j+1)`). Khai vào là cộng 1 hai lần.
Khoá bằng test riêng.

## Nợ khai báo — CHƯA sửa

- `algorithm.scan` (target #10) mang **cùng** mâu thuẫn: `scanPseudocode` sinh
  `ivar ← 1` trong khi `scan.ts:246` ghi `trackIndexVar = 0`. Ngoài phạm vi đã
  chốt cho wave này (9 bài chuyên biệt). Nhãn cột của nó ĐÃ hưởng bản vá
  `ArrayView` nên nay 2/3 bề mặt nhất quán, chip BIẾN thì chưa.
- `algorithm.bounded_control_flow` (#11) không có nợ: biến do đề đặt, không có
  hợp đồng 1-based nào để mâu thuẫn.

## Bug rời phát hiện cùng lượt soát

`vi_tri_cuc_tri` (sắp xếp chọn) không có trong `VAR_LABELS`, nên chip in thẳng
định danh snake_case ra màn hình học sinh — đúng thứ `ARCHITECTURE_MAP §8` #10
cấm. Đã thêm nhãn "vị trí cực trị" và thêm test quét toàn bộ 9 bài × mọi bước.
