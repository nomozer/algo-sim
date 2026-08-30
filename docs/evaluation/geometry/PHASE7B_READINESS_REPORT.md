# PHASE 7B — BÁO CÁO SẴN SÀNG

> Sinh bằng `scripts/report_holdout_readiness.py`. **0 API call.**
> Mọi số dẫn từ nguồn — đừng sửa tay, chạy lại.
> Chụp lúc `2026-08-30T10:14:30+00:00`.

```
READY_FOR_PHASE7B:  YES
```

---

## 1. Environment

```
git_sha                  : 9f999517da4cab535ac1493057652bed451f6561
cây sạch                 : có
cache_version            : 50
skill_hash               : 6208fc2a2d5ba98d31f56ace90d6f6e35edf5a013082553f7299146405e30a42
prompt_hash (grammar)    : 446b076922120cd426d68843537e91f95339b415f75beeaa66bd53722b6fa23b
measured_system_hash     : 16c300fed763584bd6585a4782440a30c8143304786b132af89b3d6cbcb4a40e  (146 file)
metric_contract_hash     : 2bb1b1cd64eba3643a27c5fbbbc881c0f9e3a790121cee5beea6ed6341588fe0
capability_boundary_hash : 8a85a4b287d631cc8ae11597e2efc4ca45a1f88f15da8e99752a636d4a478adc
holdout_protocol_hash    : 082070cadac037f2b9f78bcc10cd933f2eef5374cb6a1b72adcd5ac751623e01
pool_hash                : 5aa04d8ee14a136a6dc7a470da389238ddc891e1daafd0f6d21f306d6e1bc784
```

⚠️ `git_sha` ở trên là **của lúc chụp**, không phải của HEAD hiện tại —
commit kế tiếp làm nó cũ đi. **Chạy lại script ngay trước khi niêm
phong**, đừng đọc bản cũ.

⚠️ `runtime_doctor` **không** nằm ở đây: nó so **git SHA**, nên *mọi*
commit — kể cả commit sửa tài liệu — làm nó FAIL lại. Nó là bước **áp
chót** ngay trước `seal`, không phải một ô tick giữ mãi.

---

## 2. Dataset

**`accepted`: 42/40**

| Trạng thái | Số bài | `case_id` |
|---|--:|---|
| `accepted` | 42 | hp_a01_001, hp_a01_002, hp_a01_003, hp_a02_004, hp_a02_005, hp_a02_006, hp_a03_007, hp_a03_008, hp_a04_009, hp_a04_010, hp_a04_011, hp_a05_012, hp_a05_013, hp_a13_014, hp_a13_015, hp_a06_016, hp_a06_017, hp_a07_018, hp_a07_019, hp_a08_020, hp_a08_021, hp_a09_022, hp_a09_023, hp_a09_024, hp_a10_025, hp_a10_026, hp_a11_027, hp_a11_028, hp_a14_029, hp_a14_030, hp_b01_031, hp_b01_032, hp_b02_033, hp_b03_034, hp_b03_035, hp_b04_036, hp_b04_037, hp_b05_038, hp_b05_039, hp_b06_040, hp_b06_041, hp_a12_001 |
| `needs_manual_review` | 1 | hp_a14_cand_002 |
| `rejected_capability_boundary` | 2 | hp_a11_001, hp_a14_cand_001 |

### Độ phủ 20 ô

| Ô | Nghĩa vụ | Số bài | |
|---|---|--:|---|
| **A01** | `point_on_line` | 3 | ✅ Giao tuyến hai mặt phẳng — điểm thuộc giao tuyến |
| **A02** | `point_on_plane` | 3 | ✅ Điểm thuộc mặt phẳng |
| **A03** | `parallel` | 2 | ✅ Hai đường thẳng song song |
| **A04** | `parallel` | 3 | ✅ Đường thẳng song song mặt phẳng |
| **A05** | `parallel` | 2 | ✅ Hai mặt phẳng song song |
| **A06** | `perpendicular` | 2 | ✅ Hai đường thẳng vuông góc |
| **A07** | `perpendicular` | 2 | ✅ Đường thẳng vuông góc mặt phẳng |
| **A08** | `perpendicular` | 2 | ✅ Hai mặt phẳng vuông góc |
| **A09** | `angle` | 3 | ✅ Góc giữa hai đường thẳng |
| **A10** | `angle` | 2 | ✅ Góc giữa đường thẳng và mặt phẳng |
| **A11** | `distance` | 2 | ✅ Khoảng cách từ điểm đến mặt phẳng |
| **A12** | `distance` | 1 | ✅ Khoảng cách từ điểm đến đường thẳng |
| **A13** | `coplanar` | 2 | ✅ Thiết diện / bốn điểm đồng phẳng |
| **A14** | `volume` | 2 | ✅ Thể tích khối chóp hoặc lăng trụ |
| **B01** | `—` | 2 | ✅ Khoảng cách giữa hai đường thẳng chéo nhau |
| **B02** | `—` | 1 | ✅ Khoảng cách đường ∥ mặt, hoặc mặt ∥ mặt |
| **B03** | `—` | 2 | ✅ Góc nhị diện có miền (có thể tù) |
| **B04** | `—` | 2 | ✅ Oxyz: viết phương trình mặt phẳng / đường / mặt cầu |
| **B05** | `—` | 2 | ✅ Mặt cầu · mặt nón · mặt trụ |
| **B06** | `—` | 2 | ✅ Phép toán vectơ, hoặc phép chiếu song song |

### Bài bị loại / chờ phán

| `case_id` | `status` | `reason` |
|---|---|---|
| `hp_a11_001` | `rejected_capability_boundary` | distance output irrational and unsupported by kernel — d(P,(MED)) = 3√6; d² = 54 và √54 không hữu tỉ, nên `geometry_exec._do` ném GEOMETRY_IRRATIONAL_RESULT. Xem CAPABILITY_BOUNDARY §2.1. |
| `hp_a14_cand_001` | `rejected_capability_boundary` | CHỨNG MINH CÔNG THỨC TỔNG QUÁT, không phải bài cụ thể. Dữ kiện là tham số ký hiệu a, b, c và yêu cầu là chứng minh một đẳng thức — kernel dựng trên toạ độ Fraction cụ thể, không có tầng đại  |
| `hp_a14_cand_002` | `needs_manual_review` | KHÔNG vướng ranh giới năng lực — dữ kiện HỮU TỈ hoàn toàn (đáy vuông cạnh 2, SA = 3), V = (1/3)·4·3 = 4 là phân số chính xác. Vướng chỗ KHÁC: đề ở dạng TRẮC NGHIỆM 4 phương án, mà hệ không ' |

---

## 3. Metric — năm chỉ số đã đóng băng

Định nghĩa ở `PHASE7_METRIC_CONTRACT §2`, đóng băng ở `§6` (Phase
7A.2). **Chưa chỉ số nào có giá trị** — chúng chỉ sinh ra từ một lượt
chạy thật, và lượt ấy chưa xảy ra.

| | Chỉ số | Đơn vị | Trạng thái |
|---|---|---|---|
| ① | `served` | `x/k` mỗi đề | chưa đo |
| ② | `oracle` | `x/k` · **ba trạng thái**, `None` ≠ `False` | chưa đo |
| ③a | `construction_match` | `x/k'` · `k'` = số lượt **chấm được** | **chưa từng đo lần nào** |
| ③b | `verification_match` | `x/k` · so **bằng đúng** | chưa đo |
| ④ | `construction_validity` | 4 số rời, **không gộp** | chưa đo |
| ⑤ | `stability` | `x/k` + **phân bố** | chưa đo · cần `k = 3` |

`k = 3` · ngân sách `360` logic / `480` HTTP — chốt ở `HOLDOUT_K_FINAL.md`.

⚠️ ③a **chưa từng được đo trong bất kỳ lượt nào**, kể cả DEV. Con số
đầu tiên của nó phải đến từ một lượt chạy thật — không được điền bằng
cách chấm lại artifact cũ rồi gọi đó là kết quả.

---

## 4. Expectation

- Tồn tại: **CÓ**
- `expectation_hash`: `da5a8b5beb9b42dcad8064db1bbd8a6856b39b4879459775298c22ef2e1201bf`
- Con dấu `HOLDOUT_SEAL.json`: **CÓ**

Expectation chỉ soạn **sau** khi pool có bài `accepted` — soạn trước
là soạn kỳ vọng cho những bài chưa biết có nhận được không.

---

## 5. Blockers

*(không còn)*

### ⚠️ Điều phải khai khi báo cáo số

- **Số held-out THẬT là 19/20 ô**, không phải 20/20: hp_a12_001 là bài SOẠN NỘI BỘ (`curated_preseal`). Mọi số nêu hai lần — xem `PROTOCOL_AMENDMENT_A12`.
- **Seed `nguon_seed = nguoi_van_hanh`, KHÔNG phải GVHD** — `§5②` bị nới. Tính độc lập của phép rút dựa vào việc pool đã đóng băng và băm TRƯỚC khi seed được đọc (`pool_hash` trong con dấu), không dựa vào một bên thứ ba.
- **KHÔNG được viết "41/41 do người kiểm"** — chế độ xác minh là ['MÁY-TỪ-NGUỒN', 'SOẠN-NỘI-BỘ']. 4 bản ghi HIGH đã đối chiếu lại với nguồn (`HIGH_RISK_VERIFICATION.md`); phần còn lại dựa vào xuất xứ công khai + kiểm nhất quán bằng máy + đóng băng trước niêm phong.

Phân tích từng rào — vì sao tồn tại, ba đường đi, cái giá từng
đường: [`PHASE7B_READINESS.md`](PHASE7B_READINESS.md) và
[`HOLDOUT_ACQUISITION_LOG.md`](HOLDOUT_ACQUISITION_LOG.md).

