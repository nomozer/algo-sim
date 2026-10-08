# CURVED_V3_RESEAL_AFTER_SURFACE_COMPLETION

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `LIVE_V3_EXECUTED = NO` ·
> `seed` vẫn `null` · pool **chưa bị đọc nội dung**.

## 1. PRE_RESEAL_IDENTITY

HEAD `609510f`, cây SẠCH trước mọi thao tác.

| | giá trị |
|---|---|
| candidate | `a696200e8f8c668c…` · **89 file** (83 backend + 6 frontend) |
| `CACHE_VERSION` | **78** |
| grammar_card | `24e550ad1c57a2aa…` |
| analyze_schema | `515001b503af5c7c…` |
| synthesis_schema | `82dbff3f62ee26fb…` |
| prompts | `55ac1ca6a6df92ce…` |
| capability | `85bd316781b86576…` |
| semantic_environment | `30502a4404cbe6aa…` |
| pool_hash (tính lại) | `36c2153ecefd2dbf…` — khớp con dấu |
| seal cũ: `measured_system_hash` | `4d8bfb51692b7b84…` (89 file) |
| seal cũ: `seed` · `da_rut` | `null` · `null` |

Bộ đo: `run_curved_acceptance 11e4b620…` · `acceptance_integrity 323ced72…` ·
`acceptance_verdict 98cc19c8…` · `certify_acceptance_runner 07c550f5…` ·
`seal_curved_v3 4b17faf2…`

### Không có vòng tự tham chiếu danh tính

`MEASURED_SYSTEM_PATHS` = `backend/app` · `frontend/src/simulations/domains/semantic`
· mirror schema. Quét 89 file: **0 file thuộc `docs/`**, không có `V3_SEAL.json`,
không có báo cáo này. (11 file `.md` trong candidate là **skill prompt**
`app/ai/skills/*.md` — chúng thuộc hệ được đo, đúng chỗ.)

⇒ `CANDIDATE_SEAL_IDENTITY_CYCLE = NO`, và §7 đo lại xác nhận bằng thực nghiệm.

### Nguồn của lệch candidate `4d8bfb51…` → `a696200e…`

| wave | model-facing | runtime/checker | scene output | metadata |
|---|---|---|---|---|
| `GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE` (76) | — | — | **`objects[].depends`** | cache 76 |
| `CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION` (77) | **grammar_card · synthesis_schema** | **capability** (+`radius_sq_khai`) | — | cache 77 |
| `ANALYZE_OBLIGATION_SURFACE_COMPLETION` (78) | **analyze_schema** | **capability** (+2 checker) | — | cache 78 |

Ba wave, ba trục khác nhau. Không wave nào chạm `POOL.json`.

## 2. HELD_OUT_PROVENANCE

```
V3_PROVENANCE_VERDICT = CLEAN_HELD_OUT
```

Giữ nguyên kết luận preflight, cộng bằng chứng mới của lượt này:

- `POOL.json` vẫn **đúng một commit** (`dab9289`), sha256 `ba35870c…` **không
  đổi một byte** trước và sau reseal (`git diff --stat` rỗng);
- lượt này **không đọc** `de`, `mong`, tham số, đáp số, hay ánh xạ id → nội dung;
- chỉ dùng: con dấu · pool hash · candidate hash · mã công khai của
  sealer/runner/scorer · aggregate chỉ-đếm · git history.

### ⚠️ Rò rỉ đã biết — phân loại và cập nhật

Preflight ghi: một phép tiêm sandbox đã in **13 case id** dưới seed giả
`20260904`. Lượt này tiêm thêm và in **13 id** nữa dưới seed giả `20260905`.

**Phân loại: RÒ RỈ CẤU TRÚC, KHÔNG PHẢI RÒ RỈ NỘI DUNG.** Lý do đo được:

- con dấu **đã công khai** `pool_size = 26` và `13 ô` ⇒ mỗi ô đúng **2 bài**,
  và `_niem_phong` từ chối niêm phong nếu một ô có < 2 bài;
- nên tập id là `{ô}×{a,b}` — suy ra được từ con dấu mà không cần lượt tiêm nào;
- hai lượt sandbox cho **hai tập khác nhau** (`c1a…` vs `c1b…`), tức seed thật
  sự đổi lựa chọn ⇒ biết một lượt rút giả **không nói gì** về lượt rút thật;
- **không** nội dung nào bị lộ: id không mang đề, không mang đáp số.

**Cứng hoá cho lần sau (nợ, không phải blocker):** `seal_curved_v3.py` chưa có
chế độ `--kiem` không tiêu thụ, nên phép xác minh phải chạy `_rut` và `_rut`
thì in id. Thêm một mode chỉ kiểm hai vị ngữ (`pool_hash`,
`measured_system_hash`) sẽ bỏ hẳn lớp rò rỉ này.

Lượt live vẫn phải dùng **seed từ ngoài** và **evaluator độc lập**.

## 3. KNOWN_BLOCKER_RECHECK

| # | kiểm | kết quả |
|---|---|---|
| 1 | candidate verify | **PASS** exit 0 |
| 2 | runner certification | **PASS** exit 0, 0 lượt gọi |
| 3 | cache identity @78 | **15 pass** |
| 4 | `area` ∈ obligation authority | **True** |
| 5 | `lateral_area` ∈ obligation authority | **True** |
| 6 | cả hai ∈ `GEOMETRY_CHECKERS` **và** `CHECKERS` | **True** |
| 7 | analyze schema chứa cả hai | **True** |

Aggregate chỉ-đếm — **mọi giá trị khớp kỳ vọng**:

```
V3_POSITIVE_CASES                              18
V3_CASES_WITH_ALL_OBLIGATION_KINDS_EMITTABLE   18
V3_CASES_WITH_DROPPED_OBLIGATION_KIND           0
V3_CENTER_RADIUS_CASES                          4
V3_CENTER_RADIUS_CONTRACT_UNBLOCKED             4
DEAD_POSITIVE_CELLS                           0/9
MEASURABLE_BY_FAMILY  ball/cylinder/cone    6/6/6
```

```
DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3 = NOT_DETERMINABLE_FROM_METADATA
```

Đây là **giới hạn chưa biết**, không phải blocker đã chứng minh — xem §9 và §10
cho yêu cầu phân loại ở lượt live.

## 4. SEAL_COVERAGE

Đọc từ `seal_curved_v3._niem_phong` và `acceptance_integrity.mo_run`.

| thành phần | seal khoá? | authority |
|---|---|---|
| pool bytes | ✅ `pool_hash` | sealer |
| **kỳ vọng (`mong`)** | ✅ **cùng `pool_hash`** | sealer |
| số ca · cấu trúc ô · dương/âm | ✅ `pool_size`, `o`, `o_duong`, `o_am` | sealer |
| measured-system candidate | ✅ `measured_system_hash` + `_files` | candidate freezer |
| seed | ✅ `null` trước live | đầu vào NGOÀI |
| tập đã rút | ✅ `da_rut` + `case_set_hash` (khi rút) | sealer |
| **runner identity** | ❌ **KHÔNG** | `certify_acceptance_runner` + `RunManifest.runner_hash` |
| **scorer/verdict identity** | ❌ **KHÔNG** | như trên |
| **retry policy** | ❌ **KHÔNG** | `RunManifest.chinh_sach_sua` |
| **quota** | ❌ **KHÔNG** | `RunManifest.ngan_sach_goi` |
| **thresholds** | ❌ **KHÔNG** | chính sách đánh giá, ngoài seal |
| raw candidate retention | ❌ không ở seal | runner (`raw_candidates`, `theo_luot`) |
| attempt denominator | ❌ không ở seal | scorer |

**Thiết kế hai artifact, và phải đọc đúng như thế:** con dấu cố định *đo CÁI GÌ*
(pool + kỳ vọng + hệ được đo); **run manifest** cố định *đo NHƯ THẾ NÀO, vào lúc
nào* (runner hash, model/provider, retry, quota, toàn bộ môi trường sinh, git
HEAD, phân loại dirty). `mo_run` còn **từ chối chạy** trên cây bẩn ở đường trọng
yếu và **từ chối resume** vào thư mục đã tồn tại.

Hệ quả phải khai: **con dấu một mình không chặn được việc đổi runner giữa reseal
và lượt live.** Cái chặn là certification (cổng trước) + `runner_hash` trong
manifest (ghi tại chỗ). Lượt live phải chạy cả hai.

Xác nhận reseal **chỉ** ghi trường do sealer sở hữu: không trường nào sửa tay —
toàn bộ seal do `--niem-phong` sinh.

## 5. FAULT_INJECTION

Sandbox `tempfile`, bản sao byte-identical, seal/pool thật không đụng.

| # | mutation | authority bắt | exit | diagnostic |
|---|---|---|---|---|
| ① | nền (candidate hiện tại + pool chuẩn) | — | 0 | XANH |
| ② | candidate hash CŨ `4d8bfb51…` | sealer | 1 | *"hệ đã đổi sau khi niêm phong — niêm phong lại trước"* |
| ③ | đổi **một byte** pool copy | sealer | 1 | *"pool ĐÃ TRÔI khỏi con dấu — băm lệch"* |
| ④ | sửa `pool_hash` trong seal copy | sealer | 1 | *"pool ĐÃ TRÔI khỏi con dấu"* |
| ⑤ | seal đã có seed (rút lần hai) | sealer | 1 | *"đã rút bằng seed 7 — không rút lần hai"* |
| ⑥ | runner identity | **seal KHÔNG khoá** | — | trường `runner`/`runner_hash` vắng mặt trong seal; khoá bởi certification + manifest |
| ⑦ | đổi nội dung một component candidate (`measure_contract.py`, trong bộ nhớ) | candidate freezer | 1 | candidate `a696200e…` → `efb618c1…` ⇒ *"hệ đã đổi"* |

Khôi phục: `pool_hash` khớp dấu · `seed = None` · `da_rut = None`.

## 6. CANONICAL_RESEAL

```
python scripts/seal_curved_v3.py --niem-phong     exit 0
  pool        26 bài · 13 ô · 36c2153ecefd2dbf…
  hệ được đo  89 file · a696200e8f8c668c…
  ô dương/âm  9 / 4
  seed        CHƯA CÓ — cần người ngoài
```

**Diff con dấu — đúng HAI dòng:**

```diff
- "measured_system_hash": "4d8bfb51692b7b848db6c4e0eacaeee01dc9992c24d45d5b6185e99015665e19",
- "niem_phong_luc":       "2026-09-03T10:41:10+00:00",
+ "measured_system_hash": "a696200e8f8c668c82a1675eab09b4e1845e3c499edaf90c95790f108fe244c2",
+ "niem_phong_luc":       "2026-09-04T15:51:52+00:00",
```

Mọi trường khác byte-identical: `khai` · `pool_hash` · `pool_size` · `o` ·
`o_duong` · `o_am` · `measured_system_files` · `seed` · `da_rut` ·
`ghi_chu_doc_lap`.

`POOL.json` sha256 `ba35870c0808889…` **trước và sau bằng nhau**;
`git diff --stat -- POOL.json` rỗng.

### Xác minh KHÔNG TIÊU THỤ

`seal_curved_v3.py` chỉ có đường xác minh **tiêu thụ** (`_rut` ghi seed), nên
theo §F đã chạy verifier trên **bản sao byte-identical** trong sandbox:

```
verifier trên BẢN SAO:  XANH — seal mới hợp lệ, rút được
BẢN THẬT sau khi verify:
  POOL.json byte đổi?    False
  V3_SEAL.json byte đổi? False
  seed = None   da_rut = None
  pool_hash = 36c2153e…   measured_system_hash = a696200e…  == candidate: True
```

## 7. POST_RESEAL_IDENTITY

```
CANDIDATE_HASH_CHANGED_BY_RESEAL      NO   a696200e8f8c668c… (89 file)
CACHE_VERSION_CHANGED_BY_RESEAL       NO   78
MODEL_FACING_HASH_CHANGED_BY_RESEAL   NO   card·analyze·synthesis·prompt đều nguyên
CAPABILITY_HASH_CHANGED_BY_RESEAL     NO   85bd316781b86576…
POOL_HASH_CHANGED                     NO   36c2153ecefd2dbf…
SEED_ASSIGNED                         NO
CASES_DRAWN                           NO
```

`git status` sau reseal: **đúng một file đổi** —
`docs/evaluation/geometry/curved-v3/V3_SEAL.json`. Candidate verify vẫn PASS.
Đây là bằng chứng thực nghiệm cho `CANDIDATE_SEAL_IDENTITY_CYCLE = NO`.

## 8. TEST_RESULTS

Chạy **mới** tại candidate `a696200e…` (mọi lệnh từ `backend/`):

| gate | lệnh | exit | kết quả |
|---|---|---|---|
| candidate verification | `freeze_evaluation_candidate.py --verify` | 0 | PASS |
| runner certification | `certify_acceptance_runner.py` | 0 | PASS, 0 lượt gọi |
| seal verification (không tiêu thụ) | sandbox byte-identical | 0 | XANH |
| pool integrity | sha256 + `_bam(bai)` vs con dấu | 0 | khớp |
| cache identity | `pytest tests/test_cache_identity.py` | 0 | **15 pass** |
| obligation-surface | `pytest …/test_area_obligation_surface.py` | 0 | **35 pass** |
| acceptance-runner-integrity | `pytest tests/test_acceptance_runner_integrity.py` | 0 | **43 pass** |
| full backend | `pytest -q` | 0 | **3403 pass**, 1 skip, 1 deselect |
| `git diff --check` | — | 0 | sạch |

**Kế thừa** tại **cùng candidate `a696200e…`** (wave trước, không có thay đổi
nào chạm candidate kể từ đó — reseal chỉ chạm `docs/`):

| gate | kết quả kế thừa |
|---|---|
| frontend | 698 pass / 51 file |
| frontend build | PASS |
| demo replay | 5/5 · reduced 1/1 |
| crash surface | 6/6 biên, 0 ném ra ngoài |

Lý do kế thừa hợp lệ: cả bốn phụ thuộc **duy nhất** vào mã sản phẩm, và mã sản
phẩm có băm không đổi (`a696200e…`, 89 file, verify PASS ngay sau reseal).

## 9. MEASUREMENT_LIMITATIONS

- `DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3 = NOT_DETERMINABLE_FROM_METADATA`.
  Chữ ký công thức nói bán kính **là tham số**; nó không nói **đề phát biểu thế
  nào** (bán kính 13? đường kính 26?). Trả lời phải đọc `de` ⇒ phá held-out.
  Lớp *"đường kính 26"* hiện **đóng** (`arith` cho kiểu tĩnh `unknown`), nên nếu
  lượt live gặp nó, thất bại ấy là **`SYSTEM_EXPRESSIVENESS_GAP`**, KHÔNG phải
  `MODEL_SYNTHESIS_FAILURE`. Scorer phải phân biệt được — xem §10.
- Held-out **A** không có ô cho `area`/`lateral_area` (niêm phong trước khi
  chúng tồn tại) — đã khai ở `NGHIA_VU_KHONG_CO_O`.
- Seal **không** khoá runner/scorer/retry/quota/thresholds (§4).
- `18/18 obligation kinds emittable` chứng minh **bề mặt hợp đồng** đầy đủ. Nó
  KHÔNG chứng minh mô hình tổng hợp đúng, KHÔNG chứng minh family acceptance,
  KHÔNG bật product capability.
- Người soạn pool tự khai **không độc lập** với 8 ca hỏng V1+V2
  (`ghi_chu_doc_lap`) — giới hạn có sẵn, giữ nguyên.

## 10. LIVE_V3_HANDOFF

Lượt live **bắt buộc**:

1. **Evaluator độc lập** với tác nhân triển khai (tôi đã viết `radius`,
   `area`/`lateral_area` — tôi không được chấm chính mình).
2. **Seed từ bên ngoài**, do người KHÔNG soạn pool cấp; ghi vào manifest.
3. **Model/provider/version** ghi vào `RunManifest.model`.
4. **Rút đúng MỘT lần** — `_rut` tự chặn lần hai; `run_id` mới cho mỗi lượt.
5. **Giữ mọi raw candidate và mọi attempt** (`raw_candidates`, `theo_luot`).
6. **Mọi attempt vào mẫu số** — không lọc lượt hỏng ra khỏi tỉ lệ.
7. **Tách system error khỏi model error** — `acceptance_verdict.phan_loai`, và
   phải phân loại được `SYSTEM_EXPRESSIVENESS_GAP` cho ca derived-radius (§9).
8. **Capability giữ `foundation_only`** cho tới khi kết quả đạt ngưỡng đã niêm
   phong.
9. Chạy `certify_acceptance_runner` **trước** lượt chạy (seal không khoá runner).

## 11. RECOMMENDED_NEXT_ACTION

```
CURVED_V3_LIVE_ACCEPTANCE
```

---

```
APPLICATION_LLM_CALLS                         0
LIVE_V3_EXECUTED                              NO

OLD_MEASURED_SYSTEM_HASH                      4d8bfb51692b7b84…
NEW_MEASURED_SYSTEM_HASH                      a696200e8f8c668c…
CURRENT_CANDIDATE_HASH                        a696200e8f8c668c…
CANDIDATE_FILE_COUNT                          89
CACHE_VERSION                                 78

GRAMMAR_CARD_HASH                             24e550ad1c57a2aa…
ANALYZE_SCHEMA_HASH                           515001b503af5c7c…
SYNTHESIS_SCHEMA_HASH                         82dbff3f62ee26fb…
PROMPT_HASH                                   55ac1ca6a6df92ce…
CAPABILITY_HASH                               85bd316781b86576…
SEMANTIC_ENVIRONMENT_HASH                     30502a4404cbe6aa…

V3_POOL_HASH_BEFORE                           36c2153ecefd2dbf…
V3_POOL_HASH_AFTER                            36c2153ecefd2dbf…
POOL_BYTES_CHANGED                            NO   (sha256 ba35870c… không đổi)
EXPECTED_RESULTS_CHANGED                      NO   (nằm trong pool_hash)
V3_SEED                                       null
V3_DA_RUT                                     null

V3_PROVENANCE_VERDICT                         CLEAN_HELD_OUT
RUNNER_CERTIFICATION                          PASS
ANALYZE_OBLIGATION_SURFACE_COMPLETE_FOR_V3    YES
V3_POSITIVE_CASES_WITH_EMITTABLE_KINDS        18/18
V3_CENTER_RADIUS_CONTRACT_UNBLOCKED           4/4
DERIVED_RADIUS_EXPRESSIVENESS_COMPLETE_FOR_V3 NOT_DETERMINABLE_FROM_METADATA

RESEAL_PERFORMED                              YES
SEAL_VERIFICATION                             PASS (không tiêu thụ, bản sao)
READY_FOR_V3_EXECUTION                        YES
PRODUCT_CAPABILITY_CHANGED                    NO   ball/cylinder/cone = foundation_only
WORKING_TREE                                  CLEAN
```
