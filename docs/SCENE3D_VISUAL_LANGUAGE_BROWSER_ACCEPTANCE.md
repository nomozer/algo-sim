# SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE

> Khôi phục cổng trình duyệt và đo sản phẩm thật cho commit `7f34286`.
> Wave **ĐO** — không sửa renderer, không sửa camera.
>
> ```
> BROWSER_EVIDENCE  = ESTABLISHED       VISUAL_ACCEPTANCE = FAIL (ba lý do, §5)
> BASELINE 3/3 PASS · CANDIDATE 3/3 PASS · phép tiêm 8/8 bị bắt
> CANDIDATE 96a9368b… không đổi · CACHE_VERSION 95 không đổi · backend 0 byte
> ```

## 1. Vì sao cổng cũ không lập được nền — nguyên nhân, không phải triệu chứng

Wave trước ghi `spot-check-demo` 4/12 trên mã sửa và **6/12 trên mã chưa sửa**,
nền tài liệu 12/12, cùng một triệu chứng `xuong=false canvas=0`.

Nguyên nhân định vị được: `spot-check-demo.mjs` nạp cảnh bằng

```js
await import('/src/state/store.ts')
```

— đường **chỉ tồn tại trên Vite dev**. Nó buộc mọi lượt đo phải chạy qua dev
server, tức qua đúng transport mà `FINAL_SYSTEM_REPRODUCIBILITY` đã đo là chập
chờn (**dev kẹt 2/15 phiên · bản dựng 0/15**). `browser-runner.mjs` có cùng phụ
thuộc ở cuối `open()`.

Cổng mới chạy trên `dist/` phục vụ tĩnh và vào bằng `window.__ALGO_SIM_STORE__`
— thứ `main.tsx` **đã** phơi ra ở cả hai chế độ. Không sửa một dòng mã sản phẩm.
`browser-runner.mjs` nhận thêm cờ `napModuleDev` (mặc định `true`, mười script
chứng nhận cũ không đổi hành vi).

**Kết quả: baseline `7f34286^` 3/3 PASS, candidate `7f34286` 3/3 PASS.** Nền lập
lại được ⇒ lỗi hạ tầng đã tách khỏi lỗi sản phẩm.

## 2. Ba lỗi CỦA CHÍNH CỔNG, bị bắt trong lúc dựng

Ghi lại vì mỗi lỗi đều từng cho ra một kết quả xanh sai.

**① Cổng PASS 7/7 trên cảnh RỖNG.** `loadEnvelope` đặt cảnh ở **bước 0** — chỉ
có các điểm tự do. Lượt chạy đầu báo PASS trên bảy tấm ảnh chỉ có năm chấm đen
và năm cái nhãn. Sửa: hợp đồng sẵn sàng thêm `EXPECTED_STEP_VISIBLE` (tua tới
bước cuối, đòi *"Bước n/n"*) và **ngưỡng mực** ≥ 1,2 % điểm ảnh.

**② `store.toEnd()` là NO-OP trên tuyến hình học.** Tuyến này đi thẳng vào
`Scene3DExplorer`, không qua registry, nên bước nằm trong state tương tác của
explorer chứ không ở timeline của store; `withTimeline` thấy `mod.timeline`
rỗng và im lặng không làm gì. Cảnh đứng ở *"Bước 1/13"* mà cổng tưởng đã tua.
Sửa: bấm đúng nút **"Bước sau"** của người học.

**③ Server tĩnh của cổng che mất chunk mất.** Nó fallback `index.html` cho MỌI
đường, nên một `.js` bị xoá vẫn trả HTTP 200 — phép tiêm ② **lọt**, cổng báo
PASS trên một bản dựng không tải nổi mã. Sửa: fallback chỉ áp cho đường không
có phần mở rộng.

## 3. Bộ đo bề dày — và hai lần nó tự nói dối

Đo trên **điểm ảnh của ảnh chụp canvas**, không đọc `linewidth` trong mã (WebGL
bỏ qua `linewidth`, nên giá trị trong mã không nói gì về màn hình).

Hai bản đầu đều sai và bị chính số liệu bác:

- **Phân loại theo màu tuyệt đối** vỡ trên ảnh thật: mặt khối tô 0,07 và nền
  thiết diện tô 0,14 nằm đúng trên đoạn nền→màu nét, nên bộ đo nhặt cả mảng tô.
  Cùng một ảnh cho ra trung vị **0,09 px** và max **45 px**.
- **Lọc theo lõi 0,55** giết đúng ca cần phát hiện: nét 1 px khử răng cưa, xấu
  nhất, cho hai điểm ảnh 0,50 ⇒ **0 mẫu**. Ngưỡng phải dưới 0,5.
- **Nhãn điểm là DOM đè lên canvas**, chữ `#171717` gần trùng cạnh thấy
  `#1F1F1F` ⇒ bộ đo trả về **15,3 px** = độ dày thân chữ. (Thử ẩn nhãn bằng CSS
  thì canvas WebGL trắng trơn — bộ đo tự phá thứ nó đo. Nên chuyển sang **vùng
  loại trừ**, không đụng trang.)

Bản dùng cuối cùng: **tích phân mực trên nền cục bộ**. Tự kiểm trên nét tổng hợp:

| nét thật | 2,2 | 2,8 | 3,5 | 5,0 | 1,6 | 1,0 |
|---|---|---|---|---|---|---|
| đo được | 2,20 | **2,80** | 3,50 | 5,00 | 2,0 | 2,0 |

⚠️ **Bão hoà ở ~2,0 với nét ≤1,6 px.** Nên số `2,0–2,7` nghĩa là *"không quá
1,6 px"*, và **không bao giờ nhầm được với 2,8 px** — đủ để trả lời câu hỏi của
wave, không đủ để nói nét dày đúng bao nhiêu.

## 4. Số đo trên sản phẩm thật

`VISIBLE_EDGE_TARGET = 2,8 px` · `HIDDEN_EDGE_TARGET = 1,6 px` · `SECTION_TARGET = 3,5 px`

| ca | trung vị (px) | p25 | p75 | mẫu |
|---|---|---|---|---|
| p1 | 2,40 | **1,46** | 4,34 | 502 |
| p2 | 2,71 | **1,46** | 3,94 | 318 |
| p3 | 2,50 | **1,46** | 3,76 | 173 |
| p4 | 2,71 | **1,46** | 3,76 | 182 |
| p5 | 2,70 | **1,46** | 3,69 | 182 |
| p6 | 2,50 | **1,46** | 3,76 | 176 |
| p7 | 2,70 | **1,46** | 3,63 | 181 |

`SAMPLE_COUNT` 173–502 · `DPR = 1` · viewport 1440×900 · canvas 1318×545.

**Phân vị 25 % nằm đúng 1,46 px ở CẢ BẢY ca**, và trung vị rơi ngay tại mức bão
hoà của phép đo. Bằng chứng thô, đọc thẳng từ một hàng điểm ảnh cắt ngang cạnh:

```
253 253 215 148 216 216 216
        └─ một điểm ảnh tối, một điểm ảnh chuyển tiếp
```

Không phép đo nào biến profile ấy thành 2,8 px.

```
VISIBLE_EDGE_WIDTH_PX = ≈1,5 (p25 1,46 · trung vị chạm trần bão hoà 2,0–2,7)
HIDDEN_EDGE_WIDTH_PX  = NOT_MEASURED — không tách được khỏi nền tô cùng tông
SECTION_EDGE_WIDTH_PX = 2,92 (chỉ p1; sáu ca còn lại 0 mẫu — xem §5②)
```

## 5. VISUAL_ACCEPTANCE = FAIL — ba lý do, không phải một

Chỉ thị §9 dự kiến một lý do. Ảnh sản phẩm cho thấy **ba**, và hai cái sau nặng
hơn cái đầu.

### ① `FAIL_VISIBLE_EDGE_WIDTH` — đúng như dự kiến

Cạnh khối vẽ bằng `THREE.Line`; WebGL bỏ qua `linewidth` ⇒ mọi cạnh dày 1 px.
Đây là nợ `EDGE_WIDTH_IN_PIXELS` đã khai ở wave trước, nay **đo được**.

### ② `FAIL_HIGHLIGHT_OVERRIDES_ROLE_COLOR` — chưa từng được nêu

Vật thuộc nhóm `target` được vẽ với `mau = MAU.highlight`, và màu ấy **đè lên
toàn bộ bảng vai**. Hệ quả đọc thẳng trên ảnh:

- `p3` thiết diện tròn vẽ **màu xanh**, không phải đỏ cam;
- `p6`/`p7` elip thiết diện vẽ **màu xanh**;
- `p4`/`p5` cả khối trụ/nón tô **xanh, độ đục 0,24** thay vì xám 0,07;
- `p1` điểm `S` và đường `BD` cũng xanh.

Bảng màu theo vai vì thế **không tới được người học** ở đúng những ca nó quan
trọng nhất. Đây là lý do sáu trong bảy ca đo được **0 mẫu** cho màu thiết diện:
thiết diện ở đó không mang màu thiết diện.

### ③ `FAIL_CURVED_SOLID_HAS_NO_LINEWORK` — chưa từng được nêu

`p4` và `p5` render ra **một khối đặc, không một nét viền nào**: không vành đáy,
không đường sinh bao, không phân biệt thấy/khuất. Nhánh `curved_solid` chỉ dựng
một mesh (`CylinderGeometry`/`ConeGeometry`/`SphereGeometry`) và **không** gọi
`duongHaiLuot` như nhánh đa diện. Ngôn ngữ hình học đã duyệt — vành gần nét
liền, vành xa nét đứt, đường sinh bao — **không tồn tại** cho khối cong.

## 6. Những gì ĐÃ đạt

| tiêu chí | kết quả |
|---|---|
| z-up đúng | ✅ khối chóp đứng, trụ/nón dựng thẳng — camera đã ăn trong sản phẩm |
| clipping | ✅ 0/7 ca |
| nhãn ngoài khung | ✅ 0 |
| nhãn chồng | ✅ 0 |
| console error | ✅ 0 mọi lượt |
| uncaught exception | ✅ 0 |
| xoay cập nhật cảnh | ✅ p1/p6/p7: ảnh đổi sau khi kéo chuột, khung không phẳng |
| responsive 390×844 | ✅ 3/3 dựng được (mực 23–36 %) |
| T/E/C, OK/OS | ⚠️ **NOT_VERIFIED_ON_PIXELS** — nhãn có trong DOM, chưa soát trên ảnh |

⚠️ Một quan sát phụ ở mobile: canvas rộng **439 px** trong viewport **390 px** —
tràn ngang. Chưa điều tra, ghi lại để không mất.

## 7. Phép tiêm — 8/8 bị bắt

| # | tiêm | mong | thực |
|---|---|---|---|
| ① | dist thuộc commit khác | `STALE_BUILD` | ✅ |
| ② | entry chunk mất | `ENTRY_CHUNK_UNREACHABLE` | ✅ (sau khi sửa lỗi fallback, §2③) |
| ③ | `#root` rỗng | `ROOT_EMPTY` | ✅ |
| ④ | canvas bị gỡ khỏi DOM | `CANVAS_MISSING` | ✅ |
| ⑤ | cảnh dừng ở bước đầu | mực < 1,2 % | ✅ đo 0,89 % |
| ⑥ | khung WebGL phẳng | `phang = true` | ✅ |
| ⑦ | envelope sai mô phỏng | `WRONG_FIXTURE` | ✅ |
| ⑧ | oracle bề dày | phân biệt 2,8 với 1 px | ✅ 2,80 vs 2,00 |

`BUILD_FAILED` tách khỏi `ASSERTION_FAILED`: cái đầu chặn trước khi mở Chrome.

## 8. Artifact

`docs/evaluation/geometry/scene3d-visual-language-browser-acceptance/`

`BASELINE_RUNS.json` · `CANDIDATE_RUNS.json` · `ROTATED_RUNS.json` ·
`RESPONSIVE_RUNS.json` · `READINESS_DIAGNOSTICS.json` ·
`PIXEL_WIDTH_MEASUREMENTS.json` · `FAULT_INJECTIONS.json` · `SCREENSHOTS.json` ·
`CONTACT_SHEET.png` · `screenshots/` (31 ảnh).

`DEMO_SPOT_CHECK.json` và mọi artifact lịch sử **không bị chạm**.

## 9. Phạm vi giữ nguyên

Cơ chế hidden-line động hai lượt của sản phẩm (`LessEqualDepth` /
`GreaterDepth`, cập nhật sau xoay) **không đụng tới**. Möller–Trumbore của bộ
mockup **không** chuyển vào renderer.

```
NEXT_ACTION = SCENE3D_WIDELINE_DEPTH_PASS_IMPLEMENTATION
```

⚠️ Wave ấy phải xử **cả ba** lỗi ở §5, không chỉ bề dày nét. Lỗi ② rẻ nhất và
có lẽ nặng nhất về mặt đọc hình: nó chỉ là quyết định *"highlight tô đè màu vai
hay chỉ thêm một kênh nhấn"*.
