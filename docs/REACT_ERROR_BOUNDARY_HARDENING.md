# REACT_ERROR_BOUNDARY_HARDENING — chặn ngoại lệ bất ngờ ở frontend

> Thực hiện **2026-09-03**. **0 lượt gọi model · 0 dòng backend · 0 dependency
> mới.** Phòng thủ theo chiều sâu, **không** phải vá một lỗi đang chảy.

---

## 1. Điểm xuất phát

Kho **không có một error boundary nào**. Hệ quả: cả năm miền — `HOME`,
`WORKSPACE`, `SCENE3D`, `INSPECTOR`, `PLAYBACK` — chung **một số phận**. Một lần
ném ở bất kỳ đâu là React gỡ trọn cây, và người dùng nhìn một trang trắng không
còn cả thanh điều hướng để đi tiếp.

Bốn dạng envelope hỏng đã đo đều đi qua êm (`certify-refusal-surface` 21/21),
nên đây không phải bản vá cho một lỗi đang xảy ra. Nó là lưới cuối cho lớp lỗi
mà **không phép kiểm dữ liệu nào bắt được**: một bất biến bị phá trong lúc dựng.

---

## 2. Bản đồ miền hỏng, đọc từ cây thật

```
.app-root                          ← lưới NGOÀI (main.tsx → AppRoot)
  ├── AppSidebar          user
  ├── PracticeReporter    user, không vẽ gì
  ├── .app-main
  │     ├── header.nav-bar         ← NGOÀI lưới trong: sống sót khi nội dung vỡ
  │     └── ErrorBoundary mien="main"   ← lưới TRONG
  │           ├── (workspace) SimulationWorkspace → Scene3DExplorer
  │           │                 → scene3d-view · inspector · playback
  │           └── (route)     HomeView / LibraryView / …
  └── AuthGate
```

| miền | ném lúc dựng | ném lúc sự kiện | bán kính TRƯỚC | bán kính SAU |
|---|:-:|:-:|---|---|
| HOME | ✅ | ✅ | cả trang | vùng `<main>` |
| WORKSPACE | ✅ | ✅ | cả trang | vùng `<main>` |
| SCENE3D | ✅ | ✅ | cả trang | vùng `<main>` |
| INSPECTOR | ✅ | ✅ | cả trang | vùng `<main>` |
| PLAYBACK | ✅ | ✅ | cả trang | vùng `<main>` |
| vỏ (thanh trên · cột trái · `AuthGate`) | ✅ | ✅ | cả trang | lưới NGOÀI |

---

## 3. Đặt ở đâu, và vì sao không hẹp hơn

**Hai mức, mỗi mức một việc.**

**Lưới TRONG — quanh `<main>`.** Cả năm miền đều dựng bên trong nó, nên **một**
lưới ở đây phủ cả năm. Thứ nó cứu được là **thanh điều hướng và cột trái**:
chúng nằm ngoài `<main>`, nên người dùng còn đường đi tiếp.

⚠️ **Vì sao không hẹp hơn — không phải vì lười.** Với bài hình học,
`Scene3DExplorer` **chính là** cả bề mặt workspace: `SimulationWorkspace` trả nó
ra trực tiếp và truyền **đề bài vào trong** nó. Bọc riêng khung 3D vì thế vẫn
mất đề bài — không giữ thêm được gì so với lưới ở `<main>`, chỉ thêm một tầng.

**Lưới NGOÀI — quanh cả `App`, dựng ở `main.tsx`.** Phủ phần lưới trong không
với tới: thanh trên, cột trái, `AuthGate`, `PracticeReporter`. Hai lưới trả lời
hai câu khác nhau — *"nội dung hỏng, giữ lấy điều hướng"* và *"vỏ hỏng, tải lại
thôi"*. Cái sau không thể giữ điều hướng, vì điều hướng chính là thứ vừa vỡ.

Fallback cố ý **nghèo**: một câu, một nút. Càng nhiều thứ trong fallback thì
càng nhiều thứ ném được trong chính lưới cuối — và lúc ấy không còn lưới nào
bắt nữa. Nó không đọc `scene.objects`, không đọc vật đang chọn, không đọc khung
hiện tại.

---

## 4. Lỗi miền KHÔNG đi qua lưới

| loại | ví dụ | đường xử lý |
|---|---|---|
| **lỗi miền** (kết quả hợp lệ) | ngoài phạm vi · xuất xứ không đủ · không dựng được · envelope hỏng | bề mặt từ chối riêng, **không ném** |
| **ngoại lệ lập trình** | bất biến bị phá lúc dựng · `undefined` bị dùng nhầm | lưới chặn |

Định tuyến một lời từ chối qua `throw` để lưới lo là biến một câu trả lời thành
một sự cố — và lúc ấy người học mất luôn lời giải thích. `certify-refusal-surface`
vẫn **21/21** với bề mặt cũ; `ERROR_BOUNDARY_TRIGGERED_FOR_EXPECTED_REFUSAL = 0`.

---

## 5. Đặt lại — và vì sao `resetKey` là bắt buộc

`hasError` không tự mất. Không có khoá thì người dùng mở bài khác, cây con mới
hoàn toàn, mà lưới vẫn nhớ lỗi của bài trước và tiếp tục hiện fallback.

Đây **đúng lớp lỗi** mà bản vá `Bước 10/6` đã dạy một lần: trạng thái sống lâu
hơn thứ sinh ra nó. Khoá dẫn từ **bài đang mở**
(`view | simulation_id | title`), và đặt ở `getDerivedStateFromProps` chứ không
`componentDidUpdate` — nó chạy **trước** lượt dựng lại, nên cây con của bài mới
không bị fallback của bài cũ chặn mất một nhịp.

---

## 6. Một dữ kiện về SSR, đo được khi dựng phép kiểm

`renderToString` **KHÔNG chạy error boundary**: SSR không có pha commit, nên
`getDerivedStateFromError` và `componentDidCatch` không bao giờ được gọi, và
ngoại lệ lan thẳng ra ngoài. Bản đầu của tệp kiểm viết ba ca theo giả định ngược
lại, và cả ba đỏ ngay lượt chạy đầu.

Nên phép đo chia làm ba, mỗi phần đo đúng thứ nó đo được:

| | đo gì | ở đâu |
|---|---|---|
| ① | logic của lớp: bật cờ · trả fallback · đặt lại theo khoá · ghi log | `error-boundary.test.tsx` — gọi thẳng, không cần renderer |
| ② | fallback dựng ra chữ gì, có lộ gì không | `renderToString` trên chính fallback (nó không ném) |
| ③ | **hành vi thật khi một cây SỐNG ném** | Chrome thật, `certify-error-boundary.mjs` |

Kho không có `@testing-library/react` và không có jsdom, nên ③ là cách duy nhất
để câu *"lỗi có bị chặn không"* được trả lời bằng **đo** chứ không bằng **suy**.

### Tiêm lỗi mà không để lại công tắc trong sản phẩm

Đặt một getter ném trên `id` của một vật trong cảnh, rồi nạp lại envelope với
**một cảnh mới cùng mảng vật**. Vá **sống trong tab** của lượt đo, gỡ ngay sau
đó — không dòng nào tồn tại trong bản dựng. Một "chế độ gây lỗi" trong bản dựng
thật là một bề mặt tấn công và một cách để ai đó vô tình bật.

⚠️ **Hai lần tiêm đầu KHÔNG chạm tới đường dựng**, và lượt đo báo **ĐỎ** thay vì
xanh giả — ca `§15 phép tiêm phải chạm tới đường dựng` tồn tại đúng để chặn điều
đó. Nguyên nhân: xưởng tính `day` bằng `useMemo([scene])`, nên đầu độc
`scene.objects` **sau khi mount** thì không ai đọc lại. Phải đổi **danh tính**
`scene` mới buộc tính lại.

---

## 7. Điều lưới KHÔNG bắt — phân loại, không gộp

```
REACT_ERROR_BOUNDARY            CLOSED
ASYNC_EXCEPTION_CONTAINMENT     NOT_COVERED
WEBGL_CONTEXT_LOSS_RECOVERY     NOT_COVERED
```

React error boundary bắt ngoại lệ trong **render**, **lifecycle** và
**constructor**. Nó **không** bắt:

- ngoại lệ trong trình xử lý sự kiện (`onClick`…);
- promise bị từ chối mà không ai bắt;
- `setTimeout` / `requestAnimationFrame` — kể cả vòng vẽ của Three.js;
- lỗi ném từ chính fallback.

Nói *"đã chặn mọi lỗi frontend"* sau khi thêm boundary là một tuyên bố sai, và
nó sẽ được tin. Hai lớp còn hở ghi ra để chúng là **quyết định**, không phải
điều ai đó tưởng đã xong.

⚠️ `tryCreateWebGLRenderer` đã bắt thất bại **khởi tạo** WebGL và rơi về
`GEOMETRY_WEBGL_FALLBACK`; **mất context giữa chừng** thì chưa có đường phục hồi.
Không mở nó thành việc trong wave này — chưa có ca đo được.

---

## 8. Phiên bản

**`CACHE_VERSION` giữ 63.** Không một dòng backend nào đổi, envelope không đổi
byte. Bump vì xử lý ngoại lệ ở giao diện là bump vô cớ.

**`stable_capability_hash()` không đổi** · **candidate không đổi**: các tệp sửa
(`App.tsx`, `main.tsx`, `ErrorBoundary.tsx`, `global.css`) **không** thuộc
`MEASURED_SYSTEM_PATHS`.

**`NEW_NPM_DEPENDENCY = NO.** `react-error-boundary` là vài chục dòng vòng đời;
thêm một dependency cho ngần ấy là thêm một thứ phải theo dõi. Lớp ở đây theo
đúng quy ước kho (chú thích tiếng Việt, tên trường tiếng Việt) và không dùng
`any`, không `ts-ignore`.

---

## 9. Cổng

| cổng | kết quả |
|---|---|
| `vitest` | **685 passed** (50 tệp) — +13 ca lưới chặn |
| `npm run build` | PASS |
| `pytest` | **2829 passed**, 1 skipped — drift 0 |
| `certify-error-boundary.mjs` | **9/9** |
| `certify-display-authority` · `construction-bridge-g4` · `section-coplanar-edge` | 8/8 · 7/7 · 7/7 |
| `certify-display-metadata` · `journey-integration` · `offline-journey` · `refusal-surface` | 4/4 · 13/13 · 11/11 · 21/21 |

Đo được trong Chrome thật sau khi tiêm lỗi: `#root` còn **107 ký tự** nội dung,
`nav = true`, `fallback = true`, không vết ngăn xếp nào; bấm *"Thử lại"* →
`canvas = 1`, `fallback = false`; mở bài khác → dựng sạch.
