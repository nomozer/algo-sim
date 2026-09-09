# `DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH`

**2026-09-10 · 0 lượt gọi model · 0 lượt gọi provider thật.**

```
DISPLAY_NAME_PASS          10/12 → 12/12
PLACEHOLDER_DISPLAY_NAMES      2 → 0
EXACT_VALUES               12/12 → 12/12  (không đổi một ký tự)
```

---

## §1 · Nguyên nhân — ba lỗ, không phải một

Giả thuyết bàn giao từ `SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW` là
*"`_DANH_TU_NGAN` thiếu `ellipse3`"*. Kiểm lại thì **đúng nhưng chưa đủ**: cùng
một kiểu vắng mặt ở **ba** bảng, và mỗi bảng là một lối rơi khác nhau.

| bảng | vắng `ellipse3` ⇒ | hiện ra |
|---|---|---|
| `_CACH_GOI["intersect_plane_curved_ellipse"]` | không có **câu gọi tên** | `cau = None` |
| `MO_TA_KIEU["ellipse3"]` | nhãn của **vật** rơi về `_bac_ba` | `Đối tượng` |
| `_DANH_TU_NGAN["ellipse3"]` | **cách gọi ngắn** rơi về mặc định | `đối tượng` |

Nên nhãn đại lượng — dựng bằng `f"Diện tích {s[0]}"` với `s[0]` là *cách gọi
ngắn đã bọc* — thành `Diện tích «đối tượng»`.

`ellipse3` vào `MemoryType` từ **2026-09-07**
(`CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION`) nhưng
tầng trình bày không đi theo, và **không có gì bắt nó phải đi theo**. Đó mới là
lỗ thật; hai dòng bảng chỉ là triệu chứng.

### Bản vá — soi gương ca đường tròn, không phát minh cách viết thứ hai

`intersect_plane_curved` (đường tròn giao) đã có đủ ba thứ và cho
`Diện tích «Đường tròn giao của khối cong và mặt phẳng»`. Cùng hình dạng bài
toán, khác đúng một kiểu — nên bản vá dùng đúng khuôn ấy:

```python
"intersect_plane_curved_ellipse": (lambda s: f"Elip giao của {s[0]} và {s[1]}", None)
MO_TA_KIEU["ellipse3"]    = "Elip"
_DANH_TU_NGAN["ellipse3"] = "elip"
```

> **Vì sao không phải `Diện tích elip E`** như ví dụ ở `§1` của đặc tả. `§1` cho
> phép *"điều chỉnh cách viết cho khớp quy ước tên đang dùng trong sản phẩm"*,
> và quy ước ấy — với ca song sinh `p3` — là **câu gọi tên sinh ra từ toán
> hạng**, không phải ký hiệu trần. Ghép `E` vào nhãn còn đòi coi `id` của biến
> là ký hiệu, mà `_KIEU_KY_HIEU_LA_TEN` cố ý chỉ nhận `point3`/`vector3`
> (*"`line_AB` không phải ký hiệu của đường `AB`"*). Học sinh gặp `p3` và `p6`
> cạnh nhau phải đọc ra rằng chúng cùng một phép dựng.

---

## §2 · Nền và kết quả — đo bằng máy, không đọc bằng mắt

`DISPLAY_NAME_PASS = 10/12` đi qua ba wave mà **chưa lần nào có phép đo tự
động**. `backend/scripts/score_display_names.py` là bộ chấm đầu tiên; nó ghi
từng đại lượng với kiểu ngữ nghĩa thật, tên biến, nhãn và phán quyết.

```
BASELINE (fixture tại HEAD)   10/12 · 2 placeholder · FAIL: p6, p7
AFTER    (cây làm việc)       12/12 · 0 placeholder
```

Mười nhãn đang đúng **giữ nguyên từng ký tự** (`§5.3`); hai nhãn đổi:

| ca | trước | sau | giá trị |
|---|---|---|---|
| `p6` | `Diện tích «đối tượng»` | `Diện tích «Elip giao của khối cong và mặt phẳng»` | `25π√5` |
| `p7` | `Diện tích «đối tượng»` | `Diện tích «Elip giao của khối cong và mặt phẳng»` | `2π√6` |

**Bằng chứng cho `§4` — nhãn KHÔNG dẫn từ tên biến.** Hai ca đặt tên biến khác
hẳn nhau (`dien_tich_elip_e` ở `p6`, `dien_tich_E` ở `p7`) mà cho **cùng một
nhãn**. Nếu nhãn dẫn từ chính tả thì hai ca phải khác nhau.

---

## §3 · Chống tái phát — phần đáng giá nhất của wave

Sửa ba dòng bảng thì lần sau kiểu thứ mười một lại lọt. Nên
`test_moi_kieu_hinh_hoc_deu_co_danh_tu_tieng_viet` quét **mọi kiểu hình học
trong `MemoryType`** và đòi mỗi kiểu có tên tiếng Việt. Thêm một kiểu mà quên
bảng ⇒ **ĐỎ ở test**, thay vì hiện *"đối tượng"* trên màn hình học sinh vài
wave sau — đúng cách `ellipse3` đã lọt.

Lối rơi cuối (`"Đối tượng"` cho kiểu lạ) giữ **nguyên và nghèo** có chủ đích:
một kiểu chưa có tên phải trông sai ngay, chứ không được in định danh máy.

### Phép tiêm — 4/4 đạt kỳ vọng

| # | tiêm | kỳ vọng | kết quả |
|---|---|---|---|
| 1 | gỡ `_DANH_TU_NGAN["ellipse3"]` | ĐỎ | `DETECTED` |
| 2 | gỡ câu gọi tên ⇒ khôi phục `«đối tượng»` | ĐỎ | `DETECTED` |
| 3 | **đổi tên biến, giữ kiểu** | **VẪN XANH** | `INVARIANT_HELD` |
| 4 | frontend bỏ nhãn có cấu trúc | ĐỎ | `DETECTED` |

⚠️ Phép **3 ngược chiều** và cần thiết đúng bằng ba phép kia: một bộ tiêm chỉ
toàn *"phá thì đỏ"* không phát hiện được lỗi *"nhãn dẫn từ chính tả tên biến"*.

⚠️ Phép **4 bắt được một lỗ trong chính guard của tôi**: guard kiến trúc bản đầu
hỏi `src.toContain("{o.label}")` trên **cả tệp**, mà `{o.label}` còn xuất hiện ở
chỗ vẽ nhãn điểm — nên bỏ nhãn ô đọc số vẫn xanh. Đã siết vào đúng khối
`geo3d-readout`. Đây chính là việc phép tiêm sinh ra để làm.

---

## §4 · Cache — bump, và đây là hạng bump KHÁC HẲN mọi lần trước

`PRODUCT_RESPONSE_CONTRACT_ALIGNMENT` kết luận *"không bump"* vì nó chỉ đổi phản
hồi **từ chối**, mà `main.py` chỉ cache `status == "ok"`. Ở đây thì ngược hẳn:
nhãn nằm **bên trong** `scene3d.objects[].label` của một envelope `ok` — đúng
loại envelope **được** cache.

Đo bằng **row thật** (`CACHE_IMPACT.json`): ghi một row `policy_version = 94`
mang nhãn cũ, rồi gọi lại `/api/analyze`:

```
nhan_trong_envelope_TRUOC_va   : ["Diện tích «đối tượng»"]
nhan_route_TRA_VE_khi_co_row_cu: ["Diện tích «đối tượng»"]   ← trả THẲNG row cũ
provider_bi_goi                : 0
ROW_CU_DUOC_TRA_THANG          : true
```

`_cache_lookup` khớp `policy_version` rồi route trả `{**json.loads(row.envelope_json)}`
— **nguyên envelope cũ**. Học sinh đọc nhãn cũ trên mã đã sửa, và không cổng nào
kêu. Bump là cách **duy nhất** làm row ấy miss.

⇒ **`CACHE_VERSION 94 → 95`**, đủ bốn chỗ trong một commit theo nghi thức kho
(`main.py` · assert khoá ở `test_api.py` · bảng danh tính `CURRENT_STATE` ·
`test_evaluation_candidate`), cộng `lock_cache_identity.py` khoá lại.
Model-facing **5/5 KHÔNG đổi** — wave không chạm prompt, lược đồ hay năng lực.

---

## §5 · Danh tính — bốn thứ, bốn trường

```
historical_live_candidate   d72db7c3…   hệ mà lượt LIVE đã đo (bất biến)
previous_release_candidate  e40de3b1…   bản phát hành trước wave này
current_release_candidate   96a9368b…   bản đang đóng gói
live_evidence_unchanged     45 tệp · băm CÂY ghi trong manifest
```

Bump `CACHE_VERSION` làm **hai** cờ của con dấu lượt đo lệch, không chỉ một.
Sáu guard đỏ theo, và cả sáu đều thuộc cùng một lớp đã xử ở wave trước: chúng
cưỡng chế *"kho vẫn đang ở đúng hệ đã đo"* — một câu **tạm thời** bị viết như
bất biến. Cách xử giữ nguyên tinh thần ấy:

* **Bốn guard đăng ký lịch sử** (`missing_family_roadmap`, `nonconvex…`, hai
  `oblique_ellipse…`) đã có sẵn khuôn *"đăng ký giữ N, hệ ở M vì wave X"* — chỉ
  cập nhật M kèm lý do. Thứ chúng thật sự bảo vệ là **năm băm model-facing**, và
  năm băm ấy không đổi một byte.
* **`test_B1_G1`** xét `CACHE_VERSION_MATCH` riêng **cùng lý do** với
  `CANDIDATE_HASH_MATCH`, và đòi cả hai khớp văn bản khai
  (`CANDIDATE_DIVERGENCE.json` nay chở thêm `cache_version_hien_tai`).
* **`test_F12/F13`** (về TRẦN ngân sách) ghim cả hai trường trong bản sao tmp.

**Không** sửa `thesis_final_acceptance_policy.json`, **không** chấm lại số của
lượt live, **không** ghi vào thư mục artifact lịch sử một byte nào.

---

## §6 · Cổng

| cổng | kết quả |
|---|---|
| `pytest -q` | **4823 pass**, 1 skip, 1 deselect — 0 đỏ, cây sạch |
| `vitest run` | **816 pass** / 55 file |
| `npm run build` | PASS |
| product UI (Chrome thật) | **73/73** · 9 ảnh · ngoại lệ 0 |
| refusal surface (bản dựng) | **21/21** · console 0 |
| Scene3D hidden-line | **23/23** |
| world-space oracle | **7/7** tolerance 0 |
| `replay_demo_cases` · `audit_demo_crash_surface` | exit 0 · 6/6 biên |
| đối chiếu đáp số | **12/12** · 0/31 trường lệch |
| `freeze --verify` · `lock_cache_identity --verify` | exit 0 · exit 0 @ v95 |
| tiêm lỗi | **4/4** |
| artifact lượt live | **45/45 BYTE-IDENTICAL** |
| `git diff --check` | sạch |

---

## §7 · Giới hạn — nói thẳng

* **`curved_solid` vẫn được NHẮC bằng danh từ chung.** Bốn nhãn (`p4`, `p5`,
  `p6`, `p7`) chứa *«khối cong»* trong khi `curved_kind` biết rõ đó là hình trụ
  hay hình nón — nhãn của chính khối ấy đã ghi `Hình trụ`. Sửa được, nhưng nó
  **đổi bốn nhãn**, trong đó hai nhãn thuộc mười nhãn mà `§5.3` yêu cầu **giữ
  nguyên**. Nên không sửa ở wave này; ghi thành nợ
  `CURVED_KIND_IN_SHORT_REFERENCE`.
* **Chỉ `p6`/`p7` được kiểm bằng mắt trên bản dựng.** Các ca còn lại đi qua
  cổng tự động (73/73) và ảnh demo, không soi từng ảnh.
* **`FEATURE_DEVELOPMENT_STATUS` mở lại đúng một lần** cho wave này theo yêu
  cầu, rồi đóng lại. Đây là bản vá TÊN HIỂN THỊ, không phải tính năng mới:
  `NEW_GEOMETRY_FAMILIES = 0`, `NEW_IR_OPERATIONS = 0`, `NEW_MEMORY_TYPES = 0`.
* Guard `test_holdout_readiness_7b` đỏ theo thiết kế khi cây bẩn.

---

## §8 · Bàn giao

```
docs/evaluation/geometry/display-name-final-polish/
  BASELINE.json                 10/12, chấm trên fixture TẠI ref git (đo lại được)
  AFTER.json                    12/12, 0 placeholder
  CACHE_IMPACT.json             row thật · ROW_CU_DUOC_TRA_THANG = true
  FAULT_INJECTIONS.json         4/4 (một phép NGƯỢC CHIỀU)
  SCREENSHOTS.json              4 ảnh, kèm băm đề · băm envelope · camera · candidate
  RELEASE_REFRESH_MANIFEST.json bốn danh tính, bốn trường
  screenshots/                  p6, p7 và hai ảnh sau xoay
```
