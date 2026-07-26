# M17 W2C-LIVE — Live smoke `algorithm.bounded_control_flow`

**Ngày:** 2026-07-26 · **Nhánh:** `main` · **HEAD:** `2d17405` ·
**Phân loại task:** SUPPORTING

## Kết luận

> ## `W2C_LIVE_INCOMPLETE`
>
> Chạm trần **12/12 HTTP** trước khi chạy được case thứ tư. Theo §4 → **dừng,
> KHÔNG nâng ngân sách**. **Wave 2C KHÔNG được đóng.**

**Không có unsafe acceptance, không rò kết quả, không rơi về generic, không mất
ngữ nghĩa.** Hai case hợp lệ **không sinh được spec** và hệ **từ chối trung
thực** thay vì dựng mô phỏng sai — đó là `FAIL_SAFE`, không phải PASS.

## Runtime identity (§3)

| | |
|---|---|
| runtime doctor | **PASS** — `ok: true`, `findings: []` |
| `CACHE_VERSION` | 21 (source ≡ runtime) |
| family / target | 11 / 21 (source ≡ runtime) |
| `stable_catalog_hash` | `0940d65f5ca8` — **source ≡ runtime** |
| `algorithm.bounded_control_flow` | có trong `registered_target_ids` **và** `registered_ai_reachable_ids` |
| `classify.md` mới | **đã nạp** — quy tắc `2h` có mặt, `4b` đã thu hẹp |
| Model | **`gemini-2.5-flash`** (cấu hình repo, không hard-code mới) |

**Ghi trung thực:** Docker **không khả dụng** ⇒ **không xác minh được container
parity**. Backend là tiến trình uvicorn **mới khởi động** từ cây mã sạch tại
`2d17405`. `git_sha` runtime báo `unknown` (biến môi trường không truyền được vào
tiến trình con) — doctor vẫn PASS vì **catalog fingerprint khớp tuyệt đối**, đó
mới là bằng chứng danh tính mạnh.

## Bốn case

| Case | HTTP | status | route | Phán quyết |
|---|---|---|---|---|
| LIVE-CF-1 gán + if/else | 5 | *(từ chối)* | — | **FAIL_SAFE** |
| LIVE-CF-2 while có biên | 5 | *(từ chối)* | — | **FAIL_SAFE** |
| LIVE-CF-3 thiếu dữ kiện | 2 | `unsupported` | — | **từ chối ĐÚNG** (assertion nghiêm ngặt báo FAIL — xem dưới) |
| LIVE-CF-4 hàm/đệ quy | 0 | — | — | **KHÔNG CHẠY** (cạn ngân sách) |

**HTTP: 12/12.** Ngoài ra một lượt chạy trước đó đã tiêu **8 lần thử kết nối
THẤT BẠI** (egress bị chặn tạm thời, `getaddrinfo` lỗi) — **không lần nào tới
được API**, không thu được bằng chứng nào.

## LIVE-CF-1 / CF-2 — vì sao FAIL_SAFE (đây là phần đáng giá nhất)

Cả hai đều **được định tuyến đúng** (đi tới tận `simulate`), nhưng Gemini không
dựng nổi `ProgramSpec` hợp lệ trong **3/3 lượt**, cùng một lỗi lặp lại:

**CF-1** — `Biến 'y' khai kiểu số nguyên nên cần 'int_value' là số nguyên.` ×3

> Đề *"Nếu x lớn hơn 0 thì gán y bằng 1, ngược lại gán y bằng -1"* **không hề
> nói y ban đầu bằng mấy**. Hợp đồng lại bắt **mọi biến phải có giá trị ban
> đầu**. Model rơi vào thế kẹt: hoặc bịa một giá trị đề không cho, hoặc để
> trống và bị validator chặn. Nó chọn để trống — và bị chặn.

**CF-2** — `Biểu thức 'e4_compare_x_lt_5' cần 'left' và 'right' là id của biểu thức con.` ×3

> Bảng biểu thức **phẳng + tham chiếu id** (chọn có chủ đích vì structured
> output của Gemini KHÔNG biểu diễn được schema đệ quy) hoá ra **khó cho model
> điền đúng**: nó đặt id mô tả rất tự nhiên nhưng quên nối `left`/`right` sang
> id con.

Điều hệ thống **làm đúng**: không nhận spec sai, không bịa, không hạ về generic,
không trả `ok` nửa vời. Nhưng học sinh gõ đúng hai đề rất phổ thông này thì
**chưa xem được mô phỏng**.

## LIVE-CF-3 — từ chối đúng, nhưng thiếu nhãn phân loại

Thông điệp học sinh **thật sự tốt**, đòi đủ ba thứ và nói rõ không tự bịa:

> *"Đề bài yêu cầu mô phỏng vòng lặp while nhưng không cung cấp giá trị ban đầu
> của biến, điều kiện lặp và các câu lệnh cụ thể trong thân vòng lặp. Hệ thống
> không thể tự động tạo ra một chương trình mẫu để mô phỏng."*

Không bịa biến/điều kiện/thân, không có spec, không chạy executor, không generic,
không lộ token kỹ thuật.

**Nhưng** `failure_category = None`: `classify` tự từ chối (2 HTTP: analyze +
classify) **trước khi** cổng đủ-dữ-kiện kịp chạy, nên không ai gắn nhãn
`insufficient_specification`. Hệ quả: FE sẽ hiện tiêu đề từ chối chung thay vì
**"CHƯA ĐỦ DỮ KIỆN"** — đúng thứ mà W2C-VR đã chụp ảnh xác nhận là hiện đúng khi
nhãn có mặt. Assertion nghiêm ngặt của runner vì thế báo `FAIL`, dù **mọi thuộc
tính an toàn đều đạt**.

## Ba phát hiện — phân loại theo §9, KHÔNG tự vá

| # | Phát hiện | Phân loại |
|---|---|---|
| L1 | Hợp đồng bắt **mọi biến** có giá trị ban đầu, nhưng đề tự nhiên không nêu giá trị đầu của biến kết quả (`y`) | **Contract/grammar limitation** (lộ ra nhờ live) |
| L2 | Bảng biểu thức **phẳng + id** khó cho model điền đúng — quên nối `left`/`right` | **Model variability + contract ergonomics** |
| L3 | `classify` tự từ chối ⇒ envelope **không có** `failure_category` ⇒ FE mất tiêu đề "CHƯA ĐỦ DỮ KIỆN" | **Runtime/configuration defect** (nhỏ, chỉ ảnh hưởng nhãn) |

Không mở patch wave, không thêm repair/merge/retry, không sửa prompt giữa chừng,
không chạy lại đến khi đẹp. Chờ quyết định riêng.

## Chỉ số

| | |
|---|---|
| Case chạy | 3/4 |
| PASS | 0 · FAIL_SAFE **2** · FAIL (assertion nhãn) **1** · không chạy **1** |
| unsafe acceptance | **0** |
| generic leak | **0** |
| result leak | **0** |
| semantic loss | **0** |
| HTTP | **12/12** (+8 lần thử kết nối thất bại ở lượt trước, 0 tới được API) |

## Trạng thái Wave 2C

- Offline deterministic execution: **verified** (pytest 1047 · vitest 628).
- Chrome visual review: **completed** (7 REAL_VISUAL · 1 PARTIAL · 0 BROKEN).
- Live Vietnamese NL smoke: **INCOMPLETE — chưa đạt**.

⇒ **Wave 2C KHÔNG CLOSED.** Không được claim "live fully verified". Claim đúng
độ mạnh hiện có: *engine tất định + renderer đã kiểm chứng; đường LLM → spec cho
đề tiếng Việt tự nhiên CHƯA thông, và khi không thông thì hệ từ chối an toàn.*

VR-O1 giữ nguyên limitation: chương trình một câu lệnh chưa có trạng thái
tiền-thực-thi; **không sửa `TraceBuilder`** trong checkpoint này.
