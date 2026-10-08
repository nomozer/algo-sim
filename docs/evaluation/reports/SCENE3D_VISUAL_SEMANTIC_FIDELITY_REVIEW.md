# SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW

**Ngày:** 2026-09-09 · **0 lượt gọi model, 0 lượt gọi provider**

Wave này hỏi câu mà wave trước chưa hỏi: **hình trên màn hình có thể hiện đúng
quan hệ hình học không, và có đủ rõ để nhìn ra không.**

```
SCENE3D_VISUAL_SEMANTIC_FIDELITY   PARTIAL

WORLD_SPACE_GEOMETRY_PASS          7/7    (số hữu tỉ chính xác, tolerance = 0)
PLANE_SECTION_RELATION_PASS        3/3    (0/3 ở nền so sánh — chưa có chính sách)
CONCAVITY_VISIBILITY_PASS          1/1
SECTION_VISIBILITY_PASS            KHÔNG THIẾT LẬP ĐƯỢC — xem §6
CAMERA_FRAMING_PASS                7/7    (6/7 ở nền)
DISPLAY_NAME_PASS                  10/12  (10/12 ở nền — KHÔNG đổi, xem §7)
NEGATIVE_MESSAGE_CONSISTENCY       2/2    (0/2 ở nền)
TRACE_AND_STATE_REGRESSION         9/9

APPLICATION_LLM_CALLS              0
REAL_PROVIDER_CALLS                0
FRONTEND_CODE_CHANGED              YES  (renderer · camera · thông báo ca âm)
BACKEND_CODE_CHANGED               NO   (0 byte — xem §7, đã thử rồi HOÀN TÁC)
API_CONTRACT_CHANGED               NO
MODEL_FACING_HASHES_CHANGED        NO
LIVE_ARTIFACTS_CHANGED             NO
CACHE_VERSION_BEFORE/AFTER         94 / 94
CANDIDATE_HASH_BEFORE/AFTER        d72db7c3… / d72db7c3…

FAULT_INJECTIONS                   5 (oracle, 5/5 đỏ đúng chỗ) + 5 (trình duyệt, 2/5)
FRONTEND_TEST_RESULT               790 pass / 53 file, 0 đỏ
BROWSER_E2E_RESULT                 39/41 (nền 34/38) · 18 ảnh · ngoại lệ 0
BUILD_RESULT                       PASS
```

---

## 1. Phân xử trước, sửa sau — và nhánh A đã đóng bằng số học

Ảnh `p7` của wave trước cho thấy mặt phẳng như một tấm vuông trôi bên cạnh hình
nón. Ba cách giải thích, ba tầng sửa khác nhau. Sửa nhầm tầng là chữa đúng triệu
chứng ở sai chỗ, nên nhánh A phải đóng **trước**.

`backend/scripts/scene3d_world_oracles.py` — số **hữu tỉ chính xác**, tolerance
bằng 0, 16 điểm mẫu mỗi đường cong:

```
WORLD_SPACE_GEOMETRY_PASS = 7/7
```

`p7` kiểm được trọn vẹn: mặt phẳng `x + z = 9`, elip tham số hoá thành
`P(t) = (1 − 2cos t, √3 sin t, 8 + 2cos t)` — thoả `x + z = 9` với **mọi** `t`,
và `x² + y² = (c − 2)² = (6 − z/2)²`, tức nằm đúng trên mặt nón, trong đúng đoạn
chiều cao.

⚠️ **Oracle phải mở rộng sang ℚ(√c) để làm được việc ấy.** Bản đầu chỉ lấy mẫu
được khi cả hai bán trục chia cho phương ra số hữu tỉ; `p7` có bán trục nhỏ
`√(1/48)` nên nó **bỏ qua đúng ca ưu tiên cao nhất** và ghi một dấu ✗ trông y hệt
lỗi dữ liệu. Rơi về float là lối thoát sai — khi ấy phải có tolerance, mà
tolerance che đúng lớp lỗi đang đi tìm.

⚠️ **Và oracle từng có một lỗ tự tắt.** Nó ghép thiết diện với mặt phẳng bằng
cách so pháp tuyến bằng nhau, nên phép tiêm *"xoay sai pháp tuyến"* **không đỏ**:
mặt phẳng thôi khớp ⇒ phép kiểm bị BỎ QUA, và oracle im lặng báo đạt. Nay ghép
bằng **phép chứa** — *"trong cảnh có mặt phẳng nào chứa trọn thiết diện không"*.
Sau bản sửa: **5/5** phép tiêm đỏ.

```
ROOT_CAUSES_BY_CASE
  p1  VISUAL_PRESENTATION_GAP   đường vô hạn tham gia auto-fit
  p2  (không lỗi)               đáy lõm đã đọc ra là lõm ở cả nền
  p3  VISUAL_PRESENTATION_GAP   auto-fit tính ở bước 0 ⇒ mặt cầu bị CẮT;
                                miếng mặt phẳng 6×6 nhỏ hơn đường tròn r = 12
  p4  (không lỗi)
  p5  VISUAL_PRESENTATION_GAP   hộp bao nở bán kính DỌC trục ⇒ hình chiếm 21%
  p6  VISUAL_PRESENTATION_GAP   miếng mặt phẳng lệch; + tên hiển thị (§7)
  p7  VISUAL_PRESENTATION_GAP   miếng mặt phẳng RỜI HẲN thiết diện; + tên (§7)
  n1  VISUAL_PRESENTATION_GAP   lời hứa sai trên thẻ từ chối
  n2  VISUAL_PRESENTATION_GAP   thẻ nói hai giọng
```

**Không ca nào là `SCENE3D_PRODUCT_DATA_GAP`, không ca nào là
`FRONTEND_RENDERER_GAP`.** Mọi thứ sửa được đều nằm ở tầng trình bày.

---

## 2. Miếng mặt phẳng — lỗi lớn nhất, và nó đo được bằng số

`PLANE_DISPLAY_SIZE = 6`: một ô vuông **cố định**, đặt tại `plane3.point`.
Nhưng `point` chỉ là **một điểm bất kỳ** trên một mặt phẳng vô hạn.

| ca | tâm miếng | tâm thiết diện | khoảng cách | nửa đường chéo miếng |
|---|---|---|---|---|
| `p7` | (9, 0, 0) | (1, 0, 8) | **11,31** | 4,24 |
| `p6` | (−6, 0, 0) | (0, 0, 12) | **13,42** | 4,24 |
| `p3` | (0, 0, 9) | (0, 0, 9) | 0 | 4,24 *(bán kính thiết diện **12**)* |

Ở `p7` miếng **không chạm tới** thiết diện. Ảnh đọc ra đúng như vậy.

**Quy tắc mới, dùng chung, không nêu tên ca nào** (`khungMatPhang`): chiếu mọi
điểm **có biên** của cảnh xuống mặt phẳng, tâm miếng = tâm hình chiếu, cạnh =
đường kính hình chiếu × lề 1,15.

Sau bản vá — đo bằng chính hàm thuần của sản phẩm, chạy trong trang:

| ca | thiết diện | cách tâm | + bán trục | ≤ nửa cạnh |
|---|---|---|---|---|
| `p3` | `C` | 0,00 | 12,00 | **17,25** ✓ |
| `p6` | `E` | 0,00 | 11,18 | **14,91** ✓ |
| `p7` | `E` | 0,71 | 2,83 | **9,76** ✓ |

`PLANE_SECTION_RELATION_PASS = 3/3` (nền: **0/3** — chính sách chưa tồn tại).

---

## 3. Khung nhìn — hai lỗi độc lập, cùng một triệu chứng

**(a) Auto-fit tính ở bước 0.** Khung nhìn cố ý đứng yên giữa các bước (nếu
không, tua bước biến thành đổi góc máy) — nhưng nó tính từ những gì đang dựng
lúc gọi, tức **bước 0**, khi cảnh mới có vài điểm tự do. Ở `p3`, mặt cầu bán
kính 15 xuất hiện ở bước sau và **tràn ra ngoài khung**, bị cắt cả trên lẫn dưới:
`lề 0px · chiếm 100%`. Sửa: khung nhìn ôm **toàn cảnh** ngay từ đầu — camera vẫn
đứng yên, nhưng đứng ở chỗ nhìn được hình cuối.

**(b) Vật VÔ HẠN tham gia tính khung.** Miếng mặt phẳng và đoạn đại diện của
đường thẳng có cỡ do **chính tầng trình bày** chọn. Để chúng vào thì quyết định
trình bày tự khuếch đại: miếng to ra ⇒ hộp bao to ra ⇒ camera lùi ⇒ hình thật bé
lại. Nay chúng mang `userData.voHan` và bị loại khỏi phép tính.

**(c) Và một lỗi của chính bản vá.** `diemHuuHan` nở bán kính khối cong theo cả
**ba trục toạ độ**, kể cả dọc trục khối: hình nón cao 12 bán kính 5 cho hộp bao
cao **22**, và hình chỉ còn chiếm 21% khung. Bán kính vuông góc với trục nên
phép nở cũng phải vuông góc với trục.

| ca | nền | sau |
|---|---|---|
| `p3` | lề **0px** · chiếm 100% | lề 108px · chiếm 51% |
| `p5` | lề 114px · chiếm 37% | lề 190px · chiếm 33% |
| `p7` | lề 96px · chiếm 42% | lề 114px · chiếm 58% |

`CAMERA_FRAMING_PASS = 7/7` (nền 6/7).

---

## 4. Thiết diện — nét dày theo tỉ lệ cảnh

`THREE.Line` luôn dày đúng **một điểm ảnh**: WebGL bỏ qua `linewidth`. Đo được ở
nền: đường tròn thiết diện của `p3` chiếm **6 điểm ảnh có màu** trên cả khung
1318×545. Về kỹ thuật là "có vẽ"; với người học là không nhìn thấy.

Sửa: vành elip dựng thành **dải hai mép** (và đường tròn thành `RingGeometry` có
bề dày), dày theo `SECTION_STROKE_RATIO × đường kính cảnh` — cùng một hình, phóng
to hay thu nhỏ thì nét vẫn cân đối, và không phụ thuộc độ phân giải.

Cộng thêm chính sách `VAT_LIEU_THIET_DIEN = { depthTest: false }` +
`renderOrder`: khối vẫn tô bóng như cũ (hình vẫn đọc ra là vật đặc), chỉ thiết
diện thôi bị kiểm chiều sâu — nên nửa vòng phía xa không bị khối nuốt.

---

## 5. Thông báo ca âm — một thẻ, một giọng

**Nền:** `n1` đọc được *"Dạng bài này hệ có mô phỏng"* cho một bài
`OUT_OF_SCOPE`; `n2` vừa nói *"nằm ngoài năng lực"* vừa mang thân thông điệp
khuyên diễn đạt lại.

`geometry_generation_failed` nhận **cả** những ca bị chặn TRƯỚC cổng phủ
(`error_code = null`, đúng `n1`), tức những ca hệ **không biết** dạng bài có nằm
trong bao đóng không. Khẳng định một điều mình không biết, về phía có lợi cho
mình, là đúng thứ ranh giới R0 dựng ra để cấm — chỉ khác là lần này lời sai nằm
trên bề mặt học sinh chứ không trong một đáp số.

Nay: `error_code = requested_operation_uncovered` → nói giới hạn năng lực;
`error_code` vắng → **câu có điều kiện**, vẫn hữu ích mà không hứa liều.

`NEGATIVE_MESSAGE_CONSISTENCY = 2/2` (nền 0/2).

⚠️ **Chi tiết kỹ thuật mở xem riêng: CỐ Ý KHÔNG LÀM.** Bất biến #10 của kho cấm
định danh kỹ thuật lên bề mặt học sinh, và sản phẩm không có khay developer nào.
Dựng một khay như vậy là một tính năng mới, ngoài phạm vi wave này.

---

## 6. `SECTION_VISIBILITY` — KHÔNG thiết lập được, và vì sao phải nói ra

Đây là chỗ wave này **không** chứng minh được điều nó định chứng minh.

Chỉ số đầu là *"≥ N điểm ảnh màu thiết diện"*. Con số N là **tôi bịa**: nó phụ
thuộc độ phân giải, bề dày nét và mức thu phóng, tức phụ thuộc mọi thứ trừ điều
cần hỏi. Thay bằng một chỉ số không phụ thuộc tỉ lệ — *"hộp bao lớp thiết diện ≥
25% hộp bao cả hình"* — thì nó **đạt cả ở nền** (`p3`: 0,924 với 1083 điểm ảnh),
vì ở nền mặt cầu tràn kín khung nên mọi thứ đều to.

Nói thẳng: **hai chỉ số đều không cô lập được sự khác biệt mà `depthTest` tạo
ra.** Thứ đã chứng minh được là (a) quan hệ mặt phẳng ↔ thiết diện, (b) khung
nhìn, (c) oracle không gian thế giới, và (d) **bằng chứng ảnh** — so
`screenshots/before/p3` với `screenshots/after/p3` thì thấy rõ nửa vòng xa nay
hiện đủ. Bằng chứng ảnh là bằng chứng thật, chỉ không phải bằng chứng **tự
động**, nên nó không được ghi thành một con số PASS.

---

## 7. Tên hiển thị — đã sửa được, rồi HOÀN TÁC có chủ đích

Nguyên nhân định vị chính xác: `_DANH_TU_NGAN` trong
`backend/app/simulation/semantic_program/display_names.py` **thiếu `ellipse3`**
từ wave thiết diện xiên. Bảng ấy là lối rơi cuối của `goi_ngan`, nên thiếu một
kiểu là kiểu ấy mất tên trong **mọi** câu nhắc tới nó — và mất im lặng.

Bản vá hai dòng (`"ellipse3": "elip"` + `"ellipse3": "Elip"`) cho kết quả **đúng
bảng §6 của đặc tả**: `Diện tích «đối tượng»` → **`Diện tích elip`**.

**Rồi hoàn tác.** Lý do, đo được:

```
CANDIDATE_HASH  d72db7c3… → ff508b36…
test_C2_policy_tro_dung_corpus_va_candidate  ĐỎ
    assert nguong["candidate_hash"] == F.measured_system_hash()[0]
```

Hợp đồng đo `thesis_final_acceptance_policy.json` — văn bản **đăng ký trước**,
`created_before_live_run = true` — ghim `candidate_hash = d72db7c3…`, và một
guard đòi nó bằng candidate hiện tại. Muốn giữ bản vá thì phải **viết lại
candidate_hash trong một văn bản đăng ký trước cho khớp mã sửa SAU lượt đo**. Đó
đúng thứ dự án tồn tại để chặn: nó sẽ khiến hợp đồng khai rằng lượt đo cuối đã
đo một bản mã mà nó chưa từng đo.

Đặc tả wave cho phép sửa `display_names.py` (§6, §10) nhưng không lường trước
ràng buộc này. Theo §10 — *"Nếu … hash thay đổi ngoài dự kiến, dừng và báo danh
tính bị ảnh hưởng trước khi tiếp tục"* — tôi dừng, hoàn tác, và báo. `backend/app`
giữ **0 byte** thay đổi; candidate vẫn `d72db7c3…`.

```
FOLLOW_UP = DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND
  · sửa hai dòng đã biết chính xác;
  · đóng băng lại candidate ở commit riêng;
  · và TRƯỚC đó quyết định hợp đồng đo nên ghim candidate LÚC ĐO (lịch sử) hay
    candidate HIỆN TẠI — hai ngữ nghĩa khác nhau, và guard hiện chọn cái thứ hai.
  · cùng lượt: `curved_solid` nên lấy danh từ theo `curved_kind` (hình trụ /
    hình nón) thay vì "khối cong"; `thong_tin` hiện KHÔNG chở `curved_kind` nên
    phải luồn thêm một trường.
```

---

## 8. Phép tiêm lỗi — 5/5 ở oracle, 2/5 ở trình duyệt

| phép tiêm | tầng | kỳ vọng | thực tế |
|---|---|---|---|
| dời tâm elip khỏi mặt phẳng | oracle | đỏ | ✓ đỏ ở p6, p7 |
| xoay sai pháp tuyến mặt phẳng | oracle | đỏ | ✓ đỏ ở p6, p7 |
| đổi bán trục nhỏ của elip | oracle | đỏ | ✓ đỏ ở p6, p7 |
| đổi bán kính khối cong | oracle | đỏ | ✓ đỏ ở p3–p7 |
| làm phương trục thôi trực giao | oracle | đỏ | ✓ đỏ ở p6, p7 |
| đổi một đáp số `72 → 73` | trình duyệt | đỏ | ✓ |
| dời `plane3.point` **dọc** mặt phẳng 500 đơn vị | trình duyệt | **vẫn xanh** | ✓ |
| xoay sai pháp tuyến mặt phẳng | trình duyệt | đỏ | **✗ không đỏ** |
| phóng bán trục elip vượt miếng | trình duyệt | đỏ | **✗ không đỏ** |
| làm đáy LỒI | trình duyệt | đỏ | **✗ không đỏ** |

Ba phép không đỏ là **phát hiện, không phải sự cố**:

- Hai phép đầu không đỏ **vì bản vá làm đúng việc**: miếng mặt phẳng tự co giãn
  theo vùng hình học, nên xoay pháp tuyến hay phóng bán trục thì miếng vẫn phủ.
  Cổng phát hiện *"mặt phẳng có thật sự chứa thiết diện không"* là **oracle**, và
  oracle đỏ ở cả hai. Phép kiểm ở trình duyệt hỏi câu hẹp hơn: *"miếng có phủ
  không"*.
- Phép thứ ba cho thấy chỉ số lõm (diện tích/bao lồi) **không nhạy** như tôi
  tưởng: đổi một đỉnh phản xạ thành lồi vẫn cho tỉ lệ < 0,97, vì răng cưa và mép
  vẽ cũng làm tỉ lệ tụt.

Phép **thứ bảy** là phép nói lên bản vá rõ nhất: dời `plane3.point` đi 500 đơn vị
dọc mặt phẳng **không đổi gì cả**. Trước bản vá, chính phép ấy đẩy miếng ra khỏi
màn hình.

---

## 9. Cổng đã chạy

| cổng | kết quả |
|---|---|
| `scene3d_world_oracles.py` | **7/7**, tolerance 0 · `--faultcheck` **5/5** |
| `certify-scene3d-visual-fidelity.mjs --nhan after --faultcheck` | **39/41** · 9 ảnh · ngoại lệ 0 |
| … `--nhan before` (nền, trên mã chưa vá) | **34/38** |
| `npx vitest run` | **790 pass / 53 file** — 0 đỏ |
| `npm run build` | PASS |
| `pytest -q` | **4781 pass, 1 skip, 1 deselect** — 0 đỏ, cây sạch @ `f44756a` |
| `replay_demo_cases.py` | **5/5** · `REDUCED_CHAIN 1/1` |
| `audit_demo_crash_surface.py` | **6/6** biên đúng kiểu · ném ra ngoài **0** |
| `freeze --verify` | exit 0 — 92 file, `d72db7c3…` |
| `lock_cache_identity --verify` | exit 0 @ v94 |
| `git diff --check` | sạch |
| băm ảnh | 9/9 ảnh ĐỔI giữa before và after |

---

## 10. Reused / created

**Reused**: `BrowserSession` + `interceptJson` (thêm ở wave trước) ·
`evidence.provenance` · fixture 9 ca · `khungNhinVua` · `objectsAt` ·
`chiaTamGiac` · `polygon-triangulate`.

**Created**: `backend/scripts/scene3d_world_oracles.py` ·
`frontend/scripts/certify-scene3d-visual-fidelity.mjs` ·
`docs/SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW.md` · bốn artifact JSON + 18 ảnh.

**Modified**: `scene3d-model.ts` (`diemHuuHan`, `khungMatPhang`,
`duongKinhCanh`, ba hằng) · `scene3d-view.tsx` (miếng mặt phẳng, dải thiết diện,
`userData.voHan`, auto-fit toàn cảnh) · `SimulationWorkspace.tsx` (câu gợi ý ca
âm) · `product-envelope-rendering.test.tsx` (theo chính sách mới).

**Duplicate check**: không script nào đang đo điểm ảnh của canvas 3D;
`capture-*.mjs` chụp ảnh nhưng không phân tích, `audit-layout.mjs` đo bố cục DOM
chứ không đo nội dung khung vẽ.

---

```
VISUAL_DEMO_FIDELITY_ON_FROZEN_CASES = PARTIAL
PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED
NEXT_ACTION = THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW
FOLLOW_UP = DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND
FOLLOW_UP = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

**PARTIAL, không phải PASS** — và ba lý do đều nêu tên ở trên: `SECTION_VISIBILITY`
chưa có phép đo tự động cô lập được (§6); `DISPLAY_NAME_PASS` giữ 10/12 vì bản vá
đã hoàn tác có chủ đích (§7); ba phép tiêm ở tầng trình duyệt chưa đỏ (§8). Điều
kiện PASS của đặc tả đòi cả ba, nên ghi PASS ở đây là tự cho điểm.
