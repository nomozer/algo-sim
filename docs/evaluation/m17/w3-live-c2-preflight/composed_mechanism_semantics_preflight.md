# M17 W3-LIVE-C2-PREFLIGHT — ngữ nghĩa cơ chế composed

**READ-ONLY.** Không sửa production, không gọi LLM, không chạy Chrome, không commit.
Baseline `f85c0b8`, tree sạch, `CACHE_VERSION 24` · `HISTORY 2` · family 11 · target 22.

## 1. Kết luận điều hành

Ba điều, theo thứ tự quan trọng:

1. **`prescribed_procedure` là tín hiệu ĐỊNH TUYẾN/RÀNG BUỘC, không phải bản kê
   cơ chế runtime.** `analyze.md` nói thẳng: *"CHỈ đặt khi đề … ÉP một cách …
   CỤ THỂ"*, mặc định `null`. Nó **không** chọn engine, **không** vào candidate
   spec, **không** hiển thị cho người học.
2. **Cổng cơ chế hiện là no-op cho 5/9 target được audit** — cơ chế của chúng
   **không hề** nằm trong enum analyze, nên `prescribed` luôn `null` và cổng trả
   `None` ngay. Chúng không "đi qua" cổng; chúng **không bao giờ chạm** cổng.
3. **W3 thất bại vì một điều kiện cấu trúc DUY NHẤT trong toàn catalog**, không
   phải vì thiếu khái niệm composition.

Điều kiện đó: `positional_representation` là **họ exposed duy nhất bị chia cho
nhiều target**, và mỗi target chỉ sở hữu một phần:

| Target | sở hữu / exposed trong họ | exposed nhưng KHÔNG sở hữu |
|---|---|---|
| `algorithm.bounded_control_flow` | **3/3** | — (miễn nhiễm) |
| `tree.traversal` | **4/4** | — (miễn nhiễm) |
| `binary.base_conversion` | 2/3 | `character_code_mapping` |
| `binary.decimal_to_binary` | 1/3 | `character_code_mapping`, `non_binary_base` |
| **`binary.character_encoding`** | **1/3** | `binary_positional_weights`, `non_binary_base` |

Và đòn quyết định: trong bốn giá trị enum, **`character_code_mapping` là giá trị
DUY NHẤT của W3 mà `analyze.md` KHÔNG có một dòng hướng dẫn nào** — trong khi hai
giá trị anh em lại được hướng dẫn rõ, và một trong hai khớp thẳng chữ "nhị phân"
trong đề ENC-3.

## 2. Hợp đồng thật của trường mechanism (truy vết mã, không suy từ tên)

| | |
|---|---|
| Sinh ở | `ai/pipeline.py::ANALYZE_SCHEMA` (~dòng 108) — `STRING`, `nullable: true`, **không** thuộc `required` |
| Enum | đóng, dẫn xuất `mechanisms.analyze_exposed_values()` — **16 giá trị** |
| Chuẩn hoá | `mechanisms.canonical_mechanism` — biên alias DUY NHẤT; `null`/`"none"` → `None` |
| Kiểm ở | `_family_mismatch` · `check_mechanism_ownership` (selector) · `check_mechanism_consistency_for_target` (direct) |
| Dùng tiếp | `completeness_gate.normalized_requested` (gộp với `requested_mechanisms` để bắt mất mát ngữ nghĩa) · observer telemetry |
| **KHÔNG** dùng để | chọn engine/executor · ghi vào candidate spec · hiển thị cho người học · phán đúng/sai runtime |

Phân loại theo bốn khái niệm của §2:

- **A — Routing/consistency mechanism: ĐÚNG.** Đây là vai trò chính.
- **B — Required educational mechanism: MỘT PHẦN**, và qua trường khác:
  `requested_mechanisms` mới là "liệt kê ĐỦ mọi cơ chế đề yêu cầu";
  `prescribed_procedure` chỉ được gộp vào ở `completeness_gate`.
- **C — Runtime implementation dependency: SAI.** Trường này chưa bao giờ mô tả
  các bước engine thực hiện. Engine W3 gọi `divideSteps` là **chi tiết hiện
  thực**, không phải thứ analyze phải khai.
- **D — Direct result ownership: SAI.** Ownership sống ở `FamilyMembership`
  trong catalog, độc lập hoàn toàn với trường analyze.

**`prescribed = none` cho W3 đi qua là THIẾT KẾ, không phải lỗ hổng.**
`mechanism_gate.py` ghi rõ ranh giới: *"vắng tín hiệu KHÔNG phải bằng chứng của
cơ chế ngoài phạm vi"* — siết chỗ này sẽ từ chối oan mọi đề "sắp xếp tăng dần".

## 3. Ownership KHÔNG độc quyền — đã có tiền lệ đang chạy

Câu hỏi §2.2 có đáp án dứt khoát: **một mechanism được nhiều target sở hữu là
chuyện bình thường và đã tồn tại**:

| Mechanism | Owners |
|---|---|
| `positional_representation.binary_positional_weights` | `binary.decimal_to_binary`, `binary.base_conversion` |
| `single_pass_scan.track_extreme` | `algorithm.find_max`, `algorithm.find_min`, `algorithm.scan` |
| `single_pass_scan.accumulate_conditional` | `algorithm.sum_if`, `algorithm.scan` |
| `single_pass_scan.count_conditional` | `algorithm.count_if`, `algorithm.scan` |
| `single_pass_scan.find_equal_early_stop` | `algorithm.linear_search`, `algorithm.scan` |

`catalog.py` còn ghi thẳng lý do: *"nhiều target cùng own một cơ chế có tiền lệ
find_max/find_min"*. Không cần abstraction mới để chia sẻ ownership.

## 4. Composition machine-readable: KHÔNG TỒN TẠI

Chuỗi `character_code_mapping → non_binary_base` chỉ có ở **comment**
(`mechanisms.py:26-29`, `character_encoding.py:16`) và prose trong
`CURRENT_STATE`. Không một cấu trúc dữ liệu nào biểu diễn quan hệ giữa hai
mechanism. Taxonomy là **danh sách phẳng** `FamilyId → tuple[str, …]`.

## 5. Vì sao target nhiều cơ chế khác không gãy

| Target | Cơ chế trong enum analyze? | Vì sao qua |
|---|---|---|
| `database.relational_table_query` (5 cơ chế) | **0/5** | analyze không phát được ⇒ `prescribed=null` ⇒ cổng no-op. Pipeline của nó được kiểm bằng `requested_operations` + `pipeline_stages`, **không** qua mechanism gate |
| `network.protocol_encapsulation` | **0/1** | như trên |
| `network.packet_routing` | **0/1** | như trên |
| `logic.boolean_dag` | **0/1** | như trên |
| `generic.rule_scene` (3 cơ chế) | **0/3** | như trên |
| `algorithm.bounded_control_flow` (3 cơ chế) | 3/3 | sở hữu ĐỦ ⇒ nhận giá trị nào cũng hợp lệ |
| `tree.traversal` (4 cơ chế) | 4/4 | sở hữu ĐỦ |

Ghi thêm một rủi ro tiềm ẩn (chưa gây lỗi): ba cơ chế `bounded_control_flow.*`
**cũng không có hướng dẫn** trong `analyze.md`. W2C an toàn chỉ vì target sở hữu
cả ba — nếu sau này tách target, nó sẽ gãy y hệt W3.

## 6. W3 — phân tích chính xác

Pipeline runtime thật: `ký tự → code point → chia lấy dư cơ số 2 → chuỗi số dư →
dãy bit`. Engine gọi `divideSteps(cp, 2, convSteps)`
(`encoding-module.tsx:253`) — tức chiến lược **quotient-remainder**, và kết quả
**dẫn ra từ** chuỗi số dư.

Trong khi đó `analyze.md` mô tả `binary_positional_weights` là *"đổi/biểu diễn
sang HỆ NHỊ PHÂN (cơ số 2) — các bit trọng số 8/4/2/1"*. Đề ENC-3 nói *"chuyển mã
đó sang nhị phân"* ⇒ **analyze tuân thủ ĐÚNG hướng dẫn nó được cho**. Không phải
LLM sai; **prompt contract thiếu**.

Ba điều phải phân biệt cho rành mạch:

- **Utility reuse:** W3 dùng lại `divideSteps` của `base_conversion`. Đây là chi
  tiết hiện thực — **không** tạo ra quyền sở hữu cơ chế.
- **Mechanism composition:** đề ENC-3 về mặt giáo dục yêu cầu **CẢ HAI** bước
  (tra bảng mã *và* đổi cơ số). Nhưng đó là việc của `requested_mechanisms`, chứ
  không phải của `prescribed_procedure`.
- **Shared ownership:** hợp lệ về nguyên tắc, nhưng ở đây sẽ nói sai — nhãn
  "trọng số 8/4/2/1" là một **khung sư phạm khác** với phép chia lấy dư mà W3
  thực sự trình bày cho học sinh.

Kết luận mục này: **sai ở metadata prompt, không sai ở implementation, cũng không
sai ở ownership.**

## 7. Đánh giá A / B / C

| Tiêu chí | **A — dạy analyze cơ chế chính** | **B — shared ownership** | **C — composition metadata** |
|---|---|---|---|
| Đúng ngữ nghĩa trường | **Có** — khôi phục bất biến "mọi giá trị exposed đều có luật phát" | Không — nói W3 sở hữu khung "trọng số 8/4/2/1" mà engine không trình bày | Không — trường này chưa bao giờ mô tả runtime dependency |
| Giữ fail-closed | **Có** — cổng không đổi một dòng | Giảm: mọi đề "đổi sang nhị phân" thành hợp lệ cho W3, mờ ranh giới với `decimal_to_binary` | Giảm: mở thêm cạnh chuyển tiếp |
| Reuse-first | **Có** — cùng khuôn luật M15/M17 sẵn có | Có — tiền lệ shared ownership | Không — phải tạo abstraction mới |
| Không special-case target-id | **Có** — luật theo HÌNH DẠNG ĐỀ ("đầu vào là ký tự") | Có | Có |
| Không danh sách viết tay song song | **Có** | Có | Không — thêm nguồn chân lý thứ hai cạnh `FAMILY_MECHANISMS` |
| Hợp với target nhiều cơ chế | **Có** — vá luôn lỗ `bounded_control_flow.*` | Không giải quyết | Không |
| **Có sửa được ENC-3 không** | **Có** | Có | **KHÔNG** — analyze phát `binary_positional_weights`, **không** nằm trong chuỗi đã khai |
| Cache | bump | bump | bump |
| Kích thước | ~1 khối `analyze.md` + lock | 1 dòng catalog | metadata + closure + test nhiều family |
| Rủi ro phạm vi | thấp | trung bình | **cao — deep hardening** |

**C bị loại thẳng**: nó không sửa được chính ca đang hỏng, vì chuỗi khai báo
(`character_code_mapping → non_binary_base`) không chứa giá trị mà analyze thực
sự phát. Đây đúng nghĩa fixture-specific và tốn kém.

**B bị loại** vì nói sai với người học và làm mờ ranh giới ký-tự ↔ số — chính
ranh giới mà ENC-4 đang chứng minh là sạch 2/2.

## 8. Khuyến nghị: **A**, dạng nhỏ nhất

Bổ sung vào `analyze.md` một khối luật cho họ positional, cùng khuôn với khối
M15/M17 đã có, phát biểu theo **hình dạng đầu vào** chứ không theo tên target:

> đầu vào là **KÝ TỰ/CHUỖI** và đề hỏi mã của ký tự → `character_code_mapping`,
> **kể cả khi** đề nói thêm "chuyển sang nhị phân" (việc đổi mã sang nhị phân
> nằm trong hợp đồng của chính năng lực đó); đầu vào đã là **SỐ** → giữ luật cũ.

Kèm một lock chống trôi: **mọi giá trị trong `analyze_exposed_values()` phải có
hướng dẫn trong `analyze.md`** — hiện có **4 giá trị vi phạm**
(`character_code_mapping` + 3 `bounded_control_flow.*`). Lock này biến lỗi đã cắn
hai lần (enum thiếu `drag`; enum thiếu `character_code_mapping`) thành đỏ tự động.

A giải thích được cả bốn ca mà §6 yêu cầu: W3 (thêm luật thiếu), database
pipeline (không đụng — cổng vốn no-op, kiểm bằng kênh operations), bounded
control flow (vá luôn lỗ tiềm ẩn), protocol encapsulation (không đụng).

**Cảnh báo thẳng:** A **buộc phải sửa `analyze.md`** — thứ mà C1 xếp vào stop
condition. Đó chính là quyết định checkpoint này tồn tại để hỏi.

## 9. Tác động người học

Không đề xuất nâng interaction. W3 đã có learner task hợp lệ (điều khiển timeline
+ giải thích cơ chế chia lấy dư), pedagogical alignment đã có bằng chứng đại diện,
**learning impact chưa được đánh giá**. Thất bại định tuyến cơ chế là vấn đề
**tích hợp LLM**, không phải vấn đề interaction — sửa interaction **không** giúp
ENC-3 qua cổng.

## 10. Việc hoãn lại

- Lock "mọi giá trị exposed phải có hướng dẫn trong `analyze.md`" (nếu không mở C2).
- Ba cơ chế `bounded_control_flow.*` thiếu hướng dẫn — chưa gây lỗi, sẽ gãy nếu
  tách target.
- `prescribed_procedure` của họ positional thực chất mã hoá **cơ số đích**, không
  phải **cách làm** — lệch với định nghĩa "ÉP một cách làm cụ thể". Ghi nhận, chưa
  đề xuất đổi taxonomy.
- Container Docker đang stale (`cache=22 · family=10 · target=20`).
