# PHASE 7B — BÁO CÁO SẴN SÀNG

> Sinh bằng `scripts/report_holdout_readiness.py`. **0 API call.**
> Mọi số dẫn từ nguồn — đừng sửa tay, chạy lại.
> Chụp lúc `2026-08-27T18:37:07+00:00`.

```
READY_FOR_PHASE7B:  NO
```

---

## 1. Environment

```
git_sha                  : eb146d472316554e5e642937595ed702a23cb0f1
cây sạch                 : KHÔNG
cache_version            : 46
skill_hash               : 6208fc2a2d5ba98d31f56ace90d6f6e35edf5a013082553f7299146405e30a42
prompt_hash (grammar)    : 446b076922120cd426d68843537e91f95339b415f75beeaa66bd53722b6fa23b
measured_system_hash     : 7ab25683ce4e4e4d0e56efb3cb291378e7bde7127cd316eefe9702981735ce00  (144 file)
metric_contract_hash     : 2bb1b1cd64eba3643a27c5fbbbc881c0f9e3a790121cee5beea6ed6341588fe0
capability_boundary_hash : 8a85a4b287d631cc8ae11597e2efc4ca45a1f88f15da8e99752a636d4a478adc
holdout_protocol_hash    : 7741c748cab2a558ada8e601030a7a4b242bace12d070e4c92f39f52b79bab96
pool_hash                : 767cb383d9a5b4c345655fe019f88bb2a9ce4edd142a21201a005e4d9d76d713
```

⚠️ `git_sha` ở trên là **của lúc chụp**, không phải của HEAD hiện tại —
commit kế tiếp làm nó cũ đi. **Chạy lại script ngay trước khi niêm
phong**, đừng đọc bản cũ.

⚠️ `runtime_doctor` **không** nằm ở đây: nó so **git SHA**, nên *mọi*
commit — kể cả commit sửa tài liệu — làm nó FAIL lại. Nó là bước **áp
chót** ngay trước `seal`, không phải một ô tick giữ mãi.

---

## 2. Dataset

**`accepted`: 0/40**

| Trạng thái | Số bài | `case_id` |
|---|--:|---|
| `needs_manual_review` | 1 | hp_a14_cand_002 |
| `rejected_capability_boundary` | 2 | hp_a11_001, hp_a14_cand_001 |

### Độ phủ 20 ô

| Ô | Nghĩa vụ | Số bài | |
|---|---|--:|---|
| **A01** | `point_on_line` | 0 | ⛔ Giao tuyến hai mặt phẳng — điểm thuộc giao tuyến |
| **A02** | `point_on_plane` | 0 | ⛔ Điểm thuộc mặt phẳng |
| **A03** | `parallel` | 0 | ⛔ Hai đường thẳng song song |
| **A04** | `parallel` | 0 | ⛔ Đường thẳng song song mặt phẳng |
| **A05** | `parallel` | 0 | ⛔ Hai mặt phẳng song song |
| **A06** | `perpendicular` | 0 | ⛔ Hai đường thẳng vuông góc |
| **A07** | `perpendicular` | 0 | ⛔ Đường thẳng vuông góc mặt phẳng |
| **A08** | `perpendicular` | 0 | ⛔ Hai mặt phẳng vuông góc |
| **A09** | `angle` | 0 | ⛔ Góc giữa hai đường thẳng |
| **A10** | `angle` | 0 | ⛔ Góc giữa đường thẳng và mặt phẳng |
| **A11** | `distance` | 0 | ⛔ Khoảng cách từ điểm đến mặt phẳng |
| **A12** | `distance` | 0 | ⛔ Khoảng cách từ điểm đến đường thẳng |
| **A13** | `coplanar` | 0 | ⛔ Thiết diện / bốn điểm đồng phẳng |
| **A14** | `volume` | 0 | ⛔ Thể tích khối chóp hoặc lăng trụ |
| **B01** | `—` | 0 | ⛔ Khoảng cách giữa hai đường thẳng chéo nhau |
| **B02** | `—` | 0 | ⛔ Khoảng cách đường ∥ mặt, hoặc mặt ∥ mặt |
| **B03** | `—` | 0 | ⛔ Góc nhị diện có miền (có thể tù) |
| **B04** | `—` | 0 | ⛔ Oxyz: viết phương trình mặt phẳng / đường / mặt cầu |
| **B05** | `—` | 0 | ⛔ Mặt cầu · mặt nón · mặt trụ |
| **B06** | `—` | 0 | ⛔ Phép toán vectơ, hoặc phép chiếu song song |

### Bài bị loại / chờ phán

| `case_id` | `status` | `reason` |
|---|---|---|
| `hp_a11_001` | `rejected_capability_boundary` | distance output irrational and unsupported by kernel — d(P,(MED)) = 3√6; d² = 54 và √54 không hữu tỉ, nên `geometry_exec._do` ném GEOMETRY_IRRATIONAL_RESULT. Xem CAPABILITY_BOUNDARY §2.1. |
| `hp_a14_cand_001` | `rejected_capability_boundary` | CHỨNG MINH CÔNG THỨC TỔNG QUÁT, không phải bài cụ thể. Dữ kiện là tham số ký hiệu a, b, c và yêu cầu là chứng minh một đẳng thức — kernel dựng trên toạ độ Fraction cụ thể, không có tầng đại  |
| `hp_a14_cand_002` | `needs_manual_review` | KHÔNG vướng ranh giới năng lực — dữ kiện HỮU TỈ hoàn toàn (đáy vuông cạnh 2, SA = 3), V = (1/3)·4·3 = 4 là phân số chính xác. Vướng chỗ KHÁC: đề ở dạng TRẮC NGHIỆM 4 phương án, mà hệ không ' |

---

## 3. Expectation

- Tồn tại: **CHƯA**
- `expectation_hash`: `THIẾU_FILE`
- Con dấu `HOLDOUT_SEAL.json`: **CHƯA**

Expectation chỉ soạn **sau** khi pool có bài `accepted` — soạn trước
là soạn kỳ vọng cho những bài chưa biết có nhận được không.

---

## 4. Blockers

1. POOL — 0/40 bài `accepted`. Thiếu **40** bài.
2. ĐỘ PHỦ — 20/20 ô trống: A01 A02 A03 A04 A05 A06 A07 A08 A09 A10 A11 A12 A13 A14 B01 B02 B03 B04 B05 B06
3. EXPECTATION — chưa có `expectations/holdout.json` (chỉ soạn được SAU khi pool có bài accepted).
4. SEED — chưa có. Số nguyên do GVHD cấp; người đo chọn seed thì người đo chọn được cả tập.
5. NGÂN SÁCH — 360 logic / 480 HTTP (k=3) chưa được duyệt.
6. CÂY LÀM VIỆC BẨN — niêm phong đòi cây sạch.

Phân tích từng rào — vì sao tồn tại, ba đường đi, cái giá từng
đường: [`PHASE7B_READINESS.md`](PHASE7B_READINESS.md) và
[`HOLDOUT_ACQUISITION_LOG.md`](HOLDOUT_ACQUISITION_LOG.md).

