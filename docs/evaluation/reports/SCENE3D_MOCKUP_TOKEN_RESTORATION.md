# SCENE3D_MOCKUP_TOKEN_RESTORATION (2026-09-12)

Người dùng mở bộ mockup `p1`–`p7` đã chốt, đặt cạnh sản phẩm, và nói: *"tôi
muốn bạn làm như mockup ở hình trên các lần trước đã chốt rồi ý bạn toàn sửa
đâu đâu thôi kiểm tra kĩ lại giúp tôi"*.

Kiểm lại thì nhận xét ấy đúng, và đúng theo một cách tệ hơn tôi tưởng.

## 1. Không dòng nào trong bảng thị giác còn khớp mockup

Chú thích in ngay trong mockup đã ghi thang bậc: *"cạnh thấy 2,8 px · cạnh
khuất 1,6 px nét đứt · thiết diện 3,5 px"*. Bảng token trong sản phẩm ghi
2,4 / 1,4 / 3,2.

| vai | mockup (thuộc tính SVG) | sản phẩm trước wave này | lệch |
|---|---|---|---|
| nền khung | `#FAF9F7` phẳng | `#ffffff`→`#f6f5f4`, gradient hướng tâm | sai màu + thêm một tầng nền |
| cạnh thấy | `#1F1F1F` · 2,8 px | `#1a1a1a` · 2,4 px | −0,4 px |
| cạnh khuất | `#7D7975` · 1,6 px · đứt 7/5 | `#6b6560` · 1,4 px | −0,2 px, tối hơn |
| thiết diện thấy | `#D95A43` · 3,5 px | `#cf4726` · 3,2 px | −0,3 px |
| thiết diện khuất | **cùng `#D95A43`**, mờ 0,55 · 2,2 px | `#e79a84` đặc · 2,0 px | một màu mockup không có |
| đường dựng | `#99948F` · 1,2 px | `#a39c94` · 1,0 px | −0,2 px |
| mặt phẳng | viền `#77736F` 1,2 px mờ 0,85 · tô 0,07 | viền `#cdc7bf` 0,9 px · tô 0,022 | tô còn ⅓ |
| tô khối | 0,07 | 0,035 | một nửa |
| tô thiết diện | 0,14 | 0,15 | ~khớp |
| chấm điểm | `r = 4` (đk 8 px) + vành giấy 1,4 px; khuất mờ 0,45 | đk 4,4 px, không vành, không phân biệt khuất | bé gần một nửa |
| nhãn | 15 px · 600 · `#171717` · viền `#FAF9F7` 3,2 | 15 px · 600 · `#1f1f1f` · viền `#ffffff` | khớp hình, lệch sắc |

Ba cổng trình duyệt vẫn xanh suốt quá trình ấy. Không phải vì chúng hỏng, mà
vì chúng **đọc token** — và token chính là thứ đã trôi. Cổng thị giác thậm chí
còn ghi cứng *"token D2 = 2,4 px"* kèm dải `1,6 – 3,4`: một bản sao thứ hai của
thiết kế, và bản sao ấy che đúng lượt trôi mà nó lẽ ra phải bắt.

**Luật rút ra: mockup là thẩm quyền, token chỉ là bản chép.** Test phải khoá
đúng con số mockup, không khoá một tính chất suy ra từ chúng.

### Lý lẽ của vòng trước, và vì sao nó vẫn sai

Không phải vòng ấy đổi bừa. Nó có lý lẽ đo được cho mỗi thay đổi:

- *"Δ màu thiết diện thấy/khuất bằng 0 nên nét đứt 2 px đọc gần như nét liền"* —
  mockup cố ý giữ chung màu và tách bằng **độ mờ 0,55 + nét đứt**, vì mắt phải
  đọc ra *"vẫn là đường thiết diện, đang nằm sau khối"*, không phải *"một vật
  khác"*.
- *"Ba lớp tô cộng dồn (0,07+0,07+0,14) đọc ra như vết bẩn"* — chỗ cộng dồn có
  thật (xem §2), nhưng cách chữa là sửa chỗ cộng dồn, không phải hạ từng lớp.
  Hạ mảng tô là mất luôn cảm giác KHỐI ĐẶC.

Cả hai đều là tranh luận với một bản đã duyệt, được ghi vào mã dưới dạng một
sự thật.

## 2. Mảng tô đậm hơn mockup vì BA nguyên nhân, không nguyên nhân nào ở token

Sau khi chép lại đúng số mockup, mảng tô **vẫn** đậm hơn. Đo trên ảnh sản phẩm
1440×900 (mockup cho đúng `rgb(234,233,231)` ở mọi ca, alpha hiệu dụng 0,073):

```
p5 sản phẩm  rgb(224,223,221)  alpha 0,119     p2 sản phẩm  rgb(212,210,209)  alpha 0,174
```

Một **cửa sổ chứng** đã tách được ba nguyên nhân: đặt tô = 0,5 rồi đo lại, vì
câu trả lời đúng đã biết trước.

**(a) Vật liệu có chiếu sáng.** Lượt đo đầu trả về `rgb(107,105,102)` — **tối
hơn cả chính màu tô** `#77736F`. Một lớp phủ không bao giờ ra được như thế, nên
thủ phạm không phải số lớp. Thủ phạm là `MeshStandardMaterial` +
`AmbientLight(0,75)`: mặt quay khỏi đèn chỉ nhận 0,75 lượng sáng, nên màu chạm
khung tối hơn token, và tối bao nhiêu thì tuỳ hướng mặt. Mockup không có đèn —
mỗi mảng là một `<polygon fill fill-opacity>`, một wash phẳng. Năm mảng tô
chuyển sang `MeshBasicMaterial`; hai nguồn sáng gỡ hẳn vì không còn vật liệu
nào đọc tới.

⚠️ Một giả thuyết đã bị bác bằng thí nghiệm trước đó: `side: DoubleSide` khiến
mặt sau cũng tô. Đổi sang `FrontSide` **không đổi một điểm ảnh nào** — lớp
chiều sâu đã loại mặt sau từ trước. Ghi lại để lần sau không ai đi lại đường đó.

**(b) Hai vật trùng khít trong một trace hợp lệ.** Sau khi bỏ chiếu sáng, cửa
sổ chứng trả về đúng `1 − (1 − 0,5)² = 0,75`: **chính xác hai lớp**. Ca `p5` có
cả `khối nón` (đỡ nghĩa vụ thể tích) lẫn `hình nón` (đỡ nghĩa vụ diện tích xung
quanh) với cùng `radius_sq`/`height_sq`/`apex_or_top`; `p4` cũng vậy. Không sửa
được bằng phép kiểm chiều sâu (hai mặt trùng khít có cùng độ sâu) và không sửa
ở backend (hai vật ấy là dữ liệu đúng). Luật nằm ở tầng trình bày: **mảng tô là
thuộc tính của KHỐI, không phải của mỗi cái tên trỏ tới khối ấy** —
`vatToTrung` ở `scene3d-model.ts`.

**(c) Mặt được nêu tên tô ở mức thiết diện.** Đáy ngũ giác của `p2` là
`type: "face"` và đang tô 0,14 — mức dành cho thiết diện — rồi chồng lên thân
khối 0,07. Hạ về mức khối 0,07. ⚠️ Đây là **suy luận, không phải số chép**: bộ
mockup không có ca nào nêu tên một mặt, nên không có ô nào để đối chiếu.

### Sau khi sửa

```
p5  rgb(234,233,232)  so với mockup rgb(234,233,231)   lệch 1 mức
p2  rgb(229,227,225)  — còn một wash rất nhạt của đáy có tên, đúng như thiết kế
```

## 3. Bằng chứng

```
vitest                924 → 931 (thêm 7 test)     tsc + vite build   xanh
cổng QUAY             ĐẠT 3/3 (vòng 428–441°, ‖trục‖ 0,999–1,000, 0 cấp phát)
cổng THỊ GIÁC         ĐẠT 10/10 — bề dày trung vị 2,35–2,81 px (token 2,8)
cổng D2               24/28 ô (trước wave này 22/28; p6 và p3@dpr2 hết lỗi)
phép tiêm lỗi         4/4 đã chứng ĐỎ, cây khôi phục nguyên trạng
CANDIDATE_HASH        96a9368b50603c79… KHÔNG ĐỔI (92 file)
CACHE_VERSION         95 → 95        BACKEND_CHANGED = NO     0 byte backend
GEOMETRY_MODIFIED     false — không chạm toạ độ, đáp số, trace hay thứ tự sự kiện
```

Cổng thị giác nay đo bề dày **lệch so với chính token** (`CANH_THAY_SAI_SO
= 0,6`) thay vì so với một dải ghi cứng, nên nó tự đi theo mockup và chỗ duy
nhất giữ con số vẫn là `scene3d-tokens.ts`.

Ảnh đối chiếu hai cột: `D:\tmp\algosim-mockup-restore\DOI_CHIEU_MOCKUP_VS_SAN_PHAM.png`

## 4. Còn lại, đã khai

- **Bốn ô cổng D2 `NHAN_QUA_SAT_NET`**: `p7` để bàn (kc 5,00 và 5,59; cần 6) ·
  `p1` điện thoại (kc 3,00 và 2,00; cần 4). Không nhãn nào bị giấu, không
  ngưỡng nào bị nới ngầm.

  ⚠️ Và **chính ngưỡng ấy nghiêm hơn mockup**: trong `p4`/`p6`, nhãn `OK` nằm
  ĐÈ lên đường dựng, viền giấy 3,2 px cắt nét ra làm đôi cho chữ đọc được.
  Mockup cho phép đè; luật "cách mực ≥ 6 px" là luật tôi tự đặt ở vòng trước.
  **Cần người dùng quyết**: theo mockup (cho đè, dựa vào viền giấy) hay giữ
  ngưỡng nghiêm.

- **Khung vẽ 1318×610 so với mockup 1440×900.** Hình nhỏ hơn và có khoảng trống
  hai bên. Đã đo ở wave trước: không góc camera nào sửa được, vì hộp bao bài là
  2×2×4 (tỉ lệ chiếu tốt nhất 0,64) trong khi canvas là 2,42. Muốn giống mockup
  thì phải đổi **tỉ lệ khung**, tức đổi bố cục trang, không phải camera.

- **Bước 11/11 vẫn trùng byte với bước 10** — nợ cũ, chưa động tới ở wave này.

`USER_VISUAL_APPROVAL = PENDING` · `NEXT_ACTION = USER_REVIEWS_MOCKUP_PARITY`
