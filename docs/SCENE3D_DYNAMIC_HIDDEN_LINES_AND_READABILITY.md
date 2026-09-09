# SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY

**Ngày:** 2026-09-09 · **0 lượt gọi model, 0 lượt gọi provider**

```
DYNAMIC_HIDDEN_LINES            PASS
OCCLUSION_CLASSIFICATION        PASS      3/3 ca, oracle ĐỘC LẬP
RASTER_LINE_STYLE               PASS      ngưỡng hiệu chỉnh từ phép tiêm — xem §4
VISUAL_REVIEW                   ACCEPTABLE  (người kiểm: tác giả wave; ảnh ở §7)
CURVED_SOLID_READABILITY        PASS      khối nay đọc ra mặt trước/mặt sau
SECTION_READABILITY             PASS      cung khuất còn đọc được, ở dạng đứt
PLANE_PATCH_FIT                 PASS      3/3 (giữ nguyên từ wave trước)
CAMERA_AND_TRACE_REGRESSION     PASS      9/9 ca, 0 hồi quy

EXACT_VALUES_UNCHANGED          12/12
NEGATIVE_MESSAGE_REGRESSION     0        (2/2 vẫn nhất quán)
APPLICATION_LLM_CALLS           0
BACKEND_CODE_CHANGED            NO       (0 byte dưới `backend/app`)
LIVE_ARTIFACTS_CHANGED          NO
FRONTEND_IDENTITY               commit `<HEAD wave này>` · xem §8
CANDIDATE_HASH_BEFORE/AFTER     d72db7c3… / d72db7c3…
CACHE_VERSION_BEFORE/AFTER      94 / 94

FAULTS_DETECTED / FAULTS_INJECTED   6 / 6
TEST_RESULTS                    vitest 798 pass · pytest xem §8 · build PASS
                                hidden-lines 23/23 · visual-fidelity 39/41
                                product-ui 66/66 · world-space oracle 7/7
SCREENSHOT_AND_VIDEO_PATHS      §7
WORKING_TREE                    sạch
```

---

## 1. Trước wave này KHÔNG CÓ hidden-line nào cả

Không phải "làm chưa tốt" — **chưa từng có**. Mọi khối trong renderer khai
`depthWrite: false`: khối đa diện, khối cong, mặt, miếng mặt phẳng. Không ai ghi
chiều sâu thì không gì che được gì, và một cạnh nằm sau quả cầu vẽ y hệt cạnh
nằm trước nó.

Wave trước còn đi xa hơn theo hướng ngược: thiết diện mang `depthTest: false` để
"luôn nhìn thấy được". Nó đạt mục tiêu ấy bằng cách vẽ đè lên mọi thứ — và khi
mọi phần đều vẽ đè thì phần thấy và phần khuất hiện y hệt nhau. Với hình học
không gian, *"đoạn này nằm trước hay sau khối"* không phải chi tiết trang trí;
đó là thông tin chính.

## 2. Giải pháp nhỏ nhất phù hợp renderer này

Hai mảnh, không mảnh nào cần một phép hình học mới:

**① Lớp chiều sâu riêng.** Mỗi khối THẬT (đa diện, khối cong) kèm một bản sao
vô hình chỉ ghi chiều sâu (`colorWrite: false, depthWrite: true`), dùng **chung
hình học** với khối. Miếng mặt phẳng, nhãn và lưới **không** có bản sao ấy —
chúng là vật minh hoạ và không được che gì.

**② Vẽ hai lượt cho mỗi đường.** Lượt một `depthFunc: LessEqualDepth` (phần
THẤY, nét liền); lượt hai `GreaterDepth` + nét đứt (phần KHUẤT). GPU quyết định
theo **từng điểm ảnh**, nên một cạnh tự chia thành nhiều đoạn thấy/khuất, và
xoay camera thì phân loại đổi theo — **không có cache nào để lỗi thời**.

Bản sao chiều sâu là chi tiết TRÌNH BÀY: vô hình, không bắt chuột, không vào
hộp bao khung nhìn, không mang id ngữ nghĩa, không vào `final_memory`. Ba đường
nó có thể rò ra đều bị test khoá.

Nét đứt cho **vành thiết diện** không dùng vật liệu nét đứt (three.js không hỗ
trợ cho mesh) mà **bỏ đoạn xen kẽ** trên chính vành đã chia sẵn — nên chu kỳ đứt
bám đường cong thay vì bám độ dài chiếu.

## 3. Ba lỗi phải gỡ mới ra được kết quả, và cả ba đều phụ thuộc GÓC NHÌN

Đây là phần đáng ghi nhất: cả ba lỗi đều **vô hình trong một ảnh tĩnh ở một
góc**, và cả ba chỉ lộ ra khi so oracle với điểm ảnh ở nhiều góc.

**(a) `polygonOffsetFactor` co giãn theo ĐỘ DỐC.** Với một vành nằm trong mặt
cắt dốc — đúng `p3` và `p7` ở góc mặc định — độ dốc lớn khuếch đại độ lệch tới
mức cả vành thắng phép kiểm chiều sâu, và thiết diện lại vẽ liền toàn bộ y như
thời `depthTest: false`. Triệu chứng: `p7` **0 lần đổi nét** ở góc mặc định,
còn `p3` chỉ hiện nét đứt **sau khi xoay**. Sửa: `factor: 0`, giữ `units` thuần.

**(b) Lớp chiều sâu khai `transparent: true`.** Hàng đợi trong suốt còn sắp theo
**khoảng cách** chứ không chỉ `renderOrder`, nên ở một số góc lớp chiều sâu ghi
SAU khi vành đã hỏi — lượt "thấy" vẫn vẽ trên cung khuất.

> **Chẩn đoán quyết định:** tô tạm lượt khuất **màu đỏ** rồi chụp `p3` ở góc mặc
> định. Ảnh cho thấy ĐỎ và HỔ PHÁCH **chồng nhau trên cùng một cung** — tức cả
> hai lượt cùng vẽ. Không có phép thử ấy thì triệu chứng ("cung khuất vẫn liền")
> trỏ nhầm sang phép kiểm chiều sâu, sang độ lệch, hoặc sang bộ đo.

Sửa: lớp chiều sâu **đục**. Hàng đợi đục luôn chạy trước toàn bộ hàng đợi trong
suốt, nên chiều sâu chắc chắn có mặt trước khi bất kỳ đường nào hỏi.

**(c) Nét đứt quá dày.** 24 nét trên một vành ~120px (`p7`) cho khe đứt ~2,5px —
không đọc ra là nét đứt, và cũng không đo được. Chu kỳ nay 4 đoạn (2 vẽ, 2 bỏ).

## 4. Chứng minh hai tầng, và một ngưỡng phải hiệu chỉnh

**Tầng A — phân loại, oracle ĐỘC LẬP.** Ba thiết diện nằm **trên mặt** khối lồi
(đã chứng minh ở `scene3d_world_oracles.py`, tolerance 0), nên:

```
thấy  ⟺  n̂(Q) · (mắt − Q) > 0
```

Hình học thuần, tính từ toạ độ backend gửi. Không đọc cờ nào của renderer, không
đọc buffer chiều sâu, không gọi `Raycaster`.

**Tầng B — dạng nét trên canvas**, đo tại đúng vị trí oracle chỉ ra.

| ca | đoạn THẤY | đoạn KHUẤT | đổi vai sau xoay |
|---|---|---|---|
| `p3` mặt cầu | 100% liền · 0 lần đổi | 80% · 6 lần đổi | 41/72 |
| `p6` hình trụ | 100% liền · 0 lần đổi | 62% · 14 lần đổi | 45/72 |
| `p7` hình nón | 100% liền · 0 lần đổi | 79% · 4 lần đổi | 50/72 |

⚠️ **Ngưỡng "nét đứt" phải hiệu chỉnh, và lý do là một phép tiêm lọt lưới.**
Tiêu chí đầu chỉ đòi *"đổi ≥ 2 lần và tỉ lệ trong 0,1–0,95"*. Phép tiêm *"vẽ mọi
phần bằng nét liền"* **lọt qua**: khi ấy cung khuất chẳng vẽ gì cả, chỉ còn răng
cưa rải rác, ra 15–37% với 2 lần đổi — và tiêu chí đọc "thưa" thành "đứt". Hai
quần thể đo được tách bạch:

```
nét đứt THẬT        62 %  69 %  79 %  80 %   (14, 10, 4, 6 lần đổi)
tiêm "vẽ liền hết"  15 %  32 %  37 %         (2 lần đổi)
```

Vạch đặt ở **0,5**: một nét đứt thật vẽ quá nửa chiều dài cung; một cung không
được vẽ thì không. Sau khi đặt vạch: nền **20/21**, tiêm **15/21** với cả ba
cung khuất đỏ.

⚠️ **Và một phép kiểm xoay RỖNG NGHĨA đã phải bỏ.** Bản đầu so cờ nét tại đúng
các vị trí điểm ảnh cũ sau khi xoay, rồi mừng vì 69/72 điểm "đổi". Nhưng xoay
xong đường cong đã đi chỗ khác — phép ấy đo *hình có dịch không*, một điều hiển
nhiên. Nay: **tính lại camera sau xoay** (OrbitControls đổi phương vị đúng
`2π·dx/clientHeight`; damping đổi đường đi chứ không đổi điểm đến), chạy lại
oracle trên chính các điểm thế giới ấy, kèm **cổng tự-kiểm** — camera dự đoán
sai thì điểm mẫu rơi ra ngoài đường và "đoạn thấy vẫn liền" tụt xuống ngay.

## 5. Phép tiêm lỗi — 6/6 bị bắt

| phép tiêm | tầng bắt được | kết quả |
|---|---|---|
| vẽ mọi phần bằng nét liền (bỏ lượt khuất) | cấu trúc + **điểm ảnh** | 3 test đỏ · raster 15/21 |
| đảo phần thấy và phần khuất | cấu trúc | 1 test đỏ |
| mất lớp che khuất | cấu trúc | 3 test đỏ |
| bỏ `polygonOffset` (nhấp nháy) | cấu trúc | 1 test đỏ |
| khôi phục miếng mặt phẳng cố định, lệch thiết diện | điểm ảnh | 3 ca đỏ |
| *(bất biến)* dời `plane3.point` 500 đơn vị **dọc** mặt phẳng | điểm ảnh | **vẫn xanh**, đúng kỳ vọng |

Tất cả xanh lại sau khôi phục.

⚠️ **Phép tiêm thứ năm ban đầu làm cổng TỰ TẮT chứ không đỏ**: `khungMatPhang`
trả `null` ⇒ không còn cặp nào để so ⇒ phép kiểm bị bỏ qua và báo 38/38. Cùng
lớp lỗi đã sửa ở oracle không gian thế giới. Nay cảnh **có** mặt phẳng và **có**
thiết diện mà không tính được miếng là **đỏ**.

## 6. Đọc được hơn ở đâu

- **Khối cong** nay đọc ra mặt trước / mặt sau: lớp chiều sâu làm nửa gần đậm
  hơn nửa xa, thay vì một khối mờ đều không có chiều.
- **Thiết diện** vẫn nổi, nhưng nay *nói thêm một điều*: phần nào đang ở trước
  khối, phần nào ở sau. Trước wave này nó chỉ nói "có một đường tròn ở đây".
- **Đường thẳng vô hạn** (`p1`, đường `BD`) cũng hai lượt: đoạn chui vào trong
  khối chóp nay đứt.

## 7. Ảnh và chuỗi khung

```
docs/evaluation/geometry/scene3d-hidden-lines/screenshots/
  p3_mat_cau_va_thiet_dien_tron-mac-dinh.png   ← cung trái LIỀN, cung phải ĐỨT
  p3_mat_cau_va_thiet_dien_tron-sau-xoay.png
  p6_thiet_dien_elip_cua_hinh_tru-{mac-dinh,sau-xoay}.png
  p7_thiet_dien_elip_cua_hinh_non-{mac-dinh,sau-xoay}.png
  p1_chop_thiet_dien_khoang_cach-mac-dinh.png  ← hồi quy
  p2_chop_day_ngu_giac_lom-mac-dinh.png        ← hồi quy
  xoay/<case_id>/khung-01..06.png              ← CHUỖI KHUNG khi kéo xoay
```

`VISUAL_REVIEW = ACCEPTABLE`, người kiểm là tác giả wave, bằng cách mở từng ảnh
ở trên. Đó là bằng chứng hợp lệ cho **chất lượng trình bày** và nó **không** được
đổi tên thành một phép kiểm tự động — hai kết luận tự động là
`OCCLUSION_CLASSIFICATION` và `RASTER_LINE_STYLE`.

## 8. Danh tính, phạm vi và cổng

Giữ nguyên **0 byte**: `backend/app/**`, prompt và model-facing schema, corpus,
policy, manifest lượt live, raw artifact, scoring correction, đáp số,
`CACHE_VERSION = 94`, candidate `d72db7c3…`.

**Đổi (chỉ frontend trình bày):** `scene3d-view.tsx` (lớp chiều sâu, hai lượt
vẽ, vành đứt, độ lệch chiều sâu) · `scene3d.test.tsx` (helper đếm tam giác bỏ
lớp chiều sâu) · `browser-runner.mjs` (chờ trang có điều kiện) ·
`certify-scene3d-visual-fidelity.mjs` (cổng thôi tự tắt).

**Thêm:** `scene3d-hidden-lines.test.tsx` · `certify-scene3d-hidden-lines.mjs` ·
artifact `docs/evaluation/geometry/scene3d-hidden-lines/`.

| cổng | kết quả |
|---|---|
| `certify-scene3d-hidden-lines.mjs` | **23/23** · 8 ảnh + 18 khung xoay · ngoại lệ 0 |
| `certify-scene3d-visual-fidelity.mjs --nhan after` | **39/41** (không hồi quy) |
| `certify-product-ui-rendering.mjs` | **66/66** (không hồi quy) |
| `scene3d_world_oracles.py` | **7/7**, tolerance 0 |
| `npx vitest run` | **798 pass / 54 file** — 0 đỏ |
| `npm run build` | PASS |
| `pytest -q` | xem §9 |
| `freeze --verify` · cache identity | exit 0 · `d72db7c3…` · v94 |
| `git diff --check` | sạch |

---

```
REMAINING_LIMITATIONS
  · DISPLAY_NAME_PASS giữ 10/12 — thẩm quyền tên chưa đổi (nợ riêng).
  · Nét khuất của KHỐI ĐA DIỆN dùng `LineDashedMaterial`, chu kỳ theo ĐỘ DÀI
    THẾ GIỚI: thu phóng rất sâu thì mật độ nét đổi. Đọc được ở dải thu phóng
    thường, chưa đo ở dải cực trị.
  · Oracle pháp tuyến chỉ đúng cho khối LỒI. Thiết diện của khối đa diện chưa có
    oracle độc lập tương đương; phần ấy dựa vào cổng cấu trúc và ảnh.
  · `VISUAL_REVIEW` do tác giả wave kiểm, không phải người thứ hai.

NEXT_ACTION = THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW
FOLLOW_UP   = DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND
FOLLOW_UP   = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

⚠️ Wave trước vẫn là **PARTIAL** — bản này không chuyển nó thành PASS. Thứ được
kết luận PASS ở đây là **hợp đồng hiển thị mới** (`DYNAMIC_HIDDEN_LINES`), đã
kiểm bằng oracle độc lập, đo điểm ảnh và 6/6 phép tiêm.
