/**
 * scene3d-camera.ts — KHUNG NHÌN, tính từ hộp bao của vật ĐANG THẤY.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Bản trước đặt camera bằng một hằng số (`position.set(6, 5, 8)`) cho mọi bài.
 * Với bài toạ độ nhỏ thì hình chiếm một góc khung; với bài toạ độ lớn thì hình
 * tràn ra ngoài. Ảnh chụp thật cho thấy cả hai kiểu hỏng.
 *
 * ⚠️ Đây là **phép tính trình bày**, không phải phép tính hình học: đầu vào là
 * các vị trí đã do nhân hình học sinh ra, đầu ra là vị trí camera tính bằng
 * đơn vị thế giới của renderer. Nó không quay lại `Scene3D`, không sinh vật
 * mới, và không đổi một toạ độ nào.
 *
 * ⚠️ **Không tự gọi khi đổi bước.** Khung nhìn phải đứng yên giữa bước k và
 * k+1, nếu không thì hoạt cảnh tua bước biến thành hoạt cảnh đổi góc máy, và
 * người xem không phân biệt được cái nào đang đổi. Chỉ gọi khi: nạp cảnh lần
 * đầu, người dùng bấm xem lại toàn hình, và khi tách/ráp khối làm kích thước
 * hình đổi hẳn.
 */

/** Hộp bao trục, đơn vị thế giới. */
export interface HopBao {
  min: [number, number, number];
  max: [number, number, number];
}

/** Kết quả đặt khung nhìn — vị trí camera và điểm nó nhìn vào. */
export interface KhungNhin {
  viTri: [number, number, number];
  nhinVao: [number, number, number];
}

/**
 * Hướng nhìn mặc định: [8, 3, 6] (phương vị ~20.6°, góc ngẩng ~35.1°).
 * Tránh hình chiếu suy biến dọc đường chéo đáy (45° ở hình vuông, 37°-53° ở hình chữ nhật),
 * giữ S, A, C không thẳng hàng/chồng lấn trên màn hình và bảo toàn độ sâu cho mọi họ bài.
 */
const HUONG: readonly [number, number, number] = [8, 3, 6];

/** Phần khung mà hình nên chiếm. Chỉ thị đặt khoảng 55–80%; lấy giữa dải. */
const TI_LE_LAP_KHUNG = 0.68;

/** Khoảng cách tối thiểu, chặn ca hộp bao suy biến về một điểm. */
const KHOANG_TOI_THIEU = 2.5;

export function hopBaoCuaDiem(diem: [number, number, number][]): HopBao | null {
  if (diem.length === 0) return null;
  const min: [number, number, number] = [Infinity, Infinity, Infinity];
  const max: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  for (const p of diem) {
    for (let i = 0; i < 3; i++) {
      if (!Number.isFinite(p[i])) return null;
      if (p[i] < min[i]) min[i] = p[i];
      if (p[i] > max[i]) max[i] = p[i];
    }
  }
  return { min, max };
}

/**
 * Đặt khung nhìn sao cho hộp bao lấp khoảng `TI_LE_LAP_KHUNG` chiều cao khung.
 *
 * `fovDo` là góc mở dọc của camera (độ); `tiLeKhung` là rộng/cao của khung vẽ.
 * Khi khung hẹp hơn cao, chiều RỘNG mới là chiều bị bó, nên khoảng cách phải
 * lấy theo cái lớn hơn trong hai ràng buộc — bỏ qua điều này thì ở khung dọc
 * hình bị cắt hai bên.
 *
 * Trả `null` khi đầu vào không dùng được, để nơi gọi giữ nguyên khung nhìn
 * hiện tại thay vì nhảy tới một chỗ vô nghĩa. **Không bao giờ trả `NaN`.**
 */
export function khungNhinVua(
  hop: HopBao | null,
  fovDo: number,
  tiLeKhung: number,
): KhungNhin | null {
  if (!hop) return null;
  if (!Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180) return null;
  if (!Number.isFinite(tiLeKhung) || tiLeKhung <= 0) return null;

  const tam: [number, number, number] = [
    (hop.min[0] + hop.max[0]) / 2,
    (hop.min[1] + hop.max[1]) / 2,
    (hop.min[2] + hop.max[2]) / 2,
  ];
  const nuaCanh = [
    (hop.max[0] - hop.min[0]) / 2,
    (hop.max[1] - hop.min[1]) / 2,
    (hop.max[2] - hop.min[2]) / 2,
  ];
  const banKinh = Math.hypot(nuaCanh[0], nuaCanh[1], nuaCanh[2]);
  if (!Number.isFinite(banKinh)) return null;

  const fov = (fovDo * Math.PI) / 180;
  const canDoc = banKinh / Math.sin(fov / 2);
  // Góc mở NGANG suy từ góc dọc và tỉ lệ khung.
  const fovNgang = 2 * Math.atan(Math.tan(fov / 2) * tiLeKhung);
  const canNgang = banKinh / Math.sin(fovNgang / 2);
  const can = Math.max(canDoc, canNgang) / TI_LE_LAP_KHUNG;
  const khoang = Math.max(KHOANG_TOI_THIEU, can);
  if (!Number.isFinite(khoang)) return null;

  const dai = Math.hypot(HUONG[0], HUONG[1], HUONG[2]);
  return {
    viTri: [
      tam[0] + (HUONG[0] / dai) * khoang,
      tam[1] + (HUONG[1] / dai) * khoang,
      tam[2] + (HUONG[2] / dai) * khoang,
    ],
    nhinVao: tam,
  };
}

/* ─── GÓC NHÌN SƯ PHẠM (w10) ───────────────────────────────────────────────
 *
 * Một hướng cố định cho mọi cảnh nhìn dọc cạnh AB của hình chóp đáy chữ nhật:
 * đáy bị ép dẹt, đỉnh A lọt giữa hình, nhãn đè nhau (ảnh w09). Hướng nay CHỌN
 * theo số đo của chính cảnh — hình chiếu các đỉnh và cạnh — không theo tên bài
 * hay toạ độ riêng của họ nào. Z vẫn hướng lên; OrbitControls không đổi.
 */
export type Diem3 = [number, number, number];

/** Số đo của một hướng nhìn, chuẩn hoá theo bán kính R quanh trọng tâm. */
export interface ChatLuongGocNhin {
  /** Diện tích bao lồi của hình chiếu / R² — hình có "choán" mặt phẳng nhìn không. */
  dienTichBao: number;
  /** Khoảng cách nhỏ nhất giữa hai đỉnh chiếu / R — đỉnh (và nhãn) chồng nhau. */
  khoangDinhMin: number;
  /** Khoảng hở nhỏ nhất đỉnh ↔ cạnh không chứa nó / R — đỉnh nằm lên cạnh khác. */
  khoangDinhCanhMin: number;
  /** Dải độ sâu các đỉnh dọc hướng nhìn / R — hình có chiều sâu hay bẹt. */
  doSau: number;
  /** min |n·d| trên các mặt — mặt nào bị ép thành một đường thẳng. */
  matNghiengMin: number;
}

const tru = (a: Diem3, b: Diem3): Diem3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const tich = (a: Diem3, b: Diem3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cheo = (a: Diem3, b: Diem3): Diem3 =>
  [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const chuan = (a: Diem3): Diem3 => {
  const d = Math.hypot(...a) || 1;
  return [a[0] / d, a[1] / d, a[2] / d];
};

/** Hướng TỪ tâm TỚI camera, Z-up: phương vị quanh Z, góc ngẩng so với mặt Oxy. */
export function huongTuGoc(phuongViDo: number, caoDo: number): Diem3 {
  const a = (phuongViDo * Math.PI) / 180;
  const e = (caoDo * Math.PI) / 180;
  return [Math.cos(e) * Math.cos(a), Math.cos(e) * Math.sin(a), Math.sin(e)];
}

function chieu(diem: Diem3[], huong: Diem3) {
  const d = chuan(huong);
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const tam = diem.reduce<Diem3>((s, p) => [s[0] + p[0] / diem.length, s[1] + p[1] / diem.length,
    s[2] + p[2] / diem.length], [0, 0, 0]);
  const R = Math.max(1e-9, ...diem.map((p) => Math.hypot(...tru(p, tam))));
  return { d, R, uv: diem.map((p) => [tich(tru(p, tam), phai) / R, tich(tru(p, tam), len) / R]),
    sau: diem.map((p) => tich(tru(p, tam), d) / R) };
}

function dienTichBaoLoi(uv: number[][]): number {
  const p = [...uv].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (p.length < 3) return 0;
  const cross = (o: number[], a: number[], b: number[]) =>
    (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const duoi: number[][] = [];
  const tren: number[][] = [];
  for (const q of p) {
    while (duoi.length >= 2 && cross(duoi.at(-2)!, duoi.at(-1)!, q) <= 0) duoi.pop();
    duoi.push(q);
  }
  for (const q of [...p].reverse()) {
    while (tren.length >= 2 && cross(tren.at(-2)!, tren.at(-1)!, q) <= 0) tren.pop();
    tren.push(q);
  }
  const bao = [...duoi.slice(0, -1), ...tren.slice(0, -1)];
  let s = 0;
  for (let i = 0; i < bao.length; i++) {
    const [a, b] = [bao[i], bao[(i + 1) % bao.length]];
    s += a[0] * b[1] - b[0] * a[1];
  }
  return Math.abs(s) / 2;
}

function khoangDiemDoan(p: number[], a: number[], b: number[]): number {
  const ab = [b[0] - a[0], b[1] - a[1]];
  const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1])
    / Math.max(1e-12, ab[0] ** 2 + ab[1] ** 2)));
  return Math.hypot(p[0] - a[0] - t * ab[0], p[1] - a[1] - t * ab[1]);
}

function khoangDiemDoan3(p: Diem3, a: Diem3, b: Diem3): number {
  const ab = tru(b, a);
  const t = Math.max(0, Math.min(1, tich(tru(p, a), ab) / Math.max(1e-12, tich(ab, ab))));
  return Math.hypot(...tru(p, [a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2]]));
}

/** Đo một hướng nhìn. `canh`/`mat` là chỉ số vào `diem`. */
export function danhGiaGocNhin(
  diem: Diem3[], canh: [number, number][], mat: number[][], huong: Diem3,
): ChatLuongGocNhin {
  const { d, R, uv, sau } = chieu(diem, huong);
  let khoangDinhMin = Infinity;
  for (let i = 0; i < uv.length; i++) {
    for (let j = i + 1; j < uv.length; j++) {
      khoangDinhMin = Math.min(khoangDinhMin, Math.hypot(uv[i][0] - uv[j][0], uv[i][1] - uv[j][1]));
    }
  }
  let khoangDinhCanhMin = Infinity;
  for (let i = 0; i < uv.length; i++) {
    for (const [a, b] of canh) {
      if (a === i || b === i) continue;
      // Điểm NẰM TRÊN cạnh trong không gian (đỉnh thiết diện, trung điểm): hình
      // chiếu nào cũng đặt nó lên cạnh — đó là sự thật hình học, không phải chồng nhãn.
      if (khoangDiemDoan3(diem[i], diem[a], diem[b]) < 1e-6 * R) continue;
      khoangDinhCanhMin = Math.min(khoangDinhCanhMin, khoangDiemDoan(uv[i], uv[a], uv[b]));
    }
  }
  let matNghiengMin = Infinity;
  for (const f of mat) {
    if (f.length < 3) continue;
    const n = chuan(cheo(tru(diem[f[1]], diem[f[0]]), tru(diem[f[2]], diem[f[0]])));
    matNghiengMin = Math.min(matNghiengMin, Math.abs(tich(n, d)));
  }
  return {
    dienTichBao: dienTichBaoLoi(uv),
    khoangDinhMin: Number.isFinite(khoangDinhMin) ? khoangDinhMin : 0,
    khoangDinhCanhMin: Number.isFinite(khoangDinhCanhMin) ? khoangDinhCanhMin : 1,
    doSau: sau.length ? Math.max(...sau) - Math.min(...sau) : 0,
    matNghiengMin: Number.isFinite(matNghiengMin) ? matNghiengMin : 1,
  };
}

/* NGƯỠNG — hai loại, mỗi loại gắn với một tham chiếu nói rõ được:
 *
 *  · KHOẢNG HỞ (đỉnh↔đỉnh, đỉnh↔cạnh) gắn với khối lập phương đơn vị nhìn theo
 *    hướng mặc định cũ `HUONG` — hướng ấy được chọn có chủ đích để không đỉnh
 *    nào chồng đỉnh nào trên khối hộp, và các cảnh khối hộp của w09 đọc được ở
 *    đó. Đạt khi ≥ một nửa số đo tham chiếu.
 *  · DIỆN TÍCH BAO và ĐỘ SÂU gắn với hướng TỐT NHẤT của CHÍNH cảnh ấy: hình chóp
 *    cao gầy không bao giờ choán mặt phẳng nhìn như khối hộp, nên so với khối
 *    hộp là phạt hình dáng chứ không phạt góc nhìn. Đạt khi ≥ 60% / 50% cực đại.
 *  · Không mặt nào gần song song tia nhìn quá 6° (|n·d| ≥ sin 6°) — mặt ấy bị ép
 *    thành một đường thẳng, đúng kiểu "hình dẹt". */
const _LP: Diem3[] = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]];
const _LP_MAT = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]];
const _LP_CANH: [number, number][] = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4],
  [0, 4], [1, 5], [2, 6], [3, 7]];
export const GOC_NHIN_THAM_CHIEU = danhGiaGocNhin(_LP, _LP_CANH, _LP_MAT, [...HUONG]);
export const NGUONG_GOC_NHIN = {
  tiLeDienTichBao: 0.6,
  tiLeDoSau: 0.5,
  khoangDinhMin: 0.5 * GOC_NHIN_THAM_CHIEU.khoangDinhMin,
  khoangDinhCanhMin: 0.5 * GOC_NHIN_THAM_CHIEU.khoangDinhCanhMin,
  matNghiengMin: Math.sin((6 * Math.PI) / 180),
} as const;

/** Cực đại diện tích bao / độ sâu của cảnh trên lưới hướng — mẫu số của ngưỡng. */
export interface TranGocNhin { dienTichBao: number; doSau: number }

export function datNguong(q: ChatLuongGocNhin, tran: TranGocNhin): boolean {
  return q.dienTichBao >= NGUONG_GOC_NHIN.tiLeDienTichBao * tran.dienTichBao
    && q.doSau >= NGUONG_GOC_NHIN.tiLeDoSau * tran.doSau
    && q.khoangDinhMin >= NGUONG_GOC_NHIN.khoangDinhMin
    && q.khoangDinhCanhMin >= NGUONG_GOC_NHIN.khoangDinhCanhMin
    && q.matNghiengMin >= NGUONG_GOC_NHIN.matNghiengMin;
}

/** Lưới hướng: phương vị 10° × góc ngẩng 15°–40° (Z-up, như OrbitControls). */
function luoiHuong(): Diem3[] {
  const ra: Diem3[] = [];
  for (let cao = 15; cao <= 40; cao += 5) {
    for (let pv = 0; pv < 360; pv += 10) ra.push(huongTuGoc(pv, cao));
  }
  return ra;
}

/** Đo cả lưới một lần: số đo từng hướng + cực đại làm mẫu số ngưỡng. */
export function doLuoiGocNhin(diem: Diem3[], canh: [number, number][], mat: number[][]) {
  const cac = luoiHuong().map((huong) => ({ huong, q: danhGiaGocNhin(diem, canh, mat, huong) }));
  const tran: TranGocNhin = {
    dienTichBao: Math.max(0, ...cac.map((c) => c.q.dienTichBao)),
    doSau: Math.max(0, ...cac.map((c) => c.q.doSau)),
  };
  return { cac, tran };
}

/** Hướng nhìn tốt nhất trên lưới. Đạt ngưỡng trước; trong số đạt, cân diện
 *  tích, khoảng hở và độ sâu, trừ một chút cho việc xa hướng quen thuộc cũ để
 *  hình giữ tư thế sách giáo khoa. Không hướng nào đạt ⇒ hướng điểm cao nhất. */
export function chonHuongNhin(diem: Diem3[], canh: [number, number][], mat: number[][]): Diem3 {
  const quen = chuan([...HUONG]);
  const { cac, tran } = doLuoiGocNhin(diem, canh, mat);
  let tot: { huong: Diem3; diem: number; dat: boolean } | null = null;
  for (const { huong, q } of cac) {
    const dat = datNguong(q, tran);
    const diemSo = q.dienTichBao / (tran.dienTichBao || 1) + 2 * Math.min(q.khoangDinhCanhMin, 0.3)
      + Math.min(q.khoangDinhMin, 0.5) + 0.5 * q.doSau / (tran.doSau || 1)
      - 0.4 * (1 - tich(huong, quen));
    if (!tot || (dat && !tot.dat) || (dat === tot.dat && diemSo > tot.diem)) {
      tot = { huong, diem: diemSo, dat };
    }
  }
  return tot ? tot.huong : quen;
}

/** Khung nhìn: hướng sư phạm + khoảng cách vừa khít theo HÌNH CHIẾU THẬT của
 *  các điểm (không theo mặt cầu bao, vốn làm hình cao/hẹp chỉ choán một dải). */
export function khungNhinSuPham(
  diem: Diem3[], canh: [number, number][], mat: number[][], fovDo: number, tiLeKhung: number,
  huongCo?: Diem3,
): KhungNhin | null {
  const hop = hopBaoCuaDiem(diem);
  const coBan = khungNhinVua(hop, fovDo, tiLeKhung);
  // Không có cạnh nào để đo (chỉ điểm, khối cong): giữ khung cũ đã được duyệt.
  if (!coBan || diem.length < 2 || (!huongCo && canh.length === 0)) return coBan;
  const d = chuan(huongCo ?? chonHuongNhin(diem, canh, mat));
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const tanDoc = Math.tan((fovDo * Math.PI) / 360);
  const tanNgang = tanDoc * tiLeKhung;
  // Khoảng cách k nhỏ nhất để MỌI điểm lọt vào TI_LE_LAP_KHUNG của khung.
  const khoangVua = (tam: Diem3) => Math.max(KHOANG_TOI_THIEU, ...diem.map((p) => {
    const q = tru(p, tam);
    const s = tich(q, d);
    return Math.max(s + Math.abs(tich(q, phai)) / (tanNgang * TI_LE_LAP_KHUNG),
      s + Math.abs(tich(q, len)) / (tanDoc * TI_LE_LAP_KHUNG));
  }));
  // Rồi dời tâm nhìn về giữa hình chiếu thật: tâm hộp bao lệch khỏi tâm hình
  // chiếu, và phía lệch ấy phí mất một dải khung. Hai vòng là đủ hội tụ.
  let tam: Diem3 = [...coBan.nhinVao];
  for (let vong = 0; vong < 2; vong++) {
    const k = khoangVua(tam);
    const x = diem.map((p) => { const q = tru(p, tam); return tich(q, phai) / (k - tich(q, d)); });
    const y = diem.map((p) => { const q = tru(p, tam); return tich(q, len) / (k - tich(q, d)); });
    const [dx, dy] = [(Math.max(...x) + Math.min(...x)) / 2 * k, (Math.max(...y) + Math.min(...y)) / 2 * k];
    tam = [tam[0] + phai[0] * dx + len[0] * dy, tam[1] + phai[1] * dx + len[1] * dy,
      tam[2] + phai[2] * dx + len[2] * dy];
  }
  const k = khoangVua(tam);
  return { viTri: [tam[0] + d[0] * k, tam[1] + d[1] * k, tam[2] + d[2] * k], nhinVao: tam };
}
