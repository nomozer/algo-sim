/**
 * scene3d-tokens.ts — NGÔN NGỮ THỊ GIÁC, một nguồn duy nhất.
 *
 * ─── THẨM QUYỀN: BỘ MOCKUP ĐÃ DUYỆT ───────────────────────────────────────
 *
 * Mọi con số dưới đây chép từ **bộ mockup tĩnh `p1`–`p7` mà người dùng đã
 * chốt**, không phải từ một lượt cân màu nào của agent. Chính chú thích trong
 * mockup in ra thang bậc: *"cạnh thấy 2,8 px · cạnh khuất 1,6 px nét đứt ·
 * thiết diện 3,5 px"*. Muốn kiểm một dòng ở đây thì mở SVG mockup và đọc
 * thuộc tính, đừng suy từ ảnh chụp sản phẩm.
 *
 * ⚠️ **Đây là chỗ đã sai một lần, sai im lặng.** Vòng "D2" hạ toàn bộ thang bề
 * dày (2,8/1,6/3,5 → 2,4/1,4/3,2), hạ mảng tô còn một nửa tới một phần ba
 * (0,07 → 0,035; 0,07 → 0,022), thu chấm điểm từ đường kính 8 px xuống 4,4 px,
 * và đổi thiết diện khuất từ *cùng màu cam mờ đi* sang một màu hồng nhạt
 * (`#e79a84`) mockup không hề có. Không dòng nào trong bảng thị giác còn khớp
 * bản đã duyệt, mà mọi cổng vẫn xanh — vì cổng đọc token, và token chính là
 * thứ đã trôi. **Bài học: mockup là thẩm quyền, token chỉ là bản chép.**
 *
 * ─── VÌ SAO GOM MỘT FILE ──────────────────────────────────────────────────
 *
 * Trước đây bảng token nằm rải ba chỗ: màu trong `scene3d-view.tsx`, bề dày
 * trong `scene3d-wide-line.ts`, tỉ lệ lấp khung trong `scene3d-camera.ts`. Hệ
 * quả là không ai trả lời được *"vai `cạnh khuất` gồm những gì"* mà không mở
 * ba file. Renderer, test và mọi phép đo nay đọc CHUNG file này.
 *
 * ⚠️ **Không bù `linewidth` bằng hằng số.** Đã truy nguyên: renderer tuân theo
 * token đúng `1,001 × linewidth + 0,02` (đo trên cảnh chỉ một đường thẳng, 8
 * bề dày). Con số "thiếu 0,7 px" của các vòng trước là lỗi bộ đo, không phải
 * lỗi renderer — nên token phải ghi ĐÚNG số mockup, không ghi số đã bù.
 */

/**
 * Màu theo VAI, chép từ mockup.
 *
 * ⚠️ `khuat` (`#7d7975`) và `surface` (`#77736f`) chỉ cách nhau Δ ≈ 10 trong
 * không gian sRGB — hai vai ấy **rất gần nhau trên nền sáng**, và đó là lý do
 * vòng trước tự ý tách chúng ra. Nhưng chúng phân biệt được bằng thứ khác:
 * cạnh khuất là **nét đứt 7/5**, mặt phẳng là **mảng tô có viền liền**. Mockup
 * chọn như vậy; đổi màu là việc của người duyệt, không phải của renderer.
 */
export const MAU_D2 = {
  /** Cạnh khối **thấy** — vai đậm nhất của hình. Mockup: `stroke="#1F1F1F"`. */
  mesh: 0x1f1f1f,
  /** Cạnh khối **khuất** — mockup: `stroke="#7D7975"` + `stroke-dasharray="7 5"`. */
  khuat: 0x7d7975,
  /** Thiết diện **thấy** — tiêu điểm của bài. Mockup: `stroke="#D95A43"`. */
  section: 0xd95a43,
  /**
   * Thiết diện **khuất** — **CÙNG MỘT MÀU** với phần thấy.
   *
   * Mockup tách thấy/khuất bằng **độ mờ 0,55 + nét đứt**, không bằng sắc độ
   * thứ hai: `stroke="#D95A43" stroke-opacity="0.55" stroke-dasharray="7 5"`.
   * Giữ chung màu là có chủ đích — mắt đọc ra *"vẫn là đường thiết diện, chỉ
   * đang nằm sau khối"*, thay vì *"một vật khác"*.
   */
  sectionKhuat: 0xd95a43,
  /** Đường dựng (đoạn đo, trục khối cong). Mockup: `stroke="#99948F"`. */
  line: 0x99948f,
  /** Mặt phẳng phụ. Mockup: `fill`/`stroke` = `#77736F`. */
  surface: 0x77736f,
  /** Đa giác không phải thiết diện (đáy, mặt được nêu tên). */
  polygon: 0x99948f,
  /** Chỉ bật khi có `selected_id` THẬT. Không suy từ vai ngữ nghĩa. */
  highlight: 0x0075de,
} as const;

/**
 * Nền giấy của khung vẽ, và cũng là màu **viền tách** quanh chữ và quanh chấm
 * điểm. Mockup: `<rect fill="#FAF9F7">`, `stroke="#FAF9F7"`.
 *
 * ⚠️ Không phải `#ffffff`. Mockup dùng một tông giấy ấm, và khung sản phẩm
 * từng tô `#ffffff` phủ gradient hướng tâm sang `#f6f5f4` — một tầng nền
 * mockup **không có**, đủ để làm lệch mọi phép đo nền của cổng thị giác.
 */
export const MAU_GIAY_D2 = 0xfaf9f7;

/** Bề dày theo VAI, **pixel CSS**. Một THANG BẬC, không phải sáu số rời. */
export const BE_DAY_D2 = {
  /** Mockup: `stroke-width="2.8"`. */
  canhThay: 2.8,
  /** Mockup: `stroke-width="1.6"`. */
  canhKhuat: 1.6,
  /** Mockup: `stroke-width="3.5"` — vai dày nhất, vì là tiêu điểm. */
  thietDienThay: 3.5,
  /** Mockup: `stroke-width="2.2"`. */
  thietDienKhuat: 2.2,
  /** Mockup: `stroke-width="1.2"`. */
  duongDung: 1.2,
  /** Mockup: viền mặt phẳng `stroke-width="1.2"`. */
  vienMatPhang: 1.2,
} as const;

/**
 * Độ mờ của MẢNG TÔ và của vai khuất.
 *
 * ⚠️ Vòng trước hạ `khoi` và `matPhang` xuống 0,035/0,022 với lý do *"ba lớp
 * tô cộng dồn đọc ra như một vết bẩn"*. Chỗ cộng dồn là có thật, nhưng cách
 * chữa của mockup **không phải** hạ từng lớp: mockup giữ 0,07 cho cả hai và
 * tránh chồng bằng **thứ tự vẽ** — mặt phẳng cắt vẽ trước, khối sau, thiết
 * diện trên cùng. Hạ độ mờ làm mất luôn cảm giác KHỐI ĐẶC.
 */
export const DO_MO_D2 = {
  /** Mockup: khối `fill="#1F1F1F" fill-opacity="0.07"`. */
  khoi: 0.07,
  /** Mockup: mặt phẳng `fill="#77736F" fill-opacity="0.07"`. */
  matPhang: 0.07,
  /** Mockup: thiết diện `fill="#D95A43" fill-opacity="0.14"`. */
  thietDien: 0.14,
  /** Mockup: viền mặt phẳng `stroke-opacity="0.85"`. */
  vienMatPhang: 0.85,
  /** Mockup: nét thiết diện KHUẤT `stroke-opacity="0.55"`. */
  thietDienKhuat: 0.55,
  /** Mockup: chấm điểm KHUẤT `fill-opacity="0.45"`. */
  diemKhuat: 0.45,
  /** Khi người học BẤM CHỌN — đây là trạng thái tương tác, không phải vai. */
  daChon: 0.24,
  thietDienDaChon: 0.55,
} as const;

/**
 * **Đường kính** chấm điểm, pixel màn hình. Mockup: `<circle r="4">` ⇒ 8 px.
 *
 * ⚠️ Bản trước dựng chấm bằng bán kính trong TOẠ ĐỘ THẾ GIỚI, nên cỡ chấm là
 * hệ quả của đơn vị bài toán chứ không phải một quyết định thiết kế: cùng một
 * bài đo được 10 px ở 1440×900 và 15 px ở 1920×1080. Quy về pixel là đúng —
 * nhưng vòng ấy quy nhầm sang **4,4 px**, tức chỉ hơn một nửa mockup.
 */
export const DIEM_PX_D2 = 8;

/**
 * Bề rộng **vành giấy** quanh chấm điểm, pixel màn hình. Mockup vẽ hai vòng
 * chồng nhau: đĩa mực, rồi `stroke="#FAF9F7" stroke-width="1.4"` đè lên.
 *
 * Vành ấy không phải trang trí: nó cắt các nét chạy dưới chấm, nhờ đó điểm
 * đọc ra như **một đỉnh** chứ không như một chỗ ba đường giao nhau.
 */
export const DIEM_VANH_PX_D2 = 1.4;

/**
 * Phần chiều bị bó mà hình nên lấp.
 *
 * ⚠️ Thử 0,88 trước và nó làm TRÀN KHUNG ca đa diện lõm: phép khớp dùng hộp
 * bao HÌNH HỌC, còn nhãn và nửa bề dày nét nằm ngoài hộp ấy. 0,84 là mức cao
 * nhất đo được mà cả bảy ca đều không chạm mép.
 *
 * ⚠️ Và quét toàn bộ không gian góc cho thấy **không góc nào** làm hình rộng
 * ra: hộp bao bài là 2×2×4, tỉ lệ chiếu tốt nhất đạt 0,64 trong khi canvas là
 * 2,42. Khoảng trống HAI BÊN là hệ quả của tỉ lệ canvas, không sửa được bằng
 * camera.
 */
export const TI_LE_LAP_KHUNG_D2 = 0.84;

/**
 * Bán kính thử đầu tiên quanh điểm neo khi đặt nhãn, pixel CSS.
 *
 * Mockup đặt nhãn ở lệch cố định `(+21,8; −7,6)` so với chấm — tức bán kính
 * ≈ 23 px theo một hướng duy nhất. Sản phẩm không dùng được lệch cố định vì
 * hình XOAY được (mockup thì đứng yên), nên đây là bán kính thử đầu tiên của
 * bộ giải; nó bám sát con số ấy rồi mới nới ra khi bị chắn.
 */
export const NHAN_BAN_KINH = 21;

/**
 * Dưới bề rộng này thì coi là KHUNG HẸP (điện thoại) và hạ ngưỡng cách nét từ
 * 6 px xuống 4 px.
 *
 * Không phải một phép nới lỏng tuỳ tiện: ở khung hẹp mọi thứ gần nhau hơn, và
 * giữ nguyên 6 px sẽ đẩy phần lớn nhãn vào diện "không có nghiệm" rồi kéo
 * camera lùi quá xa — hình bé lại vì một con số chọn cho màn rộng.
 */
export const KHUNG_HEP_PX = 520;
