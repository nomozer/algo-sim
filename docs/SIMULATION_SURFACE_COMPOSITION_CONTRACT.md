# HỢP ĐỒNG BỀ MẶT MÔ PHỎNG (W4B-2U2A)

Tài liệu **hợp đồng** — định nghĩa từ vựng bề mặt học sinh và ranh giới trách
nhiệm. Số liệu sống ở `docs/W4B2U2A_SIMULATION_SURFACE_AUDIT.md`.
Nguồn có thẩm quyền cho bất biến: `docs/ARCHITECTURE_MAP.md §5`.

## 1. Bốn chế độ — mỗi chế độ MỘT việc

### OBSERVE — mặc định
Xem state và chuyển tiếp của mô hình tất định.

Được có: `play` · `pause` · `step` · `reset` · `speed` · `timeline`.

**KHÔNG được đòi học sinh trả lời bất cứ gì để đi tiếp.**

Đây là luật đã đúng và đã khoá (`observe-lifecycle-w4b2r.test.ts`): `nextStep`
không đọc `prediction`, `playing` chỉ bật qua `setPlaying`.

### EXPLORE
Học sinh đổi **đầu vào / state / cấu hình** có nghĩa; **engine tất định** kiểm
định hoặc tính lại hệ quả.

Ví dụ đang có: bấm bit (`decimal_to_binary`) · bấm công tắc (`and_gate`,
`boolean_dag`, `rule_scene`) · ngắt/nối liên kết (`packet_routing`) ·
`whatif_swap` sinh nhánh (9 bài thuật toán).

**Phép thử:** đổi React state cục bộ rồi tô màu **KHÔNG** phải EXPLORE. Phải đi
qua `module.apply` → engine → state/trace mới.

### EXPLAIN
Chữ sâu: diễn giải đề, biến, mã giả, lý thuyết. **Đóng mặc định.**

**Không được dùng EXPLAIN để bù cho một sân khấu yếu.** Phép thử: đóng EXPLAIN,
học sinh vẫn phải nhận ra *có gì · cái gì đang hoạt động · vừa đổi gì · quan hệ
nào đáng kể*.

### CHALLENGE — tuỳ chọn
Học sinh dự đoán/cam kết, `predict.check` chấm.

- **Phải tách khỏi OBSERVE.** Không được là bề mặt mặc định.
- **Không** chặn playback.
- Năng lực `predict` **không được xoá** — nó là bất biến #11 (chỉ rule tất định
  mới phán đúng/sai).

## 2. Bề mặt

| tên | nghĩa |
|---|---|
| **STAGE** | biểu diễn chính của mô hình. Vùng trội. |
| **STEP CAPTION** | **nhiều nhất MỘT** câu ngắn bổ trợ cho trạng thái/chuyển tiếp đang thấy. |
| **SIMULATION TERMINAL RESULT** | kết quả do ENGINE sinh (`"Phần tử lớn nhất là 9"`). **Không phải** lời khen/chê. |
| **CHALLENGE FEEDBACK** | phán quyết cho câu trả lời của học sinh (`"Chính xác"` / `"Chưa đúng"`). |
| **DIRECT MANIPULATION** | thao tác xảy ra **trên chính đối tượng/quan hệ** được mô phỏng. |
| **INLINE CONTEXTUAL TOOL** | control nhỏ **kề bên** đối tượng nó tác động. |
| **DETACHED PANEL** | vùng riêng, **không** gắn không gian với đối tượng. Mặc định là mùi lỗi. |

**Luật phân biệt hai loại kết quả** — đây là chỗ sản phẩm hay đọc thành hỏi-đáp:

> KẾT QUẢ MÔ PHỎNG là **đầu ra của engine**; PHẢN HỒI THỬ THÁCH là **phán quyết
> về học sinh**. Hai thứ khác loại thì **không được dùng chung ngữ pháp thị
> giác** (cùng sắc xanh "đúng rồi", cùng dấu ✓). Phân biệt bằng **quyền sở
> hữu**, không bằng so chuỗi.

## 3. Một dữ kiện — một chủ sở hữu

Cùng một sự thật **không được** hiện ở hai bề mặt. Tiền lệ đã sửa:

- W4B-2T: bước cuối, `.result-banner` **sở hữu** câu kết; khe thuyết minh chỉ
  giữ vế tiến trình (`processLeadOf`). Trước đó 8/8 bài in hai lần.
- W4B-2V: vùng cam kết **không** mang dữ kiện quan sát; cổng gác **quyền hành
  động**, không gác **thông tin**.

## 4. Vòng đời — theo CƠ CHẾ, không theo họ

| loại | nghĩa | target |
|---|---|---|
| **TRACE_FIRST** | giá trị sư phạm đầu tiên là **xem** một tiến trình tất định | 17 |
| **EXPLORATION_FIRST** | giá trị đầu tiên đến từ **đổi state** trực tiếp | 4 — `and_gate`, `boolean_dag`, `decimal_to_binary`, `rule_scene` |
| **HYBRID** | cả hai đều cốt lõi | 1 — `packet_routing` |

**Luật nạp:** mô phỏng theo trace nạp xong ở **READY/PAUSED**, học sinh tự chọn
Play hoặc Step. **Không tự chạy.** (Đã đúng, đã khoá.)

**KHÔNG có khoá `BASELINE_OBSERVED`.** Quyết định đã chốt ở W4B-2I và giữ
nguyên: cổng Thí nghiệm do học sinh tự mở và khả dụng **từ bước 1** — vốn đã là
tập cha của "mở sau baseline". Thêm ràng buộc chỉ **lấy đi quyền**. Mô hình
EXPLORATION_FIRST càng không được khoá: bấm công tắc là cách hiểu nó.

## 5. Mức tương tác

| mức | điều kiện |
|---|---|
| L0 / L1 | hình tĩnh / hoạt hình định sẵn — **không được admit** |
| **L2** | trace tất định + play/pause/step |
| **L3** | học sinh đổi state/hành động có nghĩa → engine kiểm định/tính lại |
| **L4** | đổi tham số **lặp đi lặp lại** tự do, không cổng quiz |

Hai luật đếm mức, cả hai đều dễ đếm sai:

1. **Nút play KHÔNG nâng lên L3.** Playback là L2.
2. **`predict` KHÔNG nâng lên L3.** Nó nộp câu trả lời *về* state kế tiếp; nó
   không đổi mô hình. L3 đòi `module.apply` đổi state thật.

Hiện tại: **L2 = 8 · L3 = 10 · L4 = 4.** Không phải mọi target đều cần lên L4.

## 6. Công khai vs nội bộ

| | |
|---|---|
| **PUBLIC_SURFACE** | vào được qua `publicCatalog()` → `LibraryView` |
| **INTERNAL_FIXTURE** | hiện vật dev/parity, `visibility: "internal_fixture"` |

**Luật phương pháp:** mọi khẳng định về UX học sinh **phải nói đo trên bề mặt
nào**. Đo một fixture nội bộ rồi kết luận "học sinh thấy màn này" là sai — lỗi
đã mắc hai lần (audit W4B-2T và bản yêu cầu W4B-2U đều dùng `gen-and`, một
fixture parity, làm bằng chứng UX học sinh).

Fixture nội bộ **vẫn phải đúng về renderer**, chỉ không được dùng làm bằng chứng
sản phẩm.

## 7. Ranh giới không đổi

LLM: **chỉ** đề xuất spec ứng viên có ràng buộc ở biên đầu vào.
Validator/catalog: khoanh năng lực, fail-closed.
Engine tất định: **sở hữu** state · transition · trace · result · phán quyết
`predict.check`.
Renderer: **chỉ đọc**; không tính kết quả, không bịa quan hệ chưa được khai.

Tuyên bố giữ nguyên: `LEARNER_IMPACT_NOT_EVALUATED` ·
`CURRICULUM_SUPPORT_PARTIAL`.

---

# PHỤ LỤC A — HỢP ĐỒNG NGHIỆM THU U2-B (ĐÓNG BĂNG)

Chủ sở hữu chung phải sửa: **`components/SimulationWorkspace.tsx`** (nơi dựng
`PredictionBar`, dòng ~217) + **`components/PredictionBar.tsx`**.
Blast radius: **11 target khai `predict`** (10 kiểm được bằng trình duyệt).

U2-B ĐẠT khi:

1. Mô phỏng theo trace nạp xong ở **PAUSED**. *(đã đúng — giữ)*
2. Play/step chạy trọn baseline **không có `PredictionBar` trong Quan sát**.
3. Năng lực `predict` **còn nguyên** ở CHALLENGE, nơi kiến trúc cho phép.
4. CHALLENGE **không** chặn Quan sát.
5. **KẾT QUẢ MÔ PHỎNG tách khỏi PHẢN HỒI THỬ THÁCH** — khác chủ sở hữu, khác
   ngữ pháp thị giác.
6. **Không xoá** hành vi `predict.check` nào của engine.
7. Test challenge hiện có được **sửa cho khớp**, không bị xoá.
8. Phủ **cả 11** target qua chủ sở hữu chung.
9. **Không** rẽ nhánh theo tên bài/chuỗi ngữ cảnh.

⚠️ **Sắc thái U2-B không được đọc sai:** `PredictionBar` **chưa từng chặn**
playback (`return null` khi `busy`; `nextStep` không đọc `prediction`). Việc
phải sửa là **sự hiện diện thường trực trong Quan sát**, không phải gỡ một cái
chốt — chốt đó không tồn tại. Viết test theo kiểu "gỡ chốt" sẽ **xanh sẵn** và
chứng minh sai.

Tiêm lỗi bắt buộc: khôi phục `PredictionBar` vào Quan sát ⇒ test **ĐỎ**.

---

# PHỤ LỤC B — BACKLOG U2-C (ĐÓNG BĂNG, ƯU TIÊN)

### P0 — `count_if` / `sum_if`: chiếu biến tích luỹ lên sân khấu
- **Lỗi:** TRANSITION là `TEXT_ONLY`; bộ đếm/tổng sống ở vùng hành động, không
  ở sân khấu. Khoảng trống ngữ pháp **duy nhất** còn lại.
- **Chủ sở hữu:** `ScanInteractionModel` (`decision.ts`) + `ArrayView`.
- **Blast radius:** 2 target *(nhỏ — nhưng là khiếm khuyết ngữ pháp thật cuối cùng)*.
- **Rủi ro:** có thể cần đổi hợp đồng model, không chỉ bố cục. **Quyết định
  trước khi code.**

### P1 — `#dcebfa` → một token ngữ nghĩa
- **Lỗi:** trôi token đã xác nhận; **không có** token đúng đang tồn tại.
- **Chủ sở hữu:** `styles/tokens.css` (thêm ĐÚNG MỘT token, vd `--col-idle`).
- **Blast radius:** 1 file + `ArrayView`. **Không** mở dọn token toàn hệ.

### P2 — mẫu offline cho `selection_sort`
- **Lỗi:** khai `predict` nhưng không kiểm được bằng trình duyệt ở mọi wave.
- **Chủ sở hữu:** `data/samples.ts`.

### P2 — harness đo bố cục hiểu sân khấu dựng bằng `div`
- **Lỗi:** `protocol_encapsulation` trả hộp bao `null`.
- **Chủ sở hữu:** `scripts/measure-composition.mjs`.

### NO_CHANGE — chốt lại để thôi mở lại
- **Bố cục họ mảng** (36–60%): thích ứng rồi **chạm trần** có chủ ý (W4B-2A).
- **`decimal_to_binary`** (17%): **ca phản chứng**, kéo giãn phá quan hệ trọng số.
- **Transition SVG `y`/`height`**: `HOOK_FALSE_POSITIVE_FOR_SVG_GEOMETRY`.
- **Chính sách 2D/3D**: 21/0/1, không mở lại nếu không có bằng chứng cơ chế mới.
- **Hình trừu tượng của mảng/cây/đồ thị**: ĐÚNG — thay bằng tranh vẽ sẽ làm hỏng.

**U2-C KHÔNG được biến thành đợt vẽ lại 22 màn bằng tay.** Mọi mục trên đều nêu
đích danh chủ sở hữu chung; mục nào không nêu được thì chưa đủ chín để làm.
