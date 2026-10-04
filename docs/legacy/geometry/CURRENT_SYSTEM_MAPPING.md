# CURRENT SYSTEM MAPPING — giữ / sửa / bỏ

> Số dòng đo bằng `wc -l`, đã trừ file test. Ba nhãn:
> **GIỮ** (không đụng hoặc đổi chuỗi) · **SỬA** (khung giữ, nội dung thay) ·
> **BỎ** (nghỉ hưu, hoặc giữ làm bằng chứng đa miền chứ không phát triển tiếp).

---

## Backend — `backend/app/` ≈ 27.000 dòng

| Thư mục | Dòng | Nhãn | Lý do |
|---|---:|---|---|
| `ai/` | 2.186 | **GIỮ** ~85 % | `pipeline`, `gemini`, `telemetry`, budget, retry — độc lập miền. Chỉ **viết lại `skills/*.md`** |
| `simulation/semantic_program/` | 4.752 | **SỬA** | Khung đúng: `contract`/`validator`/`interpreter`/`route`/`coverage_gate`/`postconditions`/`pacer`/`visual_adapter`. Thay **từ vựng** (kiểu, biểu thức, nghĩa vụ), giữ **ngữ pháp** |
| `evaluation/` | 6.777 | **GIỮ** ~90 % | Máy đánh giá độc lập miền. Chỉ đổi corpus |
| `validation/` | 1.694 | **GIỮ** ~70 % | Tầng 2 chung; phần khoá schema từng miền phải thay |
| `accounts/` | 1.090 | **GIỮ** 100 % | Lớp học, không liên quan miền |
| `persistence/` | 324 | **GIỮ** 100 % | |
| `ingestion/` | 171 | **GIỮ** 100 % | Đọc text/docx/ảnh — hình học **cần ảnh hơn** Tin học (đề kèm hình vẽ) |
| `simulation/` (catalog, gate, coverage…) | 7.734 | **BỎ** ~70 % | 24 `SimSpec` + neo chương trình Tin học. Giữ `execution_authority_gate`, `error_codes`, `scope_gate` |
| `simulation/dsl/` | 1.970 | **BỎ** | Manifest DSL của `generic.rule_scene` — cảnh khai báo tĩnh, không dùng cho hình học |
| `simulation/families/` | 340 | **BỎ** | Selector họ thuật toán |

**Backend giữ được ~60 % theo dòng.**

---

## Frontend — `frontend/src/` ≈ 27.600 dòng

| Thư mục | Dòng | Nhãn | Lý do |
|---|---:|---|---|
| `components/` | 4.401 | **GIỮ** ~85 % | Vỏ ứng dụng, transport, panel giải thích, `SessionCard`, vệ sinh UI |
| `core/` | 2.525 | **GIỮ** ~80 % | Engine chung, timeline, thuật toán nền |
| `state/` | 1.096 | **GIỮ** 100 % | Store, `loadEnvelope`, lịch sử, lớp học |
| `simulations/` (registry, types, renderer) | 1.742 | **GIỮ** ~90 % | Hợp đồng `SimulationModule` **dùng lại nguyên** — kể cả cho kéo-thả |
| `llm/` | 209 | **GIỮ** | |
| `simulations/domains/semantic/` | 521 | **SỬA** | Điểm bám của route sinh; `Workspace` thay bằng cảnh 3D |
| `data/` | 1.073 | **SỬA** | Catalog offline + sample — thay nội dung sang bài hình học |
| `domains/generic/` | 5.354 | **BỎ** ~85 % | Renderer cảnh khai báo DSL |
| `domains/algorithm/` | 2.777 | **BỎ** | |
| `domains/network/` | 2.563 | **BỎ**, trừ `encap-ui3d.tsx` (363) → **THAM CHIẾU** | Tiền lệ Three.js + `meaning_of_z` duy nhất |
| `domains/binary/` | 1.543 | **BỎ** | |
| `domains/logic/` | 1.055 | **BỎ** | |
| `domains/database/` · `web/` · `tree/` · `color/` | 2.793 | **BỎ** | |

**Frontend giữ được ~45 % theo dòng** — thấp hơn backend vì domain frontend
chiếm 16.606 dòng, gần như bỏ hết.

---

## Harness & tài liệu

| Thành phần | Nhãn |
|---|---|
| `scripts/run_sealed_evaluation.py` · `replay_harness` · `reliability_v2` · `merge_render_v` · `freeze_evaluation_candidate` · `classify_run1_failures` | **GIỮ ~95 %** — độc lập miền |
| `custodian/*` (rubric, seed, ground truth) | **GIỮ quy trình**, thay corpus |
| `RELIABILITY_EVALUATION_PLAN.md` · `RUN2_PROTOCOL.md` | **GIỮ** — luật đo, luật claim, luật mẫu nhỏ |
| `COVERAGE.md` | **SỬA** — rubric giữ, neo SGK **Toán 11/12** |
| `docs/evaluation/**` lượt #1 | **GIỮ NGUYÊN, KHÔNG SỬA** — bằng chứng đông cứng của miền cũ |

---

## Hai con số, và con số thứ hai mới quan trọng

| Cách đếm | Giữ |
|---|---|
| Theo **dòng mã** | **~50 %** |
| Theo **phần khó nhất** — kiến trúc R0, máy đánh giá, kỷ luật claim, hạ tầng test | **~85 %** |

Đếm theo dòng đánh giá thấp giá trị còn lại: 16.606 dòng domain frontend bị bỏ
là phần **dễ viết lại nhất**; 6.777 dòng `evaluation/` được giữ là phần **mất
nhiều tuần nhất và hầu như không luận văn cùng loại nào có**.

---

## Ánh xạ khái niệm cũ → mới

| Tin học | Hình học |
|---|---|
| `array`, `stack`, `graph` | `point3`, `line3`, `plane3`, `solid` |
| `array_strip`, `stack_view` | `solid_view`, `plane_patch`, `section_fill` |
| `extremum`, `membership` | `incidence`, `perpendicular`, `distance_value` |
| bước quét mảng | bước **dựng hình** |
| `prescribed_procedure` (thao tác thuật toán) | thao tác **dựng** (tìm giao tuyến, kéo dài, nối) |
| oracle = cài lại thuật toán ⇒ **khó, đã phải loại `predicate_verdict`** | oracle = **giải tích Oxyz** ⇒ **dễ hơn hẳn, chính xác** |

Dòng cuối là **điểm sáng thật của việc đổi miền**: hình học có đáp án đóng
bằng Python thuần, nên oracle độc lập **mạnh hơn** miền cũ.
