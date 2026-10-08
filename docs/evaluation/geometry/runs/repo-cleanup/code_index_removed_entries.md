# CODE_INDEX — mục của mã đã gỡ ở run `repo-cleanup`, chép nguyên văn

> Tách khỏi [`docs/CODE_INDEX.md`](../../../../CODE_INDEX.md) ở run `repo-cleanup` (2026-10-08). Nguồn: commit `11bea4a7e5d93df57609ab9731bc58fcc60d430a`
> (blob `5714b7991994d19503851384ffd7ac2c76c5ff8f`). Mỗi khối là một mục `###` mô tả một file đã gỡ (miền Tin học, công cụ đo một lần, test của
> chúng); sha256 tính trên các dòng của khối nối bằng LF. Đây là lịch sử: không sửa. Đường dẫn tương đối trong khối
> viết cho thư mục `docs/`.

<!-- khối 1/59 · dòng 415–419 của bản gốc · sha256 1f02709afc536a5083fd1a296cbdad000dd1b3e243f03acbbd966b905ea24af5 -->
### `ai/explain.py` · Change impact: targeted live
Q&A Socratic trên snapshot state THẬT. Exports: `EXPLAIN_SCHEMA`, `explain_state`.
Notes: **bề mặt hội thoại LLM duy nhất**; không phán đúng/sai, không điều khiển
mô phỏng.

<!-- hết khối 1 -->

<!-- khối 2/59 · dòng 425–441 của bản gốc · sha256 e31deda4455a9638fed49c3ea40bdae5f8b0d1152d7a8c174d00908c528ba423 -->
### `frontend/scripts/after-matrix-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — MA TRẬN AFTER cho **toàn bộ** danh mục: ghép ba nguồn (descriptor sinh
từ registry + module frontend đang chạy qua CDP + `measure-1920.json`). Phân loại
trải nghiệm bằng luật KHAI TRƯỚC ở đầu file; **đếm tổng chỉ sau khi có bảng từng
target**. Tách bạch ĐO ĐƯỢC ↔ CHỈ KHAI BÁO (9/23 target chưa có bài mẫu offline
nên không dựng được state để đo) — cộng hai cột lại là tự cho điểm cao hơn bằng
chứng. Ba phép suy BỊ CẤM ghi ngay trong file: `predict` ⇒ thao tác trực tiếp ·
`timeline` ⇒ mô hình tương tác · có trong catalog ⇒ có phủ chương trình.
Artifact: `docs/evaluation/m17/w4b3a-after/after-matrix.{json,md}`.
Notes (M15 Task 16): `sorting` tốt nghiệp `PILOT` → `SUPPORTED` sau formalize
thành family selector (M14) + conformance proof (M15) — note tự giới hạn claim
(live n=4 M14 + n=2 M15 W1 — đếm case live chạm sorting gồm cả near-miss từ
chối đúng — là **targeted acceptance, KHÔNG phải bằng chứng thống kê**, không
được nói mạnh hơn). `binary_system` note bổ sung control cơ
số ≠ 2 (M15 W1: hex/octal → `capability_gap` có 2 lớp phòng thủ, xem
`mechanism_gate.py`).

<!-- hết khối 2 -->

<!-- khối 3/59 · dòng 451–483 của bản gốc · sha256 d7e7849f28a97600976b452b331f7c16087caf6e68c49ffab657276403c2bdf6 -->
### `frontend/scripts/certify-experience-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi: **ĐÓNG thử thách rồi, học sinh làm được gì có nghĩa trên màn này?** — tầng
thứ ba, khác hai tầng đã có: `interaction-semantics.test.ts` hỏi *module nhận
action gì* (hợp đồng), `certify-viewports-w12.mjs` hỏi *affordance có thấy được
không* (bề mặt).
Phân loại: đổi được đầu vào ⇒ `TOOL_PASS` · không đổi được nhưng tua THAY THẾ ⇒
`TRACE_PASS` · không đổi được và tua chỉ THÊM DỒN ⇒ **`EXPERIENCE_FAIL`**.
⚠️ "Tua thì màn hình đổi" KHÔNG phân biệt được gì — trình chiếu cũng đổi. Nên
phép đo tách **thêm dồn** (bước sau chứa trọn bước trước = bảng in dần từng
dòng, đáp án có sẵn) khỏi **thay thế** (giá trị bị đổi, vùng xét co lại = cơ chế
đang chạy).
⚠️ Ứng viên action sinh từ config, và hình dạng phải ĐỌC `simulations/types.ts`:
đoán `whatif_swap {from,to}` / `toggle {id}` thì action bị **nuốt lặng lẽ** và
`find_max` đọc ra TRACE_PASS trong khi nó là công cụ — đoán sai ở đây luôn đánh
giá THẤP sản phẩm. Hợp đồng thật: `{i,j}` · `{target}` · `{a,b}`.
⚠️ PHÉP ĐO NÀY ĐÃ SAI BỐN LẦN, và **cả bốn lần đều đánh giá THẤP sản phẩm** —
ghi lại để lần sau không lặp:
1. So `st.cursor` (không tồn tại ở tầng store) ⇒ mọi vòng lặp thoát ngay bước
   đầu, báo "1 bước" cho cả 23 target.
2. Đoán hình dạng action (`whatif_swap {from,to}`, `toggle {id}`) ⇒ action bị
   **nuốt lặng lẽ**. Hợp đồng thật ở `simulations/types.ts`: `{i,j}`, `{target}`.
3. Đoán TÊN action theo TÊN field config: `decimal_to_binary` khai
   `decimalValue` nhưng `apply` nhận `set_param {name:'decimal'}` — đọc ra
   `STATIC_ILLUSTRATION` cho một bài mà `narrate` nói thẳng "bấm từng bit".
4. Chỉ đo CHỮ trong `.sim-stage` ⇒ mất hai thứ: dải quan sát
   (`.search-observe` là ANH EM của `.sim-stage`, và chính nó đổi theo bước) và
   MÀU (`ScanWorkspace` chỉ vẽ `ArrayView` — cột nào đang xét mã bằng `fill`).
   Cho ra "13 bước engine, 1 bước màn", một kết luận sai về sản phẩm.
Nay dấu vân = chữ CẢ THẺ (trừ đồ đạc) + `fill`/`class` của mọi phần tử SVG.
Vẫn KHÔNG bắt được vị trí/kích thước — giới hạn, không phải đã phủ.
Số hiện tại: **20 TOOL_PASS · 3 TRACE_PASS · 0 EXPERIENCE_FAIL**. Chênh
engine/màn còn lại (40→14, 33→14…) là trần 14 bước của vòng lặp, không phải lỗi.

<!-- hết khối 3 -->

<!-- khối 4/59 · dòng 484–493 của bản gốc · sha256 b6fa9d8c95d84a9b14cf0d88e59470b16246aeb6fc2745e33f07cf6ac015bceb -->
### `frontend/scripts/faultcheck-visual-weight-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Chứng minh `certify-visual-weight-w12.mjs` **còn đỏ được**. Phép đo ấy đã bị NỚI
ba lần để nhìn thấy `<canvas>`, DOM thật, rồi `.encap-layer` — mỗi lần nới là
một lần dễ xanh hơn, nên con số 23/23 chưa đáng tin cho tới khi có đối chứng.
Ba nhánh: giấu khối cơ chế thật ⇒ **ĐỎ** · phình vỏ rỗng `.encap-2d` ⇒
**KHÔNG được xanh** · nguyên trạng ⇒ **XANH**. Mỗi nhánh chứng minh
`MUTATION_OBSERVED` trước khi phán — phép tiêm không chạm đối tượng thì kết quả
của nó vô nghĩa.
Số hiện tại: **3/3 đúng kì vọng** (nguyên trạng ink 0,39 · 8 chủ sở hữu).

<!-- hết khối 4 -->

<!-- khối 5/59 · dòng 494–512 của bản gốc · sha256 5a180fea51a5bb96bcb65c57f164d909204d0bd4e44feed014d80fef7d634e02 -->
### `frontend/scripts/certify-visual-weight-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi câu mà MỌI tiêu chí W12 khác bỏ sót: **trên sân khấu, HÌNH chiếm bao nhiêu
so với CHỮ?** Các tiêu chí trước chỉ hỏi "đổi đầu vào thì kết quả có tính lại
không" — nên `network.packet_routing` (4 biểu tượng đứng yên + 4 bước chữ) đạt
hết, trong khi mở ra nhìn thì nó là hình minh hoạ có chú thích.
Đo `inkShare` (diện tích svg/canvas/`.web-page` trên diện tích thẻ) và
`proseChars` (chỉ khối văn xuôi; KHÔNG tính nhãn trong hình, KHÔNG tính ô bảng
— bảng LÀ kết quả engine, phạt nó là phạt nhầm). Bài có bảng được miễn ngưỡng
`inkShare`, và điều đó ghi rõ chứ không miễn lặng lẽ.
⚠️ Ngưỡng `MIN_GLYPHS` của bản đầu ĐÃ GỠ vì nó SAI hai đường: đo kích thước dữ
liệu (dãy 3 phần tử có 5 hình chữ nhật) và không nhìn được vào `<canvas>` — nó
vừa gán "tranh tĩnh" cho cảnh 3D thật. `glyphs` còn trong artifact để đọc.
⚠️ Đo BỀ MẶT, không đo hiểu biết — `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.
⚠️ Hai ngoại lệ, cả hai đều KIỂM NGƯỢC được nên không nuốt được luật: bài có
`<table>` (bảng là kết quả engine) và `CODE_IS_THE_MECHANISM`
(`bounded_control_flow` — sân khấu là mã giả có con trỏ dòng, như trình gỡ lỗi;
vẽ thêm hình ở đó là trang trí). Khai "mã là cơ chế" mà lại nhiều hình ⇒ ĐỎ.
Số hiện tại: **23/23 lấy HÌNH làm chính**.

<!-- hết khối 5 -->

<!-- khối 6/59 · dòng 513–527 của bản gốc · sha256 7bcc3a49b7f9b2311340bd513153c64bd95c4c5a03ff85889094ef93ae32daba -->
### `frontend/scripts/certify-scroll-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi: vỏ ứng dụng có đọc thành MỘT khối liền, và máng cuộn có ổn định không?
5 màn × 4 bề rộng trên `browser-runner.mjs`: home · library · history ·
workspace gọn · workspace rất dài — cố ý phủ cả trang KHÔNG cuộn lẫn trang cuộn.
Khẳng định: header trải hết bề rộng vỏ · máng đúng bằng bề rộng thanh cuộn đã
khai (10px) · không tràn ngang · **máng giống nhau giữa trang ngắn và trang
dài** (không nhảy ngang — phép so này mới là câu hỏi thật; đo một màn thì không
bao giờ phát hiện được nhảy).
⚠️ KHÔNG đo được thumb có nhìn thấy hay không: CDP không đọc computed style của
`::-webkit-scrollbar-thumb`. Việc đó do `styles/scrollbar-ownership.test.ts`
khoá ở mức mã nguồn — ranh giới này ghi thẳng vào artifact, không để một con số
trông-như-đã-phủ.
⚠️ KHÔNG đảo quyết định W4B-1A (cuộn thuộc về TÀI LIỆU, không phải panel): vùng
cuộn nội bộ từng giấu 170px nội dung học mà không có tín hiệu ở mức trang.

<!-- hết khối 6 -->

<!-- khối 7/59 · dòng 528–538 của bản gốc · sha256 f92474295fd11e520e479cc6b8bd3cd7e62a8aecf9d8452732566f1091fc64cd -->
### `frontend/src/simulations/action-probe.ts` (M20 W12) · Change impact: offline
NGUỒN DUY NHẤT của câu "học sinh có đường nào đổi đầu vào bài này không".
`candidateActions(config)` dẫn ứng viên từ config đã validate; dùng bởi CẢ
`experience-gate.test.ts` (offline, <1s) lẫn `scripts/certify-experience-w12.mjs`
(trình duyệt, qua `session.mods.probe`).
⚠️ TÊN ACTION KHÔNG SUY ĐƯỢC TỪ TÊN FIELD CONFIG — nó nằm trong `module.apply`.
Đã sai ba lần trong W12 và **cả ba đều đánh giá THẤP sản phẩm**, vì action sai
hình dạng không ném lỗi mà bị `apply` trả về state cũ, đọc y hệt "bài này không
tương tác được": `whatif_swap {from,to}`→`{i,j}` · `toggle {id}`→`{target}` ·
`set_param 'decimalValue'`→`'decimal'`. Thêm target mới thì MỞ MODULE RA ĐỌC.

<!-- hết khối 7 -->

<!-- khối 8/59 · dòng 539–552 của bản gốc · sha256 08e644db09883b9d08f138e938b4dbd742800e1b6cc7478c8e0cdbefc99c4bc0 -->
### `frontend/src/simulations/tool-affordance.ts` (M20 W12) · Change impact: offline
NGUỒN DUY NHẤT của câu hỏi "công cụ thao tác của học sinh có được hiện ra
không". `toolAffordanceOpen({exploreOpen, challengeOpen, busy})` — hàm THUẦN,
kiểm được không cần Chrome. Cả `domains/algorithm/ui.tsx` (kéo cột) và
`domains/network/ui.tsx` (ngắt/nối liên kết) đọc nó.
⚠️ Trước W12 hai miền chép tay CÙNG một luật (`exploreOpen && !busy`), nên công
cụ nằm sau một nút học sinh phải tự biết bấm: đo trên trình duyệt được **52/92**
dòng ma trận bề rộng "không có affordance". Luật nay là W12 §6 Policy B — thử
thách ĐÓNG thì công cụ dùng được; MỞ thì có thể siết để câu hỏi đang chờ không
bị chính học sinh vô hiệu hoá. `mode: "hidden"` của `interaction-policy.ts` vẫn
thắng tuyệt đối (kéo ở `sum_if`/`count_if` là trang trí).
⚠️ Bật affordance KHÔNG nâng hạng ngữ nghĩa: `whatif_swap` vẫn là
INPUT_MANIPULATION (W12 §8) — phân loại thuộc `interaction-semantics.test.ts`.

<!-- hết khối 8 -->

<!-- khối 9/59 · dòng 553–569 của bản gốc · sha256 6081b24c96259f93340a18f70b4051df7c8e90c8155121ea005620c388d8251a -->
### `frontend/scripts/e2e-stack-production.mjs` (vNext) · **TIÊU QUOTA THẬT**

E2E đường NGƯỜI DÙNG: gõ đề vào `.composer-text`, bấm `.composer-send`, chờ HTTP
`/api/analyze` thật, rồi bấm `button[title="Tiến một bước"]`. **Không**
`loadEnvelope`, không fixture, không sample offline — đó là ranh giới với
`capture-stack-vnext.mjs` bên dưới, thứ chỉ là bằng chứng COMPONENT.

Chộp response `/api/analyze` qua `page.on("response")` làm nguồn sự thật cho
"route nào đã phục vụ" (`simulation_id` / `source`), vì UI không hiển thị điều
đó. Kết quả: `docs/evaluation/semantic-vnext/e2e/`.

⚠️ Mỗi lượt là một request phân tích thật (nhiều lượt LLM phía backend) và tiêu
một lượt dùng thử của khách. Cần `SEMANTIC_ROUTE_MODE=serve` ở container thì
route sinh mới chạy. Backend chạy uvicorn KHÔNG reload dù `app/` được bind-mount
⇒ sửa mã Python xong phải `docker compose restart backend`, nếu không đo phải
bản cũ trong bộ nhớ.

<!-- hết khối 9 -->

<!-- khối 10/59 · dòng 570–585 của bản gốc · sha256 c87a5f810f6fad15791d7a777f148f2f0136f0f7945727f5884d1ab742b273de -->
### `frontend/scripts/certify-transport-vnext.mjs` (vNext) · cần dev server + Playwright

Sở hữu tầng bằng chứng **transport qua CONTROL THẬT**: bấm đúng nút "Sau"/"Trước"
trên trang rồi hỏi *màn hình có đổi không*. Ranh giới với `learner-gate.test.ts`:
test đó gọi `mod.timeline` TRỰC TIẾP nên chứng minh hợp đồng ở tầng engine, không
chứng minh nút bấm nối được vào engine — đúng khoảng trống mà sự cố `main.py`
quên `semantic_route` đã phơi ra (mảnh nào cũng xanh mà chưa mảnh nào được ghép).

Dùng **bài mẫu offline** (`data/samples.ts`) nên **0 gọi `/api`, 0 quota, không
inject store** — người dùng chọn bài, bấm nút, trạng thái đổi thật.

Hai điều kiện của anti-pattern #14 đều có: **dấu vân tay trang** (đúng bài + >1
bước, sai thì thoát != 0) và **`--faultcheck`** (chặn sự kiện nút "Sau" ⇒ bản
soát phải TỤT ĐIỂM). Chạy: `node scripts/certify-transport-vnext.mjs --port 3177
[--faultcheck]`.

<!-- hết khối 10 -->

<!-- khối 11/59 · dòng 586–609 của bản gốc · sha256 c3e7b41b188fb4074a923eeb073a552619e026713a5aec82bfb3223680b0a437 -->
### `frontend/scripts/certify-transport-vnext.mjs` (vNext) · cần dev server + Playwright

Sở hữu HAI bản soát trên UI THẬT, **không inject store**: §6 transport (Tiến ·
Lùi · Về đầu · Dựng lại · Tự chạy/Dừng) và §5 rõ ràng thị giác ở ba bề rộng.
Dùng **bài mẫu offline** (`data/samples.ts`) nên 0 API call — người dùng chọn
bài, bấm nút, trạng thái đổi thật. Ba miền: array/quét · tree/duyệt · graph/BFS.

Hai cái bẫy đã cắn và nay ghi lại trong code: nút bước là nút ICON chỉ có
`title` (tìm theo chữ trượt IM LẶNG), và `Tự chạy` **đổi nhãn thành `Dừng`** sau
khi bấm. Nhịp tự chạy đo được ~1 bước/giây, tick đầu ~1,2s — chờ 900ms thì bản
soát vu oan cho sản phẩm.

Đo HÌNH HỌC chứ không so pixel (repo không có `@playwright/test`): chữ SVG nằm
trong khung vẽ · không tràn ngang · không chữ kích thước 0 · nút bước còn bấm
được. `--faultcheck` chặn nút Tiến ở tầng capture để chứng minh guard đỏ được.

**`SUPPORTED_MIN_WIDTH = 320px`**, khoá bằng hai viewport `min-320`/`min-344`
trong chính runner. Trước vNext bố cục tràn ngang dưới ~354px và trang mất dữ
liệu ở mép phải; truy được chuỗi `.control-zone` (nowrap, 252/304px) →
`.player` (229px) → `.panel-controls` → `.app-layout` → `html`. Sửa bằng
`flex-wrap` trên `.control-zone` ở `global.css` — một luật ở tầng dùng chung,
không vá theo ảnh chụp, và không breakpoint nào phải nhớ vì wrap chỉ kích hoạt
khi hết chỗ (màn rộng không đổi một pixel).

<!-- hết khối 11 -->

<!-- khối 12/59 · dòng 610–628 của bản gốc · sha256 dcaeea4ded8583c97f52b53a469dc50cc15b3b97c44cd364fe4d23ea9013e53c -->
### `frontend/scripts/capture-stack-vnext.mjs` (vNext) · cần dev server + Playwright

Bằng chứng trình duyệt cho case Stack `{[()]}`: tiêm envelope thẳng qua
`useAppStore.loadEnvelope`, đặt cursor tới 6 khung mốc, chụp ảnh và trích **phép
chiếu ngữ nghĩa từ DOM** (nội dung `<text>` trong SVG) — không so pixel. Kết quả:
`docs/evaluation/semantic-vnext/browser-evidence/` (`stack-visual-acceptance.json`
· 6 ảnh); báo cáo đi kèm ở `semantic-vnext/reports/STACK_VISUAL_ACCEPTANCE.md`.

Hai điều kiện của anti-pattern #14 đều CÓ THẬT trong script: **dấu vân tay trang**
(khẳng định đúng tiêu đề + 7 bước, sai thì thoát `3`) và **`--faultcheck`** (thay
`push`/`pop` bằng `highlight` ⇒ bản soát phải tụt khỏi 6/6, không tụt thì thoát
`4`). Chế độ tiêm lỗi tái hiện đúng triệu chứng gốc — ngăn xếp rỗng ở mọi khung
trong khi narration vẫn kể push/pop.

⚠️ Bộ trích phải LOẠI chú giải trình bày khỏi danh sách phần tử: lượt chạy đầu
nuốt nhãn `← TOP` vào `stack` và báo FAIL nhầm 4 khung. Chú giải không phải dữ
liệu. ⚠️ Cổng 3000 hay bị chiếm bởi dev server khác đang chạy mã CŨ; dùng
`--port` để dựng server riêng, đừng chụp vào cổng lạ (tiền lệ `0a71268`).

<!-- hết khối 12 -->

<!-- khối 13/59 · dòng 629–640 của bản gốc · sha256 632fa791f330f4da71ccb63e03889c1ce880fdd4189f138e670b6dd712027ed7 -->
### `frontend/scripts/capture-before-after.mjs` (W6) · cần `npm run dev` + Chrome
Chụp CLIP theo `.workspace-card` ở MỘT trạng thái xác định (`--target`,
`--viewport`, `--act`). Ghép với `git checkout <ref> -- <file>` (Vite HMR nạp lại
ngay, không cần dựng lại) thì có cặp TRƯỚC/SAU trên cùng máy, cùng bề rộng, cùng
đề — khác biệt duy nhất là bản vá. Dùng để chứng minh một pha có HẬU QUẢ HỌC SINH
NHÌN THẤY, chứ không chỉ có hợp đồng/test đã đổi.
⚠️ URL module lấy từ `performance.getEntriesByType('resource')`, KHÔNG `import()`
đường trần: Vite băm URL theo phiên nên import trần tạo instance THỨ HAI với store
rỗng. ⚠️ Phải nạp trước bốn module rồi mới dùng — lượt `import()` đầu của module
nặng có thể chưa trả kịp qua CDP, và khi ấy `Runtime.evaluate` trả `undefined`
CHỨ KHÔNG ném. Cả hai đều từng làm script im lặng hỏng.

<!-- hết khối 13 -->

<!-- khối 14/59 · dòng 641–658 của bản gốc · sha256 553b5994ca089179f6d80a3e184e36fb80e7781c756f4e460e76abb36008de3d -->
### `frontend/src/core/predicate.ts` (W5C) · Change impact: offline
CHỦ SỞ HỮU DUY NHẤT của "sáu phép so sánh `> >= < <= == !=` nghĩa là gì".
`compareNumbers(x, op, y)` + `includesBoundary(op)` — hàm THUẦN trên hai SỐ.
⚠️ Trước W5C cùng sáu toán tử được cài BA LẦN: `algorithms.ts::testCondition`
(sum_if/count_if), `scan.ts::opHolds` (algorithm.scan), và nhánh `compare` của
`program.ts` (bounded_control_flow). Ba bản đồng ý nhau vì MAY, không vì có gì
bắt chúng thế — và một lần đổi `>=` thành `>` ở một bản chỉ chấm sai đúng những
học sinh ở NGƯỠNG, tức chỗ bài học nằm ("từ 8,0 trở lên" ≠ "trên 8,0"). Cả ba
nay uỷ quyền xuống đây.
⚠️ `switch` cố ý KHÔNG có `default` — vét cạn để tsc đỏ khi thêm toán tử thứ
bảy. Đó chính là bẫy `program.ts` từng mắc: `default` cũ trả `l >= r`, nên mọi
op không khớp lặng lẽ thành `>=`. Nay op lạ thì NÉM.
⚠️ `program.ts` giữ riêng `==`/`!=`: ở đó hai vế có thể là bool/chuỗi, nên đó là
so sánh đồng nhất chứ không phải so sánh SỐ. Chỉ so sánh THỨ TỰ uỷ quyền xuống.
Khoá bởi `core/predicate-family-w5c.test.ts`: bảng chân trị 6 op × 3 quan hệ
VIẾT TAY (sinh từ code sẽ là test tự xác nhận) + đối chiếu đáp số engine + guard
chống mọc bản cài thứ tư.

<!-- hết khối 14 -->

<!-- khối 15/59 · dòng 659–673 của bản gốc · sha256 28084ee3f301a69c6f241581090f36f291e254f75e7e3e7bbe79a100cb4c8099 -->
### `frontend/src/simulations/color-channels.ts` (W5A) · Change impact: offline
CHỦ SỞ HỮU DUY NHẤT của phép toán BA KÊNH ↔ MỘT MÀU, dùng chung cho
`web.style_model` và `color.rgb_model`. Giữ `Channel`/`CHANNELS`/`CHANNEL_LABEL`/
`CHANNEL_MAX`, mẫu `HEX_COLOR`, `rgbOf`/`hexOf`/`rgbTextOf`/`cssColorOf`,
`isChannelValue`/`clampChannel`, `channelRamp` (vệt màu của thanh trượt) và
`readableInkOn` (chọn màu CHỮ đặt trên ô màu theo luma BT.601).
⚠️ Nâng từ `domains/web/props.ts` trong W5A — trước đó phép toán thuộc sở hữu
của MỘT miền, nên miền thứ hai chỉ có hai lối: import chéo miền (đảo hướng phụ
thuộc) hoặc chép lại (hai bản `hexOf`, và ngày chúng lệch thì hai màn hình nói
hai giá trị khác nhau về cùng một màu).
⚠️ `channelRamp` giữ HAI kênh kia cố định — đó là điều kiện để vệt màu nói thật
về màu sắp nhận được; một vệt đỏ-thuần cố định sẽ nói dối.
⚠️ `clampChannel` dùng ở BIÊN NHẬN (thanh trượt/ô số), KHÔNG dùng để chữa config
sai — kẹp im lặng ở đó biến một đề hỏng thành mô phỏng trông như đúng.

<!-- hết khối 15 -->

<!-- khối 16/59 · dòng 674–683 của bản gốc · sha256 995afa55172c449754a62dbf0372c5522675eb7b23eba45e2190d0ecc7edb5d7 -->
### `frontend/scripts/measure-transport-w7.mjs` (M20 W7) · offline (cần `npm run dev`)
Hỏi: cơ chế to nhỏ khác nhau thì khay điều khiển có đổi bề rộng theo không? Đo
độ LỆCH bề rộng qua nhiều target thay vì so với một con số ma. Đo ở HEAD
104c752: cơ chế lệch 849px, khay lệch **đúng 849px** — bám 1:1; sau W7 khay lệch
**0px**.
⚠️ Đếm HÀNG bằng TÂM DỌC có dung sai, không bằng mép trên: `align-items: center`
khiến ba cụm khác chiều cao có mép trên lệch vài pixel dù cùng một hàng, và bản
đầu vì thế báo 3 hàng cho một dải rõ ràng một hàng. Artifact:
`docs/evaluation/m20/transport-{before,after,catalog,browser}.json`.

<!-- hết khối 16 -->

<!-- khối 17/59 · dòng 919–928 của bản gốc · sha256 cca639dd75c1084d85439cf0d5af2cb90e83894a069c3b7a51bfec6e0ea6a10b -->
### `frontend/scripts/certify-viewports-w12.mjs` (M20 W12-C) · offline (cần `npm run dev`)
23 target × 4 bề rộng = 92 dòng, dùng lại `browser-runner.mjs`. Hỏi câu KHÁC với
`audit-composition.mjs`: **ở bề rộng này học sinh có DÙNG ĐƯỢC target không** —
sân khấu hiện · affordance chính thấy được · thử thách đóng sẵn · tràn/cắt/chồng.
⚠️ Đếm affordance phải gồm CUE CON TRỎ trên SVG: cột `ArrayView` là một `rect`
gắn pointer handler và React gắn listener ở gốc nên không lộ ra DOM. Bản đầu chỉ
tìm `input/button/[tabindex]` và đọc ra 0 affordance cho mọi target thuật toán —
một kết luận sai vì thước đo hẹp.
Artifact: `docs/evaluation/m20/w12-viewport-matrix.json`.

<!-- hết khối 17 -->

<!-- khối 18/59 · dòng 929–940 của bản gốc · sha256 fea720a7c1aa21e52db35a9413e1a88a80df76419bd787f7ddc852431290b469 -->
### `frontend/scripts/quiz-dominance-w12.mjs` (M20 W12-A) · offline (cần `npm run dev`)
Hỏi: khi mở thử thách, CƠ CHẾ còn là khối lớn nhất trên màn hình không? Đo tỉ lệ
`chiều cao khối thử thách / chiều cao sân khấu` — không đo bề rộng, vì cả hai
nằm cùng cột nên bề rộng luôn bằng nhau và phép so sẽ không bao giờ phân biệt
được gì (lỗi "luật không thể sai" đã gặp ở M19).
⚠️ Bản đầu đo ngay ở cursor 0 và chỉ chạm được 2/23 target — `predict.challenge`
trả null ở phần lớn các bước, nên 21 target còn lại bị đọc nhầm thành "không có
thử thách". Nay tiến từng bước tới khi lối vào hiện ra.
Đo được ở HEAD daf9b28: `network.packet_routing` 111px/180px = **0,62** (FAIL).
Sau bản sửa chủ sở hữu chung: 61px/180px = **0,34**, 0 FAIL.
Artifact: `docs/evaluation/m20/w12-quiz-dominance.json`.

<!-- hết khối 18 -->

<!-- khối 19/59 · dòng 941–949 của bản gốc · sha256 03615e8c5ca61191969044dbf9cd3164d29e174003a1d783b88d287b9145da3f -->
### `frontend/scripts/certify-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Chứng nhận tương tác trong trình duyệt THẬT theo luật: hành động → SimAction →
`module.apply` → **state tất định đổi** → hệ quả nhìn thấy trong DOM. Một cú bấm
không đủ, một hoạt hình không đủ, trả lời thử thách không đủ.
⚠️ Phân biệt `CERTIFIED` với `PROBE_UNVERIFIED`: state không đổi có thể là target
không nhận action ấy HOẶC probe chưa đúng từ vựng miền. Gộp hai ca thành "hỏng"
là đổ lỗi cho sản phẩm vì phép đo hẹp — Wave 1 đã ghi rằng bộ thăm dò chung chỉ
là CẬN DƯỚI. Artifact: `docs/evaluation/m20/w12-interaction.json`.

<!-- hết khối 19 -->

<!-- khối 20/59 · dòng 1024–1038 của bản gốc · sha256 862dd61c6b6a170653f3de12b37b786a0048f1abec3d41388984d93b1f63ae4d -->
### `frontend/scripts/certify-sweep-w12.mjs` (M20 W12) · LƯỢT CHỨNG NHẬN · cần Chrome
Chủ sở hữu của bất biến **source-freeze**: chụp `HEAD`/`sourceFingerprint`/cây
bẩn ở HAI đầu lượt, chạy toàn bộ cổng con W12 (`GATES` — 1 DERIVED + 7 BROWSER),
rồi đòi nguồn y nguyên và `uniqueFingerprints === 1`. Vi phạm ⇒
`CERTIFICATION_SWEEP_INVALID`, thoát != 0.

Vì sao cần dù mọi cổng con đã có `provenance()`: `provenanceVerdict` phán MỘT
artifact tại MỘT thời điểm, nên bảy artifact đo trên bảy trạng thái nguồn khác
nhau vẫn qua được từng cổng rồi được cộng thành một tuyên bố COMPLETE về một sản
phẩm chưa từng tồn tại. Đo được điều đó phải nhìn cả LƯỢT. Khoá bởi
`src/certification-sweep.test.ts` (tiêm lỗi từng ca + chặn cổng con rụng im lặng).

Primitive nằm ở `evidence.mjs`: `sweepBegin/sweepEnd/sweepVerdict`,
`crossCheckFreshness`, `SWEEP_FAULTS`.

<!-- hết khối 20 -->

<!-- khối 21/59 · dòng 1039–1051 của bản gốc · sha256 8708853c4e827fc607f4899257dc100fa9efe9bf682cf46c0d0d31d02957eb55 -->
### `frontend/src/core/var-label.ts` (M20 · Product Experience) · offline
`varLabel(name)` / `varPhrase(name, fallback)` — đổi TÊN BIẾN ENGINE sang cụm
tiếng Việt đọc lên được. Bảng chỉ phủ biến do chính engine đặt (`tong`, `dem`,
`max`, `min`, `can_tim`, `gia_tri_chen`, `giua`, `vi_tri_cuc_tri`, `vt`); tên do
ĐẶC TẢ cấp (`seed.varName`, LLM sinh) trả `null` ⇒ bên gọi phải nói bằng khái
niệm, không đoán cách viết có dấu (bỏ dấu là ánh xạ mất thông tin: `tong` có thể
là tổng/tông/tống).

Đóng lỗi thật quét được toàn danh mục: `core/scan.ts` và `core/algorithms.ts`
nội suy thẳng tên biến vào câu thuyết minh, nên `algorithm.scan` đọc ra
**"Khởi tạo nguong = 4."** trên màn học sinh. `ui-hygiene` không bắt được vì nó
soi chuỗi TĨNH trong mã, còn đây là chuỗi nội suy LÚC CHẠY.

<!-- hết khối 21 -->

<!-- khối 22/59 · dòng 1052–1067 của bản gốc · sha256 3aa75d63abcc4670d1866285234f3c25e9e82b445ad56c1275252821f19f96fb -->
### `frontend/src/simulations/svg-affordance.ts` (M20 W12) · offline
`svgAffordance({label,onAct,pressed})` trả PROPS cho một hình SVG bấm được:
`role="button"` + `tabIndex` + `aria-label` + `aria-pressed` + Enter/Space (có
`stopPropagation` vì Space là phím tắt Tự chạy toàn cục) + lớp `.sim-affordance`
(vòng tiêu điểm ở `global.css`).

Vì sao trả props chứ không phải component: chỗ gọi trải vào `<g>`/`<line>`/`<rect>`
có hình học riêng, và bọc thêm một `<g>` sẽ làm lệch phép đo hình học đã chứng
nhận (`audit-composition.mjs`, `certify-visual-weight-w12.mjs`).

Đóng lỗi thật: idiom "`<g>` có `cursor:pointer` + `onClick`" dựng ở 5 chỗ, đúng
ở 2. `logic.and_gate` có 13 phần tử focus được, không cái nào là công tắc A/B.
`network/ui.tsx::LinkHandle` và `logic/dag-module.tsx` là nguồn gốc của khuôn và
KHÔNG bị viết lại (đổi mã đã chứng nhận để cho đối xứng = đánh đổi rủi ro hồi
quy lấy cái đẹp). Khoá bởi `scripts/certify-a11y-w12.mjs`.

<!-- hết khối 22 -->

<!-- khối 23/59 · dòng 1068–1103 của bản gốc · sha256 af010d5957838962cfa33da3e7d24d65106eab2f2a5f10d7fa815f772a7ad89a -->
### `frontend/scripts/certify-a11y-w13.mjs` (M20 W13) · cần Chrome
Giảm chuyển động + tương phản, đo bằng GIÁ TRỊ TÍNH TOÁN sau khi mọi tầng CSS đã
phân giải. Không lặp phép đo của `styles/tokens.test.ts` — vitest dừng ở "luật CÓ
được viết ra", script này đo "trình duyệt CÓ làm theo". Bật/tắt giả lập qua CDP
`Emulation.setEmulatedMedia` (đúng thứ hệ điều hành gửi), đo trước/sau.
⚠️ Tương phản chấm theo CẶP THẬT, không theo bảng màu: leo cây tổ tiên tìm nền
ĐỤC đầu tiên, vì nền thật là kết quả của DOM (thẻ lồng thẻ, nền trong suốt xuyên
xuống) — guard tĩnh chỉ GIẢ ĐỊNH được `--canvas`/`--canvas-soft`. Ngưỡng theo cỡ
chữ đúng WCAG 1.4.3 (≥24px, hoặc ≥18.66px và đậm → 3:1; còn lại 4.5:1); chấm mọi
thứ bằng 4.5 là tự sinh phát hiện giả trên tiêu đề.
⚠️ QUÉT TOÀN DANH MỤC **VÀ ĐI QUA CÁC BƯỚC** — 26 bề mặt (home · library · mọi
target `offlineCatalog()`) × tới 6 bước, 104 bước, 5431 phần tử có chữ. Phạm vi
này lớn dần theo ba lần bị lừa, mỗi lần đều báo CERTIFIED trước khi bị mở rộng:
ba bề mặt bỏ sót 8 lỗi · một-khung-mỗi-target bỏ sót 5 lỗi nữa, vì
`.frontier-tag.is-done`, `.loop-cond-verdict`, `.hold-label`, `.loop-back.is-active`
và nhãn nút mạng **chỉ tồn tại ở TRẠNG THÁI** chứ không ở khung đầu. Bước tới
bằng `nextStep()` (đúng hàm học sinh bấm) và nhận biết hết bước bằng cách so
TRẠNG THÁI ENGINE trước/sau — không đoán tên trường con trỏ, vì con trỏ nằm
trong state của module chứ không ở store.
Bản đầu đo ba bề mặt rồi báo CERTIFIED trong khi **8 lỗi nữa đang tồn tại** ở
những target nó không đi qua
(`.frontier-tag`, `.loop-cond-verdict`, nhãn SVG program-module, huy hiệu bảng):
đúng anti-pattern #13 — guard đặt ở chỗ phụ thuộc route nào tình cờ được ghé.
Một target không nạp được ⇒ `boQua`, và `boQua` khác rỗng thì verdict là RED,
KHÔNG phải "sạch".
⚠️ CHỮ SVG lấy màu từ `fill` chứ không phải `color`, và nền của nó là hình ANH
EM chứ không phải tổ tiên — nên nền dò bằng `elementsFromPoint` tại tâm chữ.
Hai bẫy đã cắn trong lúc dựng: (1) leo cây DOM cho chữ SVG đẻ ra "trắng trên
trắng 1:1"; (2) `elementsFromPoint` trả về CẢ TỔ TIÊN, mà `g`/`svg` có `fill`
mặc định đen ⇒ 8 "nền đen" giả. Nay bỏ tổ tiên và chỉ nhận
rect/circle/ellipse/polygon/path. Phát hiện giả sinh từ chính công cụ đo là
loại nguy hiểm nhất: nó trông y hệt phát hiện thật.
Mục FAULT tự bơm một khối CSS đặt SAU mọi stylesheet — đúng hình dạng lỗi mà
guard tĩnh không thấy: `global.css` vẫn đúng nguyên vẹn, chỉ tầng phân giải cuối
bị luật khác thắng. Artifact: `docs/evaluation/m20/w13-a11y.json`.

<!-- hết khối 23 -->

<!-- khối 24/59 · dòng 1230–1238 của bản gốc · sha256 26d6cacc5f612b56fa43f2cd0be033bd85c9fb200c41d80362503741e4c6e6d7 -->
### `frontend/scripts/certify-a11y-w12.mjs` (M20 W12) · cần Chrome
Khả năng tiếp cận đo bằng PHÍM THẬT qua CDP `Input.dispatchKeyEvent` — sự kiện
tự dựng (`isTrusted:false`) không chứng minh được người dùng bàn phím đi được.
Sáu bề mặt đại diện; mỗi ca đòi đủ chuỗi focus → Enter thật → STATE ĐỔI, cộng
`ACCESSIBLE_NAME` · `VISIBLE_FOCUS` (`outline-style !== none`) ·
`STATE_NOT_COLOR_ONLY` · Escape đóng thử thách + trả tiêu điểm · 768px.
Tiêm lỗi: `A11Y_NAME_REMOVED` · `A11Y_KEYBOARD_PATH_REMOVED` ·
`CHALLENGE_ESCAPE_BROKEN` (thay khối bằng bản sao rời fiber) + CONTROL.

<!-- hết khối 24 -->

<!-- khối 25/59 · dòng 1239–1246 của bản gốc · sha256 aca8e0c77f0640eb4441f68faf905b48889c62bd65873580ae3335a6a55c654f -->
### `frontend/scripts/certify-representation-w12.mjs` (M20 W12) · cần Chrome
Hai câu hỏi một chủ đề: mỗi target bày ĐÚNG MỘT cách xem cho học sinh, và target
còn renderer nội bộ thì hai renderer đọc cùng một sự thật. Sinh bảng 23 dòng
(mode công khai · mode khả dụng · bày cho học sinh · bản nội bộ · vi phạm) +
parity 2D↔3D. Tiêm lỗi `PUBLIC_DUAL_MODE_WITHOUT_POLICY` ·
`RENDERER_PARITY_STATE_DIVERGENCE`.
⚠️ Renderer 3D là chunk NẠP LƯỜI ⇒ nó là object, không phải function.

<!-- hết khối 25 -->

<!-- khối 26/59 · dòng 1247–1255 của bản gốc · sha256 d3f53f011416c66a61a521111cad1e93e9010f61a97a6939d38ede2954977fee -->
### `frontend/scripts/certify-teaching-walkthrough-w12.mjs` (M20 W12) · cần Chrome
Câu hỏi nghiệm thu duy nhất: bỏ thử thách đi, giáo viên còn phơi bày được cơ chế
không? 11 kịch bản, từ vựng action lấy NGUYÊN từ `certify-w12.mjs::PLAN`.
⚠️ Phạm vi đo là `.workspace-card`, KHÔNG phải `.sim-stage` — cơ chế của
`web.style_model` là DOM thật, của ba target cơ số/bảng là `<table>`, của
`protocol_encapsulation` là `.encap-layer`. Tiêm lỗi
`TEACHING_WALKTHROUGH_CHALLENGE_ONLY`.
⚠️ KHÔNG dùng để nói bất cứ điều gì về kết quả học tập.

<!-- hết khối 26 -->

<!-- khối 27/59 · dòng 1256–1263 của bản gốc · sha256 208ef9ced0b23890303917f8d06f55c5cbeb1388dddee1033fa4963f560cd33f -->
### `frontend/scripts/certify-classroom-continuation-w12.mjs` (M20 W12) · cần Chrome + backend
Rời đi rồi quay lại: đăng nhập → mở bài đã giao → thao tác THẬT → ghi tiến độ →
ĐĂNG XUẤT + xoá sạch `localStorage` → đăng nhập lại → tiến độ trở lại. Xoá lưu
trữ là bắt buộc, nếu không phép đo sẽ xanh nhờ LỊCH SỬ CỤC BỘ — cơ chế khác hẳn.
⚠️ `/api/auth/me` trả 200 kèm `user: null` cho khách, KHÔNG trả 401.
⚠️ Cần container backend MỚI (bản cũ không phục vụ `/api/auth/*`) + seed fixture.
Tiêm lỗi `CLASSROOM_PERSISTENCE_REMOVED` · `CLASSROOM_RESTORE_MISMATCH`.

<!-- hết khối 27 -->

<!-- khối 28/59 · dòng 1273–1284 của bản gốc · sha256 1be337a496b969b2a3c4850e89a920196cc42d91d75a5b6f7eb909a2be24a344 -->
### `frontend/scripts/runtime-zero-ai-w7.mjs` (M20 W7 closure) · offline (cần `npm run dev`)
ĐẾM request thật thay vì suy từ cấu trúc mã. Bọc `window.fetch` và `module.init`
của mọi module trong registry, chụp số đếm trước/sau từng hành động. Có PHÉP THỬ
DƯƠNG TÍNH mỗi lượt chạy (gọi fetch một lần có chủ đích) để "delta 0" nghĩa là
"không có gọi", không phải "bộ đếm không gắn được".
Phủ: mở/đóng dòng thời gian · trace theo tham số hiện tại · Đặt lại — mỗi cái
kiểm cả fetch, `init`, và ảnh chụp state.
⚠️ Khẳng định "trace theo tham số mới" phải NỐI với giá trị hiện tại (bước chia
đầu = `decimalValue`, chia cho `targetBase`), không so với hằng số: bản đầu tìm
dấu vết "cơ số 2" nhưng mẫu offline vốn đã là cơ số 16 nên phép tiêm giữ
`state.steps` đi qua sạch 23/23. Artifact: `docs/evaluation/m20/w7-runtime.json`.

<!-- hết khối 28 -->

<!-- khối 29/59 · dòng 1291–1302 của bản gốc · sha256 f54f595496692ba35ef26e01c4c8c3daa484d2b967c89eb97c26b6e3c98a38b0 -->
### `frontend/scripts/measure-tool-first-w5.mjs` (M20 W5) · offline (cần `npm run dev`)
Trả lời câu §7: **ở cursor 0, DOM có hiện đúng đáp án mà engine đang giữ không?**
Đọc đáp án THẲNG từ store rồi tìm nó trong DOM — kiểm renderer có nói đúng thứ
engine giữ (ranh giới R0); tính đúng của bản thân đáp án do oracle độc lập bên
vitest lo.
⚠️ Ba lần phải sửa chính phép đo trước khi tin được, ghi trong file: (1) hàm tua
gọi `st.next()` — API không tồn tại — nên trả 'ok' mà không tua, mọi target đọc
ra "không bị khoá"; (2) chỉ đếm `table td` nên không thấy bề mặt dựng bằng lưới
div — đo THẺ chứ không đo THÔNG TIN; (3) phán bằng hiệu số nội dung khi tua, sai
tiêu chí vì §1 nói diễn giải NÊN hiện dần. Artifact:
`docs/evaluation/m20/tool-first-{before,after-*}.json`.

<!-- hết khối 29 -->

<!-- khối 30/59 · dòng 1303–1309 của bản gốc · sha256 d2744ece8aee46a4790b4f6246f1e359a6526b43c0432d50500c6fca1bce11ec -->
### `evaluation/metamorphic.py` (M20 W2B) · Change impact: offline
7 phép biến hình TẤT ĐỊNH giữ nguyên ngữ nghĩa (đổi tên người/thiết bị, cách nói
tương đương, đổi số, đảo dãy, hai phép khoảng trắng) để đo hệ có đọc CƠ CHẾ hay
chỉ khớp mẫu chữ. Hai ràng buộc dễ phá: `shift_numbers` **giữ nguyên 0 và 1** (ở
đề logic/nhị phân chúng là giá trị bit) và `reverse_sequence` chỉ đụng dãy ≥3 số.
`variants()` loại biến thể trùng bản gốc — giữ lại chỉ làm con số phủ to giả.

<!-- hết khối 30 -->

<!-- khối 31/59 · dòng 1310–1315 của bản gốc · sha256 00a161f7c071cb707f5a8bf4eaa15c3cc9eda6f51e8ed54d879b8578dfad28ec -->
### `evaluation/product_scope.py` (M20 W2C) · Change impact: offline
`ProductScope` + `SCOPE_OVERRIDES` tách ba loại case bị trộn số: nội dung Tin học
CÔNG KHAI (tính vào phủ) · fixture ENGINE nội bộ (chứng minh DSL, KHÔNG tính) ·
case NGOÀI PHẠM VI (chứng minh từ chối trung thực, KHÔNG tính). Mỗi override phải
nói VÌ SAO theo NỘI DUNG; test từ chối lý do kiểu "nó vốn nằm trong pool khác".

<!-- hết khối 31 -->

<!-- khối 32/59 · dòng 1418–1422 của bản gốc · sha256 9b36afd6924928b8642808b745f3548958a15b1a038546854e60c4a95b19ff4c -->
### `evaluation/dataset.py` · Change impact: offline
**Chỉ định nghĩa benchmark** (30 đề, không gọi API). Exports: `EvalItem`, `DATASET`.
`tags`: `smoke` (8 đề), `boundary` (4 đề). Đổi group/expect = đổi ngữ nghĩa
benchmark → cân nhắc kỹ.

<!-- hết khối 32 -->

<!-- khối 33/59 · dòng 1620–1656 của bản gốc · sha256 6b04818615f829dcd9fd6eae4f57eaf3466fd71315d4775c05a836454443fe97 -->
### `scripts/diagnose-responsive.mjs` · Change impact: offline (cần `npm run dev`)
**Chủ sở hữu phép đo responsive** — trục chiều rộng **và chiều cao**, before/after.
W4B-1A mở rộng: viewport tham số hoá (`--viewports 1366x768,1536x864`), checkpoint
timeline (`--checkpoints initial,mid,final`), chế độ quét danh mục
(`--fixture catalog|stress|all`), dấu vân tay trang (sai route → **thoát 2**),
và **acceptance chấm máy có mã thoát** (vi phạm → **thoát 1**): `HORIZONTAL_OVERFLOW`
· `CONTENT_HIDDEN_IN_PANEL` · `CONTROL_OCCLUDED` (elementFromPoint) ·
`CONTROL_OFFSCREEN` · `TEXT_CLIPPED`.

**Bất biến bố cục nó khoá** (hai cái, hai trục):
1. **Chiều cao** — trang phải cuộn được khi nội dung cao hơn viewport; nội dung
   **không** được biến mất vào thanh cuộn nội bộ của `.panel-center`. Lớp lỗi mà
   mọi breakpoint theo chiều RỘNG không bao giờ bắt được (`global.css` khối
   `@media (min-width: 1101px) and (max-height: 900px)`).
2. **Chiều rộng** (W4B-1A.1) — `LAYOUT_NOT_USING_VIEWPORT`: `.app-layout` phải
   dùng gần trọn khung cha, hoặc đạt đúng `max-width` đã khai khi màn rộng hơn.
   Bề rộng mong đợi **dẫn xuất từ `css_max_width` đo được**, không hard-code.
   Lớp lỗi này guard đầu tiên không thấy: năm điều kiện cũ đều hỏi "có tràn / có
   bị giấu", không cái nào hỏi "app có DÙNG màn hình không".

**Cô lập phiên (W4B-1A.1)** — mỗi lượt chạy sở hữu Chrome riêng:
`--remote-debugging-port=0` rồi đọc cổng thật từ `DevToolsActivePort` trong
profile của chính nó; PID/cổng/profile ghi vào `session` của artifact. Dấu vân
tay kiểm **danh tính** (`store.active.moduleId` so với target đang yêu cầu), không
chỉ hình dạng DOM → lệch thì `WRONG_SIMULATION_OR_FIXTURE` + thoát 2. Mọi lối ra
(thành công · exit != 0 · throw · unhandled rejection · SIGINT/SIGTERM) đi qua
`shutdown()`. Cờ `--self-test-throw` tiêm lỗi tái lập được để chứng minh đường
dọn dẹp. **Lý do tồn tại**: cổng cố định 9337 + thiếu teardown từng khiến hai
lượt chạy song song bám chéo và sinh artifact gắn nhãn sai fixture.

Lệnh hồi quy (0 API call, cần dev server):
```bash
cd frontend && node scripts/diagnose-responsive.mjs --port 3000 --fixture all \
  --routes workspace --checkpoints initial,mid,final --viewports 1366x768,1536x864 --out <dir>
```
Bằng chứng + injected-fault proof: `docs/evaluation/m17/w4b1a-responsive/`.

<!-- hết khối 33 -->

<!-- khối 34/59 · dòng 1657–1663 của bản gốc · sha256 303dd9dc1e91577d94cdd1f23330922dcb15866ae1b4988ee2c35519f7797f46 -->
### `scripts/fixtures.mjs` · Change impact: offline
**Bộ fixture DÙNG CHUNG** cho runner Chrome/CDP (dữ liệu thuần, 0 side effect).
Tách khỏi `visual-stress-audit.mjs` ở W4B-1A — script đó nay `import`, dữ liệu
không đổi. Lý do tồn tại: `offlineCatalog()` của app chỉ phủ **13/22** target,
nên bản soát bố cục cần nguồn bù. Thêm fixture ở ĐÂY, không chép sang runner
khác. Cùng `offlineCatalog()` phủ đủ **22/22** target.

<!-- hết khối 34 -->

<!-- khối 35/59 · dòng 1676–1684 của bản gốc · sha256 578d3cf460e3977f041d3077c09962828dd7d2874e23a9cc8ec36d39fcaa6d0a -->
### `core/` (`algorithms.ts`, `trace-builder.ts`, `pseudocode.ts`, `types.ts`) · offline
Engine của domain `algorithm` (ngoài `simulations/` vì có trước registry).
**Không** dùng làm hạ tầng chung cho domain khác. M9-S1: narration ở BƯỚC QUYẾT
ĐỊNH là câu hỏi (không lộ đáp án sớm — hệ quả thuộc bước kế tiếp); phần tử đã
duyệt/không thỏa được mark `eliminated`; export thêm `OP_TEXT`.
`TraceBuilder` (M12) = **substrate thực thi tái dụng** cho MỌI engine trace
(cùng union `TraceEvent`); 8 engine specialized là 8 driver mệnh lệnh ~15 dòng
trên cùng substrate, KHÔNG phải 8 module rời.

<!-- hết khối 35 -->

<!-- khối 36/59 · dòng 1685–1699 của bản gốc · sha256 0452df9b5a2b877b9c42eb764211bc27e6ef82dac518c3f20247256e1687aaa2 -->
### `core/program.ts` (M17 W2C) · offline
**Interpreter luồng điều khiển hữu hạn**, engine-owned — MIRROR của
`program_spec.py` + `validation/program.py`. Exports: `PROGRAM_VERSION`,
`PROGRAM_LIMITS`, kiểu `ProgramSpec`/`ProgramStatement`/`ProgramExpression`/
`ProgramVariable`/`CompletionState`, `validateProgramSpec(raw)`,
`programLines(spec) → {lines, lineOf}`, `renderExpression(spec, id)`,
`runProgram(spec) → {trace, completion, outputs}`.
Interpreter sở hữu TOÀN BỘ: môi trường biến, thứ tự chạy, kết quả điều kiện,
nhánh được chọn, số lượt lặp, biên dừng. **MỘT NGUỒN cho mã giả**: `programLines`
vừa sinh dòng hiển thị vừa trả `lineOf` mà interpreter dùng để gắn `Step.line`
⇒ highlight không thể trôi khỏi câu lệnh đang chạy.
Dùng lại `TraceBuilder`/`Step`/`Snapshot.vars` (không có trace builder thứ hai).
Chạm biên → `completion="limit_reached"` + câu "chưa kết thúc", KHÔNG treo.
Tests: `program.test.ts`. Consumer: `domains/algorithm/program-module.tsx`.

<!-- hết khối 36 -->

<!-- khối 37/59 · dòng 1700–1718 của bản gốc · sha256 31e1b7f2dfb8ad34394ea8e9a1bd3a589c4aaa407c5e24a9ea92fb21587a45af -->
### `core/scan.ts` (M12) · offline
**Declarative Bounded Scan** — MỘT interpreter tất định, engine-owned, cho họ
bài single-pass trên mảng. Exports: `ScanSpec` (+ `ScanSeed/ScanCompare/
ScanUpdate/ScanMarking/ScanStop`), `runScan(spec, whatIf?) → Trace`,
`validateScanSpec(raw) → {ok, spec|error}`, `SCAN_VERSION`.
Interpreter sở hữu **toàn bộ** vòng lặp/tiến chỉ số/biên dừng (≤ n, non-Turing)/
sinh event/gọi `TraceBuilder`; spec chỉ chọn **enum ĐÓNG** (seed/compare/update/
marking/stop) + hằng đầu vào — **KHÔNG** while/guard/mutation/đệ quy/code. Chứng
minh (`scan.test.ts`): parity NGỮ NGHĨA (decisions + finalMarks + stepCount) với
`runAlgorithm` cho find_max/count_if/sum_if/linear_search — cùng interpreter,
spec khác, **0 primitive theo-thuật-toán**. `validateScanSpec` allowlist mọi
trường + coherence "quét trên GIÁ TRỊ phần tử". (M12-AI-SCAN) `scanPseudocode(spec)` — mã giả
5 dòng DẪN XUẤT từ spec; `runScan` gắn `Step.line`/narration từ CÙNG layout
(một nguồn, chống highlight trôi). Đã wire: module `algorithm.scan`
(`domains/algorithm/scan-module.tsx` — module thứ 9 của domain, adapter mỏng,
prediction/what-if HOÃN) + route NL backend (catalog `algorithm.scan`).
Specialized giữ nguyên làm oracle — KHÔNG thay thế. Mirror Python:
`simulation/scan_engine.py`.

<!-- hết khối 37 -->

<!-- khối 38/59 · dòng 1719–1727 của bản gốc · sha256 80209c331355646afdf7ba4b030662da583d37812cb308d9c7d39af6b5e42930 -->
### `scripts/capture-w4b2b-experiment.mjs` · offline (cần Chrome + Vite)
Runner LUỒNG HỌC SINH qua CDP — khác `diagnose-responsive.mjs` (runner ĐO hình
học, không bấm nút). Chứng minh chuỗi: Quan sát không vùng cam kết → mở cổng
BẰNG BÀN PHÍM → cam kết sai/đúng qua `predict.check` → đóng cổng → timeline vẫn
chạy; cộng `JSON.stringify(active.state)` không đổi qua mọi lần bật/tắt trình
bày, và 0 rò rỉ đáp án trong DOM. Cờ: `--port --targets --out`. ⚠️ Chỉ tin kết
quả trên tiến trình Vite MỚI: server đã qua nhiều lượt HMR cho phán quyết sai
(đo được: store `view:"workspace"` mà React vẫn vẽ Home).

<!-- hết khối 38 -->

<!-- khối 39/59 · dòng 1728–1743 của bản gốc · sha256 7a15f59affc1b7df5063cd1bd7b7cbb1b6f171478d3c6731969040f632594aec -->
### `scripts/capture-w4b2i-interaction.mjs` · offline (cần Chrome + Vite)
Runner CDP của W4B-2I, hai chuỗi hành vi trong một lượt: (A) `binary_search` —
Quan sát 0 vùng bấm → mở Thí nghiệm → **3 vùng bấm trên chính các cột** (nửa
trái / phần tử giữa / nửa phải) → `svg` đổi `role` `img`→`group` → focus bàn
phím → bấm sai: `JSON.stringify(active.state)` KHÔNG đổi; (B) `packet_routing` —
tuyến gốc → ngắt chặng → **không tới được** → nối lại → **Về mạng ban đầu**.
Cờ: `--port --window --out`. Có **dấu vân tay trang** (`active.moduleId`, sai thì
thoát != 0).
⚠️ Hai cái bẫy đã dính trong chính wave này, đừng lặp lại:
(1) `evaluate` phải **thử lại** khi CDP báo `Promise was collected` — lần import
đầu làm Vite pre-bundle rồi RELOAD trang, huỷ execution context; coi đó là lỗi
sản phẩm là tố cáo nhầm. Có `warmup()` nạp trước đồ thị module nặng.
(2) Dừng bước theo nút "Thí nghiệm" là **SAI** — nút đó hiện ở mọi bước chưa
phải bước cuối, nên runner đứng ở bước 0 (không có điểm quyết định) rồi báo FAIL.
Mốc đúng là `.search-observe` (chỉ dựng khi `searchInteractionOf != null`).

<!-- hết khối 39 -->

<!-- khối 40/59 · dòng 1744–1745 của bản gốc · sha256 3f0ef2ee552576c152801642972158d4c213951951bc0803f9bfe91369b296f6 -->
### `frontend/scripts/accept-workspace-w4b3b.mjs` — xem mục ở phần script bên dưới.

<!-- hết khối 40 -->

<!-- khối 41/59 · dòng 1746–1755 của bản gốc · sha256 042dbad9e0507edfa5b2f38e96282632bffcb79e1cbe370cb3c2489cb60ae5dd -->
### `core/trace-builder.ts` — bổ sung W4B-3C
`clearVar(name)` — GỠ một biến TẠM khi thứ nó mô tả hết tồn tại. Không có nó thì
biến mô tả thao tác ĐANG DỞ sống tới hết trace và bước `done` tự mâu thuẫn:
`insertion_sort` tuyên bố đã sắp xong trong khi snapshot vẫn khai đang giữ một
phần tử, và renderer vẽ trung thành cái nó được kể (quân bài ngoài dãy + ô trống).
Chủ sở hữu là ENGINE — **đừng vá bằng `if (bước cuối) ẩn quân bài`**, đó là dạy
renderer nói dối hộ engine và để nguyên mâu thuẫn trong state gửi cho AI giải
thích. Tests: `core/terminal-truth-w4b3c.test.ts` (cả họ sắp xếp × 2 chiều +
quét toàn danh mục + bất biến "hold luôn có bước chèn phía sau").

<!-- hết khối 41 -->

<!-- khối 42/59 · dòng 1756–1769 của bản gốc · sha256 c2c537f5b53f85a8a5a8afd2059c8c49deb7e9afe38e541174b6502a5e265b89 -->
### `scripts/measure-composition.mjs` · offline (cần Chrome + Vite)
**ĐO bố cục, không cảm nhận** (W4B-2T §4). Với mỗi target chạy được offline, đo
trong Chrome: hộp bao **sân khấu** vs hộp bao **nội dung có nghĩa** (hợp của mọi
`svg`/`table` bên trong), mức dùng bề ngang/bề dọc, số **dải thông tin** quanh mô
phỏng (chú giải · thuyết minh · dải nhân quả · trạng thái tìm kiếm · kết quả ·
teaser · công cụ · khay giữ), và **TRÙNG NGHĨA ở bước cuối** (so tập từ ≥ 60%,
không so chuỗi — hai câu diễn đạt khác nhau vẫn là trùng). Cờ:
`--out --shots --window --port`.
⚠️ **Tỉ lệ dùng KHÔNG phải điểm chất lượng.** Cây cần khoảng thở, bit gom cụm là
đúng, `decimal_to_binary` 17% là ca DISCONFIRMING hợp lệ. Con số là dữ kiện để
phân loại, đừng biến thành mục tiêu tối ưu.
⚠️ Biết trước: encap 2D dựng bằng `div` nên không có `svg/table` ⇒ hộp bao trả
`null`. Đó là giới hạn của phép đo, không phải lỗi sản phẩm.

<!-- hết khối 42 -->

<!-- khối 43/59 · dòng 1770–1781 của bản gốc · sha256 ca4fb31ba5448c8c9824932e7f9eed1ca765601aa2ad790929a2ebb411488f2a -->
### `scripts/capture-w4b2r-representation.mjs` · offline (cần Chrome + Vite)
Runner CDP của W4B-2R — chứng minh CHÍNH SÁCH BIỂU DIỄN + vòng đời Quan sát trên
**7 bài làm chứng chọn theo CƠ CHẾ** (§31: tìm kiếm · sắp xếp · logic · hệ cơ số
· cảnh DSL · mạng đổi chính sách · mạng 3D sư phạm), không chọn theo ảnh ai gửi.
Mỗi bài kiểm ba việc: **READY/PAUSED** sau khi nạp (không tự chạy) · **toggle
2D/3D chỉ xuất hiện khi `representationPolicyOf` = `2d_and_3d_justified`** ·
chạy **trọn** canonical bằng nút Tiến với `prediction` vẫn `null`. Sidecar ghi
policy/renderer owner/timeline/capability đọc THẲNG từ store + `renderer.ts`,
không suy từ DOM. Cờ: `--port --window --out`.
⚠️ Dùng lại `warmup()` + thử lại `Promise was collected` của
`capture-w4b2i-interaction.mjs` (Vite pre-bundle làm reload trang giữa lượt đo).

<!-- hết khối 43 -->

<!-- khối 44/59 · dòng 1791–1800 của bản gốc · sha256 9a55657b2cd3b050d28cdc628f8e5042421da9e7d5157dde693bea34f556197a -->
### `scripts/audit-search-position.mjs` · offline (cần Chrome + Vite)
Runner ĐO HỆ ĐẾM VỊ TRÍ của họ tìm kiếm (W4B-2D §4) — chỉ ĐỌC, không bấm cam
kết, không mở Thí nghiệm. Ở một bước cam kết của `linear_search`/`binary_search`
nó thu hoạch MỌI bề mặt nói vị trí (nhãn cột `ArrayView` · `SearchActionZone` ·
chip `VarsView` · dải nhân quả · thuyết minh · mã giả) rồi đối chiếu bằng SỐ LẤY
TỪ ENGINE, không bằng chuỗi. Kết luận `SAME_SCREEN_CONTRADICTION` khi cùng một
vị trí ngữ nghĩa hiện hai hệ đếm. Có DẤU VÂN TAY bắt buộc (`active.moduleId` +
sân khấu đã dựng, sai thì exit 2). Cờ: `--port --out`. Artifact:
`docs/evaluation/m17/w4b2d-search-family/position-numbering/`.

<!-- hết khối 44 -->

<!-- khối 45/59 · dòng 1801–1812 của bản gốc · sha256 4e25fceef6bd903104f55510e5a7451acf424616505a44edf6263b030836d0b5 -->
### `frontend/scripts/measure-dag-composition.mjs` · offline (cần `npm run dev`)
W4B-4D — ĐO KHOẢNG TRỐNG CHẾT của sân khấu `logic.boolean_dag` ở bốn bề rộng.
Hai phép đo KHÁC NHAU, đừng lẫn: `fillPct` đo MỰC (rect trong SVG) so với thẻ —
sơ đồ to hay nhỏ; `gutterLeft/gutterRight/skew` đo CỤM nội dung so với thẻ —
hình có bị dồn về một bên không. Khiếu nại "dồn sang trái" là phép đo thứ hai,
nên một bản vá chỉ kéo `fillPct` lên vẫn hỏng đúng chỗ bị kêu.

Chính nó bắt được hai lỗi mà SSR không thấy: SVG rơi về bề rộng mặc định 300px
khi cha là `fit-content`, và khung nét đứt của cổng đầu ra bị viewBox cắt mất
7px. Có dấu vân tay trang (không thấy sân khấu DAG ⇒ thoát != 0).
Artifact: `docs/evaluation/m17/w4b4d-composition/`.

<!-- hết khối 45 -->

<!-- khối 46/59 · dòng 1813–1820 của bản gốc · sha256 c4bb25bb019dcb1999e79d397712d3f2fe7da7069f13a5cb2d900a01c5d10f8c -->
### `frontend/scripts/accept-experience-w4b4c.mjs` · offline (cần `npm run dev`)
W4B-4C — NGHIỆM THU TRẢI NGHIỆM: hỏi CÂU HỎI NGHIỆM THU bằng Chrome thật ở bốn
bề rộng. Với mỗi target đã chuyển sang tương tác, nó nạp bài, phát ĐÚNG action
mà bộ điều khiển trên màn hình phát, rồi khẳng định (a) trường kết quả ĐỔI,
(b) `state` đổi tham chiếu, (c) **không** phải bật Play. Vế (c) là vế chính:
một bài chỉ đổi khi chạy timeline thì vẫn là animation-first.
Artifact: `docs/evaluation/m17/w4b4c-experience/acceptance.json`.

<!-- hết khối 46 -->

<!-- khối 47/59 · dòng 1821–1829 của bản gốc · sha256 4a68c50317ca5a0a5e1ea85079d08f41cfd615dfaec9a176d5043da35b5fb14e -->
### `frontend/scripts/accept-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — NGHIỆM THU TRÌNH DUYỆT ở BỐN bề rộng (1920/1536/1366/768) cho 7 target
đại diện: 0 dải `experiment-trigger`; mọi `.sim-secondary-action` phải nằm TRONG
`.player-controls`; không tràn ngang; mở Thử thách ⇒ ≤1 bề mặt cam kết; parity
2D↔3D của `protocol_encapsulation` (cursor/stepCount/`getExplainContext` phải
KHỚP khi đổi cách xem); phiên A→Khám phá→B→A giữ nguyên object state, 0 `fetch`.
Có dấu vân tay trang + `--self-test` (tiêm lỗi giả, exit 1). Cờ:
`--port --out --self-test`. Artifact: `docs/evaluation/m17/w4b3a-after/`.

<!-- hết khối 47 -->

<!-- khối 48/59 · dòng 1830–1861 của bản gốc · sha256 4be0bbdcf01bd59cf88a2ab1e5aa9cb81e749da446d808f42ac9be45cc5d5e83 -->
### `frontend/scripts/accept-workspace-w4b3b.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3B — NGHIỆM THU BỐ CỤC KHÔNG-GIAN-LÀM-VIỆC ở 4 bề rộng, ở các trạng thái
unit test không với tới: **1 phiên · 2 phiên TRÙNG TIÊU ĐỀ · 6 phiên (quá sức
chứa) · chuyển phiên**. Khẳng định: 0 cột phiên thường trực · sân khấu KHÔNG hẹp
đi và KHÔNG bị đẩy sang phải khi số phiên tăng · 0 tràn ngang · tiêu đề 1 dòng ·
đúng 1 tab đang-xem · nhãn không trùng khi tiêu đề trùng · `Mô phỏng mới` tới
được **kể cả khi chỉ có 1 phiên** · dải điều khiển không xuống dòng trên desktop ·
chuyển phiên giữ đúng object state, 0 `fetch`. Có `--self-test` + `--label`.
Artifact: `docs/evaluation/m17/w4b3b-workspace/{before,acceptance}.json`.

**BA BẪY ĐÃ CẮN KHI VIẾT SCRIPT NÀY** (đọc trước khi viết script CDP mới):
1. **Đếm dòng bằng `top` là SAI.** Trong flex row có `align-items:center`, con
   cao thấp khác nhau thì `top` khác nhau — phép đếm đó báo 5–7 dòng cho một
   hàng phẳng. Đếm bằng CHỒNG LẤN DỌC theo thứ tự DOM.
2. **WARMUP PHẢI DÙNG URL ĐÃ GIẢI**, không dùng đường dẫn trần. Warmup bằng
   `import('/src/state/store.ts')` ĐĂNG KÝ chính URL trần vào
   `performance.getEntriesByType('resource')`, nên `pick()` sau đó chọn nó thay
   vì URL `?t=…` app đang chạy ⇒ lại lái store thứ hai. Bẫy hai-instance cắn
   LẦN THỨ HAI, do chính lớp chống nó gây ra vì thêm sai thứ tự.
3. **`Promise was collected`** = Vite tối ưu deps rồi reload GIỮA lúc await.
   Phải có `warmup()` + retry trên lỗi CDP (cùng khuôn `measure-composition.mjs`).
   Và **chú thích bên trong template literal KHÔNG được chứa dấu backtick**.
4. **Đếm dòng bằng `top` là SAI** (xem 1).

**BẪY ĐÃ CẮN MỘT LẦN — đọc trước khi viết script CDP mới.** Vite gắn
`?t=<timestamp>` vào URL module sau HMR, nên `import('/src/state/store.ts')` từ
console có thể trả về **instance THỨ HAI**: script lái một store, trang vẽ theo
store kia, và mọi khẳng định "không thấy X" đều XANH vì lý do sai. Script này
giải URL từ chính trang (`performance.getEntriesByType('resource')`).
`measure-composition.mjs` KHÔNG có lớp bảo vệ đó — nó thất bại ồn ào (null
`querySelectorAll`), nên gặp lỗi đó thì **restart `npm run dev`**, đừng sửa số.

<!-- hết khối 48 -->

<!-- khối 49/59 · dòng 2019–2026 của bản gốc · sha256 e9aed3bc88d11de3d00a29e3862a8dbf929d2382b6d0ad081501d47940cab570 -->
### `frontend/scripts/accept-classroom-m18.mjs` · offline (cần dev + uvicorn)
Nghiệm thu tầng lớp học ở bốn bề rộng × ba vai. Kiểm DANH TÍNH BACKEND trước
tiên: container Docker cũ chiếm cổng 8000 sẽ trả 404 cho mọi endpoint mới và
làm mọi kết quả sau đó vô nghĩa (đã cắn một lần). Khẳng định: khách không có
thanh điều hướng và bị 401 ở lớp/bài · học sinh nhận bài, bị 403 khi tạo lớp và
khi quan sát · giáo viên thấy lớp + mã + bảng quan sát, và envelope hỏng bị
chặn 400. Artifact: `docs/evaluation/m18/classroom-acceptance.json`.

<!-- hết khối 49 -->

<!-- khối 50/59 · dòng 2490–2508 của bản gốc · sha256 31bcb9784f721ac29048ddad180afd1dc74ee1b7d7469251c745b9fda73640d6 -->
### `frontend/scripts/measure-stage-composition.mjs` · offline (cần `npm run dev`)
Đo bố cục sân khấu cho **mọi** target (khác `measure-dag-composition.mjs` chỉ đo
được `logic.boolean_dag`). Ba số mỗi target: `fillPct` (bề rộng MỰC / bề rộng
trong thẻ) · `skew` (lệch lề trái–phải của mực) · `railSpan` (mép trái của chữ
cách mép trái của mực bao xa — lớn = hai hệ căn lề trong cùng một thẻ).

⚠️ HAI LẦN ĐO SAI TRƯỚC KHI RA SỐ ĐÚNG, ghi lại vì cả hai đều "xanh mà vô nghĩa":
1. bản đầu lấy hộp bao của `querySelectorAll('*')` — div BỌC rộng bằng thẻ nên
   **mọi** target ra "lấp 99.9%, lệch 0", tức báo SẠCH cho đúng bố cục đang bị
   kêu. Nay chỉ đếm `<svg>` và phần tử LÁ thật sự có sơn.
2. bản thứ hai đếm cả bảng `details` gập được nên `boolean_dag` báo lệch 558px
   trong khi sơ đồ của nó đã căn giữa 0px — phép đo tự bịa ra một lỗi không có.

Và một lần nữa dính bẫy **backtick trong template literal** (đã cắn hai lần ở
`capture-*.mjs`): chú thích tiếng Việt trong khối `MEASURE` có \`...\` làm Node
báo `SyntaxError`. Trong khối đó không được có backtick nào.

Artifact: `docs/evaluation/m18/stage-composition.json`.

<!-- hết khối 50 -->

<!-- khối 51/59 · dòng 2509–2531 của bản gốc · sha256 77e2b10ef2804954aaf70f2646e72b2540581c1c859c72823d970abcefeb35af -->
### `frontend/scripts/audit-composition.mjs` · offline (cần `npm run dev`)
M19 — SOÁT BỐ CỤC DÙNG CHUNG toàn danh mục. Thay `measure-stage-composition.mjs`
(bản đó chỉ đo mực/thẻ, không đo KHUNG và không đo bốn rail).

Mỗi dòng: sân khấu · khung cơ chế · mực có nghĩa · `frameFill` · bốn rail +
`maxRailDelta` · tràn ngang · cắt hình · PHÁN QUYẾT. Hai lỗi tách bạch, không
gộp thành một điểm: **A** = mực < 70% KHUNG mà khung lại chiếm > 90% sân khấu
(cơ chế nhỏ trôi trong khung quá khổ) · **B** = rail lệch > 24px (hình và chữ
hai hệ căn lề).

⚠️ KHÔNG chấm bằng tỉ lệ lấp một mình: 17% là ĐÚNG nếu khung cũng ôm sát 17% ấy.
Lỗi là 17% mực trong khung rộng 100%, nên mẫu số là KHUNG chứ không phải thẻ.

Cách chọn "mực có nghĩa" khai ngay trong file (bắt buộc — ba lần đo trước đều
trả về số mà vẫn sai): tính `<svg>` + phần tử LÁ có sơn; bỏ div BỌC (rộng bằng
thẻ nên nuốt mọi phép đo) và bỏ đồ đạc của thẻ (tiêu đề, chú giải, thuyết minh,
bảng gập, thanh tham số).

Hai hiện vật đã sửa trong chính script: lỗi trong trang bị nuốt thành
"(không trả lời)" nên bốn target hỏng đọc ra như thiếu mẫu — nay lỗi nổi lên; và
lượt nạp nặng thỉnh thoảng không trả kịp nên có THỬ LẠI một lần, vẫn hỏng thì
ghi dòng `KHÔNG ĐO ĐƯỢC` chứ không im lặng bỏ.

<!-- hết khối 51 -->

<!-- khối 52/59 · dòng 2532–2545 của bản gốc · sha256 0f7395c3fe8081887c2c813adf4e0320082940b008daf93cc65771442acca8dc -->
### `simulations/stage-size.ts`
M19 — MỘT LUẬT KÍCH THƯỚC SVG SÂN KHẤU, một chủ sở hữu. `stageSvgSize(w)` trả
`width={w}` + `max-width: 100%` (co được, KHÔNG phóng được).

Vì sao gom: sáu renderer cùng viết `width="100%"` + `maxWidth: w`, dạng đó KHÔNG
khai bề rộng riêng nên khi cha là `fit-content` thì `100%` không có gì quy chiếu
và Chrome rơi về 300px mặc định (`boolean_dag` đã dính: sơ đồ 662px vẽ ở 300px).
Nó cũng buộc phải kèm `margin: 0 auto` để trông cân, và chính cú căn giữa đó tạo
RAIL THỨ HAI — đo được `and_gate` lệch 581px, `decimal_to_binary` 673px.

Áp cho `binary/ui` · `logic/ui` · `network/ui` · `algorithm/program-module`.
`ArrayView` giữ bề rộng tự đo từ khung chứa (nó vốn co giãn theo cột) nhưng đã
BỎ `margin: 0 auto` cùng lý do.

<!-- hết khối 52 -->

<!-- khối 53/59 · dòng 5288–5319 của bản gốc · sha256 1e72cd474cbd751c5953b9ae43b0cc47bf8b85679d819f23a8f6f5b6101772ec -->
### `backend/scripts/replay_harness.py` · offline · **0 API call**

Chạy MỘT `SemanticProgramSpec` trên **nhiều đầu vào** rồi so chuỗi hành động.
Export: `replay()` · `KetQuaReplay` · `TIM_MAX` / `GAN_CUNG` (hai chương trình
đối chứng) · `SO_BIEN_THE`.

VÌ SAO: tới 2026-08-24 một chương trình chỉ chạy đúng **một** lần, trên đúng
`initial_value` mà LLM viết cùng nó. Với một mẫu, *"tính ra đáp án"* và *"biết
trước đáp án"* cho cùng kết quả.

**RANH GIỚI VỚI C₁b — đọc trước khi thêm detector.** `coverage_gate` (`3e0d67c`)
đã bịt "gán thẳng đáp án" bằng kiểm **TĨNH** (witness phải có đường phụ thuộc,
kể cả qua nhánh, về container đầu vào). File này **không làm lại**. Nó phủ chỗ
tĩnh không với tới: chương trình *có* đọc container mà vẫn không tính đúng —
`GAN_CUNG` cố ý đọc `a` qua `length` nên **qua được C₁b**, và chỉ replay mới lộ.
Cũng khác `evaluation/metamorphic.py` (cái đó biến đổi **văn bản đề** cho
classifier; đây giữ chương trình, đổi **dữ liệu**).

Ba detector, **không cần oracle** — chạy được trên bất kỳ chương trình sinh nào:
`INPUT_IGNORED` (mọi đầu vào cho cùng một chuỗi hành động) · `DEAD_STATE`
(container khai ra mà không lượt nào đụng) · `HARD_CODED?` (witness hằng qua mọi
biến thể). Truyền `oracle=` thì so thêm.

⚠️ **`HARD_CODED?` là NGHI VẤN, KHÔNG vào `ok`** — một nghĩa vụ có thể hằng
chính đáng, biến nó thành phán quyết là đẻ false rejection ở chỗ khó cãi nhất.
Chỉ `INPUT_IGNORED` và `DEAD_STATE` quyết PASS/FAIL.

Chữ ký hành động cố ý **bỏ giá trị**, chỉ giữ `(action, target)`: giữ giá trị
thì hai lượt luôn khác nhau và `INPUT_IGNORED` xanh vĩnh viễn. Khoá bởi
`test_replay_harness.py` (9 test, nửa là ca ÂM TÍNH — chương trình thật không
được gắn cờ).

<!-- hết khối 53 -->

<!-- khối 54/59 · dòng 5320–5341 của bản gốc · sha256 9fd6364179d3fb42111222d5f1f42e8c99c758136517081727fa8b9ad41015f5 -->
### `backend/scripts/classify_run1_failures.py` · offline · **0 API call**

Soi lại các ca trượt thẩm định của SEALED #1 bằng hợp đồng HIỆN TẠI, phân loại
**từng lỗi Pydantic** thành `GOP:<biên đã gộp>` hoặc `TRUOT:<lý do>`. Export:
`chay()` · `tach_loi()` · `phan_loai()` · `BOOL_KINDS`.

Nó trả lời *"bốn biên chuẩn hoá đáng giá bao nhiêu"* mà **không tiêu một lượt
LLM nào** — làm được vì `sealed_cases.json` giữ nguyên văn khối lỗi Pydantic, và
khối ấy liệt kê ĐỦ mọi lỗi của một chương trình. Kết quả 2026-08-24: **22/27 ca
nay qua tầng Pydantic**, 3 vẫn trượt (`kind` bịa ra · `field` ngoài
`{left,right,val,data}`), 2 không kết luận được (JSON cụt).

HAI RANH GIỚI, đừng trích sai: (1) qua Pydantic mới là **chạm cổng kế**, sau đó
còn `validate_semantic_program` → interpreter → C₁a → C₁b → C₂ — ở lượt #1, 9
chương trình qua cú pháp rụng còn 3 chạy được và 1 phát được; (2) nó chạy trên
**40 ca ĐÃ LỘ** nên là **chẩn đoán**, không phải số held-out.

`tach_loi()` phân biệt `None` (không phải lỗi schema — JSON hỏng) với `[]` (có
khối lỗi nhưng rỗng): hai thứ dẫn tới hai kết luận khác nhau, gộp là mất một
nhóm ca. Ba lớp `TRUOT` được ghi thành **dự đoán tiền đăng ký** ở
`RUN2_PREFLIGHT.md §3c` để lượt #2 bác bỏ được.

<!-- hết khối 54 -->

<!-- khối 55/59 · dòng 5870–5884 của bản gốc · sha256 a11bdfa47ddb777a570c27561fc93840643fd1e0a22ad6dbc03e1cad62b493e7 -->
### `backend/scripts/ocr_sgk_ingest.py` · **live** (Cloud Vision), có CACHE

Đọc SGK bản QUÉT thành text. Năm cuốn trong `data/knowledge/sources/` không có
lớp chữ — `pdftotext` trả 60 ký tự cho 60 trang, đúng bằng số dấu ngắt trang.
Repo **không có** RAG/index/cache nào để tái dùng, và `app/ingestion/input.py`
là lớp chuẩn hoá input của **sản phẩm** (text/docx/ảnh), không đọc PDF.

Đường đọc: PyMuPDF dựng ảnh trang → Cloud Vision `document_text_detection`.
Credential lấy từ `.secrets/` qua `GOOGLE_APPLICATION_CREDENTIALS`; **không in
và không ghi** giá trị secret vào artifact.

**Cache là điểm chính**: mỗi trang OCR đúng một lần rồi ghi vào
`data/knowledge/ocr-cache/<sách>.json`. `data/` bị gitignore nên text SGK không
vào kho mã. `--stats` báo trạng thái cache mà **không tốn call nào**.

<!-- hết khối 55 -->

<!-- khối 56/59 · dòng 5885–5896 của bản gốc · sha256 52df2cb86c30befbe3a5eca5bc6fb5f709ab5172ab85ff3f17398733187c5cf1 -->
### `backend/scripts/validate_sealed_submission.py` · offline, CUSTODIAN chạy

Kiểm **hình dạng** tập SEALED trước khi niêm phong: trường thiếu, `case_id`
trùng, `obligation_kind` sai chính tả, 4 metadata guard, và dạng `expected` cũ
`{tên_biến: giá_trị}` (bị bỏ vì tên biến do LLM đặt). Tách khỏi runner có chủ
đích — runner chạy một lần, còn cái này chạy bao nhiêu lần cũng được vì không
gọi API.

**Cố ý KHÔNG kiểm** phạm vi đề và tính đúng của ground truth: ground truth mà
máy kiểm được thì không còn độc lập. Khoá bởi `test_sealed_validator.py`, gồm cả
một test chống chính nó tự nhận là bộ chấm.

<!-- hết khối 56 -->

<!-- khối 57/59 · dòng 5897–5970 của bản gốc · sha256 0822c34124e72565a0514722f76cc249a190db7b07e0bf655fb211111bb05b02 -->
### `backend/scripts/run_sealed_evaluation.py` · **live**, chạy ĐÚNG MỘT LẦN

Runner Task 12. Kiểm candidate + vân tay con dấu **trước** khi mở SEALED, chạy
`run_pipeline(semantic_route="shadow")` nên MỘT lượt đo được cả hai route. Ngân
sách 440 logic / 520 HTTP cưỡng chế qua `gemini.ApiBudget` (dùng lại, không viết
bộ đếm mới). Viết **trước** khi thấy SEALED có chủ đích; phần chấm/tổng kết được
khoá offline bởi `tests/semantic_program/test_sealed_runner.py` vì chạy lại là
mất tính held-out.

Bốn thứ trong đây dễ bị viết sai vào luận văn, nên mỗi thứ có một test khoá:
**A−B phải phân rã** (chỉ một nhánh là `verification_gap`) · **B là
STRONG-assurance nội bộ, không phải "đúng"** (oracle độc lập báo riêng, và case
`servable` mà oracle nói sai được nêu đích danh) · **D1 là claim CẤU TRÚC**
(số lượt LLM đứng yên khi số bước trải rộng; token/case chỉ là telemetry hỗ trợ)
· **N=40 khoá**, chạy thiếu thì `evaluation_complete: false` và A/B không được
công bố như kết quả chính.

**`--dataset dev` (2026-08-24) — đường đo KHÔNG cần seed của GVHD.** 20 case ở
`dev/cases.json`, tập tự khai *"DEV **được nhìn**; SEALED thì không"*. Chạy nó
**không đốt** pool 49 bài held-out và **không cần** seed, nên nó là cách duy
nhất biết A/B của hệ hiện tại trước lượt #2. Ba khác biệt so với đường sealed,
đều cố ý: bỏ `_kiem_seal()` (DEV không có con dấu — giả vờ có là nói dối xuất
xứ) · **vẫn** `_kiem_candidate()` (chạy trên cây đã trôi thì số không gắn với
bản nào) · trần riêng `TRAN_LOGIC_DEV`/`TRAN_HTTP_DEV` = 260/310, **dẫn từ cùng
call graph** với N=20 nên đổi một trần không kéo trần kia theo.

⚠️ **Số của DEV không bao giờ là số của luận văn**: hệ đã được chỉnh trên chính
20 case này. Nó trả lời đúng một câu — *bốn biên chuẩn hoá + vòng sửa có làm
phễu thông hơn không*. Oracle sẽ **UNGRADED toàn bộ**: ground truth của DEV còn
ở định dạng cũ (khoá theo TÊN BIẾN), không phải hợp đồng nghĩa-vụ + giá-trị mà
`_cham` đòi — và **không được tự chuyển đổi**, viết lại ground truth là việc của
custodian. Báo cáo tự đeo `dataset` + `canh_bao_dataset`; đầu ra mặc định vào
`dev-results/`, và có **chặn cứng** không cho DEV ghi vào `results/`. Khoá bởi
ba test mới ở `test_sealed_runner.py` §7.

**ĐÃ CHẠY 2026-08-23 — lượt duy nhất, không được gọi lại.** Artifact ở
`docs/evaluation/semantic-benchmark/results/`:

- `sealed_summary.json` — số tổng hợp (A/B/A−B/oracle/D1/D2/ngân sách).
  **Hai khối thêm 2026-08-24, đọc được từ LƯỢT #2 trở đi**:
  `token_dau_ra_theo_route` (token ĐẦU RA = `candidates` **+** `thoughts`, tách
  route sinh ↔ route module — bỏ `thoughts` là báo thấp đi gần ba lần, nó lớn
  hơn `candidates` 2,6× ở stage `semantic_program`; vẫn là telemetry HỖ TRỢ,
  **không** phải D2 vì hai route chạy trên hai population khác nhau) và
  `coercion_rate` (bốn biên chuẩn hoá nổ bao nhiêu lần — xem `coercion_stats.py`).
  Lượt #1 **không có** hai khối này, nhưng token đầu ra của nó vẫn tính lại được
  từ `sealed_cases.json[].token` vì `record_usage` đã ghi đủ năm trường ngay từ
  đầu.
  **Khối thứ ba, 2026-08-24**: `reliability_v2` (8 tầng thất bại + G1/G2/A/R/B/
  V/O) — xem `reliability_v2.py`. Đặt CẠNH `A_generative_executability` và
  `B_internal_servable`, **không thay** chúng: hai cái ấy là chỉ số duy nhất so
  trực tiếp được với lượt #1. Khoá bởi `test_sealed_runner.py §8`
  (`_KHOA_CU` — mất một khoá cũ là ĐỎ).

**Runner BỌC `stage_semantic_program` từ phía harness** để bắt
`SemanticProgramSpec` cho replay. Observer không mang spec, mà phát thêm spec ra
observer là sửa `pipeline.py` — tức sửa engine. Proxy đi qua nguyên vẹn, chỉ ghi
lại, và **khôi phục trong `finally`**: một case ném lỗi mà để lại proxy thì case
sau chạy qua hàm đã bọc chồng nhiều lớp, mỗi lớp thêm một lượt LLM. Khoá bởi
`test_proxy_bat_spec_KHONG_ro_ri_sang_case_sau`.

**Tầng ⑦ (renderer) KHÔNG chạy ở đây** — `renderer_V` luôn `None` ở pha A. Nó
thuộc pha B (trình duyệt, 0 call LLM), chạy lại được mà không phải tiêu quota
lần nữa.
- `sealed_cases.json` — 40 bản ghi case-level: `semantic` (stage_reached,
  executable, servable, error_code, reason), `legacy` (route module để so),
  `contract` (nghĩa vụ khai), `cham` (verdict oracle), `token` theo stage.
- `OFFICIAL_RESULT.md` — **bản diễn giải chính thức, nguồn trích cho luận văn**.
  Chứa cảnh báo bắt buộc: 17/40 case chết ở `spec_version` float vs
  `Literal["1.0"]`, nên A = 3/40 là cận dưới của cận dưới.

Gọi lại runner sẽ ghi đè artifact và **phá tính held-out** — muốn đo lại phải
niêm phong SEALED MỚI, không phải chạy lại tập cũ.

<!-- hết khối 57 -->

<!-- khối 58/59 · dòng 5996–5999 của bản gốc · sha256 8b53c86e22ac5a74bf2cc473a316f01d62a4c279d1527a8c404c247dcbc89fbc -->
### `backend/scripts/seal_benchmark.py` · offline

Khoá/kiểm fingerprint của SEALED benchmark. Thoát != 0 khi seal vỡ.

<!-- hết khối 58 -->

<!-- khối 59/59 · dòng 6009–6015 của bản gốc · sha256 d9b524e15d7378fb0c69b6859bae53c0690ffdafee98da6189b7b3b9ef2b2077 -->
### `frontend/scripts/capture-stack-vnext.mjs` · cần Chrome + `npm run dev`

Bằng chứng trình duyệt thật cho kịch bản Stack vNext: kiểm tra trạng thái tương tác
thay đổi thật sự khi bấm chuyển bước (khắc phục điểm mù của SSR renderToString).
Đo đạc dấu vân tay trang, kiểm tra render ngăn xếp qua Playwright và hỗ trợ `--faultcheck`.


<!-- hết khối 59 -->
