# SCORER_ERRATUM — bản chấm đầu gộp hai thang chấm

**Ngày**: 2026-08-29 · **Lượt**: `phase7b-official-82917341` ·
**Số lời gọi model lặp lại: 0.**

## 1. Lỗi

`score_phase7b_official.cham()` bản đầu tính năm chỉ số trên **cả 20 bài**
bằng một thang duy nhất. Nó đọc `servable = False` của sáu ô tầng B như 18
lượt **TRƯỢT**, và `_taxonomy` xếp chúng vào nhóm `A_llm_synthesis` — *lỗi
sinh chương trình của mô hình*.

## 2. Định nghĩa đã đăng ký trước mà nó vi phạm

`HOLDOUT_PROTOCOL §3`, đóng băng trước lượt chạy:

> ```
> tầng A (14)   chấm A · O · obligation_match
> tầng B  (6)   chấm nhị phân: TỪ CHỐI TRUNG THỰC  |  BỊA HÌNH
> ```
> Hai thang **không được gộp** thành một cột.

Sáu ô `B*` nằm ngoài (hoặc chỉ một phần trong) phủ hợp đồng. Ở đó
`servable = False` **là kết cục đúng**: đề vượt khả năng và hệ nói ra điều
ấy. Đếm nó thành lỗi là **kết tội mô hình ở đúng chỗ nó làm đúng** — cùng
lớp sai lệch mà `PHASE7_METRIC_CONTRACT §3` ghi là đã xảy ra một lần trước
đây (Phase 6.7, 2/15 lượt).

## 3. Phép sửa, tất định

Ba thay đổi, tất cả nằm trong **bộ đo** (`backend/scripts/`), không một dòng
nào trong hệ được đo:

1. `cham()` tách `TIER_A_14` và `TIER_B_6` theo tiền tố `slot`.
2. `_tang_b()` mới: chấm nhị phân theo giao thức, cộng **một ô thứ ba** cho
   `envelope_status = EXCEPTION`. Ném lỗi không phải *từ chối trung thực*
   (hệ sập chứ không *nói* là không diễn đạt được) và cũng không phải *bịa
   hình*. Nhét vào ô nào trong hai ô kia cũng sai một chiều.
3. `_taxonomy()` nhận tập id tầng B; không-served ở đó vào
   `C_capability_refusal` — một nhóm vốn đã có trong sáu nhóm của §18 nhưng
   bản đầu không bao giờ dùng tới.

Không định nghĩa chỉ số nào bị đổi. Không mẫu số nào bị nới. Không kỳ vọng
nào bị sửa. Không artifact thô nào bị ghi lại.

## 4. Giá trị nào ĐỔI

| Báo cáo | Bản đầu | Bản đúng |
|---|---|---|
| `served` | 20/57 (gộp) | **tầng A 20/42** + **tầng B 14/18 từ chối đúng** |
| tầng B, bịa hình | — (không đo) | **0/18** |
| tầng B, ném lỗi | — (không đo) | 4/18 |
| `A_llm_synthesis` | 25 | **21** |
| `C_capability_refusal` | 0 | **14** |
| `F_transport_provider` | 4 | **0** |
| `E_metric_tooling` | 2 | 6 |
| `D_deterministic_exec` | 13 | 7 |

`F_transport_provider = 4` của bản đầu cũng sai: bốn lượt ấy là
`envelope_status = EXCEPTION` trên ô tầng B, không phải sự cố mạng. Gọi
chúng là lỗi hạ tầng vi phạm §11 theo chiều ngược lại — **biến một lỗi hệ
thành một lỗi hạ tầng**. Số đúng của nhóm F là **0**.

## 5. Giá trị nào KHÔNG ĐỔI

Toàn bộ tầng A, không một đơn vị:

```
served              20/42 áp dụng · N/A 0  · trượt 22
oracle               6/33 áp dụng · N/A 9  · trượt 27
construction_match  14/23 áp dụng · N/A 19 · trượt 9
verification_match  32/42 áp dụng · N/A 0  · trượt 10
stability            7/14 bài ổn định
```

Cả `RUN_COMPLETENESS`, `LOGICAL_CALLS 225/360`, `HTTP_CALLS 245/480`,
`seal_hash`, `measured_system_hash` đều không đổi.

## 6. Không lượt gọi model nào lặp lại

Phép sửa chỉ đọc lại 60 artifact đã ghi. `ALLOW_LIVE_AI` không được đặt,
không tiến trình nào chạm provider. `BASELINE_LOCK.json` băm từng file thô;
băm ấy được tính **sau** khi sửa bộ chấm và **trước** khi mở wave phát triển,
nên mọi thay đổi về sau đối với thư mục này đều đỏ.
