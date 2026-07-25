# RULES.md — Luật cứng + AGENT BOOTSTRAP + SCOPE GUARD

**Đây là tài liệu agent đọc ĐẦU TIÊN.** Nó giữ ba vai trò canonical: *agent
bootstrap* (§1–§2), *scope guard* (§3), và *luật cứng* (§4). Tài liệu được Git
quản lý — nó là **nguồn có thẩm quyền**; `CLAUDE.md` (bị gitignore) chỉ là con
trỏ local.

Bản thiết kế gốc v0.3 đã được lưu trữ tại `docs/legacy/RULES_v0.3.md` (tài liệu
lịch sử — mô tả các kiến trúc chưa/không xây như tầng sandbox chạy code hay
kịch bản vẽ do AI sinh; **không dùng cho quyết định implementation**).

## 1. Thứ tự đọc bắt buộc trước mọi thay đổi không tầm thường

0. **File này** — bootstrap + phân loại phạm vi.
1. `docs/ARCHITECTURE_MAP.md` — bản đồ kiến trúc, bất biến đánh số, anti-pattern.
2. `docs/CURRENT_STATE.md` — danh tính kho mã, milestone, baseline test, scope freeze.
3. `docs/CORRECTNESS.md` — mô hình đúng đắn canonical ↔ learner.
4. `docs/COVERAGE.md` — nguyên tắc sư phạm, phạm vi phủ, tuyên bố bị cấm.
5. `docs/CODE_INDEX.md` — **cái gì đã tồn tại ở đâu** (chống viết trùng).
6. **Code và test thật.**

> Nếu tài liệu mâu thuẫn với code/test: **CODE/TESTS THẮNG** — sửa tài liệu,
> không bẻ code theo tài liệu. Nếu chỗ sai thuộc *update policy* của
> `CODE_INDEX.md`, sửa luôn; nếu không, báo là stale entry.

**Không được nói "đã đọc" nếu chưa thực sự mở file.**

## 2. PRE-FLIGHT — báo cáo trước khi sửa dòng code đầu tiên

Chạy trước:

```
git branch --show-current
git rev-parse HEAD
git status --short
```

Rồi báo đủ các mục sau. Chỉ **sau** PRE-FLIGHT mới được sửa code:

```
Active branch:
HEAD:
Working tree:
Current milestone:
Task classification:            (CORE / SUPPORTING / DEEP_HARDENING / OUT_OF_SCOPE)
Thesis relevance:
Existing related modules:
Existing functions/classes that may be reused:
Source of truth:
Files expected to change:
Contract/cache/history impact:
Duplicate implementation risk:
Dependency-cycle risk:
Scope-creep risk:
Smallest sufficient implementation:
Explicitly excluded work:
Stop conditions:
```

### 2b. Checklist chống viết trùng (bắt buộc trước khi thêm function/class/module/schema)

1. Search **đúng tên**: `rg -n "<symbol>" backend frontend`.
2. Search **cùng trách nhiệm nhưng khác tên** (từ khoá nghiệp vụ).
3. Search **callers/dependencies** để biết ai đang dùng abstraction sẵn có.
4. Đối chiếu `docs/CODE_INDEX.md`.
5. Liệt kê ít nhất các ứng viên có thể REUSE.

Có thành phần tương đương → **reuse / extend**, không tạo bản song song, không
đổi tên chỉ để đẻ file mới. Chỉ CREATE khi trách nhiệm **thực sự khác**, không
phá single source of truth, hướng phụ thuộc đúng, và **đã giải thích vì sao
abstraction hiện có không phù hợp**.

Post-flight phải ghi: **reused modules · created modules · duplicate check result**.

## 3. SCOPE GUARD — phân loại phạm vi trước mọi task

Tên đề tài (giữ nguyên chính xác):

> **Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán bằng ngôn
> ngữ tự nhiên hỗ trợ dạy học môn Tin học THPT**

### 3a. Phạm vi cốt lõi

1. LLM phân tích bài toán ngôn ngữ tự nhiên.
2. Tạo candidate spec.
3. Validator kiểm định **fail-closed**.
4. Deterministic engine **sở hữu** state, timeline và result.
5. Renderer 2D/3D trình bày **authoritative state**.
6. Hỗ trợ nội dung Tin học THPT và tương tác học tập.
7. Yêu cầu thiếu dữ kiện hoặc ngoài khả năng → **từ chối trung thực**.

### 3b. Bốn loại — mọi task phải được xếp loại

| Loại | Nghĩa | Được làm gì |
|---|---|---|
| **CORE** | tạo/hoàn thiện chức năng trực tiếp của đề tài | **triển khai** |
| **SUPPORTING** | test, refactor, tài liệu, UI tối thiểu để CORE chạy được | **chỉ làm phần nhỏ nhất đủ dùng** |
| **DEEP_HARDENING** | reliability production nâng cao · self-repair nhiều tầng · retry orchestration phức tạp · fingerprint/provenance toàn diện · audit framework quá lớn · vá một prompt hiếm bằng nhiều patch liên tiếp | **DỪNG — xin quyết định** |
| **OUT_OF_SCOPE** | không phục vụ trực tiếp hệ mô phỏng giáo dục | **không triển khai** |

### 3c. Dấu hiệu đã đi quá đề tài

- một capability phụ cần **từ ba patch wave trở lên**;
- thay đổi nhiều tầng chỉ để **một prompt phức tạp** đạt tuyệt đối;
- test/audit/tooling tăng mạnh nhưng **học sinh không có chức năng mới**;
- xây **self-healing LLM orchestration**;
- mở rộng thành interpreter / database / browser engine tổng quát;
- đổi nhiều family chỉ vì **một fixture**;
- thêm observability quy mô production không phục vụ demo/luận văn;
- tiếp tục **sửa model** thay vì giữ *right-or-refuse*;
- thay đổi lớn nhưng **không** tạo chức năng học tập mới và **không** sửa
  correctness blocker.

### 3d. Luật dừng bắt buộc

Task bị xếp **DEEP_HARDENING** hoặc **OUT_OF_SCOPE** → **không sửa code, không mở
patch wave**, và báo đúng bốn mục:

1. phần nào đang đi quá;
2. chức năng cốt lõi **thực sự** cần gì;
3. giải pháp **nhỏ nhất**;
4. limitation **có thể chấp nhận**.

> Tiền lệ: W2B PATCH2/PATCH3 là DEEP_HARDENING đã bị loại khỏi tuyến chính —
> `docs/evaluation/m17/W2B_THESIS_SCOPE_DECISION.md`.

## 4. Các luật cứng bền vững (tóm tắt — nơi thực thi ở ARCHITECTURE_MAP §5)

1. **LLM không bao giờ sở hữu runtime**: không sinh timeline / bước / kết quả.
   LLM chỉ trích xuất ngữ nghĩa, phân loại, điền config được validate.
2. **Engine tất định sở hữu sự thật** — mọi diễn biến từ `init`/`apply`/`timeline`.
3. **Canonical simulation: đúng hoặc `capability_gap`** — không render xấp xỉ
   gây hiểu lầm.
4. **Học sinh được phép sai** — thao tác/dự đoán sai là cơ hội học.
5. **Chỉ rule tất định mới phán đúng/sai** — không có rule → `unsupported_to_verify`;
   LLM không bao giờ là giám khảo.
6. **Renderer không sở hữu sự thật ngữ nghĩa** — chỉ đọc state, phát action;
   bố cục/camera là của renderer, cấm vào engine state.
7. **2D/3D dùng chung module/config/state/timeline** — 3D là renderer,
   không phải domain; không simulation_id "_3d".
8. **Mọi tương tác của người học phải chạm cơ chế ẩn** và sinh hệ quả tất định —
   tương tác trang trí không được admit (COVERAGE §2.6).
9. **Không mở rộng kiểu một-module-một-bài-học** — ưu tiên specialized có sẵn →
   generic DSL → năng lực tái sử dụng → từ chối trung thực.
10. **Test mặc định = 0 API call thật** — live AI là opt-in có ngân sách.
