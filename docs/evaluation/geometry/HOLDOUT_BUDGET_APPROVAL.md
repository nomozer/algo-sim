# HOLDOUT_BUDGET_APPROVAL — ngân sách lượt đo Phase 7B

> File này **chép lại một quyết định của người**, không phải một suy luận của
> script. `report_holdout_readiness.blockers` đọc nó, và chỉ hạ blocker
> NGÂN SÁCH khi ba con số dưới đây **khớp đúng** hằng số trong
> `seal_geometry_holdout` (`K_CHOT`, `LOGIC_MOI_LUOT`, `HTTP_MOI_LUOT`). Đổi
> hằng số mà quên sửa file này ⇒ blocker dựng lại.

## Quyết định

```
DUYET_NGAN_SACH: 360 logic / 480 HTTP
K: 3
NGAY: 2026-08-28
NGUOI_DUYET: chủ nhiệm đề tài (người vận hành kho mã)
```

## Nguyên văn

Chốt trong chỉ thị **PHASE 7B — M1 TO READY EXECUTION WAVE** (2026-08-28),
mục *QUYẾT ĐỊNH ĐÃ CHỐT*:

> 3. k = 3.
> 4. Budget benchmark giữ 360 logic / 480 HTTP.

## Phép tính, để con số dẫn ra được

20 ô × `k = 3` lượt = **60 lượt**. Mỗi lượt: **6** lời gọi logic và **8** lượt
HTTP (`LOGIC_MOI_LUOT`, `HTTP_MOI_LUOT` — chốt ở `HOLDOUT_K_FINAL.md`).

```
60 × 6 = 360 logic
60 × 8 = 480 HTTP
```

Hai tài liệu `HOLDOUT_K_FINAL.md` và `HOLDOUT_PROTOCOL.md` phải nói **cùng
một số** — `test_ngan_sach_KHOP_PHEP_TINH_o_ca_HAI_tai_lieu` khoá điều đó.
Ngân sách trôi giữa hai file là loại lỗi chỉ lộ ra lúc quota cạn giữa phiên đo.

## Cái file này KHÔNG làm

Nó **không** duyệt lượt chạy. Trước khi tiêu call thật vẫn phải:

- có **seed** (blocker riêng, `§5②`);
- `freeze_evaluation_candidate.py --verify` PASS;
- `runtime_doctor.py` PASS;
- cây làm việc sạch.

Và nó **không** cho phép chạy quá số đã duyệt: `--max-api-calls` vẫn là cổng
cứng ở runner.
