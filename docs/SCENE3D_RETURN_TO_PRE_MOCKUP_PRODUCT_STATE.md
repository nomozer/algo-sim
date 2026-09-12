# SCENE3D_RETURN_TO_PRE_MOCKUP_PRODUCT_STATE (2026-09-12)

Người dùng yêu cầu đưa phần mô phỏng hình học về **trạng thái trước commit
triển khai mockup đầu tiên** — không phải trước D2, mà trước `7f34286`.

## 1. Mốc

```
PRE_MOCKUP_PRODUCT_HEAD        = e6c2330   docs(state): tách hai tuyến next…   2026-09-10 19:59
FIRST_MOCKUP_IMPLEMENTATION    = 7f34286   feat(geometry): đưa ngôn ngữ…       2026-09-11 02:03
PARENT_OF_FIRST_MOCKUP_COMMIT  = e6c2330   ✓ `git rev-parse 7f34286^` khớp
HEAD trước khi phục hồi        = 6edddb3   cây sạch
```

17 commit trong khoảng, **13 chạm mã sản phẩm**, 4 chỉ chạm tài liệu/công cụ.
Backend: **0 byte** đổi trong toàn bộ khoảng.

## 2. Bản cũ trông như thế nào — đo, không nhớ

Worktree tại `e6c2330`, `npm install` bằng bản sao `node_modules` thật (dependency
giữa hai mốc **giống hệt**, nên bản sao là chính xác chứ không phải xấp xỉ; không
junction, không symlink).

```
BUILD / TEST         build ✓ · vitest 817/817 ✓
CAMERA               Y-up — up = (−0,268; 0,894; −0,358); p4/p5 ra
                     (−0,268; −0,358; −0,894) ⇒ trụ và nón NẰM NGANG
QUAY 360°            CÓ — quét 940°, quanh Y 1051°, quanh Z chỉ 12°
KÍCH THƯỚC           chiếm 0,556–0,859 (desktop 1318×610) · 0,524–0,850 (mobile 340×418)
DPR                  1 — khung vẽ bằng đúng cỡ CSS, không có DPR 2
MÀU                  tím/lavender cho mặt phẳng · nâu/vàng cho khối · cam cho thiết diện
NÉT                  bề dày 2,02–2,79 px; khối cong KHÔNG có đường bao
NHÃN                 2–6 nhãn/ca; p3 chỉ 2, p6 chỉ 2
MẢNG TÔ              đậm tới mức bị đếm là MỰC (p1 49 452 điểm; HEAD cũ 11 282)
TỪNG BƯỚC bài thật   bước 8 ≡ bước 11 (trùng băm ec987bbf00b2);
                     bước 6 (6537 mực) NHIỀU hơn bước 8 (4371)
```

### ⚠️ Một lỗi BỘ ĐO đã suýt vào báo cáo

Lượt đo đầu trả **13°** cho một cú kéo dài 1,4 lần bề rộng khung — đọc như
*"bản cũ không quay được"*. Sai: phép đo phân tích phương vị quanh trục **z**,
còn bản cũ quay quanh **y**, nên phương vị theo z không cộng dồn. Con số ấy đo
chính phép đo dùng sai hệ, không đo sản phẩm.

Đo lại bằng **tổng góc giữa hai hướng nhìn liên tiếp** — không phụ thuộc trục —
ra **940°**. Bản cũ xoay tự do; nó chỉ xoay **quanh trục sai**. Cùng dữ liệu,
hai kết luận ngược nhau, và bản sai trông giống bằng chứng hơn.

## 3. So sánh ba cột trước khi đổi mã

`BA_COT_P1_P7_DESKTOP.png` · `BA_COT_P1_P7_MOBILE.png` · `BA_COT_BAI_THAT.png`,
cùng fixture, cùng bước, cùng khung, **cùng bộ đo**; chỉ `dist/` khác nhau. Video
ba bản dùng **cùng một chuỗi pointer event**. `main` không bị đụng trong bước này.

Người dùng xem xong và xác nhận mốc vẫn là `e6c2330`.

## 4. Phục hồi

Không `reset --hard`, không rewrite, không xoá lịch sử. Toàn bộ 17 commit vẫn
nằm nguyên trong `git log`.

Đường sản phẩm đưa về đúng nội dung `e6c2330`:

```
git checkout e6c2330 -- frontend/src/simulations/domains/geometry frontend/src/styles
git rm <10 module sinh sau mốc>
```

⚠️ **Không dùng 13 lượt `git revert` nối tiếp**, và đây là một lựa chọn có lý
do chứ không phải đi tắt: `git revert` không nhận pathspec, nên mỗi lượt sẽ kéo
theo cả phần tài liệu/công cụ của commit ấy rồi phải gỡ tay — 13 lần, với xung
đột chồng nhau vì các commit sau viết đè lên cùng những vùng mã. Kết quả cây
làm việc **giống hệt nhau**, nhưng cách trên có một bất biến kiểm được bằng máy:

```
git diff e6c2330 HEAD -- frontend/src/simulations/domains/geometry frontend/src/styles
⇒ RỖNG
```

Phạm vi **không** chạm: `backend/**` · `frontend/src/data/**` · mọi tài liệu và
artifact bằng chứng của các wave đã qua (chúng ở lại làm lịch sử).

Hai công cụ đo bị gỡ vì **không chạy nổi** sau khi phục hồi — cả hai đọc
`scene3d-tokens.ts`, và chủ thể chúng đo đã không còn:
`scene3d-d2-gate.mjs` · `scene3d-fidelity-gate.mjs`.
`scene3d-orbit-gate.mjs` **được giữ**: nó không đọc mã sản phẩm.

Test bị gỡ đều là test **của chính hành vi đã phục hồi** (token mockup, nét dày
theo pixel, đường bao khối cong, DPR, thiết diện luỹ tiến, vòng đời quay). Không
test nào bị gỡ để làm xanh một hành vi vẫn còn tồn tại.

## 5. Kiểm chứng

```
vitest                817/817 ✓  — BẰNG ĐÚNG số test ở worktree e6c2330
tsc -b + vite build   ✓
pytest                4821 pass, 2 fail → CẢ HAI do CÂY LÀM VIỆC BẨN lúc đo
                      (`cay_sach: False`), xanh lại sau khi commit
backend                0 byte đổi so với e6c2330
CANDIDATE_HASH         96a9368b50603c79… KHÔNG ĐỔI (92 file)
CACHE_VERSION          95 → 95
dữ liệu hình học       0 byte (`frontend/src/data`, `backend/app`)
```

**Khớp ở mức ĐIỂM ẢNH, không chỉ mức mã nguồn.** Chụp lại P1–P7 và bài thật từ
`main` sau phục hồi rồi so với bản chụp từ worktree `e6c2330`:

| | e6c2330 | main sau phục hồi |
|---|---|---|
| mực p1…p7 | 49452 · 3149 · 37931 · 60127 · 23966 · 39276 · 29262 | **giống hệt** |
| băm bài thật b1/b6/b8/b11 | 9ca7a85508eb · 3e458b110a36 · ec987bbf00b2 · ec987bbf00b2 | **giống hệt** |
| quay | quét 940°, quanh Y 1051°, quanh Z 12° | quét 940°, quanh Y 1052°, quanh Z 12° |

Cổng quay trên bản đã phục hồi: **KHÔNG ĐẠT — `TRUC_TROI` cả ba ca**
(vòng 71–104°, trục 0,545–0,549). Đó là phán quyết **đúng** về sản phẩm đã phục
hồi, không phải cổng hỏng.

## 6. Mất gì, được gì — không giấu

| | trạng thái sau phục hồi |
|---|---|
| **Camera** | **Y-up** (three.js mặc định). Trụ/nón nằm ngang, chóp p1 đọc ra tứ giác dẹt |
| **Quay** | Vẫn quay tự do (quét 940°/một cú kéo) nhưng **quanh trục Y**; cổng quay báo `TRUC_TROI` |
| **Thiết diện từng bước** | **Vẽ đầy đủ ngay**, không hiện dần. Bước 8 ≡ bước 11 |
| **Khớp khung** | Theo **cầu ngoại tiếp** (hình nhỏ hơn thực tế cần) |

**Chức năng MẤT khi phục hồi** — không tồn tại ở `e6c2330`:

- nét dày theo pixel (`Line2`/`LineMaterial`) ⇒ mọi nét về 1 px danh nghĩa
- đường bao khối cong ⇒ cầu/trụ/nón không có nét viền
- nhãn cho thiết diện, đường tròn/elip và trục khối cong
- DPR 2 (màn retina nhận bản 1× phóng to)
- thiết diện hiện dần theo sự kiện `EXTEND`
- bảng token theo mockup; bảng màu quay về **theo nguồn gốc vật**
- bộ giải đặt nhãn (`giaiNhan`) và phép lùi camera thích ứng
- `vatToTrung` (mảng tô một khối chỉ tô một lần)
- hai cổng trình duyệt đo thị giác

**Lỗi BIẾN MẤT**: mọi lỗi do wave mockup/D2 gây ra — gồm cả việc bảng token
trôi khỏi mockup, vì bảng ấy không còn.

**Lỗi CŨ XUẤT HIỆN LẠI** (đều có ở `e6c2330`, đo được trên bản phục hồi):

- **trục quay trôi** — cổng quay `TRUC_TROI` 3/3, trục 0,545–0,549
- **khối nằm nghiêng** do Y-up; p4/p5 nằm ngang
- **khối cong không một nét bao**
- **bảng màu theo nguồn gốc vật** (tím/nâu/cam) thay vì theo vai
- **bước 8 ≡ bước 11** ở bài thật
- mảng tô đậm

```
PRE_MOCKUP_PRODUCT_HEAD       = e6c2330
FIRST_MOCKUP_IMPLEMENTATION   = 7f34286
CURRENT_HEAD                  = (commit của wave này)
PRODUCT_COMMITS_REVERTED      = 13 (hiệu lực; 4 commit docs/công cụ giữ nguyên)
SCENE3D_FILES_RESTORED        = 10 sửa lại + 10 gỡ (+ 2 công cụ gỡ)
BACKEND_CHANGED               = NO (0 byte)
GEOMETRY_PARITY               = dữ liệu và đáp số 0 byte; candidate 96a9368b… không đổi
P1_P7_RESULT                  = 7/7 khớp ĐIỂM ẢNH với e6c2330 (desktop + mobile)
ROTATION_RESULT               = quét 940°, quanh Y 1052° — quay được, quanh TRỤC Y;
                                cổng quay KHÔNG ĐẠT (TRUC_TROI 3/3)
TEST_RESULTS                  = vitest 817/817 · tsc ✓ · build ✓ · pytest 4821 pass
COMMITS_CREATED               = 1
WORKING_TREE                  = sạch
```

`USER_VISUAL_APPROVAL = PENDING` ·
`NEXT_ACTION = USER_REVIEWS_RESTORED_PRE_MOCKUP_STATE`
