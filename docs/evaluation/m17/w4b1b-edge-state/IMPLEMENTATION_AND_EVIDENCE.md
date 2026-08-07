# W4B-1B — EDGE STATE · STEP-SCOPED INSPECTOR · EVALUATION COVERAGE

Ba việc, một chủ đề chung: **thứ engine đã biết phải đến được mắt học sinh, và
thứ học sinh chưa đáng biết thì không được lộ.**

| | |
|---|---|
| Nền | `9e8c3ed` (sau Phase I W4B-1A.1) |
| Chrome | 150.0.7871.187, headless, DPR 1, zoom 100% |
| Gate | vitest **946** · build OK · pytest **1135** · catalog matrix **22 PASS** |

---

## 1. Engine giữ provenance thay vì vứt đi (§9)

`TraverseStep.visit` nay mang **`parent`** (nút mà `current` được nạp từ đó) và
**`frontierAdded`** (hàng xóm thực sự được nạp ở bước này). Cả hai đã được tính
sẵn trong `buildTraversal` — `entry.parent` và `added` — chỉ là dùng xong rồi bỏ.

### Vì sao không được suy từ thứ tự thăm (§10)

Fixture `A–B, B–C, A–D`, DFS từ A → thứ tự thăm **A, B, C, D**. Nhưng D được nạp
từ **A**, không phải từ C, và **C với D không hề kề nhau**.

| Cách dẫn xuất | Cạnh sinh ra | Có thật trong đồ thị? |
|---|---|---|
| "nút thăm liền trước → nút hiện tại" | A–B · B–C · **C–D** | **KHÔNG** — C–D không tồn tại |
| `parent → current` (engine) | A–B · B–C · **A–D** | có, cả ba |

Renderer vẽ C–D là **bịa ngữ nghĩa** (bất biến #6) — tệ hơn hẳn việc không tô
gì. Test khoá đúng ca này, và khoá cả chiều ngược: chứng minh rằng cách ngây thơ
**thật sự** sinh ra cạnh ma.

## 2. Trạng thái cạnh là hàm THUẦN (§11, §12)

`domains/network/edge-view.ts` — không import từ module nào của domain, nên
hướng phụ thuộc một chiều, không có vòng.

Lý do tách khỏi JSX: renderer 3D của `packet_routing` là THREE.js **mệnh lệnh**.
Nếu phần dẫn xuất nằm trong component thì không có cách nào assert trạng thái
cạnh 3D bằng test. Tách ra thì phép đối chiếu 2D↔3D chỉ còn là một phép so bằng
— cùng khuôn với `layout3d` ở `render-parity.test.tsx`.

**Mỗi target chỉ dùng tập con trạng thái engine của nó thật sự có:**

| Target | Trạng thái dùng | Không dùng |
|---|---|---|
| `graph_traversal` | idle · considering · active · traversed | `remaining` — engine không biết trước đường đi |
| `packet_routing` | idle · active · traversed · remaining | `considering` — tuyến do BFS tính trước, không có nhịp cân nhắc nào để hiển thị |

`packet_routing` **không thêm một trường nào vào state**: `route + cursor` đã đủ
vì `steps[k].packetAt === route[k]`. Thêm field vào `NetStep` sẽ là nhân bản sự
thật.

**3D nay đọc cùng dẫn xuất.** Trước đây cạnh dựng một lần trong effect khoá theo
topology, và comment ngay tại đó ghi *"goToStep chỉ đổi cursor nên effect này
không chạy lại theo bước"* — tức 3D vẽ y hệt ở mọi bước. Nay trụ cạnh được giữ
theo khoá cạnh trong `SceneHandles`, effect theo bước chỉ ánh xạ status → màu.
3D không có nét đứt như SVG nên kênh tín hiệu thứ hai là **độ mờ**.

Mỗi trạng thái mang **ít nhất hai kênh** (DESIGN_BRIEF §3.5): màu + độ dày, cộng
nét đứt / độ mờ.

## 3. Inspector hiện dần (§13) và audit toàn bề mặt (§14)

Inspector `graph_traversal` in **toàn bộ** `visitedOrder` và `path` vô điều kiện
— tức ở bước 1/8. Module anh em `tree.traversal` đã sửa đúng lỗi này ở M17-VR1
và có comment ghi lại; ở đây bị bỏ quên. Đúng hình dạng `ARCHITECTURE_MAP §8`
anti-pattern #10.

Thay vì sửa một chỗ, khoá thành **bất biến toàn bề mặt**
(`simulations/inspector-exposure.test.tsx`): với mọi mô phỏng **có** dòng thời
gian, panel Quan sát ở bước đầu **không được giống hệt** bước cuối. Giống hệt
nghĩa là nó không đọc `cursor`. Kèm hai luật vệ sinh: không inspector nào rò
`simulation_id` hay chuỗi `(engine)`.

> **Một phát hiện về chính guard này — tìm ra bằng tiêm lỗi, không bằng đọc
> code.** Bản đầu chỉ dựa vào `offlineCatalog()`, mà danh mục đó phủ 13/22
> target và **không có mẫu cho `network.graph_traversal`** — đúng target audit
> được viết ra để canh. Test "ca gốc" có dòng `if (!s) return` nên nó **bỏ qua
> im lặng** và guard xanh giả. Đã bổ sung fixture tường minh và assert rằng
> audit **thật sự nhìn thấy** target đó.

**Chứng minh đỏ được**: khôi phục bản inspector trước bản vá (`671778e~1`) làm
**3 test đỏ** — bắt đúng cả "inspector mù bước" lẫn "lộ đáp án". Khôi phục lại
thì xanh.

## 4. Độ phủ đánh giá — reconciliation trước, patch sau (§16)

Inventory **runtime** từ `POOLS` (không phải `grep`):

| | |
|---|---|
| Pool | 6 · **118 item duy nhất** |
| Target có ca tường minh **trước** | **19/22** |
| Item không khai `expect_simulation_id` | **22 — tất cả `group="unsupported"`** |

22 item đó là ca **từ chối cố ý** (phản ứng hoá học, đạo hàm, quỹ đạo hành tinh,
"thuật toán em tự nghĩ ra"), không phải lỗ độ phủ.

Ba target thiếu đúng bằng `CM-1` của W4B-0. Đã thêm ba ca — **hai pool khác
nhau, có chủ đích**:

| Ca | Pool | Vì sao pool đó |
|---|---|---|
| `cur-t11-selection-sort` | `curriculum` | neo T11CS.CD6 |
| `cur-t11-graph-traversal-bfs` | `curriculum` | neo T12.CD2 |
| `cap-base-conversion-hex` | **`capability`** | **không neo SGK** — xem §5 |

### Ràng buộc CLI đã khoá luôn trong test

`--case` lọc **sau** `--suite`, và suite mặc định `smoke` không chọn ca nào ở hai
pool này. Lệnh đúng: `--dataset <pool> --suite full --case <id>`. Chứng minh
**offline, 0 API call**, bằng chính code path của `live.py` — vì `live.py` từ
chối chạy khi thiếu `ALLOW_LIVE_AI` nên không thể dùng CLI để chứng minh
selection mà không tiêu quota.

## 5. Mâu thuẫn capability ↔ curriculum, và cách giải (§5 quyết định)

`binary.base_conversion` ship ở M17 W1, khai `ai_reachable`, schema nhận cơ số
**{2, 8, 10, 16}**. Nhưng dataset có **ba ca kỳ vọng TỪ CHỐI** đúng những đề đó
(`m15-hex-gap`, `m15-octal-gap`, `m16-nm-hex-gap`), với lý do trộn **hai lập
luận khác hẳn nhau**: *"ngoài neo SGK"* (chính sách) và *"không target nào sở
hữu"* (năng lực). Lập luận thứ hai đã hết đúng.

**Policy chốt — hai trục tách rời** (`COVERAGE.md §4b`):

| Trục | Giá trị |
|---|---|
| CAPABILITY | `ENGINE_SUPPORTED` · `AI_REACHABLE` · `UNSUPPORTED` |
| CURRICULUM | `ANCHORED` · `PARTIAL` · `NOT_ANCHORED` |

`binary.base_conversion` = **ENGINE_SUPPORTED + AI_REACHABLE + NOT_ANCHORED**.
Trạng thái đó **không** sinh ra tuyên bố phủ chương trình.

- Bằng chứng lịch sử **giữ nguyên, không viết lại** — nhãn hiện hành là
  `STALE_BY_CURRENT_CAPABILITY_POLICY`.
- **Hệ quả đã biết**: ba ca đó sẽ **fail dưới policy hiện hành** khi chạy live.
  Đó là **delta có chủ ý, không phải hồi quy** — ghi ở đây để lượt live sau
  không tưởng là lỗi mới.
- `m16-cr-positional-fail` (**cơ số 5**) vẫn là ca từ chối **hợp lệ** vì 5 không
  thuộc hợp đồng, và có test riêng sẽ đỏ nếu ai nới hợp đồng mà quên xét lại nó.

## 6. Tuyên bố — và ranh giới của nó

✅ **"22/22 catalog target có ca đánh giá tường minh, chọn được trực tiếp bằng
runner hiện có."**

Ngay sau đó, bắt buộc:

> Điều này **không** có nghĩa cả 22 target đã được đánh giá bằng mô hình thật.

**Cấm** nói: *"22/22 curriculum-supported"* · *"22/22 đã đo live"* · *"baseline
M16 đã sai"* (M16 phản ánh policy lịch sử; HEAD phản ánh policy hiện hành).

`LEARNER_IMPACT_NOT_EVALUATED` và `CURRICULUM_SUPPORT_PARTIAL` **giữ nguyên**.

## 7. Giới hạn

- **BEFORE của `packet_routing` chưa chụp trên bố cục mới.** Chỉ `graph_traversal`
  có cặp trước–sau đầy đủ (`before/graph_traversal` ↔ `after/graph_traversal`).
  Artifact W4B-0 có ảnh cũ nhưng ở bố cục **trước** Phase I nên không so trực
  tiếp được.
- Bằng chứng trình duyệt là **hình học + ảnh**, không phải đánh giá thẩm mỹ.
  Ảnh minh hoạ; JSON chịu trách nhiệm chấm.
- Audit inspector là **điều kiện cần**: nó bắt lớp lỗi "inspector mù bước",
  không chứng minh mọi inspector đều hiện dần **đúng mức**.
- Hành vi "đề hex sẽ định tuyến tới `base_conversion`" hiện là **kỳ vọng**, chưa
  phải hành vi đã đo — cần một lượt live có ngân sách.
