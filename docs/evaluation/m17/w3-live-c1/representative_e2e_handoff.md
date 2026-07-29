# M17 W3-LIVE-C1 §12/§13 — handoff đại diện: live candidate → engine → Chrome

**Kết luận: `REPRESENTATIVE_E2E_VERIFIED`** cho **một** case. 3 ảnh · **0 LLM
call** ở bước này.

## Câu hỏi được trả lời

Một candidate do **LLM thật sinh ra ở lượt live** có thực sự chạy qua engine tất
định của frontend và hiện lên trình duyệt không — hay ta chỉ đang tin vào fixture
viết tay?

## Chuỗi giám hộ (chain of custody)

Candidate **không** được gõ lại. Adapter đọc thẳng
`character_encoding_live_rerun.json`, lấy record `LIVE-ENC-1 run1`, rồi nạp qua
**chính** `store.loadEnvelope` — đúng đường production, không dựng engine song song.

```
live prompt "Mô phỏng mã ASCII của ký tự A."
  → validated candidate {"spec_version":"charenc-1.0","text":"A","encoding":"ascii"}
  → sha256 0217f627de318132981dc66f6d642b592c8dccc8adeb32428ef66b6bec05c429   (artifact)
  → store.loadEnvelope → engine FE
  → sha256 0217f627de318132981dc66f6d642b592c8dccc8adeb32428ef66b6bec05c429   (spec engine đang chạy)
```

**Hai hash TRÙNG KHÍT.** Lệch một bit là adapter thoát mã 3.

## Bằng chứng đọc từ engine, không phải từ ảnh

13 bước. Ba mốc được giải bằng cách **hỏi chính `state.meta`** phase nào ở bước
nào — không số học trên cursor.

| Mốc | Bước | Phase | Bằng chứng |
|---|---|---|---|
| initial | 0 | `select_character` | DOM **chưa** chứa `1000001` |
| mechanism-mid | 3 | `divide_step` | `{value: 65, base: 2, quotient: 32, remainder: 1, digit: "1"}` |
| final | 12 | `complete` | `A → cp 65 → dec 65 → bin 1000001` |

Thuyết minh do engine sinh ở mốc giữa:

> *65 : 2 = 32 dư 1 → chữ số 1. Các số dư đọc NGƯỢC từ dưới lên sẽ thành kết quả.*

Bảy assertion đều xanh: `hash_match` · `target_runtime_dung`
(`binary.character_encoding`) · `khong_phai_generic` · `initial_chua_co_binary` ·
`mid_co_phep_chia_that` · `final_binary_do_engine_sinh` · `text_giu_nguyen`.

Ghi cho chính xác: mô hình `rows` của engine giữ giá trị cuối ngay từ đầu; thứ
được kiểm ở mốc initial là **DOM người học nhìn thấy** chưa có dãy bit — tức là
trình bày tăng dần thật, không phải công bố sẵn đáp án.

## Case không đo được

`E2E-ENC-2` (Unicode `U+1EBF`) = **`NOT_MEASURED`**. Lượt live không cho candidate
nào được chấp nhận cho LIVE-ENC-3 (cổng cơ chế chặn đúng luật — xem
`mechanism_gate_correction.md §6`). Adapter **từ chối** dựng config bằng tay:
làm vậy sẽ biến bằng chứng E2E thành fixture trá hình.

## Phạm vi

Một target, một case, một viewport. **Không** suy rộng ra toàn catalog, và
**không** nói gì về hiệu quả học tập.
