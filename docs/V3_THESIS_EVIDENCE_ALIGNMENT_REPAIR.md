# V3_THESIS_EVIDENCE_ALIGNMENT_REPAIR

> Nhánh `feat/photo-problem-to-scene` · 2026-09-20.
> START_HEAD `58770bb` · commit mã `b3530fc` · `main` giữ `085cae6` (không đổi).
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/v3-thesis-evidence-alignment-repair/`.
> **0 request Gemini · 0 request mạng.**

```text
V3_THESIS_EVIDENCE_ALIGNMENT_REPAIR = PASS
H6_ROOT_CAUSE_CLASS                 = C — MEASUREMENT_OR_GENERATOR_BUG
V3_PARITY_ROOT_CAUSE_CLASS          = C — MEASUREMENT_OR_GENERATOR_BUG
PRODUCT_CODE_CHANGED                = NO   (backend/app diff = 0)
PRODUCT_BEHAVIOR_CHANGED            = NO
V3_ARTIFACT_REGENERATED             = NO   (không tệp bằng chứng nào bị ghi lại)
FULL_BACKEND (clean worktree)       = 5323 passed / 2 failed  →  5349 passed / 0 FAILED
CANDIDATE_HASH                      = b42f17f4… → b42f17f4… (không đổi)
CACHE_VERSION                       = 97 → 97
```

## 1. Một nguyên nhân gốc cho cả hai lỗi

Hai test **đỏ trong mọi worktree mới mà xanh ở cây nguồn** — cùng một commit,
hai phán quyết. Đó là dấu hiệu phép đo phụ thuộc môi trường, không phải bằng
chứng bị trôi.

Kho đặt `core.autocrlf = true` và **không có `.gitattributes`**, nên git viết
CRLF ra đĩa trong khi blob giữ LF. Cả hai test băm **byte thô**
(`sha256(path.read_bytes())`), nên chúng đo **lượt checkout**, không đo nội dung.

Đo được trên `curved-acceptance-v3/manifest.json` tại cùng commit `58770bb`:

| | LF | CR | size | sha256 |
|---|---|---|---|---|
| cây nguồn | 149 | **0** | 4936 | `b2a454f0…` ✅ |
| worktree mới | 149 | **149** | 5085 | `4059f9db…` ❌ |
| **blob (git)** | 149 | **0** | 4936 | `b2a454f0…` |

Chênh lệch đúng **149 byte = số dòng**. Blob khớp cây nguồn.

## 2. Bằng chứng KHÔNG hề bị sửa

Điều này phải chứng minh trước, vì nếu sai thì đây là một lớp lỗi hoàn toàn khác:

- Cả **bốn** tệp nguồn V3 có **đúng một commit** (`85b584c`, 2026-09-05).
  `git log -- <file>` cho `commits=1` với từng tệp.
- Băm **blob** của chúng khớp bản đã công bố.
- Ba tệp của H6 cũng vậy: băm ghi trong `SCORING_CORRECTION.json` **chính là**
  băm blob, nên H6 **không phải sửa một hằng số nào**.

## 3. Vì sao chỉ `manifest.json` đỏ — và đó là chỗ bẫy

`BAM_NGUON` cũ **tự mâu thuẫn**: ba giá trị đo trên bản **CRLF**, một
(`manifest.json`) đo trên bản **LF**. Khi ghi 2026-09-05, `manifest.json` tình
cờ đang là LF trên đĩa.

Ở worktree mới cả bốn đều CRLF ⇒ ba khớp, một lệch. Chính sự **khớp bộ phận** ấy
làm bộ test trông như đang hoạt động, và giấu lỗi suốt từ 2026-09-05.

## 4. Sửa — đúng công cụ đo, không chạm sản phẩm

Theo `§6 MEASUREMENT_OR_GENERATOR_BUG`, và theo **tiền lệ đã có trong kho**
(`tests/geometry/test_phase7b_baseline_immutable.py::_bam`): chuẩn hoá
`\r\n` → `\n` trước khi băm. Một cách chuẩn hoá cho mọi phép kiểm bất biến của
bằng chứng, không hai.

**H6**: đổi đúng một dòng. Không hằng số nào đổi.

**V3 parity**: `BAM_NGUON` **giữ nguyên từng ký tự** — những con số ấy đã công
bố trong `V3_PRODUCT_PATH_PARITY_CORRECTION.json` **và**
`docs/CURVED_V3_LIVE_ACCEPTANCE.md`; viết lại là viết lại bằng chứng đã xuất
bản. Thay vào đó:

- `BAM_NGUON` giữ vai trò **bản ghi lịch sử**, `test_02` vẫn đối chiếu nó với
  artifact đính chính;
- thêm `BAM_NOI_DUNG` = băm của **bản đã commit**, và `test_01` chuyển sang đó;
- `test_23` chứng minh hai bảng mô tả **cùng một tệp**: mỗi giá trị lịch sử phải
  là băm LF **hoặc** CRLF của chính blob ấy. Nếu giả thuyết *"chỉ là lượt
  checkout"* sai, chính test này sẽ đỏ.

## 5. Test hồi quy — và một lỗ hổng phép tiêm lỗi tìm ra

| test | bắt điều gì |
|---|---|
| `test_19` | còn ký tự `\r` lẻ sau chuẩn hoá (một lớp khác, không được che) |
| `test_20` | **cửa sổ chứng** — LF và CRLF của cùng nội dung cho **cùng** băm |
| `test_21` | chuẩn hoá **không làm phép đo mù**: đổi một byte nội dung vẫn ĐỎ |
| `test_22` | hằng số khớp blob đọc thẳng qua `git cat-file` — không đi qua đĩa |
| `test_24` | **phạm vi đăng ký không được thu hẹp** |

⚠️ **`test_24` sinh ra vì phép tiêm F3 lọt hoàn toàn.** Gỡ `attribution.json`
khỏi bảng đăng ký cho **36 passed, 0 failed**: bộ test parametrize theo chính
bảng ấy, nên xoá một mục chỉ làm **ít ca đi** chứ không đỏ. Đó là cách làm xanh
mà không sửa gì, và không test nào đang chặn.

## 6. Không đụng sản phẩm

```
backend/app          0 file đổi
frontend/src         0 file đổi
app/ai/skills        0 file đổi
docs/schemas         0 file đổi
```

Chỉ **hai tệp test** đổi. `CACHE_VERSION` giữ 97, candidate giữ `b42f17f4…`
(wave không chạm `MEASURED_SYSTEM_PATHS`). Section normalization 29/29 và visual
obligation gate 35/35 — không hồi quy.

Nếu buộc phải sửa product để làm test xanh, `§6` bắt dừng với
`PRODUCT_REGRESSION`. Điều đó **không** xảy ra.

## 7. Giới hạn

1. **Nguyên nhân gốc trong `.git/config` vẫn còn.** Wave sửa *phép đo*, không sửa
   `core.autocrlf` và không thêm `.gitattributes` — đó là thay đổi phạm vi toàn
   kho, sẽ ảnh hưởng mọi tệp và mọi test băm byte khác, nên không thuộc wave này.
   Hệ quả: một test **mới** băm byte thô sẽ mắc lại đúng lỗi này. Cách phòng đã
   có sẵn — dùng `_bam` chuẩn hoá, và `test_22` là khuôn mẫu.
2. **Chỉ hai test được soát.** Kho còn nhiều chỗ băm `read_bytes()`
   (`test_benchmark_seal`, `test_counter_decomposition`,
   `test_v3_threshold_and_run_identity`…). Chúng hiện **xanh ở cả hai cây**, nên
   nằm ngoài phạm vi; nhưng chúng xanh vì hai vế co giãn cùng nhau, không vì
   chúng miễn nhiễm.
3. **`V3_SEAL.json`** trong `source_artifact_hashes` cũng là băm CRLF; nó không
   thuộc `BAM_NGUON` nên không test nào chạm, và wave không đổi nó.

```text
TOKEN_OPTIMIZATION = NOT_RUN
MERGE_ALLOWED      = NO
NEXT_ACTION        = GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE
```
