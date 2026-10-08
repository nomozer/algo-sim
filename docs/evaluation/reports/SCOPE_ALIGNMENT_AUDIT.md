# SCOPE_ALIGNMENT_AUDIT — gỡ mã Tin học khỏi tuyến đang chạy

> `FINAL_THESIS_SCOPE_ALIGNMENT`, 2026-09-01. **0 lượt gọi model.**
> Audit theo `§1`, và **kết quả audit chặn phần xoá** — lý do ở `§3`.
> Bộ đo: `backend/scripts/audit_domain_graph.py` (đọc import/registry/test,
> **không** đọc tên thư mục).

## 1. Bảng phân loại domain (frontend)

| domain | phân loại | file | đăng ký | dùng bởi mã sản phẩm | dùng bởi test |
|---|---|---|---|---|---|
| `geometry` | **GEOMETRY_CORE** | 17 | · | 3 | 2 |
| `semantic` | **GEOMETRY_CORE** | 4 | ✔ | 1 | 0 |
| `algorithm` | LEGACY_ACTIVE | 19 | ✔ | 5 | 17 |
| `binary` | LEGACY_ACTIVE | 11 | ✔ | 1 | 5 |
| `color` | LEGACY_ACTIVE | 4 | ✔ | 1 | 0 |
| `database` | LEGACY_ACTIVE | 5 | ✔ | 1 | 0 |
| `generic` | LEGACY_ACTIVE | 24 | ✔ | 2 | 2 |
| `logic` | LEGACY_ACTIVE | 6 | ✔ | 1 | 7 |
| `network` | LEGACY_ACTIVE | 20 | ✔ | 1 | 8 |
| `tree` | LEGACY_ACTIVE | 4 | ✔ | 2 | 0 |
| `web` | LEGACY_ACTIVE | 10 | ✔ | 1 | 0 |

Hai điều bảng này nói mà tên thư mục không nói:

- **`geometry` KHÔNG nằm trong registry**, và đó là đúng: mặt 3D không đi qua
  registry. `SimulationWorkspace` gắn `Scene3DExplorer` thẳng khi envelope mang
  một `scene3d` hợp lệ. `semantic` mới là thứ đăng ký `generic.semantic_program`
  — `simulation_id` mà **mọi** envelope hình học mang.
- Phần lớn domain Tin học "active" **chỉ vì chính registry đăng ký chúng**. Gỡ
  dòng đăng ký là chúng thành `LEGACY_UNUSED`. Ba cạnh thật cần gỡ trước:
  `learner-gate → generic/model` · `renderer-fit → tree/layout-size` · bốn
  component UI (`ArrayView`, `ScanActionZone`, `SearchStateView`,
  `SortActionZone`) → `algorithm/decision`.

`geometry` và `semantic` **không nhập một dòng nào** từ chín domain kia. Hạ tầng
chung mà chúng nhập chỉ có: `components/icons.tsx`, `state/classroom-sync.ts`,
`simulations/registry.ts`, `simulations/types.ts`.

## 2. Backend

`app/simulation/semantic_program/` — tuyến hình học — **cố ý tách khỏi danh mục
Tin học**, và tài liệu trong mã nói thẳng điều đó: `analyze_contract.py` *"TÁCH
HẲN khỏi từ vựng catalog"*, `obligations.py` *"không khoá vào catalog"*,
`pipeline_adapter.py` *"KHÔNG đi qua `dsl/validator.py`"*. `route.py` không nhập
gì từ `catalog`/`dsl`.

Ràng buộc nằm ở **một chỗ duy nhất**: `app/ai/pipeline.py` (1805 dòng).

## 3. ⛔ Vì sao phần XOÁ bị chặn — hai lý do, cả hai kiểm được

### 3a. Tuyến hình học là một nhánh SHADOW bên trong pipeline Tin học

`run_pipeline` gọi **`stage_analyze` (Tin học) TRƯỚC**, rồi mới chạy
`_semantic_shadow`, rồi `stage_classify`. Nghĩa là một đề hình học đi qua sản
phẩm vẫn tiêu một lượt `analyze` Tin học trước. Cổng phạm vi của chính tuyến
hình học (`check_scope_and_simulatability`) đọc enum của `analyze.md` Tin học và
có một khối miễn trừ được ghi chú kỹ cho hình học.

⇒ Bỏ `CATALOG`/`dsl` **không phải một phép xoá**, nó là **viết lại bộ điều phối
sản phẩm** — chính thứ `§17` cấm (*"scope cleanup, không phải refactor
project"*). Và mọi cổng bị thay là một thay đổi hành vi của **hệ đang được đo**,
chỉ xác nhận được bằng lượt gọi thật — `§12` cấm.

### 3b. Danh mục bài mẫu offline là 100% Tin học

`frontend/src/data/samples.ts` + `offline-catalog.ts` chứa **13 bài mẫu, không
bài hình học nào**. Đó là đường DUY NHẤT chạy giao diện không cần backend và
không cần API key.

⇒ Xoá miền Tin học **làm thư viện sản phẩm rỗng**. Tạo bài mẫu hình học là công
việc MỚI mà wave này không cho phép (`§17` — không thêm capability).

### 3c. Đã thử thật, và đã hoàn nguyên

Không suy đoán: phần xoá **đã được thực hiện** rồi đo fallout rồi hoàn nguyên.

| đo được | |
|---|---|
| test frontend hỏng ngay sau khi xoá 9 domain | **30 file** |
| test backend chạm `catalog`/`dsl` | **73/249 file** |
| cross-lock chặn đứng | `capability-descriptors.test.ts` khoá **target backend ↔ module frontend là SONG ÁNH 1:1** |

Cross-lock ấy là mấu chốt: xoá module frontend mà giữ 24 target backend làm nó
ĐỎ, và cách duy nhất để nó xanh trở lại là **hoặc** xoá cả hai phía **hoặc** nới
chính cái khoá. Nới một guard để một phép xoá đi lọt là đúng thứ kho này cấm.

⇒ Hai phía **phải đi cùng một wave**, và wave ấy là refactor, không phải cleanup.

## 4. Điều wave này ĐÃ hoàn thành

- **README viết lại toàn bộ** cho đề hình học 3D (`§10`) — 12 mục, không chỉ
  thêm disclaimer. Danh sách năng lực là năng lực **đang hoạt động thật**.
- **Bảng audit trên** (`§1`) — điều kiện tiên quyết của mọi lượt xoá về sau, và
  nó chứng minh chính xác cái gì an toàn, cái gì không.
- Bằng chứng lịch sử **không đổi**; điểm số **không hồi tố**.

## 5. Kế hoạch xoá — thứ tự bắt buộc

Làm sai thứ tự là kho ĐỎ giữa chừng.

1. **Tạo bài mẫu hình học offline** (≥3 bài) để thư viện không rỗng khi mẫu Tin
   học ra đi. Đây là chặn cứng, và là việc nội dung chứ không phải việc xoá.
2. **Tách tuyến hình học khỏi `run_pipeline`**: một đường vào riêng
   `đề → geometry_analyze → tổng hợp → route`, không đi qua `stage_analyze`/
   `stage_classify`. Cổng phạm vi thay bằng phép kiểm tất định của chính miền.
3. **FAIL CLOSED** cho miền không phải hình học ở đường vào sản phẩm (`§5`) —
   chỉ làm được sau bước 2, vì trước đó nó chính là đường Tin học.
4. Xoá `CATALOG` + `dsl/` + prompt Tin học + 73 test đi kèm; sinh lại descriptor
   và schema.
5. Xoá 9 domain frontend + 30 test + 4 component UI + `renderer-fit` +
   `learner-gate`; trích tối thiểu phần dùng chung nếu còn ai cần.
6. Chạy lại: demo replay 5/5 · crash surface 6/6 · suite · build · smoke.
7. Đóng băng lại evaluation candidate.

Bước 2 và 3 **đổi hành vi hệ đang được đo**. Sau chúng, mọi số live cũ chỉ còn
giá trị lịch sử, và cần một lượt xác nhận live mới — thứ `§12` của wave này cấm,
nên nó thuộc về một wave có ngân sách riêng.
