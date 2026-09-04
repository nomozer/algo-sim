# ANALYZE_OBLIGATION_SURFACE_COMPLETION

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · V3 `POOL`/`SEAL`/`seed` không
> đụng · `RESEAL_PERFORMED = NO` · product capability vẫn `foundation_only`.

## 1. ROOT_CAUSE

`area` và `lateral_area` đã là **lượng đo** từ Phase 1 và Phase 2 — kernel tính
chúng chính xác — nhưng chưa bao giờ là **nghĩa vụ**. `analyze_contract` loại
mọi nghĩa vụ có `kind` ngoài `OBLIGATION_KINDS` **im lặng** (dòng 489), nên một
đề hỏi diện tích mất câu hỏi của chính nó ngay ở biên hợp đồng, trước khi chạm
bất kỳ cổng nào.

Tái hiện tất định (§A), trước khi sửa:

```
① ② BANG_PHEP_DO ĐÃ biết đo:  area of:(polygon3, section, circle3)
                              lateral_area of:(curved_solid,)
④ …nhưng VẮNG ở NGHIA_VU_DO = [angle, distance, radius, volume]
   ⇒ OBLIGATION_KINDS: area=False  lateral_area=False
   ⇒ GEOMETRY_CHECKERS: area=False  lateral_area=False
③ gửi vào 3 nghĩa vụ → contract giữ 1 (chỉ `volume`)
   ⇒ MẤT: ['area', 'lateral_area']   không mã lỗi, không cảnh báo
⑤ coverage/C₂ chỉ còn `volume` để kiểm — thứ đề HỎI không nằm trong tập ấy
⑥ pool V3: 18 ca dương · 14 ca mất nghĩa vụ · 4 ca center+radius · 0/4 đo được
```

Điều đáng ghi nhất: **hai guard tự khai điều kiện lật của chính chúng.**

- `test_08_KHONG_them_lateral_area`: *"đây là 'chưa biết', không phải 'không
  cần'"* — kèm cảnh báo rằng cùng câu chữ ấy đã sai một lần cho `radius`.
- `test_09_..._KHONG_co_nghia_vu__va_do_la_chu_y`: *"Khi nào cần: khi đo được
  rằng `analyze` gán nhầm… Chưa có phép đo ấy, nên chưa thêm."*

`CURVED_V3_RESEAL_PREFLIGHT` là phép đo còn thiếu. Lập luận *"chưa có phép đo
nào chứng minh là cần"* nay đã sai **ba lần liên tiếp**: `radius` (V2), `area`,
`lateral_area`. Nó không phải bằng chứng vắng mặt — nó chỉ nói ta chưa nhìn.

⚠️ Một khác biệt phải nói đúng: `radius` bị **ép** sang `distance`; `area` và
`lateral_area` bị **loại thẳng**. Cùng họ bệnh (hợp đồng không có cách hợp lệ
nào để nói điều đề hỏi), khác cách chết.

## 2–3. AUTHORITY_BEFORE → AUTHORITY_AFTER

| | trước | sau |
|---|---|---|
| `NGHIA_VU_DO` | 4 (`angle`,`distance`,`radius`,`volume`) | **6** (+`area`,+`lateral_area`) |
| `OBLIGATION_KINDS` (hình học) | 10 | **12** — *dẫn xuất*, không sửa tay |
| `GEOMETRY_CHECKERS` | 10 | **12** |
| enum lược đồ analyze | 10 | **12** — *dẫn xuất* |
| `BANG_PHEP_DO` | 7 | **7 — không đổi** |

`NEW_AUTHORITIES = 0`: đăng ký vào authority sẵn có. Kiểu chủ thể **không** khai
tay — `kieu_chu_the_nghia_vu` dẫn từ `BANG_PHEP_DO.kieu_of`, nên mở một lượng đo
cho kiểu mới là nghĩa vụ tự nhận (`test_D1b`).

## 4. SEMANTIC_CONTRACT

| Measure | Kiểu chủ thể (dẫn xuất) | Exact output | Obligation | Checker |
|---|---|---|---|---|
| `area` | `polygon3` · `section` · `circle3` | `Fraction` hoặc `k·π` | `area` | server |
| `lateral_area` | `curved_solid` | `k·π` hoặc `π√q` | `lateral_area` | server |

`SEMANTIC_CONTRACT_BLOCKED = NO` — cả hai đã có nghĩa và kiểu chủ thể xác định
duy nhất ở `BANG_PHEP_DO`.

**HAI nghĩa riêng, không gộp**: `area` đo hình PHẲNG, `lateral_area` đo MẶT
CONG của khối. Gộp sẽ làm *"diện tích đáy"* và *"diện tích xung quanh"* thành
cùng một câu hỏi. Diện tích **toàn phần** vẫn ngoài miền số (`πrl + πr²` có hai
căn khác nhau) — nghĩa vụ **không được** rộng hơn lượng đo nó dựa vào.

## 5. IMPLEMENTATION

```
BANG_PHEP_DO ──(không đổi)──► NGHIA_VU_DO (+2) ──► OBLIGATION_KINDS (dẫn xuất)
   ──► analyze schema enum (dẫn xuất) ──► RequestContract giữ nguyên nghĩa vụ
   ──► coverage + witness binding (dẫn xuất kiểu) ──► exact measure (dùng lại)
   ──► check_area / check_lateral_area ──► postcondition verdict
```

Hai cửa mới tách từ `_do`, **dùng chung với đường CHẠY** — đúng tiền lệ
`volume_of`, và đúng con bug `check_volume` từng mắc khi viết lại nhánh
`curved_solid` lần thứ hai:

- `geometry_exec.area_of` (+ vị ngữ `la_hinh_phang`)
- `geometry_exec.lateral_area_of`

`NEW_IR_OPERATIONS = 0` · `NEW_CURVED_TEMPLATES = 0` ·
`NEW_FAMILY_SPECIAL_CASES = 0`. `ten_da_hoa_giai` giữ **phẳng** như đã khai.

### Tám guard phải cập nhật — mỗi cái một lý do

| guard | đổi gì |
|---|---|
| `test_taxonomy_frozen` | +2 kind; trả lời câu hỏi bắt buộc: nguồn là **V3 preflight**, không phải DEV, không phải SEALED |
| `test_wave1_oracle_connectivity` | 10 → **12** kind; nhóm ĐẠI LƯỢNG +2 |
| `test_curved_coverage_bridge::test_09` | lật hẳn — danh sách nay RỖNG |
| `test_radius_obligation::test_08` | lật hẳn — `LATERAL_AREA_TAXONOMY_CHANGED = YES` |
| `test_curved_foundation` · `test_radius_verification` · `test_volume_verification` | tập checker +2; `lateral_area` rời danh sách CẤM, `surface_area` **ở lại** |
| `test_section_capability` | `area` chấm được `Section` — taxonomy cho qua nhờ dẫn xuất |
| `test_geometry_wave2` | enum 10 → 12 |
| `test_verification_capability_identity` | vân tay `kiem_chung_do` +2 |
| `seal_geometry_holdout.NGHIA_VU_KHONG_CO_O` | +2 mục: held-out A **KHÔNG** đo diện tích, khai kèm hệ quả |

`test_measure_checker_subject_drift` đòi **mẫu** cho `polygon3` và `section`, và
đòi đúng: không có mẫu thì nó không kết luận được checker có nhận kiểu ấy hay
không, và một cổng im lặng vì thiếu dữ liệu là cổng không gác. Đã thêm hai mẫu.

## 6. MODEL_FACING_DELTA

```
analyze_schema     a4d5ed7c65a68007 → 515001b503af5c7c   ĐỔI  (enum +2 kind)
capability         8cb3d5081bfcb7f7 → 85bd316781b86576   ĐỔI  (+2 checker)
semantic_env       e9492e6354e0c813 → 30502a4404cbe6aa   ĐỔI  (dẫn xuất)
grammar_card       24e550ad1c57a2aa                       KHÔNG ĐỔI
synthesis_schema   82dbff3f62ee26fb                       KHÔNG ĐỔI
prompts            55ac1ca6a6df92ce                       KHÔNG ĐỔI
```

Thẻ văn phạm không đổi vì nó mô tả **IR tổng hợp**, không liệt kê taxonomy nghĩa
vụ — hai bề mặt khác nhau, và wave này chỉ chạm bề mặt `analyze`.

## 7. CACHE_DECISION

`CACHE_VERSION 77 → 78`. Tiền lệ **68** (`radius` vào taxonomy làm lược đồ
analyze đổi), không phải 70/73/74 (thẻ đổi) hay 75/76 (đầu ra đổi).

Vì sao bắt buộc: envelope đã cache chở một `RequestContract` sinh dưới enum
**cũ** — enum không có hai kind ấy — nên một đề hỏi diện tích đã phân tích trước
đây mang hợp đồng **thiếu đúng nghĩa vụ đề hỏi**, và mọi cổng phía sau phán
quyết trên hợp đồng ấy.

Năm cổng đồng bộ: `main.py` · `test_api.py` · `CURRENT_STATE.md` ·
`test_evaluation_candidate.py` · `cache_identity.lock.json`.

## 8. FAULT_INJECTION

| tiêm | kỳ vọng | thực tế |
|---|---|---|
| gỡ `area` khỏi `OBLIGATION_KINDS` | analyze loại lại | ĐỎ đúng (`test_D4a[area]`) |
| gỡ `lateral_area` khỏi authority | analyze loại lại | ĐỎ đúng (`test_D4a[lateral_area]`) |
| gỡ đăng ký checker từng kind | nghĩa vụ rơi mức yếu | ĐỎ đúng (`test_D4b`) |
| checker nhận SAI MemoryType | type-safety đỏ | ĐỎ đúng (`test_D4c`) |
| khôi phục bộ lọc analyze cũ | reproduction đỏ | ĐỎ đúng (§A tái hiện lại) |

Bốn phép tiêm đầu **nằm trong suite** (`monkeypatch`), không phải một lần thử tay.

## 9. V3_COUNT_ONLY_REMEASUREMENT

Chạy lại **đúng** script count-only của preflight; nội dung `de`/`mong`/tham số
vẫn **chưa đọc**.

```
                                              TRƯỚC   SAU   kỳ vọng
V3_POSITIVE_CASES                                18    18      18
V3_CASES_WITH_ALL_OBLIGATION_KINDS_EMITTABLE      4    18      18  ✅
V3_CASES_WITH_DROPPED_OBLIGATION_KIND            14     0       0  ✅
V3_CENTER_RADIUS_CASES                            4     4       4
V3_CENTER_RADIUS_CONTRACT_UNBLOCKED               0     4       4  ✅
ô dương chỉ chứa ca bị chặn                     7/9   0/9
ca đo được theo hình (ball/cylinder/cone)     2/0/2  6/6/6
```

**Điều này chứng minh gì và KHÔNG chứng minh gì:**

| | |
|---|---|
| ✅ bề mặt obligation của analyze đã đầy đủ cho V3 | 18/18 phát được |
| ❌ **chưa** chứng minh model tổng hợp đúng chương trình | chưa lượt live nào |
| ❌ **chưa** chứng minh derived-radius expressiveness | không suy được từ metadata |
| ❌ **chưa** chứng minh family acceptance hay product support | vẫn `foundation_only` |

## 10. TEST_RESULTS

| gate | lệnh | exit | kết quả |
|---|---|---|---|
| obligation surface (mới) | `pytest tests/geometry/test_area_obligation_surface.py` | 0 | **35 pass** |
| full backend | `pytest -q` | 0 | **3403 pass**, 1 skip, 1 deselect |
| candidate verification | `freeze_evaluation_candidate.py --verify` | 0 | `a696200e8f8c668c…` |
| runner certification | `certify_acceptance_runner.py` | 0 | PASS, 0 lượt gọi |
| cache identity | `pytest tests/test_cache_identity.py` | 0 | 15 pass |
| demo replay | `replay_demo_cases.py` | 0 | 5/5 · reduced 1/1 |
| crash surface | `audit_demo_crash_surface.py` | 0 | 6/6 biên, 0 ném |
| center-radius replay | fixture 3 bán kính | 0 | `13→8788π/3` · `5/2→125π/6` · `√3→4π√3` |
| frontend | `npx vitest run` | 0 | **698 pass / 51 file** |
| frontend build | `npm run build` | 0 | PASS |
| `git diff --check` | — | 0 | sạch |

`SCOPE_REGRESSION_BLOCKED = NO`.

## 11. LIMITATIONS

- Held-out **A** (`seal_geometry_holdout`) **không** có ô cho `area`/
  `lateral_area` — pool niêm phong trước khi chúng tồn tại. Đã khai ở
  `NGHIA_VU_KHONG_CO_O` kèm hệ quả: số của held-out A không nói gì về năng lực
  diện tích.
- Diện tích **toàn phần** vẫn ngoài miền số — có chủ đích.
- `DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3` vẫn
  `NOT_DETERMINABLE_FROM_METADATA`: chữ ký công thức nói bán kính **là tham
  số**, không nói **đề phát biểu nó thế nào** (bán kính 13? đường kính 26?).
  Trả lời được câu ấy phải đọc `de` — tức phá held-out.
- Lớp bài *"đường kính 26"* vẫn đóng (`arith` cho kiểu tĩnh `unknown`) — nợ
  riêng từ wave trước, không thuộc wave này.
- `ten_da_hoa_giai` vẫn phẳng.

## 12. RECOMMENDED_NEXT_ACTION

```
CURVED_V3_RESEAL_AFTER_SURFACE_COMPLETION
```

---

```
AREA_OBLIGATION_ASKABLE                        YES
LATERAL_AREA_OBLIGATION_ASKABLE                YES
AREA_CHECKER_SERVER_OWNED                      YES
LATERAL_AREA_CHECKER_SERVER_OWNED              YES
ANALYZE_OBLIGATION_SURFACE_COMPLETE_FOR_V3     YES
V3_POSITIVE_CASES_WITH_EMITTABLE_KINDS         18/18
V3_CENTER_RADIUS_CONTRACT_UNBLOCKED            4/4
DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3  NOT_DETERMINABLE_FROM_METADATA

NEW_AUTHORITIES                                0
NEW_IR_OPERATIONS                              0
NEW_CURVED_TEMPLATES                           0
NEW_FAMILY_SPECIAL_CASES                       0

ANALYZE_SCHEMA_CHANGED                         YES  a4d5ed7c → 515001b5
SYNTHESIS_SCHEMA_CHANGED                       NO
GRAMMAR_CARD_CHANGED                           NO
PROMPT_CHANGED                                 NO
CAPABILITY_HASH_CHANGED                        YES  8cb3d508 → 85bd3167
CHECKER_RUNTIME_BEHAVIOR_CHANGED               YES  (+2 checker)
CACHE_VERSION_BEFORE                           77
CACHE_VERSION_AFTER                            78

V3_POOL_CHANGED                                NO   36c2153e… (một commit duy nhất)
V3_SEAL_CHANGED                                NO   dab9289
V3_SEED                                        null
RESEAL_PERFORMED                               NO
APPLICATION_LLM_CALLS                          0
PRODUCT_CAPABILITY_CHANGED                     NO   ball/cylinder/cone = foundation_only
CANDIDATE_HASH                                 a696200e8f8c668c…  (89 file)
WORKING_TREE                                   CLEAN
```
