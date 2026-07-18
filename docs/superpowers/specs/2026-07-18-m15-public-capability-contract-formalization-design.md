# M15 — Public Capability Contract Formalization & Migration — DESIGN

Trạng thái: **rev2 — chờ user duyệt**. Docs-only; chưa có implementation plan,
chưa có production code. (rev1 được duyệt có điều kiện; rev2 sửa 6 điểm review.)

Nguồn: Phase 1 Post-M14 Migration Audit A–G (đã duyệt, phiên 2026-07-18, repo
`main` @ `8b14723`) + 14 quyết định user đã khoá khi duyệt audit. Mọi tham chiếu
file/symbol trong doc này đã được đối chiếu source tại commit đó.

### Revision log

- rev1 (2026-07-18): bản đầu theo khung A–S user yêu cầu; đưa vào 14 quyết định
  đã khoá; bổ sung hai hệ quả phái sinh đã báo trước khi viết: (i) namespace hoá
  taxonomy kéo theo đổi giá trị enum sorting đã live-verify → Wave 1 phải có
  control sorting; (ii) tách taxonomy đầy đủ (membership-side) khỏi
  ANALYZE-EXPOSED subset để tránh salience bloat (bài học M8-PRE S3).
- rev2 (2026-07-18): sửa 6 điểm review rev1 — (1) **cross-family mismatch
  KHÔNG còn permissive**: prescribed namespace ∉ memberships của target →
  `ROUTE_MECHANISM_FAMILY_MISMATCH`, không simulate, một lượt bounded
  reclassification rồi fail-closed (§E2 viết lại + 4 offline test tối thiểu);
  tách bạch hai mã lỗi mismatch↔ownership; (2) **KHÔNG đổi giá trị sorting
  đã live-verify**: taxonomy canonical namespaced nội bộ + alias normalization
  một chiều tại compatibility boundary — analyze/prompt giữ legacy values
  sorting trong M15 (§D1/§D2), gỡ rủi ro rename + control live rename khỏi
  §M/§Q; (3) sửa fact "13 entry còn lại" → **12 concrete entry non-sorting**
  (§A); (4) khoá live-acceptance nhất quán: offline hex VÀ octal đều gap, live
  tối thiểu MỘT case non-binary-base (ưu tiên hex), octal live optional
  (§M/§R); (5) `config_contract_version` bao gồm **validation policy** chứ
  không chỉ JSON shape + per-entry locks trong cùng `algo-cfg-1` (§C2/§K);
  (6) claim boundary tường minh: mọi family có owned_mechanisms máy-đọc,
  nhưng runtime gate CHỈ enforce khi prescribed non-null thuộc analyze-exposed
  taxonomy — không claim phân biệt cơ chế cho mọi request mọi family (§D2/§R).

---

## A. Problem statement (sau audit)

Sau M14, hệ có **một** capability family (comparison_sort) với contract lifecycle
đầy đủ: bounded FamilySpec có version, mechanism ownership tường minh
(`owned_mechanisms` trên `FamilySelector`), mechanism-consistency gate, adapter
tất định, cross-lock chống drift, metric tách bạch, và live acceptance. **12
concrete entry non-sorting** còn lại của CATALOG **chạy đúng** (executor tất
định sở hữu kết quả — R0 nguyên vẹn) nhưng **contract của chúng không đồng nhất
về mặt hình thức**:

- **FACT (audit A):** 6 entry `algorithm.*` (5 scan + binary_search) dùng chung
  `_ALGO_CONFIG_SCHEMA` legacy không version ([catalog.py:71](../../backend/app/simulation/catalog.py));
  logic/binary/network/encap có config bounded nhưng không version, không
  ownership khai máy-đọc-được; chỉ encap khai `known_gaps` (:470).
- **FACT (audit C):** tín hiệu cơ chế `prescribed_procedure` là enum
  CHỈ-SORTING, import thẳng từ `families.sorting` vào `ANALYZE_SCHEMA`
  ([pipeline.py:96-100](../../backend/app/ai/pipeline.py)) — không family khác
  nào có prescription signal.
- **FACT (audit B):** `FamilyMembership` có `mechanism_id` (số ít, chỉ dùng cho
  variant routing của selector) nhưng **không có** khái niệm "tập cơ chế mà
  membership này SỞ HỮU" — ownership hiện chỉ tồn tại ở `FamilySelector`, tức
  chỉ tồn tại cho đúng một family.
- **FACT (M14 design §K/§N):** M14 tự khai để lại cho M15: validator-contract
  parity cho mọi family (§K:642), tổng quát hoá taxonomy cơ chế (§N5),
  error-code granularity validator legacy (§N3).

Hệ quả: tuyên bố "capability được kiểm soát bằng contract" hiện chỉ đúng đầy đủ
cho sorting; các family khác dựa vào tổ hợp {prompt rule + validator + gate M13}
đúng về hành vi nhưng **không được khoá thành contract máy-kiểm-được**. M15 đóng
lỗ hổng hình thức hoá đó — **thống nhất bề mặt CONTRACT, không thống nhất
execution** — mà không viết lại bất kỳ executor/renderer nào.

Audit đã phủ quyết giả thuyết "đa số family cần migrate": **không family nào
cần MIGRATE_SPEC_SURFACE**; phần lớn là FORMALIZE_ONLY trên config đã bounded
sẵn.

## B. Conformance model

Một capability/family là **conformant** khi có đủ 8 thuộc tính (định nghĩa đã
khoá khi duyệt audit):

1. bounded machine-readable input contract;
2. explicit family membership;
3. owned mechanisms (máy đọc được, cross-lock);
4. contract version;
5. deterministic executor authority (executor sở hữu state/timeline/result);
6. validator/contract locks (test khoá chống drift);
7. honest near-miss boundaries (đường từ chối/chuẩn hoá tường minh);
8. preserved interaction/renderer behavior.

Năm trạng thái phân loại và phán quyết cuối (kế thừa audit B, user đã duyệt):

| Family | Thành viên | Trạng thái M15 | Việc còn thiếu để conformant |
|---|---|---|---|
| F3 comparison_sort | bubble, insertion | **ALREADY_CONFORMANT** | 0 (reference; chỉ đổi PHIÊN BẢN GIÁ TRỊ mechanism id theo §D — không thiết kế lại) |
| F1 single_pass_scan | 5 specialized + `algorithm.scan` | **FORMALIZE_ONLY** | ownership + config_contract_version + locks; **không selector** (§G) |
| F2 interval_elimination | binary_search | **FORMALIZE_ONLY** | ownership + version + lock chính-sách-chuẩn-hoá (§F) |
| F4 boolean_composition | logic.and_gate + generic (comp) | **KEEP_DUAL_SURFACE** | formalize quan hệ hai bề mặt + boundary locks (§H) |
| F5 positional_representation | binary.decimal_to_binary | **FORMALIZE_ONLY** | ownership + version + near-miss control cơ-số-≠-2 (§F) |
| F6 graph_traversal | network.packet_routing | **FORMALIZE_ONLY** | ownership + version + `known_gaps` chuẩn hoá (§I) |
| F7 layered_pdu_transform | network.protocol_encapsulation | **FORMALIZE_ONLY** | ownership + version (known_gaps đã có — hình mẫu) (§I) |
| F8 structural_progressive_representation | generic (repr) | **ALREADY_CONFORMANT** | consistency proof + docs (§J) |

**MIGRATE_SPEC_SURFACE: không có trong M15.** **DEFER_CAPABILITY_GAP** (ghi
trung thực, không triển khai): `database_table_query`, `os_process_fsm`,
`dijkstra_weighted_shortest_path` ([coverage.py:74-83](../../backend/app/simulation/coverage.py))
— không tự động thành migration target.

## C. FamilyMembership ownership / version model

Hai mở rộng descriptor, **không nguồn sự thật mới**, không đổi envelope:

**C1. `owned_mechanisms` ở mức membership** (quyết định 3, 4):

```python
@dataclass(frozen=True)
class FamilyMembership:
    family_id: FamilyId
    result_authority: ResultAuthority
    variant_id: str | None = None
    family_spec_version: str | None = None
    mechanism_id: str | None = None          # giữ nguyên: cơ chế của VARIANT (selector routing)
    owned_mechanisms: tuple[str, ...] = ()   # MỚI: tập cơ chế membership này SỞ HỮU
```

- Ngữ nghĩa: "executor của target này biểu diễn TRUNG THỰC các cơ chế nào trong
  family này". Membership-level (không phải SimSpec-level) vì một target đa
  membership sở hữu cơ chế KHÁC NHAU theo từng family (generic: boolean DAG ≠
  reveal/move).
- Lock: `mechanism_id ∈ owned_mechanisms` khi cả hai cùng đặt; với family có
  selector: `selector.owned_mechanisms == ⋃ owned_mechanisms` của các membership
  variant (cross-lock mở rộng từ `cross_lock_violations`
  [families/__init__.py:46](../../backend/app/simulation/families/__init__.py)).
- **Không tạo one-variant selector** để tái dùng gate (quyết định 4) — gate tổng
  quát đọc ownership từ membership (§E).

**C2. `config_contract_version` ở mức descriptor** (quyết định 6):

- Kwarg mới trên `SimSpec` (theo khuôn M14 §N1 — diff nhỏ nhất), khai cho đủ 14
  entry; **KHÔNG đưa vào runtime envelope**, không Alembic, không đụng history.
- Version đặt theo **bề mặt config**, không theo entry: 8 entry algorithm legacy
  chung một `algo-cfg-1` (chung `_ALGO_CONFIG_SCHEMA`); `algorithm.scan` alias
  version engine sẵn có (`scan-1.0` ← `SCAN_VERSION`
  [scan_engine.py:15](../../backend/app/simulation/scan_engine.py));
  `logic-cfg-1`; `binary-cfg-1`; `net-cfg-1`; `encap-cfg-1`; generic alias
  `dsl-1.0` ← `SUPPORTED_VERSIONS` ([manifest.py:11](../../backend/app/simulation/dsl/manifest.py)).
  Quan hệ với `family_spec_version` (đã có trên membership): family_spec_version
  = version bề mặt FAMILY (chỉ family có selector); config_contract_version =
  version bề mặt CONFIG của chính entry. Hai trục độc lập, cùng xuất ra
  `capability-descriptors.json` (sync-lock + FE cross-lock test-only mở rộng
  tương ứng — production FE vẫn KHÔNG import, giữ điểm 6 M14).
- **Ngữ nghĩa version (rev2 điểm 5):** `config_contract_version` đặt tên cho
  **toàn bộ contract của bề mặt config = JSON shape + VALIDATION POLICY** —
  required fields theo entry, bounds, hành vi chuẩn hoá tất định (vd
  binary_search tự sắp + chú thích), annotation policy, semantic precondition.
  Đổi bất kỳ thành phần policy nào trong số đó = đổi contract = phải bump
  version, dù JSON shape không đổi.
- **Per-entry locks dưới version dùng chung:** các entry cùng `algo-cfg-1`
  (chung `_ALGO_CONFIG_SCHEMA`) vẫn PHẢI có lock RIÊNG TỪNG ENTRY cho phần
  policy khác nhau theo `algorithm_id`: required fields (`target` bắt buộc với
  linear/binary_search; `condition` với sum_if/count_if; `order` với 2 sort —
  [simulation.py:92-115](../../backend/app/validation/simulation.py)), bounds
  2–15 phần tử, chuẩn hoá + annotation (binary_search :121-129), semantic
  precondition. Version dùng chung nói "cùng một bề mặt"; lock per-entry nói
  "policy từng biến thể trong bề mặt đó không được trôi".

## D. Namespaced mechanism taxonomy (quyết định 5)

**D1. Nguồn duy nhất:** module mới `backend/app/simulation/mechanisms.py`:

```python
FAMILY_MECHANISMS: dict[FamilyId, tuple[str, ...]]   # enum ĐÓNG, id dạng "<family_id>.<mechanism>"
```

- Không free-text; không keyword-patch; không chứa result/trace/timeline (kế
  thừa nguyên tắc §O7 M14 — mô tả THAO TÁC).
- **Canonical nội bộ + alias compatibility (rev2 điểm 2 — KHÔNG đổi giá trị
  external đã live-verify):** taxonomy canonical dùng id namespaced
  (`comparison_sort.adjacent_compare_swap`…). **Memberships, selector
  ownership và mọi gate CHỈ so sánh canonical id.** Nhưng bề mặt
  analyze (ANALYZE_SCHEMA enum + analyze.md) **GIỮ NGUYÊN legacy values
  sorting** (`adjacent_compare_swap`, `shift_into_sorted_prefix`,
  `select_extreme_repeated`, `partition_recursive`, `other_unspecified`,
  `none`) trong M15. Cầu nối là **một hàm chuẩn hoá một chiều tại
  compatibility boundary**:

  ```python
  canonical_mechanism(raw: str | None) -> str | None
  # "adjacent_compare_swap" → "comparison_sort.adjacent_compare_swap"
  # giá trị đã namespaced → trả nguyên; None/"none" → None
  ```

  Alias map là **compatibility boundary, KHÔNG phải nguồn sự thật thứ hai**:
  nó chỉ ánh xạ legacy→canonical, không định nghĩa cơ chế mới; lock: mọi giá
  trị đích của alias ∈ taxonomy canonical, và không alias nào trỏ ra ngoài
  namespace `comparison_sort`. Gate (cả selector branch lẫn direct branch)
  normalize prescribed TRƯỚC khi so; `analysis` trong envelope giữ nguyên văn
  (không mutate — không đổi output nhìn thấy được). Gỡ alias CHỈ xem xét sau
  M16, dựa trên evidence, không nằm trong M15.
- Mechanism MỚI (M15: `positional_representation.*`) dùng thẳng giá trị
  namespaced ở cả taxonomy lẫn analyze-exposed — không tạo alias mới.
- Granularity: đủ THÔ để trung thực về ranh giới, không mịn hơn nhu cầu gate.
  Ví dụ dự kiến (chốt chính tả khi implement — §S1): scan KHÔNG tách max/min
  (`single_pass_scan.track_extreme`), sorting giữ 4 lớp M14 + other,
  positional_representation = {`binary_positional_weights`,
  `non_binary_base`} (giá trị sau **không target nào sở hữu** — chính là
  gap-trigger của control hex/octal, §F).

**D2. Tách hai tầng — taxonomy đầy đủ ≠ enum analyze:**

- **Membership-side (đầy đủ):** mọi membership khai `owned_mechanisms` từ
  taxonomy; cross-lock: mọi id ∈ `FAMILY_MECHANISMS[family_id]`, namespace khớp
  family.
- **ANALYZE-EXPOSED subset:** `prescribed_procedure` trong `ANALYZE_SCHEMA` chỉ
  liệt kê giá trị có nhu cầu prescription-detection THẬT trong M15: **legacy
  values sorting giữ nguyên** (M14, qua alias §D1) + **giá trị namespaced
  `positional_representation.*`** (consumer Wave 1). Lý do tách: enum analyze
  là bề mặt prompt — bơm 20 giá trị cho mọi family là đúng kiểu
  salience-failure M8-PRE S3 đã đo; scan/boolean/network không cần prescription
  signal vì near-miss của chúng đã có control khác (classify 4b/2c/3d +
  computation gate — audit E). Mở rộng subset về sau = quyết định có ý thức
  từng namespace, kèm bump cache + smoke.
- **Claim boundary (rev2 điểm 6):** M15 claim được: *mọi family có
  `owned_mechanisms` máy-đọc-được*, và *runtime mechanism gate enforce KHI VÀ
  CHỈ KHI analyze phát prescribed mechanism non-null thuộc analyze-exposed
  taxonomy*. M15 KHÔNG claim: analyze/gate hiện phân biệt cơ chế cho MỌI
  request của MỌI family — các family ngoài analyze-exposed subset có ownership
  khai để descriptor/coverage trung thực và sẵn sàng cho gate, nhưng không có
  prescription signal runtime trong M15.
- Sentinel giữ nguyên: `null` = đề không chỉ định cơ chế (quyết định 5);
  `"none"` giữ làm giá trị tường minh tương đương null (tương thích M14
  [mechanism_gate.py:24](../../backend/app/simulation/mechanism_gate.py)).
- Cross-lock ba chiều: analyze-exposed ⊆ taxonomy; mỗi giá trị exposed hoặc
  được ≥1 membership sở hữu, hoặc là giá trị cố-ý-không-ai-sở-hữu (gap-trigger,
  phải có test khoá từng giá trị như vậy); taxonomy ↔ selector.owned (C1).

## E. Direct concrete choice vs FamilySelector lifecycle

Hai lifecycle **đều conformant** — chọn theo nhu cầu variant-resolution, không
theo thẩm mỹ đồng nhất:

**E1. Selector lifecycle (M14, giữ nguyên):** token → mechanism gate tầng 1 →
FamilySpec → validate fail-closed → variant-consistency tầng 2 → resolve tất
định → validator concrete → envelope concrete id. Điều kiện dùng: ≥2 concrete
target mà LLM phải chọn theo CƠ CHẾ, và/hoặc sibling không-executor cần gate
variant. M15: chỉ comparison_sort. **Không selector mới** (quyết định 1, 4).

**E2. Direct lifecycle (tổng quát hoá trong M15 — rev2 điểm 1, fail-closed):**
concrete id trong menu → **mechanism-consistency check tổng quát** (mới) →
stage_simulate với config contract của entry → validator → envelope. Check chạy
trên prescribed đã normalize qua `canonical_mechanism` (§D1):

```
check_mechanism_consistency_for_target(analysis, spec)
  -> (ErrorCode, msg) | None
```

Ba nhánh, phân biệt HAI mã lỗi có ngữ nghĩa khác nhau:

1. `prescribed ∈ {null, "none"}` → None (permissive — giữ triết lý E4 M14:
   vắng tín hiệu không phải bằng chứng cơ chế ngoài phạm vi).
2. namespace của prescribed **khớp** một membership của target nhưng
   `prescribed ∉ owned_mechanisms` của membership đó →
   **`GATE_MECHANISM_OWNERSHIP`** = *cùng family, capability được chọn không
   sở hữu cơ chế* → `capability_gap` (tái dùng ErrorCode sẵn có
   [error_codes.py:25](../../backend/app/simulation/error_codes.py)).
3. namespace của prescribed **∉** {m.family_id của spec.family_memberships} →
   **`ROUTE_MECHANISM_FAMILY_MISMATCH`** (mã MỚI trong `error_codes.py`) =
   *analyze mechanism family và classify target family mâu thuẫn nhau*.
   **KHÔNG được tiếp tục `stage_simulate` với target mâu thuẫn** — hai tín hiệu
   cấu trúc đối nghịch mà vẫn simulate là bỏ qua bằng chứng mâu thuẫn.

**Xử lý mismatch (nhánh 3) — bounded reclassification rồi fail-closed:**

- Production orchestration CÓ seam phù hợp: chính call-site `stage_classify`
  trong `run_pipeline` ([pipeline.py:410](../../backend/app/ai/pipeline.py)) —
  cùng khuôn retry-có-lý-do mà `stage_simulate` đã dùng. Thiết kế: **đúng MỘT
  lượt reclassify bounded** — gọi lại `stage_classify` với message bổ sung nêu
  mâu thuẫn cấu trúc ("phân tích xác định cơ chế thuộc family X;
  simulation_id đã chọn không biểu diễn family đó — chọn lại trong danh mục
  hoặc trả unsupported"), temperature 0, không đổi schema.
- Kết quả reclassify: (a) route mới có membership phủ namespace prescribed →
  đi tiếp lifecycle tương ứng (selector hoặc direct — check E2/tier-1 chạy lại
  trên route mới); (b) unsupported → envelope unsupported trung thực như thường
  lệ; (c) VẪN mâu thuẫn → **fail-closed `capability_gap`** với
  `error_code = ROUTE_MECHANISM_FAMILY_MISMATCH`, không simulate.
- Chi phí: +1 call LLM CHỈ trên đường mâu thuẫn (hiếm — cần analyze phát
  prescribed non-null VÀ classify chọn lệch family); đường thường 0 call thêm.
- Observer: emit `gate_checked` `gate="mechanism"` (nhánh 2) /
  `gate="route_mechanism"` (nhánh 3) + event reclassify — eval kế thừa qua
  observer, **không sửa harness-lifecycle** (bất biến #22 nguyên vẹn).
- Ví dụ recovery có giá trị thật: đề sắp-xếp bị classify lệch về generic →
  prescribed (sorting, đã normalize) ∉ {boolean_composition,
  structural_progressive_representation} → mismatch → reclassify với lý do →
  kỳ vọng về token `comparison_sort` → lifecycle selector đúng.
- Defense-in-depth GIỮ NGUYÊN, không thay thế: computation gate M13
  (`result_ownership` fail-closed, bất biến #21) vẫn chặn lớp "generic minh
  hoạ đáp án" độc lập với check này.

**Offline tests tối thiểu (rev2 điểm 1 — không keyword-patch, tất cả mock):**

| # | Kịch bản | Kỳ vọng |
|---|---|---|
| T1 | prescribed `positional_representation.non_binary_base` + target `binary.decimal_to_binary` | nhánh 2 → `GATE_MECHANISM_OWNERSHIP`, capability_gap |
| T2 | prescribed `positional_representation.*` + target `algorithm.binary_search` (family không liên quan) | nhánh 3 → `ROUTE_MECHANISM_FAMILY_MISMATCH`, **stage_simulate KHÔNG được gọi** (assert qua mock), reclassify 1 lượt rồi fail-closed nếu vẫn lệch |
| T3 | prescribed sorting (legacy value, qua alias) + target `binary.decimal_to_binary` | nhánh 3 → family mismatch, không simulate |
| T4 | prescribed = null + lần lượt MỌI direct family | None — không chặn oan (FP-budget) |

## F. Wave 1 vertical slice (quyết định 10, 11)

Hạ tầng chung **chỉ được viết kèm consumer chứng minh ngay**:

**Hạ tầng:** `mechanisms.py` (taxonomy canonical + `canonical_mechanism` alias
boundary — D1) + mở rộng `FamilyMembership`/`SimSpec` (C) + check tổng quát hai
mã lỗi + seam reclassify bounded (E2) + `ROUTE_MECHANISM_FAMILY_MISMATCH` vào
`error_codes.py` + cross-locks (D2/C1) + mở rộng artifact
`capability-descriptors.json` + sync-lock/FE cross-lock + `ANALYZE_SCHEMA` enum
mới (= legacy sorting values GIỮ NGUYÊN + `none` + giá trị namespaced
`positional_representation.*`) + vá `analyze.md` (CHỈ THÊM khối dạy
`positional_representation.*` theo khuôn thao tác §O7 — khối sorting hiện có
giữ nguyên văn) + **bump `CACHE_VERSION` 11→12, MỘT lần cho toàn M15** (§L).

**Consumer 1 — `binary.decimal_to_binary`:**
- membership `positional_representation` + `owned_mechanisms =
  ("positional_representation.binary_positional_weights",)`;
  `config_contract_version = "binary-cfg-1"`.
- **Control hex/octal → capability_gap (quyết định 9, rev2 điểm 4):** analyze
  dạy đặt `positional_representation.non_binary_base` khi đề đổi sang cơ số ≠ 2;
  giá trị này không membership nào sở hữu → gate E2 nhánh 2 nổ. KHÔNG
  keyword-patch trong code — server chỉ so tín hiệu cấu trúc, đúng khuôn
  sorting. Nếu classify tự unsupported trước khi tới gate: chấp nhận, gate là
  backstop (đúng pattern known-issue 1b của M14). **Offline: CẢ hex VÀ octal
  đều phải có case khoá → capability_gap** (2 eval case mới trong pool
  `capability`, đúng luật kết nạp; frozen DATASET không đụng). Live: xem §M.
- Lock contract: bounds 0–255/1–8 bit ↔ contract text ↔ validator
  ([simulation.py:183](../../backend/app/validation/simulation.py)) khoá bằng
  test.

**Consumer 2 — `algorithm.binary_search`:**
- membership `interval_elimination` + `owned_mechanisms =
  ("interval_elimination.halve_sorted_interval",)`; `config_contract_version =
  "algo-cfg-1"`.
- **Lock chính-sách-chuẩn-hoá (quyết định 9):** input chưa sắp → **chuẩn hoá
  tất định + chú thích sư phạm, KHÔNG refuse** — hành vi ĐÃ có
  ([simulation.py:121-129](../../backend/app/validation/simulation.py)), M15 chỉ
  KHOÁ nó thành test đặt tên tường minh + một dòng trong `docs/CORRECTNESS.md`
  (chống "sửa nhầm" thành refuse về sau). Không đổi code validator.

**Control 3 — sorting compatibility (rev2 điểm 2, thay control rename):**
KHÔNG còn rename external → `m14_sorting` offline expectations GIỮ NGUYÊN và
phải xanh nguyên trạng qua alias boundary (chính suite này là proof của
`canonical_mechanism`); thêm test T3 (§E2 — sorting prescribed + binary target
→ mismatch) và test alias-lock (mọi alias đích ∈ taxonomy, không alias ngoài
namespace `comparison_sort`). Live sorting control hạ xuống OPTIONAL (§M) — chỉ
còn phòng salience do analyze.md dài thêm khối positional, không còn rủi ro đổi
giá trị.

## G. Scan formalization — không selector (quyết định 1, 2)

- `algorithm.scan` GIỮ ScanSpec hiện có — nó **đã là** bounded versioned spec
  (enum đóng dẫn xuất engine, `scan_version`, validator hai phía, interpreter sở
  hữu vòng lặp/dừng). M15 chỉ: alias `config_contract_version="scan-1.0"`,
  membership `owned_mechanisms` (toàn bộ không gian single-pass cấu hình được),
  và **consistency-proof test** đối chiếu ScanSpec với checklist conformance §B
  (chứng minh ALREADY-bounded, không viết spec mới).
- 5 specialized scan giữ **direct concrete LLM surface** + executor/interaction
  nguyên trạng; mỗi entry khai owned_mechanisms một cơ chế thô
  (track_extreme ×2, accumulate_conditional, count_conditional,
  find_equal_early_stop — chính tả chốt ở §S1); `config_contract_version =
  "algo-cfg-1"`.
- **Không dạy analyze phát cơ chế scan** (D2): near-miss scan đã có control
  tất định/prompt (multi-pass & vòng biến tự do → unsupported, classify 4b +
  m11 loop-gap; ưu tiên specialized — classify 2c; live-proven M12 4/4, M13
  tier-2b 4/4). Ownership membership-side tồn tại để descriptor/coverage trung
  thực và để gate DÙNG ĐƯỢC về sau nếu một ngày cần expose namespace này —
  quyết định lúc đó, kèm bump + smoke.
- Trạng thái hoãn predict/what-if của scan GIỮ NGUYÊN (non-goal — quyết định
  14), ghi rõ trong lock để không bị đọc nhầm thành thiếu sót mới.

## H. Boolean dual surfaces (KEEP_DUAL_SURFACE)

- Hai bề mặt phục vụ sư phạm khác nhau, **không hợp nhất** (tái khẳng định
  quyết định 10 của M14 design §K): `logic.and_gate` = MỘT cổng AND hai đầu vào
  thuận, exploratory, bảng chân trị; `generic.rule_scene` (membership
  boolean_composition/computation) = DAG rule hợp thành (NOT/≥3/ghép/lồng qua
  trung gian).
- M15 formalize quan hệ: owned_mechanisms hai phía (vd
  `boolean_composition.single_gate_truth_table` cho and_gate;
  `boolean_composition.composed_rule_dag` cho generic — generic-side có thể dẫn
  xuất một phần từ manifest `rule_types()`/`bool_ops()` để không viết tay);
  `config_contract_version` (`logic-cfg-1`, `dsl-1.0`); **boundary lock
  offline**: expectations m11 (NOT ✅ generic, `a-and` ✅ specialized — đối
  chứng chống over-correction) được trỏ thành lock chính thức của family này.
- Ranh giới vẫn dạy ở classify.md rule 2 (prompt) — M15 KHÔNG chuyển boundary
  logic vào code (không keyword-patch), chỉ khoá bằng eval expectations +
  descriptor facts.
- Known-issue 7b (nested truth-table không có cổng production) GIỮ NGUYÊN trạng
  thái đã ghi — nằm ngoài M15 (quyết định 14).

## I. Network ownership / gaps

- `network.packet_routing`: membership `graph_traversal`, owned =
  {`graph_traversal.unweighted_hop_bfs`}; `config_contract_version="net-cfg-1"`;
  **bổ sung `known_gaps`** theo khuôn encap (hiện entry này chưa khai —
  audit A): ("đường đi ngắn nhất có trọng số (Dijkstra)", "topo dựng từng
  bước"). Ranh giới weighted đã có 3 lớp (classify 4c + computation gate +
  coverage CAPABILITY_GAP + case `cap-dijkstra-gap`) — M15 chỉ khai máy-đọc,
  không thêm control mới.
- `network.protocol_encapsulation`: membership `layered_pdu_transform`, owned =
  {`layered_pdu_transform.encapsulate_decapsulate_4layer`};
  `config_contract_version="encap-cfg-1"`; `known_gaps` giữ nguyên
  ([catalog.py:470](../../backend/app/simulation/catalog.py)) — entry này là
  hình mẫu sẵn có của mô hình khai gap.
- Interaction/renderer bất di bất dịch: timeline+predict cả hai; 3D
  `architectural_poc` (routing) / `pedagogical` (encap) — bất biến #16/#18
  không đụng.

## J. Structural representation authority

- Membership `structural_progressive_representation` của generic:
  `result_authority = REPRESENTATION` — engine dựng frame reveal/move, **không
  phải** domain computation. owned_mechanisms DẪN XUẤT từ manifest process
  types (`reveal_sequence`, `move_along_path` —
  [manifest.py](../../backend/app/simulation/dsl/manifest.py) `process_types()`)
  → không hằng viết tay, đúng anti-pattern #1.
- Consistency proof (Wave 5): test khẳng định (i) hai membership của generic
  mang authority KHÁC nhau đúng như khai; (ii) đường "representation trả lời bài
  computation" bị chặn bởi `result_ownership` fail-closed (bất biến #21 — test
  đã có, trỏ thành lock của family này); (iii) known-issue 2 (`move_along_path`
  không ép path theo edge) ghi là thiết kế có chủ đích trong descriptor note,
  không phải gap mới.

## K. Validation / error / contract-lock strategy

Khuôn lock dùng chung mọi wave (viết một lần ở Wave 1, tái dùng):

1. **Descriptor completeness lock:** đủ 14 entry có memberships ≠ ∅,
   owned_mechanisms ≠ ∅ trên từng membership, config_contract_version ≠ "",
   curriculum_anchor ≠ "" (mở rộng lock Task 2 M14).
2. **Taxonomy cross-lock (D2):** namespace khớp family; analyze-exposed ⊆
   taxonomy; gap-trigger values có test riêng từng giá trị; selector.owned ==
   ⋃ variant owned.
3. **Contract-text ↔ validator lock:** bounds/enum trong contract text phải dẫn
   xuất hoặc assert khớp validator (khuôn `test_dsl_contract_json_khong_troi...`
   sẵn có; áp cho binary/logic/net/encap ở mức assert hằng số).
4. **Artifact sync-lock:** `capability-descriptors.json` thêm trường mới
   (owned_mechanisms, config_contract_version) — BE sync-lock + FE cross-lock
   test-only cập nhật; production FE vẫn không import.
5. **Error contract (rev2 điểm 1):** hai mã tách bạch ngữ nghĩa —
   `GATE_MECHANISM_OWNERSHIP` (cùng family, capability không sở hữu cơ chế) và
   `ROUTE_MECHANISM_FAMILY_MISMATCH` (MỚI — analyze mechanism family ↔ classify
   target family mâu thuẫn); envelope unsupported mang `error_code` ở cả hai
   (đối xứng nhánh selector). Legacy validator vẫn map `STRUCTURAL_INVALID` ở
   `stage_simulate` (đã đủ cho categorization hiện tại); granularity mịn hơn
   (§N3 M14) CHỈ thêm nếu eval Wave 1 chứng minh cần — mặc định không (§S8).
6. **Per-entry policy locks dưới version chung** (rev2 điểm 5 — chi tiết §C2):
   một test/lock cho từng `algorithm_id` trong `algo-cfg-1` khoá required
   fields/bounds/normalization/annotation/precondition riêng của nó.

## L. Cache / history / backward compatibility

- **MỘT bump `CACHE_VERSION` 11→12** tại Wave 1 (ANALYZE_SCHEMA enum đổi +
  analyze.md đổi). Wave 2–5 **không bump** trừ khi chạm bề mặt LLM — theo thiết
  kế này thì không (mọi việc còn lại là descriptor/lock/test).
- **Envelope không đổi shape ở mọi wave** → history cũ mở lại nguyên vẹn
  (zero-AI, bất biến #17); `config_contract_version` KHÔNG vào envelope
  (quyết định 6); không Alembic (không bảng mới, không cột mới).
- Pattern store: không đụng (`run_gates` giữ nguyên; validator generic không
  đổi trong M15).
- Rollback tương thích: trước merge = revert wave; sau khi một deploy đã phục
  vụ v12 → forward-fix + bump tiếp (không quay lui số version đã phát hành).

## M. Evaluation / live policy

- **Offline-first:** mọi wave xanh pytest/vitest/build trước khi nói tới live.
  Eval case mới (hex/octal near-miss; các control Wave 1) vào pool
  `capability`/`curriculum` theo luật kết nạp `check_admission` — **frozen
  DATASET 30 case không đụng** (audit xác nhận nó không có case sorting positive
  — không "sửa cho đẹp metric").
- **Suite live `m15_wave1`** (một suite mới, đăng ký `SUITES`
  [live.py:31](../../backend/app/evaluation/live.py)) — chạy SAU khi Wave 1
  xanh offline, user duyệt ngân sách riêng. **Nhất quán offline↔live (rev2
  điểm 4): offline khoá CẢ hex VÀ octal → capability_gap; live BẮT BUỘC tối
  thiểu MỘT case non-binary-base, ƯU TIÊN hex; octal live là OPTIONAL theo
  ngân sách.** Acceptance viết TRƯỚC:
  - **Bắt buộc:**
    1. hex → unsupported (classify-refuse hoặc gate-fired đều đạt — gate là
       backstop), 0 generic config;
    2. binary positive ("đổi 13 sang nhị phân") → `binary.decimal_to_binary`,
       valid spec, KHÔNG bị gate chặn oan;
    3. binary_search dãy chưa sắp → ok + note chuẩn hoá trong config.
  - **Optional theo ngân sách:**
    4. octal → như case 1;
    5. sorting positive (paraphrase cơ chế) → concrete đúng qua token —
       control salience khi analyze.md dài thêm (không còn rủi ro rename,
       §F Control 3);
    6. selection near-miss → từ chối trung thực.
  Đề xuất trần: **≤6 case logic / ≤20 HTTP** (con số cuối do user duyệt lúc
  chạy). Ghi nhật ký đúng khuôn CURRENT_STATE §1: logical cases, HTTP thực,
  retry, transient. Không prompt-fix trước khi có exact trace; tối đa MỘT
  prompt-only fix cho một root cause đã chứng minh; **không sửa validator/gate
  đúng để LLM pass**.
- Wave 2–4: không live (không đổi bề mặt LLM). **Wave 5: không live mặc định**
  — chỉ khi một wave giữa chừng buộc phải chạm analyze/classify (khi đó gộp một
  smoke cuối, acceptance viết trước). Metric mới không cần: harness đã đo
  `mechanism_gate_fired`/family/variant/final-route từ observer (bất biến #22).
- KHÔNG comprehensive catalog evaluation — đó là M16 (quyết định 14).

## N. Coverage updates

- `sorting`: **PILOT → SUPPORTED** kèm note claim-boundary nguyên văn: live
  n=4 là targeted acceptance, KHÔNG phải bằng chứng thống kê (quyết định 8).
- `binary_system`: giữ SUPPORTED, note bổ sung "cơ số ≠ 2 → capability_gap có
  control (M15 Wave 1)".
- Không thêm/xoá knowledge unit; các hàng CAPABILITY_GAP/OUT_OF_SCOPE giữ
  nguyên (quyết định 13 — không capability mới lấp coverage).
- `coverage_rows()` sinh docs — cập nhật qua source, lock
  `test_coverage_matrix.py` giữ enum đóng.

## O. Migration waves & rollback

| Wave | Phạm vi | File/symbol dự kiến | Prereq | Oracle offline | Live | Rollback boundary |
|---|---|---|---|---|---|---|
| **W1** | Hạ tầng (mechanisms.py + alias boundary, membership/SimSpec mở rộng, check E2 hai mã + seam reclassify bounded, `ROUTE_MECHANISM_FAMILY_MISMATCH`, locks K, artifact, ANALYZE_SCHEMA [legacy sorting giữ nguyên + positional namespaced], analyze.md [chỉ thêm khối positional], CACHE 12) + binary + binary_search + T1–T4 + alias-lock | `simulation/mechanisms.py` (mới), `descriptor.py`, `catalog.py`, `families/sorting.py` (hằng canonical nội bộ), `mechanism_gate.py`, `error_codes.py`, `ai/pipeline.py`, `skills/analyze.md`, `main.py`, tests + 2 eval case hex/octal | quyết định S1 chốt chính tả id | engine binary/binary_search sẵn có; FP-budget T4; **m14_sorting offline xanh NGUYÊN TRẠNG qua alias** | **suite `m15_wave1`** (§M) | revert trọn W1; nếu chỉ hỏng control hex → gỡ giá trị `non_binary_base` khỏi analyze-exposed + giữ phần còn lại (gap-trigger là phần tách được) |
| **W2** | Scan: ownership 6 entry, `scan-1.0` alias, consistency proof, tag lại m12 locks | `catalog.py`, `mechanisms.py`, tests | W1 | m12 parity + scan_engine | 0 | revert W2 (descriptor/test-only) |
| **W3** | Boolean dual-surface: ownership 2 phía, boundary locks m11 | `catalog.py`, `mechanisms.py`, tests | W1 | m11 expectations offline | 0 | revert W3 |
| **W4** | Network: ownership + known_gaps routing, version 2 entry | `catalog.py`, `mechanisms.py`, tests | W1 | encap/network tests + m10 offline | 0 | revert W4 |
| **W5** | Generic repr consistency proof + coverage (N) + docs close (CURRENT_STATE §1/§2/§5, ARCHITECTURE_MAP nếu thêm bất biến — §S6, COVERAGE, CODE_INDEX) | `coverage.py`, docs, tests | W1–W4 | coverage lock + full regression | 0 mặc định (§M) | docs revert |

Thứ tự: W1 mang toàn bộ rủi ro LLM-surface (một bump, một smoke); W2–W4 thuần
descriptor/lock offline — độc lập nhau, có thể đổi chỗ nếu review muốn, W5 đóng.
Mỗi wave một commit-set riêng, kết thúc bằng full pytest/vitest/build xanh.

## P. Non-goals (M15 KHÔNG làm)

- Không FamilySelector/FamilySpec mới; không one-variant selector (QĐ 1, 4).
- Không thiết kế lại sorting (QĐ 12) — giá trị external/live-verified sorting
  GIỮ NGUYÊN (rev2 điểm 2); chỉ có hằng canonical nội bộ + alias boundary,
  `m14_sorting` offline phải xanh nguyên trạng. Không gỡ alias trong M15 (chỉ
  xem xét sau M16 theo evidence).
- Không capability/executor/domain mới; không Selection/Quick Sort, không
  Dijkstra (QĐ 13, 14).
- Không nested truth-table production gate; không binary challenge UI (M9-S2);
  không scan predict/what-if (QĐ 14).
- Không version field trong runtime envelope; không Alembic migration cho
  việc versioning (QĐ 6).
- Không đổi FE production/renderer/3D/DSL vocabulary; không đụng scope-freeze
  §5b; không universal DSL; không module theo từng đề.
- Không comprehensive catalog evaluation; không bắt đầu M16 (QĐ 14).
- Không sửa frozen dataset; không "phủ giả" coverage.

## Q. Failure modes / stop conditions

| Failure mode | Phát hiện | Xử lý |
|---|---|---|
| Alias normalization sai/thiếu (legacy sorting value không về đúng canonical) | `m14_sorting` offline phải xanh NGUYÊN TRẠNG + alias-lock (§F Control 3) | bug boundary — sửa trước mọi bước sau; alias không được thành nguồn sự thật thứ hai |
| Reclassify seam gây vòng lặp/đổi hành vi đường thường | lock: đường prescribed=null 0 call thêm (mock đếm call); reclassify tối đa 1 lượt (assert) | bug orchestration — blocker; observer phải thấy đủ event để eval không mù |
| `ROUTE_MECHANISM_FAMILY_MISMATCH` nổ oan trên đề thường (analyze phát prescribed sai chỗ) | T4 FP-budget offline; case 2–3 smoke live | nếu analyze phát bừa prescribed cho đề ngoài phạm vi dạy → siết analyze.md 1 vòng có trace (khuôn 1b); KHÔNG nới gate cho qua |
| Gate E2 chặn oan đề thường (FP) | FP-budget offline bắt buộc trước live; case 2 của smoke | bug gate — sửa trước mọi bước sau; nếu chỉ sửa được bằng nới permissive-null thì đúng thiết kế, nếu phải keyword-patch → DỪNG (stop) |
| analyze không phát `non_binary_base` ổn định (salience) | case 1 (và 4 nếu chạy) của smoke | chấp nhận nếu classify đã tự refuse (gate = backstop, khuôn 1b); chỉ siết analyze.md 1 vòng có trace; không đuổi thêm |
| Taxonomy phình / một family đòi free-text mechanism | review W2–W4 | STOP — tín hiệu family đó không bounded được, báo user (điều kiện dừng 2 khung M15) |
| Cross-lock nổ hàng loạt khi mở rộng artifact | pytest W1 | sửa generator/lock trước khi wave sau; không nới lock cho qua |
| Chạm LLM-surface ngoài kế hoạch ở W2–W5 | diff review từng wave | dồn về một smoke cuối W5 + bump nếu buộc phải; báo user trước |
| Baseline đỏ không liên quan / quota không đủ | trước mỗi wave | DỪNG báo user (điều kiện dừng 12, 13 khung M15) |

Kế thừa nguyên vẹn stop-conditions khung M15 user đã đặt (universal DSL,
rewrite executor, LLM sinh timeline, keyword-patch-only, mất interaction,
destructive cache/history change, tách lại eval lifecycle...).

## R. COMPLETE criteria (kiểm được)

1. 14/14 entry CATALOG khai đủ: memberships + owned_mechanisms (từng
   membership) + config_contract_version + curriculum_anchor — lock K1 xanh.
2. Taxonomy đóng namespaced canonical + cross-locks K2 xanh; alias boundary
   sorting một chiều có lock (không nguồn sự thật thứ hai); analyze-exposed
   subset đúng thiết kế D2; không free-text. **Claim boundary D2 tôn trọng
   trong mọi phát ngôn**: ownership máy-đọc cho mọi family ≠ runtime
   prescription-detection cho mọi family.
3. Mechanism-consistency sống trên CẢ HAI lifecycle (selector + direct) trong
   `run_pipeline` với HAI mã tách bạch (`GATE_MECHANISM_OWNERSHIP` ↔
   `ROUTE_MECHANISM_FAMILY_MISMATCH`); mismatch không bao giờ dẫn tới
   stage_simulate trên target mâu thuẫn; reclassify bounded đúng 1 lượt;
   T1–T4 + FP-budget xanh; permissive-null được test khoá.
4. Hai control quyết định 9 khoá: **offline CẢ hex VÀ octal → capability_gap;
   live tối thiểu MỘT case non-binary-base đạt (ưu tiên hex, octal optional)**;
   binary_search unsorted → normalize + annotate, không refuse (test đặt tên +
   CORRECTNESS.md).
5. Mỗi family có phán quyết conformance ở §B được chứng minh bằng lock tương
   ứng (W2 scan proof — không selector; W3 dual-surface; W4 network known_gaps;
   W5 generic authority proof).
6. Selector token vẫn không bao giờ là envelope id; envelope shape không đổi;
   history cũ mở lại nguyên vẹn (test hiện có xanh).
7. Bất biến #22 nguyên vẹn: eval vẫn đi `run_pipeline`, observer đo được gate
   mới mà không sửa harness-lifecycle.
8. `CACHE_VERSION` = 12, đúng MỘT bump.
9. Coverage matrix cập nhật trung thực (sorting SUPPORTED + claim boundary;
   không unit mới) — lock xanh.
10. Suite `m15_wave1` đạt acceptance viết trước, nhật ký live ghi CURRENT_STATE
    §1 (logical cases/HTTP/retry/transient chính xác).
11. Full offline regression xanh (pytest/vitest/build); FE production diff = 0
    (chỉ artifact test-only + test).
12. Docs close: CURRENT_STATE §2 hàng M15, §5 cập nhật; ARCHITECTURE_MAP (nếu
    chốt bất biến mới — §S6); COVERAGE; CODE_INDEX cho module mới.
13. Không selector mới, không capability mới, M16 chưa bắt đầu.

## S. Open implementation questions (không chặn design — trả lời ở implementation plan)

1. **Chính tả + granularity chính xác của mechanism ids** từng family (vd
   `track_extreme` có tách max/min không — mặc định KHÔNG; tên tiếng Anh
   snake_case sau namespace).
2. **Hình thức code của gate E2**: mở rộng `mechanism_gate.py` (hàm mới cạnh
   `check_mechanism_ownership`) hay tách module — chọn theo diff nhỏ nhất +
   một-nguồn message.
3. **Mở rộng `FamilyMembership`**: thêm field default `()` (giữ frozen
   dataclass) — xác nhận không vỡ chỗ khởi tạo hiện có (audit: chỉ catalog.py
   khởi tạo).
4. **Cách analyze.md dạy `positional_representation.*`**: số ví dụ, vị trí
   trong prompt (gần khối sorting §O7 hiện có) — chốt khi viết, đo bằng smoke.
5. **`config_contract_version` scheme**: chuỗi đề xuất ở C2 (`algo-cfg-1`…)
   — xác nhận không cần suffix minor.
6. **Có đăng bất biến #23** ("mechanism ownership là membership-level, taxonomy
   đóng namespaced, gate so tín hiệu cấu trúc — không keyword") vào
   ARCHITECTURE_MAP không, hay chỉ ghi §6 — quyết ở W5 theo giá trị thực tế.
7. **Chi tiết seam reclassify**: nguyên văn message mâu thuẫn ghép vào user
   message của classify; tên event observer (`reclassify_attempted`?); vị trí
   assert "tối đa 1 lượt" — chốt khi viết plan, ràng buộc cứng: đường
   prescribed=null không thêm call, envelope events đủ cho harness.
8. **Error-code granularity N3**: chỉ thêm nếu categorization Wave 1 cần;
   danh sách tối thiểu nếu cần là gì.
