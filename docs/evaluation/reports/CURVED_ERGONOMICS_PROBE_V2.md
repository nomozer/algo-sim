# CURVED_ERGONOMICS_PROBE_V2 — hai lượt, và câu trả lời là KHÔNG

> Chạy **2026-09-04**. **23 lượt gọi model thật** (lượt 1: 6 · lượt 2: 17).
> DỮ LIỆU PHÁT TRIỂN — không nghiệm thu, không bật năng lực sản phẩm.
> V3 **không** chạy, seed **không** rút, pool giữ nguyên niêm phong.
> Số của probe §18 **không hồi tố**. `PROMPT_CHANGED = NO`.

## 0. Kết luận trước

```
CURVED_SYNTHESIS_ERGONOMICS = NO_MEASURABLE_GAIN   →  DỪNG chỉnh prompt
SYSTEM_FAILURES             = 0
R0                          = còn nguyên · CURVED_GEOMETRY_LAUNDERING = 0
FINAL_PRODUCT_SUCCESS       = 0 / 4        (§18 cũng 0 / 4)
NEXT_ACTION                 = AUDIT_SYNTHESIS_BOTTLENECK · KHÔNG chạy V3
```

Bốn ca vẫn hỏng, và hỏng trong cùng một họ hình dạng: **dùng sai TỪ VỰNG đã có
trong thẻ văn phạm**. Chín lượt sửa không cứu được ca nào.

## 1. Hai lượt, vì lượt 1 dừng bởi lỗi của chính bộ đo

| | `curved-ergonomics-v2` | `curved-ergonomics-v2-run2` |
|---|---|---|
| HEAD | `532f0b3` | `e8d4ae5` |
| ca chạy | 3 / 4 (dừng sớm) | **4 / 4** |
| pass B | không | **có** |
| lượt gọi | 6 | 17 |

Lượt 1 dừng ở `ball_1` theo luật *"gặp lỗi HỆ bất ngờ thì DỪNG"* — **báo động
giả**. `acceptance_verdict` xếp `LEARNER_SURFACE_INCOMPLETE` thành
`SYSTEM_VERIFICATION_FAILURE` vì tôi đọc **nhãn** `failure_category =
verification_gap` thay vì đọc **cổng**. Cổng ấy hỏi *"biến đáng thấy có được
khai binding không"* — hỏi về thứ **chương trình** cung cấp, nên đó là lỗi MÔ
HÌNH.

Đúng cái lỗi mà cả tuyến `ACCEPTANCE_RUNNER_INTEGRITY` dựng ra để chặn, chỉ theo
**chiều ngược**: thay vì đổ lỗi hệ cho mô hình, nó đổ lỗi mô hình cho hệ. Đã sửa
(`→ MODEL_FIRST_BINDING_FAILURE`), hai vế đều có test khoá; artifact lượt 1 giữ
nguyên bản phân loại sai của nó, không ghi đè. Không sửa mã rồi chạy tiếp cùng
`run_id` — lượt 2 mang `run_id` mới.

## 2. Kết quả lượt 2 — 4 / 4 hỏng

| ca | one-shot | sau sửa | vì sao |
|---|---|---|---|
| `ball_1` | `MODEL_FIRST_BINDING_FAILURE` | *(không sửa được)* | chạy ĐÚNG, `R = 6`, `V = 288π` **đã qua postconditions**, nhưng `visual_bindings` RỖNG |
| `ball_2` | `MODEL_SCHEMA_FAILURE` | vẫn hỏng | `UNANCHORED_DERIVED_ASSUMPTION` — bịa điểm `A` không có trong đề |
| `cylinder_2` | `MODEL_SCHEMA_FAILURE` | vẫn hỏng | dùng `intersect_plane_curved` làm **CÂU LỆNH** (nó là BIỂU THỨC) |
| `circumsphere` | `MODEL_SCHEMA_FAILURE` | vẫn hỏng | `vector_from_points` truyền sai tên toán hạng (`from_point`/`to_point` = null) |

```
ANALYZE_CALLS 4 · SYNTHESIS_CALLS 4 · REPAIR_CALLS 9 · TOTAL 17
INPUT 44203 · OUTPUT 15903 · THOUGHT 39254 · TOTAL_TOKENS 99360
TELEMETRY_MISSING (không)
```

**Chín lượt sửa, không ca nào được cứu.** Lỗi được gửi ngược đầy đủ cho mô hình
và nó vẫn không thoát ra — đây là tín hiệu mạnh hơn cả tỉ lệ 0/4.

## 3. Hình dạng lỗi trước → sau, và một CẢNH BÁO về chính thước đo

Cùng bộ dò tất định (`curved_ergonomics_metrics`) chấm cả hai lượt.

| ca | §18 (trước) | lượt 2 (sau) |
|---|---|---|
| `ball_1` | schema 0 · bịa 0 | schema 0 · bịa 0 |
| `ball_2` | schema 1 · bịa 0 | schema 1 · bịa 0 |
| `cylinder_2` | schema 1 · bịa 0 | schema 1 · bịa 0 |
| `circumsphere` | schema 0 · **bịa 2** (`O`, `D_aux`) | schema 1 · bịa 0 |
| **tổng** | schema **2** · bịa **2** | schema **3** · bịa **0** |

⚠️ **`INVENTED_HELPER_POINT` 2 → 0 KHÔNG phải tiến bộ, và thước đo của tôi bị
nhiễu ở đúng chỗ này.** Khi một ca hỏng ở lược đồ thì **không có chương trình để
soi**, nên mọi bộ đếm hình dạng đọc ra 0. `circumsphere` không ngừng bịa điểm —
nó chỉ hỏng **sớm hơn**, ở một cổng trước đó. Đọc bảng này thành *"mô hình hết
bịa điểm"* là đọc ngược.

Ghi lại giới hạn ấy vào chính bộ dò còn hơn là báo một con số đẹp: một lớp lỗi
biến mất khỏi bảng vì ca chết sớm hơn thì đó là thông tin về **thứ tự cổng**,
không phải về mô hình.

Bằng chứng độc lập rằng hành vi bịa điểm vẫn còn: `ball_2` lượt 2 bị chặn với
`UNANCHORED_DERIVED_ASSUMPTION` — *"A: không có trong đề bài"*. Cùng hành vi,
cổng khác.

## 4. Vì sao kết luận là NO_MEASURABLE_GAIN

Luật quyết định của wave: *"Nếu 4 case vẫn fail gần như cùng hình dạng ⇒
NO_MEASURABLE_GAIN và DỪNG prompt tuning."*

- 4/4 hỏng ở cả §18 lẫn lượt 2; `FINAL_PRODUCT_SUCCESS = 0` cả hai lượt.
- `cylinder_2` lặp lại **đúng** lỗi §18 đã ghi (`intersect_plane_curved` dùng
  làm câu lệnh).
- `ball_1` hỏng **giống hệt nhau** ở lượt 1 và lượt 2 (thiếu `visual_bindings`).
- Không lớp lỗi mục tiêu nào giảm một cách đọc được — thay đổi duy nhất
  (`bịa 2 → 0`) là nhiễu của thước đo, đã giải thích ở §3.

Điều kiện `CLOSED` đòi *"ít nhất một failure class mục tiêu giảm có thể đo
được"*. Không có. ⇒ **`NO_MEASURABLE_GAIN`.** Không chỉnh prompt thêm để ép tập
phát triển xanh.

## 5. Điều hệ TẤT ĐỊNH đã tốt lên — và nó không thuộc về ecgônômi

`ball_1` ở §18 chết **tại** `postconditions` (*'cần một `solid`'*). Ở cả hai
lượt V2 nó **đi qua** cổng ấy: `VOLUME_VERIFICATION_BRIDGE` chứng thực được
`curved_solid`, nên `288π` được **kiểm** chứ không chỉ được tính.

Đây là xác nhận SỐNG cho bản vá ấy — §18 không thể cho xác nhận này vì hệ khi đó
còn hỏng. Nhưng cái đổi là **bộ kiểm**, không phải prompt: nó không tính vào
ecgônômi tổng hợp.

## 6. Điểm nghẽn tổng hợp — dữ liệu cho wave sau

Ba lỗi lược đồ của lượt 2 **không phải** do thiếu từ vựng. Kiểm bằng máy:

| từ vựng | trong `grammar_card()` | mô hình vẫn dùng sai |
|---|---|---|
| `intersect_plane_curved` | **CÓ** | dùng làm câu lệnh thay vì biểu thức |
| `vector_from_points` / `from_point` | **CÓ** | truyền sai tên toán hạng |
| `visual_bindings` | **CÓ** | bỏ trống hoàn toàn |

(`geometry_program_generator.md` **không nhắc** cả ba — chúng chỉ đến từ thẻ.)

Bốn quan sát cho wave audit, không sửa gì trong wave này:

1. **`visual_bindings` là cổng CHẾT.** `ball_1` đúng toán học tuyệt đối mà vẫn
   không phục vụ được, và lỗi ấy **không repair-eligible** — `learner_surface`
   nằm ngoài vòng sửa của `pipeline._sinh_chuong_trinh`. Mô hình không bao giờ
   được biết nó thiếu gì.
2. **Ranh giới CÂU LỆNH ↔ BIỂU THỨC** là chỗ trượt lặp lại (§18 và lượt 2).
3. **Tên toán hạng** (`from_point`/`to_point`) trượt cả ở mô hình lẫn ở tôi —
   tôi mắc đúng lỗi ấy khi viết ca chứng nhận.
4. **Chín lượt sửa không cứu ca nào** ⇒ vòng gửi-lỗi-ngược không hiệu quả với
   lớp lỗi này. Đó là phát hiện về CƠ CHẾ SỬA, đáng đo riêng.

## 7. Trạng thái

```
CURVED_SYNTHESIS_ERGONOMICS = NO_MEASURABLE_GAIN
SYSTEM_FAILURES             = 0
CURVED_GEOMETRY_LAUNDERING  = 0
BALL_PRODUCT_ENABLED        = NO
CYLINDER_PRODUCT_ENABLED    = NO
CONE_PRODUCT_ENABLED        = NO
V3                          = NOT RUN · pool niêm phong · seed chưa rút
PROMPT_CHANGED              = NO
MODEL_FACING_CONTRACT_CHANGED = NO
STABLE_CAPABILITY_HASH / CACHE_VERSION / candidate = không đổi
```

Offline sau lượt đo: pytest **3170 pass** · freeze `--verify` PASS · cache-lock
`--verify` PASS.

## 8. Việc kế tiếp

```
NEXT_ACTION = AUDIT_SYNTHESIS_BOTTLENECK   (tất định, 0 lượt gọi)
KHÔNG chạy V3 · KHÔNG chỉnh prompt tiếp
```

Bốn quan sát ở §6 là đầu vào. Không mở năng lực mới, không đụng prompt cho tới
khi audit nói được **vì sao** vòng sửa không ăn với lớp lỗi này.
