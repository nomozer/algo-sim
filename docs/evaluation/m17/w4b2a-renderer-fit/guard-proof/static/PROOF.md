# GUARD PROOF — `VISUAL_FIT_OUT_OF_RANGE` đỏ được ở CẢ HAI hướng

Một renderer hỏng được theo **hai** hướng. Một cổng chấm chỉ bắt được một hướng
là cổng nửa mù — và luật "hình phải chiếm ≥ X% sân khấu" thì **thưởng** cho
hướng thứ hai. Nên phép chứng minh phải cho thấy nó đỏ được **cả hai chiều**,
không chỉ một.

## Mô hình chạy — vì sao mỗi trạng thái một tiến trình Vite

Lượt chứng minh trước **không hợp lệ**: tôi sửa nguồn trong lúc Vite và runner
đang chạy, nên HMR nạp lại module **giữa lượt đo** và lượt chạy chết vì đứt
import — không phải vì phán quyết của guard.

Không dùng bản build tĩnh: runner cố ý lái app qua **URL nguồn của Vite**
(`/src/state/store.ts`, `/src/data/offline-catalog.ts`,
`/src/simulations/index.ts`). Sau khi bundle, những đường đó không còn tồn tại,
nên bản tĩnh sẽ làm hỏng chính cơ chế đo.

Thứ tự bắt buộc, lặp lại cho từng trạng thái:

```
đặt trạng thái NGUỒN → khởi động Vite mới → chờ server sẵn sàng
→ chạy runner → DỪNG Vite → chỉ khi đó mới sửa/hoàn tác nguồn
```

Không file nguồn nào được đổi khi tiến trình Vite còn sống.

## Năm lượt chạy

Cùng runner · cùng fixture `algorithm.find_max` (5 phần tử) · cùng viewport
1920×1080 · cùng checkpoint `mid` · cùng `visualMode` 2D · Vite mới mỗi lượt.
Chỉ khác **trạng thái lỗi của nguồn**.

| # | Trạng thái nguồn | Kết quả | Mã thoát |
|---|---|---|---:|
| A | sạch | `PASS` | **0** |
| B | **tiêm A** — renderer bỏ qua bề rộng đo được (`arrayChartLayout(n, 0)`) | `VISUAL_FIT_OUT_OF_RANGE` → **UNDER_UTILIZED** | **1** |
| C | hoàn tác | `PASS` | **0** |
| D | **tiêm B** — trần cột về lại 96px (mật độ đã bị bác) | `VISUAL_FIT_OUT_OF_RANGE` → **OVER_EXPANDED** | **1** |
| E | hoàn tác | `PASS` | **0** |

Chi tiết hai lượt đỏ:

```
B  algorithm.find_max  1920x1080/mid
   UNDER_UTILIZED — hình 364px < mong đợi 494px
   (sân khấu 1306px · trần ngữ nghĩa 494px)

D  algorithm.find_max  1920x1080/mid
   OVER_EXPANDED — 125px/phần tử > trần mật độ 100px
   (hình 624px, 5 phần tử)
```

Cả hai đều thoả điều kiện hợp lệ: đúng danh tính mô phỏng, đúng `visualMode`,
trang nạp bình thường, `store.active` tồn tại, runner chạy tới bước chấm vừa
khung, và lỗi do **chính** `VISUAL_FIT_OUT_OF_RANGE` phát ra.

## Vì sao lượt D mới là phần đáng giá

`semanticMaxWidth` được tính **từ chính hàm bố cục**. Nếu trần mật độ cũng tính
từ đó thì nới `MAX_COL_W` sẽ làm trần nới theo, và cổng chấm **không bao giờ**
thấy được vượt mức — guard sẽ mù đúng hướng hỏng mà milestone này vừa mắc phải.

Vì vậy `maxWidthPerItem = 100` được **khai riêng**, phát biểu điều kiện thiết kế
(hai cột kề nhau phải nằm gọn trong một lần nhìn) chứ không mô tả cài đặt. Lượt
D chứng minh sự tách rời đó có tác dụng thật.

> Đây là **ràng buộc thiết kế hiện hành**, suy từ yêu cầu đọc được của phép so
> sánh kề nhau. **Không phải** bằng chứng về tác động học tập.

## Một khiếm khuyết runner lộ ra giữa chừng

Lượt B đầu tiên trả `WRONG_SIMULATION_OR_FIXTURE` với
`analysisError: "Hệ thống chưa có mô phỏng algorithm.find_max"` — **không hợp lệ**
làm bằng chứng theo tiêu chí ở trên.

Nguyên nhân: nhánh nạp **fixture đơn** chưa được vá đăng ký registry (lượt trước
chỉ vá nhánh catalog). Nó "may thì chạy" — phụ thuộc app đã kịp đăng ký hay
chưa, và lượt A trúng may. Đã ép đăng ký ở cả hai nhánh, nên phép đo nay tất
định thay vì phụ thuộc thời điểm.

Đáng ghi lại: dấu vân tay danh tính đã **chặn đúng** một bằng chứng giả. Nếu nó
chỉ kiểm cấu trúc DOM như bản đầu, lượt B đó đã được ghi nhầm thành một lượt đỏ
hợp lệ.

## Sau lượt E

`git diff` của `frontend/src/components/ArrayView.tsx`: **rỗng** — không còn dấu
vết lỗi tiêm nào trong mã production. vitest **957 passed**, build OK.
