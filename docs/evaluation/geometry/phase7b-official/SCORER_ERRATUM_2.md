# SCORER_ERRATUM #2 — ba lượt cuối gần chắc là lỗi NHÀ CUNG CẤP, không phải lỗi hệ

**Ngày**: 2026-08-29 · **Lượt**: `phase7b-official-82917341` ·
**Số lời gọi model lặp lại: 0.** Không artifact thô nào bị sửa.

## 1. Chuyện gì xảy ra

Trong wave phát triển sau Phase 7B, một lượt đo DEV gặp:

```
RuntimeError: Gemini API lỗi HTTP 429: "Your prepayment credits are
depleted." · status RESOURCE_EXHAUSTED
```

Chữ ký của một lượt hỏng vì lý do ấy, đo trực tiếp:

```
logical_calls = 1 · http_requests = 4 · ~8.5–8.7 s
request_contract = KHÔNG có · reason = None · envelope_status = EXCEPTION
```

`http = 4` cho **một** lượt logic là dấu hiệu riêng: đó là thang retry
transport (`MAX_ATTEMPTS = 4`, `TRANSIENT_STATUS ∋ 429`) chạy hết nấc. Một
lượt bị từ chối vì ngữ nghĩa chỉ tốn **một** HTTP.

## 2. Ba bản ghi của lượt chính thức mang đúng chữ ký ấy

| Bản ghi | thời gian | logic | http | contract | reason |
|---|---|---|---|---|---|
| `hp_b06_041-lan1` | 8.8s | 1 | 4 | KHÔNG | `None` |
| `hp_b06_041-lan2` | 8.9s | 1 | 4 | KHÔNG | `None` |
| `hp_b06_041-lan3` | 8.6s | 1 | 4 | KHÔNG | `None` |

Chúng là **ba lượt cuối cùng** của cả lượt đo (bài 20/20), đúng chỗ credit
cạn nếu nó cạn.

Bản ghi `EXCEPTION` thứ tư, `hp_b05_038-lan3`, **KHÔNG** mang chữ ký ấy:
83.4s · 5 logic · 8 http · có contract · reason *"Chương trình dùng dữ liệu
không truy được về đề bài."* Đó là một lượt hỏng THẬT của hệ, và nó ở
nguyên chỗ cũ.

## 3. Điều KHÔNG chứng minh được, và vì sao

`measure_geometry_stability.mot_luot` dựng `env = {"status": "EXCEPTION",
"reason": …}` nhưng `ban_ghi` đọc `reason` từ **observer**, mà observer
không phát gì khi pipeline ném trước chặng đầu tiên. Nên **lời nhắn của sự
cố bị rơi mất** và artifact chỉ còn `envelope_status`.

Vì thế bằng chứng ở đây là **chữ ký trùng khít**, không phải thông báo lỗi.
Ba dấu hiệu độc lập cùng chỉ một hướng — `logic=1`, `http=4` (retry cạn
nấc), vị trí cuối lượt — nhưng không dấu hiệu nào là lời khai trực tiếp.

Khuyết tật của **bộ đo** ấy đã vá: `ban_ghi` nay mang trường `su_co` giữ
nguyên `type(e).__name__: e`. Lượt sau sẽ không còn phải suy đoán.

## 4. Cách đọc đúng, và con số nào đổi

Giữ nguyên artifact; đây là **chú giải**, không phải bản chấm lại.

| | Đã công bố | Đọc đúng |
|---|---|---|
| tầng B, từ chối trung thực | 14/18 | **14/15 lượt đánh giá được** |
| tầng B, ném lỗi (E) | 4/18 | **1/15** (`hp_b05_038-lan3`) |
| tầng B, lỗi nhà cung cấp (F) | 0 | **3** (`hp_b06_041` ×3) — ngoài mẫu |
| `E_metric_tooling` | 6 | 3 |
| `F_transport_provider` | 0 | 3 |

**`BỊA HÌNH` vẫn là 0.** Kết luận mạnh nhất của lượt đo không đụng tới.

Mọi số **tầng A** không đổi một đơn vị: `served 20/42` · `oracle 6/33` ·
`construction 14/23` · `verification 32/42` · `stability 7/14`.

## 5. Vì sao phải sửa theo chiều này

`POST_PHASE7B §11` cấm biến lỗi hạ tầng thành lỗi mô hình. Bản chấm hiện tại
làm đúng điều bị cấm: nó ghi ba lượt hết-quota vào `E_metric_tooling` với lý
do *"ngoài phủ mà NÉM LỖI thay vì nói không diễn đạt được"* — một lời buộc
tội về hành vi hệ thống, cho ba lượt hệ thống chưa kịp chạy.

Sửa theo chiều này làm hệ **trông tốt hơn**, nên nó phải dựa vào bằng chứng
chứ không vào mong muốn. Bằng chứng ở §2; giới hạn của bằng chứng ở §3; và
`hp_b05_038-lan3` **không** được hưởng cùng cách đọc, vì nó không có cùng
chữ ký.
