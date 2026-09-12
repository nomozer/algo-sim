/**
 * scene3d-tokens.ts — NGÔN NGỮ THỊ GIÁC D2, một nguồn duy nhất.
 *
 * ─── VÌ SAO MỘT FILE ──────────────────────────────────────────────────────
 *
 * Trước bản này bảng token nằm rải ba chỗ: màu trong `scene3d-view.tsx`, bề
 * dày trong `scene3d-wide-line.ts`, tỉ lệ lấp khung trong `scene3d-camera.ts`.
 * Hệ quả là không ai trả lời được *"vai `cạnh khuất` gồm những gì"* mà không
 * mở ba file, và một lượt sửa màu rất dễ quên bề dày đi kèm. Renderer, test và
 * mọi phép đo nay đọc CHUNG file này.
 *
 * ─── D2 KHÁC VÒNG TRƯỚC Ở ĐÂU ─────────────────────────────────────────────
 *
 * Bảng cũ có hai chỗ mắt không tách được, đã đo:
 *   · thiết diện **thấy** và **khuất** dùng chung một màu ⇒ Δ = 0;
 *   · cạnh khuất `#7d7975` và mặt phẳng `#77736f` ⇒ Δ = 10,4, dưới ngưỡng
 *     phân biệt trên nền sáng.
 * Bảng D2 có Δ nhỏ nhất giữa sáu vai là **69,9**.
 *
 * Mảng tô cũng đổi: chỗ mặt phẳng cắt khối từng là ba lớp tô cộng dồn
 * (0,07 + 0,07 + 0,14), đọc ra như một vết bẩn. D2 hạ tô khối và tô mặt phẳng
 * xuống mức chỉ còn gợi ý (0,035 / 0,022) và giữ thiết diện ở 0,15 — nó là
 * tiêu điểm của bài nên phải là vai nổi nhất.
 *
 * ⚠️ **Không bù `linewidth` bằng hằng số.** Đã truy nguyên: renderer tuân theo
 * token đúng `1,001 × linewidth + 0,02` (đo trên cảnh chỉ một đường thẳng, 8
 * bề dày). Con số "thiếu 0,7 px" của các vòng trước là lỗi bộ đo, không phải
 * lỗi renderer.
 */

/** Màu theo VAI. Sáu vai phải tách được bằng mắt trên nền sáng. */
export const MAU_D2 = {
  /** Cạnh khối **thấy** — vai đậm nhất của hình. */
  mesh: 0x1a1a1a,
  /** Cạnh khối **khuất**: xám ĐẶC, không phải bản mờ của cạnh thấy. */
  khuat: 0x6b6560,
  /** Thiết diện **thấy** — tiêu điểm của bài, nổi hơn mọi vai khác. */
  section: 0xcf4726,
  /**
   * Thiết diện **khuất** — vai RIÊNG, thêm ở D2.
   *
   * Bảng cũ để phần khuất của thiết diện trùng màu phần thấy, nên hình mất
   * đúng câu trả lời *"đoạn này nằm trước hay sau khối"* ở chính cái hình mà
   * bài đang hỏi.
   */
  sectionKhuat: 0xe79a84,
  /** Đường dựng (đường thẳng, trục khối cong). */
  line: 0xa39c94,
  /** Mặt phẳng phụ — phải KHÔNG trùng `khuat`. */
  surface: 0xcdc7bf,
  /** Đa giác không phải thiết diện (đáy, mặt được nêu tên). */
  polygon: 0xa39c94,
  /** Chỉ bật khi có `selected_id` THẬT. Không suy từ vai ngữ nghĩa. */
  highlight: 0x0075de,
} as const;

/** Bề dày theo VAI, **pixel CSS**. Một THANG BẬC, không phải sáu số rời. */
export const BE_DAY_D2 = {
  canhThay: 2.4,
  canhKhuat: 1.4,
  thietDienThay: 3.2,
  thietDienKhuat: 2.0,
  duongDung: 1.0,
  vienMatPhang: 0.9,
} as const;

/**
 * Độ mờ của MẢNG TÔ. Cố ý thấp: chồng nhiều lớp tô cùng một chỗ là cách nhanh
 * nhất biến một hình học thành một vết bẩn.
 */
export const DO_MO_D2 = {
  khoi: 0.035,
  matPhang: 0.022,
  thietDien: 0.15,
  /** Khi người học BẤM CHỌN — đây là trạng thái tương tác, không phải vai. */
  daChon: 0.24,
  thietDienDaChon: 0.55,
} as const;

/**
 * Đường kính chấm điểm, **pixel màn hình**.
 *
 * ⚠️ Bản trước dựng chấm bằng bán kính trong TOẠ ĐỘ THẾ GIỚI, nên cỡ chấm là
 * hệ quả của đơn vị bài toán chứ không phải một quyết định thiết kế: cùng một
 * bài đo được 10 px ở 1440×900 và 15 px ở 1920×1080, và một bài có toạ độ lớn
 * gấp mười cho chấm nhỏ gấp mười.
 */
export const DIEM_PX_D2 = 4.4;

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
 * Nhỏ hơn thì chữ dính vào chấm điểm; lớn hơn thì chữ trôi khỏi vật nó đặt
 * tên và người đọc phải đoán chữ nào của điểm nào.
 */
export const NHAN_BAN_KINH = 17;

/**
 * Dưới bề rộng này thì coi là KHUNG HẸP (điện thoại) và hạ ngưỡng cách nét từ
 * 6 px xuống 4 px.
 *
 * Không phải một phép nới lỏng tuỳ tiện: ở khung hẹp mọi thứ gần nhau hơn, và
 * giữ nguyên 6 px sẽ đẩy phần lớn nhãn vào diện "không có nghiệm" rồi kéo
 * camera lùi quá xa — hình bé lại vì một con số chọn cho màn rộng.
 */
export const KHUNG_HEP_PX = 520;
