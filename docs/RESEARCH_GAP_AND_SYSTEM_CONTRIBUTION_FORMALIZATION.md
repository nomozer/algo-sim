# RESEARCH_GAP_AND_SYSTEM_CONTRIBUTION_FORMALIZATION

> Wave đóng **2026-09-10** trên HEAD `df8ad21`. Wave **tài liệu và khảo sát**:
> không sửa mã sản phẩm, không đổi bề mặt mô hình, không gọi model ứng dụng.
>
> ```
> APPLICATION_LLM_CALLS = 0      PRODUCT_CODE_CHANGED   = NO
> REAL_PROVIDER_CALLS   = 0      MODEL_FACING_CHANGED   = NO
> CACHE_VERSION_CHANGED = NO     HISTORICAL_ARTIFACTS_CHANGED = NO
> ```
>
> Tra cứu web và đọc bài báo **không** đi qua `backend/app`, không dùng
> `GEMINI_API_KEY`, không sinh Semantic Program nào ⇒ không tính là application
> LLM call.

## 0. Tài liệu sinh ra

| file | vai trò |
|---|---|
| `docs/research/RELATED_WORK_SEARCH_PROTOCOL.md` | giao thức scoping review + **sai lệch giao thức** |
| `docs/research/LITERATURE_COMPARISON_MATRIX.md` | ma trận 20 hàng × 20 trục |
| `docs/research/RESEARCH_GAP_AND_CONTRIBUTIONS.md` | ba loại khoảng trống · C1–C4 · ba phát biểu · rà soát RQ |
| `docs/research/CLAIM_TO_EVIDENCE_MAP.md` | 18 tuyên bố ↔ artifact ↔ **lớp bằng chứng** |
| `docs/research/PUBLICATION_READINESS_ASSESSMENT.md` | 8 mục + loại bài phù hợp |
| `docs/thesis/RELATED_WORK_DRAFT.md` | bản thảo §1.8 viết lại |
| `docs/thesis/references_geometry_systems.bib` | 26 mục, mỗi mục ghi mức xác minh |
| `docs/evaluation/geometry/research-gap-formalization/` | `SEARCH_LOG.json` · `INCLUDED_SOURCES.json` · `EXCLUDED_SOURCES.json` · `SOURCE_METADATA.json` · `CLAIM_AUDIT.json` |

---

## 1. Kết quả khảo sát — số

```
truy vấn đã chạy            14  (13 tiếng Anh · 1 tiếng Việt)
kết quả xem sơ bộ          111
mở trang công bố            24 lượt → 19 thành công · 5 hỏng
PRIMARY_ACADEMIC_SOURCES    23   (ngưỡng ≥ 15  ✓)
OFFICIAL_TOOL_SOURCES        3   (ngưỡng ≥  3  ✓)
COMPARABLE_ENTRIES          19   (ngưỡng ≥ 18  ✓)  + 1 hàng AlgoSim = 20 hàng
nguồn bị loại                8
nguồn hiện ra, CHƯA thẩm định 7
```

Trong 23 nguồn học thuật: **11 bình duyệt đã in kỷ yếu/tạp chí** · **1 đã được
nhận (ACL 2026)** · **12 tiền ấn bản**. Tỉ lệ tiền ấn bản cao là hình dạng thật
của mảng này — phần lớn công trình gần đề tài nhất mới ra trong 12–18 tháng.

### ⚠️ Sai lệch giao thức — phải khai mỗi lần dẫn kết quả khảo sát

Wave yêu cầu tìm tại Google Scholar · IEEE Xplore · ACM DL · SpringerLink/
ScienceDirect · arXiv · trang chính thức. **Thực tế**: mọi truy vấn đi qua **một**
giao diện web tổng quát, có chạm arXiv · ACL Anthology · NeurIPS Proceedings ·
OpenReview · trang nhà cung cấp, nhưng **không** truy vấn native trong IEEE
Xplore, ACM DL, SpringerLink hay Google Scholar.

⇒ Độ phủ cho mảng IEEE/ACM/Springer **chưa** tuyên bố được. Mọi phát biểu mang
giới từ *"trong phạm vi đã khảo sát"*. Đóng nợ trước khi nộp **bài báo** (không
bắt buộc cho khoá luận): chạy lại 14 chuỗi trong giao diện native của ba cơ sở
dữ liệu ấy.

---

## 2. Hệ đã giải quyết vấn đề nghiên cứu nào

> Cho một đề hình học không gian viết bằng tiếng Việt (Toán 11–12), sinh ra một
> **mô phỏng 3D chạy được và kiểm chứng được**: chuỗi bước dựng tất định, các đại
> lượng tính bằng số học chính xác, và một cảnh ba chiều tua được theo từng bước
> — sao cho **không giai đoạn nào** để mô hình ngôn ngữ quyết định một con số hay
> một kết luận đúng/sai.

Ba ràng buộc đi kèm, cả ba có chủ đích: **không làm tròn** · **không xấp xỉ hình**
(đề vượt khả năng biểu đạt phải bị từ chối có địa chỉ) · **không có mã riêng cho
từng dạng bài**.

---

## 3. Ba loại khoảng trống — tóm tắt

Chi tiết ở `RESEARCH_GAP_AND_CONTRIBUTIONS.md §1`.

**Nghiên cứu.** Bảy điều kiện (đề 3D tiếng Việt · IR có kiểu · kiểm chứng tất
định · số học chính xác · mô phỏng 3D tương tác · phát lại quá trình dựng · từ
chối có cấu trúc). **Không điều kiện nào tự nó mới**; chỗ trống là **giao** của
chúng, cụ thể là giao của điều kiện 1 + 4 + 5 + 6 + 7.

**Kỹ thuật.** Tám lớp lỗi đã đóng, mỗi lớp có bằng chứng: JSON hợp lệ nhưng sai
quan hệ hình học (K1) · nguồn dữ kiện tồn tại nhưng nội dung không khớp (K2) ·
đáp số đúng nhưng hình sai (K3) · khối lõm cho thể tích sai (K4 — hệ từng **phục
vụ** `28` thay vì `20`) · mặt phẳng khác nhau cho cùng diện tích thiết diện (K5) ·
thiếu trace/producer (K6) · hình chưa kiểm chứng vẫn có nguy cơ được phục vụ (K7) ·
**bộ đo sai theo hướng tố cáo hệ** (K8).

**Sản phẩm.** Giao diện · nhãn · responsive · thẩm mỹ. Có giá trị sử dụng,
**không** được gọi là điểm mới khoa học.

---

## 4. Hai công trình làm hẹp khoảng trống — nêu tên, không giấu

Đây là phát hiện quan trọng nhất của wave, vì nó **bác một phần** phát biểu
khoảng trống đang có trong `THESIS_DRAFT §1.8`.

| công trình | nó đã làm gì | phần nào của khoảng trống bị mất |
|---|---|---|
| **GeoBuildBench** (2026, tiền ấn bản) | benchmark *đề tự nhiên → chương trình DSL → hình thoả **ràng buộc kiểm được***, 489 đề tiếng Trung | Ý tưởng nền *"dựng hình thực thi được từ đề tự nhiên, có kiểm chứng"* **không còn mới**. Còn lại: 2D · là **thước đo** chứ không phải hệ phục vụ |
| **Draw2Think** (2026, tiền ấn bản) | vòng *Propose–Draw–Verify* trên constraint engine GeoGebra, khai phủ **cả hình không gian**, +16,4 % ở hình không gian | *"dựng hình 3D từ đề bài"* **không còn** là chỗ trống. Còn lại: mục đích là **giải đúng hơn**, thẩm quyền số thuộc engine có sẵn, không có từ chối hướng người học |

Và một công trình định vị chính xác chiều của khoảng trống:

**Geoparsing** (ACL 2026, đã được nhận) là công trình **duy nhất trong tập khảo
sát** có ngôn ngữ hình thức hợp nhất cho cả hình phẳng và hình không gian — nhưng
chạy **chiều ngược**: hình → ngôn ngữ hình thức. AlgoSim đi đề → chương trình →
hình. Đây là cách phát biểu khoảng trống chặt nhất mà bằng chứng cho phép.

---

## 5. Kiến trúc theo ĐƯỜNG CHẠY THẬT

### 5.1. Sơ đồ dùng được trong luận văn

```
        ┌──────────────────────────── VÙNG XÁC SUẤT ────────────────────────────┐
        │                     (mô hình ngôn ngữ, có thể sai)                    │
        │                                                                       │
đề tiếng Việt                                                                   │
   │    │                                                                       │
   ▼    │                                                                       │
┌────────────────┐  KHÔNG phải hình học → unsupported · GATE_OUT_OF_SCOPE       │
│ detect_domain  │  TẤT ĐỊNH · chạy trên VĂN BẢN · 0 lượt gọi model             │
└───────┬────────┘  (fail-closed, không còn nhánh nào khác)                     │
        │ hình học                                                              │
        ▼                                                                       │
┌──────────────────────┐   ① LLM đọc đề, trích nghĩa vụ + dữ kiện              │
│ stage_semantic_      │      → RequestContract  ĐÓNG BĂNG                      │
│ analyze              │                                                        │
└───────┬──────────────┘                                                        │
        ▼                                                                       │
┌──────────────────────┐   ② LLM viết CÁC BƯỚC DỰNG (sửa ≤ 3 lượt)             │
│ stage_semantic_      │      → Semantic Program                                │
│ program              │      mọi toán hạng hình học là TÊN vật đã dựng         │
└───────┬──────────────┘      (cưỡng chế ở LƯỢC ĐỒ, không ở prompt)             │
        │                                                                       │
════════╪═══════════════ R0 ═══ SAU ĐÂY KHÔNG CÒN LƯỢT GỌI MODEL ══════════════╪═
        │                                                                       │
        ▼            ┌──────────────── VÙNG TẤT ĐỊNH ─────────────────┐        │
┌──────────────────┐ │  chuẩn hoá + thẩm định tĩnh                    │        │
│ contract ·       │ │  hoisting · ir_static_check                    │        │
│ hoisting · IR    │ └───────────────────────────────────────────────┘        │
└───────┬──────────┘                                                            │
        ▼                                                                       │
┌──────────────────┐   grounding_gate  — mọi dữ kiện truy về ĐỀ                 │
│ grounding ·      │   coverage_gate   — khai trung thực năng lực               │
│ coverage         │   source invariants                                        │
└───────┬──────────┘                                                            │
        ▼                                                                       │
┌──────────────────┐   NHÂN HÌNH HỌC: exact → predicates → kernel → measure     │
│ interpreter →    │   ℚ mở rộng bởi căn thức và π · KHÔNG `float`              │
│ geometry kernel  │   (+ radical · section · curved)                           │
└───────┬──────────┘                                                            │
        ▼                                                                       │
┌──────────────────┐   kiểm lại TỪ HÌNH, không tin số mô hình khai              │
│ GEOMETRY_CHECKERS│   + postconditions                                         │
└───────┬──────────┘                                                            │
        ▼                                                                       │
┌──────────────────┐   trace (producer/depends) → scene3d                       │
│ pipeline_adapter │   song ánh  khung k ⇔ bước k  (bất biến #31)               │
│ transport ·      │                                                            │
│ scene3d          │                                                            │
└───────┬──────────┘                                                            │
        ▼                                                                       │
   ValidatedSimulationEnvelope                                                   │
        │                                                                        │
        ├── phục vụ được  → Scene3DExplorer: chọn vật · tách khối · TUA BƯỚC     │
        └── không kiểm chứng được → TỪ CHỐI CÓ CẤU TRÚC                          │
              giai đoạn dừng · loại thất bại · mã lỗi · thông điệp tiếng Việt    │
        └────────────────────────────────────────────────────────────────────────┘
```

**Điều sơ đồ phải làm nổi bật, và là luận điểm của đề tài:** đường kẻ `R0`. Trên
đường ấy mô hình được phép sai; dưới đường ấy không thành phần nào có quyền đoán.

### 5.2. Bảng tầng

| tầng | nhiệm vụ | vào | ra | thẩm quyền | lỗi bị chặn | bằng chứng | hạn chế còn lại |
|---|---|---|---|---|---|---|---|
| `detect_domain` | phân loại miền | văn bản | miền hoặc từ chối | **tất định** | bài ngoài hình học tiêu quota | fail-closed, 0 lượt gọi | phân loại theo văn bản, không hiểu ngữ nghĩa sâu |
| `stage_semantic_analyze` | trích nghĩa vụ + dữ kiện | đề | `RequestContract` | **LLM** | — | `n1` 3 fact toạ độ, `n2` 4 | `ANALYZE_SOURCE_FACT_COMPLETENESS = PARTIAL`; `n3`/`n4` **không** fact toạ độ nào |
| `stage_semantic_program` | tổng hợp bước dựng | contract | Semantic Program | **LLM** (≤ 3 lượt sửa) | — | `FIRST_ATTEMPT 6/7` | n = 1 mỗi họ |
| `contract`/`hoisting`/`ir_static_check` | chuẩn hoá + thẩm định tĩnh | IR thô | IR hợp lệ | **tất định** | sai kiểu toán hạng, IR không hợp lệ | `p3` bị chặn ở `ir_static` rồi sửa được | `CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL` |
| `grounding_gate` | truy dữ kiện về đề | IR + contract | pass/từ chối | **tất định** | mô hình **bịa dữ kiện** | `n1` bị `UNANCHORED_DERIVED_ASSUMPTION` | đường từ chối R0 *bên trong* vòng tổng hợp không phát mã cho `cham_ca_am` |
| `coverage_gate` | khai trung thực năng lực | IR | pass/từ chối | **tất định** | phục vụ thứ ngoài bao đóng | `n2` = `requested_operation_uncovered` | ranh giới chứng minh bằng **vắng mặt**, không bằng mã lỗi mang tên họ |
| `interpreter` + kernel | thực thi, tính đại lượng | IR | state + số | **tất định**, ℚ(√, π) | làm tròn, sai vị ngữ | **12/12** đại lượng khớp từng ký tự + oracle độc lập | bao đóng số là ℚ(√, π); ngoài ⇒ từ chối |
| `GEOMETRY_CHECKERS` + `postconditions` | kiểm lại từ hình | state | pass/từ chối | **tất định** | đáp số đúng mà hình sai | 7/7 hậu điều kiện | checker theo nghĩa vụ đã đăng ký, không phải kiểm toàn diện |
| `pipeline_adapter`/`scene3d` | dẫn xuất cảnh + dòng thời gian | trace | envelope | **tất định** | cảnh không truy được về bước | `TRACE 7/7` · `SCENE3D 7/7`; bất biến #31 | đo **cấu trúc**, không đo chất lượng sư phạm |
| bề mặt học sinh | hiển thị hoặc từ chối | envelope | UI | renderer chỉ **ĐỌC** | định danh kỹ thuật lọt lên UI | 66/66 phép kiểm · **12/12 đáp số đọc trên màn hình** | `PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED` |

---

## 6. Đóng góp — phân loại

```
C1 NOVELTY_CANDIDATE        1
C2 INTEGRATIVE_CONTRIBUTION 3
C3 ENGINEERING_CONTRIBUTION 4
C4 PRODUCT_FEATURE          3
```

**C1.1** — nhân số học chính xác làm **thẩm quyền duy nhất** của đáp số trong một
đường ống LLM → dựng hình, đáp số giữ dạng ký hiệu, đối chiếu bằng oracle cài độc
lập. Căn cứ: cột *số học chính xác* của ma trận trả `Không` cho hai hàng đã đọc rõ
và `NR`/`UNCLEAR` cho phần còn lại. ⚠️ **VeriGeo (2026) là đối thủ gần nhất và
phải nêu tên mỗi lần dẫn C1.1**; nếu đọc toàn văn VeriGeo thấy nó giữ dạng chính
xác thì **C1.1 hạ xuống C2**.

**C2** — ① đóng góp tích hợp có kiểm chứng (đúng giả thuyết wave đặt ra, **giữ
nguyên** sau khảo sát) · ② R0 cưỡng chế bằng **lược đồ** · ③ song ánh khung ⇔ bước.

**C3** — biên thẩm định sáu tầng · nền tất định cho khối lõm và thiết diện xiên ·
trung thực năng lực ba mức · kỷ luật đo lường (gồm **tự bác bộ đo của chính mình**).

**C4** — nhãn hiển thị 12/12 · hidden-line động · thẻ từ chối tiếng Việt. **Không**
đếm vào đóng góp khoa học.

---

## 7. Rà soát năm câu hỏi nghiên cứu — `RQS_MAPPED = 5/5`

| RQ | trả lời trực tiếp | đề nghị | lý do |
|---|---|---|---|
| RQ1 độ phủ | **Có** | giữ nguyên | metric đo được bằng quét AST |
| RQ2 tính đúng | **Có** | chỉnh câu chữ | bản thảo phải viết **12** đại lượng, không phải 11 (đính chính D-1) |
| RQ3 tự sinh | **Một phần** | chỉnh câu chữ | in kèm mẫu số; cấm chữ *ổn định* và tỉ lệ % đứng một mình |
| RQ4 an toàn | **Có** | **tách làm hai** | đang gộp *có từ chối không* (2/2 ✓) với *có từ chối ĐÚNG CHỖ không* (`TARGET_BOUNDARY_PASS = 1/2`); gộp lại làm con số 1/2 biến mất |
| RQ5 hiệu quả | **Một phần** | giữ nguyên | mô tả kèm mẫu số |

Không sửa registration lịch sử. Năm RQ hiện có **phủ đủ** năm trục gợi ý của wave.

---

## 8. Tuyên bố PHẢI giới hạn

Chín mục ở `RESEARCH_GAP_AND_CONTRIBUTIONS.md §5`: tác động học tập · tư duy
không gian · dễ dùng · ổn định trên phân phối rộng · phủ toàn bộ hình học không
gian · tốt hơn GeoGebra mọi tiêu chí · triển khai đại trà · mọi chương trình mô
hình sinh đều đúng · khối tròn xoay tổng quát và boolean geometry.

⚠️ **Một ca mỗi họ chỉ tạo bằng chứng phát triển hoặc nghiệm thu hẹp**, không tạo
bằng chứng về độ ổn định thống kê.

---

## 9. Trôi danh tính — phát hiện phụ, phải ghi

| | lúc đo live (08/09) | tại HEAD (10/09) |
|---|---|---|
| candidate | `d72db7c3…` | **`96a9368b50603c79…`** |
| `CACHE_VERSION` | `94` | **`95`** |

`docs/thesis/CLAIM_EVIDENCE_MATRIX.md` §G ghi *"hai giá trị hiện trùng nhau"* và
*"`CACHE_VERSION = 94` ở cả hai thời điểm"* — **đúng lúc viết, sai hôm nay**.
Đính chính ghi ở `CLAIM_TO_EVIDENCE_MAP.md §0`; **không sửa** bản gốc.

Hệ quả phải khai trong khoá luận: mọi con số của lượt live mô tả bản `d72db7c3`,
**không** mô tả bản đang chạy.

---

## 10. Cổng hoàn thành

```
PRIMARY_ACADEMIC_SOURCES      23  ≥ 15   PASS
OFFICIAL_TOOL_SOURCES          3  ≥  3   PASS
COMPARABLE_ENTRIES            19  ≥ 18   PASS
SEARCH_PROTOCOL_RECORDED           YES   PASS  (kèm SAI LỆCH đã khai)
EVERY_MATRIX_CLAIM_CITED_OR_NR     YES   PASS
ALGORITHM_ARCHITECTURE_MAPPED      YES   PASS  (§5, 10 tầng + sơ đồ)
RQS_MAPPED                        5/5    PASS
CLAIMS_MAPPED_TO_ARTIFACTS         YES   PASS  (18 tuyên bố)
UNSUPPORTED_SUPERLATIVE_CLAIMS       0   PASS
HISTORICAL_ARTIFACTS_CHANGED        NO   PASS
PRODUCT_CODE_CHANGED                NO   PASS
MODEL_FACING_CHANGED                NO   PASS
APPLICATION_LLM_CALLS                0   PASS
REAL_PROVIDER_CALLS                  0   PASS
```

Cổng đã chạy: `freeze_evaluation_candidate.py --verify` exit 0 (92 file,
`96a9368b…`) · `lock_cache_identity.py --verify` exit 0 @ v95 · `git diff --check`
sạch · `pytest tests/semantic_program tests/test_current_state_identity.py -q` ·
vitest có mục tiêu. **Kế thừa**: pytest toàn bộ và `npm run build` — 0 byte mã
sản phẩm đổi trong wave này.

`NEXT_ACTION = FRONTEND_PRODUCT_DESIGN_AUDIT_AND_INTERACTIVE_PROTOTYPE`

⚠️ Nhãn ấy là nhãn wave **đã chạy và bị TỪ CHỐI** (`USER_APPROVAL = REJECTED`,
prototype đã gỡ 2026-09-10). Lượt kế tiếp phải bắt đầu bằng **mockup tĩnh trước
khi viết code** (`STATIC_VISUAL_MOCKUP_BEFORE_CODE`), không dựng lại prototype
chạy được rồi mới hỏi.
