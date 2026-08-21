# Phát hiện từ bốn lượt pilot

> Số liệu ở đây là **pilot**, không phải Task 12 — xem
> `../pilot-results/PILOT_KHONG_PHAI_TASK_12.md`. Nhưng các **phát hiện** dưới
> đây không phụ thuộc tính held-out: chúng là lỗi của hệ, quan sát được bất kể
> ai soạn đề.

## Diễn biến bốn lượt

| lượt | A | B | chết ở đâu |
|---|---|---|---|
| 1 | 0/40 | 0/40 | HTTP 400 — chưa gọi được API lần nào |
| 2 | 0/40 | 0/40 | sai tên trường cấp cao nhất |
| 3 | 0/40 | 0/40 | lỗi mô hình hoá trong hợp đồng đúng |
| 4 | **6/40** | **1/40** | rải rác, xem dưới |

Ba lượt đầu **không đo được gì về năng lực hệ** — chúng đo lỗi tích hợp. Chỉ
lượt 4 mới bắt đầu nói được điều gì đó về route.

## Phát hiện 1 — Route chưa từng chạy được với API thật

`_sanitize_gemini_schema` xoá `$defs` nhưng giữ `$ref` trỏ vào đó. Mọi lượt gọi
`semantic_program` bị HTTP 400. **1725 test offline vẫn xanh**, vì tất cả đều
mock `call_gemini`.

> Test đơn vị xanh không chứng minh đường tích hợp tồn tại. Đây là lần thứ hai
> cùng một bài học xuất hiện trong dự án — lần đầu là `stage_semantic_program`
> không có ai gọi.

## Phát hiện 2 — IR không diễn đạt được bằng structured output của Gemini

| độ sâu nội suy `$ref` | kích thước |
|---|---|
| 2 | 296 KB |
| 3 | 3,0 MB |
| 4 | 29,9 MB |

Nổ ~10× mỗi bậc vì IR đệ quy (câu lệnh chứa câu lệnh), mà độ sâu 2 còn quá nông
cho một `for_range` có `if` bên trong. **Đây là giới hạn thiết kế, thuộc phần
hạn chế của luận văn.** Hệ quả: constrained decoding không dùng được; hợp đồng
phải đi kèm dưới dạng thẻ văn phạm sinh từ Pydantic (~3,2 KB/lượt gọi).

## Phát hiện 3 — Bằng chứng live cũ không chứng minh điều nó có vẻ chứng minh

`run_live_gemini_semantic_smoke.py` từng cho `LIVE_GEMINI_CERTIFIED_OK`. Nhưng:

- nó **không gửi `responseSchema`**, tự dựng lời gọi httpx riêng ⇒ không đi
  đường production, không chạm constrained decoding;
- "đề bài" của nó **đọc sẵn lời giải bằng đúng từ vựng IR**: *"…duyệt từng ký
  tự qua `for_each`, kiểm tra map/bảng tra `{'a':1,…}`, và tăng biến
  `vowel_count`"*.

Đó là **đọc chính tả**, không phải "LLM đọc đề, engine diễn hoạt". Artifact ấy
không nên được trích như bằng chứng cho claim A.

## Phát hiện 4 — Tầng kiểm chứng nội bộ KHÔNG ĐÁNG TIN, theo cả hai chiều

Đây là kết quả quan trọng nhất, và nó chỉ lộ ra vì oracle độc lập được báo
**riêng** khỏi phán quyết nội bộ.

Trên 40 case của lượt 4:

```
hệ tự cho là PHÁT ĐƯỢC (servable) : 1 case  → sealed_038
oracle độc lập nói case đó         : SAI
hệ trả lời ĐÚNG                    : 2 case  → sealed_006, sealed_031
hệ PHÁT được hai case đó không     : KHÔNG, cả hai bị từ chối
```

**Giao của "hệ tự tin" và "hệ đúng" là RỖNG.**

### 4a. C₂ chấp nhận rác — `sealed_038`

Đề: xoá phần tử giữa của dãy `1 2 2 3 4 5 5`. Bộ nhớ cuối:

```json
"day_so_sau_khi_xoa": [
  {"kind":"index","container":"day_so_a","index":{"kind":"var","name":"i"}},
  … lặp lại 6 lần …
]
```

Chương trình đẩy **object biểu thức chưa được tính** vào mảng thay vì giá trị.
Validator, P2, C₁a, C₁b và C₂ **đều cho qua**. Checker `derived_sequence` không
phát hiện được rằng phần tử không phải giá trị vô hướng.

### 4b. C₂ từ chối câu trả lời đúng — `sealed_006`, `sealed_031`

```
sealed_006  đếm cặp nghịch đảo của [3,2,1,5,4]
            hệ = 4  ·  oracle = 4  ·  C₂ nói "đúng phải là 5"

sealed_031  đếm số bạn cao hơn chiều cao trung bình (8 số đo)
            hệ = 4  ·  oracle = 4  ·  C₂ nói "đúng phải là 8"
```

Nguyên nhân: `_pred_of` trong `postconditions.py` **mặc định về `any`** khi
`pred` không nằm trong `_PREDS`. Với `aggregate_matching(count)`, "đếm mọi phần
tử" chính là `len(container)` — nên checker báo 5 và 8, tức đúng bằng số phần
tử. Nó không kiểm được vị từ mà nó không biểu diễn được, và **im lặng đoán**
thay vì từ chối.

> Cùng một lớp lỗi đã lặp lại nhiều lần trong dự án: **giá trị mặc định thầm
> lặng ở chỗ đáng lẽ phải fail-closed.** Sửa đúng là `_pred_of` trả về "không
> kiểm được" ⇒ nghĩa vụ rơi xuống mức yếu (`verification_gap`), thay vì bịa ra
> một kỳ vọng sai rồi kết tội chương trình.

### Hệ quả cho luận văn

`B_internal_servable` **không phải** thước đo tính đúng, và lượt pilot này cho
bằng chứng số: trên tập đã chạy, nó **sai cả khi nói có lẫn khi nói không**.
Việc tách nó khỏi `dung_theo_oracle_doc_lap` — và nêu đích danh case
`phat_nhung_oracle_noi_SAI` — là thứ duy nhất làm điều này nhìn thấy được.

## Điều KHÔNG được kết luận từ lượt này

- **Không** kết luận A ≈ 15% là năng lực thật của route. Tập này do chính tác
  nhân viết hệ soạn, và hệ đã được sửa bốn lần dựa trên chính nó.
- **Không** dùng bất kỳ số nào ở đây làm A/B/D của Task 12.
- **Không** kết luận 34 case còn lại là "hệ không làm được": phần lớn chết ở
  `semantic_program_invalid` (24), tức lỗi mô hình hoá của LLM dưới một hợp
  đồng mà nó chỉ nhìn thấy qua thẻ văn phạm — chưa tách được "LLM chưa đủ giỏi"
  khỏi "hợp đồng chưa đủ rõ".

## Việc còn treo, cố ý KHÔNG làm

Vòng lặp pilot dừng ở lượt 4 theo thoả thuận, để tránh nắn hệ theo đúng 40 đề
này. Hai lỗi ở Phát hiện 4 **chưa được sửa** — chúng được ghi lại nguyên trạng:

1. `_pred_of` mặc định `any` ⇒ C₂ bịa kỳ vọng sai (`postconditions.py`).
2. Checker `derived_sequence` không kiểm phần tử có phải giá trị vô hướng không.

Cả hai đều nên sửa **trước** Task 12 thật, và cả hai đều là sửa fail-closed chứ
không phải mở rộng năng lực.
