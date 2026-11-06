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
export const HUONG: readonly [number, number, number] = [8, 3, 6];

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

/** Hướng QUEN kiểu SGK mà `chonHuongNhin` kéo về: phương vị của `HUONG`, góc ngẩng 22.4° — góc "Góc SGK" của HTML
 *  tham chiếu (φ = 1.18 rad ⇒ 90° − 67.6°). Chỉ đổi lực kéo trong điểm chấm; ngưỡng vẫn đo theo `HUONG`. */
export const HUONG_SGK: Diem3 = huongTuGoc((Math.atan2(HUONG[1], HUONG[0]) * 180) / Math.PI, 22.4);

/** Trọng số kéo về `HUONG_SGK` trong điểm chấm (bản trước 0.85 — đo trên các cảnh B1/B2: quá yếu để đổi lựa chọn
 *  giữa các hướng ĐÃ đạt ngưỡng). Ngưỡng vẫn xét TRƯỚC, nên hướng suy biến không thắng nhờ lực kéo. */
const LUC_KEO_SGK = 2;

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

export interface TuyChonHuongNhin {
  /** Pháp tuyến đơn vị của các miền/mặt trọng tâm (thiết diện, tam giác qua trục, mặt phẳng nghiên cứu, tam giác nhân chứng vuông góc). */
  matTrongTam?: Diem3[];
  /** Cặp tâm hai đáy khối trụ `[tamDuoi, tamTren, banKinh]` để tránh góc nhìn làm hai đáy chồng lấn hoặc một đáy bị nhìn nghiêng bẹt. */
  capDayTru?: [Diem3, Diem3, number][];
  /** Các mặt nắp ngang của khối đa diện hai đáy (`[tamMat, phapTuyenDonVi]`, vd lăng trụ / hình hộp) để tránh góc nhìn phối cảnh làm mặt đáy trên bị bẹt thành đường thẳng. */
  matCap?: [Diem3, Diem3][];
  /** Cảnh có khối tròn xoay (nón/trụ) kết hợp mặt/tam giác trọng tâm — tránh hướng nhìn trùng khít đường sinh biên làm cạnh thiết diện đè lên đường bao khối. */
  coKhoiCong?: boolean;
}

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

function doMoMatTrongTam(
  huong: Diem3,
  matTrongTam: readonly Diem3[],
  coKhoiCong = false,
): { tb: number; minNghieng: number; coMatDung: boolean } {
  if (matTrongTam.length === 0) return { tb: 0, minNghieng: 1, coMatDung: false };
  const d = chuan(huong);
  let tong = 0;
  let minNghieng = Infinity;
  let coMatDung = false;
  let dem = 0;
  for (const rawN of matTrongTam) {
    const len = Math.hypot(...rawN);
    if (!(len > 1e-9)) continue;
    const n: Diem3 = [rawN[0] / len, rawN[1] / len, rawN[2] / len];
    const mo = Math.abs(tich(n, d));
    const kich = coKhoiCong && Math.abs(n[2]) < 0.35
      ? (mo <= 0.87 ? mo / 0.87 : Math.max(0.74, 1 - 0.95 * ((mo - 0.87) / 0.13)))
      : Math.min(mo, 0.94) / 0.94;
    tong += kich;
    dem += 1;
    if (Math.abs(n[2]) < 0.90) {
      coMatDung = true;
      minNghieng = Math.min(minNghieng, mo);
    }
  }
  return {
    tb: dem > 0 ? tong / dem : 0,
    minNghieng: Number.isFinite(minNghieng) ? minNghieng : 1,
    coMatDung,
  };
}

function uocLuongCameraPhoiCanh(diem: Diem3[], d: Diem3): Diem3 {
  if (diem.length >= 2) {
    const kn = khungNhinSuPham(diem, [], [], 40, 1.25, d, { tiLeDoc: 0.67 });
    if (kn) return kn.viTri;
  }
  return [d[0] * 10, d[1] * 10, d[2] * 10];
}

function kiemMoPhoiCanhNapDaDien(camEst: Diem3, matCap: readonly [Diem3, Diem3][]): boolean {
  for (const [tamMat, phap] of matCap) {
    const tia = chuan(tru(camEst, tamMat));
    if (Math.abs(tich(phap, tia)) < 0.22) return false;
  }
  return true;
}

function diemTachDayTru(
  huong: Diem3,
  camEst: Diem3,
  capDayTru: readonly [Diem3, Diem3, number][],
): { hopLe: boolean; thuong: number } {
  if (capDayTru.length === 0) return { hopLe: true, thuong: 0 };
  const d = chuan(huong);
  let hopLe = true;
  let tong = 0;
  for (const [c0, c1, r] of capDayTru) {
    const truc = tru(c1, c0);
    const h = Math.hypot(...truc);
    if (!(h > 1e-6)) continue;
    const doc = tich(truc, d);
    const hChieu = Math.sqrt(Math.max(0, h * h - doc * doc));
    const u: Diem3 = [truc[0] / h, truc[1] / h, truc[2] / h];
    const banTrucNho = Math.max(0, r) * Math.abs(tich(u, d));
    const moDay0 = Math.abs(tich(u, chuan(tru(camEst, c0))));
    const moDay1 = Math.abs(tich(u, chuan(tru(camEst, c1))));
    if (r > 1e-6 && (hChieu < 1.05 * banTrucNho || Math.min(moDay0, moDay1) < 0.22)) hopLe = false;
    tong += (r > 1e-6 ? Math.min(1, hChieu / (1.35 * r)) : Math.min(1, hChieu / h)) * Math.min(1, Math.min(moDay0, moDay1) / 0.35);
  }
  return { hopLe, thuong: tong / capDayTru.length };
}

/** Hướng nhìn tốt nhất trên lưới. Đạt ngưỡng trước; trong số đạt, cân diện
 *  tích, khoảng hở và độ sâu, trừ một chút cho việc xa hướng quen thuộc cũ để
 *  hình giữ tư thế sách giáo khoa. Không hướng nào đạt ⇒ hướng điểm cao nhất. */
export function chonHuongNhin(
  diem: Diem3[], canh: [number, number][], mat: number[][], tuyChon?: TuyChonHuongNhin,
): Diem3 {
  const quen = HUONG_SGK;
  const { cac, tran } = doLuoiGocNhin(diem, canh, mat);
  const matTrongTam = tuyChon?.matTrongTam ?? [];
  const capDayTru = tuyChon?.capDayTru ?? [];
  const matCap = tuyChon?.matCap ?? [];
  const coKhoiCong = Boolean(tuyChon?.coKhoiCong);
  const coTuyChon = matTrongTam.length > 0 || capDayTru.length > 0 || matCap.length > 0;

  if (!coTuyChon) {
    let tot: { huong: Diem3; diem: number; dat: boolean } | null = null;
    for (const { huong, q } of cac) {
      const dat = datNguong(q, tran);
      const diemSo = q.dienTichBao / (tran.dienTichBao || 1) + 2 * Math.min(q.khoangDinhCanhMin, 0.2)
        + Math.min(q.khoangDinhMin, 0.38) + 0.5 * q.doSau / (tran.doSau || 1)
        - LUC_KEO_SGK * (1 - tich(huong, quen));
      if (!tot || (dat && !tot.dat) || (dat === tot.dat && diemSo > tot.diem)) {
        tot = { huong, diem: diemSo, dat };
      }
    }
    return tot ? tot.huong : quen;
  }

  const danhSach = cac.map(({ huong, q }) => {
    const d = chuan(huong);
    const camEst = uocLuongCameraPhoiCanh(diem, d);
    const mo = doMoMatTrongTam(huong, matTrongTam, coKhoiCong);
    const truInfo = diemTachDayTru(huong, camEst, capDayTru);
    const napMo = kiemMoPhoiCanhNapDaDien(camEst, matCap);
    const datKhongDetNap = truInfo.hopLe && napMo;
    const datCoBan = datNguong(q, tran) && datKhongDetNap;
    const datMo = !mo.coMatDung || mo.minNghieng >= 0.55;
    return { huong, q, mo, truInfo, datKhongDetNap, datCoBan, datDayDu: datCoBan && datMo };
  });
  const coUngVienMo = danhSach.some((x) => x.datDayDu);
  const coUngVienCoBan = danhSach.some((x) => x.datCoBan);

  let tot: { huong: Diem3; diem: number; hang: number } | null = null;
  for (const item of danhSach) {
    const { huong, q, mo, truInfo, datKhongDetNap, datCoBan, datDayDu } = item;
    const hang = coUngVienMo
      ? (datDayDu ? 3 : datCoBan ? 2 : datKhongDetNap ? 1 : 0)
      : coUngVienCoBan
        ? (datCoBan ? 2 : datKhongDetNap ? 1 : 0)
        : (datKhongDetNap ? 1 : 0);
    const lucKeo = mo.coMatDung ? 0.55 : LUC_KEO_SGK;
    const diemSo = q.dienTichBao / (tran.dienTichBao || 1)
      + 2.2 * Math.min(q.khoangDinhCanhMin, 0.22)
      + Math.min(q.khoangDinhMin, 0.38)
      + 0.5 * q.doSau / (tran.doSau || 1)
      + (matTrongTam.length > 0 ? 2.6 * mo.tb : 0)
      + (capDayTru.length > 0 ? 0.45 * truInfo.thuong : 0)
      - lucKeo * (1 - tich(huong, quen));
    if (!tot || hang > tot.hang || (hang === tot.hang && diemSo > tot.diem)) {
      tot = { huong, diem: diemSo, hang };
    }
  }
  return tot ? tot.huong : quen;
}

/**
 * TỈ LỆ HÌNH CHIẾU cao/rộng của các điểm theo hướng `huong` (mobile-canvas-fit, D5) — cùng cơ sở phải/lên với
 * `khungNhinSuPham`. Phép chiếu song song: bỏ qua phối cảnh vài phần trăm, nằm trong lề của `TI_LE_LAP_KHUNG`.
 * `null` khi hình chiếu suy biến (ít hơn hai điểm, bề ngang 0).
 */
export function tiLeHinhChieu(diem: Diem3[], huong: Diem3): number | null {
  if (diem.length < 2) return null;
  const { uv } = chieu(diem, huong);
  const rong = Math.max(...uv.map((p) => p[0])) - Math.min(...uv.map((p) => p[0]));
  const cao = Math.max(...uv.map((p) => p[1])) - Math.min(...uv.map((p) => p[1]));
  return rong > 1e-9 && Number.isFinite(cao) ? cao / rong : null;
}

export interface TuyChonKhungNhinSuPham {
  /** Tỉ lệ lấp khung dọc mục tiêu (mặc định TI_LE_LAP_KHUNG = 0.78). */
  tiLeDoc?: number;
  /** Tỉ lệ lấp khung ngang mục tiêu (mặc định TI_LE_LAP_KHUNG = 0.78). */
  tiLeNgang?: number;
  /** Độ dịch tâm vùng an toàn theo phương ngang (tỉ lệ nửa chiều rộng khung, âm = dịch hình sang trái khi mở panel phải). */
  dichTamNgang?: number;
  /** Độ dịch tâm vùng an toàn theo phương dọc (tỉ lệ nửa chiều cao khung). */
  dichTamDoc?: number;
}

/** Khung nhìn: hướng sư phạm + khoảng cách vừa khít theo HÌNH CHIẾU THẬT của
 *  các điểm (không theo mặt cầu bao, vốn làm hình cao/hẹp chỉ choán một dải). */
export function khungNhinSuPham(
  diem: Diem3[], canh: [number, number][], mat: number[][], fovDo: number, tiLeKhung: number,
  huongCo?: Diem3,
  tuyChon?: TuyChonKhungNhinSuPham,
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
  const tiLeDoc = Math.max(0.25, Math.min(0.9, tuyChon?.tiLeDoc ?? TI_LE_LAP_KHUNG));
  const tiLeNgang = Math.max(0.25, Math.min(0.9, tuyChon?.tiLeNgang ?? TI_LE_LAP_KHUNG));
  // Khoảng cách k nhỏ nhất để MỌI điểm lọt vào tiLeDoc/tiLeNgang của khung.
  const khoangVua = (tam: Diem3) => Math.max(KHOANG_TOI_THIEU, ...diem.map((p) => {
    const q = tru(p, tam);
    const s = tich(q, d);
    return Math.max(s + Math.abs(tich(q, phai)) / (tanNgang * tiLeNgang),
      s + Math.abs(tich(q, len)) / (tanDoc * tiLeDoc));
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
  const dichNgang = (tuyChon?.dichTamNgang ?? 0) * tanNgang * k;
  const dichDoc = (tuyChon?.dichTamDoc ?? 0) * tanDoc * k;
  const tamCuoi: Diem3 = [
    tam[0] - phai[0] * dichNgang - len[0] * dichDoc,
    tam[1] - phai[1] * dichNgang - len[1] * dichDoc,
    tam[2] - phai[2] * dichNgang - len[2] * dichDoc,
  ];
  return { viTri: [tamCuoi[0] + d[0] * k, tamCuoi[1] + d[1] * k, tamCuoi[2] + d[2] * k], nhinVao: tamCuoi };
}

/**
 * HƯỚNG LÊN TRÌNH BÀY (regular-triangular-pyramid-w01) — pháp tuyến đơn vị của ĐÁY chóp, quay về phía ĐỈNH; `null` khi
 * đáy đã nằm ngang (|n_z| ≈ 1 — mọi họ đo trước: hình không đổi một điểm ảnh) hoặc đáy suy biến.
 *
 * Vì sao: đáy tam giác đều cạnh căn chỉ có toạ độ ℚ³ trên mặt NGHIÊNG x+y+z=k (amendment §18.2), nên hình chóp đúng
 * toán nằm nghiêng so với trục lên z của camera. View XOAY HIỂN THỊ (float) nhóm hình để pháp tuyến này về +z — không
 * đổi một toạ độ nào của cảnh, không đổi camera (z-up khoá ở `scene3d-zup-lifecycle.test.tsx`). Phép tính trình bày như
 * mọi hướng nhìn của module này; đáy và đỉnh do backend chỉ (`scene3d-model.dayVaDinhChop`).
 */
/**
 * KHUNG của ký hiệu góc vuông tại chân đường cao (regular-triangular-pyramid-w01): `d` dọc đoạn chân → đỉnh, `e1` là
 * trục x chiếu lên mặt ⊥ d (rơi về trục y khi d gần trục x), `e2 = d × e1`. Đoạn THẲNG ĐỨNG (mọi họ trước) cho đúng
 * x̂, ŷ, ẑ — ký hiệu không đổi một điểm ảnh; đáy nghiêng thì ký hiệu nằm theo đáy thay vì theo trục toạ độ.
 * `null` khi hai đầu trùng nhau.
 */
export function khungGocVuong(chan: Diem3, dinh: Diem3): { e1: Diem3; d: Diem3; e2: Diem3 } | null {
  const v = tru(dinh, chan);
  if (!(Math.hypot(...v) > 0)) return null;
  const d = chuan(v);
  const truc: Diem3 = Math.abs(d[0]) > 0.9 ? [0, 1, 0] : [1, 0, 0];
  const k = tich(truc, d);
  const e1 = chuan([truc[0] - k * d[0], truc[1] - k * d[1], truc[2] - k * d[2]]);
  return { e1, d, e2: cheo(d, e1) };
}

export function huongLenHienThi(day: Diem3[], dinh: Diem3): Diem3 | null {
  if (day.length < 3) return null;
  const n = cheo(tru(day[1], day[0]), tru(day[2], day[0]));
  if (!(Math.hypot(...n) > 0)) return null;
  const len = chuan(tich(tru(dinh, day[0]), n) < 0 ? [-n[0], -n[1], -n[2]] : n);
  return Math.abs(len[2]) > 1 - 1e-9 ? null : len;
}

export interface TamXoayOnDinh {
  tamXoay: Diem3;
  banKinhKhoi: number;
  diemKhoiChinh: Diem3[];
  /** The main (outer) solids the centre was taken from; their real surfaces bound the near zoom limit. */
  khoiChinh?: readonly LoaiKhoiTamXoay[];
}

export type LoaiKhoiTamXoay =
  | { loai: "solid"; vertices: readonly Diem3[]; faces: readonly number[][] }
  | {
      loai: "curved_solid";
      curvedKind: string;
      anchor: Diem3;
      radius: number;
      apexOrTop: Diem3;
      pts: readonly Diem3[];
    };

export interface VungAnToanNdc {
  xMin?: number;
  xMax?: number;
  yMin?: number;
  yMax?: number;
}

function trongTamTheTichDaDien(verts: readonly Diem3[], faces: readonly number[][]): { tam: Diem3; vol: number } {
  const n = verts.length;
  if (n === 0) return { tam: [0, 0, 0], vol: 0 };
  const v0: Diem3 = [
    verts.reduce((s, p) => s + p[0], 0) / n,
    verts.reduce((s, p) => s + p[1], 0) / n,
    verts.reduce((s, p) => s + p[2], 0) / n,
  ];
  let tongVol6 = 0;
  const tichLuy: Diem3 = [0, 0, 0];
  let tongDienTich2 = 0;
  const tichLuyMat: Diem3 = [0, 0, 0];

  for (const f of faces) {
    if (f.length < 3) continue;
    const a = verts[f[0]];
    if (!a) continue;
    for (let i = 1; i < f.length - 1; i++) {
      const b = verts[f[i]];
      const c = verts[f[i + 1]];
      if (!b || !c) continue;
      const crMat = cheo(tru(b, a), tru(c, a));
      const dt2 = Math.hypot(...crMat);
      if (dt2 > 1e-12) {
        tongDienTich2 += dt2;
        tichLuyMat[0] += (dt2 * (a[0] + b[0] + c[0])) / 3;
        tichLuyMat[1] += (dt2 * (a[1] + b[1] + c[1])) / 3;
        tichLuyMat[2] += (dt2 * (a[2] + b[2] + c[2])) / 3;
      }
      const cr = cheo(tru(b, v0), tru(c, v0));
      const vol6 = Math.abs(tich(tru(a, v0), cr));
      if (vol6 > 1e-12) {
        tongVol6 += vol6;
        tichLuy[0] += vol6 * 0.25 * (v0[0] + a[0] + b[0] + c[0]);
        tichLuy[1] += vol6 * 0.25 * (v0[1] + a[1] + b[1] + c[1]);
        tichLuy[2] += vol6 * 0.25 * (v0[2] + a[2] + b[2] + c[2]);
      }
    }
  }
  if (tongVol6 > 1e-12) {
    return {
      tam: [tichLuy[0] / tongVol6, tichLuy[1] / tongVol6, tichLuy[2] / tongVol6],
      vol: tongVol6 / 6,
    };
  }
  if (tongDienTich2 > 1e-12) {
    return {
      tam: [tichLuyMat[0] / tongDienTich2, tichLuyMat[1] / tongDienTich2, tichLuyMat[2] / tongDienTich2],
      vol: 0,
    };
  }
  return { tam: v0, vol: 0 };
}

function hopBaoChuaHopBao(lon: HopBao, nho: HopBao, eps = 1e-4): boolean {
  return (
    lon.min[0] - eps <= nho.min[0] && nho.max[0] <= lon.max[0] + eps &&
    lon.min[1] - eps <= nho.min[1] && nho.max[1] <= lon.max[1] + eps &&
    lon.min[2] - eps <= nho.min[2] && nho.max[2] <= lon.max[2] + eps
  );
}

/**
 * Tính tâm xoay quỹ đạo ổn định (`OrbitControls.target`) từ dữ liệu số thuần của các khối hình học:
 * - Ưu tiên khối chính (`solid`, `curved_solid`), loại trừ khối con nằm trọn bên trong khối bao lớn hơn
 *   (ví dụ chóp con tỉ số thể tích, nón cụt phần trên, mặt cầu nội tiếp) để không kéo lệch trục đối xứng.
 * - Kết hợp cân bằng 50/50 giữa trọng tâm thể tích `G_vol` và tâm hộp bao khối chính `C_aabb`:
 *   giữ nguyên trục đối xứng trên chóp đều/lăng trụ/trụ/nón/cầu, đồng thời tách hẳn khỏi các điểm trung gian
 *   như `P, M, N` trên chóp cạnh bên vuông góc đáy (`S.ABCD`).
 * - Bất biến qua mọi bước dựng (chỉ đọc dữ liệu hình học hợp lệ, không làm lộ vật chưa xuất hiện trên canvas).
 * - Khi bài không có khối đặc, fallback về trung bình khử trùng + tâm hộp bao của các đối tượng hữu hạn
 *   (bỏ qua đường thẳng vô hạn và mặt phẳng mở rộng).
 */
export function tinhTamXoayTuKhoi(
  dsKhoiDauVao: readonly LoaiKhoiTamXoay[],
  diemDuPhong: readonly Diem3[],
): TamXoayOnDinh | null {
  const dsKhoi: { pts: Diem3[]; hop: HopBao; tamVol: Diem3; vol: number; nguon: LoaiKhoiTamXoay }[] = [];

  for (const k of dsKhoiDauVao) {
    if (k.loai === "solid" && k.vertices.length > 0) {
      const verts: Diem3[] = k.vertices.map((v) => [v[0], v[1], v[2]]);
      const hop = hopBaoCuaDiem(verts);
      if (!hop) continue;
      const { tam, vol } = trongTamTheTichDaDien(verts, k.faces);
      dsKhoi.push({ pts: verts, hop, tamVol: tam, vol: Math.max(vol, 1e-6), nguon: k });
    } else if (k.loai === "curved_solid" && Number.isFinite(k.radius) && k.radius > 0) {
      const pts: Diem3[] = k.pts.map((p) => [p[0], p[1], p[2]]);
      const hop = hopBaoCuaDiem(pts);
      if (!hop) continue;
      const r = k.radius;
      const c = k.anchor;
      const dinh = k.apexOrTop;
      const chieuCao = Math.hypot(dinh[0] - c[0], dinh[1] - c[1], dinh[2] - c[2]);
      let tamVol: Diem3 = [c[0], c[1], c[2]];
      let vol = (4 / 3) * Math.PI * r * r * r;
      if (k.curvedKind === "cylinder") {
        tamVol = [(c[0] + dinh[0]) * 0.5, (c[1] + dinh[1]) * 0.5, (c[2] + dinh[2]) * 0.5];
        vol = Math.PI * r * r * Math.max(chieuCao, 1e-6);
      } else if (k.curvedKind === "cone") {
        tamVol = [
          0.75 * c[0] + 0.25 * dinh[0],
          0.75 * c[1] + 0.25 * dinh[1],
          0.75 * c[2] + 0.25 * dinh[2],
        ];
        vol = (1 / 3) * Math.PI * r * r * Math.max(chieuCao, 1e-6);
      }
      dsKhoi.push({ pts, hop, tamVol, vol: Math.max(vol, 1e-6), nguon: k });
    }
  }

  if (dsKhoi.length > 0) {
    const khoiNgoai = dsKhoi.filter(
      (nho, idx) =>
        !dsKhoi.some(
          (lon, jdx) =>
            jdx !== idx &&
            lon.vol > nho.vol * (1 + 1e-4) &&
            hopBaoChuaHopBao(lon.hop, nho.hop),
        ),
    );
    const chon = khoiNgoai.length > 0 ? khoiNgoai : dsKhoi;
    const diemKhoiChinh = chon.flatMap((k) => k.pts);
    const hopChung = hopBaoCuaDiem(diemKhoiChinh);
    if (hopChung) {
      const tongVol = chon.reduce((s, k) => s + k.vol, 0) || 1;
      const gVol: Diem3 = [
        chon.reduce((s, k) => s + k.vol * k.tamVol[0], 0) / tongVol,
        chon.reduce((s, k) => s + k.vol * k.tamVol[1], 0) / tongVol,
        chon.reduce((s, k) => s + k.vol * k.tamVol[2], 0) / tongVol,
      ];
      const cAabb: Diem3 = [
        (hopChung.min[0] + hopChung.max[0]) * 0.5,
        (hopChung.min[1] + hopChung.max[1]) * 0.5,
        (hopChung.min[2] + hopChung.max[2]) * 0.5,
      ];
      const tamXoay: Diem3 = [
        (gVol[0] + cAabb[0]) * 0.5,
        (gVol[1] + cAabb[1]) * 0.5,
        (gVol[2] + cAabb[2]) * 0.5,
      ];
      const banKinhKhoi = Math.max(
        0.25,
        ...diemKhoiChinh.map((p) => Math.hypot(p[0] - tamXoay[0], p[1] - tamXoay[1], p[2] - tamXoay[2])),
      );
      return { tamXoay, banKinhKhoi, diemKhoiChinh, khoiChinh: chon.map((k) => k.nguon) };
    }
  }

  // Chiến lược dự phòng cho bài không có solid: chỉ lấy đối tượng hữu hạn hợp lệ (bỏ line3 / plane3 vô hạn).
  const huuHan: Diem3[] = diemDuPhong.filter((pm) => pm.every(Number.isFinite)).map((pm) => [pm[0], pm[1], pm[2]]);
  const hopDuPhong = hopBaoCuaDiem(huuHan);
  if (!hopDuPhong) return null;
  const duyNhat: Diem3[] = [];
  for (const p of huuHan) {
    if (!duyNhat.some((q) => Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) < 1e-6)) {
      duyNhat.push(p);
    }
  }
  const tb: Diem3 = [
    duyNhat.reduce((s, p) => s + p[0], 0) / duyNhat.length,
    duyNhat.reduce((s, p) => s + p[1], 0) / duyNhat.length,
    duyNhat.reduce((s, p) => s + p[2], 0) / duyNhat.length,
  ];
  const cAabb: Diem3 = [
    (hopDuPhong.min[0] + hopDuPhong.max[0]) * 0.5,
    (hopDuPhong.min[1] + hopDuPhong.max[1]) * 0.5,
    (hopDuPhong.min[2] + hopDuPhong.max[2]) * 0.5,
  ];
  const tamXoay: Diem3 = [
    (tb[0] + cAabb[0]) * 0.5,
    (tb[1] + cAabb[1]) * 0.5,
    (tb[2] + cAabb[2]) * 0.5,
  ];
  const banKinhKhoi = Math.max(
    0.25,
    ...duyNhat.map((p) => Math.hypot(p[0] - tamXoay[0], p[1] - tamXoay[1], p[2] - tamXoay[2])),
  );
  return { tamXoay, banKinhKhoi, diemKhoiChinh: duyNhat };
}

/**
 * Khoảng TỰA của khối chính theo hướng nhìn `huong` (từ tâm xoay về phía camera): max⟨p − tâm, u⟩ trên mặt THẬT của khối
 * — đỉnh đa diện; cầu c·u + r; trụ/nón: đĩa đáy/đỉnh c·u + r·√(1 − (n·u)²) (và đỉnh nón). Đây là chỗ mặt gần camera nhất
 * thực sự nằm; cầu bao chỉ là cận trên (với khối cong nó TRÙNG mặt, nên không dùng được để giữ khoảng cách).
 */
export function khoangTuaTheoHuong(info: TamXoayOnDinh, huong: Diem3): number {
  const len = Math.hypot(huong[0], huong[1], huong[2]);
  if (!(len > 0)) return info.banKinhKhoi;
  const u: Diem3 = [huong[0] / len, huong[1] / len, huong[2] / len];
  const t = info.tamXoay;
  const chieu = (p: readonly number[]) => (p[0] - t[0]) * u[0] + (p[1] - t[1]) * u[1] + (p[2] - t[2]) * u[2];
  let tua = Math.max(0, ...info.diemKhoiChinh.map(chieu));
  for (const k of info.khoiChinh ?? []) {
    if (k.loai === "solid") {
      for (const v of k.vertices) tua = Math.max(tua, chieu(v));
      continue;
    }
    const truc: Diem3 = [k.apexOrTop[0] - k.anchor[0], k.apexOrTop[1] - k.anchor[1], k.apexOrTop[2] - k.anchor[2]];
    const h = Math.hypot(...truc);
    if ((k.curvedKind === "cylinder" || k.curvedKind === "cone") && h > 0) {
      const nu = (truc[0] * u[0] + truc[1] * u[1] + truc[2] * u[2]) / h;
      const vanh = k.radius * Math.sqrt(Math.max(0, 1 - nu * nu));
      tua = Math.max(tua, chieu(k.anchor) + vanh, chieu(k.apexOrTop) + (k.curvedKind === "cylinder" ? vanh : 0));
    } else {
      tua = Math.max(tua, chieu(k.anchor) + k.radius);
    }
  }
  return tua;
}

/** Mặt gần nhất của khối chính không bao giờ quá NỬA đường từ camera tới tâm xoay. */
export const HE_SO_KHOANG_GAN_MAT = 2;

/**
 * Giới hạn zoom gần (`OrbitControls.minDistance`) theo hướng nhìn hiện tại. Giữ luật cũ (theo khung vừa và cầu bao) làm
 * sàn, nâng lên `HE_SO_KHOANG_GAN_MAT × khoảng tựa` để camera không áp sát mặt thật của khối (cầu/trụ/nón), và chặn trên ở
 * 0.8 khoảng khung vừa để luôn còn cận cảnh. Không đổi hình học — chỉ khoảng cách camera.
 */
export function khoangGanToiThieu(info: TamXoayOnDinh | null | undefined, huong: Diem3, khoangKhung: number): number {
  const r = info?.banKinhKhoi;
  if (!info || !(typeof r === "number" && Number.isFinite(r) && r > 1e-4)) return Math.max(0.8, khoangKhung * 0.42);
  const cu = Math.max(0.5, Math.min(khoangKhung * 0.55, r * 1.08));
  return Math.min(Math.max(cu, HE_SO_KHOANG_GAN_MAT * khoangTuaTheoHuong(info, huong)), Math.max(cu, khoangKhung * 0.8));
}

/**
 * Đặt vị trí camera dọc theo hướng nhìn đi qua ĐÚNG `tamXoay` cố định sao cho mọi điểm hữu hạn `diem`
 * đều nằm gọn trong vùng an toàn NDC `[xMin, xMax] × [yMin, yMax]`, tuyệt đối không dịch chuyển `nhinVao`
 * khỏi tâm xoay chuẩn của khối hình học chính.
 */
export function khungNhinQuanhTam(
  diem: readonly Diem3[],
  tamXoay: Diem3,
  fovDo: number,
  tiLeKhung: number,
  huongChon?: Diem3,
  vungAnToanNdc?: VungAnToanNdc,
): KhungNhin | null {
  if (
    diem.length === 0 ||
    !tamXoay.every(Number.isFinite) ||
    !Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180 ||
    !Number.isFinite(tiLeKhung) || tiLeKhung <= 0
  ) {
    return null;
  }
  const d = chuan(
    huongChon && huongChon.every(Number.isFinite) && Math.hypot(...huongChon) > 1e-9
      ? huongChon
      : ([...HUONG] as Diem3),
  );
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const tanDoc = Math.tan((fovDo * Math.PI) / 360);
  const tanNgang = tanDoc * tiLeKhung;
  if (!(tanDoc > 0) || !(tanNgang > 0)) return null;

  const xMin = Math.max(-0.92, Math.min(-0.15, vungAnToanNdc?.xMin ?? -TI_LE_LAP_KHUNG));
  const xMax = Math.min(0.92, Math.max(0.15, vungAnToanNdc?.xMax ?? TI_LE_LAP_KHUNG));
  const yMin = Math.max(-0.92, Math.min(-0.15, vungAnToanNdc?.yMin ?? -TI_LE_LAP_KHUNG));
  const yMax = Math.min(0.92, Math.max(0.15, vungAnToanNdc?.yMax ?? TI_LE_LAP_KHUNG));

  let k = KHOANG_TOI_THIEU;
  for (const p of diem) {
    if (!p.every(Number.isFinite)) continue;
    const q = tru(p, tamXoay);
    const s = tich(q, d);
    const rx = tich(q, phai);
    const ry = tich(q, len);
    const kx = rx >= 0 ? rx / (xMax * tanNgang) : (-rx) / (-xMin * tanNgang);
    const ky = ry >= 0 ? ry / (yMax * tanDoc) : (-ry) / (-yMin * tanDoc);
    k = Math.max(k, s + Math.max(0.25, kx, ky));
  }

  return {
    viTri: [tamXoay[0] + d[0] * k, tamXoay[1] + d[1] * k, tamXoay[2] + d[2] * k],
    nhinVao: [tamXoay[0], tamXoay[1], tamXoay[2]],
  };
}
