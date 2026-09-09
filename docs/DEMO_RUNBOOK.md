# DEMO_RUNBOOK — chạy buổi demo AlgoSim

**Bản đóng băng:** `algosim-thesis-2026-09-09+display-name-polish` · candidate `96a9368b…` ·
`CACHE_VERSION 95`. Danh tính đầy đủ:
`docs/evaluation/geometry/final-system-release/RELEASE_MANIFEST.json`.

> **Buổi demo KHÔNG cần khoá API và KHÔNG gọi model.** Chín ca demo chạy từ
> chương trình đã đóng băng. Không có khoá nào trong tài liệu này, và không cần
> có.

---

## 1 · Yêu cầu môi trường

| thứ | bản đã kiểm | ghi chú |
|---|---|---|
| Node.js | **v24.13.0** | `node --version` |
| npm | **11.6.2** | |
| Chrome | bản ổn định trên máy | chỉ cần cho *kiểm tra tự động*; demo dùng trình duyệt nào cũng được |
| Hệ điều hành | Windows 11 (26100) | đã kiểm ở đây; không có phụ thuộc riêng của Windows trong sản phẩm |
| Python | 3.12 trong `backend/.venv` | chỉ cần nếu muốn chạy cổng kiểm |
| WebGL | **bắt buộc** | không có WebGL thì khung 3D hiện lời nhắn thay canvas |

Kiểm WebGL trước: mở `chrome://gpu` → *WebGL* phải là **Hardware accelerated**
hoặc **Software only**. Cả hai đều chạy được; phần mềm thì chậm hơn.

## 2 · Cài đặt

```bash
git clone <repo> && cd algo-sim
cd frontend && npm ci
```

Backend **không cần** cho chín ca demo (xem §5). Nếu muốn chạy cổng kiểm Python:

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
```

## 3 · Khởi động — DÙNG BẢN DỰNG, KHÔNG DÙNG DEV SERVER

```bash
cd frontend
npm run build                       # tsc -b + vite build
npx vite preview --port 4173 --strictPort
```

> ⚠️ **Vì sao bản dựng chứ không phải `npm run dev`.** Đo được ở wave
> `FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE`: **13–25 % phiên trình duyệt
> không tải nổi module từ Vite dev** (`ERR_CONNECTION_REFUSED` /
> `ERR_NETWORK_ACCESS_DENIED`, trang trắng, `#root` rỗng). Cùng phép đo trên
> **bản dựng: 0/15 lần lỗi**. Đây là lỗi transport của dev server, không phải
> lỗi sản phẩm — nhưng một buổi bảo vệ không phải chỗ để rút thăm.
> Bằng chứng: `final-system-release/PAGE_BOOT_MEASUREMENT.json`.

## 4 · Backend (CHỈ khi muốn demo đường phân tích thật)

Chín ca demo **không cần** backend. Nếu vẫn muốn dựng:

```bash
docker compose up -d --build            # backend + Postgres
cd backend && .venv/Scripts/python.exe scripts/runtime_doctor.py
```

Đường phân tích LLM cần `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY` trong
`backend/.env` (file này bị gitignore). **Không cần cho demo**, và mỗi lượt
tiêu quota thật.

## 5 · Mở đúng trang

```
http://localhost:4173
```

Không đăng nhập. Màn hình đầu là ô nhập đề. Dòng *"Máy chủ phân tích chưa
chạy — vẫn dùng được các mô phỏng mẫu bên dưới"* là **bình thường** khi không
dựng backend.

## 6 · Chín ca demo, theo thứ tự

Đề bài đầy đủ nằm trong `docs/evaluation/geometry/product-ui-result-rendering/
fixtures/<case_id>.json` (trường `problem_text`) — mở, chép, dán vào ô nhập.
Ảnh đối chiếu: `final-system-release/demo-screenshots/<case_id>.png`.

| # | case_id | dựng gì | đáp số phải thấy |
|---|---|---|---|
| 1 | `p1_chop_thiet_dien_khoang_cach` | chóp + thiết diện + khoảng cách | `72` · `9` · `3√6` |
| 2 | `p2_chop_day_ngu_giac_lom` | chóp đáy ngũ giác **LÕM** | `96` |
| 3 | `p3_mat_cau_va_thiet_dien_tron` | mặt cầu + thiết diện tròn | `4500π` · `144π` |
| 4 | `p4_hinh_tru_the_tich_va_xung_quanh` | hình trụ | `360π` · `120π` |
| 5 | `p5_hinh_non_the_tich_va_xung_quanh` | hình nón | `100π` · `65π` |
| 6 | `p6_thiet_dien_elip_cua_hinh_tru` | thiết diện **elip** của trụ | `25π√5` |
| 7 | `p7_thiet_dien_elip_cua_hinh_non` | thiết diện **elip** của nón | `2π√6` |
| 8 | `n1_khoi_tron_xoay_tong_quat` | **từ chối** — khối tròn xoay tổng quát | *(không có đáp số)* |
| 9 | `n2_khoi_ghep_bu_can_boolean` | **từ chối** — khối ghép/bù cần boolean | *(không có đáp số)* |

**Thứ tự kể chuyện đề nghị:** 1 → 2 (lõm — phá định kiến "chỉ khối lồi") →
3, 4, 5 (mặt cong) → 6, 7 (elip, dạng chính xác `25π√5`) → 8, 9 (từ chối).
Hai ca cuối là **điểm nhấn**, không phải phần thừa: chúng cho thấy hệ nói
thật khi không làm được.

## 7 · Kết quả mong đợi của từng ca

**Bảy ca dương.** Khung 3D dựng thật (canvas WebGL); thanh tua chạy được;

**bước đầu chưa hiện đáp số** — đó là chủ đích sư phạm, không phải lỗi; tua tới
bước cuối thì ô đọc số hiện **đúng dạng chính xác** ở bảng trên (`3√6` chứ
không phải `7.348…`).

> ⚠️ **Tên đại lượng phải là tên TOÁN HỌC, không phải «đối tượng».**
> Từ 2026-09-10 (`DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH`) cả 12 đại
> lượng đều có tên có nghĩa — `p6`/`p7` đọc *«Elip giao của khối cong và mặt
> phẳng»*. Thấy `Diện tích «đối tượng»` trên màn hình nghĩa là đang chạy **bản
> cũ**, hoặc một **row cache `CACHE_VERSION` cũ** còn sót: kiểm `cache_version`
> trong `RELEASE_MANIFEST.json` phải là **95**.

**Hai ca âm.** Thẻ từ chối hiện đủ bốn thứ:

* nhãn: `CHƯA DỰNG ĐƯỢC MÔ PHỎNG` (`n1`) · `NGOÀI PHẠM VI DỰNG HÌNH` (`n2`);
* lý do cho người học, tiếng Việt, không token kỹ thuật;
* khối **Dừng ở bước / Loại vấn đề** — hai sự thật có cấu trúc;
* một câu gợi ý **khác** với lý do (không lặp lại).

Không ca âm nào dựng khung 3D, và không ca nào in mã lỗi thô ra màn hình.

## 8 · Xoay và phóng để thấy nét khuất

Kéo chuột trái trên khung 3D để **xoay**; lăn chuột để **phóng**; nút *"Xem lại
toàn hình"* đưa camera về khung nhìn ban đầu.

Đáng chỉ ra nhất ở `p3`, `p6`, `p7`: thiết diện nằm **trên mặt cong**, nên khi
xoay, phần cung bị khối che **đổi từ nét liền sang nét đứt** ngay lập tức.
Phân loại do GPU quyết theo **từng điểm ảnh**, nên một cạnh tự chia thành nhiều
đoạn — không có bảng nào được tính sẵn. Ảnh đối chiếu:
`demo-screenshots/<case_id>--sau-xoay.png`.

Nút *"Tách khối"* tách các mảnh để nhìn vào trong (hữu ích ở `p1`, `p2`).

## 9 · Trình bày hai ca từ chối

Nói đúng ba ý, theo thứ tự:

1. **Hệ nhận ra đây là bài hình học** — nó không đổ cho đề bài là môn khác.
2. **Nó dừng ở đâu và vì sao** — đọc thẳng khối *Dừng ở bước / Loại vấn đề*.
   `n1` dừng ở *viết chương trình dựng hình*; `n2` dừng ở *đối chiếu với các
   phép dựng hệ có*.
3. **Vì sao từ chối là kết quả ĐÚNG** — hệ không hiển thị hình chưa kiểm chứng.
   Thà không có mô phỏng còn hơn một hình sai mà học sinh tin theo.

⚠️ Đừng hứa quá cho `n1`: hệ dừng **trước** cổng phủ, nên nó biết *chương trình
không hợp lệ*, **không** biết bài có nằm ngoài bao đóng hay không. Câu gợi ý
trên màn hình cố ý viết ở dạng **có điều kiện** vì lý do ấy.

## 10 · Nếu WebGL hoặc font khác môi trường chuẩn

| triệu chứng | xử lý |
|---|---|
| Khung 3D hiện lời nhắn thay canvas | WebGL tắt → bật lại ở `chrome://settings`, hoặc chạy Chrome với `--enable-unsafe-swiftshader` (GPU phần mềm, chậm hơn nhưng đủ) |
| Hình dựng được nhưng chậm/giật | đang dùng SwiftShader; giảm cửa sổ trình duyệt, hoặc bật tăng tốc phần cứng |
| Chữ tràn hoặc nhãn chồng nhau | thiếu font Inter → trình duyệt rơi về `system-ui`. Không ảnh hưởng hình học; nếu quan trọng, cài Inter |
| Trang trắng | **không** phải lỗi sản phẩm — xem §3: dùng bản dựng, đừng dùng dev server. Tải lại **không** cứu được; mở lại tab/trình duyệt thì được |
| Đáp số hiện `7.348…` thay vì `3√6` | sai bản: bản đóng băng giữ dạng chính xác. Kiểm `candidate_hash` trong manifest |

## 11 · Kiểm nhanh TRƯỚC buổi bảo vệ

Khoảng 5 phút, không tiêu một lượt gọi model nào:

```bash
# ① sản phẩm dựng được và bản dựng sạch
cd frontend && npm run build

# ② chín envelope thật dựng thành mô phỏng trong Chrome thật (cần `npm run dev`)
cd frontend && node scripts/certify-product-ui-rendering.mjs      # 73/73

# ③ bề mặt từ chối (chạy trên BẢN DỰNG — cần `vite preview` ở §3)
cd frontend && node scripts/certify-refusal-surface.mjs           # 21/21

# ④ đáp số vẫn khớp lượt đo cuối, số học chính xác
cd backend && .venv/Scripts/python.exe scripts/doi_chieu_ket_qua_cuoi.py \
  ../docs/evaluation/geometry/thesis-final-acceptance/thesis-final-20260908T160224Z

# ⑤ danh tính bản đang chạy đúng bản đã đóng băng
cd backend && .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
cd backend && .venv/Scripts/python.exe scripts/lock_cache_identity.py --verify
```

Đặt `PYTHONIOENCODING=utf-8` cho mọi lệnh Python — thiếu nó thì một lượt PASS
vẫn có thể chết ở dòng `print` và **trông y hệt** một lượt thất bại.

## 12 · Thời lượng dự kiến

| phần | phút |
|---|---|
| Dựng và mở trang (làm TRƯỚC, không tính vào buổi) | 2 |
| Bảy ca dương, mỗi ca ~1,5 phút | 10 |
| Xoay/tách khối ở `p3`, `p6`, `p7` | 3 |
| Hai ca từ chối | 3 |
| Hỏi đáp về ranh giới R0 và giới hạn | 5 |
| **Tổng** | **~21 phút** (không kể chuẩn bị) |

Rút gọn còn 10 phút thì giữ: `p1` (đa diện + thiết diện) · `p2` (lõm) ·
`p7` (elip trên nón, có xoay) · `n2` (từ chối trung thực).
