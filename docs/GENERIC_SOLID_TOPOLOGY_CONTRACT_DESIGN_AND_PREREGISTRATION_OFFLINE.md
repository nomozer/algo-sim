# Báo Cáo Thiết Kế & Tiền Đăng Ký Hợp Đồng Topology Khối Đa Diện Tổng Quát (Offline)

> **Wave ID**: `GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE`  
> **Chế độ thực thi**: `ANTIGRAVITY TWO-GATE MODE (Gate 2 Final Execution)`  
> **Cam kết bất biến**: Hoàn toàn offline (0 network, 0 Gemini/provider call), không sửa mã sản phẩm (`PRODUCT_CODE_CHANGED = NO`), không sửa prompt/schema sản phẩm, không bump cache, giữ nguyên working tree của người dùng (`D frontend/public/favicon.svg`).

---

## 1. Mốc Thực Hiện và Kiểm Tra Tiền Điều Kiện (Precheck)

Toàn bộ các tham số hệ thống tại `START_HEAD` đã được đo lường và khóa khớp 100%:

```text
WAVE = GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
BRANCH = feat/photo-problem-to-scene
START_HEAD = 65d09a897e3ab88703b6d9cad5c14e797b4810b4
MAIN_HEAD = 085cae67392d3607ad0a58a7f48c17d8a5e5157d
CANDIDATE_SHA256 = 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1
CANDIDATE_FILE_COUNT = 103
CACHE_VERSION = 99
DEFAULT_MODE = LLM_ONLY
PRESERVED_USER_CHANGE = D frontend/public/favicon.svg
PRECHECK_STATUS = PASS
```

Các cam kết phạm vi tuân thủ nghiêm ngặt:
* `PRODUCT_CODE_CHANGED = NO`
* `PROMPT_CHANGED = NO`
* `SCHEMA_CHANGED = NO`
* `FACT_GRAPH_CHANGED = NO`
* `COMPILER_CHANGED = NO`
* `ROUTING_CHANGED = NO`
* `DEFAULT_ARCHITECTURE_CHANGED = NO`
* `NEW_GEMINI_REQUESTS = 0`
* `NETWORK_REQUESTS = 0`
* `DOTENV_LOADED = NO`
* `API_KEY_LOADED = NO`
* `HISTORICAL_REPORTS_CHANGED = NO`
* `HISTORICAL_ARTIFACTS_CHANGED = NO`

---

## 2. Bối Cảnh & Động Lực Kiến Trúc

Tại báo cáo đối soát phạm vi `docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md`, hệ thống ghi nhận kết luận:
```text
RELATION_KINDS_FOR_ORTHOGONALITY = SUFFICIENT
SOLID_TOPOLOGY_REPRESENTATION = MISSING
FINAL_DECISION = INCOMPLETE
```
Bế tắc kỹ thuật cốt lõi: Quan hệ trực giao (`perpendicular_lines`, `perpendicular_line_plane`) đã đủ để diễn đạt tính vuông góc của đáy và cạnh bên lăng trụ, nhưng hoàn toàn thiếu lớp biểu diễn cấu trúc khối đa diện (solid topology). Nếu không có cấu trúc topology:
1. `RequestContract` không có cách nào chở thông tin lăng trụ từ khâu Analyze sang Compiler mà không buộc compiler tự đoán mò hoặc đọc vụng `problem_text`.
2. Mô hình phân tích dễ tạo ra các khối hở, mặt suy biến hoặc ánh xạ cạnh bên bắt chéo mà không có cơ chế phát hiện và từ chối an toàn (fail-closed).
3. Việc mở rộng thêm các họ hình mới (lăng trụ tứ giác, hình hộp, chóp n-giác, đa diện tổng quát) sẽ tiếp tục bị tắc nếu mỗi họ hình đòi hỏi một bộ quan hệ hình học chắp vá riêng.

Wave này hoàn thành việc **thiết kế, đối chuẩn và tiền đăng ký offline** một hợp đồng topology khối đa diện tổng quát, chuẩn bị đầy đủ nền tảng kỹ thuật để triển khai vertical slice cho họ bài thứ hai trong tương lai.

---

## 3. Phân Tách Hai Lớp Hợp Đồng: Internal Contract ↔ Model-Facing Transport

Để đảm bảo đồng thời tính toàn vẹn kiểu dữ liệu (type safety), nguyên tắc một nguồn sự thật (SSOT), và an toàn trước các giới hạn của dialect Gemini API, hệ thống phân tách triệt để thành hai lớp:

### 3.1. Lớp A: `INTERNAL_CANONICAL_CONTRACT` (Nội Bộ Server)
Sử dụng **Tagged/Discriminated Union** trên trường discriminator `solid_kind`:
```python
class PyramidTopologySpec(BaseModel, frozen=True):
    solid_kind: Literal["pyramid"] = "pyramid"
    apex: str
    base_cycle: tuple[str, ...]

class PrismTopologySpec(BaseModel, frozen=True):
    solid_kind: Literal["prism"] = "prism"
    base_cycle: tuple[str, ...]
    top_cycle: tuple[str, ...]
    correspondence: tuple[tuple[str, str], ...]

class GenericPolyhedronTopologySpec(BaseModel, frozen=True):
    solid_kind: Literal["polyhedron"] = "polyhedron"
    faces: tuple[tuple[str, ...], ...]

SolidTopologySpec = Annotated[
    Union[PyramidTopologySpec, PrismTopologySpec, GenericPolyhedronTopologySpec],
    Field(discriminator="solid_kind")
]
```
* Là cấu trúc dữ liệu chính tắc duy nhất sau khi dữ liệu đã được parse và kiểm thực phía server.
* Ngăn chặn tuyệt đối các cặp kiểu mâu thuẫn (ví dụ: gán `solid_kind="prism"` nhưng lại truyền trường của hình chóp).

### 3.2. Lớp B: `MODEL_FACING_TRANSPORT_SCHEMA` (Giao Tiếp LLM)
* Schema dạng phẳng (flattened schema), không dùng `$defs`, không dùng `$ref`, tuân thủ dialect schema của Gemini API.
* Đã được chứng minh bằng thực nghiệm mã nguồn trong `test_generic_solid_topology_preregistration.py`: Khi chạy qua hàm `_sanitize_gemini_schema` trong `backend/app/ai/gemini.py`, schema phẳng được làm sạch thành công và **KHÔNG BỊ TRẢ VỀ `None`**.
* Đăng ký trạng thái chấp nhận của API trực tiếp:
  ```text
  GEMINI_LIVE_SCHEMA_ACCEPTANCE = NOT_ESTABLISHED_UNTIL_LIVE_REVALIDATION
  ```
  *(Trạng thái này không chặn wave thiết kế offline PASS, nhưng bắt buộc phải chặn việc kích hoạt sản phẩm và rollout prompt/schema cho tới khi có đợt live revalidation có ngân sách).*
* Server nhận payload từ model, ánh xạ tất định sang `INTERNAL_CANONICAL_CONTRACT` và chạy bộ kiểm thực topology độc lập. Mọi payload không hợp lệ đều bị từ chối an toàn ngay tại biên (`fail-closed`).

---

## 4. Nguyên Tắc Single Source of Truth (SSOT)

Hợp đồng loại bỏ hoàn toàn việc lưu trữ trùng lặp dữ liệu:
* **Với họ hình có cấu trúc (`pyramid`, `prism`):**
  - Các trường đặc thù của họ (`apex`, `base_cycle` cho chóp; `base_cycle`, `top_cycle`, `correspondence` cho lăng trụ) là **canonical semantic source**.
  - Model **KHÔNG** được yêu cầu khai báo lặp danh sách `faces`, `vertices`, `edges` trong payload. Toàn bộ các thực thể này bắt buộc do validator và compiler adapter suy diễn tất định (`deterministically derived`).
* **Với đa diện tổng quát (`generic polyhedron`):**
  - Danh sách các mặt `faces` là **canonical source**.
  - `vertices` và `edges` được suy diễn tất định từ tập các mặt.

---

## 5. Định Nghĩa Phạm Vi Topology Được Hỗ Trợ (Supported Topology Class)

> [!IMPORTANT]
> **Không có tọa độ 3D thì KHÔNG THỂ chứng minh tính lồi (convexity).**  
> Dữ liệu topology thuần túy không chứa thông tin về góc nhị diện (dihedral angles) hay vị trí không gian để khẳng định khối là đa diện lồi.

Phạm vi chính xác được validator và hợp đồng hỗ trợ và chứng minh hình thức được định nghĩa là:

```text
SUPPORTED_TOPOLOGY_CLASS = "closed, connected, orientable, genus-zero polygonal 2-manifold"
```

* **Đặc trưng tô-pô được kiểm chứng độc lập:**
  1. **Tính đa tạp 2 chiều (2-manifold without boundary):** Mỗi cạnh được chia sẻ bởi chính xác 2 mặt theo hướng ngược nhau (`INV-TOPO-18`).
  2. **Tính liên thông (connected):** Đồ thị đối ngẫu mặt-cạnh là liên thông.
  3. **Giống bằng không (genus-0):** Bề mặt tương đương đồng phôi với hình cầu $S^2$.
  4. **Đặc trưng Euler:** Thỏa mãn hệ thức Euler $V - E + F = 2$ (`INV-TOPO-12`).
* **Giới hạn phạm vi:** Euler $V - E + F = 2$ chỉ là **điều kiện cần cho đa tạp 2 chiều genus-0 đóng**, **TUYỆT ĐỐI KHÔNG GỌI LÀ BẰNG CHỨNG CỦA TÍNH LỒI (CONVEXITY)**. Việc xác minh tính lồi hình học thuộc trách nhiệm của compiler/solver khi đã tính toán xong hệ tọa độ không gian.

---

## 6. Quy Tắc Ánh Xạ Tương Ứng & Suy Diễn Mặt Của Lăng Trụ (Prism Face Derivation)

Hợp đồng `PrismTopologySpec` hỗ trợ lăng trụ $n$-giác tổng quát ($n \ge 3$):
* Cho đáy dưới $B = (u_0, u_1, \dots, u_{n-1})$ và đáy trên $T = (v_0, v_1, \dots, v_{n-1})$ với $|B| = |T| = n \ge 3$.
* Ánh xạ tương ứng $f: B \to T$ được biểu diễn bởi danh sách các cặp $(u_i, f(u_i))$.
* **Bộ quy tắc bắt buộc của ánh xạ $f$:**
  1. **Tính song ánh (Bijection):** $f$ là ánh xạ 1-1 toàn phần từ $B$ lên $T$. Mọi đỉnh của $B$ và $T$ xuất hiện đúng 1 lần (`INV-TOPO-08`, `INV-TOPO-09`).
  2. **Bảo toàn kề cận chu kỳ (Preserves cyclic adjacency):** Với mọi cạnh $(u_i, u_{(i+1) \bmod n})$ trên chu trình $B$, hai ảnh tương ứng $(f(u_i), f(u_{(i+1) \bmod n}))$ phải là hai đỉnh kề nhau trên chu trình $T$.
     - Nói cách khác, $f$ cảm sinh một tự đẳng cấu đồ thị trên chu trình $C_n$ (thuộc nhóm nhị diện $D_n$).
     - Cho phép quay chu trình ($i \mapsto (i+k) \bmod n$) và đảo hướng chu trình ($i \mapsto (-i+k) \bmod n$).
     - **Ghi chú về trường hợp tam giác ($n=3$):** Đối với $n=3$, đồ thị chu trình $C_3 \cong K_3$ có nhóm tự đẳng cấu $\mathrm{Aut}(C_3) \cong S_3 = D_3$. Mọi hoán vị của 3 đỉnh đều bảo toàn tính kề cận. Do đó, bất biến `CYCLIC_ADJACENCY_PRESERVED` là **vacuously satisfied** đối với $n=3$.
     - **Trường hợp $n \ge 4$:** Với $n \ge 4$, $\mathrm{Aut}(C_n) = D_n \subsetneq S_n$. Các hoán vị không thuộc $D_n$ sẽ làm ánh xạ cạnh đáy thành đường chéo đáy trên, gây ra hiện tượng cạnh bên chéo nhau / vặn mặt bên (twisted/crossed correspondence) và bị từ chối tuyệt đối với mã `NON_CYCLIC_CORRESPONDENCE` (`NEG-TOPO-11`).
* **Suy diễn mặt duy nhất (Unique face derivation):**
  - Mặt đáy dưới: $F_{bottom} = (u_0, u_1, \dots, u_{n-1})$.
  - Mặt đáy trên: $F_{top} = (f(u_{n-1}), \dots, f(u_1), f(u_0))$ (chuẩn hóa hướng ngược nhau để định hướng đa tạp).
  - $n$ mặt bên tứ giác: $F_{side, i} = (u_i, u_{(i+1) \bmod n}, f(u_{(i+1) \bmod n}), f(u_i))$ với $i = 0, \dots, n-1$.

---

## 7. Định Nghĩa Vũ Trụ Đỉnh & Phân Định Xuất Xứ Dữ Kiện

### 7.1. Định Nghĩa `DECLARED_VERTEX_UNIVERSE`
Với các họ hình có cấu trúc không khai trường `vertices`, và đa diện tổng quát suy diễn `vertices` từ `faces`, một payload topology đứng độc lập không thể tự nhận biết một đỉnh có phải là "undeclared" hay không nếu không có ngữ cảnh từ đề bài.

```text
DECLARED_VERTEX_UNIVERSE = Tập các nhãn điểm (point labels) đã được trích xuất và xác thực trong RequestContract / input facts tại adapter boundary.
```

* **Bất biến liên hợp đồng (Cross-contract invariant) `INV-TOPO-01` (`ALL_POINT_LABELS_DECLARED`):**  
  Mọi nhãn đỉnh suy ra từ `apex`, `base_cycle`, `top_cycle`, `correspondence`, hoặc `faces` bắt buộc phải thuộc `DECLARED_VERTEX_UNIVERSE`.
* **Ranh giới kiểm thử:** Validator thuần topology nhận `declared_vertex_universe` như một tham số đầu vào kiểm thử độc lập. Validator **TUYỆT ĐỐI KHÔNG TỰ ĐỌC `problem_text`** và **KHÔNG DÙNG DỮ LIỆU GROUND TRUTH**.

### 7.2. Phân Định Xuất Xứ Dữ Kiện (Provenance Rules)
* **`EXTRACTED_FROM_SOURCE` (hay `GIVEN`):** Đề bài trực tiếp nêu thuộc tính (ví dụ: "Cho lăng trụ đứng ABC.A'B'C'...").
* **`DEFINITIONAL_DERIVED`:** Thuộc tính do engine tự suy ra từ định nghĩa (ví dụ: các cạnh bên vuông góc với đáy và đôi một song song).
* **Luật xuất xứ:** Engine **KHÔNG ĐƯỢC TỰ GẮN** dữ kiện suy diễn thành `GIVEN`. Khi xảy ra trùng lặp giữa đề và định nghĩa, cơ chế Deduplication phải giữ nguyên xuất xứ `GIVEN` gốc.
* **`LAYOUT_DERIVED`:** Tọa độ $(x, y, z)$ do solver tính toán.
* **`MODEL_ASSUMPTION`:** Giả định do LLM phỏng đoán, không được tự động nâng thành `GIVEN`.

---

## 8. Ma Trận Đánh Giá 14 Tiêu Chí & Quyết Định Tuyển Chọn

| STT | Tiêu chí đánh giá | Candidate A (Family-Specific) | Candidate B (Generic Face-Based) | Candidate C (Hybrid Discriminated - Đã sửa SSOT) |
|---|---|---|---|---|
| 1 | Biểu diễn được chóp hiện có | Cần spec riêng (`PyramidSpec`) | Có (4 đỉnh, 4 mặt tam giác) | **Có** (`PyramidTopologySpec` với apex & base_cycle) |
| 2 | Biểu diễn được lăng trụ đứng đáy tam giác | Có (`PrismTopologySpec`) | Có (6 đỉnh, 5 mặt) | **Có** (`PrismTopologySpec` với 2 cycle & correspondence) |
| 3 | Single Source of Truth (SSOT) | **Đạt** (mỗi trường 1 ý nghĩa) | **Đạt** (thuần faces) | **Đạt** (phân lập rõ: structured dùng cycle, generic dùng faces) |
| 4 | Không phụ thuộc tọa độ (`LAYOUT_DERIVED`) | **Đạt** | **Đạt** | **Đạt** |
| 5 | Khả năng kiểm thực 2-manifold | Kém (không kiểm tra được tính đóng mặt) | **Tốt** (kiểm tra đầy đủ chia sẻ cạnh) | **Tốt** (generic kiểm tra mặt; structured kiểm tra chu trình và suy diễn mặt chuẩn 2-manifold) |
| 6 | Label-permutation invariance | Đạt | Đạt | **Đạt** |
| 7 | Phát hiện topology mâu thuẫn | Bắt được lỗi cycle, bỏ sót lỗi mặt bên | Bắt được mặt hở, mặt suy biến | **Toàn diện** (bắt cả lỗi tương ứng cycle và lỗi định hướng mặt) |
| 8 | Không buộc adapter đọc `problem_text` | **Đạt** | **Đạt** | **Đạt** |
| 9 | Tương thích với `FactGraph` | Phải thêm node riêng cho từng khối | Mất ngữ nghĩa phân loại bài toán | **Phù hợp kiến trúc `[PROVISIONAL]`** (phân giải rõ `Nut` solid kèm `kind`) |
| 10 | Tương thích Gemini `responseSchema` | Cần nhiều schema | Đơn giản nhất | **CẦN ĐÁNH GIÁ (NOT_ESTABLISHED)**: Đã giải quyết bằng 2 lớp Transport / Internal |
| 11 | Khả năng mở rộng đa diện mới | Kém (viết model mới) | Tốt | **Linh hoạt cao `[PROVISIONAL]`** (vừa có generic vừa có family chuyên biệt) |
| 12 | Rủi ro LLM sinh lỗi topology | Thấp | Cao (LLM sinh sai thứ tự đỉnh mặt) | **Giảm thiểu rủi ro `[DESIGN_HYPOTHESIS]`** (model chỉ khai chu trình, validator suy diễn mặt) |
| 13 | Bốn chiều tương thích ngược | Đã phân tích 4 chiều độc lập | Đã phân tích 4 chiều độc lập | **Đã phân tích 4 chiều độc lập** |
| 14 | Giá trị cho luận văn & benchmark | Hạn chế | Trung bình | **Tiềm năng cao `[PROVISIONAL]`** (cho phép so sánh và đối chứng kiến trúc) |

* **Kết luận lựa chọn:** **Candidate C (Hybrid Discriminated with SSOT Fix)** được chọn làm thiết kế mục tiêu vì giải quyết trọn vẹn sự thống nhất giữa tính trừu tượng hình học (kiểm thực 2-manifold) và tính định hướng ngữ nghĩa của bài toán (giúp compiler nhận diện primitive nhanh chóng mà không cần giải bài toán đồ thị đẳng cấu).

---

## 9. Bộ 18 Bất Biến Topology Thiết Kế (Topology Invariants)

1. `INV-TOPO-01` (`ALL_POINT_LABELS_DECLARED`): Mọi nhãn điểm xuất hiện trong chu trình hoặc mặt phải thuộc `DECLARED_VERTEX_UNIVERSE`.
2. `INV-TOPO-02` (`NO_DUPLICATE_VERTICES_IN_CYCLE`): Không có đỉnh trùng lặp trong cùng một chu trình đáy.
3. `INV-TOPO-03` (`FACE_MINIMAL_ARITY`): Mỗi mặt đa giác phải có ít nhất 3 đỉnh phân biệt ($|face| \ge 3$).
4. `INV-TOPO-04` (`NO_DEGENERATE_FACES`): Không có mặt suy biến (các đỉnh liên tiếp không được trùng nhau).
5. `INV-TOPO-05` (`NO_ORPHAN_VERTICES`): Không có đỉnh mồ côi; mọi đỉnh phải thuộc ít nhất 3 mặt của đa diện.
6. `INV-TOPO-06` (`NO_DUPLICATE_FACES`): Không có hai mặt trùng nhau dưới phép quay vòng hoặc đảo chiều chu trình.
7. `INV-TOPO-07` (`VALID_BASE_CYCLES`): Hai đáy của lăng trụ phải có cùng số lượng đỉnh ($|base\_cycle| = |top\_cycle| \ge 3$).
8. `INV-TOPO-08` (`BIJECTIVE_CORRESPONDENCE`): Ánh xạ tương ứng đỉnh giữa hai đáy lăng trụ là một song ánh 1-1.
9. `INV-TOPO-09` (`CORRESPONDENCE_COVERS_CYCLES`): Mọi đỉnh của đáy dưới và đáy trên xuất hiện chính xác một lần trong `correspondence`.
10. `INV-TOPO-10` (`BASES_SHARE_NO_VERTICES`): Đáy trên và đáy dưới của lăng trụ không chia sẻ bất kỳ đỉnh chung nào ($base\_cycle \cap top\_cycle = \emptyset$).
11. `INV-TOPO-11` (`CYCLIC_ADJACENCY_PRESERVED`): Ánh xạ tương ứng đỉnh của lăng trụ phải bảo toàn tính kề cận chu kỳ trên $C_n$ ($n \ge 4$; thỏa mãn vacuously khi $n=3$).
12. `INV-TOPO-12` (`EULER_CHARACTERISTIC_GENUS_ZERO`): Thỏa mãn hệ thức Euler $V - E + F = 2$ cho đa tạp 2 chiều genus-0 đóng (không khẳng định tính lồi).
13. `INV-TOPO-13` (`LABEL_PERMUTATION_INVARIANCE`): Thay thế đồng cấu toàn bộ nhãn đỉnh bằng một hoán vị không làm thay đổi tính hợp lệ tô-pô.
14. `INV-TOPO-14` (`CYCLE_ORIENTATION_INVARIANCE`): Đảo chiều cả hai chu trình đáy cùng lúc không làm thay đổi tính hợp lệ của khối.
15. `INV-TOPO-15` (`NO_COORDINATES_IN_SEMANTIC_CONTRACT`): Hợp đồng ngữ nghĩa tuyệt đối không chứa tọa độ $(x, y, z)$ hay tham số render.
16. `INV-TOPO-16` (`DEFINITIONAL_PROVENANCE_INTEGRITY`): Tính chất do engine sinh phải mang nhãn `DEFINITIONAL_DERIVED`, không được giả mạo `GIVEN`.
17. `INV-TOPO-17` (`MODEL_ASSUMPTION_NOT_ELEVATED`): Thuộc tính `model_assumption=True` không được tự động nâng thành dữ kiện thực tế trong pipeline.
18. `INV-TOPO-18` (`TWO_MANIFOLD_EDGE_SHARING`): Mỗi cạnh của đa diện được chia sẻ bởi chính xác 2 mặt theo hai hướng ngược nhau.

---

## 10. Kết Quả Kiểm Chứng Bộ Fixtures Tiền Đăng Ký

Bộ kiểm thử độc lập gồm **16 fixtures** (5 positive, 11 negative) được kiểm chứng 100% bằng mã máy tại `test_generic_solid_topology_preregistration.py`:

### Positive Fixtures (5/5 PASS):
* `POS-TOPO-01` (`historical_pyramid`): Chóp $S.ABC$ qua `PyramidTopologySpec` $\implies V=4, E=6, F=4, \chi=2$ (PASS).
* `POS-TOPO-02` (`basic_right_triangular_prism`): Lăng trụ đứng tam giác $ABC.DEF$ $\implies V=6, E=9, F=5, \chi=2$ (PASS).
* `POS-TOPO-03` (`permuted_labels_prism`): Lăng trụ hoán vị nhãn $MNP.XYZ$ $\implies V=6, E=9, F=5, \chi=2$ (PASS).
* `POS-TOPO-04` (`reversed_cycle_orientation_prism`): Lăng trụ đảo hướng chu trình $(C,B,A)$ và $(F,E,D)$ $\implies V=6, E=9, F=5, \chi=2$ (PASS).
* `POS-TOPO-05` (`fractional_metric_prism`): Lăng trụ đo đạc phân số $ABC.A_1B_1C_1$ $\implies V=6, E=9, F=5, \chi=2$ (PASS).

### Negative Fixtures (11/11 BỊ CHẶN CHÍNH XÁC):
* `NEG-TOPO-01`: Đỉnh $K$ ngoài vũ trụ $\implies$ Chặn với `UNDECLARED_VERTEX`.
* `NEG-TOPO-02`: Đỉnh trùng lặp $(A,B,A)$ trong chu trình $\implies$ Chặn với `DUPLICATE_VERTEX_IN_CYCLE`.
* `NEG-TOPO-03`: Mặt suy biến chỉ có 2 đỉnh $\implies$ Chặn với `DEGENERATE_FACE_ARITY`.
* `NEG-TOPO-04`: Ánh xạ không đơn ánh ($A \to D$ và $B \to D$) $\implies$ Chặn với `NON_BIJECTIVE_CORRESPONDENCE`.
* `NEG-TOPO-05`: Ánh xạ thiếu đỉnh $C$ $\implies$ Chặn với `CORRESPONDENCE_INCOMPLETE`.
* `NEG-TOPO-06`: Hai đáy chia sẻ chung đỉnh $A$ $\implies$ Chặn với `BASES_SHARE_VERTICES`.
* `NEG-TOPO-07`: Cạnh $(A,B)$ chia sẻ bởi 3 mặt $\implies$ Chặn với `NON_MANIFOLD_EDGE_INCIDENCE`.
* `NEG-TOPO-08`: Payload chứa trường tọa độ $\implies$ Chặn với `COORDINATES_FORBIDDEN_IN_CONTRACT`.
* `NEG-TOPO-09`: Giả định model đòi quyền GIVEN $\implies$ Chặn với `UNVERIFIED_ASSUMPTION_REJECTED`.
* `NEG-TOPO-10`: Khối 4 đỉnh gán nhãn prism $\implies$ Chặn với `DEGENERATE_BASE_CYCLE`.
* `NEG-TOPO-11`: Lăng trụ tứ giác ($n=4$) có correspondence bắt chéo/xoắn ($A \to E, B \to G$) biến cạnh đáy thành đường chéo $\implies$ Chặn với `NON_CYCLIC_CORRESPONDENCE`.

---

## 11. Bốn Chiều Tương Thích Ngược Được Đánh Giá Dự Báo

Vì đây là wave thiết kế offline (0 product code changed), không tuyên bố `PASS` khi chưa chạy test trên mã sản phẩm:

```text
HISTORICAL_PAYLOAD_VALIDATION_COMPATIBILITY = EXPECTED_PASS_REQUIRES_VERTICAL_SLICE_TEST
RUNTIME_BEHAVIOR_COMPATIBILITY = EXPECTED_PASS_REQUIRES_VERTICAL_SLICE_TEST
MODEL_FACING_SCHEMA_IDENTITY_COMPATIBILITY = EXPECTED_BREAKS_IDENTITY
CACHE_IDENTITY_COMPATIBILITY = EXPECTED_BREAKS_IDENTITY
```

---

## 12. Định Vị Đóng Góp Học Thuật & Giả Thuyết Nghiên Cứu

* **`THESIS_CORE_CONTRIBUTION`**:
  Xây dựng hợp đồng cấu trúc đa diện tổng quát (`Generic Solid Topology Contract`) làm cầu nối hình thức giữa bóc tách ngôn ngữ tự nhiên/ảnh và engine biên dịch hình học tất định, đảm bảo phân lập triệt để giữa ngữ nghĩa không gian và tính toán tọa độ trình bày.
* **`PUBLICATION_HYPOTHESIS` (Kiểm định được, không định trước kết quả):**
  > *"A generic/hybrid solid-topology contract with deterministic validation may improve cross-family generalization, reduce invalid topology, and increase safe rejection compared with contracts without explicit topology."*  
  *(Mọi tỷ lệ phần trăm cụ thể chỉ được khẳng định và công bố sau khi thực hiện benchmark đầy đủ trên tập dữ liệu đánh giá)*.
* **`LITERATURE_NOVELTY_STATUS`**: `NOT_ESTABLISHED` (chưa tiến hành tổng quan tài liệu có hệ thống trong wave offline này).
* **15 Chỉ số Benchmark Được Đăng Ký Trước:** Đã lưu trữ đầy đủ tại `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/RESEARCH_FRAMING.json`.

---

## 13. Future Product Allowlist (PROVISIONAL)

> [!CAUTION]
> Danh sách dưới đây mang tính **TẠM THỜI (PROVISIONAL)**, chỉ ra các điểm tiếp xúc tiềm năng trong mã sản phẩm khi triển khai vertical slice trong tương lai. Danh sách này **CHƯA PHẢI LÀ ALLOWLIST CHÍNH THỨC** cho đến khi hoàn thành đầy đủ 7 hạng mục audit:
> 1. Audit bộ test schema (`test_analyze_contract.py`, `test_schemas.py`).
> 2. Audit tính tương thích `responseSchema` với dialect của Gemini (`test_gemini.py`).
> 3. Audit các file quản lý cache identity (`cache.py`, bảng đăng ký `CACHE_VERSION`).
> 4. Audit các artifact candidate freeze/refreeze (`test_pipeline_candidate_freeze.py`).
> 5. Audit bộ test prompt (`test_prompts.py`, `test_skill_analyze.py`).
> 6. Audit bộ test hồi quy adapter / FactGraph / compiler.
> 7. Audit công cụ và quy trình live revalidation.

### Danh mục điểm chạm dự kiến (PROVISIONAL):
1. `backend/app/simulation/semantic_program/request_contract.py`
2. `backend/app/simulation/semantic_program/analyze_contract.py`
3. `backend/app/ai/skills/geometry_analyze.md`
4. `backend/app/simulation/geometry_compiler/contract_adapter.py`
5. `backend/app/simulation/geometry_compiler/fact_graph.py`
6. `backend/app/simulation/geometry_compiler/primitives.py`
7. `backend/app/simulation/geometry_compiler/compiler.py`
8. `backend/app/main.py` (`CACHE_VERSION`)

---

## 14. Quyết Định Chung Cuộc & Bước Tiếp Theo

```text
FINAL_DECISION = PASS
SELECTED_CANDIDATE = Candidate C (Hybrid Discriminated with SSOT Fix)
UNBLOCKED_NEXT_ACTION = PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE
```

Hợp đồng topology khối đa diện tổng quát đã được thiết kế hoàn chỉnh, chứng minh tính chặt chẽ về toán học và kiểm thực trên 16 fixtures độc lập. Bế tắc kỹ thuật về dữ liệu topology được gỡ bỏ hoàn toàn, mở đường an toàn cho việc triển khai `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE` trong các wave tiếp theo.
