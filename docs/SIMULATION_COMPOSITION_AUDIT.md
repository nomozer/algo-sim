# W4B-2T — AUDIT BỐ CỤC MÔ PHỎNG (22 TARGET)

Baseline `2d37784`. Đo bằng `frontend/scripts/measure-composition.mjs` trong
Chrome thật; dữ liệu thô: `docs/evaluation/m17/w4b2t-composition/measure.json`
(TRƯỚC) và `measure-after.json` (SAU).

## 0. Quy trình đã dùng (§0)

**Đính chính tiền đề:** `.impeccable/` chỉ chứa `config.local.json` (consent) +
`hook.cache.json`; `.superpowers/` chỉ chứa **hiện vật của các lượt chạy trước**
(brief/report SDD, HTML brainstorm). **Không thư mục nào chứa định nghĩa skill.**
Định nghĩa thật nằm ở `.claude/skills/impeccable/SKILL.md` (v4.0.4) — đã đọc.

Thứ tự thực tế: **ĐO trước, critique sau**. Lý do: `critique` chấm theo ảnh, mà
câu hỏi của wave này ("khoảng trống có phục vụ cơ chế không?") cần **số**, không
cần điểm thẩm mỹ. Đo xong mới biết chỗ nào là lỗi, chỗ nào là thiết kế đúng.

## 1. Tỉ lệ dùng KHÔNG phải điểm chất lượng

Đây là kết luận quan trọng nhất và nó **bác bỏ** cách đọc đơn giản "hUse thấp =
hỏng":

- `binary.decimal_to_binary` **17%** — ca DISCONFIRMING mà §7 chỉ đích danh.
  Bốn bit gom cụm ở giữa là ĐÚNG; kéo giãn ra toàn màn sẽ phá quan hệ trọng số
  vị trí. **Không đụng.**
- 8 target mảng **36–60%** — `ArrayView` ĐÃ thích ứng từ W4B-2A
  (`arrayChartLayout(n, available)` có `MAX_COL_W`). Con số thấp vì cột **chạm
  trần có chủ đích**, không vì bố cục cứng. §16 cấm mở lại hình học W4B-2A.
  **Không đụng.**
- `network.packet_routing` **37.6%** — khác hẳn: `layout2d` trả **hằng số 610px**
  bất kể sân khấu rộng bao nhiêu. Đây mới là lỗi thật.

Phân biệt: **thích ứng rồi chạm trần** (đúng) ≠ **không thích ứng** (sai).

## 2. Hai phát hiện có CHỦ SỞ HỮU CHUNG

### A. `INFORMATION_DUPLICATION` — 8/22 target, một chủ sở hữu

Ở bước cuối, `.result-banner` và khe thuyết minh in **cùng một câu**:

| | trước |
|---|---|
| 4 bài | trùng **từng ký tự** (`linear_search`, `binary_search`, `bubble_sort`, `insertion_sort`) |
| 4 bài | chỉ khác tiền tố `"Duyệt hết dãy. "` (`find_max`, `find_min`, `sum_if`, `count_if`) |

Đúng ví dụ §9 nêu. Chủ sở hữu: `algorithm/index.ts::narrate`. Và file đó **đã có
sẵn luật này** cho một ca khác — *"DỮ KIỆN QUYẾT ĐỊNH CHỈ THUỘC MỘT CHỖ"*, trả
`null` khi vùng hành động đã sở hữu dữ kiện. W4B-2T chỉ **áp cùng luật cho bước
cuối**: dải kết quả sở hữu câu kết, thuyết minh giữ phần TIẾN TRÌNH
(`processLeadOf`), không còn gì thì trả `null`.

Engine không đổi một ký tự — `step.narration` và `getExplainContext` nguyên vẹn.

### B. `UNDERUTILIZED_STAGE` — 1 target, do bố cục cứng

`layout2d` nay nhận `available` và suy khoảng cách cột, **kẹp `[150, 240]`** —
đúng khuôn `arrayChartLayout` mà họ mảng đã dùng từ W4B-2A. Kẹp trên là bắt buộc:
không có nó thì 4 nút trải trên 3000px thành bốn hòn đảo, "dùng hết sân khấu" mà
quan hệ nối kết loãng ra (§7 *"không làm thiết bị to lố"*).

## 3. Ma trận 22 target

`RUN` = có mẫu offline nên đo được trong Chrome.

| # | target | họ | RUN | hUse trước→sau | dải | phân loại chính |
|---|---|---|---|---|---|---|
| 1 | `algorithm.find_max` | quét | ✓ | 48 → 48 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 2 | `algorithm.find_min` | quét | ✓ | 42.2 → 42.2 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 3 | `algorithm.sum_if` | quét | ✓ | 53.9 → 53.9 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 4 | `algorithm.count_if` | quét | ✓ | 59.7 → 59.7 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 5 | `algorithm.linear_search` | tìm | ✓ | 48 → 48 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 6 | `algorithm.binary_search` | tìm | ✓ | 59.7 → 59.7 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 7 | `algorithm.bubble_sort` | sắp | ✓ | 42.2 → 42.2 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 8 | `algorithm.insertion_sort` | sắp | ✓ | 36.3 → 36.3 | 3 | `INFORMATION_DUPLICATION` → **đã sửa** |
| 9 | `algorithm.selection_sort` | sắp | — | — | — | `INFORMATION_DUPLICATION` → **đã sửa** (cùng chủ sở hữu; khoá bằng test toàn họ) |
| 10 | `algorithm.scan` | quét | — | — | — | `COMPOSITION_GOOD` (suy: dùng chung `ArrayView` đã thích ứng) |
| 11 | `algorithm.bounded_control_flow` | luồng | — | — | — | `COMPOSITION_GOOD` (mã giả + biến, không phải sân khấu hình học) |
| 12 | `binary.decimal_to_binary` | nhị phân | ✓ | 17 → 17 | 1 | **`COMPOSITION_GOOD` — ca DISCONFIRMING, cố ý giữ gọn** |
| 13 | `binary.base_conversion` | nhị phân | — | — | — | `COMPOSITION_GOOD` (chuỗi phép chia là danh sách) |
| 14 | `binary.character_encoding` | nhị phân | — | — | — | `COMPOSITION_GOOD` |
| 15 | `logic.and_gate` | logic | ✓ | 28.4 → 28.4 | 1 | `COMPOSITION_GOOD` — mạch nhỏ, luồng vào→cổng→ra liên tục |
| 16 | `logic.boolean_dag` | logic | — | — | — | `COMPOSITION_GOOD` (DAG + bảng cổng) |
| 17 | `tree.traversal` | cấu trúc | — | — | — | `COMPOSITION_GOOD` — cây CẦN khoảng thở (§8) |
| 18 | `network.graph_traversal` | cấu trúc | — | — | — | `RESPONSIVE_COMPOSITION_GAP` (chưa đo được — không có mẫu offline) |
| 19 | **`network.packet_routing`** | mạng | ✓ | **37.6 → 54.3** | 3 | **`UNDERUTILIZED_STAGE` → đã sửa** |
| 20 | `network.protocol_encapsulation` | mạng | ✓ | n/a | 2 | `COMPOSITION_GOOD` — hộp bao `null` là **giới hạn phép đo** (dựng bằng `div`), không phải lỗi |
| 21 | `database.relational_table_query` | bảng | — | — | — | `COMPOSITION_GOOD` (`<table>` thật, tự chiếm bề ngang) |
| 22 | `generic.rule_scene` | generic | ✓ | 37 → 37 | 0 | `RELATIONSHIP_GAP` — **CHƯA SỬA**, xem §5 |

## 4. Kết quả đo được

| chỉ số | trước | sau |
|---|---|---|
| target trùng nghĩa ở bước cuối | **8** | **0** |
| `packet_routing` mức dùng bề ngang | 37.6% | **54.3%** |
| `decimal_to_binary` (ca disconfirming) | 17% | **17%** — giữ nguyên |
| họ mảng | 36–60% | **không đổi** — đúng chủ ý |

## 5. CHƯA SỬA: `generic.rule_scene` `RELATIONSHIP_GAP`

Ví dụ AND trong generic có A, B, Output như ba widget rời — quan hệ "A AND B →
output" không do sân khấu chở. **Không sửa ở wave này**, và lý do là ranh giới
kiến trúc chứ không phải hết giờ:

- Sửa đúng cách đòi **biểu diễn đã validate phải sở hữu quan hệ/cạnh**. Phải xác
  định trước: DSL hiện có mang nổi quan hệ đó không?
- Nếu chưa mang được thì đây là **khoảng trống biểu diễn của DSL**, phải sửa ở
  manifest/validator — tức đụng hợp đồng, không phải đụng CSS.
- §7 cấm rõ: không rẽ theo `title.includes("AND")`, không biến `rule_scene`
  thành renderer logic viết tay thứ hai.

Vẽ một wire nối ba widget mà không có dữ liệu quan hệ đã validate **chính là
renderer bịa quan hệ** — thứ `SIMULATION_VS_ILLUSTRATION_CONTRACT` cấm.

## 6. Tiêm lỗi (§14)

| lỗi | kết quả |
|---|---|
| C — khôi phục trùng nghĩa ở bước cuối | **ĐỎ** (2 test) |
| D — thu vai trò mạng về hình chung | **ĐỎ** |
| A — khôi phục bố cục pixel cứng | **ĐỎ** *(sau khi bổ sung guard — xem dưới)* |

**Tiêm lỗi A lần đầu KHÔNG có test nào đỏ.** Bố cục thích ứng chỉ được phép đo
trình duyệt bảo vệ, mà phép đo không chạy trong CI. Đã bổ sung
`composition-w4b2t.test.ts` (hàm thuần, 5 ca: nới theo bề rộng · kẹp trên · kẹp
dưới · bề rộng 0 · không nút mồ côi) rồi tiêm lại ⇒ ĐỎ.

B (tách trạng thái khỏi đối tượng) và E (xoá cạnh quan hệ) **không áp dụng**: B
đã được `observation-preservation.test.tsx` giữ từ W4B-2V; E cần `rule_scene` sở
hữu quan hệ, mà §5 vừa nói là chưa.

## 7. Không đụng sự thật

`narrate` là **tầng trình bày**. `step.narration`, `trace`, `predict.check`,
`getExplainContext` không đổi một ký tự. `layout2d` là bố cục renderer
(M7.FREEZE) — không có toạ độ nào vào engine state.

## 8. Còn lại

- `generic.rule_scene` `RELATIONSHIP_GAP` (§5) — cần quyết định hợp đồng DSL.
- `graph_traversal`, `tree.traversal`, `database`, `scan`, `bounded_control_flow`,
  `base_conversion`, `character_encoding`, `selection_sort` **chưa có mẫu offline**
  ⇒ chưa đo được trong trình duyệt; phân loại ở §3 là **suy từ mã**, đã ghi rõ.
- Hộp bao của encap 2D không đo được (dựng bằng `div`) — giới hạn phép đo.
