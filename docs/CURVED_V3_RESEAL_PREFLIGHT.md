# CURVED_V3_RESEAL_PREFLIGHT

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `RESEAL_PERFORMED = NO` ·
> seal V3 giữ nguyên · `seed` vẫn `null` · pool **chưa bị đọc nội dung**.

```
APPLICATION_LLM_CALLS                        0
CURRENT_CANDIDATE_HASH                       54a47ae5670eb77f…  (89 file)
CACHE_VERSION                                77
V3_POOL_HASH                                 36c2153ecefd2dbf…  (khớp con dấu)
EXPECTED_RESULTS_HASH                        (không có trường riêng — xem §A4)
RUNNER_CERTIFICATION                         PASS  (exit 0, 0 lượt gọi)
V3_PROVENANCE_VERDICT                        CLEAN_HELD_OUT  (kèm cảnh báo §B3)
V3_CAN_MEASURE_CENTER_RADIUS_DISCOVERABILITY NO
ANALYZE_OBLIGATION_SURFACE_COMPLETE_FOR_V3   NO
DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3 NOT_DETERMINABLE_FROM_METADATA
RESEAL_PERFORMED                             NO
READY_FOR_V3_EXECUTION                       NO  →  BLOCKED
PRODUCT_CAPABILITY_CHANGED                   NO  (ball·cylinder·cone = foundation_only)
WORKING_TREE                                 CLEAN  (HEAD 22019a4)
```

## Kỷ luật held-out của chính lượt này

Tôi là **tác nhân triển khai** — người vừa viết ô `radius`. Đọc nội dung ca đo
V3 sẽ tự tay huỷ tính held-out của nó. Nên lượt này:

- **KHÔNG đọc** `de`, `mong`, tham số công thức, hay id-kèm-nội-dung;
- chỉ dùng **con dấu** (`V3_SEAL.json`), **mã nguồn** bộ niêm phong (công khai),
  và **tổng hợp chỉ-đếm** tính bằng script in ra duy nhất các con số;
- ⚠️ Một rò rỉ cấp thấp phải khai: lượt tiêm lỗi ① chạy `_rut` trong **sandbox**
  với seed **20260904 do tôi tự chọn**, và nó in 13 **id** được rút. Đó là id,
  không phải nội dung; seal sandbox đã huỷ; seed thật đến từ ngoài nên tập rút
  thật sẽ khác. Ghi lại để người sau tự chấm mức độ, không tự xoá.

## A · DANH TÍNH

| | giá trị |
|---|---|
| HEAD · cây làm việc | `22019a4` · **CLEAN** |
| candidate (mã sản phẩm) | `54a47ae5670eb77f…` · **89 file** |
| `CACHE_VERSION` | **77** |
| grammar_card | `24e550ad1c57a2aa…` |
| analyze_schema | `a4d5ed7c65a68007…` |
| synthesis_schema | `82dbff3f62ee26fb…` |
| prompts | `55ac1ca6a6df92ce…` |
| capability = `stable_capability_hash` | `8cb3d5081bfcb7f7…` |
| `semantic_environment_hash` | `e9492e6354e0c813…` |
| V3 pool_hash | `36c2153ecefd2dbf…` — **tính lại KHỚP** |

Danh tính bộ đo: `run_curved_acceptance.py 11e4b620…` ·
`acceptance_integrity.py 323ced72…` · `acceptance_verdict.py 98cc19c8…` ·
`certify_acceptance_runner.py 07c550f5…` · `seal_curved_v3.py 4b17faf2…`

### A4 — seal trỏ đi đâu, lệch ở đâu

| trường trong seal | giá trị | hiện tại | lệch? |
|---|---|---|---|
| `pool_hash` | `36c2153e…` | `36c2153e…` | **không** |
| `measured_system_hash` | `4d8bfb51…` (89 file) | `54a47ae5…` (89 file) | **LỆCH** |
| `seed` · `da_rut` | `null` · `null` | — | chưa rút |

**Không có `expected_results_hash` riêng.** Kỳ vọng (`mong`) nằm *bên trong*
pool, nên `pool_hash` bao trùm nó: pool và kỳ vọng không thể trôi độc lập. Đó là
một tính chất tốt, nhưng cũng nghĩa là **không thể xác nhận kỳ vọng còn nguyên
mà không xác nhận cả pool** — ghi lại, không phải lỗi.

### Phân loại thay đổi giữa seal và hiện tại

| loại | có đổi? | bằng chứng |
|---|---|---|
| **model-facing** | **CÓ** | `grammar_card` `e0790ba8→24e550ad` · `synthesis_schema` `8e47707d→82dbff3f` (wave 77) |
| **runtime/checker** | **CÓ** | `capability` `5b61b9ea→8cb3d508`; `CurvedSolid` thêm `radius_sq_khai` |
| **scene output** | **CÓ** | wave 76: `objects[].depends` của vật dẫn xuất |
| **chỉ seal/metadata** | không | seal chưa được chạm từ `dab9289` |

Nên đây **không phải** lệch metadata đơn thuần — hệ được đo đã đổi thật ở cả ba
trục. Chính `seal_curved_v3._rut` cũng chặn: *"hệ đã đổi sau khi niêm phong —
niêm phong lại trước"*.

## B · TÍNH HELD-OUT

```
V3_PROVENANCE_VERDICT = CLEAN_HELD_OUT
```

| # | câu hỏi | trả lời | bằng chứng |
|---|---|---|---|
| 1 | nội dung V3 có dùng để thiết kế wave 75–77? | **KHÔNG** | `git diff --stat dab9289 HEAD -- curved-v3/` = **rỗng**; ba design record chỉ nhắc *trạng thái* V3 (`NOT RUN`, `pool sealed`), không nhắc ca nào |
| 2 | artifact `ball_2` thúc đẩy `radius_sq` thuộc corpus nào? | **V1/V2**, không phải V3 | truy vấn thành viên: `'ball_2' in pool_ids` → **False**. `ball_2` khai trong `run_curved_acceptance.py`, corpus phát triển |
| 3 | agent sửa hệ có đọc payload V3 không? | **không chứng minh được bằng git** | đọc không để lại dấu. Cái *chứng minh được*: thiết kế dẫn từ corpus rời, và không commit nào chạm V3. Người soạn pool **tự khai không độc lập** với V1/V2 (`ghi_chu_doc_lap`) — giới hạn có sẵn, không phải nhiễm mới |
| 4 | pool_hash + expected giữ nguyên từ lần niêm phong đầu? | **CÓ** | `POOL.json` có **đúng một** commit (`dab9289`); băm tính lại khớp con dấu |
| 5 | tái niêm phong có đổi bản chất held-out? | **KHÔNG** | `--niem-phong` băm lại pool **không đổi byte** và ghi lại `measured_system_hash`; `seed` vốn `null` nên không mất gì |

Verdict `CLEAN_HELD_OUT` áp cho **trục nội dung**: không có bằng chứng nào cho
thấy V3 định hình bản vá, và có bằng chứng dương rằng corpus khác đã làm việc đó.

## C · V3 CÓ ĐO ĐÚNG THỨ CẦN ĐO KHÔNG

### Bảng coverage aggregate (chỉ đếm, dẫn từ `cong_thuc` — từ vựng đóng 14 mục)

| | ca |
|---|---|
| pool | **26** (18 dương · 8 âm) |
| hình cầu · trụ · nón | 8 · 6 · 6 |
| bán kính cầu **là dữ kiện** (lớp center+radius) | **4** |
| bán kính cầu **dẫn xuất** (ngoại tiếp) | 2 |

Lượng đo pool đòi → nghĩa vụ hệ:

| nghĩa vụ | số lần | `analyze` phát được? |
|---|---|---|
| `volume` | 6 | ✅ |
| `radius` | 8 | ✅ |
| `distance` | 2 | ✅ |
| **`area`** | **8** | ❌ **không có trong `OBLIGATION_KINDS`** |
| **`lateral_area`** | **6** | ❌ **không có trong `OBLIGATION_KINDS`** |

### Hệ quả — đây là BLOCKER, không phải nợ ngoài phạm vi

`analyze_contract` **loại im lặng** nghĩa vụ có `kind` ngoài `OBLIGATION_KINDS`
(dòng 489). Đếm theo **CA**:

```
ca dương                                18
  mọi nghĩa vụ analyze PHÁT ĐƯỢC         4     ← ball 2 · cone 2 · cylinder 0
  có nghĩa vụ BỊ LOẠI IM LẶNG           14
center+radius (R là dữ kiện)             4
  … VÀ đo được                           0
  … NHƯNG bị chặn                        4
```

Và phép rút là **một ca mỗi ô**:

```
ô dương chỉ chứa ca BỊ CHẶN:  C1 C2 C4 C5 C6 C7 C8   →  7/9 ô
ô dương còn đo được:          C3, C9                 →  2/9 ô
```

Chạy V3 bây giờ ⇒ **7 trong 9 ô dương chắc chắn hỏng** vì một khiếm khuyết
*hợp đồng analyze*, không phải vì năng lực tổng hợp hình cong. Và `--rut` **từ
chối rút lần hai**, nên lượt chạy ấy tiêu vĩnh viễn một pool held-out để lấy một
con số 78% là nhiễu.

### Verdict từng mục

```
V3_CAN_MEASURE_GENERAL_CURVED_SYNTHESIS       NO   (4/18 ca dương đo được)
V3_CAN_MEASURE_CENTER_RADIUS_DISCOVERABILITY  NO   (4 ca có, 0 ca đo được)
V3_CAN_MEASURE_BALL                           PARTIAL (2/8 — cả hai là NGOẠI TIẾP,
                                                       bán kính DẪN XUẤT)
V3_CAN_MEASURE_CYLINDER                       NO   (0/6)
V3_CAN_MEASURE_CONE                           PARTIAL (2/6)
ANALYZE_OBLIGATION_SURFACE_COMPLETE_FOR_V3    NO
DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3 NOT_DETERMINABLE_FROM_METADATA
```

`DERIVED_RADIUS…`: chữ ký công thức cho biết bán kính **là tham số**, nhưng
không cho biết **đề phát biểu nó thế nào** (bán kính 13? đường kính 26?). Trả
lời được câu ấy phải đọc `de` — tức phá held-out. Để **NOT_DETERMINABLE**, không
đoán.

### C6–C7 · scorer phân biệt được gì (đọc mã, không đọc pool)

`acceptance_verdict.co_giai_doan` phát **bảy cờ riêng biệt** trên
`stage_reached`: `schema_valid · grounding_pass · coverage_pass · static_valid ·
runtime_executable · postconditions_pass · servable`, cộng `trich_ket_qua` đọc
`outcome.final_memory` (khớp đáp số chính xác) và `scene3d` dựng riêng.
`phan_loai` tách **model error ↔ system error** bằng 13 lớp
(`LOP_PHAN_QUYET`), có `_cong_phu_hep_hon_bo_kiem` và
`nghia_vu_du_noi_dung_hut_ten` để không đổ lỗi hệ cho mô hình và ngược lại.

`run_curved_ergonomics_v2` giữ **mọi attempt** (`raw_candidates`, `theo_luot`)
và đếm cả lượt hỏng vào mẫu số. ⇒ **C6 = ĐỦ · C7 = ĐỦ.**

## D · QUYẾT ĐỊNH TÁI NIÊM PHONG

| điều kiện §D | đạt? |
|---|---|
| provenance `CLEAN_HELD_OUT` | ✅ |
| runner certification PASS | ✅ exit 0 |
| pool + expected byte-identical | ✅ |
| candidate hiện tại xác minh | ✅ exit 0 |
| **nghĩa vụ trong pool có đường analyze hợp lệ** | ❌ **14/18 ca không có** |
| scorer đo đúng claim | ✅ |

**Một điều kiện KHÔNG đạt ⇒ `BLOCKED`.** Giữ nguyên seal hiện tại; **không**
tái niêm phong. Tái niêm phong bây giờ chỉ làm `_rut` thôi chặn — tức gỡ đúng
cái phanh đang cứu pool khỏi bị tiêu cho một phép đo hỏng.

## E · TIÊM LỖI

Sandbox `tempfile`, không đụng seal/pool thật.

| # | tiêm | kết quả |
|---|---|---|
| ① | nền, seal trỏ đúng candidate hiện tại | **XANH** (rút được) |
| ② | candidate hash CŨ trong seal | **ĐỎ** — *"hệ đã đổi sau khi niêm phong"* |
| ③ | đổi **một byte** bản sao pool | **ĐỎ** — *"pool ĐÃ TRÔI khỏi con dấu"* |
| ④ | `pool_hash` trong seal bị sửa | **ĐỎ** — *"pool ĐÃ TRÔI khỏi con dấu"* |
| ⑤ | seal đã có seed (rút lần hai) | **ĐỎ** — *"không rút lần hai"* |

Khôi phục: `pool_hash` khớp dấu **True** · `seed` **null** · `da_rut` **null**.

## Cổng đã chạy

| gate | lệnh | kết quả |
|---|---|---|
| runner certification | `certify_acceptance_runner.py` | exit **0**, PASS, 0 lượt gọi |
| candidate verification | `freeze_evaluation_candidate.py --verify` | exit **0** |
| seal verification | `_rut` trong sandbox (§E) | 1 xanh / 4 đỏ đúng kỳ vọng |
| cache identity | `pytest tests/test_cache_identity.py` | **15 pass** |
| center-radius foundation | `pytest tests/geometry/test_center_radius_ball.py` | **27 pass** |
| curved foundation + integrity | `pytest …test_curved_foundation.py …test_acceptance_runner_integrity.py` | **108 pass** |
| replay tất định center-radius | fixture 3 bán kính | `13 → 8788π/3` · `5/2 → 125π/6` · `√3 → 4π√3`, đều `served` |
| full backend | `pytest -q` | **3362 pass**, 1 skip, 1 deselect |
| `git diff --check` | — | exit **0**, cây sạch |

## Giới hạn phép đo còn lại

- **hệ biểu đạt được** center+radius: ✅ có test (wave 77).
- **engine thực thi đúng**: ✅ ba giá trị chính xác.
- **AI tự phát hiện và tổng hợp được**: ❌ **chưa đo** — và V3 hiện **không đo
  được** nó.
- **ổn định qua acceptance**: ❌ chưa có phép đo hợp lệ để nói.
- **đủ điều kiện lên `supported`**: ❌ không family nào; giữ `foundation_only`.
- `area`/`lateral_area` **tính được nhưng không hỏi được** — trước đây ghi là nợ
  ngoài phạm vi; **lượt này chứng minh nó là blocker của V3**, vì pool dùng
  chúng ở 14/18 ca dương.

## RECOMMENDED_NEXT_ACTION

```
ANALYZE_OBLIGATION_SURFACE_COMPLETION
```

Nâng `area` và `lateral_area` từ **lượng đo** lên **nghĩa vụ**: thêm vào
`BANG_PHEP_DO`-dẫn-xuất `NGHIA_VU_DO` và viết **hai checker server-owned**
(`check_area`, `check_lateral_area`). Cả hai công thức đã có sẵn và chính xác
trong kernel (`dien_tich_hinh_tron`, `dien_tich_mat_cong`), nên đây là wave
**nhỏ và tất định, 0 lượt gọi model**.

Nó mở khoá **14/18 ca dương** và **7/9 ô** — biến V3 từ một phép đo 78% nhiễu
thành một phép đo dùng được, mà **không** chạm pool, seed hay bất kỳ tuyên bố
lịch sử nào.

Chỉ **sau** wave ấy mới tái niêm phong V3 rồi chạy acceptance. Hai hướng còn lại
của đề bài bị loại bằng bằng chứng: *"giữ V3 cho tuyên bố cũ + acceptance riêng
cho center+radius"* là dựng phép đo thứ hai cho một lỗ dùng chung, và *"xếp V3
replay-only + pool mới"* vứt một pool **vẫn còn nguyên vẹn và vẫn held-out** vì
một khiếm khuyết nằm ở hệ, không ở pool.
