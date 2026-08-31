# ERRATUM — NGỮ NGHĨA PHÉP ĐO GÓC (2026-08-31)

> Ghi thêm, **không sửa** số đo lịch sử. Matrix 3/9, fresh probe 4/6, mọi token
> count và mọi artifact cũ giữ nguyên.

## Lỗi

`angle_cos_sq` mang **hai** đại lượng toán học khác nhau tuỳ kiểu toán hạng:

| toán hạng | trả về (TRƯỚC) | đúng ra |
|---|---|---|
| line3 × line3 | cos²θ | cos²θ ✓ |
| plane3 × plane3 | cos²θ | cos²θ ✓ |
| **line3 × plane3** | **sin²θ** | cos²θ ✗ |
| **plane3 × line3** | **sin²θ** | cos²θ ✗ |

Một tên đổi nghĩa theo kiểu toán hạng là một tên nói dối ở đúng nửa số lần
dùng — và nửa ấy **không tự khai ra**: ở 45° thì cos² = sin², nên mọi bộ đo
chỉ chạy ca 45° đều báo XANH.

## Nó lọt được vì bộ chấm mang BẢN SAO của chính lỗi ấy

`geometry_obligations.check_angle` có một bản sao của phép phân phối theo cặp
kiểu, và bản sao ấy cũng gọi `sin_sq_line_plane` rồi cũng gọi kết quả là cos².
Bộ chấm không thể bắt được lỗi này: nó tính lại **cùng một đại lượng sai**.

Một bộ chấm chép luật của thứ nó chấm thì nó chỉ chấm được lỗi gõ nhầm.

## Ai phơi ra

`fresh-probe fp_5` (2026-08-31): đề hỏi côsin góc giữa `SC` và `(ABC)`. Mô
hình đo `angle_cos_sq`, đặt tên biến `cos_angle_SC_ABC_sq`, runtime trả
**1/3**. cos² của góc ấy là **2/3**. Mô hình không sai — nó làm đúng thứ hợp
đồng dạy.

Ca đó được chấm `EXECUTABLE_BUT_INCORRECT` và **giữ nguyên** như thế: điểm
lịch sử là điểm lịch sử.

## Đã sửa

`measure.cos_sq_giua(a, b)` — **một** thẩm quyền, cả đường thực thi lẫn đường
chấm cùng gọi. `angle_cos_sq` nay trả cos²θ ở cả bốn cặp, với
`cos_sq_line_plane = 1 − sin_sq_line_plane` (phép trừ đi hết trong ℚ, vẫn
chính xác).

Không thêm opcode. `angle_sin_sq` **không** được mở: §5 của chỉ thị cho phép cả
hai đường, và đường này ít bề mặt trôi hơn — không đổi schema, không thêm từ
vựng cho mô hình, và bộ chấm không cần biết chương trình đã chọn opcode nào.

## Phạm vi migration

`scripts/audit_angle_semantics.py` quét **mọi** chương trình đã lưu trong
`docs/evaluation/`:

    4 lần dùng `angle_cos_sq` · 1 trong đó là cặp (đường, mặt)

Ca duy nhất ấy là `fp_5`, nằm trong một artifact lịch sử. **Không có chương
trình sản phẩm hay fixture nào cần migration.**

⚠️ Bản quét ĐẦU TIÊN báo **0** — nó chỉ đọc `memory_declarations`, trong khi
`fp_5` dựng `SC_line`/`ABC_plane` bằng câu lệnh `construct_*`. Một con số
"sạch" sinh ra từ một bộ quét mù. Bản hiện tại gom kiểu từ cả hai nguồn.

### Pool holdout — KHÔNG sửa, và vì sao

`holdout/pool.json` khai `__don_vi_oracle__.angle` là *"sin² cho cặp
ĐƯỜNG–MẶT"*, và hai ô A10 mang ghi chú `phep_chuyen` theo quy ước ấy. Văn bản
đó nay đã lỗi thời.

Pool **không bị sửa**: `HOLDOUT_SEAL.json` đã rút xong 20 ca theo seed do GVHD
cấp, và phá con dấu vì một dòng chú thích là đổi một tập held-out.

Giá trị thì vẫn đúng, và đó là điều thật sự quan trọng:

| ô | đề | góc | oracle | dưới cos² |
|---|---|---|---|---|
| `hp_a10_025` | góc `A'C'` với `(BCC'B')` trong lập phương | 45° | `1/2` | `1/2` ✓ |
| `hp_a10_026` | hình thoi, `SO ⊥ (ABCD)` | 45° | `1/2` | `1/2` ✓ |

Cả hai nằm đúng **điểm bất động** cos² = sin² = 1/2. Đổi ngữ nghĩa là phép
không đổi với chúng.

`test_A10_trong_pool_van_DUNG_duoi_ngu_nghia_MOI` khoá điều này: một ô A10 mới
có oracle **khác** `1/2` sẽ ĐỎ, buộc người soạn khai theo cos².

Bốn ô A09 (đường–đường) vốn đã là cos² — không đổi.

## Điều erratum này KHÔNG làm

- Không đổi `matrix.json`, `probe.json`, hay bất kỳ điểm số nào.
- Không sửa `pool.json` hay `HOLDOUT_SEAL.json`.
- Không biến `fp_5` thành một ca đúng.
- Không gọi model.
